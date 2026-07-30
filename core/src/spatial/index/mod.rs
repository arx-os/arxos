//! Versioned hierarchical AABB spatial index stored as content-addressed objects.

mod build;
mod incremental;
mod query;

pub use build::build_index;
pub use incremental::insert_incremental;
pub use query::{filter_by_floor, query_index, query_index_refined, volume_around_pose};

// Index nodes are ordinary ObjectBody::SpatialIndexNode values. The root CID of
// the index is referenced from RootBody::spatial_index_root.

use std::collections::BTreeMap;

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{
    Aabb, Object, ObjectBody, ObjectHeader, ObjectType, SpatialIndexNodeBody, SCHEMA_VERSION,
};
use crate::store::ObjectStore;

use super::aabb::POINT_HALF_EXTENT_M;

/// Max object refs in a leaf before splitting.
pub const LEAF_CAPACITY: usize = 16;

/// Max tree depth (guards pathological inputs).
pub const MAX_DEPTH: usize = 24;

/// One indexable object with bounds.
#[derive(Debug, Clone, PartialEq)]
pub struct SpatialEntry {
    pub cid: Cid,
    pub bounds: Aabb,
    pub object_type: ObjectType,
    /// Optional floor object CID when known.
    pub floor: Option<Cid>,
}

/// Extract a spatial entry from an object, if it has pose and/or bounds.
pub fn entry_from_object(cid: Cid, obj: &Object) -> Option<SpatialEntry> {
    let object_type = obj.header.object_type;
    let (bounds, floor) = match &obj.body {
        ObjectBody::Space(b) => {
            let bounds = b
                .bounds
                .clone()
                .or_else(|| b.pose.as_ref().map(|p| Aabb::from_pose(p, 1.0)))?;
            (bounds, b.floor)
        }
        ObjectBody::Surface(b) => {
            let bounds = b.bounds.clone().or_else(|| {
                b.pose
                    .as_ref()
                    .map(|p| Aabb::from_pose(p, POINT_HALF_EXTENT_M))
            })?;
            (bounds, None)
        }
        ObjectBody::Opening(b) => {
            let bounds = b
                .pose
                .as_ref()
                .map(|p| Aabb::from_pose(p, POINT_HALF_EXTENT_M))?;
            (bounds, None)
        }
        ObjectBody::Equipment(b) => {
            let bounds = b
                .pose
                .as_ref()
                .map(|p| Aabb::from_pose(p, POINT_HALF_EXTENT_M))?;
            (bounds, None)
        }
        ObjectBody::Sensor(b) => {
            let bounds = b
                .pose
                .as_ref()
                .map(|p| Aabb::from_pose(p, POINT_HALF_EXTENT_M))?;
            (bounds, None)
        }
        ObjectBody::Fixture(b) => {
            let bounds = b
                .pose
                .as_ref()
                .map(|p| Aabb::from_pose(p, POINT_HALF_EXTENT_M))?;
            (bounds, None)
        }
        ObjectBody::Annotation(b) => {
            let bounds = b
                .pose
                .as_ref()
                .map(|p| Aabb::from_pose(p, POINT_HALF_EXTENT_M))?;
            (bounds, None)
        }
        ObjectBody::PointCloudChunk(b) => {
            let bounds = b
                .bounds
                .clone()
                .or_else(|| b.pose.as_ref().map(|p| Aabb::from_pose(p, 1.0)))?;
            (bounds, None)
        }
        ObjectBody::Mesh(b) => {
            let bounds = b
                .bounds
                .clone()
                .or_else(|| b.pose.as_ref().map(|p| Aabb::from_pose(p, 1.0)))?;
            (bounds, None)
        }
        ObjectBody::BoundingVolume(b) => (b.bounds.clone(), None),
        ObjectBody::Floor(b) => {
            // Floor slab with default horizontal extent for indexing.
            let slab = Aabb::floor_slab(b.elevation_m, 1.5);
            let bounds = Aabb {
                min: [-50.0, slab.min[1], -50.0],
                max: [50.0, slab.max[1], 50.0],
            };
            (bounds, Some(cid))
        }
        _ => return None,
    };
    Some(SpatialEntry {
        cid,
        bounds,
        object_type,
        floor,
    })
}

/// Collect spatial entries for an object set from the store.
pub fn collect_entries(store: &ObjectStore, cids: impl IntoIterator<Item = Cid>) -> Result<Vec<SpatialEntry>> {
    let mut out = Vec::new();
    for cid in cids {
        match store.get(&cid) {
            Ok(obj) => {
                if let Some(e) = entry_from_object(cid, &obj) {
                    out.push(e);
                }
            }
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        }
    }
    Ok(out)
}

pub(super) fn node_object(bounds: Aabb, children: Vec<Cid>, object_refs: Vec<Cid>) -> Object {
    let mut properties = BTreeMap::new();
    properties.insert("index_kind".into(), "aabb_tree".into());
    properties.insert(
        "is_leaf".into(),
        if children.is_empty() {
            "true".into()
        } else {
            "false".into()
        },
    );
    Object {
        header: ObjectHeader {
            object_type: ObjectType::SpatialIndexNode,
            schema_version: SCHEMA_VERSION,
            // Spatial index nodes are internal derived structures rebuilt from domain geometry.
            // Using a fixed timestamp of 0 ensures index builds are completely deterministic.
            created: 0,
            author: None,
            signature: None,
        },
        body: ObjectBody::SpatialIndexNode(SpatialIndexNodeBody {
            bounds,
            children,
            object_refs,
            properties,
        }),
    }
}

/// Build a hierarchical spatial index into `store`; returns the index root CID.

#[cfg(test)]
mod tests {
    use super::*;
    use crate::spatial::QueryVolume;
    use crate::capture::{annotation_object, AnnotationCapture};
    use crate::object::Pose;
    use tempfile::tempdir;

    #[test]
    fn build_and_query() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let mut cids = Vec::new();
        for i in 0..40 {
            let obj = annotation_object(&AnnotationCapture::new(
                format!("n{i}"),
                Pose {
                    position: [i as f64, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            cids.push(store.put(&obj).unwrap());
        }
        let entries = collect_entries(&store, cids.iter().copied()).unwrap();
        assert_eq!(entries.len(), 40);
        let root = build_index(&store, entries).unwrap().unwrap();

        let hits = query_index_refined(
            &store,
            &root,
            &QueryVolume {
                bounds: Aabb::from_min_max([-0.5, -1.0, -1.0], [5.5, 1.0, 1.0]),
            },
        )
        .unwrap();
        // points 0..5 inclusive roughly
        assert!(hits.len() >= 5 && hits.len() <= 8, "hits={}", hits.len());
    }

    #[test]
    fn test_spatial_index_determinism() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let mut cids = Vec::new();
        for i in 0..40 {
            let obj = annotation_object(&AnnotationCapture::new(
                format!("node-{i}"),
                Pose {
                    position: [i as f64, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            cids.push(store.put(&obj).unwrap());
        }

        // Build first time
        let entries1 = collect_entries(&store, cids.iter().copied()).unwrap();
        let root1 = build_index(&store, entries1).unwrap().unwrap();

        // Build second time (possibly different system time)
        let entries2 = collect_entries(&store, cids.iter().copied()).unwrap();
        let root2 = build_index(&store, entries2).unwrap().unwrap();

        assert_eq!(root1, root2);
    }

    #[test]
    fn test_incremental_index_determinism() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let mut cids = Vec::new();
        for i in 0..40 {
            let obj = annotation_object(&AnnotationCapture::new(
                format!("node-{i}"),
                Pose {
                    position: [i as f64, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            cids.push(store.put(&obj).unwrap());
        }

        let entries = collect_entries(&store, cids.iter().copied()).unwrap();

        // Path A: Incremental insertion 1
        let mut root1 = None;
        for entry in &entries {
            root1 = insert_incremental(&store, root1, vec![entry.clone()]).unwrap();
        }

        // Path B: Incremental insertion 2
        let mut root2 = None;
        for entry in &entries {
            root2 = insert_incremental(&store, root2, vec![entry.clone()]).unwrap();
        }

        assert_eq!(root1, root2);
        assert!(root1.is_some());
    }

    /// Query-set equivalence: full rebuild and incremental insert return the same
    /// object CIDs for refined queries. Index *node* CIDs may differ between the
    /// two construction algorithms (different split heuristics); that is expected.
    ///
    /// Canonical path for checkpoints / merge is [`build_index`]; day-to-day
    /// commits use [`insert_incremental`].
    #[test]
    fn rebuild_and_incremental_query_equivalent() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let mut cids = Vec::new();
        for i in 0..32 {
            let obj = annotation_object(&AnnotationCapture::new(
                format!("eq-{i}"),
                Pose {
                    position: [(i % 8) as f64, 0.0, (i / 8) as f64],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            cids.push(store.put(&obj).unwrap());
        }
        let mut entries = collect_entries(&store, cids.iter().copied()).unwrap();
        entries.sort_by_key(|e| e.cid);

        let rebuilt = build_index(&store, entries.clone()).unwrap().unwrap();

        let mut incremental = None;
        for entry in &entries {
            incremental =
                insert_incremental(&store, incremental, vec![entry.clone()]).unwrap();
        }
        let incremental = incremental.unwrap();

        let volume = QueryVolume {
            bounds: Aabb::from_min_max([-1.0, -1.0, -1.0], [10.0, 1.0, 10.0]),
        };
        let h1 = query_index_refined(&store, &rebuilt, &volume).unwrap();
        let h2 = query_index_refined(&store, &incremental, &volume).unwrap();
        let mut c1: Vec<_> = h1.into_iter().map(|h| h.object).collect();
        let mut c2: Vec<_> = h2.into_iter().map(|h| h.object).collect();
        c1.sort();
        c2.sort();
        assert_eq!(c1, c2, "query results must match across construction paths");
        assert_eq!(c1.len(), 32);
    }
}
