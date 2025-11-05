// Spatial data processing for ArxOS
use nalgebra::Point3;

pub mod types;
pub mod grid;
pub use types::*;
pub use grid::{GridCoordinate, GridSystem};

/// Spatial engine for geometric operations
pub struct SpatialEngine {
    // Spatial processing engine
}

impl Default for SpatialEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl SpatialEngine {
    pub fn new() -> Self {
        Self {}
    }

    /// Calculate distance between two 3D points
    pub fn calculate_distance(&self, p1: Point3<f64>, p2: Point3<f64>) -> f64 {
        let dx = p1.x - p2.x;
        let dy = p1.y - p2.y;
        let dz = p1.z - p2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    /// Find equipment within a given radius of a point
    pub fn find_equipment_within_radius<'a>(
        &self,
        center: Point3<f64>,
        radius: f64,
        equipment: &'a [SpatialEntity],
    ) -> Vec<&'a SpatialEntity> {
        equipment
            .iter()
            .filter(|entity| {
                let entity_point = Point3::new(entity.position.x, entity.position.y, entity.position.z);
                self.calculate_distance(center, entity_point) <= radius
            })
            .collect()
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

    /// Calculate bounding box for a collection of spatial entities
    pub fn calculate_global_bounding_box(&self, entities: &[SpatialEntity]) -> Option<BoundingBox3D> {
        if entities.is_empty() {
            return None;
        }

        let points: Vec<Point3D> = entities.iter()
            .flat_map(|entity| vec![entity.bounding_box.min, entity.bounding_box.max])
            .collect();

        BoundingBox3D::from_points(&points)
    }
}
