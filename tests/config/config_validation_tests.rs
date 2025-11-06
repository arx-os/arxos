//! Configuration validation tests
//!
//! Tests for configuration precedence hierarchy and validation

use arxos::config::{ConfigManager, ArxConfig, ConfigError};
use std::path::PathBuf;
use tempfile::TempDir;
use std::fs;
use std::env;

#[test]
fn test_config_precedence_environment_overrides_all() {
    // Set environment variables
    env::set_var("ARX_USER_NAME", "Env User");
    env::set_var("ARX_AUTO_COMMIT", "false");
    env::set_var("ARX_MAX_THREADS", "8");
    
    // Create config files with different values
    let temp_dir = TempDir::new().unwrap();
    let project_dir = temp_dir.path().join(".arxos");
    fs::create_dir_all(&project_dir).unwrap();
    
    let project_config = project_dir.join("config.toml");
    fs::write(&project_config, r#"
        [user]
        name = "Project User"
        email = "project@example.com"
        
        [building]
        auto_commit = true
    "#).unwrap();
    
    // Change to temp directory to load project config
    let original_dir = env::current_dir().unwrap();
    env::set_current_dir(temp_dir.path()).unwrap();
    
    // Load config - environment should override
    let manager = ConfigManager::new().unwrap();
    let config = manager.get_config();
    
    assert_eq!(config.user.name, "Env User");
    assert!(!config.building.auto_commit);
    assert_eq!(config.performance.max_parallel_threads, 8);
    
    // Restore
    env::set_current_dir(original_dir).unwrap();
    env::remove_var("ARX_USER_NAME");
    env::remove_var("ARX_AUTO_COMMIT");
    env::remove_var("ARX_MAX_THREADS");
}

#[test]
fn test_config_precedence_project_overrides_user() {
    let temp_dir = TempDir::new().unwrap();
    let project_dir = temp_dir.path().join(".arxos");
    fs::create_dir_all(&project_dir).unwrap();
    
    // Create user config (simulated)
    let user_config_dir = temp_dir.path().join("user_home").join(".arxos");
    fs::create_dir_all(&user_config_dir).unwrap();
    let user_config = user_config_dir.join("config.toml");
    fs::write(&user_config, r#"
        [user]
        name = "User Config Name"
        email = "user@example.com"
        
        [building]
        auto_commit = false
    "#).unwrap();
    
    // Create project config
    let project_config = project_dir.join("config.toml");
    fs::write(&project_config, r#"
        [user]
        name = "Project Config Name"
        email = "project@example.com"
        
        [building]
        auto_commit = true
    "#).unwrap();
    
    // Change to temp directory to load project config
    let original_dir = env::current_dir().unwrap();
    env::set_current_dir(temp_dir.path()).unwrap();
    
    // Load config - project should override user
    let manager = ConfigManager::new().unwrap();
    let config = manager.get_config();
    
    // Project config should take precedence
    assert_eq!(config.user.name, "Project Config Name");
    assert_eq!(config.user.email, "project@example.com");
    assert!(config.building.auto_commit);
    
    // Restore
    env::set_current_dir(original_dir).unwrap();
}

#[test]
fn test_config_validation_valid_config() {
    let mut config = ArxConfig::default();
    config.user.name = "Test User".to_string();
    config.user.email = "test@example.com".to_string();
    
    let result = ConfigManager::validate_config(&config);
    assert!(result.is_ok());
}

#[test]
fn test_config_validation_invalid_email() {
    let mut config = ArxConfig::default();
    config.user.name = "Test User".to_string();
    config.user.email = "invalid-email".to_string();
    
    let result = ConfigManager::validate_config(&config);
    assert!(result.is_err());
    
    if let Err(ConfigError::ValidationFailed { field, .. }) = result {
        assert_eq!(field, "user.email");
    } else {
        panic!("Expected ValidationFailed error");
    }
}

#[test]
fn test_config_validation_invalid_thread_count() {
    let mut config = ArxConfig::default();
    config.performance.max_parallel_threads = 0;
    
    let result = ConfigManager::validate_config(&config);
    assert!(result.is_err());
    
    if let Err(ConfigError::ValidationFailed { field, .. }) = result {
        assert_eq!(field, "performance.max_parallel_threads");
    } else {
        panic!("Expected ValidationFailed error");
    }
}

#[test]
fn test_config_validation_invalid_coordinate_system() {
    let mut config = ArxConfig::default();
    config.building.default_coordinate_system = "INVALID".to_string();
    
    let result = ConfigManager::validate_config(&config);
    assert!(result.is_err());
    
    if let Err(ConfigError::ValidationFailed { field, .. }) = result {
        assert_eq!(field, "building.default_coordinate_system");
    } else {
        panic!("Expected ValidationFailed error");
    }
}

#[test]
fn test_config_validation_missing_naming_pattern_placeholder() {
    let mut config = ArxConfig::default();
    config.building.naming_pattern = "no-placeholder".to_string();
    
    let result = ConfigManager::validate_config(&config);
    assert!(result.is_err());
    
    if let Err(ConfigError::ValidationFailed { field, .. }) = result {
        assert_eq!(field, "building.naming_pattern");
    } else {
        panic!("Expected ValidationFailed error");
    }
}

#[test]
fn test_config_validation_path_conflicts() {
    let temp_dir = TempDir::new().unwrap();
    let test_path = temp_dir.path().join("test_dir");
    fs::create_dir_all(&test_path).unwrap();
    
    let mut config = ArxConfig::default();
    config.paths.default_import_path = test_path.clone();
    config.paths.backup_path = test_path.clone();
    config.paths.template_path = PathBuf::from("./templates");
    config.paths.temp_path = PathBuf::from("./temp");
    
    let result = ConfigManager::validate_config(&config);
    assert!(result.is_err());
    
    if let Err(ConfigError::ValidationFailed { field, .. }) = result {
        assert_eq!(field, "paths");
    } else {
        panic!("Expected ValidationFailed error for duplicate paths");
    }
}

#[test]
fn test_config_validation_cross_config_cache_path_conflict() {
    let temp_dir = TempDir::new().unwrap();
    let test_path = temp_dir.path().join("test_dir");
    fs::create_dir_all(&test_path).unwrap();
    
    let mut config = ArxConfig::default();
    config.paths.default_import_path = test_path.clone();
    config.performance.cache_enabled = true;
    config.performance.cache_path = test_path.clone();
    
    let result = ConfigManager::validate_config(&config);
    assert!(result.is_err());
    
    if let Err(ConfigError::ValidationFailed { field, .. }) = result {
        assert_eq!(field, "performance.cache_path");
    } else {
        panic!("Expected ValidationFailed error for cache path conflict");
    }
}

