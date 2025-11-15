//! Equipment data extraction for 3D rendering
//!
//! Extracts equipment from both floor-level and room-level locations,
//! creating unified 3D representations with positions and bounding boxes.

use crate::render3d::types::Equipment3D;
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::yaml::BuildingData;
use std::sync::Arc;

/// Extract 3D equipment representations from building data
///
/// Extracts equipment from multiple sources:
/// - Floor-level equipment (not in rooms)
/// - Room-level equipment (within wings)
///
/// # Arguments
///
/// * `building_data` - Source building data containing equipment
///
/// # Returns
///
/// Vector of Equipment3D objects with computed positions and bounding boxes
///
/// # Bounding Box Calculation
///
/// Equipment bounding boxes are computed as ±0.5 units around the equipment position,
/// creating a 1x1x1 unit cube for standard equipment visualization.
pub fn extract_equipment_3d(building_data: &BuildingData) -> Vec<Equipment3D> {
    let mut equipment_3d = Vec::new();

    for floor in &building_data.building.floors {
        // Extract floor-level equipment
        for equipment in &floor.equipment {
            equipment_3d.push(Equipment3D {
                id: Arc::new(equipment.id.clone()),
                name: Arc::new(equipment.name.clone()),
                equipment_type: equipment.equipment_type.clone(),
                status: equipment.status,
                position: Point3D {
                    x: equipment.position.x,
                    y: equipment.position.y,
                    z: equipment.position.z,
                },
                bounding_box: BoundingBox3D {
                    min: Point3D {
                        x: equipment.position.x - 0.5,
                        y: equipment.position.y - 0.5,
                        z: equipment.position.z - 0.5,
                    },
                    max: Point3D {
                        x: equipment.position.x + 0.5,
                        y: equipment.position.y + 0.5,
                        z: equipment.position.z + 0.5,
                    },
                },
                floor_level: floor.level,
                room_id: equipment
                    .room_id
                    .as_ref()
                    .map(|room_id| Arc::new(room_id.clone())),
                connections: Vec::new(),
                spatial_relationships: None,
                nearest_entity_distance: None,
            });
        }

        // Extract equipment from rooms within wings
        for wing in &floor.wings {
            for room in &wing.rooms {
                for equipment in &room.equipment {
                    equipment_3d.push(Equipment3D {
                        id: Arc::new(equipment.id.clone()),
                        name: Arc::new(equipment.name.clone()),
                        equipment_type: equipment.equipment_type.clone(),
                        status: equipment.status,
                        position: Point3D {
                            x: equipment.position.x,
                            y: equipment.position.y,
                            z: equipment.position.z,
                        },
                        bounding_box: BoundingBox3D {
                            min: Point3D {
                                x: equipment.position.x - 0.5,
                                y: equipment.position.y - 0.5,
                                z: equipment.position.z - 0.5,
                            },
                            max: Point3D {
                                x: equipment.position.x + 0.5,
                                y: equipment.position.y + 0.5,
                                z: equipment.position.z + 0.5,
                            },
                        },
                        floor_level: floor.level,
                        room_id: Some(Arc::new(room.id.clone())),
                        connections: Vec::new(),
                        spatial_relationships: None,
                        nearest_entity_distance: None,
                    });
                }
            }
        }
    }

    equipment_3d
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Equipment, EquipmentStatus, EquipmentType, Floor, Room, SpatialProperties, Wing};

    #[test]
    fn test_extract_floor_level_equipment() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);

        let mut equipment = Equipment::new("AC-1".to_string(), EquipmentType::HVAC);
        equipment.position = crate::core::spatial::Point3D::new(10.0, 10.0, 1.5);
        equipment.status = EquipmentStatus::Healthy;

        floor.equipment.push(equipment);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let extracted = extract_equipment_3d(&building_data);

        assert_eq!(extracted.len(), 1);
        assert_eq!(*extracted[0].name, "AC-1");
        assert_eq!(extracted[0].position.x, 10.0);
        assert_eq!(extracted[0].position.y, 10.0);
        assert_eq!(extracted[0].position.z, 1.5);
    }

    #[test]
    fn test_extract_room_level_equipment() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);
        let mut wing = Wing::new("Wing A".to_string());
        let mut room = Room::new("Room 101".to_string());

        let mut equipment = Equipment::new("Light-1".to_string(), EquipmentType::Electrical);
        equipment.position = crate::core::spatial::Point3D::new(12.0, 12.0, 2.0);
        equipment.status = EquipmentStatus::Healthy;

        room.equipment.push(equipment);
        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let extracted = extract_equipment_3d(&building_data);

        assert_eq!(extracted.len(), 1);
        assert_eq!(*extracted[0].name, "Light-1");
        assert_eq!(extracted[0].equipment_type, EquipmentType::Electrical);
        assert!(extracted[0].room_id.is_some());
    }

    #[test]
    fn test_equipment_bounding_box() {
        let mut building = Building::default();
        let mut floor = Floor::new("Floor 1".to_string(), 0);

        let mut equipment = Equipment::new("AC-1".to_string(), EquipmentType::HVAC);
        equipment.position = crate::core::spatial::Point3D::new(10.0, 10.0, 1.5);

        floor.equipment.push(equipment);
        building.add_floor(floor);

        let building_data = crate::yaml::BuildingData {
            building,
            equipment: Vec::new(),
        };

        let extracted = extract_equipment_3d(&building_data);

        // Bounding box should be ±0.5 around position
        assert_eq!(extracted[0].bounding_box.min.x, 9.5);
        assert_eq!(extracted[0].bounding_box.min.y, 9.5);
        assert_eq!(extracted[0].bounding_box.min.z, 1.0);
        assert_eq!(extracted[0].bounding_box.max.x, 10.5);
        assert_eq!(extracted[0].bounding_box.max.y, 10.5);
        assert_eq!(extracted[0].bounding_box.max.z, 2.0);
    }
}
