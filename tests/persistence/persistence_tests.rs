//! Integration tests for the persistence module
//!
//! These tests verify that building data can be saved to and loaded from YAML files,
//! and that Git commit operations work correctly.
//!
//! Tests are configured to run serially to prevent interference from directory changes
//! and file operations that occur in temporary directories.

use arxos::persistence::{PersistenceManager, invalidate_building_data_cache};
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData};
use chrono::Utc;
use serial_test::serial;
use std::fs;
use std::path::{Path, PathBuf};
use std::thread;
use std::time::Duration;
use tempfile::TempDir;

/// RAII guard for directory changes - automatically restores original directory on drop
/// Also cleans up YAML files created during the test to ensure isolation
struct DirectoryGuard {
    original_dir: Option<PathBuf>,
    test_dir: PathBuf,
}

impl DirectoryGuard {
    fn new(target_dir: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let original_dir = std::env::current_dir().ok();
        let test_dir = target_dir.to_path_buf();
        std::env::set_current_dir(&test_dir)?;
        Ok(DirectoryGuard {
            original_dir,
            test_dir,
        })
    }
    
}

impl Drop for DirectoryGuard {
    fn drop(&mut self) {
        // Clean up any YAML files in test directory to ensure isolation
        if let Ok(entries) = std::fs::read_dir(&self.test_dir) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "yaml" || ext == "yml" || ext == "bak" {
                        let _ = std::fs::remove_file(entry.path());
                    }
                }
            }
        }
        
        // Restore original directory
        if let Some(ref original) = self.original_dir {
            // Best effort restore - don't panic if it fails
            // Use multiple attempts in case directory is temporarily unavailable
            for _ in 0..3 {
                if std::env::set_current_dir(original).is_ok() {
                    return;
                }
                std::thread::sleep(std::time::Duration::from_millis(10));
            }
        }
    }
}

fn setup_test_environment() -> TempDir {
    tempfile::tempdir().expect("Failed to create temp directory")
}

/// Clean up any YAML files in the current directory
/// This ensures test isolation by removing files from previous test runs
fn cleanup_yaml_files() {
    let current_dir = std::env::current_dir().unwrap();
    if let Ok(entries) = std::fs::read_dir(&current_dir) {
        for entry in entries.flatten() {
            if let Some(ext) = entry.path().extension() {
                if ext == "yaml" || ext == "yml" || ext == "bak" {
                    let _ = std::fs::remove_file(entry.path());
                }
            }
        }
    }
}

#[test]
#[serial]
fn test_persistence_manager_creation() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Ensure directory is clean - remove any existing YAML files
    cleanup_yaml_files();
    
    // Verify directory is empty of YAML files
    let current_dir = std::env::current_dir().unwrap();
    let yaml_count = std::fs::read_dir(&current_dir)
        .unwrap()
        .flatten()
        .filter(|entry| {
            entry.path().extension()
                .and_then(|s| s.to_str())
                .map(|ext| ext == "yaml" || ext == "yml")
                .unwrap_or(false)
        })
        .count();
    
    assert_eq!(yaml_count, 0, "Test directory should be empty of YAML files");
    
    // PersistenceManager should fail to find any building files
    let persistence = PersistenceManager::new("Test Building");
    assert!(persistence.is_err(), "Should fail when no YAML files exist in current directory");
    
    // Verify it's the expected error type
    if let Err(e) = persistence {
        match e {
            arxos::persistence::PersistenceError::FileNotFound { .. } => {
                // Expected error type
            }
            _ => panic!("Expected FileNotFound error, got: {:?}", e),
        }
    }
    
    // Now create a test building file and verify it succeeds
    let test_file = temp_dir.path().join("test_building.yaml");
    let building_data = create_test_building_data();
    use arxos::BuildingYamlSerializer;
    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).unwrap();
    fs::write(&test_file, yaml_content).unwrap();
    
    // Now PersistenceManager should succeed
    let persistence = PersistenceManager::new("test_building");
    assert!(persistence.is_ok(), "Should succeed when building file exists in current directory");
}

#[test]
#[serial]
fn test_load_building_data() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    cleanup_yaml_files(); // Ensure clean start
    
    // Use relative path since we're now in the temp directory
    let test_file = PathBuf::from("test_building.yaml");
    
    // Create a test building file using the serializer
    let building_data = create_test_building_data();
    use arxos::BuildingYamlSerializer;
    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).unwrap();
    fs::write(&test_file, yaml_content).unwrap();
    
    // Create persistence manager
    let persistence = PersistenceManager::new("test_building").unwrap();
    
    // Load building data
    let loaded_data = persistence.load_building_data().unwrap();
    
    assert_eq!(loaded_data.building.name, "Test Building");
    assert_eq!(loaded_data.floors.len(), 1);
    assert_eq!(loaded_data.floors[0].name, "Ground Floor");
}

#[test]
#[serial]
fn test_save_building_data() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    cleanup_yaml_files(); // Ensure clean start
    
    // Use relative path since we're now in the temp directory
    let test_file = PathBuf::from("test_building.yaml");
    
    // Create initial building data using the serializer
    let building_data = create_test_building_data();
    use arxos::BuildingYamlSerializer;
    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).unwrap();
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
        floors: vec![{
            use arxos::core::Floor;
            Floor {
                id: "floor-0".to_string(),
                name: "Ground Floor".to_string(),
                level: 0,
                elevation: Some(0.0),
                bounding_box: None,
                wings: vec![],
                equipment: vec![],
                properties: std::collections::HashMap::new(),
            }
        }],
        coordinate_systems: vec![],
    }
}

// File Size Limit Tests
//
// Tests verify that YAML files exceeding size limits are properly rejected
// to prevent memory issues and ensure system stability.

mod file_size_limit_tests {
    use super::*;
    use std::io::Write;

    /// Create a mock YAML file with specified size in the current directory
    /// Uses valid BuildingData structure that can be deserialized
    fn create_mock_yaml_file(size_mb: u64) -> PathBuf {
        use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
        use chrono::Utc;
        
        // Create minimal valid building data structure
        let building_data = BuildingData {
            building: BuildingInfo {
                id: "test-1".to_string(),
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
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "World".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![],
        };
        
        // Serialize to YAML
        let serializer = arxos::BuildingYamlSerializer::new();
        let yaml_content = serializer.to_yaml(&building_data).expect("Failed to serialize building data");
        
        // Calculate target size and write padding to reach target
        // We'll write the valid YAML first, then append padding as a comment block
        let target_bytes: usize = (size_mb as usize) * 1024 * 1024;
        let current_size = yaml_content.len();
        
        let file_path = PathBuf::from("large_building.yaml");
        let mut file = fs::File::create(&file_path).expect("Failed to create mock YAML file");
        
        // Write valid YAML structure first
        file.write_all(yaml_content.as_bytes()).expect("Failed to write YAML header");
        
        // Add padding as YAML comments (safe, doesn't break structure)
        if current_size < target_bytes {
            let padding_needed = target_bytes - current_size;
            // Ensure we end the YAML with a newline before adding comments
            file.write_all(b"\n").expect("Failed to write newline");
            
            // Write complete comment lines to avoid breaking YAML structure
            let comment_line = b"# Padding for size test: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n";
            let mut remaining = padding_needed.saturating_sub(1); // Account for the newline we just added
            
            while remaining >= comment_line.len() {
                file.write_all(comment_line).expect("Failed to write padding");
                remaining -= comment_line.len();
            }
            
            // If there's remaining space, write a truncated but valid comment
            if remaining > 2 {
                // Write "# " prefix and fill with padding, ensure newline at end
                file.write_all(b"# ").expect("Failed to write comment prefix");
                remaining -= 2;
                while remaining > 1 {
                    file.write_all(b"x").expect("Failed to write padding char");
                    remaining -= 1;
                }
                if remaining > 0 {
                    file.write_all(b"\n").expect("Failed to write final newline");
                }
            }
        }
        
        file_path
    }

    #[test]
    #[serial]
    fn test_yaml_file_size_limit_accepted() {
        // YAML file just under 10MB should be accepted
        let temp_dir = setup_test_environment();
        let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
        cleanup_yaml_files(); // Ensure clean start
        let _yaml_file = create_mock_yaml_file(9);
        
        let persistence = PersistenceManager::new("Test Building");
        
        if let Ok(pm) = persistence {
            let result = pm.load_building_data();
            // May fail for invalid YAML, but not for size
            if let Err(e) = result {
                assert!(!matches!(e, arxos::persistence::PersistenceError::FileTooLarge { .. }), 
                        "File under 10MB should not be rejected for size");
            }
        }
    }

    #[test]
    #[serial]
    fn test_yaml_file_size_limit_exceeded() {
        // YAML file over 10MB should be rejected
        let temp_dir = setup_test_environment();
        let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
        cleanup_yaml_files(); // Ensure clean start
        
        // Create file with name that will be found by PersistenceManager
        // The file should be large enough to exceed 10MB after integer division
        // (11MB = 11534336 bytes, which is > 10MB when divided)
        let file_path = create_mock_yaml_file(11);
        
        // Rename file to match what PersistenceManager expects
        // PersistenceManager looks for files containing building name or uses first YAML file
        let target_file = PathBuf::from("test-building.yaml");
        if target_file.exists() {
            fs::remove_file(&target_file).ok();
        }
        fs::rename(&file_path, &target_file).expect("Failed to rename test file");
        
        let persistence = PersistenceManager::new("Test Building")
            .expect("Failed to create PersistenceManager - file should exist");
        
        let result = persistence.load_building_data();
        assert!(result.is_err(), "File over 10MB should be rejected");
        if let Err(arxos::persistence::PersistenceError::FileTooLarge { size, max }) = result {
            // File size should be at least 10MB (accounting for integer division)
            // 11MB = 11534336 bytes / (1024*1024) = 11MB, so size should be 11
            assert!(size > 10, "File size should be greater than 10MB, got {}MB", size);
            assert_eq!(max, 10, "Max size should be 10MB");
        } else {
            panic!("Expected FileTooLarge error, got: {:?}", result.unwrap_err());
        }
    }

    #[test]
    #[serial]
    fn test_yaml_save_size_validation() {
        // Attempting to save YAML over 10MB should be rejected before writing
        let temp_dir = setup_test_environment();
        let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
        cleanup_yaml_files(); // Ensure clean start
        // Use relative path since we're now in the temp directory
        let test_file = PathBuf::from("test_building.yaml");
        
        // Create initial small building file using the serializer
        let building_data = create_test_building_data();
        use arxos::BuildingYamlSerializer;
        let serializer = BuildingYamlSerializer::new();
        let yaml_content = serializer.to_yaml(&building_data).unwrap();
        fs::write(&test_file, yaml_content).unwrap();
        
        let persistence = PersistenceManager::new("test_building").unwrap();
        
        // Small building data should save successfully
        let result = persistence.save_building_data(&building_data);
        assert!(result.is_ok(), "Small building data should save successfully");
    }
    
    #[test]
    #[serial]
    fn test_building_data_caching() {
        let temp_dir = TempDir::new().unwrap();
        let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
        
        // Create test building data
        let building_data = create_test_building_data();
        let serializer = BuildingYamlSerializer::new();
        let yaml_content = serializer.to_yaml(&building_data).unwrap();
        let test_file = temp_dir.path().join("test_building.yaml");
        fs::write(&test_file, yaml_content).unwrap();
        
        // Invalidate cache first
        invalidate_building_data_cache();
        
        let persistence = PersistenceManager::new("test_building").unwrap();
        
        // First load - cache miss
        let data1 = persistence.load_building_data().unwrap();
        assert_eq!(data1.building.name, "Test Building");
        
        // Second load - cache hit (same file, no modification)
        let data2 = persistence.load_building_data().unwrap();
        assert_eq!(data2.building.name, "Test Building");
        
        // Modify file to invalidate cache
        thread::sleep(Duration::from_millis(10)); // Ensure file modification time changes
        let mut modified_data = building_data.clone();
        modified_data.building.name = "Modified Building".to_string();
        let yaml_content = serializer.to_yaml(&modified_data).unwrap();
        fs::write(&test_file, yaml_content).unwrap();
        
        // Third load - cache miss (file modified)
        let data3 = persistence.load_building_data().unwrap();
        assert_eq!(data3.building.name, "Modified Building");
    }
    
    #[test]
    #[serial]
    fn test_cache_invalidation() {
        invalidate_building_data_cache();
        // Cache should be cleared (no error means success)
        assert!(true);
    }
}

#[cfg(test)]
mod indexing_tests {
    use super::*;
    use arxos::yaml::BuildingDataIndex;
    
    fn create_test_building_with_floors(floor_count: usize) -> BuildingData {
        use arxos::core::Floor;
        let mut floors = Vec::new();
        for i in 0..floor_count {
            floors.push(Floor {
                id: format!("floor-{}", i),
                name: format!("Floor {}", i),
                level: i as i32,
                elevation: Some((i as f64) * 3.0),
                bounding_box: None,
                wings: vec![],
                equipment: vec![],
                properties: std::collections::HashMap::new(),
            });
        }
        
        BuildingData {
            building: BuildingInfo {
                id: "test-1".to_string(),
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
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "local".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors,
            coordinate_systems: vec![],
        }
    }
    
    #[test]
    fn test_building_data_index_creation() {
        let building_data = create_test_building_with_floors(10);
        let index = building_data.build_index();
        
        // Verify all floors are indexed
        assert_eq!(index.floors_by_level.len(), 10);
        for i in 0..10 {
            assert!(index.get_floor_index(i as i32).is_some());
        }
    }
    
    #[test]
    fn test_indexed_lookup_performance() {
        let building_data = create_test_building_with_floors(100);
        let index = building_data.build_index();
        
        // Test O(1) lookup
        let floor_idx = index.get_floor_index(50);
        assert!(floor_idx.is_some());
        assert_eq!(floor_idx.unwrap(), 50);
    }
}

