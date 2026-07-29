//! Spatial index: versioned hierarchical AABB tree stored as CAS objects.
//!
//! Phase 3 delivers:
//! - build / query of spatial indexes
//! - partial materialization by volume or floor
//! - AABB helpers for capture and merge

mod aabb;
mod index;

pub use aabb::{union_all, POINT_HALF_EXTENT_M};
pub use index::{
    build_index, collect_entries, entry_from_object, filter_by_floor, query_index,
    query_index_refined, volume_around_pose, SpatialEntry, LEAF_CAPACITY, MAX_DEPTH,
    insert_incremental,
};

use serde::{Deserialize, Serialize};

use crate::cid::Cid;
use crate::object::Aabb;

/// Query volume for spatial range queries.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct QueryVolume {
    pub bounds: Aabb,
}

impl QueryVolume {
    pub fn new(bounds: Aabb) -> Self {
        Self { bounds }
    }

    pub fn from_min_max(min: [f64; 3], max: [f64; 3]) -> Self {
        Self {
            bounds: Aabb::from_min_max(min, max),
        }
    }
}

/// Result of a spatial query.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpatialHit {
    pub object: Cid,
    pub bounds: Option<Aabb>,
}
