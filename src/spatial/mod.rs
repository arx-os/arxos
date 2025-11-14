//! Spatial data processing for ArxOS

pub mod grid;
pub mod types;

pub use grid::{GridCoordinate, GridSystem};
pub use types::*;

// Re-export grid address utilities

/// Spatial engine for geometric operations
pub struct SpatialEngine {
    /// Grid system configuration
    pub grid_system: GridSystem,
}

impl Default for SpatialEngine {
    fn default() -> Self {
        Self {
            grid_system: GridSystem::default(),
        }
    }
}

impl SpatialEngine {
    /// Create a new spatial engine
    pub fn new(grid_system: GridSystem) -> Self {
        Self { grid_system }
    }

    /// Transform coordinates between coordinate systems
    pub fn transform_coordinates(
        &self,
        point: Point3D,
        from_system: &CoordinateSystem,
        to_system: &CoordinateSystem,
    ) -> Point3D {
        // For now, simple translation (can be enhanced later)
        let dx = to_system.origin.x - from_system.origin.x;
        let dy = to_system.origin.y - from_system.origin.y;
        let dz = to_system.origin.z - from_system.origin.z;

        Point3D::new(point.x + dx, point.y + dy, point.z + dz)
    }
}