//! Full hierarchical AABB index construction.

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::store::ObjectStore;

use super::super::aabb::union_all;
use super::{node_object, SpatialEntry, LEAF_CAPACITY, MAX_DEPTH};

pub fn build_index(store: &ObjectStore, mut entries: Vec<SpatialEntry>) -> Result<Option<Cid>> {
    if entries.is_empty() {
        return Ok(None);
    }
    // Stable order for deterministic CIDs.
    entries.sort_by_key(|e| e.cid);
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
