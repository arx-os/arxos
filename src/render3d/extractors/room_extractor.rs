//! Room data extraction for 3D rendering
//!
//! Converts room data from all floors and wings into 3D representations
//! with spatial properties and equipment references.

use crate::render3d::types::Room3D;
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::core::Building;
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
pub fn extract_rooms_3d(building: &Building) -> Vec<Room3D> {
    let mut rooms_3d = Vec::new();

    for floor in &building.floors {
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
    use crate::core::{Building, Equipment, EquipmentStatus, EquipmentType, Floor, Room, RoomType, SpatialProperties, Wing};

    fn create_test_spatial_properties() -> SpatialProperties {
        SpatialProperties {
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
        }
    }

    #[test]
    fn test_extract_rooms_3d() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);
        let mut wing = Wing::new("Wing A".to_string());

        let mut room = Room::new("Room 101".to_string(), RoomType::Office);
        room.spatial_properties = create_test_spatial_properties();

        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        let rooms = extract_rooms_3d(&building);

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
        let mut room = Room::new("Room 101".to_string(), RoomType::Office);

        room.spatial_properties = create_test_spatial_properties();

        // Add equipment to room
        let mut equipment1 = Equipment::new(
            "AC-1".to_string(),
            "/TEST_BUILDING/FLOOR_1/WING_A/ROOM_101/AC-1".to_string(),
            EquipmentType::HVAC,
        );
        equipment1.position = crate::core::Position {
            x: 12.0,
            y: 12.0,
            z: 2.0,
            coordinate_system: "LOCAL".to_string(),
        };

        let mut equipment2 = Equipment::new(
            "Light-1".to_string(),
            "/TEST_BUILDING/FLOOR_1/WING_A/ROOM_101/Light-1".to_string(),
            EquipmentType::Electrical,
        );
        equipment2.position = crate::core::Position {
            x: 8.0,
            y: 8.0,
            z: 2.5,
            coordinate_system: "LOCAL".to_string(),
        };

        let eq1_id = equipment1.id.clone();
        let eq2_id = equipment2.id.clone();

        room.equipment.push(equipment1);
        room.equipment.push(equipment2);

        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        let rooms = extract_rooms_3d(&building);

        assert_eq!(rooms[0].equipment.len(), 2);
        assert_eq!(*rooms[0].equipment[0], eq1_id);
        assert_eq!(*rooms[0].equipment[1], eq2_id);
    }

    #[test]
    fn test_room_bounding_box() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);
        let mut wing = Wing::new("Wing A".to_string());
        let mut room = Room::new("Room 101".to_string(), RoomType::Office);

        room.spatial_properties = create_test_spatial_properties();

        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        let rooms = extract_rooms_3d(&building);

        assert_eq!(rooms[0].bounding_box.min.x, 5.0);
        assert_eq!(rooms[0].bounding_box.min.y, 5.0);
        assert_eq!(rooms[0].bounding_box.min.z, 0.0);
        assert_eq!(rooms[0].bounding_box.max.x, 15.0);
        assert_eq!(rooms[0].bounding_box.max.y, 15.0);
        assert_eq!(rooms[0].bounding_box.max.z, 3.0);
    }
}
