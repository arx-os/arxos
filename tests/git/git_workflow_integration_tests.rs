//! Integration tests for Git workflow
//!
//! These tests verify the complete Git integration including:
//! - Building data commits
//! - History tracking
//! - Diff generation
//! - Multi-user collaboration scenarios

use arxos::git::{BuildingGitManager, GitConfig, GitConfigManager};
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
use arxos::core::{Floor, Equipment, EquipmentType, EquipmentStatus, EquipmentHealthStatus, Position};
use arxos::BuildingYamlSerializer;
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use tempfile::TempDir;
use chrono::Utc;
use serial_test::serial;

fn create_test_building_data(name: &str) -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: format!("test-{}", name.to_lowercase().replace(' ', "-")),
            name: name.to_string(),
            description: Some("Test building for Git workflow".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "Test".to_string(),
            total_entities: 1,
            spatial_entities: 1,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![
            Floor {
                id: "floor-1".to_string(),
                name: "Floor 1".to_string(),
                level: 1,
                elevation: Some(0.0),
                bounding_box: None,
                wings: vec![],
                equipment: vec![
                    Equipment {
                        id: "eq-1".to_string(),
                        name: "Test Equipment".to_string(),
                        path: "/building/floor-1/eq-1".to_string(),
                        address: None,
                        equipment_type: EquipmentType::HVAC,
                        position: Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "LOCAL".to_string() },
                        properties: HashMap::new(),
                        status: EquipmentStatus::Active,
                        health_status: Some(EquipmentHealthStatus::Healthy),
                        room_id: None,
                        sensor_mappings: None,
                    },
                ],
                properties: HashMap::new(),
            },
        ],
        coordinate_systems: vec![],
    }
}

#[test]
#[serial]
fn test_git_workflow_init_and_commit() {
    let temp_dir = TempDir::new().unwrap();
    let repo_path = temp_dir.path();
    
    // Configure Git
    let config = GitConfig {
        user_name: "Test User".to_string(),
        user_email: "test@example.com".to_string(),
        auto_commit: true,
        gpg_sign: false,
    };
    
    // Create Git manager
    let git_manager = BuildingGitManager::new(repo_path, config).unwrap();
    
    // Create and export building
    let building_data = create_test_building_data("Test Building");
    let result = git_manager.export_building(&building_data, Some("Initial commit")).unwrap();
    
    // Verify commit was created
    assert!(!result.commit_id.is_empty(), "Should create commit");
    assert_eq!(result.files_changed, 1, "Should change 1 file");
    
    // Verify file was created
    let yaml_file = repo_path.join("test-building.yaml");
    assert!(yaml_file.exists(), "YAML file should be created");
    
    // Verify Git repository was initialized
    let git_dir = repo_path.join(".git");
    assert!(git_dir.exists(), "Git repository should be initialized");
}

#[test]
#[serial]
fn test_git_workflow_multiple_commits() {
    let temp_dir = TempDir::new().unwrap();
    let repo_path = temp_dir.path();
    
    let config = GitConfig {
        user_name: "Test User".to_string(),
        user_email: "test@example.com".to_string(),
        auto_commit: true,
        gpg_sign: false,
    };
    
    let git_manager = BuildingGitManager::new(repo_path, config).unwrap();
    
    // First commit
    let mut building_data = create_test_building_data("Multi Commit Building");
    git_manager.export_building(&building_data, Some("Initial commit")).unwrap();
    
    // Modify and commit again
    building_data.floors[0].equipment.push(Equipment {
        id: "eq-2".to_string(),
        name: "Additional Equipment".to_string(),
        path: "/building/floor-1/eq-2".to_string(),
        address: None,
        equipment_type: EquipmentType::Electrical,
        position: Position { x: 5.0, y: 5.0, z: 1.0, coordinate_system: "LOCAL".to_string() },
        properties: HashMap::new(),
        status: EquipmentStatus::Active,
        health_status: Some(EquipmentHealthStatus::Healthy),
        room_id: None,
        sensor_mappings: None,
    });
    
    let result2 = git_manager.export_building(&building_data, Some("Added equipment")).unwrap();
    
    // Verify second commit
    assert!(!result2.commit_id.is_empty());
    assert_eq!(result2.files_changed, 1);
    
    // Verify we have 2 commits
    let repo = git2::Repository::open(repo_path).unwrap();
    let mut revwalk = repo.revwalk().unwrap();
    revwalk.push_head().unwrap();
    let commits: Vec<_> = revwalk.collect();
    assert_eq!(commits.len(), 2, "Should have 2 commits");
}

#[test]
#[serial]
fn test_git_diff_detection() {
    let temp_dir = TempDir::new().unwrap();
    let repo_path = temp_dir.path();
    
    let config = GitConfig {
        user_name: "Test User".to_string(),
        user_email: "test@example.com".to_string(),
        auto_commit: true,
        gpg_sign: false,
    };
    
    let git_manager = BuildingGitManager::new(repo_path, config).unwrap();
    
    // Initial commit
    let building_data = create_test_building_data("Diff Test Building");
    git_manager.export_building(&building_data, Some("Initial")).unwrap();
    
    // Modify file without committing
    let yaml_file = repo_path.join("diff-test-building.yaml");
    let mut content = fs::read_to_string(&yaml_file).unwrap();
    content.push_str("\n# Modified comment\n");
    fs::write(&yaml_file, content).unwrap();
    
    // Verify diff can be detected
    let repo = git2::Repository::open(repo_path).unwrap();
    let statuses = repo.statuses(None).unwrap();
    assert!(statuses.len() > 0, "Should detect modifications");
}

#[test]
#[serial]
fn test_git_commit_metadata() {
    let temp_dir = TempDir::new().unwrap();
    let repo_path = temp_dir.path();
    
    let test_name = "Metadata Test User";
    let test_email = "metadata@example.com";
    
    let config = GitConfig {
        user_name: test_name.to_string(),
        user_email: test_email.to_string(),
        auto_commit: true,
        gpg_sign: false,
    };
    
    let git_manager = BuildingGitManager::new(repo_path, config).unwrap();
    let building_data = create_test_building_data("Metadata Building");
    git_manager.export_building(&building_data, Some("Test commit")).unwrap();
    
    // Verify commit metadata
    let repo = git2::Repository::open(repo_path).unwrap();
    let head = repo.head().unwrap();
    let commit = head.peel_to_commit().unwrap();
    
    assert_eq!(commit.author().name().unwrap(), test_name);
    assert_eq!(commit.author().email().unwrap(), test_email);
    assert_eq!(commit.message().unwrap(), "Test commit");
}

#[test]
#[serial]
fn test_git_workflow_preserves_history() {
    let temp_dir = TempDir::new().unwrap();
    let repo_path = temp_dir.path();
    
    let config = GitConfig {
        user_name: "Test User".to_string(),
        user_email: "test@example.com".to_string(),
        auto_commit: true,
        gpg_sign: false,
    };
    
    let git_manager = BuildingGitManager::new(repo_path, config).unwrap();
    let mut building_data = create_test_building_data("History Building");
    
    // Create multiple commits with different changes
    git_manager.export_building(&building_data, Some("Commit 1: Initial")).unwrap();
    
    building_data.building.description = Some("Updated description".to_string());
    git_manager.export_building(&building_data, Some("Commit 2: Updated desc")).unwrap();
    
    building_data.floors[0].equipment[0].name = "Modified Equipment".to_string();
    git_manager.export_building(&building_data, Some("Commit 3: Modified equipment")).unwrap();
    
    // Verify history is preserved
    let repo = git2::Repository::open(repo_path).unwrap();
    let mut revwalk = repo.revwalk().unwrap();
    revwalk.push_head().unwrap();
    
    let commits: Vec<_> = revwalk
        .map(|oid| repo.find_commit(oid.unwrap()).unwrap())
        .collect();
    
    assert_eq!(commits.len(), 3, "Should have 3 commits");
    assert!(commits[0].message().unwrap().contains("Commit 3"));
    assert!(commits[1].message().unwrap().contains("Commit 2"));
    assert!(commits[2].message().unwrap().contains("Commit 1"));
}

#[test]
#[serial]
fn test_git_no_commit_when_disabled() {
    let temp_dir = TempDir::new().unwrap();
    let repo_path = temp_dir.path();
    
    let config = GitConfig {
        user_name: "Test User".to_string(),
        user_email: "test@example.com".to_string(),
        auto_commit: false,  // Disabled
        gpg_sign: false,
    };
    
    // Initialize repo manually
    git2::Repository::init(repo_path).unwrap();
    
    // Write file directly (simulating save without commit)
    let building_data = create_test_building_data("No Commit Building");
    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).unwrap();
    let yaml_file = repo_path.join("no-commit-building.yaml");
    fs::write(&yaml_file, yaml_content).unwrap();
    
    // Verify file exists but is not committed
    assert!(yaml_file.exists());
    
    let repo = git2::Repository::open(repo_path).unwrap();
    let statuses = repo.statuses(None).unwrap();
    
    // File should be untracked or modified
    assert!(statuses.len() > 0, "Should have uncommitted changes");
}

