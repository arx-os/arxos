//! Tests for spatial operations command handlers

use arxos::core::{spatial_query, validate_spatial, SpatialValidationResult};
use arxos::persistence::PersistenceManager;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData, EquipmentData};
use arxos::spatial::{Point3D, BoundingBox3D};
use tempfile::TempDir;
use std::fs;
use std::collections::HashMap;

/// Helper function to create a test building with rooms and equipment
fn create_test_building_data() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: Some("Test building for spatial operations".to_string()),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "ArxOS v2.0".to_string(),
            total_entities: 4,
            spatial_entities: 4,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![FloorData {
            id: "floor-1".to_string(),
            name: "Floor 1".to_string(),
            level: 1,
            elevation: 0.0,
            rooms: vec![
                RoomData {
                    id: "room-1".to_string(),
                    name: "Room A".to_string(),
                    room_type: "Office".to_string(),
                    area: Some(100.0),
                    volume: Some(300.0),
                    position: Point3D::new(0.0, 0.0, 0.0),
                    bounding_box: BoundingBox3D {
                        min: Point3D::new(-5.0, -5.0, 0.0),
                        max: Point3D::new(5.0, 5.0, 3.0),
                    },
                    equipment: vec![],
                    properties: HashMap::new(),
                },
                RoomData {
                    id: "room-2".to_string(),
                    name: "Room B".to_string(),
                    room_type: "Classroom".to_string(),
                    area: Some(200.0),
                    volume: Some(600.0),
                    position: Point3D::new(20.0, 0.0, 0.0),
                    bounding_box: BoundingBox3D {
                        min: Point3D::new(15.0, -10.0, 0.0),
                        max: Point3D::new(25.0, 10.0, 3.0),
                    },
                    equipment: vec![],
                    properties: HashMap::new(),
                },
            ],
            equipment: vec![
                EquipmentData {
                    id: "equip-1".to_string(),
                    name: "HVAC Unit 1".to_string(),
                    equipment_type: "HVAC".to_string(),
                    system_type: "HVAC".to_string(),
                    position: Point3D::new(10.0, 10.0, 1.5),
                    bounding_box: BoundingBox3D {
                        min: Point3D::new(9.5, 9.5, 1.0),
                        max: Point3D::new(10.5, 10.5, 2.0),
                    },
                    status: arxos::yaml::EquipmentStatus::Healthy,
                    properties: HashMap::new(),
                    universal_path: "/buildings/test/equipment/equip-1".to_string(),
                    sensor_mappings: None,
                },
                EquipmentData {
                    id: "equip-2".to_string(),
                    name: "Electrical Panel".to_string(),
                    equipment_type: "Electrical".to_string(),
                    system_type: "ELECTRICAL".to_string(),
                    position: Point3D::new(15.0, 5.0, 2.0),
                    bounding_box: BoundingBox3D {
                        min: Point3D::new(14.5, 4.5, 1.5),
                        max: Point3D::new(15.5, 5.5, 2.5),
                    },
                    status: arxos::yaml::EquipmentStatus::Healthy,
                    properties: HashMap::new(),
                    universal_path: "/buildings/test/equipment/equip-2".to_string(),
                    sensor_mappings: None,
                },
            ],
            bounding_box: None,
        }],
        coordinate_systems: vec![],
    }
}

/// Helper function to setup test environment with building data
fn setup_test_environment() -> (TempDir, String) {
    let temp_dir = TempDir::new().expect("Failed to create temp directory");
    let original_dir = std::env::current_dir().expect("Failed to get current directory");
    
    // Change to temp directory
    std::env::set_current_dir(temp_dir.path()).expect("Failed to change directory");
    
    // Create building data
    let building_data = create_test_building_data();
    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).expect("Failed to serialize building");
    
    let yaml_file = "test_building.yaml";
    fs::write(yaml_file, yaml_content).expect("Failed to write YAML file");
    
    (temp_dir, original_dir.to_string_lossy().to_string())
}

/// Helper function to cleanup test environment
fn cleanup_test_environment(temp_dir: TempDir, original_dir: String) {
    drop(temp_dir);
    std::env::set_current_dir(&original_dir).expect("Failed to restore directory");
}

#[test]
fn test_spatial_query_all() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = spatial_query("all", "", vec![]);
    assert!(result.is_ok(), "spatial_query should succeed");
    
    let results = result.unwrap();
    assert_eq!(results.len(), 4, "Should return 4 entities (2 rooms + 2 equipment)");
    
    // Verify all entities are present
    let entity_names: Vec<String> = results.iter().map(|r| r.entity_name.clone()).collect();
    assert!(entity_names.contains(&"Room A".to_string()));
    assert!(entity_names.contains(&"Room B".to_string()));
    assert!(entity_names.contains(&"HVAC Unit 1".to_string()));
    assert!(entity_names.contains(&"Electrical Panel".to_string()));
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_room_filter() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = spatial_query("all", "room", vec![]);
    assert!(result.is_ok());
    
    let results = result.unwrap();
    assert_eq!(results.len(), 2, "Should return only 2 rooms");
    
    for result in &results {
        assert!(result.entity_type.contains("Room"));
    }
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_equipment_filter() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = spatial_query("all", "equipment", vec![]);
    assert!(result.is_ok());
    
    let results = result.unwrap();
    assert_eq!(results.len(), 2, "Should return only 2 equipment");
    
    for result in &results {
        assert!(result.entity_type.contains("Equipment"));
    }
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_distance() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = spatial_query("distance", "", vec!["Room A".to_string(), "Room B".to_string()]);
    assert!(result.is_ok());
    
    let results = result.unwrap();
    assert_eq!(results.len(), 1);
    
    // Distance from (0,0,0) to (20,0,0) should be 20.0
    let distance = results[0].distance;
    assert!((distance - 20.0).abs() < 0.01, "Distance should be approximately 20.0");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_distance_invalid_entities() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = spatial_query("distance", "", vec!["Nonexistent".to_string(), "Room A".to_string()]);
    assert!(result.is_err(), "Should fail with invalid entity");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_within_radius() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Query entities within radius 15.0 of point (10, 10, 1.5)
    let result = spatial_query(
        "within_radius",
        "",
        vec!["10.0".to_string(), "10.0".to_string(), "1.5".to_string(), "15.0".to_string()]
    );
    assert!(result.is_ok());
    
    let results = result.unwrap();
    assert!(results.len() >= 1, "Should find at least HVAC Unit 1");
    
    // Results should be sorted by distance
    for i in 1..results.len() {
        assert!(results[i].distance >= results[i-1].distance, "Results should be sorted by distance");
    }
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_within_radius_invalid_params() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Missing radius parameter
    let result = spatial_query(
        "within_radius",
        "",
        vec!["10.0".to_string(), "10.0".to_string(), "1.5".to_string()]
    );
    assert!(result.is_err(), "Should fail with insufficient parameters");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_nearest() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Find nearest entity to point (12, 8, 1.5)
    let result = spatial_query(
        "nearest",
        "",
        vec!["12.0".to_string(), "8.0".to_string(), "1.5".to_string()]
    );
    assert!(result.is_ok());
    
    let results = result.unwrap();
    assert_eq!(results.len(), 1, "Should return exactly one nearest entity");
    
    // Should be HVAC Unit 1 (at 10, 10, 1.5) which is closest
    assert_eq!(results[0].entity_name, "HVAC Unit 1");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_nearest_with_max_distance() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Find nearest entity within 5.0 units of point (12, 8, 1.5)
    let result = spatial_query(
        "nearest",
        "",
        vec!["12.0".to_string(), "8.0".to_string(), "1.5".to_string(), "5.0".to_string()]
    );
    assert!(result.is_ok());
    
    let results = result.unwrap();
    assert_eq!(results.len(), 1);
    assert_eq!(results[0].entity_name, "HVAC Unit 1");
    assert!(results[0].distance <= 5.0);
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_nearest_no_results_within_max_distance() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Find nearest entity within 0.1 units (too small)
    let result = spatial_query(
        "nearest",
        "",
        vec!["100.0".to_string(), "100.0".to_string(), "100.0".to_string(), "0.1".to_string()]
    );
    assert!(result.is_ok());
    
    let results = result.unwrap();
    assert_eq!(results.len(), 0, "Should return no results if nothing within max distance");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_spatial_query_invalid_query_type() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = spatial_query("invalid_type", "", vec![]);
    assert!(result.is_err(), "Should fail with invalid query type");
    
    let error_msg = result.unwrap_err().to_string();
    assert!(error_msg.contains("Unknown query type"));
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_validate_spatial_all_entities() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = validate_spatial(None, None);
    assert!(result.is_ok());
    
    let validation = result.unwrap();
    assert_eq!(validation.entities_checked, 4, "Should check all 4 entities");
    assert!(validation.is_valid, "All entities should be valid");
    assert_eq!(validation.issues_found, 0, "Should find no issues");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_validate_spatial_specific_entity() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = validate_spatial(Some("Room A"), None);
    assert!(result.is_ok());
    
    let validation = result.unwrap();
    assert_eq!(validation.entities_checked, 1);
    assert!(validation.is_valid);
    assert_eq!(validation.issues_found, 0);
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_validate_spatial_invalid_entity() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = validate_spatial(Some("Nonexistent Entity"), None);
    assert!(result.is_err(), "Should fail with nonexistent entity");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_validate_spatial_with_custom_tolerance() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    let result = validate_spatial(None, Some(0.0001));
    assert!(result.is_ok());
    
    let validation = result.unwrap();
    assert_eq!(validation.tolerance, 0.0001);
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_validate_spatial_invalid_bounding_box() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Create a building with invalid bounding box
    let mut building_data = create_test_building_data();
    building_data.floors[0].rooms[0].bounding_box = BoundingBox3D {
        min: Point3D::new(10.0, 10.0, 10.0), // min > max (invalid)
        max: Point3D::new(5.0, 5.0, 5.0),
    };
    
    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).expect("Failed to serialize");
    fs::write("test_building.yaml", yaml_content).expect("Failed to write");
    
    let result = validate_spatial(Some("Room A"), None);
    assert!(result.is_ok());
    
    let validation = result.unwrap();
    assert!(!validation.is_valid, "Should detect invalid bounding box");
    assert!(validation.issues_found > 0, "Should find issues");
    
    // Check that issues contain bounding box problems
    let has_bbox_issue = validation.issues.iter()
        .any(|issue| issue.issue_type == "BoundingBoxInvalid");
    assert!(has_bbox_issue, "Should have BoundingBoxInvalid issue");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_validate_spatial_zero_dimension() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Create a building with zero-width bounding box
    let mut building_data = create_test_building_data();
    building_data.floors[0].rooms[0].bounding_box = BoundingBox3D {
        min: Point3D::new(0.0, 0.0, 0.0),
        max: Point3D::new(0.0, 5.0, 3.0), // Zero width
    };
    
    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).expect("Failed to serialize");
    fs::write("test_building.yaml", yaml_content).expect("Failed to write");
    
    let result = validate_spatial(Some("Room A"), None);
    assert!(result.is_ok());
    
    let validation = result.unwrap();
    assert!(!validation.is_valid, "Should detect zero dimension");
    
    let has_zero_dim_issue = validation.issues.iter()
        .any(|issue| issue.issue_type == "ZeroDimension");
    assert!(has_zero_dim_issue, "Should have ZeroDimension issue");
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_validate_spatial_issue_details() {
    let (temp_dir, original_dir) = setup_test_environment();
    
    // Create invalid bounding box
    let mut building_data = create_test_building_data();
    building_data.floors[0].rooms[0].bounding_box = BoundingBox3D {
        min: Point3D::new(10.0, 0.0, 0.0),
        max: Point3D::new(5.0, 5.0, 3.0),
    };
    
    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).expect("Failed to serialize");
    fs::write("test_building.yaml", yaml_content).expect("Failed to write");
    
    let result = validate_spatial(Some("Room A"), None);
    assert!(result.is_ok());
    
    let validation = result.unwrap();
    assert!(!validation.issues.is_empty());
    
    // Check issue details
    let issue = &validation.issues[0];
    assert_eq!(issue.entity_name, "Room A");
    assert_eq!(issue.entity_type, "Room");
    assert!(!issue.message.is_empty());
    assert!(!issue.severity.is_empty());
    
    cleanup_test_environment(temp_dir, original_dir);
}

#[test]
fn test_coordinate_transformation() {
    // Coordinate transformation is reserved for future implementation
    // The function transform_coordinates exists but returns a status message
    // This test verifies the function exists and can be called
    let result = crate::core::transform_coordinates("building_local", "world", "test_entity");
    assert!(result.is_ok());
    let message = result.unwrap();
    assert!(message.contains("Coordinate transformation"));
}
