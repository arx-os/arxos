//! Spatial adapters (LiDAR pipeline → `core::Building`).
//!
//! Geometry types live in `core::spatial`. This module only hosts input adapters.

pub mod lidar;

// Re-export canonical Point3D so `arxos::spatial::Point3D` remains a single type
// (alias to core) for existing external paths during consolidation.
pub use crate::core::spatial::Point3D;
