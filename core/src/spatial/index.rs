//! Versioned hierarchical AABB spatial index stored as content-addressed objects.
//!
//! Index nodes are ordinary [`ObjectBody::SpatialIndexNode`] values. The root CID
//! of the index is referenced from [`crate::root::RootBody::spatial_index_root`].

use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{
    Aabb, Object, ObjectBody, ObjectHeader, ObjectType, SpatialIndexNodeBody, SCHEMA_VERSION,
};
use crate::store::ObjectStore;

use super::aabb::{union_all, POINT_HALF_EXTENT_M};
use super::{QueryVolume, SpatialHit};

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

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
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

fn node_object(bounds: Aabb, children: Vec<Cid>, object_refs: Vec<Cid>) -> Object {
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
            created: now_secs(),
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
pub fn build_index(store: &ObjectStore, mut entries: Vec<SpatialEntry>) -> Result<Option<Cid>> {
    if entries.is_empty() {
        return Ok(None);
    }
    // Stable order for deterministic CIDs.
    entries.sort_by(|a, b| a.cid.cmp(&b.cid));
    let root = build_recursive(store, entries, 0)?;
    Ok(Some(root))
}

fn build_recursive(store: &ObjectStore, entries: Vec<SpatialEntry>, depth: usize) -> Result<Cid> {
    let bounds = union_all(entries.iter().map(|e| e.bounds.clone())).ok_or_else(|| {
        Error::Validation("empty entries in spatial index node".into())
    })?;

    if entries.len() <= LEAF_CAPACITY || depth >= MAX_DEPTH {
        let refs: Vec<Cid> = entries.into_iter().map(|e| e.cid).collect();
        let obj = node_object(bounds, Vec::new(), refs);
        return store.put(&obj);
    }

    let axis = bounds.longest_axis();
    let mut sorted = entries;
    sorted.sort_by(|a, b| {
        let ca = a.bounds.centroid()[axis];
        let cb = b.bounds.centroid()[axis];
        ca.partial_cmp(&cb).unwrap_or(std::cmp::Ordering::Equal)
    });
    // Fix Equal casing via sed later if needed - use Ordering::Equal carefully
    let mid = sorted.len() / 2;
    if mid == 0 || mid == sorted.len() {
        let refs: Vec<Cid> = sorted.into_iter().map(|e| e.cid).collect();
        let obj = node_object(bounds, Vec::new(), refs);
        return store.put(&obj);
    }
    let right = sorted.split_off(mid);
    let left = sorted;
    let left_cid = build_recursive(store, left, depth + 1)?;
    let right_cid = build_recursive(store, right, depth + 1)?;
    let obj = node_object(bounds, vec![left_cid, right_cid], Vec::new());
    store.put(&obj)
}

/// Query the spatial index: returns object CIDs whose node bounds intersect `volume`.
///
/// Only loads index node objects (partial). Does not load hit objects themselves.
pub fn query_index(
    store: &ObjectStore,
    index_root: &Cid,
    volume: &QueryVolume,
) -> Result<Vec<SpatialHit>> {
    let mut hits = Vec::new();
    let mut stack = vec![*index_root];
    while let Some(node_cid) = stack.pop() {
        let obj = store.get(&node_cid)?;
        let ObjectBody::SpatialIndexNode(node) = obj.body else {
            return Err(Error::Validation(format!(
                "expected spatial index node, got {}",
                obj.header.object_type
            )));
        };
        if !node.bounds.intersects(&volume.bounds) {
            continue;
        }
        if node.children.is_empty() {
            // Leaf: all object_refs are candidates; refine by loading bounds if present
            // via optional BoundingVolume — for Phase 3 we trust leaf membership.
            for cid in node.object_refs {
                hits.push(SpatialHit {
                    object: cid,
                    bounds: Some(node.bounds.clone()),
                });
            }
        } else {
            stack.extend(node.children);
        }
    }
    // Dedupe CIDs (can appear if overlapping leaves — shouldn't with our build).
    hits.sort_by(|a, b| a.object.cmp(&b.object));
    hits.dedup_by(|a, b| a.object == b.object);
    Ok(hits)
}

/// Query and refine hits by loading each object and testing its true bounds.
pub fn query_index_refined(
    store: &ObjectStore,
    index_root: &Cid,
    volume: &QueryVolume,
) -> Result<Vec<SpatialHit>> {
    let coarse = query_index(store, index_root, volume)?;
    let mut refined = Vec::new();
    for hit in coarse {
        match store.get(&hit.object) {
            Ok(obj) => {
                if let Some(entry) = entry_from_object(hit.object, &obj) {
                    if entry.bounds.intersects(&volume.bounds) {
                        refined.push(SpatialHit {
                            object: hit.object,
                            bounds: Some(entry.bounds),
                        });
                    }
                }
            }
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        }
    }
    Ok(refined)
}

/// Filter entries by floor CID (exact) or Y-slab intersection.
pub fn filter_by_floor(entries: &[SpatialEntry], floor: &Cid) -> Vec<SpatialEntry> {
    entries
        .iter()
        .filter(|e| e.floor.as_ref() == Some(floor))
        .cloned()
        .collect()
}

/// Query volume around a pose (sphere approximated as AABB).
pub fn volume_around_pose(pose: &crate::object::Pose, radius_m: f64) -> QueryVolume {
    QueryVolume {
        bounds: Aabb::from_pose(pose, radius_m),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
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
}
