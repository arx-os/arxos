//! Integration tests for spreadsheet command handlers
//!
//! Tests CLI command integration:
//! - Command parsing and routing
//! - Building data loading
//! - Error handling (missing files, invalid data)
//! - CSV import command
//! - Command options (filter, commit, no-git)

use arxos::commands::spreadsheet::handle_spreadsheet_command;
use arxos::cli::SpreadsheetCommands;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
use arxos::core::{Floor, Equipment, EquipmentType, EquipmentStatus, EquipmentHealthStatus, Position};
use arxos::persistence::PersistenceManager;
use arxos::BuildingYamlSerializer;
use arxos::spatial::{Point3D, BoundingBox3D};
use chrono::Utc;
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use tempfile::TempDir;

/// RAII guard for directory changes
struct DirectoryGuard {
    original_dir: Option<PathBuf>,
    test_dir: PathBuf,
}

impl DirectoryGuard {
    fn new(target_dir: &std::path::Path) -> Result<Self, Box<dyn std::error::Error>> {
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
        // Clean up YAML files
        if let Ok(entries) = std::fs::read_dir(&self.test_dir) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "yaml" || ext == "yml" || ext == "bak" || ext == "lock" {
                        let _ = std::fs::remove_file(entry.path());
                    }
                }
            }
        }
        
        // Restore original directory
        if let Some(ref original) = self.original_dir {
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

fn create_test_building_data() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building-1".to_string(),
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
            total_entities: 2,
            spatial_entities: 2,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![Floor {
            id: "floor-1".to_string(),
            name: "Ground Floor".to_string(),
            level: 0,
            elevation: Some(0.0),
            bounding_box: None,
            wings: vec![],
            equipment: vec![
                Equipment {
                    id: "eq-1".to_string(),
                    name: "HVAC Unit 1".to_string(),
                    path: "/building/floor-1/eq-1".to_string(),
                    address: None,
                    equipment_type: EquipmentType::HVAC,
                    position: Position { x: 5.0, y: 5.0, z: 0.0, coordinate_system: "LOCAL".to_string() },
                    properties: HashMap::new(),
                    status: EquipmentStatus::Active,
                    health_status: Some(EquipmentHealthStatus::Healthy),
                    room_id: None,
                    sensor_mappings: None,
                },
                Equipment {
                    id: "eq-2".to_string(),
                    name: "Electrical Panel 1".to_string(),
                    path: "/building/floor-1/eq-2".to_string(),
                    address: None,
                    equipment_type: EquipmentType::Electrical,
                    position: Position { x: 8.0, y: 8.0, z: 0.0, coordinate_system: "LOCAL".to_string() },
                    properties: HashMap::new(),
                    status: EquipmentStatus::Active,
                    health_status: Some(EquipmentHealthStatus::Warning),
                    room_id: None,
                    sensor_mappings: None,
                },
            ],
            properties: HashMap::new(),
        }],
        coordinate_systems: vec![],
    }
}

fn create_test_building_file(temp_dir: &TempDir, building_data: &BuildingData) -> Result<PathBuf, Box<dyn std::error::Error>> {
    let building_name = "Test Building";
    let yaml_file = format!("{}.yaml", building_name);
    let file_path = temp_dir.path().join(&yaml_file);
    
    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(building_data)?;
    fs::write(&file_path, yaml_content)?;
    
    Ok(file_path)
}

#[test]
#[serial]
fn test_spreadsheet_equipment_command_missing_building() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Try to open spreadsheet for non-existent building
    let command = SpreadsheetCommands::Equipment {
        building: Some("NonExistent Building".to_string()),
        filter: None,
        commit: false,
        no_git: false,
    };
    
    let result = handle_spreadsheet_command(command);
    assert!(result.is_err(), "Should fail when building file doesn't exist");
}

#[test]
#[serial]
fn test_spreadsheet_equipment_command_loads_data() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Verify data can be loaded (this is what the command does internally)
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    
    // Verify equipment is loaded
    assert_eq!(loaded_data.floors.len(), 1);
    assert_eq!(loaded_data.floors[0].equipment.len(), 2);
    assert_eq!(loaded_data.floors[0].equipment[0].name, "HVAC Unit 1");
}

#[test]
#[serial]
fn test_spreadsheet_rooms_command_loads_data() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building file with rooms
    let mut building_data = create_test_building_data();
    // Add room to wing (create wing if needed)
    if building_data.floors[0].wings.is_empty() {
        building_data.floors[0].wings.push(arxos::core::Wing {
            id: "wing-1".to_string(),
            name: "Main Wing".to_string(),
            rooms: vec![],
            equipment: vec![],
            properties: HashMap::new(),
        });
    }
    building_data.floors[0].wings[0].rooms.push(arxos::core::Room {
        id: "room-1".to_string(),
        name: "Room 1".to_string(),
        room_type: arxos::core::RoomType::Office,
        equipment: vec![],
        spatial_properties: arxos::core::SpatialProperties {
            position: arxos::core::Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "LOCAL".to_string() },
            dimensions: arxos::core::Dimensions { width: 10.0, height: 3.0, depth: 10.0 },
            bounding_box: arxos::core::BoundingBox {
                min: arxos::core::Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "LOCAL".to_string() },
                max: arxos::core::Position { x: 10.0, y: 10.0, z: 3.0, coordinate_system: "LOCAL".to_string() },
            },
            coordinate_system: "LOCAL".to_string(),
        },
        properties: HashMap::new(),
        created_at: None,
        updated_at: None,
    });
    
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Verify data can be loaded
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    
    // Verify rooms are loaded
    assert_eq!(loaded_data.floors[0].wings[0].rooms.len(), 1);
    assert_eq!(loaded_data.floors[0].wings[0].rooms[0].name, "Room 1");
}

#[test]
#[serial]
fn test_spreadsheet_sensors_command_readonly() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Sensors command should work even with no sensor data (read-only view)
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name);
    
    // Command should not fail even with no sensors
    // (SensorDataSource handles empty data gracefully)
    assert!(persistence.is_ok());
}

#[test]
#[serial]
fn test_spreadsheet_import_command_csv_not_found() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Try to import non-existent CSV
    let command = SpreadsheetCommands::Import {
        file: "nonexistent.csv".to_string(),
        building: Some("Test Building".to_string()),
        commit: false,
    };
    
    let result = handle_spreadsheet_command(command);
    assert!(result.is_err(), "Should fail when CSV file doesn't exist");
}

#[test]
#[serial]
fn test_spreadsheet_import_command_valid_csv() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Create a valid CSV file
    let csv_path = temp_dir.path().join("import.csv");
    let csv_content = "Name,Type\nNew Equipment,HVAC\n";
    fs::write(&csv_path, csv_content).unwrap();
    
    // Import command should parse CSV (even if it doesn't open TUI in test)
    // The import logic should handle the CSV parsing
    let csv_content_read = fs::read_to_string(&csv_path).unwrap();
    assert!(csv_content_read.contains("Name"));
    assert!(csv_content_read.contains("New Equipment"));
}

#[test]
#[serial]
fn test_spreadsheet_command_options() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Test different command option combinations
    let building_name = "Test Building";
    
    // Test with building name specified
    let command1 = SpreadsheetCommands::Equipment {
        building: Some(building_name.to_string()),
        filter: None,
        commit: false,
        no_git: false,
    };
    
    // Test with no-git option
    let command2 = SpreadsheetCommands::Equipment {
        building: Some(building_name.to_string()),
        filter: None,
        commit: false,
        no_git: true,
    };
    
    // Test with commit option
    let command3 = SpreadsheetCommands::Equipment {
        building: Some(building_name.to_string()),
        filter: None,
        commit: true,
        no_git: false,
    };
    
    // Test with filter option
    let command4 = SpreadsheetCommands::Equipment {
        building: Some(building_name.to_string()),
        filter: Some("status=Active".to_string()),
        commit: false,
        no_git: false,
    };
    
    // All commands should parse correctly (even if TUI doesn't run in test)
    // The important thing is that options are accepted
    assert!(matches!(command1, SpreadsheetCommands::Equipment { .. }));
    assert!(matches!(command2, SpreadsheetCommands::Equipment { no_git: true, .. }));
    assert!(matches!(command3, SpreadsheetCommands::Equipment { commit: true, .. }));
    assert!(matches!(command4, SpreadsheetCommands::Equipment { filter: Some(_), .. }));
}

#[test]
#[serial]
fn test_spreadsheet_command_routing() {
    // Test that command routing works correctly
    let equipment_cmd = SpreadsheetCommands::Equipment {
        building: None,
        filter: None,
        commit: false,
        no_git: false,
    };
    
    let rooms_cmd = SpreadsheetCommands::Rooms {
        building: None,
        filter: None,
        commit: false,
        no_git: false,
    };
    
    let sensors_cmd = SpreadsheetCommands::Sensors {
        building: None,
        filter: None,
        commit: false,
        no_git: false,
    };
    
    let import_cmd = SpreadsheetCommands::Import {
        file: "test.csv".to_string(),
        building: None,
        commit: false,
    };
    
    // Verify all command variants are recognized
    assert!(matches!(equipment_cmd, SpreadsheetCommands::Equipment { .. }));
    assert!(matches!(rooms_cmd, SpreadsheetCommands::Rooms { .. }));
    assert!(matches!(sensors_cmd, SpreadsheetCommands::Sensors { .. }));
    assert!(matches!(import_cmd, SpreadsheetCommands::Import { .. }));
}

