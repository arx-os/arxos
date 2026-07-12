//! LiDAR incremental merge — thin adapter over the shared ingest merge policy.

use crate::core::Building;
use crate::ifc::mapping::{
    merge_building_with_policy, MergePolicy, MergeResult, MergeStats,
};

/// Merges a new LiDAR-derived building model into an existing one.
///
/// Uses [`MergePolicy::lidar`]: existing hierarchy is the base, rooms/equipment
/// match by id / path / spatial proximity, and scan geometry + enrichment win
/// when present while operational Arx state is preserved.
pub struct ModelMerger;

impl ModelMerger {
    /// Merge `incoming` scan into `existing` and return the updated building.
    pub fn merge(existing: Building, incoming: Building) -> Building {
        Self::merge_with_report(existing, incoming).building
    }

    /// Same as [`merge`](Self::merge) but returns full merge statistics and warnings.
    pub fn merge_with_report(existing: Building, incoming: Building) -> MergeResult {
        let result =
            merge_building_with_policy(&existing, incoming, &MergePolicy::lidar());
        log::info!(
            "LiDAR merge: rooms {} matched / {} added, equipment {} matched / {} added",
            result.stats.rooms_matched,
            result.stats.rooms_added,
            result.stats.equipment_matched,
            result.stats.equipment_added
        );
        for w in &result.warnings {
            log::warn!("[{}] {}", w.code, w.message);
        }
        result
    }

    /// Convenience: merge and return stats only.
    pub fn merge_stats(existing: Building, incoming: Building) -> (Building, MergeStats) {
        let r = Self::merge_with_report(existing, incoming);
        (r.building, r.stats)
    }
}
