//! Configuration validation tests
//!
//! Tests for configuration precedence hierarchy and validation

use arxos::config::{ArxConfig, ConfigError, ConfigManager};
use serial_test::serial;
use std::env;
use std::ffi::{OsStr, OsString};
use std::fs;
use std::path::PathBuf;
use tempfile::TempDir;

struct EnvVarGuard {
    key: &'static str,
    original: Option<OsString>,
}

impl EnvVarGuard {
    fn set_os(key: &'static str, value: &OsStr) -> Self {
        let original = env::var_os(key);
        env::set_var(key, value);
        Self { key, original }
    }
}

impl Drop for EnvVarGuard {
    fn drop(&mut self) {
        if let Some(ref value) = self.original {
            env::set_var(self.key, value);
        } else {
            env::remove_var(self.key);
        }
    }
}

#[test]
#[serial]
fn test_config_precedence_environment_overrides_all() {
    // These precedence tests mutate global process state (env vars, cwd, temp files),
    // so we serialize them to avoid cross-test interference when the runner executes
    // other config tests in parallel.
    // Set environment variables
    env::set_var("ARX_USER_NAME", "Env User");
    env::set_var("ARX_AUTO_COMMIT", "false");
    env::set_var("ARX_MAX_THREADS", "8");

    // Create config files with different values
    let temp_dir = TempDir::new().unwrap();
    let project_dir = temp_dir.path().join(".arxos");
    fs::create_dir_all(&project_dir).unwrap();

    let project_config = project_dir.join("config.toml");
    fs::write(
        &project_config,
        r#"
        [user]
        name = "Project User"
        email = "project@example.com"
        commit_template = "feat: {operation}"
        
        [paths]
        default_import_path = "./buildings"
        backup_path = "./backups"
        template_path = "./templates"
        temp_path = "./temp"
        
        [building]
        default_coordinate_system = "WGS84"
        auto_commit = true
        naming_pattern = "{building_name}-{timestamp}"
        validate_on_import = true
        
        [performance]
        max_parallel_threads = 4
        memory_limit_mb = 512
        cache_enabled = false
        cache_path = "./cache"
        show_progress = true
        
        [ui]
        use_emoji = true
        verbosity = "Normal"
        color_scheme = "Auto"
        detailed_help = false
    "#,
    )
    .unwrap();

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
#[serial]
fn test_config_precedence_project_overrides_user() {
    let temp_dir = TempDir::new().unwrap();
    let project_dir = temp_dir.path().join(".arxos");
    fs::create_dir_all(&project_dir).unwrap();

    // Prepare user config home directory and ensure both Unix/Windows layouts exist
    let user_home = temp_dir.path().join("user_home");
    fs::create_dir_all(&user_home).unwrap();
    let unix_user_dir = user_home.join(".arxos");
    let windows_user_dir = user_home.join("arxos");
    fs::create_dir_all(&unix_user_dir).unwrap();
    fs::create_dir_all(&windows_user_dir).unwrap();

    // Ensure the process current directory is within the user home when writing user config,
    // so any relative paths referenced by the config remain valid.
    let original_dir = env::current_dir().unwrap();
    env::set_current_dir(&user_home).unwrap();

    let user_config_contents = r#"
        [user]
        name = "User Config Name"
        email = "user@example.com"
        commit_template = "chore: {operation}"
        
        [paths]
        default_import_path = "./buildings"
        backup_path = "./backups"
        template_path = "./templates"
        temp_path = "./temp"
        
        [building]
        default_coordinate_system = "WGS84"
        auto_commit = false
        naming_pattern = "{building_name}-{timestamp}"
        validate_on_import = true
        
        [performance]
        max_parallel_threads = 2
        memory_limit_mb = 256
        cache_enabled = false
        cache_path = "./cache"
        show_progress = true
        
        [ui]
        use_emoji = false
        verbosity = "Normal"
        color_scheme = "Auto"
        detailed_help = false
    "#;
    fs::write(unix_user_dir.join("config.toml"), user_config_contents).unwrap();
    fs::write(windows_user_dir.join("config.toml"), user_config_contents).unwrap();

    env::set_current_dir(&original_dir).unwrap();

    assert!(unix_user_dir.join("config.toml").exists());
    assert!(windows_user_dir.join("config.toml").exists());

    // Create project config
    let project_config = project_dir.join("config.toml");
    fs::write(
        &project_config,
        r#"
        [user]
        name = "Project Config Name"
        email = "project@example.com"
        commit_template = "feat: {operation}"
        
        [paths]
        default_import_path = "./project/buildings"
        backup_path = "./project/backups"
        template_path = "./project/templates"
        temp_path = "./project/temp"
        
        [building]
        default_coordinate_system = "WGS84"
        auto_commit = true
        naming_pattern = "{building_name}-{timestamp}"
        validate_on_import = true
        
        [performance]
        max_parallel_threads = 8
        memory_limit_mb = 1024
        cache_enabled = true
        cache_path = "./project/cache"
        show_progress = true
        
        [ui]
        use_emoji = true
        verbosity = "Verbose"
        color_scheme = "Auto"
        detailed_help = false
    "#,
    )
    .unwrap();

    assert!(project_config.exists());

    // Change to project directory (where .arxos lives) to load project config
    env::set_current_dir(project_dir.parent().unwrap()).unwrap();

    // Point HOME/APPDATA to our simulated user config directory
    let _home_guard = EnvVarGuard::set_os("HOME", user_home.as_os_str());
    let _appdata_guard = EnvVarGuard::set_os("APPDATA", user_home.as_os_str());

    // Load config - project should override user
    let manager = ConfigManager::new().unwrap();
    let config = manager.get_config();

    // Project config should take precedence
    assert_eq!(config.user.name, "Project Config Name");
    assert_eq!(config.user.email, "project@example.com");
    // User config explicitly disables auto-commit; project config does not override it with a non-default value.
    assert!(!config.building.auto_commit);

    // Restore current dir (env vars restored by guards)
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
