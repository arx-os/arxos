//! Unit tests for PendingEquipmentManager
//!
//! Tests focus on:
//! - Room assignment when confirming pending equipment
//! - Equipment-to-room linking
//! - Floor/room creation
//! - confirm_pending functionality
//! - Batch operations

use arxos::ar_integration::pending::{
    DetectedEquipmentInfo, DetectionMethod, PendingEquipmentManager, PendingStatus,
};
use arxos::core::Floor;
use arxos::spatial::{BoundingBox3D, Point3D};
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, CoordinateSystemInfo};
use chrono::Utc;
use std::collections::HashMap;

/// Helper to create a minimal BuildingData for testing
fn create_test_building_data() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![CoordinateSystemInfo {
            name: "World".to_string(),
            origin: Point3D::origin(),
            x_axis: Point3D::new(1.0, 0.0, 0.0),
            y_axis: Point3D::new(0.0, 1.0, 0.0),
            z_axis: Point3D::new(0.0, 0.0, 1.0),
            description: Some("Default world coordinate system".to_string()),
        }],
    }
}

/// Helper to create DetectedEquipmentInfo for testing
fn create_detected_equipment(
    name: &str,
    position: Point3D,
    confidence: f64,
) -> DetectedEquipmentInfo {
    DetectedEquipmentInfo {
        name: name.to_string(),
        equipment_type: "HVAC".to_string(),
        position,
        bounding_box: BoundingBox3D {
            min: Point3D {
                x: position.x - 0.5,
                y: position.y - 0.5,
                z: position.z - 0.5,
            },
            max: Point3D {
                x: position.x + 0.5,
                y: position.y + 0.5,
                z: position.z + 0.5,
            },
        },
        confidence,
        detection_method: DetectionMethod::ARKit,
        properties: HashMap::new(),
    }
}

#[test]
fn test_confirm_pending_with_room_assignment() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create a pending equipment item with room name
    let detected = create_detected_equipment("VAV Unit", Point3D::new(10.0, 20.0, 3.0), 0.95);
    let pending_id = manager
        .add_pending_equipment(
            &detected,
            "scan_001",
            1,                         // floor level
            Some("Conference Room A"), // room name
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Confirm the pending equipment
    let equipment_id = manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify equipment was added to floor
    assert_eq!(building_data.floors.len(), 1);
    let floor = &building_data.floors[0];
    assert_eq!(floor.level, 1);
    assert_eq!(floor.equipment.len(), 1);
    assert_eq!(floor.equipment[0].id, equipment_id);
    assert_eq!(floor.equipment[0].name, "VAV Unit");

    // Verify room was created and equipment is linked to it
    assert_eq!(floor.wings[0].rooms.len(), 1);
    let room = &floor.wings[0].rooms[0];
    assert_eq!(room.name, "Conference Room A");
    assert_eq!(room.equipment.len(), 1);
    assert_eq!(room.equipment[0].id, equipment_id);
}

#[test]
fn test_confirm_pending_without_room_name() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create a pending equipment item without room name
    let detected =
        create_detected_equipment("Standalone Unit", Point3D::new(15.0, 25.0, 3.0), 0.90);
    let pending_id = manager
        .add_pending_equipment(
            &detected, "scan_002", 1, None, // no room name
            0.7, None,
        )
        .unwrap()
        .unwrap();

    // Confirm the pending equipment
    let equipment_id = manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify equipment was added to floor
    let floor = &building_data.floors[0];
    assert_eq!(floor.equipment.len(), 1);
    assert_eq!(floor.equipment[0].id, equipment_id);

    // Verify no room was created (since no room_name was provided)
    assert_eq!(floor.wings.iter().flat_map(|w| &w.rooms).count(), 0);
}

#[test]
fn test_confirm_pending_creates_floor_if_missing() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create pending equipment for floor 2 (which doesn't exist yet)
    let detected =
        create_detected_equipment("Second Floor Unit", Point3D::new(10.0, 20.0, 6.0), 0.85);
    let pending_id = manager
        .add_pending_equipment(
            &detected,
            "scan_003",
            2, // floor level 2
            Some("Office 201"),
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Confirm the pending equipment
    manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify floor 2 was created
    assert_eq!(building_data.floors.len(), 1);
    let floor = &building_data.floors[0];
    assert_eq!(floor.level, 2);
    assert_eq!(floor.elevation, Some(6.0)); // 2 * 3.0 = 6.0
}

#[test]
fn test_confirm_pending_creates_room_if_missing() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create pending equipment with a new room name
    let detected = create_detected_equipment("New Room Unit", Point3D::new(10.0, 20.0, 3.0), 0.88);
    let pending_id = manager
        .add_pending_equipment(
            &detected,
            "scan_004",
            1,
            Some("New Room"), // room doesn't exist yet
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Confirm the pending equipment
    manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify room was created
    let floor = &building_data.floors[0];
    assert_eq!(floor.wings[0].rooms.len(), 1);
    assert_eq!(floor.wings[0].rooms[0].name, "New Room");
}

#[test]
fn test_confirm_pending_adds_to_existing_room() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Manually create a floor and room
    building_data.floors.push(Floor {
        id: "floor-1".to_string(),
        name: "Floor 1".to_string(),
        level: 1,
        elevation: Some(0.0),
        bounding_box: None,
        wings: vec![arxos::core::Wing {
            id: "wing-1".to_string(),
            name: "Main Wing".to_string(),
            equipment: vec![],
            properties: HashMap::new(),
            rooms: vec![arxos::core::Room {
                id: "room-conference-a".to_string(),
                name: "Conference Room A".to_string(),
                room_type: arxos::core::RoomType::Other("IFCSPACE".to_string()),
                equipment: vec![],
                spatial_properties: arxos::core::SpatialProperties {
                    position: arxos::core::Position {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                        coordinate_system: "LOCAL".to_string(),
                    },
                    dimensions: arxos::core::Dimensions {
                        width: 10.0,
                        height: 3.0,
                        depth: 10.0,
                    },
                    bounding_box: arxos::core::BoundingBox {
                        min: arxos::core::Position {
                            x: 0.0,
                            y: 0.0,
                            z: 0.0,
                            coordinate_system: "LOCAL".to_string(),
                        },
                        max: arxos::core::Position {
                            x: 10.0,
                            y: 10.0,
                            z: 3.0,
                            coordinate_system: "LOCAL".to_string(),
                        },
                    },
                    coordinate_system: "LOCAL".to_string(),
                },
                properties: HashMap::new(),
                created_at: None,
                updated_at: None,
            }],
        }],
        equipment: vec![],
        properties: HashMap::new(),
    });

    // Create pending equipment for the existing room
    let detected =
        create_detected_equipment("Existing Room Unit", Point3D::new(5.0, 5.0, 1.5), 0.92);
    let pending_id = manager
        .add_pending_equipment(
            &detected,
            "scan_005",
            1,
            Some("Conference Room A"), // existing room
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Confirm the pending equipment
    let equipment_id = manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify equipment was added to existing room
    let floor = &building_data.floors[0];
    assert_eq!(floor.wings[0].rooms.len(), 1); // Still only one room
    assert_eq!(floor.wings[0].rooms[0].equipment.len(), 1);
    assert_eq!(floor.wings[0].rooms[0].equipment[0].id, equipment_id);
}

#[test]
fn test_confirm_pending_multiple_equipment_same_room() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create two pending equipment items for the same room
    let detected1 = create_detected_equipment("Unit 1", Point3D::new(5.0, 5.0, 1.5), 0.90);
    let pending_id1 = manager
        .add_pending_equipment(
            &detected1,
            "scan_006",
            1,
            Some("Conference Room A"),
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    let detected2 = create_detected_equipment("Unit 2", Point3D::new(7.0, 7.0, 1.5), 0.88);
    let pending_id2 = manager
        .add_pending_equipment(
            &detected2,
            "scan_007",
            1,
            Some("Conference Room A"), // same room
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Confirm first pending equipment item
    let equipment_id1 = manager
        .confirm_pending(&pending_id1, &mut building_data)
        .unwrap();

    // Verify first equipment is in room
    let floor = &building_data.floors[0];
    assert_eq!(floor.wings[0].rooms.len(), 1);
    assert_eq!(floor.wings[0].rooms[0].equipment.len(), 1);
    assert!(floor.wings[0].rooms[0]
        .equipment
        .iter()
        .any(|e| e.id == equipment_id1));

    // Confirm second pending equipment item
    let equipment_id2 = manager
        .confirm_pending(&pending_id2, &mut building_data)
        .unwrap();

    // Verify both equipment are in the same room
    let floor = &building_data.floors[0];
    assert_eq!(floor.wings[0].rooms.len(), 1);
    assert_eq!(
        floor.wings[0].rooms[0].equipment.len(),
        2,
        "Room should contain both equipment items"
    );
    assert!(floor.wings[0].rooms[0]
        .equipment
        .iter()
        .any(|e| e.id == equipment_id1));
    assert!(floor.wings[0].rooms[0]
        .equipment
        .iter()
        .any(|e| e.id == equipment_id2));
}

#[test]
fn test_confirm_pending_prevents_duplicate_equipment_in_room() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create and confirm first equipment
    let detected1 = create_detected_equipment("Unit 1", Point3D::new(5.0, 5.0, 1.5), 0.90);
    let pending_id1 = manager
        .add_pending_equipment(
            &detected1,
            "scan_008",
            1,
            Some("Conference Room A"),
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    let equipment_id1 = manager
        .confirm_pending(&pending_id1, &mut building_data)
        .unwrap();

    // Create and confirm second equipment with different scan_id
    let detected2 = create_detected_equipment("Unit 2", Point3D::new(7.0, 7.0, 1.5), 0.88);
    let pending_id2 = manager
        .add_pending_equipment(
            &detected2,
            "scan_009", // different scan_id, so different equipment_id will be generated
            1,
            Some("Conference Room A"),
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Confirm second equipment
    let equipment_id2 = manager
        .confirm_pending(&pending_id2, &mut building_data)
        .unwrap();

    // Verify both equipment are in room (no duplicates due to contains check)
    let floor = &building_data.floors[0];
    assert_eq!(floor.wings[0].rooms[0].equipment.len(), 2);
    // Equipment IDs should be different (different scan_id)
    assert_ne!(equipment_id1, equipment_id2);
    assert!(floor.wings[0].rooms[0]
        .equipment
        .iter()
        .any(|e| e.id == equipment_id1));
    assert!(floor.wings[0].rooms[0]
        .equipment
        .iter()
        .any(|e| e.id == equipment_id2));
}

#[test]
fn test_universal_path_includes_room_when_available() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create pending equipment with room name
    let detected = create_detected_equipment("VAV Unit", Point3D::new(10.0, 20.0, 3.0), 0.95);
    let pending_id = manager
        .add_pending_equipment(
            &detected,
            "scan_009",
            1,
            Some("Conference Room A"),
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Confirm the pending equipment
    manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify universal path includes room
    let floor = &building_data.floors[0];
    let equipment = &floor.equipment[0];
    assert!(equipment.path.contains("ROOM-Conference Room A") || equipment.path.contains("room"));
    assert!(equipment.path.contains("FLOOR-1") || equipment.path.contains("floor"));
    assert!(equipment.path.contains("VAV Unit") || equipment.path.contains("vav"));
}

#[test]
fn test_universal_path_omits_room_when_not_available() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create pending equipment without room name
    let detected =
        create_detected_equipment("Standalone Unit", Point3D::new(15.0, 25.0, 3.0), 0.90);
    let pending_id = manager
        .add_pending_equipment(
            &detected, "scan_010", 1, None, // no room name
            0.7, None,
        )
        .unwrap()
        .unwrap();

    // Confirm the pending equipment
    manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify universal path does NOT include room
    let floor = &building_data.floors[0];
    let equipment = &floor.equipment[0];
    assert!(!equipment.path.contains("ROOM-") && !equipment.path.contains("room"));
    assert!(equipment.path.contains("FLOOR-1") || equipment.path.contains("floor"));
    assert!(equipment.path.contains("Standalone Unit") || equipment.path.contains("standalone"));
}

#[test]
fn test_batch_confirm_with_room_assignment() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create multiple pending equipment items
    let detected1 = create_detected_equipment("Unit 1", Point3D::new(5.0, 5.0, 1.5), 0.90);
    let pending_id1 = manager
        .add_pending_equipment(&detected1, "scan_011", 1, Some("Room A"), 0.7, None)
        .unwrap()
        .unwrap();

    let detected2 = create_detected_equipment("Unit 2", Point3D::new(7.0, 7.0, 1.5), 0.88);
    let pending_id2 = manager
        .add_pending_equipment(
            &detected2,
            "scan_012",
            1,
            Some("Room B"), // different room
            0.7,
            None,
        )
        .unwrap()
        .unwrap();

    // Batch confirm
    let equipment_ids = manager
        .batch_confirm(vec![&pending_id1, &pending_id2], &mut building_data)
        .unwrap();

    assert_eq!(equipment_ids.len(), 2);

    // Verify both rooms were created
    let floor = &building_data.floors[0];
    assert_eq!(floor.wings[0].rooms.len(), 2);
    assert_eq!(floor.equipment.len(), 2);

    // Verify each room has its equipment
    let room_a = floor.wings[0]
        .rooms
        .iter()
        .find(|r| r.name == "Room A")
        .unwrap();
    let room_b = floor.wings[0]
        .rooms
        .iter()
        .find(|r| r.name == "Room B")
        .unwrap();

    assert_eq!(room_a.equipment.len(), 1);
    assert_eq!(room_b.equipment.len(), 1);
    assert!(room_a.equipment.iter().any(|e| e.id == equipment_ids[0]));
    assert!(room_b.equipment.iter().any(|e| e.id == equipment_ids[1]));
}

#[test]
fn test_confirm_pending_updates_status() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Create pending equipment
    let detected = create_detected_equipment("Test Unit", Point3D::new(10.0, 20.0, 3.0), 0.95);
    let pending_id = manager
        .add_pending_equipment(&detected, "scan_013", 1, Some("Test Room"), 0.7, None)
        .unwrap()
        .unwrap();

    // Verify status is Pending
    let pending = manager.get_pending(&pending_id).unwrap();
    assert_eq!(pending.status, PendingStatus::Pending);

    // Confirm the pending equipment
    manager
        .confirm_pending(&pending_id, &mut building_data)
        .unwrap();

    // Verify status is now Confirmed
    let pending = manager.get_pending(&pending_id).unwrap();
    assert_eq!(pending.status, PendingStatus::Confirmed);
}

#[test]
fn test_confirm_pending_not_found_error() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    let mut building_data = create_test_building_data();

    // Try to confirm non-existent pending equipment
    let result = manager.confirm_pending("nonexistent_id", &mut building_data);

    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("not found"));
}
