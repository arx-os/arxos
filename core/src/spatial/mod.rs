//! Spatial index scaffolding (Phase 0: types only; construction in Phase 3).

use serde::{Deserialize, Serialize};

use crate::cid::Cid;
use crate::object::Aabb;

/// Placeholder query volume for future spatial queries.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct QueryVolume {
    pub bounds: Aabb,
}

/// Result of a spatial query (Phase 3 will populate).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpatialHit {
    pub object: Cid,
    pub bounds: Option<Aabb>,
}

// Spatial index construction and query land in Phase 3.
// Roots already carry `spatial_index_root: Option<Cid>`.
