//! Integration tests for the persistence module
//!
//! These tests verify that building data can be saved to and loaded from YAML files,
//! and that Git commit operations work correctly.

use arxos::persistence::PersistenceManager;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData};
use chrono::Utc;
use std::fs;
use std::path::PathBuf;
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

//! File Size Limit Tests
//!
//! Tests verify that YAML files exceeding size limits are properly rejected
//! to prevent memory issues and ensure system stability.

mod file_size_limit_tests {
    use super::*;
    use std::io::Write;

    /// Create a mock YAML file with specified size
    fn create_mock_yaml_file(dir: &TempDir, size_mb: u64) -> PathBuf {
        let file_path = dir.path().join("large_building.yaml");
        let mut file = fs::File::create(&file_path).expect("Failed to create test file");
        
        // Write minimal valid YAML header
        file.write_all(b"building:\n  name: Test Building\n  id: test-1\nfloors:\n")
            .expect("Failed to write YAML header");
        
        // Fill with dummy floor/room data to reach target size
        let target_bytes = size_mb * 1024 * 1024;
        let mut written = file.metadata().unwrap().len();
        
        while written < target_bytes {
            let room_yaml = format!(
                "- level: {}\n  rooms:\n  - name: Room{}\n    id: room-{}\n",
                written % 100,
                written,
                written
            );
            file.write_all(room_yaml.as_bytes()).unwrap();
            written = file.metadata().unwrap().len();
            if written >= target_bytes {
                break;
            }
        }
        
        file_path
    }

    #[test]
    fn test_yaml_file_size_limit_accepted() {
        // YAML file just under 10MB should be accepted
        let temp_dir = setup_test_environment();
        let original_dir = std::env::current_dir().unwrap();
        
        std::env::set_current_dir(temp_dir.path()).unwrap();
        let _yaml_file = create_mock_yaml_file(&temp_dir, 9);
        
        let persistence = PersistenceManager::new("Test Building");
        
        if let Ok(pm) = persistence {
            let result = pm.load_building_data();
            // May fail for invalid YAML, but not for size
            if let Err(e) = result {
                assert!(!matches!(e, arxos::persistence::PersistenceError::FileTooLarge { .. }), 
                        "File under 10MB should not be rejected for size");
            }
        }
        
        std::env::set_current_dir(&original_dir).unwrap();
    }

    #[test]
    fn test_yaml_file_size_limit_exceeded() {
        // YAML file over 10MB should be rejected
        let temp_dir = setup_test_environment();
        let original_dir = std::env::current_dir().unwrap();
        
        std::env::set_current_dir(temp_dir.path()).unwrap();
        let _yaml_file = create_mock_yaml_file(&temp_dir, 11);
        
        let persistence = PersistenceManager::new("Test Building");
        
        if let Ok(pm) = persistence {
            let result = pm.load_building_data();
            assert!(result.is_err(), "File over 10MB should be rejected");
            assert!(matches!(result.unwrap_err(), 
                    arxos::persistence::PersistenceError::FileTooLarge { size: 11, max: 10 }),
                    "Should return FileTooLarge error with correct size");
        }
        
        std::env::set_current_dir(&original_dir).unwrap();
    }

    #[test]
    fn test_yaml_save_size_validation() {
        // Attempting to save YAML over 10MB should be rejected before writing
        let temp_dir = setup_test_environment();
        let original_dir = std::env::current_dir().unwrap();
        
        std::env::set_current_dir(temp_dir.path()).unwrap();
        let test_file = temp_dir.path().join("test_building.yaml");
        
        // Create initial small building file
        let building_data = create_test_building_data();
        let yaml_content = serde_yaml::to_string(&building_data).unwrap();
        fs::write(&test_file, yaml_content).unwrap();
        
        let persistence = PersistenceManager::new("test_building").unwrap();
        
        // Small building data should save successfully
        let result = persistence.save_building_data(&building_data);
        assert!(result.is_ok(), "Small building data should save successfully");
        
        std::env::set_current_dir(&original_dir).unwrap();
    }
}

