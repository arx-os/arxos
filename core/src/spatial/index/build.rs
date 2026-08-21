//! Full hierarchical AABB index construction.

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::store::ObjectWrite;

use super::super::aabb::union_all;
use super::{
    node_object, sort_entries_for_split, split_evenly, SpatialEntry, LEAF_CAPACITY, MAX_CHILDREN,
    MAX_DEPTH,
};

pub fn build_index<W: ObjectWrite + ?Sized>(
    store: &W,
    mut entries: Vec<SpatialEntry>,
) -> Result<Option<Cid>> {
    if entries.is_empty() {
        return Ok(None);
    }
    // Stable order for deterministic CIDs.
    entries.sort_by_key(|e| e.cid);
    let root = build_recursive(store, entries, 0)?;
    Ok(Some(root))
}

fn build_recursive<W: ObjectWrite + ?Sized>(
    store: &W,
    entries: Vec<SpatialEntry>,
    depth: usize,
) -> Result<Cid> {
    let bounds = union_all(entries.iter().map(|e| e.bounds.clone())).ok_or_else(|| {
        Error::Validation("empty entries in spatial index node".into())
    })?;

    if entries.len() <= LEAF_CAPACITY || depth >= MAX_DEPTH {
        let refs: Vec<Cid> = entries.into_iter().map(|e| e.cid).collect();
        let obj = node_object(bounds, Vec::new(), refs);
        return store.put(&obj);
    }

    let mut sorted = entries;
    sort_entries_for_split(&mut sorted, &bounds);
    let groups = split_evenly(sorted, MAX_CHILDREN);
    if groups.len() < 2 {
        let refs: Vec<Cid> = groups.into_iter().flatten().map(|e| e.cid).collect();
        let obj = node_object(bounds, Vec::new(), refs);
        return store.put(&obj);
    }

    let mut children = Vec::with_capacity(groups.len());
    for group in groups {
        children.push(build_recursive(store, group, depth + 1)?);
    }
    children.sort();
    let obj = node_object(bounds, children, Vec::new());
    store.put(&obj)
}
