//! Integration tests for ArxAddress YAML + Git workflow
//!
//! Tests the complete workflow of:
//! - Creating ArxAddress from equipment data
//! - Serializing to YAML
//! - Git repository layout based on address
//! - Loading and deserializing from YAML

use arxos::domain::ArxAddress;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, EquipmentStatus};
use arxos::spatial::{Point3D, BoundingBox3D};
use arxos::persistence::PersistenceManager;
use arxos::git::manager::BuildingGitManager;
use chrono::Utc;
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use tempfile::TempDir;

/// Test ArxAddress creation and YAML serialization
#[test]
#[serial]
fn test_address_yaml_serialization() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create address
    let address = ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01").unwrap();
    
    // Create building data with address
    let building_data = BuildingData {
        building: BuildingInfo {
            id: building_name.to_string(),
            name: building_name.to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: 1,
            spatial_entities: 1,
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
                        address: Some(address.clone()),
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
                ],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![],
    };
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Reload and verify address is preserved
    let reloaded = persistence.load_building_data().unwrap();
    let reloaded_address = &reloaded.floors[0].equipment[0].address.as_ref().unwrap();
    
    assert_eq!(reloaded_address.path, address.path, "Address should be preserved in YAML");
    assert!(reloaded_address.validate().is_ok(), "Reloaded address should be valid");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test Git repository layout based on ArxAddress
#[test]
#[serial]
fn test_git_repo_layout_from_address() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Initialize Git repository
    let repo_path = temp_dir.path().join("repo");
    fs::create_dir_all(&repo_path).unwrap();
    
    // Change to repo directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(&repo_path).unwrap();
    
    // Initialize Git
    let git_manager = BuildingGitManager::init(&repo_path, building_name).unwrap();
    
    // Create address
    let address = ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01").unwrap();
    
    // Create file structure based on address
    let file_path = git_manager.create_file_structure(&address, "equipment.yaml").unwrap();
    
    // Verify directory structure matches address
    let expected_path = repo_path.join("usa/ny/brooklyn/test-building/floor-1/mech/equipment.yaml");
    assert_eq!(file_path, expected_path, "File path should match address structure");
    
    // Verify directories were created
    assert!(expected_path.parent().unwrap().exists(), "Parent directories should exist");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test address round-trip through YAML and Git
#[test]
#[serial]
fn test_address_yaml_git_roundtrip() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create address
    let original_address = ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01").unwrap();
    
    // Create building data
    let building_data = BuildingData {
        building: BuildingInfo {
            id: building_name.to_string(),
            name: building_name.to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: 1,
            spatial_entities: 1,
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
                        address: Some(original_address.clone()),
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
                ],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![],
    };
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Save to YAML
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Reload from YAML
    let reloaded = persistence.load_building_data().unwrap();
    let reloaded_address = reloaded.floors[0].equipment[0].address.as_ref().unwrap();
    
    // Verify address is preserved
    assert_eq!(reloaded_address.path, original_address.path);
    assert_eq!(reloaded_address.guid(), original_address.guid(), "GUID should be stable");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test multiple addresses with different paths
#[test]
#[serial]
fn test_multiple_addresses_yaml() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create multiple addresses
    let addresses = vec![
        ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01").unwrap(),
        ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-02").unwrap(),
        ArxAddress::from_path("/usa/ny/manhattan/test-building/floor-1/plumbing/valve-01").unwrap(),
    ];
    
    // Create building data with multiple equipment
    let mut building_data = BuildingData {
        building: BuildingInfo {
            id: building_name.to_string(),
            name: building_name.to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: 3,
            spatial_entities: 3,
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
                equipment: vec![],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![],
    };
    
    // Add equipment with addresses
    for (idx, address) in addresses.iter().enumerate() {
        building_data.floors[0].equipment.push(EquipmentData {
            address: Some(address.clone()),
            id: format!("eq-{}", idx + 1),
            name: format!("Equipment {}", idx + 1),
            equipment_type: "HVAC".to_string(),
            system_type: "HVAC".to_string(),
            position: Point3D::new((idx as f64) * 5.0, (idx as f64) * 5.0, 0.0),
            bounding_box: BoundingBox3D::new(
                Point3D::new((idx as f64) * 5.0 - 1.0, (idx as f64) * 5.0 - 1.0, 0.0),
                Point3D::new((idx as f64) * 5.0 + 1.0, (idx as f64) * 5.0 + 1.0, 2.0),
            ),
            status: EquipmentStatus::Healthy,
            properties: HashMap::new(),
            universal_path: String::new(),
            sensor_mappings: None,
        });
    }
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Save and reload
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    let reloaded = persistence.load_building_data().unwrap();
    
    // Verify all addresses are preserved
    assert_eq!(reloaded.floors[0].equipment.len(), 3);
    for (idx, equipment) in reloaded.floors[0].equipment.iter().enumerate() {
        assert!(equipment.address.is_some(), "Equipment {} should have address", idx);
        assert_eq!(
            equipment.address.as_ref().unwrap().path,
            addresses[idx].path,
            "Address {} should match",
            idx
        );
    }
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test address validation after YAML load
#[test]
#[serial]
fn test_address_validation_after_load() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create valid address
    let address = ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/hvac/boiler-01").unwrap();
    assert!(address.validate().is_ok(), "Address should be valid");
    
    // Create building data
    let building_data = BuildingData {
        building: BuildingInfo {
            id: building_name.to_string(),
            name: building_name.to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: 1,
            spatial_entities: 1,
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
                        address: Some(address),
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
                ],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![],
    };
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Save and reload
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    let reloaded = persistence.load_building_data().unwrap();
    let reloaded_address = reloaded.floors[0].equipment[0].address.as_ref().unwrap();
    
    // Verify address is still valid after round-trip
    assert!(reloaded_address.validate().is_ok(), "Reloaded address should be valid");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test GUID stability across YAML save/load
#[test]
#[serial]
fn test_address_guid_stability() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create address
    let address = ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01").unwrap();
    let original_guid = address.guid();
    
    // Create building data
    let building_data = BuildingData {
        building: BuildingInfo {
            id: building_name.to_string(),
            name: building_name.to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: 1,
            spatial_entities: 1,
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
                        address: Some(address),
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
                ],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![],
    };
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Save and reload multiple times
    let persistence = PersistenceManager::new(building_name).unwrap();
    
    for _ in 0..3 {
        persistence.save_building_data(&building_data).unwrap();
        let reloaded = persistence.load_building_data().unwrap();
        let reloaded_address = reloaded.floors[0].equipment[0].address.as_ref().unwrap();
        let reloaded_guid = reloaded_address.guid();
        
        assert_eq!(
            reloaded_guid, original_guid,
            "GUID should be stable across save/load cycles"
        );
    }
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

