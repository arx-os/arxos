//! Building-data contributions for the ArxOS reward path.
//!
//! **Vision defaults (locked):**
//! - Software is free; rewards attach to **verified as-built building data**.
//! - Primary labor unit: validated `Building` / `building.yaml` (optionally Git commit).
//! - Oracle consumes a deterministic **commitment** + quality scores — not sensor DeviceState.
//!
//! Sensor-based hashing remains in `blockchain::contribution` as a secondary path only.

mod commitment;
mod package;
mod quality;

pub use commitment::{
    building_content_hash, building_entity_merkle_root, commit_building, BuildingCommitment,
    HASH_ALG_LABEL,
};
pub use package::{build_contribution_package, ContributionPackage, PackageOptions};
pub use quality::{quality_from_building, QualityScores};
