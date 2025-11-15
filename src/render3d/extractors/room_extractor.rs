//! Room data extraction for 3D rendering
//!
//! Converts room data from all floors and wings into 3D representations
//! with spatial properties and equipment references.

use crate::render3d::types::Room3D;
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::yaml::BuildingData;
use std::sync::Arc;

/// Extract 3D room representations from building data
///
/// Extracts rooms from all wings across all floors, converting them
/// into 3D representations with spatial properties.
///
/// # Arguments
///
/// * `building_data` - Source building data containing rooms
///
/// # Returns
///
/// Vector of Room3D objects with spatial properties and equipment references
///
/// # Spatial Properties
///
/// - Position: Center point of the room
/// - Bounding box: 3D extents of the room
/// - Equipment: References to equipment IDs within the room
pub fn extract_rooms_3d(building_data: &BuildingData) -> Vec<Room3D> {
    let mut rooms_3d = Vec::new();

    for floor in &building_data.building.floors {
        for wing in &floor.wings {
            for room in &wing.rooms {
                rooms_3d.push(Room3D {
                    id: Arc::new(room.id.clone()),
                    name: Arc::new(room.name.clone()),
                    room_type: room.room_type.clone(),
                    position: Point3D {
                        x: room.spatial_properties.position.x,
                        y: room.spatial_properties.position.y,
                        z: room.spatial_properties.position.z,
                    },
                    bounding_box: BoundingBox3D {
                        min: Point3D {
                            x: room.spatial_properties.bounding_box.min.x,
                            y: room.spatial_properties.bounding_box.min.y,
                            z: room.spatial_properties.bounding_box.min.z,
                        },
                        max: Point3D {
                            x: room.spatial_properties.bounding_box.max.x,
                            y: room.spatial_properties.bounding_box.max.y,
                            z: room.spatial_properties.bounding_box.max.z,
                        },
                    },
                    floor_level: floor.level,
                    equipment: room
                        .equipment
                        .iter()
                        .map(|e| Arc::new(e.id.clone()))
                        .collect(),
                });
            }
        }
    }

    rooms_3d
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Equipment, EquipmentStatus, EquipmentType, Floor, Room, SpatialProperties, Wing};

    #[test]
    fn test_extract_rooms_3d() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);
        let mut wing = Wing::new("Wing A".to_string());

        let mut room = Room::new("Room 101".to_string());
        room.spatial_properties = SpatialProperties {
            position: crate::core::spatial::Point3D::new(10.0, 10.0, 0.0),
            bounding_box: crate::core::spatial::BoundingBox3D::new(
                crate::core::spatial::Point3D::new(5.0, 5.0, 0.0),
                crate::core::spatial::Point3D::new(15.0, 15.0, 3.0),
            ),
        };

        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let rooms = extract_rooms_3d(&building_data);

        assert_eq!(rooms.len(), 1);
        assert_eq!(*rooms[0].name, "Room 101");
        assert_eq!(rooms[0].position.x, 10.0);
        assert_eq!(rooms[0].position.y, 10.0);
    }

    #[test]
    fn test_room_equipment_references() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);
        let mut wing = Wing::new("Wing A".to_string());
        let mut room = Room::new("Room 101".to_string());

        room.spatial_properties = SpatialProperties {
            position: crate::core::spatial::Point3D::new(10.0, 10.0, 0.0),
            bounding_box: crate::core::spatial::BoundingBox3D::new(
                crate::core::spatial::Point3D::new(5.0, 5.0, 0.0),
                crate::core::spatial::Point3D::new(15.0, 15.0, 3.0),
            ),
        };

        // Add equipment to room
        let mut equipment1 = Equipment::new("AC-1".to_string(), EquipmentType::HVAC);
        equipment1.position = crate::core::spatial::Point3D::new(12.0, 12.0, 2.0);

        let mut equipment2 = Equipment::new("Light-1".to_string(), EquipmentType::Electrical);
        equipment2.position = crate::core::spatial::Point3D::new(8.0, 8.0, 2.5);

        room.equipment.push(equipment1);
        room.equipment.push(equipment2);

        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let rooms = extract_rooms_3d(&building_data);

        assert_eq!(rooms[0].equipment.len(), 2);
        assert_eq!(*rooms[0].equipment[0], "AC-1");
        assert_eq!(*rooms[0].equipment[1], "Light-1");
    }

    #[test]
    fn test_room_bounding_box() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);
        let mut wing = Wing::new("Wing A".to_string());
        let mut room = Room::new("Room 101".to_string());

        room.spatial_properties = SpatialProperties {
            position: crate::core::spatial::Point3D::new(10.0, 10.0, 0.0),
            bounding_box: crate::core::spatial::BoundingBox3D::new(
                crate::core::spatial::Point3D::new(5.0, 5.0, 0.0),
                crate::core::spatial::Point3D::new(15.0, 15.0, 3.0),
            ),
        };

        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let rooms = extract_rooms_3d(&building_data);

        assert_eq!(rooms[0].bounding_box.min.x, 5.0);
        assert_eq!(rooms[0].bounding_box.min.y, 5.0);
        assert_eq!(rooms[0].bounding_box.min.z, 0.0);
        assert_eq!(rooms[0].bounding_box.max.x, 15.0);
        assert_eq!(rooms[0].bounding_box.max.y, 15.0);
        assert_eq!(rooms[0].bounding_box.max.z, 3.0);
    }
}
