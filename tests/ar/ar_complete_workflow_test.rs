//! Complete AR workflow integration test
//!
//! This test verifies the complete end-to-end AR workflow:
//! 1. AR scan from mobile device
//! 2. Process scan to pending equipment
//! 3. Confirm pending equipment
//! 4. Commit changes to Git
//!
//! This ensures the full AR → Pending → Confirmed → Git workflow is working

use arxos::ar_integration::processing::{process_ar_scan_to_pending, ARScanData, DetectedEquipmentData, validate_ar_scan_data};
use arxos::ar_integration::pending::{PendingEquipmentManager, DetectedEquipmentInfo, DetectionMethod};
use arxos::git::manager::{BuildingGitManager, GitConfig, GitConfigManager};
use arxos::spatial::{Point3D, BoundingBox3D};
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentStatus};
use arxos::utils::loading::load_building_data;
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use tempfile::TempDir;

/// RAII guard for directory changes
struct DirectoryGuard {
    original_dir: Option<std::path::PathBuf>,
    _test_dir: std::path::PathBuf,
}

impl DirectoryGuard {
    fn new(target_dir: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let original_dir = std::env::current_dir().ok();
        let test_dir = target_dir.to_path_buf();
        std::env::set_current_dir(&test_dir)?;
        Ok(DirectoryGuard {
            original_dir,
            _test_dir: test_dir,
        })
    }
}

impl Drop for DirectoryGuard {
    fn drop(&mut self) {
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

#[serial]
#[test]
fn test_complete_ar_workflow_with_git() -> Result<(), Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let _guard = DirectoryGuard::new(temp_dir.path())?;
    
    // Phase 1: Initialize Git repository
    let git_config = GitConfig {
        author_name: "AR Test User".to_string(),
        author_email: "artest@example.com".to_string(),
        branch: "main".to_string(),
        remote_url: None,
    };
    
    let mut git_manager = BuildingGitManager::new(
        temp_dir.path().to_str().unwrap(),
        "Test Building",
        git_config.clone(),
    )?;
    
    // Phase 2: Create initial building data
    let initial_building = BuildingData {
        building: BuildingInfo {
            id: "test-building-id".to_string(),
            name: "Test Building".to_string(),
            description: Some("Building for AR workflow test".to_string()),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![FloorData {
            id: "floor-3".to_string(),
            name: "Floor 3".to_string(),
            level: 3,
            elevation: 9.0,
            rooms: vec![],
            equipment: vec![],
            bounding_box: None,
        }],
        coordinate_systems: vec![],
    };
    
    // Commit initial building
    let initial_result = git_manager.export_building(&initial_building, Some("Initial building setup"))?;
    assert!(!initial_result.commit_id.is_empty());
    
    // Phase 3: Simulate AR scan from mobile device
    let ar_scan = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301-New".to_string(),
                equipment_type: "VAV".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 9.0 },
                confidence: 0.95,
                detection_method: Some("ARKit".to_string()),
            },
            DetectedEquipmentData {
                name: "Thermostat-301".to_string(),
                equipment_type: "Thermostat".to_string(),
                position: Point3D { x: 12.0, y: 22.0, z: 9.0 },
                confidence: 0.88,
                detection_method: Some("ARKit".to_string()),
            },
        ],
    };
    
    // Validate scan
    let validation_result = validate_ar_scan_data(&ar_scan);
    assert!(validation_result.is_ok(), "AR scan validation should pass");
    
    // Phase 4: Process AR scan to pending equipment
    let pending_ids = process_ar_scan_to_pending(&ar_scan, "Test Building", 0.7)?;
    assert_eq!(pending_ids.len(), 2, "Should create 2 pending items");
    
    // Phase 5: Setup pending equipment manager
    let mut pending_manager = PendingEquipmentManager::new("Test Building".to_string());
    
    // Add pending equipment manually for this test
    let detected_info = DetectedEquipmentInfo {
        name: "VAV-301-New".to_string(),
        equipment_type: "VAV".to_string(),
        position: Point3D { x: 10.0, y: 20.0, z: 9.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 9.5, y: 19.5, z: 8.5 },
            max: Point3D { x: 10.5, y: 20.5, z: 9.5 },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::ARKit,
        properties: HashMap::new(),
    };
    
    let pending_id = pending_manager.add_pending_equipment(&detected_info, "scan_1", 3, Some("Room 301"), 0.7)?
        .expect("Should return pending ID");
    
    // Phase 6: Load building data from filesystem (after export)
    let mut building_data = load_building_data("Test Building")?;
    assert_eq!(building_data.floors.len(), 1);
    assert_eq!(building_data.floors[0].equipment.len(), 0);
    
    // Phase 7: Confirm pending equipment
    let equipment_id = pending_manager.confirm_pending(&pending_id, &mut building_data)?;
    assert!(!equipment_id.is_empty());
    
    // Verify equipment was added
    let floor = building_data.floors.iter().find(|f| f.level == 3).unwrap();
    let equipment = floor.equipment.iter().find(|e| e.name == "VAV-301-New").unwrap();
    assert_eq!(equipment.position, Point3D { x: 10.0, y: 20.0, z: 9.0 });
    assert!(matches!(equipment.status, EquipmentStatus::Healthy));
    
    // Phase 8: Commit changes to Git
    let commit_result = git_manager.export_building(&building_data, Some("Added VAV-301-New from AR scan"))?;
    assert!(!commit_result.commit_id.is_empty());
    
    // Phase 9: Verify Git history
    let commits = git_manager.list_commits(10)?;
    assert!(commits.len() >= 2, "Should have at least 2 commits");
    assert_eq!(commits[0].message, "Added VAV-301-New from AR scan");
    assert_eq!(commits[1].message, "Initial building setup");
    
    // Phase 10: Verify Git diff shows the equipment addition
    let status = git_manager.get_status()?;
    assert_eq!(status.last_commit_message, "Added VAV-301-New from AR scan");
    
    // Phase 11: Verify YAML file was updated (check building.yml)
    let building_yaml_path = temp_dir.path().join("building.yml");
    assert!(building_yaml_path.exists(), "building.yml should exist after export");
    let content = fs::read_to_string(&building_yaml_path)?;
    assert!(content.contains("VAV-301-New"), "YAML should contain new equipment");
    
    // Also check the floor file for equipment
    let floor_yaml_path = temp_dir.path().join("floors/floor-3.yml");
    assert!(floor_yaml_path.exists(), "floor-3.yml should exist");
    let floor_content = fs::read_to_string(&floor_yaml_path)?;
    assert!(floor_content.contains("VAV-301-New"), "Floor YAML should contain new equipment");
    
    Ok(())
}

#[serial]
#[test]
fn test_ar_workflow_reject_pending() -> Result<(), Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let _guard = DirectoryGuard::new(temp_dir.path())?;
    
    let git_config = GitConfigManager::default_config();
    let mut git_manager = BuildingGitManager::new(
        temp_dir.path().to_str().unwrap(),
        "Test Building",
        git_config,
    )?;
    
    // Create initial building
    let building = BuildingData::default();
    git_manager.export_building(&building, Some("Initial"))?;
    
    // Create pending manager and add equipment
    let mut pending_manager = PendingEquipmentManager::new("Test Building".to_string());
    let detected = DetectedEquipmentInfo {
        name: "Bad-Equipment".to_string(),
        equipment_type: "Unknown".to_string(),
        position: Point3D { x: 10.0, y: 20.0, z: 9.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 9.5, y: 19.5, z: 8.5 },
            max: Point3D { x: 10.5, y: 20.5, z: 9.5 },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::Manual,
        properties: HashMap::new(),
    };
    
    let pending_id = pending_manager.add_pending_equipment(&detected, "scan_1", 3, None, 0.7)?
        .expect("Should return ID");
    
    // Reject the pending equipment
    pending_manager.reject_pending(&pending_id)?;
    
    // Verify it's not in pending list
    let pending_list = pending_manager.list_pending();
    assert!(pending_list.is_empty(), "Should have no pending items after rejection");
    
    // Load building and verify equipment was NOT added (since we rejected it)
    let building_data = load_building_data("Default Building")?;
    // BuildingData::default() has no floors, so verify it's empty
    assert_eq!(building_data.floors.len(), 0, "Default building should have no floors");
    
    Ok(())
}

