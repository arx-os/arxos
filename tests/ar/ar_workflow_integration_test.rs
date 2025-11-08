//! Integration tests for AR workflow - AR scan to pending equipment to confirmed equipment

use arxos::ar_integration::pending::{
    DetectedEquipmentInfo, DetectionMethod, PendingEquipmentManager,
};
use arxos::ar_integration::processing::{
    process_ar_scan_to_pending, validate_ar_scan_data, ARScanData, DetectedEquipmentData,
};
use arxos::core::Floor;
use arxos::spatial::{BoundingBox3D, Point3D};
use arxos::yaml::{BuildingData, BuildingInfo};
use std::collections::HashMap;
use std::path::PathBuf;
use tempfile::TempDir;

#[test]
fn test_ar_workflow_complete() {
    // Phase 1: Create AR scan data
    let ar_scan = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301".to_string(),
                equipment_type: "VAV".to_string(),
                position: Point3D {
                    x: 10.0,
                    y: 20.0,
                    z: 3.0,
                },
                confidence: 0.95,
                detection_method: Some("ARKit".to_string()),
            },
            DetectedEquipmentData {
                name: "Thermostat-A".to_string(),
                equipment_type: "Thermostat".to_string(),
                position: Point3D {
                    x: 12.0,
                    y: 22.0,
                    z: 3.0,
                },
                confidence: 0.88,
                detection_method: Some("ARKit".to_string()),
            },
        ],
        floor_level: Some(3),
        room_name: Some("Room 301".to_string()),
    };

    // Phase 2: Validate AR scan data
    let validation_result = validate_ar_scan_data(&ar_scan);
    assert!(validation_result.is_ok(), "AR scan validation should pass");

    // Phase 3: Process AR scan to pending equipment
    let temp_dir = TempDir::new().expect("Should create temp directory");
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let original_dir = std::env::current_dir().unwrap_or_else(|_| repo_root.clone());
    std::env::set_current_dir(temp_dir.path()).unwrap();

    let pending_ids = process_ar_scan_to_pending(&ar_scan, "test_building", 0.7, None)
        .expect("Should create pending equipment");

    assert_eq!(
        pending_ids.len(),
        2,
        "Should create 2 pending equipment items"
    );

    // Phase 4: Create building data and pending manager
    let building_data = create_test_building_data();

    let storage_file = temp_dir.path().join("test_building_pending.json");
    let mut manager = PendingEquipmentManager::new("test_building".to_string());
    manager.set_storage_path(storage_file.clone());

    // Manually add detected equipment for testing
    let detected_info = DetectedEquipmentInfo {
        name: "VAV-301".to_string(),
        equipment_type: "VAV".to_string(),
        position: Point3D {
            x: 10.0,
            y: 20.0,
            z: 3.0,
        },
        bounding_box: BoundingBox3D {
            min: Point3D {
                x: 9.5,
                y: 19.5,
                z: 2.5,
            },
            max: Point3D {
                x: 10.5,
                y: 20.5,
                z: 3.5,
            },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::ARKit,
        properties: HashMap::new(),
    };

    let pending_id = manager
        .add_pending_equipment(&detected_info, "scan_1", 3, Some("Room 301"), 0.7, None)
        .expect("Should add pending equipment")
        .expect("Should return pending ID");

    // Phase 5: List pending equipment
    let pending_list = manager.list_pending();
    assert_eq!(pending_list.len(), 1, "Should have 1 pending item");
    assert_eq!(pending_list[0].name, "VAV-301");

    // Phase 6: Save to storage
    manager.save_to_storage().expect("Should save to storage");

    assert!(storage_file.exists(), "Storage file should be created");

    // Phase 7: Load from storage
    let mut manager2 = PendingEquipmentManager::new("test_building".to_string());
    manager2
        .load_from_storage(&storage_file)
        .expect("Should load from storage");

    let loaded_pending = manager2.list_pending();
    assert_eq!(loaded_pending.len(), 1, "Should load 1 pending item");

    // Phase 8: Confirm pending equipment
    let mut building_data_mut = building_data.clone();
    let equipment_id = manager2
        .confirm_pending(&pending_id, &mut building_data_mut)
        .expect("Should confirm pending equipment");

    assert!(!equipment_id.is_empty(), "Should return equipment ID");

    // Phase 9: Verify equipment was added
    let floor = building_data_mut
        .floors
        .iter()
        .find(|f| f.level == 3)
        .unwrap();
    let equipment = floor
        .equipment
        .iter()
        .find(|e| e.name == "VAV-301")
        .unwrap();

    assert_eq!(equipment.name, "VAV-301");
    // EquipmentStatus doesn't implement PartialEq, use debug string comparison
    // Check health_status instead of old EquipmentStatus
    assert!(equipment.health_status.is_some());
    // Compare position coordinates individually
    assert_eq!(equipment.position.x, 10.0);
    assert_eq!(equipment.position.y, 20.0);
    assert_eq!(equipment.position.z, 3.0);

    // Phase 10: Verify pending item is marked as confirmed
    let confirmed_pending = manager2.list_pending();
    assert!(
        confirmed_pending.is_empty(),
        "Confirmed items should not appear in pending list"
    );

    // Cleanup working directory
    if std::env::set_current_dir(&original_dir).is_err() {
        std::env::set_current_dir(repo_root).unwrap();
    }
}

#[test]
fn test_ar_workflow_with_low_confidence() {
    // Test that low-confidence equipment is filtered out
    let ar_scan = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "High-Confidence".to_string(),
                equipment_type: "Equipment".to_string(),
                position: Point3D {
                    x: 10.0,
                    y: 20.0,
                    z: 3.0,
                },
                confidence: 0.95,
                detection_method: Some("ARKit".to_string()),
            },
            DetectedEquipmentData {
                name: "Low-Confidence".to_string(),
                equipment_type: "Equipment".to_string(),
                position: Point3D {
                    x: 12.0,
                    y: 22.0,
                    z: 3.0,
                },
                confidence: 0.50,
                detection_method: Some("ARKit".to_string()),
            },
        ],
        floor_level: Some(1),
        room_name: Some("Test Room".to_string()),
    };

    let temp_dir = TempDir::new().expect("Should create temp directory");
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();

    let pending_ids = process_ar_scan_to_pending(&ar_scan, "test_building", 0.7, None)
        .expect("Should process AR scan");

    assert_eq!(
        pending_ids.len(),
        1,
        "Should only create 1 pending item (high confidence)"
    );

    std::env::set_current_dir(original_dir).unwrap();
}

#[test]
fn test_ar_workflow_rejection() {
    let mut manager = PendingEquipmentManager::new("test_building".to_string());

    let detected_info = DetectedEquipmentInfo {
        name: "Bad-Equipment".to_string(),
        equipment_type: "Unknown".to_string(),
        position: Point3D {
            x: 10.0,
            y: 20.0,
            z: 3.0,
        },
        bounding_box: BoundingBox3D {
            min: Point3D {
                x: 9.5,
                y: 19.5,
                z: 2.5,
            },
            max: Point3D {
                x: 10.5,
                y: 20.5,
                z: 3.5,
            },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::Manual,
        properties: HashMap::new(),
    };

    let pending_id = manager
        .add_pending_equipment(&detected_info, "scan_1", 3, None, 0.7, None)
        .expect("Should add pending equipment")
        .expect("Should return pending ID");

    // Reject the pending equipment
    manager
        .reject_pending(&pending_id)
        .expect("Should reject pending equipment");

    // Verify it's not in pending list
    let pending_list = manager.list_pending();
    assert!(
        pending_list.is_empty(),
        "Rejected item should not appear in pending list"
    );
}

fn create_test_building_data() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        floors: vec![Floor {
            id: "floor-3".to_string(),
            name: "Floor 3".to_string(),
            level: 3,
            elevation: Some(9.0),
            bounding_box: None,
            wings: vec![],
            equipment: vec![],
            properties: HashMap::new(),
        }],
        metadata: arxos::yaml::BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            tags: vec![],
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "default".to_string(),
            units: "meters".to_string(),
        },
        coordinate_systems: vec![],
    }
}
