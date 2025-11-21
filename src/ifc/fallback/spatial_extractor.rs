//! Spatial data extraction from IFC entities
//!
//! Extracts spatial information (position, bounding box) from IFC entities.

use super::types::IFCEntity;
use crate::ifc::geometry::PlacementResolver;
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::core::spatial::SpatialEntity;

/// Extracts spatial data from IFC entities
pub struct SpatialExtractor;

impl SpatialExtractor {
    pub fn new() -> Self {
        Self
    }

    /// Check if an entity type has spatial information
    pub fn is_spatial_entity(&self, entity_type: &str) -> bool {
        matches!(
            entity_type,
            "IFCBUILDINGSTOREY"
                | "IFCSPACE"
                | "IFCFLOWTERMINAL"
                | "IFCBUILDINGELEMENT"
                | "IFCWALL"
                | "IFCDOOR"
                | "IFCWINDOW"
        )
    }

    /// Extract spatial data from an IFC entity
    pub fn extract_spatial_data(
        &self,
        entity: &IFCEntity,
        resolver: &PlacementResolver,
    ) -> Option<SpatialEntity> {
        if !self.is_spatial_entity(&entity.entity_type) {
            return None;
        }

        // Resolve coordinates via placement resolver
        let position = self.resolve_entity_position(entity, resolver);

        let bounding_box = if let Some((min_vec, max_vec)) =
            resolver.compute_entity_bounding_box(entity)
        {
            BoundingBox3D::new(
                Point3D::new(min_vec.x, min_vec.y, min_vec.z),
                Point3D::new(max_vec.x, max_vec.y, max_vec.z),
            )
        } else {
            self.default_bounding_box(&position, &entity.entity_type)
        };

        // Create a SpatialEntity with the extracted data
        let spatial_entity = SpatialEntity::new(
            entity.id.clone(),
            entity.name.clone(),
            entity.entity_type.clone(),
            position,
        )
        .with_bounding_box(bounding_box);

        Some(spatial_entity)
    }

    fn resolve_entity_position(
        &self,
        entity: &IFCEntity,
        resolver: &PlacementResolver,
    ) -> Point3D {
        if let Some(transform) = resolver.resolve_entity_transform(entity) {
            let nalgebra_point = transform.to_point();
            Point3D::new(nalgebra_point.x, nalgebra_point.y, nalgebra_point.z)
        } else {
            self.generate_fallback_coordinates(entity)
        }
    }

    fn default_bounding_box(&self, center: &Point3D, entity_type: &str) -> BoundingBox3D {
        let size = self.get_entity_size(entity_type);
        BoundingBox3D::new(
            Point3D::new(
                center.x - size.0 / 2.0,
                center.y - size.1 / 2.0,
                center.z - size.2 / 2.0,
            ),
            Point3D::new(
                center.x + size.0 / 2.0,
                center.y + size.1 / 2.0,
                center.z + size.2 / 2.0,
            ),
        )
    }

    /// Get default size for entity type
    fn get_entity_size(&self, entity_type: &str) -> (f64, f64, f64) {
        match entity_type {
            "IFCSPACE" => (5.0, 4.0, 3.0),        // Room size
            "IFCFLOWTERMINAL" => (1.0, 1.0, 0.5), // Equipment size
            "IFCWALL" => (0.2, 10.0, 3.0),        // Wall dimensions
            _ => (1.0, 1.0, 1.0),                 // Default size
        }
    }

    /// Generate fallback coordinates when placement parsing fails
    fn generate_fallback_coordinates(&self, entity: &IFCEntity) -> Point3D {
        // Generate deterministic coordinates based on entity properties
        let id_hash = self.hash_string(&entity.id);
        let name_hash = self.hash_string(&entity.name);

        // Generate coordinates based on entity type and properties
        match entity.entity_type.as_str() {
            "IFCSPACE" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.1,
                )
            }
            "IFCFLOWTERMINAL" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5,
                )
            }
            "IFCWALL" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5,
                )
            }
            "IFCDOOR" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 0.9,
                )
            }
            "IFCWINDOW" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.2,
                )
            }
            "IFCCOLUMN" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.5,
                )
            }
            "IFCSLAB" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height,
                )
            }
            "IFCBEAM" => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 2.7,
                )
            }
            _ => {
                let floor_height = 3.0;
                let floor = (id_hash % 5) as f64;
                Point3D::new(
                    (id_hash % 1000) as f64 / 10.0,
                    (name_hash % 800) as f64 / 10.0,
                    floor * floor_height + 1.0,
                )
            }
        }
    }

    /// Generate a simple hash from a string for deterministic positioning
    fn hash_string(&self, s: &str) -> u64 {
        let mut hash = 5381u64;
        for byte in s.bytes() {
            hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
        }
        hash
    }
}

impl Default for SpatialExtractor {
    fn default() -> Self {
        Self::new()
    }
}
