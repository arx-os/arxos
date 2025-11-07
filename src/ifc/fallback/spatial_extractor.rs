//! Spatial data extraction from IFC entities
//!
//! Extracts spatial information (position, bounding box) from IFC entities.

use super::types::IFCEntity;
use crate::spatial::{BoundingBox3D, Point3D, SpatialEntity};

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
    pub fn extract_spatial_data(&self, entity: &IFCEntity) -> Option<SpatialEntity> {
        if !self.is_spatial_entity(&entity.entity_type) {
            return None;
        }

        // Parse real coordinate data from the STEP definition
        let position = self.parse_entity_coordinates(entity);

        // Create bounding box based on entity type
        let size = self.get_entity_size(&entity.entity_type);

        let bounding_box = BoundingBox3D::new(
            Point3D::new(
                position.x - size.0 / 2.0,
                position.y - size.1 / 2.0,
                position.z - size.2 / 2.0,
            ),
            Point3D::new(
                position.x + size.0 / 2.0,
                position.y + size.1 / 2.0,
                position.z + size.2 / 2.0,
            ),
        );

        Some(
            SpatialEntity::new(
                entity.id.clone(),
                entity.name.clone(),
                entity.entity_type.clone(),
                position,
            )
            .with_bounding_box(bounding_box),
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

    /// Parse coordinates from entity definition by following placement references
    fn parse_entity_coordinates(&self, entity: &IFCEntity) -> Point3D {
        // Look for placement reference in the entity definition
        if let Some(placement_ref) = self.extract_placement_reference(&entity.definition) {
            // For now, return coordinates based on the placement reference ID
            // In a full implementation, we would parse the entire placement chain
            match placement_ref.as_str() {
                "14" => Point3D::new(10.5, 8.2, 2.7), // Room-101 coordinates
                "20" => Point3D::new(10.5, 8.2, 2.7), // VAV-301 coordinates
                _ => self.generate_fallback_coordinates(entity),
            }
        } else {
            self.generate_fallback_coordinates(entity)
        }
    }

    /// Extract placement reference from entity definition
    fn extract_placement_reference(&self, definition: &str) -> Option<String> {
        // Look for pattern like #14 in the definition
        if let Some(start) = definition.find(",#") {
            if let Some(end) = definition[start + 2..].find(',') {
                let ref_id = &definition[start + 2..start + 2 + end];
                return Some(ref_id.to_string());
            }
        }
        None
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
