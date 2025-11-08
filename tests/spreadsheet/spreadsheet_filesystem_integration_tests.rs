//! Integration tests for spreadsheet file system operations
//!
//! Tests file system integration:
//! - YAML persistence with backups
//! - Git staging and commit operations
//! - File locking during edits
//! - Conflict detection

use arxos::core::{
    Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType, Floor, Position,
};
use arxos::persistence::PersistenceManager;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
use arxos::BuildingYamlSerializer;
use arxui::tui::spreadsheet::data_source::{EquipmentDataSource, SpreadsheetDataSource};
use arxui::tui::spreadsheet::types::{CellValue, ColumnDefinition};
use arxui::tui::spreadsheet::workflow::{ConflictDetector, FileLock};
use chrono::Utc;
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::thread;
use std::time::Duration;
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
                thread::sleep(Duration::from_millis(10));
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
            total_entities: 1,
            spatial_entities: 1,
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
            equipment: vec![Equipment {
                id: "eq-1".to_string(),
                name: "HVAC Unit 1".to_string(),
                path: "/building/floor-1/eq-1".to_string(),
                address: None,
                equipment_type: EquipmentType::HVAC,
                position: Position {
                    x: 5.0,
                    y: 5.0,
                    z: 0.0,
                    coordinate_system: "LOCAL".to_string(),
                },
                status: EquipmentStatus::Active,
                health_status: Some(EquipmentHealthStatus::Healthy),
                properties: HashMap::new(),
                room_id: None,
                sensor_mappings: None,
            }],
            properties: HashMap::new(),
        }],
        coordinate_systems: vec![],
    }
}

fn create_test_building_file(
    temp_dir: &TempDir,
    building_data: &BuildingData,
) -> Result<PathBuf, Box<dyn std::error::Error>> {
    let building_name = "Test Building";
    let yaml_file = format!("{}.yaml", building_name);
    let file_path = temp_dir.path().join(&yaml_file);

    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(building_data)?;
    fs::write(&file_path, yaml_content)?;

    Ok(file_path)
}

fn column_index(columns: &[ColumnDefinition], id: &str) -> usize {
    columns
        .iter()
        .position(|col| col.id == id)
        .unwrap_or_else(|| panic!("Column {id} not found"))
}

#[test]
#[serial]
fn test_yaml_persistence_with_backup() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();

    // Create initial building file
    let building_data = create_test_building_data();
    let file_path = create_test_building_file(&temp_dir, &building_data).unwrap();
    let backup_path = file_path.with_extension("yaml.bak");

    // Load and modify via data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let mut data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());

    // Edit
    let columns = data_source.columns();
    let name_col = column_index(&columns, "equipment.name");
    data_source
        .set_cell(0, name_col, CellValue::Text("Updated Name".to_string()))
        .unwrap();

    // Save (should create backup)
    data_source.save(false).unwrap();

    // Verify backup file was created
    assert!(backup_path.exists(), "Backup file should be created");
}

#[test]
#[serial]
fn test_git_staging() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();

    // Initialize Git repo
    let repo_path = temp_dir.path().to_str().unwrap();
    let _ = git2::Repository::init(repo_path);

    // Create building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();

    // Load and modify
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let mut data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());

    // Edit
    let columns = data_source.columns();
    let name_col = column_index(&columns, "equipment.name");
    data_source
        .set_cell(0, name_col, CellValue::Text("Git Staged".to_string()))
        .unwrap();

    // Save with staging (no commit)
    data_source.save(false).unwrap();

    // Verify file was modified
    let persistence2 = PersistenceManager::new(building_name).unwrap();
    let reloaded = persistence2.load_building_data().unwrap();
    assert_eq!(reloaded.floors[0].equipment[0].name, "Git Staged");
}

#[test]
#[serial]
fn test_file_locking() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();

    // Create building file
    let building_data = create_test_building_data();
    let building_file = create_test_building_file(&temp_dir, &building_data).unwrap();

    // Acquire lock using the building file path (FileLock creates .yaml.lock automatically)
    let lock = FileLock::acquire(&building_file).unwrap();

    // Verify lock file exists (has .yaml.lock extension)
    let lock_file_path = lock.lock_file().to_path_buf();
    assert!(lock_file_path.exists(), "Lock file should exist");

    // Try to acquire lock again (should fail because current process has it)
    let second_lock = FileLock::acquire(&building_file);
    assert!(
        second_lock.is_err(),
        "Second lock acquisition should fail when lock is active"
    );

    // Release the first lock
    lock.release().unwrap();

    // Verify lock file is removed
    assert!(
        !lock_file_path.exists(),
        "Lock file should be removed after release"
    );

    // Now we should be able to acquire the lock again
    let final_lock = FileLock::acquire(&building_file);
    assert!(
        final_lock.is_ok(),
        "Should be able to acquire lock after release"
    );
    final_lock.unwrap().release().unwrap();
}

#[test]
#[serial]
fn test_conflict_detection() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();

    // Create building file
    let building_data = create_test_building_data();
    let file_path = create_test_building_file(&temp_dir, &building_data).unwrap();

    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let _data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());

    // Create conflict detector (this captures the initial modification time)
    let conflict_detector = ConflictDetector::new(&file_path).unwrap();

    // Simulate external change by modifying file directly
    let mut modified_data = create_test_building_data();
    modified_data.floors[0].equipment[0].name = "Externally Modified".to_string();
    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&modified_data).unwrap();
    fs::write(&file_path, yaml_content).unwrap();

    // Wait a bit to ensure different modification time
    thread::sleep(Duration::from_millis(100));

    // Check for conflict (should detect the external modification)
    let has_conflict = conflict_detector.check_conflict().unwrap();
    assert!(has_conflict, "Should detect external modification");
}

#[test]
#[serial]
fn test_save_with_git_commit() {
    let temp_dir = setup_test_environment();
    let _guard = DirectoryGuard::new(temp_dir.path()).unwrap();

    // Initialize Git repo
    let repo_path = temp_dir.path().to_str().unwrap();
    let _ = git2::Repository::init(repo_path);

    // Create and commit initial building file
    let building_data = create_test_building_data();
    create_test_building_file(&temp_dir, &building_data).unwrap();

    // Initial commit
    let repo = git2::Repository::open(repo_path).unwrap();
    let mut index = repo.index().unwrap();
    index
        .add_all(["*"], git2::IndexAddOption::DEFAULT, None)
        .unwrap();
    index.write().unwrap();
    let tree_id = index.write_tree().unwrap();
    let tree = repo.find_tree(tree_id).unwrap();
    let signature = git2::Signature::now("Test", "test@test.com").unwrap();
    repo.commit(
        Some("HEAD"),
        &signature,
        &signature,
        "Initial commit",
        &tree,
        &[],
    )
    .unwrap();

    // Load and modify via data source
    let building_name = "Test Building";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let loaded_data = persistence.load_building_data().unwrap();
    let mut data_source = EquipmentDataSource::new(loaded_data, building_name.to_string());

    // Edit
    let columns = data_source.columns();
    let name_col = column_index(&columns, "equipment.name");
    data_source
        .set_cell(0, name_col, CellValue::Text("Committed Change".to_string()))
        .unwrap();

    // Save with commit
    data_source.save(true).unwrap();

    // Verify commit was created
    let head = repo.head().unwrap();
    let commit = head.peel_to_commit().unwrap();
    assert!(
        commit.message().unwrap().contains("equipment")
            || commit.message().unwrap().contains("spreadsheet")
    );
}
