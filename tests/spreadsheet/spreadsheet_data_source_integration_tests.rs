//! Integration tests for spreadsheet data source workflows
//!
//! Tests end-to-end workflows:
//! - Load → Edit → Save → Reload cycle
//! - Git integration (staging and commit)
//! - Multi-floor data handling
//! - ID-based equipment/room matching

use arxos::ui::spreadsheet::data_source::{EquipmentDataSource, RoomDataSource, SpreadsheetDataSource};
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, RoomData, EquipmentStatus};
use arxos::spatial::{Point3D, BoundingBox3D};
use arxos::persistence::PersistenceManager;
use arxos::BuildingYamlSerializer;
use chrono::Utc;
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use tempfile::TempDir;

/// RAII guard for directory changes - automatically restores original directory on drop
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
        // Clean up any YAML files in test directory
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
            description: Some("Test building for integration tests".to_string()),
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
        floors: vec![
            FloorData {
                id: "floor-1".to_string(),
                name: "Ground Floor".to_string(),
                level: 0,
                elevation: 0.0,
                rooms: vec![
                    RoomData {
                        id: "room-1".to_string(),
                        name: "Room 1".to_string(),
                        room_type: "Office".to_string(),
                        area: Some(100.0),
                        volume: Some(300.0),
                        position: Point3D::new(0.0, 0.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(0.0, 0.0, 0.0),
                            Point3D::new(10.0, 10.0, 3.0),
                        ),
                        equipment: vec![],
                        properties: HashMap::new(),
                    },
                ],
                equipment: vec![
                    EquipmentData {
                        id: "eq-1".to_string(),
                        name: "HVAC Unit 1".to_string(),
                        equipment_type: "HVAC".to_string(),
                        system_type: "HVAC".to_string(),
                        position: Point3D::new(5.0, 5.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(4.0, 4.0, 0.0),
                            Point3D::new(6.0, 6.0, 2.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "/building/floor-1/eq-1".to_string(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        id: "eq-2".to_string(),
                        name: "Electrical Panel 1".to_string(),
                        equipment_type: "Electrical".to_string(),
                        system_type: "Electrical".to_string(),
                        position: Point3D::new(8.0, 8.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(7.0, 7.0, 0.0),
                            Point3D::new(9.0, 9.0, 1.5),
                        ),
                        status: EquipmentStatus::Warning,
                        properties: HashMap::new(),
                        universal_path: "/building/floor-1/eq-2".to_string(),
                        sensor_mappings: None,
                    },
                ],
                bounding_box: None,
            },
        ],
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
fn test_equipment_data_source_full_cycle() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create initial building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Load data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let mut data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());
    
    // Verify initial state
    assert_eq!(data_source.row_count(), 2);
    let original_name = data_source.get_cell(0, 1).unwrap(); // Name column
    assert_eq!(original_name.to_string(), "HVAC Unit 1");
    
    // Edit a cell
    use arxos::ui::spreadsheet::types::CellValue;
    let new_name = CellValue::Text("Updated HVAC Unit".to_string());
    data_source.set_cell(0, 1, new_name.clone()).unwrap();
    
    // Verify change in memory
    let updated_name = data_source.get_cell(0, 1).unwrap();
    assert_eq!(updated_name, new_name);
    
    // Save (stage only, no commit)
    data_source.save(false).unwrap();
    
    // Reload from file
    data_source.reload().unwrap();
    
    // Verify change persisted
    let reloaded_name = data_source.get_cell(0, 1).unwrap();
    assert_eq!(reloaded_name, CellValue::Text("Updated HVAC Unit".to_string()));
}

#[test]
#[serial]
fn test_room_data_source_full_cycle() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create initial building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Load data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let mut data_source = RoomDataSource::new(loaded_data, building_name.to_string());
    
    // Verify initial state
    assert_eq!(data_source.row_count(), 1);
    let original_name = data_source.get_cell(0, 1).unwrap(); // Name column
    assert_eq!(original_name.to_string(), "Room 1");
    
    // Edit a cell
    use arxos::ui::spreadsheet::types::CellValue;
    let new_name = CellValue::Text("Updated Room 1".to_string());
    data_source.set_cell(0, 1, new_name.clone()).unwrap();
    
    // Verify change in memory
    let updated_name = data_source.get_cell(0, 1).unwrap();
    assert_eq!(updated_name, new_name);
    
    // Save (stage only, no commit)
    data_source.save(false).unwrap();
    
    // Reload from file
    data_source.reload().unwrap();
    
    // Verify change persisted
    let reloaded_name = data_source.get_cell(0, 1).unwrap();
    assert_eq!(reloaded_name, CellValue::Text("Updated Room 1".to_string()));
}

#[test]
#[serial]
fn test_data_source_id_matching() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create initial building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Load data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let mut data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());
    
    // Edit equipment at row 1 (eq-2)
    use arxos::ui::spreadsheet::types::CellValue;
    let new_name = CellValue::Text("Updated Panel".to_string());
    data_source.set_cell(1, 1, new_name.clone()).unwrap(); // Edit row 1, column 1 (name)
    
    // Save
    data_source.save(false).unwrap();
    
    // Reload
    data_source.reload().unwrap();
    
    // Verify the correct equipment (eq-2) was updated, not eq-1
    let eq1_name = data_source.get_cell(0, 1).unwrap();
    assert_eq!(eq1_name.to_string(), "HVAC Unit 1"); // Should be unchanged
    
    let eq2_name = data_source.get_cell(1, 1).unwrap();
    assert_eq!(eq2_name, CellValue::Text("Updated Panel".to_string())); // Should be updated
}

#[test]
#[serial]
fn test_data_source_multiple_edits() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create initial building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Load data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let mut data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());
    
    // Edit multiple cells
    use arxos::ui::spreadsheet::types::CellValue;
    data_source.set_cell(0, 1, CellValue::Text("HVAC Updated".to_string())).unwrap();
    data_source.set_cell(1, 1, CellValue::Text("Panel Updated".to_string())).unwrap();
    
    // Save
    data_source.save(false).unwrap();
    
    // Reload
    data_source.reload().unwrap();
    
    // Verify both changes persisted
    assert_eq!(data_source.get_cell(0, 1).unwrap(), CellValue::Text("HVAC Updated".to_string()));
    assert_eq!(data_source.get_cell(1, 1).unwrap(), CellValue::Text("Panel Updated".to_string()));
}

#[test]
#[serial]
fn test_data_source_empty_building() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building with no equipment
    let mut building_data = create_test_building_data();
    building_data.floors[0].equipment.clear();
    
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Load data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());
    
    // Verify empty data source
    assert_eq!(data_source.row_count(), 0);
}

#[test]
#[serial]
fn test_data_source_multiple_floors() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();
    
    // Create building with multiple floors
    let mut building_data = create_test_building_data();
    building_data.floors.push(FloorData {
        id: "floor-2".to_string(),
        name: "Second Floor".to_string(),
        level: 1,
        elevation: 3.0,
        rooms: vec![],
        equipment: vec![
            EquipmentData {
                id: "eq-3".to_string(),
                name: "HVAC Unit 2".to_string(),
                equipment_type: "HVAC".to_string(),
                system_type: "HVAC".to_string(),
                position: Point3D::new(5.0, 5.0, 3.0),
                bounding_box: BoundingBox3D::new(
                    Point3D::new(4.0, 4.0, 3.0),
                    Point3D::new(6.0, 6.0, 5.0),
                ),
                status: EquipmentStatus::Healthy,
                properties: HashMap::new(),
                universal_path: "/building/floor-2/eq-3".to_string(),
                sensor_mappings: None,
            },
        ],
        bounding_box: None,
    });
    
    create_test_building_file(&temp_dir, &building_data).unwrap();
    
    // Load data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());
    
    // Verify all equipment from all floors is loaded
    assert_eq!(data_source.row_count(), 3); // 2 from floor 1, 1 from floor 2
    
    // Verify equipment from second floor is accessible
    let floor2_eq = data_source.get_cell(2, 1).unwrap();
    assert_eq!(floor2_eq.to_string(), "HVAC Unit 2");
}

