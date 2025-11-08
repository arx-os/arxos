//! Tests for git operations command handlers

use arxui::commands::git_ops::{handle_status, handle_diff, handle_history};
use arxos::yaml::BuildingData;
use tempfile::TempDir;
use std::fs::{create_dir_all, write};
use std::path::PathBuf;

/// Create a temporary test directory with building data
fn setup_test_building(temp_dir: &TempDir) -> PathBuf {
    let building_dir = temp_dir.path().join("test_building");
    create_dir_all(&building_dir).unwrap();
    
    // Create a basic building YAML file
    let building_yaml = r#"
building:
  name: Test Building
  address: 123 Test St
  total_floors: 3
metadata:
  version: 1.0
  last_updated: "2024-01-01T00:00:00Z"
floors:
  - name: Floor 1
    level: 1
    rooms: []
    equipment: []
"#;
    
    let yaml_path = building_dir.join("building.yaml");
    write(&yaml_path, building_yaml).unwrap();
    
    building_dir
}

#[test]
#[ignore] // Requires Git repository
fn test_git_status_in_non_git_directory() {
    let temp_dir = tempfile::tempdir().unwrap();
    let _building_dir = setup_test_building(&temp_dir);
    
    // This will fail gracefully (not a Git repo)
    let result = handle_status(false);
    // We expect this to fail or succeed depending on context
    // Just verify it doesn't panic
    drop(result);
}

#[test]
#[ignore] // Requires Git repository and proper setup
fn test_git_diff_operations() {
    // This test would verify diff functionality
    // Would need a proper Git repository setup
}

#[test]
#[ignore] // Requires Git repository and proper setup
fn test_git_history_with_filters() {
    // This test would verify history functionality
    // Would need a proper Git repository setup with commits
}

//! Git Configuration Tests
//!
//! Tests verify that Git commits use the configured author information
//! from GitConfig instead of hardcoded values.

mod git_config_tests {
    use super::*;
    use arxos::git::{BuildingGitManager, GitConfig, GitConfigManager};
    use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    use std::env;
    use std::fs;

    fn create_test_building_data() -> BuildingData {
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
                coordinate_system: "World".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![],
        }
    }

    #[test]
    fn test_git_commit_uses_custom_author() {
        let temp_dir = TempDir::new().unwrap();
        let custom_config = GitConfig {
            author_name: "Test User".to_string(),
            author_email: "test@example.com".to_string(),
            branch: "main".to_string(),
            remote_url: None,
        };
        
        let mut manager = BuildingGitManager::new(
            temp_dir.path().to_str().unwrap(),
            "Test Building",
            custom_config.clone(),
        ).expect("Failed to create Git manager");
        
        let building_data = create_test_building_data();
        let result = manager.export_building(&building_data, Some("Test commit"));
        
        assert!(result.is_ok(), "Export should succeed");
        
        // Verify commit uses custom author
        let commits = manager.list_commits(1).expect("Should list commits");
        assert!(!commits.is_empty(), "Should have at least one commit");
        
        if let Some(commit) = commits.first() {
            assert_eq!(commit.author, custom_config.author_name, 
                      "Commit author should match config");
        }
    }

    #[test]
    fn test_git_config_from_environment() {
        // Save original values
        let orig_name = env::var("GIT_AUTHOR_NAME").ok();
        let orig_email = env::var("GIT_AUTHOR_EMAIL").ok();
        
        // Set test environment variables
        env::set_var("GIT_AUTHOR_NAME", "Env Test User");
        env::set_var("GIT_AUTHOR_EMAIL", "env@example.com");
        
        let config = GitConfigManager::load_from_arx_config_or_env();
        
        assert_eq!(config.author_name, "Env Test User");
        assert_eq!(config.author_email, "env@example.com");
        
        // Restore original values
        if let Some(name) = orig_name {
            env::set_var("GIT_AUTHOR_NAME", name);
        } else {
            env::remove_var("GIT_AUTHOR_NAME");
        }
        
        if let Some(email) = orig_email {
            env::set_var("GIT_AUTHOR_EMAIL", email);
        } else {
            env::remove_var("GIT_AUTHOR_EMAIL");
        }
    }

    #[test]
    fn test_git_config_default_fallback() {
        // Clear environment to test default
        env::remove_var("GIT_AUTHOR_NAME");
        env::remove_var("GIT_AUTHOR_EMAIL");
        env::remove_var("ARX_USER_NAME");
        env::remove_var("ARX_USER_EMAIL");
        
        let config = GitConfigManager::default_config();
        
        assert_eq!(config.author_name, "ArxOS");
        assert_eq!(config.author_email, "arxos@arxos.io");
        assert_eq!(config.branch, "main");
    }

    #[test]
    fn test_git_commit_staged_uses_config() {
        let temp_dir = TempDir::new().unwrap();
        let custom_config = GitConfig {
            author_name: "Staged Test User".to_string(),
            author_email: "staged@example.com".to_string(),
            branch: "main".to_string(),
            remote_url: None,
        };
        
        let mut manager = BuildingGitManager::new(
            temp_dir.path().to_str().unwrap(),
            "Test Building",
            custom_config.clone(),
        ).expect("Failed to create Git manager");
        
        // Create a test file
        let test_file = temp_dir.path().join("test.txt");
        fs::write(&test_file, "test content").unwrap();
        
        // Stage and commit
        manager.stage_file("test.txt").expect("Should stage file");
        let commit_id = manager.commit_staged("Test staged commit")
            .expect("Should commit");
        
        assert!(!commit_id.is_empty(), "Should return commit ID");
        
        // Verify author
        let commits = manager.list_commits(1).expect("Should list commits");
        assert!(!commits.is_empty());
        if let Some(commit) = commits.first() {
            assert_eq!(commit.author, custom_config.author_name);
        }
    }
}

