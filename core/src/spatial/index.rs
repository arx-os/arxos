//! Versioned hierarchical AABB spatial index stored as content-addressed objects.
//!
//! Index nodes are ordinary [`ObjectBody::SpatialIndexNode`] values. The root CID
//! of the index is referenced from [`crate::root::RootBody::spatial_index_root`].

use std::collections::BTreeMap;

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

enum InsertResult {
    Unsplit(Cid),
    Split(Cid, Cid),
}

/// Insert new spatial entries incrementally into an existing index tree.
/// Reuses unchanged subtrees (structural sharing).
pub fn insert_incremental(
    store: &ObjectStore,
    root_cid: Option<Cid>,
    new_entries: Vec<SpatialEntry>,
) -> Result<Option<Cid>> {
    let mut current_root = root_cid;

    // In-memory cache for writes and reads during incremental building.
    let cache = std::cell::RefCell::new(std::collections::BTreeMap::new());

    // Helper closure to get from cache or store (and cache the read result)
    let get_obj = |cid: &Cid, cache: &std::cell::RefCell<std::collections::BTreeMap<Cid, Object>>, store: &ObjectStore| -> Result<Object> {
        if let Some(obj) = cache.borrow().get(cid) {
            return Ok(obj.clone());
        }
        let obj = store.get(cid)?;
        cache.borrow_mut().insert(*cid, obj.clone());
        Ok(obj)
    };

    for entry in new_entries {
        if let Some(rcid) = current_root {
            match insert_recursive_cached(store, &cache, &get_obj, rcid, &entry)? {
                InsertResult::Unsplit(new_rcid) => {
                    current_root = Some(new_rcid);
                }
                InsertResult::Split(left_cid, right_cid) => {
                    let left_obj = get_obj(&left_cid, &cache, store)?;
                    let right_obj = get_obj(&right_cid, &cache, store)?;
                    let ObjectBody::SpatialIndexNode(left_node) = left_obj.body else {
                        return Err(Error::Validation("invalid left node".into()));
                    };
                    let ObjectBody::SpatialIndexNode(right_node) = right_obj.body else {
                        return Err(Error::Validation("invalid right node".into()));
                    };
                    let mut parent_bounds = left_node.bounds.clone();
                    parent_bounds.min[0] = parent_bounds.min[0].min(right_node.bounds.min[0]);
                    parent_bounds.min[1] = parent_bounds.min[1].min(right_node.bounds.min[1]);
                    parent_bounds.min[2] = parent_bounds.min[2].min(right_node.bounds.min[2]);
                    parent_bounds.max[0] = parent_bounds.max[0].max(right_node.bounds.max[0]);
                    parent_bounds.max[1] = parent_bounds.max[1].max(right_node.bounds.max[1]);
                    parent_bounds.max[2] = parent_bounds.max[2].max(right_node.bounds.max[2]);

                    let mut children = vec![left_cid, right_cid];
                    children.sort(); // Determinism
                    let new_root = node_object(parent_bounds, children, Vec::new());
                    let new_root_cid = new_root.cid()?;
                    cache.borrow_mut().insert(new_root_cid, new_root);
                    current_root = Some(new_root_cid);
                }
            }
        } else {
            current_root = build_index(store, vec![entry])?;
        }
    }

    // Flush only reachable nodes to the ObjectStore at the very end!
    if let Some(ref final_root_cid) = current_root {
        let mut reachable = std::collections::BTreeSet::new();
        let mut queue = vec![*final_root_cid];
        let cache_ref = cache.borrow();
        while let Some(cid) = queue.pop() {
            if !reachable.insert(cid) {
                continue;
            }
            if let Some(obj) = cache_ref.get(&cid) {
                if let ObjectBody::SpatialIndexNode(node) = &obj.body {
                    for child_cid in &node.children {
                        if cache_ref.contains_key(child_cid) {
                            queue.push(*child_cid);
                        }
                    }
                }
            }
        }
        // Release borrow so we can store.put which might read or mutate
        drop(cache_ref);

        let mut cache_mut = cache.borrow_mut();
        for cid in reachable {
            if let Some(obj) = cache_mut.remove(&cid) {
                store.put(&obj)?;
            }
        }
    }

    Ok(current_root)
}

fn insert_recursive_cached<F>(
    store: &ObjectStore,
    cache: &std::cell::RefCell<std::collections::BTreeMap<Cid, Object>>,
    get_obj: &F,
    node_cid: Cid,
    entry: &SpatialEntry,
) -> Result<InsertResult>
where
    F: Fn(&Cid, &std::cell::RefCell<std::collections::BTreeMap<Cid, Object>>, &ObjectStore) -> Result<Object>,
{
    let obj = get_obj(&node_cid, cache, store)?;
    let ObjectBody::SpatialIndexNode(node) = obj.body else {
        return Err(Error::Validation(format!(
            "expected spatial index node, got {}",
            obj.header.object_type
        )));
    };

    let mut new_bounds = node.bounds.clone();
    new_bounds.min[0] = new_bounds.min[0].min(entry.bounds.min[0]);
    new_bounds.min[1] = new_bounds.min[1].min(entry.bounds.min[1]);
    new_bounds.min[2] = new_bounds.min[2].min(entry.bounds.min[2]);
    new_bounds.max[0] = new_bounds.max[0].max(entry.bounds.max[0]);
    new_bounds.max[1] = new_bounds.max[1].max(entry.bounds.max[1]);
    new_bounds.max[2] = new_bounds.max[2].max(entry.bounds.max[2]);

    if node.children.is_empty() {
        // Leaf node!
        let mut refs = node.object_refs.clone();
        refs.push(entry.cid);
        refs.sort(); // Determinism

        if refs.len() <= LEAF_CAPACITY {
            let leaf_node = node_object(new_bounds, Vec::new(), refs);
            let leaf_cid = leaf_node.cid()?;
            cache.borrow_mut().insert(leaf_cid, leaf_node);
            Ok(InsertResult::Unsplit(leaf_cid))
        } else {
            // Split the leaf! Collect entry bounds.
            let mut leaf_entries = Vec::new();
            for r_cid in refs {
                if r_cid == entry.cid {
                    leaf_entries.push(entry.clone());
                } else if let Ok(ref_obj) = get_obj(&r_cid, cache, store) {
                    if let Some(le) = entry_from_object(r_cid, &ref_obj) {
                        leaf_entries.push(le);
                    }
                }
            }

            let split_axis = new_bounds.longest_axis();
            leaf_entries.sort_by(|a, b| {
                let ca = a.bounds.centroid()[split_axis];
                let cb = b.bounds.centroid()[split_axis];
                ca.partial_cmp(&cb)
                    .unwrap_or(std::cmp::Ordering::Equal)
                    .then_with(|| a.cid.cmp(&b.cid)) // Stable sorting tie-breaker
            });

            let mid = leaf_entries.len() / 2;
            let left_entries = &leaf_entries[..mid];
            let right_entries = &leaf_entries[mid..];

            let left_bounds = union_all(left_entries.iter().map(|e| e.bounds.clone()))
                .ok_or_else(|| Error::Validation("empty left split".into()))?;
            let right_bounds = union_all(right_entries.iter().map(|e| e.bounds.clone()))
                .ok_or_else(|| Error::Validation("empty right split".into()))?;

            let left_refs: Vec<Cid> = left_entries.iter().map(|e| e.cid).collect();
            let right_refs: Vec<Cid> = right_entries.iter().map(|e| e.cid).collect();

            let left_node = node_object(left_bounds, Vec::new(), left_refs);
            let right_node = node_object(right_bounds, Vec::new(), right_refs);

            let left_cid = left_node.cid()?;
            let right_cid = right_node.cid()?;

            cache.borrow_mut().insert(left_cid, left_node);
            cache.borrow_mut().insert(right_cid, right_node);

            Ok(InsertResult::Split(left_cid, right_cid))
        }
    } else {
        // Internal node! Choose child requiring minimal area/volume expansion.
        assert!(!node.children.is_empty());
        let mut best_child_idx = 0;
        let mut min_expansion = f64::MAX;

        for (idx, child_cid) in node.children.iter().enumerate() {
            let child_obj = get_obj(child_cid, cache, store)?;
            let ObjectBody::SpatialIndexNode(child_node) = child_obj.body else {
                return Err(Error::Validation("invalid child node type".into()));
            };
            let current_vol = child_node.bounds.volume();
            let mut expanded_bounds = child_node.bounds.clone();
            expanded_bounds.min[0] = expanded_bounds.min[0].min(entry.bounds.min[0]);
            expanded_bounds.min[1] = expanded_bounds.min[1].min(entry.bounds.min[1]);
            expanded_bounds.min[2] = expanded_bounds.min[2].min(entry.bounds.min[2]);
            expanded_bounds.max[0] = expanded_bounds.max[0].max(entry.bounds.max[0]);
            expanded_bounds.max[1] = expanded_bounds.max[1].max(entry.bounds.max[1]);
            expanded_bounds.max[2] = expanded_bounds.max[2].max(entry.bounds.max[2]);
            let expanded_vol = expanded_bounds.volume();

            let expansion = expanded_vol - current_vol;
            if expansion < min_expansion {
                min_expansion = expansion;
                best_child_idx = idx;
            }
        }

        let chosen_cid = node.children[best_child_idx];
        let mut new_children = node.children.clone();

        match insert_recursive_cached(store, cache, get_obj, chosen_cid, entry)? {
            InsertResult::Unsplit(new_child_cid) => {
                new_children[best_child_idx] = new_child_cid;
                // Recompute parent bounds from child node bounds
                let mut bounds_union: Option<Aabb> = None;
                for child_cid in &new_children {
                    let child_obj = get_obj(child_cid, cache, store)?;
                    if let ObjectBody::SpatialIndexNode(child_node) = child_obj.body {
                        if let Some(ref mut u) = bounds_union {
                            u.min[0] = u.min[0].min(child_node.bounds.min[0]);
                            u.min[1] = u.min[1].min(child_node.bounds.min[1]);
                            u.min[2] = u.min[2].min(child_node.bounds.min[2]);
                            u.max[0] = u.max[0].max(child_node.bounds.max[0]);
                            u.max[1] = u.max[1].max(child_node.bounds.max[1]);
                            u.max[2] = u.max[2].max(child_node.bounds.max[2]);
                        } else {
                            bounds_union = Some(child_node.bounds.clone());
                        }
                    }
                }
                let parent_bounds = bounds_union.unwrap_or(new_bounds);
                let new_parent = node_object(parent_bounds, new_children, Vec::new());
                let new_parent_cid = new_parent.cid()?;
                cache.borrow_mut().insert(new_parent_cid, new_parent);
                Ok(InsertResult::Unsplit(new_parent_cid))
            }
            InsertResult::Split(left_cid, right_cid) => {
                new_children.remove(best_child_idx);
                new_children.push(left_cid);
                new_children.push(right_cid);
                new_children.sort(); // Determinism

                if new_children.len() <= 2 {
                    let mut bounds_union: Option<Aabb> = None;
                    for child_cid in &new_children {
                        let child_obj = get_obj(child_cid, cache, store)?;
                        if let ObjectBody::SpatialIndexNode(child_node) = child_obj.body {
                            if let Some(ref mut u) = bounds_union {
                                u.min[0] = u.min[0].min(child_node.bounds.min[0]);
                                u.min[1] = u.min[1].min(child_node.bounds.min[1]);
                                u.min[2] = u.min[2].min(child_node.bounds.min[2]);
                                u.max[0] = u.max[0].max(child_node.bounds.max[0]);
                                u.max[1] = u.max[1].max(child_node.bounds.max[1]);
                                u.max[2] = u.max[2].max(child_node.bounds.max[2]);
                            } else {
                                bounds_union = Some(child_node.bounds.clone());
                            }
                        }
                    }
                    let parent_bounds = bounds_union.unwrap_or(new_bounds);
                    let new_parent = node_object(parent_bounds, new_children, Vec::new());
                    let new_parent_cid = new_parent.cid()?;
                    cache.borrow_mut().insert(new_parent_cid, new_parent);
                    Ok(InsertResult::Unsplit(new_parent_cid))
                } else {
                    // Split the internal node itself
                    let mut child_entries = Vec::new();
                    for child_cid in &new_children {
                        let child_obj = get_obj(child_cid, cache, store)?;
                        if let ObjectBody::SpatialIndexNode(child_node) = child_obj.body {
                            child_entries.push((*child_cid, child_node.bounds.clone()));
                        }
                    }

                    let split_axis = new_bounds.longest_axis();
                    child_entries.sort_by(|a, b| {
                        let ca = a.1.centroid()[split_axis];
                        let cb = b.1.centroid()[split_axis];
                        ca.partial_cmp(&cb)
                            .unwrap_or(std::cmp::Ordering::Equal)
                            .then_with(|| a.0.cmp(&b.0)) // Stable sorting tie-breaker
                    });

                    let left_c = &child_entries[..1];
                    let right_c = &child_entries[1..];

                    let left_bounds = left_c[0].1.clone();
                    let right_bounds = union_all(right_c.iter().map(|e| e.1.clone()))
                        .ok_or_else(|| Error::Validation("empty right split".into()))?;

                    let left_node = node_object(left_bounds, vec![left_c[0].0], Vec::new());
                    let right_node = node_object(right_bounds, right_c.iter().map(|e| e.0).collect(), Vec::new());

                    let left_parent_cid = left_node.cid()?;
                    let right_parent_cid = right_node.cid()?;

                    cache.borrow_mut().insert(left_parent_cid, left_node);
                    cache.borrow_mut().insert(right_parent_cid, right_node);

                    Ok(InsertResult::Split(left_parent_cid, right_parent_cid))
                }
            }
        }
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
}
