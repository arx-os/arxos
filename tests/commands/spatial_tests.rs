//! Tests for spatial operations command handlers

use arxos::core::{spatial_query, validate_spatial};
use arxos::core::{
    BoundingBox, Dimensions, Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType,
    Floor, Position, Room, RoomType, SpatialProperties, Wing,
};
use arxos::spatial::Point3D;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use tempfile::TempDir;

/// Helper function to create a test building with rooms and equipment
fn create_test_building_data() -> BuildingData {
    fn spatial_properties_from_bbox(min: Point3D, max: Point3D) -> SpatialProperties {
        let dimensions = Dimensions {
            width: max.x - min.x,
            depth: max.y - min.y,
            height: max.z - min.z,
        };

        SpatialProperties {
            position: Position {
                x: (min.x + max.x) / 2.0,
                y: (min.y + max.y) / 2.0,
                z: min.z,
                coordinate_system: "building_local".to_string(),
            },
            dimensions,
            bounding_box: BoundingBox {
                min: Position {
                    x: min.x,
                    y: min.y,
                    z: min.z,
                    coordinate_system: "building_local".to_string(),
                },
                max: Position {
                    x: max.x,
                    y: max.y,
                    z: max.z,
                    coordinate_system: "building_local".to_string(),
                },
            },
            coordinate_system: "building_local".to_string(),
        }
    }

    fn make_room(id: &str, name: &str, room_type: RoomType, min: Point3D, max: Point3D) -> Room {
        let mut room = Room::new(name.to_string(), room_type);
        room.id = id.to_string();
        room.spatial_properties = spatial_properties_from_bbox(min, max);
        room
    }

    fn make_equipment(
        id: &str,
        name: &str,
        equipment_type: EquipmentType,
        position: Point3D,
        path: &str,
    ) -> Equipment {
        Equipment {
            id: id.to_string(),
            name: name.to_string(),
            path: path.to_string(),
            address: None,
            equipment_type,
            position: Position {
                x: position.x,
                y: position.y,
                z: position.z,
                coordinate_system: "building_local".to_string(),
            },
            properties: HashMap::new(),
            status: EquipmentStatus::Active,
            health_status: Some(EquipmentHealthStatus::Healthy),
            room_id: None,
            sensor_mappings: None,
        }
    }

    let room_a = make_room(
        "room-1",
        "Room A",
        RoomType::Office,
        Point3D::new(-5.0, -5.0, 0.0),
        Point3D::new(5.0, 5.0, 3.0),
    );

    let room_b = make_room(
        "room-2",
        "Room B",
        RoomType::Classroom,
        Point3D::new(15.0, -10.0, 0.0),
        Point3D::new(25.0, 10.0, 3.0),
    );

    let mut main_wing = Wing::new("Main Wing".to_string());
    main_wing.rooms.push(room_a);
    main_wing.rooms.push(room_b);

    let equipment_hvac = make_equipment(
        "equip-1",
        "HVAC Unit 1",
        EquipmentType::HVAC,
        Point3D::new(10.0, 10.0, 1.5),
        "/buildings/test/equipment/equip-1",
    );

    let equipment_panel = make_equipment(
        "equip-2",
        "Electrical Panel",
        EquipmentType::Electrical,
        Point3D::new(15.0, 5.0, 2.0),
        "/buildings/test/equipment/equip-2",
    );

    let floor = Floor {
        id: "floor-1".to_string(),
        name: "Floor 1".to_string(),
        level: 1,
        elevation: Some(0.0),
        bounding_box: None,
        wings: vec![main_wing],
        equipment: vec![equipment_hvac, equipment_panel],
        properties: HashMap::new(),
    };

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
        floors: vec![floor],
        coordinate_systems: vec![],
    }
}

/// Helper function to setup test environment with building data
struct TestEnvironment {
    _temp_dir: TempDir,
    original_dir: PathBuf,
}

impl TestEnvironment {
    fn new() -> Self {
        let temp_dir = TempDir::new().expect("Failed to create temp directory");
        let original_dir = std::env::current_dir().expect("Failed to get current directory");

        std::env::set_current_dir(temp_dir.path()).expect("Failed to change directory");

        Self {
            _temp_dir: temp_dir,
            original_dir,
        }
    }

    fn write_default_building(&self) {
        let building_data = create_test_building_data();
        let serializer = arxos::yaml::BuildingYamlSerializer::new();
        let yaml_content = serializer
            .to_yaml(&building_data)
            .expect("Failed to serialize building");
        fs::write("test_building.yaml", yaml_content).expect("Failed to write YAML file");
    }
}

impl Drop for TestEnvironment {
    fn drop(&mut self) {
        if let Err(err) = std::env::set_current_dir(&self.original_dir) {
            let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
            if let Err(fallback_err) = std::env::set_current_dir(&manifest_dir) {
                eprintln!(
                    "TestEnvironment: failed to restore directory {}: {}. Fallback to manifest dir {} failed: {}",
                    self.original_dir.display(),
                    err,
                    manifest_dir.display(),
                    fallback_err
                );
            }
        }
    }
}

fn setup_test_environment() -> TestEnvironment {
    let env = TestEnvironment::new();
    env.write_default_building();
    env
}

#[test]
#[serial]
fn test_spatial_query_all() {
    let _env = setup_test_environment();

    let result = spatial_query("all", "", vec![]);
    assert!(result.is_ok(), "spatial_query should succeed");

    let results = result.unwrap();
    assert_eq!(
        results.len(),
        4,
        "Should return 4 entities (2 rooms + 2 equipment)"
    );

    // Verify all entities are present
    let entity_names: Vec<String> = results.iter().map(|r| r.entity_name.clone()).collect();
    assert!(entity_names.contains(&"Room A".to_string()));
    assert!(entity_names.contains(&"Room B".to_string()));
    assert!(entity_names.contains(&"HVAC Unit 1".to_string()));
    assert!(entity_names.contains(&"Electrical Panel".to_string()));
}

#[test]
#[serial]
fn test_spatial_query_room_filter() {
    let _env = setup_test_environment();

    let result = spatial_query("all", "room", vec![]);
    assert!(result.is_ok());

    let results = result.unwrap();
    assert_eq!(results.len(), 2, "Should return only 2 rooms");

    for result in &results {
        assert!(result.entity_type.contains("Room"));
    }
}

#[test]
#[serial]
fn test_spatial_query_equipment_filter() {
    let _env = setup_test_environment();

    let result = spatial_query("all", "equipment", vec![]);
    assert!(result.is_ok());

    let results = result.unwrap();
    assert_eq!(results.len(), 2, "Should return only 2 equipment");

    for result in &results {
        assert!(result.entity_type.contains("Equipment"));
    }
}

#[test]
#[serial]
fn test_spatial_query_distance() {
    let _env = setup_test_environment();

    let result = spatial_query(
        "distance",
        "",
        vec!["Room A".to_string(), "Room B".to_string()],
    );
    assert!(result.is_ok());

    let results = result.unwrap();
    assert_eq!(results.len(), 1);

    // Distance from (0,0,0) to (20,0,0) should be 20.0
    let distance = results[0].distance;
    assert!(
        (distance - 20.0).abs() < 0.01,
        "Distance should be approximately 20.0"
    );
}

#[test]
#[serial]
fn test_spatial_query_distance_invalid_entities() {
    let _env = setup_test_environment();

    let result = spatial_query(
        "distance",
        "",
        vec!["Nonexistent".to_string(), "Room A".to_string()],
    );
    assert!(result.is_err(), "Should fail with invalid entity");
}

#[test]
#[serial]
fn test_spatial_query_within_radius() {
    let _env = setup_test_environment();

    // Query entities within radius 15.0 of point (10, 10, 1.5)
    let result = spatial_query(
        "within_radius",
        "",
        vec![
            "10.0".to_string(),
            "10.0".to_string(),
            "1.5".to_string(),
            "15.0".to_string(),
        ],
    );
    assert!(result.is_ok());

    let results = result.unwrap();
    assert!(!results.is_empty(), "Should find at least HVAC Unit 1");

    // Results should be sorted by distance
    for i in 1..results.len() {
        assert!(
            results[i].distance >= results[i - 1].distance,
            "Results should be sorted by distance"
        );
    }
}

#[test]
#[serial]
fn test_spatial_query_within_radius_invalid_params() {
    let _env = setup_test_environment();

    // Missing radius parameter
    let result = spatial_query(
        "within_radius",
        "",
        vec!["10.0".to_string(), "10.0".to_string(), "1.5".to_string()],
    );
    assert!(result.is_err(), "Should fail with insufficient parameters");
}

#[test]
#[serial]
fn test_spatial_query_nearest() {
    let _env = setup_test_environment();

    // Find nearest entity to point (12, 8, 1.5)
    let result = spatial_query(
        "nearest",
        "",
        vec!["12.0".to_string(), "8.0".to_string(), "1.5".to_string()],
    );
    assert!(result.is_ok());

    let results = result.unwrap();
    assert_eq!(results.len(), 1, "Should return exactly one nearest entity");

    // Should be HVAC Unit 1 (at 10, 10, 1.5) which is closest
    assert_eq!(results[0].entity_name, "HVAC Unit 1");
}

#[test]
#[serial]
fn test_spatial_query_nearest_with_max_distance() {
    let _env = setup_test_environment();

    // Find nearest entity within 5.0 units of point (12, 8, 1.5)
    let result = spatial_query(
        "nearest",
        "",
        vec![
            "12.0".to_string(),
            "8.0".to_string(),
            "1.5".to_string(),
            "5.0".to_string(),
        ],
    );
    assert!(result.is_ok());

    let results = result.unwrap();
    assert_eq!(results.len(), 1);
    assert_eq!(results[0].entity_name, "HVAC Unit 1");
    assert!(results[0].distance <= 5.0);
}

#[test]
#[serial]
fn test_spatial_query_nearest_no_results_within_max_distance() {
    let _env = setup_test_environment();

    // Find nearest entity within 0.1 units (too small)
    let result = spatial_query(
        "nearest",
        "",
        vec![
            "100.0".to_string(),
            "100.0".to_string(),
            "100.0".to_string(),
            "0.1".to_string(),
        ],
    );
    assert!(result.is_ok());

    let results = result.unwrap();
    assert_eq!(
        results.len(),
        0,
        "Should return no results if nothing within max distance"
    );
}

#[test]
#[serial]
fn test_spatial_query_invalid_query_type() {
    let _env = setup_test_environment();

    let result = spatial_query("invalid_type", "", vec![]);
    assert!(result.is_err(), "Should fail with invalid query type");

    let error_msg = result.unwrap_err().to_string();
    assert!(error_msg.contains("Unknown query type"));
}

#[test]
#[serial]
fn test_validate_spatial_all_entities() {
    let _env = setup_test_environment();

    let result = validate_spatial(None, None);
    assert!(result.is_ok());

    let validation = result.unwrap();
    assert_eq!(
        validation.entities_checked, 4,
        "Should check all 4 entities"
    );
    assert!(validation.is_valid, "All entities should be valid");
    assert_eq!(validation.issues_found, 0, "Should find no issues");
}

#[test]
#[serial]
fn test_validate_spatial_specific_entity() {
    let _env = setup_test_environment();

    let result = validate_spatial(Some("Room A"), None);
    assert!(result.is_ok());

    let validation = result.unwrap();
    assert_eq!(validation.entities_checked, 1);
    assert!(validation.is_valid);
    assert_eq!(validation.issues_found, 0);
}

#[test]
#[serial]
fn test_validate_spatial_invalid_entity() {
    let _env = setup_test_environment();

    let result = validate_spatial(Some("Nonexistent Entity"), None);
    assert!(result.is_err(), "Should fail with nonexistent entity");
}

#[test]
#[serial]
fn test_validate_spatial_with_custom_tolerance() {
    let _env = setup_test_environment();

    let result = validate_spatial(None, Some(0.0001));
    assert!(result.is_ok());

    let validation = result.unwrap();
    assert_eq!(validation.tolerance, 0.0001);
}

#[test]
#[serial]
fn test_validate_spatial_invalid_bounding_box() {
    let _env = setup_test_environment();

    // Create a building with invalid bounding box
    let mut building_data = create_test_building_data();
    let room = &mut building_data.floors[0].wings[0].rooms[0];
    room.spatial_properties.bounding_box = BoundingBox {
        min: Position {
            x: 10.0,
            y: 10.0,
            z: 10.0,
            coordinate_system: "building_local".to_string(),
        },
        max: Position {
            x: 5.0,
            y: 5.0,
            z: 5.0,
            coordinate_system: "building_local".to_string(),
        },
    };

    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer
        .to_yaml(&building_data)
        .expect("Failed to serialize");
    fs::write("test_building.yaml", yaml_content).expect("Failed to write");

    let result = validate_spatial(Some("Room A"), None);
    assert!(result.is_ok());

    let validation = result.unwrap();
    assert!(!validation.is_valid, "Should detect invalid bounding box");
    assert!(validation.issues_found > 0, "Should find issues");

    // Check that issues contain bounding box problems
    let has_bbox_issue = validation
        .issues
        .iter()
        .any(|issue| issue.issue_type == "BoundingBoxInvalid");
    assert!(has_bbox_issue, "Should have BoundingBoxInvalid issue");
}

#[test]
#[serial]
fn test_validate_spatial_zero_dimension() {
    let _env = setup_test_environment();

    // Create a building with zero-width bounding box
    let mut building_data = create_test_building_data();
    let room = &mut building_data.floors[0].wings[0].rooms[0];
    room.spatial_properties.bounding_box = BoundingBox {
        min: Position {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        },
        max: Position {
            x: 0.0,
            y: 5.0,
            z: 3.0,
            coordinate_system: "building_local".to_string(),
        },
    };

    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer
        .to_yaml(&building_data)
        .expect("Failed to serialize");
    fs::write("test_building.yaml", yaml_content).expect("Failed to write");

    let result = validate_spatial(Some("Room A"), None);
    assert!(result.is_ok());

    let validation = result.unwrap();
    assert!(!validation.is_valid, "Should detect zero dimension");

    let has_zero_dim_issue = validation
        .issues
        .iter()
        .any(|issue| issue.issue_type == "ZeroDimension");
    assert!(has_zero_dim_issue, "Should have ZeroDimension issue");
}

#[test]
#[serial]
fn test_validate_spatial_issue_details() {
    let _env = setup_test_environment();

    // Create invalid bounding box
    let mut building_data = create_test_building_data();
    let room = &mut building_data.floors[0].wings[0].rooms[0];
    room.spatial_properties.bounding_box = BoundingBox {
        min: Position {
            x: 10.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        },
        max: Position {
            x: 5.0,
            y: 5.0,
            z: 3.0,
            coordinate_system: "building_local".to_string(),
        },
    };

    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer
        .to_yaml(&building_data)
        .expect("Failed to serialize");
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
}

#[test]
fn test_coordinate_transformation() {
    // Coordinate transformation is reserved for future implementation
    // The function transform_coordinates exists but returns a status message
    // This test verifies the function exists and can be called
    let result = arxos::core::transform_coordinates("building_local", "world", "test_entity");
    assert!(result.is_ok());
    let message = result.unwrap();
    assert!(message.contains("Coordinate transformation"));
}
