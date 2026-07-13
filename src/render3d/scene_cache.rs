//! Scene caching for 3D rendering
//!
//! Provides efficient caching of building scene data to avoid repeated extraction
//! and transformation operations during rendering.

use super::extractors::{extract_equipment_3d, extract_floors_3d, extract_rooms_3d};
use super::types::*;
use crate::core::Building;
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
    /// Create a new scene cache from building
    ///
    /// Extracts and caches all 3D scene elements for efficient rendering.
    ///
    /// # Arguments
    ///
    /// * `building` - Source building to cache
    ///
    /// # Returns
    ///
    /// A new SceneCache with all scene elements pre-processed
    pub fn new(building: &Building) -> Self {
        Self {
            building_name: Arc::new(building.name.clone()),
            floors: extract_floors_3d(building),
            equipment: extract_equipment_3d(building),
            rooms: extract_rooms_3d(building),
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
    use crate::core::{Building, Equipment, Floor, Room, Wing};
    use crate::core::{
        EquipmentHealthStatus, EquipmentStatus, EquipmentType, RoomType, SpatialProperties,
    };

    fn create_test_building() -> Building {
        let mut building = Building::default();
        building.name = "Test Building".to_string();

        let mut floor = Floor::new("Floor 1".to_string(), 0);
        floor.elevation = Some(0.0);

        let mut wing = Wing::new("Wing A".to_string());

        let mut room = Room::new("Room 101".to_string(), RoomType::Office);
        room.spatial_properties = SpatialProperties {
            position: crate::core::Position {
                x: 10.0,
                y: 10.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            },
            dimensions: crate::core::Dimensions {
                width: 10.0,
                height: 3.0,
                depth: 10.0,
            },
            bounding_box: crate::core::BoundingBox {
                min: crate::core::Position {
                    x: 5.0,
                    y: 5.0,
                    z: 0.0,
                    coordinate_system: "building_local".to_string(),
                },
                max: crate::core::Position {
                    x: 15.0,
                    y: 15.0,
                    z: 3.0,
                    coordinate_system: "building_local".to_string(),
                },
            },
            mesh: None,
            coordinate_system: "building_local".to_string(),
        };

        let mut equipment = Equipment::new(
            "AC-1".to_string(),
            "US/HQ/Main/test_facility/Floor 1/Wing A/Room 101/AC-1".to_string(),
            EquipmentType::HVAC,
        );
        equipment.position = crate::core::Position {
            x: 12.0,
            y: 12.0,
            z: 2.0,
            coordinate_system: "building_local".to_string(),
        };
        equipment.status = EquipmentStatus::Active;
        equipment.health_status = Some(EquipmentHealthStatus::Healthy);

        room.equipment.push(equipment);
        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        building
    }

    #[test]
    fn test_scene_cache_creation() {
        let building = create_test_building();
        let cache = SceneCache::new(&building);

        assert_eq!(cache.building_name(), "Test Building");
        assert_eq!(cache.floors().len(), 1);
        assert_eq!(cache.rooms().len(), 1);
        assert_eq!(cache.equipment().len(), 1);
    }
}
