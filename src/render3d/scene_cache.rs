//! Scene caching for 3D rendering
//!
//! Provides efficient caching of building scene data to avoid repeated extraction
//! and transformation operations during rendering.

use super::extractors::{extract_equipment_3d, extract_floors_3d, extract_rooms_3d};
use super::types::*;
use crate::yaml::BuildingData;
use std::sync::Arc;

/// Cache of 3D scene data extracted from building data
///
/// Stores pre-processed 3D representations of floors, equipment, and rooms
/// to optimize rendering performance.
pub struct SceneCache {
    pub(super) building_name: Arc<String>,
    pub(super) floors: Vec<Floor3D>,
    pub(super) equipment: Vec<Equipment3D>,
    pub(super) rooms: Vec<Room3D>,
}

impl SceneCache {
    /// Create a new scene cache from building data
    ///
    /// Extracts and caches all 3D scene elements for efficient rendering.
    ///
    /// # Arguments
    ///
    /// * `building_data` - Source building data to cache
    ///
    /// # Returns
    ///
    /// A new SceneCache with all scene elements pre-processed
    pub fn new(building_data: &BuildingData) -> Self {
        Self {
            building_name: Arc::new(building_data.building.name.clone()),
            floors: extract_floors_3d(building_data),
            equipment: extract_equipment_3d(building_data),
            rooms: extract_rooms_3d(building_data),
        }
    }

    /// Get cached floors
    pub fn floors(&self) -> &[Floor3D] {
        &self.floors
    }

    /// Get cached equipment
    pub fn equipment(&self) -> &[Equipment3D] {
        &self.equipment
    }

    /// Get cached rooms
    pub fn rooms(&self) -> &[Room3D] {
        &self.rooms
    }

    /// Get building name
    pub fn building_name(&self) -> &str {
        &self.building_name
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor, Wing, Room, Equipment};
    use crate::core::{SpatialProperties, EquipmentType, EquipmentStatus};

    fn create_test_building_data() -> BuildingData {
        let mut building = Building::default();
        building.name = "Test Building".to_string();

        let mut floor = Floor::new("Floor 1".to_string(), 0);
        floor.elevation = Some(0.0);

        let mut wing = Wing::new("Wing A".to_string());

        let mut room = Room::new("Room 101".to_string());
        room.spatial_properties = SpatialProperties {
            position: crate::core::spatial::Point3D::new(10.0, 10.0, 0.0),
            bounding_box: crate::core::spatial::BoundingBox3D::new(
                crate::core::spatial::Point3D::new(5.0, 5.0, 0.0),
                crate::core::spatial::Point3D::new(15.0, 15.0, 3.0),
            ),
        };

        let mut equipment = Equipment::new("AC-1".to_string(), EquipmentType::HVAC);
        equipment.position = crate::core::spatial::Point3D::new(12.0, 12.0, 2.0);
        equipment.status = EquipmentStatus::Healthy;

        room.equipment.push(equipment);
        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        BuildingData {
            building,
            equipment: Vec::new(),
        }
    }

    #[test]
    fn test_scene_cache_creation() {
        let building_data = create_test_building_data();
        let cache = SceneCache::new(&building_data);

        assert_eq!(cache.building_name(), "Test Building");
        assert_eq!(cache.floors().len(), 1);
        assert_eq!(cache.rooms().len(), 1);
        assert_eq!(cache.equipment().len(), 1);
    }

}
