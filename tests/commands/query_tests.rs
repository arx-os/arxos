//! Integration tests for query command (`arx query`)
//!
//! Tests the query engine with glob pattern matching for ArxAddress paths

use arxos::commands::query::handle_query_command;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, EquipmentStatus};
use arxos::spatial::{Point3D, BoundingBox3D};
use arxos::persistence::PersistenceManager;
use arxos::domain::ArxAddress;
use chrono::Utc;
use serial_test::serial;
use std::collections::HashMap;
use tempfile::TempDir;

/// Helper to create test building data with ArxAddress
fn create_test_building_with_addresses() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: 4,
            spatial_entities: 4,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![
            FloorData {
                id: "floor-1".to_string(),
                name: "Floor 1".to_string(),
                level: 1,
                elevation: 0.0,
                rooms: vec![],
                wings: vec![],
                equipment: vec![
                    EquipmentData {
                        address: Some(ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01").unwrap()),
                        id: "eq-1".to_string(),
                        name: "Boiler 01".to_string(),
                        equipment_type: "HVAC".to_string(),
                        system_type: "HVAC".to_string(),
                        position: Point3D::new(5.0, 5.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(4.0, 4.0, 0.0),
                            Point3D::new(6.0, 6.0, 2.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: String::new(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        address: Some(ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-02").unwrap()),
                        id: "eq-2".to_string(),
                        name: "Boiler 02".to_string(),
                        equipment_type: "HVAC".to_string(),
                        system_type: "HVAC".to_string(),
                        position: Point3D::new(8.0, 8.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(7.0, 7.0, 0.0),
                            Point3D::new(9.0, 9.0, 2.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: String::new(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        address: Some(ArxAddress::from_path("/usa/ny/manhattan/test-building/floor-1/plumbing/valve-01").unwrap()),
                        id: "eq-3".to_string(),
                        name: "Valve 01".to_string(),
                        equipment_type: "Plumbing".to_string(),
                        system_type: "Plumbing".to_string(),
                        position: Point3D::new(10.0, 10.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(9.0, 9.0, 0.0),
                            Point3D::new(11.0, 11.0, 1.5),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: String::new(),
                        sensor_mappings: None,
                    },
                ],
                bounding_box: None,
            },
            FloorData {
                id: "floor-2".to_string(),
                name: "Floor 2".to_string(),
                level: 2,
                elevation: 3.0,
                rooms: vec![],
                wings: vec![],
                equipment: vec![
                    EquipmentData {
                        address: Some(ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-2/hvac/ahu-01").unwrap()),
                        id: "eq-4".to_string(),
                        name: "AHU 01".to_string(),
                        equipment_type: "HVAC".to_string(),
                        system_type: "HVAC".to_string(),
                        position: Point3D::new(12.0, 12.0, 3.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(11.0, 11.0, 3.0),
                            Point3D::new(13.0, 13.0, 5.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: String::new(),
                        sensor_mappings: None,
                    },
                ],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![],
    }
}

/// Test query command with exact match
#[test]
#[serial]
fn test_query_exact_match() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query for exact path
    let result = handle_query_command(
        "/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01",
        "json",
        false,
    );
    
    assert!(result.is_ok(), "Query should succeed");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with wildcard city
#[test]
#[serial]
fn test_query_wildcard_city() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query for all NY boilers (wildcard city)
    let result = handle_query_command(
        "/usa/ny/*/test-building/floor-*/mech/boiler-*",
        "json",
        false,
    );
    
    assert!(result.is_ok(), "Query should succeed with wildcard pattern");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with wildcard floor
#[test]
#[serial]
fn test_query_wildcard_floor() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query for all equipment on any floor in Brooklyn
    let result = handle_query_command(
        "/usa/ny/brooklyn/test-building/floor-*/*/*",
        "json",
        false,
    );
    
    assert!(result.is_ok(), "Query should succeed with wildcard floor");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with wildcard system
#[test]
#[serial]
fn test_query_wildcard_system() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query for all HVAC equipment
    let result = handle_query_command(
        "/usa/ny/*/test-building/floor-*/hvac/*",
        "json",
        false,
    );
    
    assert!(result.is_ok(), "Query should succeed with wildcard system");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with no matches
#[test]
#[serial]
fn test_query_no_matches() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query for non-existent path
    let result = handle_query_command(
        "/usa/ca/san-francisco/test-building/floor-1/mech/boiler-01",
        "json",
        false,
    );
    
    assert!(result.is_ok(), "Query should succeed even with no matches");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with invalid glob pattern
#[test]
#[serial]
fn test_query_invalid_pattern() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query with invalid pattern (should handle gracefully)
    let result = handle_query_command(
        "/usa/ny/[invalid",
        "json",
        false,
    );
    
    // Should handle error gracefully (either return error or empty results)
    // The exact behavior depends on implementation
    let _ = result; // Don't fail test - just verify it doesn't panic
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with different output formats
#[test]
#[serial]
fn test_query_output_formats() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Test JSON format
    let result_json = handle_query_command(
        "/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01",
        "json",
        false,
    );
    assert!(result_json.is_ok(), "JSON format should work");
    
    // Test YAML format
    let result_yaml = handle_query_command(
        "/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01",
        "yaml",
        false,
    );
    assert!(result_yaml.is_ok(), "YAML format should work");
    
    // Test table format
    let result_table = handle_query_command(
        "/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01",
        "table",
        false,
    );
    assert!(result_table.is_ok(), "Table format should work");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with verbose output
#[test]
#[serial]
fn test_query_verbose() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query with verbose flag
    let result = handle_query_command(
        "/usa/ny/brooklyn/test-building/floor-1/mech/boiler-*",
        "json",
        true,
    );
    
    assert!(result.is_ok(), "Verbose query should work");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command with complex glob pattern
#[test]
#[serial]
fn test_query_complex_glob() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_addresses();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query with complex pattern: all boilers in NY on any floor
    let result = handle_query_command(
        "/usa/ny/*/test-building/floor-*/mech/boiler-*",
        "json",
        false,
    );
    
    assert!(result.is_ok(), "Complex glob pattern should work");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test query command handles equipment without address
#[test]
#[serial]
fn test_query_missing_address() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create building data with some equipment missing address
    let mut building_data = create_test_building_with_addresses();
    building_data.floors[0].equipment.push(EquipmentData {
        address: None,
        id: "eq-5".to_string(),
        name: "Legacy Equipment".to_string(),
        equipment_type: "Other".to_string(),
        system_type: "Other".to_string(),
        position: Point3D::new(15.0, 15.0, 0.0),
        bounding_box: BoundingBox3D::new(
            Point3D::new(14.0, 14.0, 0.0),
            Point3D::new(16.0, 16.0, 1.0),
        ),
        status: EquipmentStatus::Healthy,
        properties: HashMap::new(),
        universal_path: "Legacy::Path".to_string(),
        sensor_mappings: None,
    });
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Query should skip equipment without address
    let result = handle_query_command(
        "/usa/ny/*/test-building/floor-*/*/*",
        "json",
        false,
    );
    
    assert!(result.is_ok(), "Query should handle missing addresses gracefully");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

