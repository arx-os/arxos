//! Spatial index range queries.

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{Aabb, ObjectBody};
use crate::store::ObjectStore;

use super::super::{QueryVolume, SpatialHit};
use super::{entry_from_object, SpatialEntry};

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
    hits.sort_by_key(|h| h.object);
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

