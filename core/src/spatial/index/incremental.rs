//! Incremental inserts with structural sharing.

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{Aabb, Object, ObjectBody};
use crate::store::ObjectStore;

use super::super::aabb::union_all;
use super::build::build_index;
use super::{
    entry_from_object, node_object, sort_cid_bounds_for_split, sort_entries_for_split,
    SpatialEntry, LEAF_CAPACITY, MAX_CHILDREN,
};

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

            sort_entries_for_split(&mut leaf_entries, &new_bounds);

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

                if new_children.len() <= MAX_CHILDREN {
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
                    // Overflow: longest-axis median-of-centroids (same as full build).
                    let mut child_entries = Vec::new();
                    for child_cid in &new_children {
                        let child_obj = get_obj(child_cid, cache, store)?;
                        if let ObjectBody::SpatialIndexNode(child_node) = child_obj.body {
                            child_entries.push((*child_cid, child_node.bounds.clone()));
                        }
                    }

                    sort_cid_bounds_for_split(&mut child_entries, &new_bounds);
                    let mid = child_entries.len() / 2;
                    if mid == 0 || mid == child_entries.len() {
                        return Err(Error::Validation(
                            "internal node overflow could not be split".into(),
                        ));
                    }
                    let left_c = &child_entries[..mid];
                    let right_c = &child_entries[mid..];

                    let left_bounds = union_all(left_c.iter().map(|e| e.1.clone()))
                        .ok_or_else(|| Error::Validation("empty left split".into()))?;
                    let right_bounds = union_all(right_c.iter().map(|e| e.1.clone()))
                        .ok_or_else(|| Error::Validation("empty right split".into()))?;

                    let mut left_kids: Vec<Cid> = left_c.iter().map(|e| e.0).collect();
                    let mut right_kids: Vec<Cid> = right_c.iter().map(|e| e.0).collect();
                    left_kids.sort();
                    right_kids.sort();

                    let left_node = node_object(left_bounds, left_kids, Vec::new());
                    let right_node = node_object(right_bounds, right_kids, Vec::new());

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

