//! Integration tests for the persistence module
//!
//! These tests verify that building data can be saved to and loaded from YAML files,
//! and that Git commit operations work correctly.

use arxos::persistence::PersistenceManager;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData};
use chrono::Utc;
use std::fs;
use tempfile::TempDir;

fn setup_test_environment() -> TempDir {
    tempfile::tempdir().expect("Failed to create temp directory")
}

#[test]
fn test_persistence_manager_creation() {
    let temp_dir = setup_test_environment();
    let test_file = temp_dir.path().join("test_building.yaml");
    
    // Create a test building file
    let building_data = create_test_building_data();
    let yaml_content = serde_yaml::to_string(&building_data).unwrap();
    fs::write(&test_file, yaml_content).unwrap();
    
    // Create persistence manager
    let persistence = PersistenceManager::new("Test Building");
    
    // Should fail because building not found in current directory
    assert!(persistence.is_err());
}

#[test]
fn test_load_building_data() {
    let temp_dir = setup_test_environment();
    let original_dir = std::env::current_dir().unwrap();
    
    // Change to temp directory
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    let test_file = temp_dir.path().join("test_building.yaml");
    
    // Create a test building file
    let building_data = create_test_building_data();
    let yaml_content = serde_yaml::to_string(&building_data).unwrap();
    fs::write(&test_file, yaml_content).unwrap();
    
    // Create persistence manager
    let persistence = PersistenceManager::new("test_building").unwrap();
    
    // Load building data
    let loaded_data = persistence.load_building_data().unwrap();
    
    assert_eq!(loaded_data.building.name, "Test Building");
    assert_eq!(loaded_data.floors.len(), 1);
    assert_eq!(loaded_data.floors[0].name, "Ground Floor");
    
    // Restore original directory
    std::env::set_current_dir(&original_dir).unwrap();
}

#[test]
fn test_save_building_data() {
    let temp_dir = setup_test_environment();
    let original_dir = std::env::current_dir().unwrap();
    
    // Change to temp directory
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    let test_file = temp_dir.path().join("test_building.yaml");
    
    // Create initial building data
    let building_data = create_test_building_data();
    let yaml_content = serde_yaml::to_string(&building_data).unwrap();
    fs::write(&test_file, yaml_content).unwrap();
    
    // Create persistence manager
    let persistence = PersistenceManager::new("test_building").unwrap();
    
    // Load data
    let mut loaded_data = persistence.load_building_data().unwrap();
    
    // Modify data
    loaded_data.building.name = "Modified Building".to_string();
    
    // Save data
    persistence.save_building_data(&loaded_data).unwrap();
    
    // Reload and verify
    let reloaded_data = persistence.load_building_data().unwrap();
    assert_eq!(reloaded_data.building.name, "Modified Building");
    
    // Verify backup file was created
    let backup_file = test_file.with_extension("yaml.bak");
    assert!(backup_file.exists());
    
    // Restore original directory
    std::env::set_current_dir(&original_dir).unwrap();
}

fn create_test_building_data() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-1".to_string(),
            name: "Test Building".to_string(),
            description: Some("Test building".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: Some("test.ifc".to_string()),
            parser_version: "1.0".to_string(),
            total_entities: 10,
            spatial_entities: 5,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![FloorData {
            id: "floor-0".to_string(),
            name: "Ground Floor".to_string(),
            level: 0,
            elevation: 0.0,
            rooms: vec![],
            equipment: vec![],
            bounding_box: None,
        }],
        coordinate_systems: vec![],
    }
}

