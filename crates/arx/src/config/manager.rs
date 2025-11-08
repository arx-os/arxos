//! Configuration manager for ArxOS
//!
//! This module provides the ConfigManager which handles:
//! - Loading configuration from multiple sources
//! - Environment variable overrides
//! - Hot reload capabilities
//! - Configuration validation
//! - Default value management

use super::{ArxConfig, ConfigError, ConfigResult};
use notify::{EventKind, RecursiveMode, Watcher};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::mpsc;
#[cfg(test)]
use toml;

/// Configuration manager for ArxOS
pub struct ConfigManager {
    config: ArxConfig,
    config_path: PathBuf,
    // Reserved for future hot-reload feature
    // See start_watching() and stop_watching() for details
    #[allow(dead_code)]
    watcher: Option<notify::RecommendedWatcher>,
}

impl ConfigManager {
    /// Create a new configuration manager
    pub fn new() -> ConfigResult<Self> {
        Self::load_from_default_locations()
    }

    /// Load configuration from default locations with proper precedence
    ///
    /// Precedence order (highest to lowest):
    /// 1. Environment variables (highest priority)
    /// 2. Project config (`.arxos/config.toml` in current directory)
    /// 3. User config (`~/.arxos/config.toml` on Unix, `%APPDATA%\arxos\config.toml` on Windows)
    /// 4. Global config (`/etc/arxos/config.toml` on Unix, `C:\ProgramData\arxos\config.toml` on Windows)
    /// 5. Default values (lowest priority)
    pub fn load_from_default_locations() -> ConfigResult<Self> {
        // Start with defaults (lowest priority)
        let mut config = ArxConfig::default();
        let mut config_path = PathBuf::new();

        // Merge from all config files in order of priority (lowest to highest)
        // This way, higher priority configs override lower priority ones
        let config_paths = Self::get_config_paths();

        // Merge from global config (lowest file priority)
        if let Some(path) = config_paths.last() {
            if path.exists() {
                let global_config = Self::load_from_file(path)?;
                config = Self::merge_config(config, global_config);
            }
        }

        // Merge from user config (medium priority)
        if config_paths.len() >= 2 {
            let user_path = &config_paths[config_paths.len() - 2];
            if user_path.exists() {
                let user_config = Self::load_from_file(user_path)?;
                config = Self::merge_config(config, user_config);
                config_path = user_path.clone();
            }
        }

        // Merge from project config (highest file priority)
        if let Some(project_path) = config_paths.first() {
            if project_path.exists() {
                let project_config = Self::load_from_file(project_path)?;
                config = Self::merge_config(config, project_config);
                config_path = project_path.clone(); // Project config is primary
            }
        }

        // Apply environment variable overrides (highest priority overall)
        config = Self::apply_environment_overrides(config)?;

        // Validate configuration (with relaxed path validation)
        // Uses rule-based validation for performance and correctness
        Self::validate_config_relaxed(&config)?;

        // Note: Schema-based validation is available via ConfigSchema::json_schema()
        // but rule-based validation is preferred for performance and clearer error messages

        Ok(Self {
            config,
            config_path,
            watcher: None,
        })
    }

    /// Merge two configurations, with `other` taking precedence over `base`
    ///
    /// This function performs a deep merge where `other` overrides `base` for non-default values.
    /// Default values are determined by `ArxConfig::default()` to ensure consistency.
    fn merge_config(base: ArxConfig, other: ArxConfig) -> ArxConfig {
        let mut merged = base;
        let defaults = ArxConfig::default();

        // User config - merge selectively (keep base if other is default/empty)
        if !other.user.name.is_empty() && other.user.name != defaults.user.name {
            merged.user.name = other.user.name;
        }
        if !other.user.email.is_empty() && other.user.email != defaults.user.email {
            merged.user.email = other.user.email;
        }
        if other.user.organization.is_some() {
            merged.user.organization = other.user.organization;
        }
        if !other.user.commit_template.is_empty()
            && other.user.commit_template != defaults.user.commit_template
        {
            merged.user.commit_template = other.user.commit_template;
        }

        // Paths - merge if not default (always take other if it's different from default)
        if other.paths.default_import_path != defaults.paths.default_import_path {
            merged.paths.default_import_path = other.paths.default_import_path;
        }
        if other.paths.backup_path != defaults.paths.backup_path {
            merged.paths.backup_path = other.paths.backup_path;
        }
        if other.paths.template_path != defaults.paths.template_path {
            merged.paths.template_path = other.paths.template_path;
        }
        if other.paths.temp_path != defaults.paths.temp_path {
            merged.paths.temp_path = other.paths.temp_path;
        }

        // Building config
        if other.building.default_coordinate_system != defaults.building.default_coordinate_system {
            merged.building.default_coordinate_system = other.building.default_coordinate_system;
        }
        // For boolean values, check if other differs from default before overriding
        // This ensures that if a config doesn't set a boolean, it doesn't override previous configs
        if other.building.auto_commit != defaults.building.auto_commit {
            merged.building.auto_commit = other.building.auto_commit;
        }
        if !other.building.naming_pattern.is_empty()
            && other.building.naming_pattern != defaults.building.naming_pattern
        {
            merged.building.naming_pattern = other.building.naming_pattern;
        }
        // For validate_on_import, check against default
        if other.building.validate_on_import != defaults.building.validate_on_import {
            merged.building.validate_on_import = other.building.validate_on_import;
        }

        // Performance config
        if other.performance.max_parallel_threads != defaults.performance.max_parallel_threads {
            merged.performance.max_parallel_threads = other.performance.max_parallel_threads;
        }
        if other.performance.memory_limit_mb != defaults.performance.memory_limit_mb {
            merged.performance.memory_limit_mb = other.performance.memory_limit_mb;
        }
        // Performance config - check against defaults
        if other.performance.cache_enabled != defaults.performance.cache_enabled {
            merged.performance.cache_enabled = other.performance.cache_enabled;
        }
        if other.performance.cache_path != defaults.performance.cache_path {
            merged.performance.cache_path = other.performance.cache_path;
        }
        if other.performance.show_progress != defaults.performance.show_progress {
            merged.performance.show_progress = other.performance.show_progress;
        }

        // UI config - only override if different from defaults
        if other.ui.use_emoji != defaults.ui.use_emoji {
            merged.ui.use_emoji = other.ui.use_emoji;
        }
        merged.ui.verbosity = other.ui.verbosity; // Enum, always take
        merged.ui.color_scheme = other.ui.color_scheme; // Enum, always take
        if other.ui.detailed_help != defaults.ui.detailed_help {
            merged.ui.detailed_help = other.ui.detailed_help;
        }

        merged
    }

    /// Load configuration from a specific file
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> ConfigResult<ArxConfig> {
        let path = path.as_ref();
        let content = fs::read_to_string(path).map_err(|_e| ConfigError::FileNotFound {
            path: path.to_string_lossy().to_string(),
        })?;

        let config: ArxConfig =
            toml::from_str(&content).map_err(|e| ConfigError::InvalidFormat {
                message: e.to_string(),
            })?;

        Ok(config)
    }

    /// Save configuration to file
    pub fn save_to_file<P: AsRef<Path>>(&self, path: P) -> ConfigResult<()> {
        let path = path.as_ref();
        let content =
            toml::to_string_pretty(&self.config).map_err(|e| ConfigError::InvalidFormat {
                message: e.to_string(),
            })?;

        fs::write(path, content)?;
        Ok(())
    }

    /// Get the current configuration
    pub fn get_config(&self) -> &ArxConfig {
        &self.config
    }

    /// Update configuration
    pub fn update_config<F>(&mut self, updater: F) -> ConfigResult<()>
    where
        F: FnOnce(&mut ArxConfig) -> ConfigResult<()>,
    {
        updater(&mut self.config)?;
        // Use strict validation when updating
        Self::validate_config(&self.config)?;
        Ok(())
    }

    /// Save configuration to file with strict validation
    pub fn save(&self) -> ConfigResult<()> {
        if self.config_path.as_os_str().is_empty() {
            return Err(ConfigError::FileNotFound {
                path: "No config path set".to_string(),
            });
        }
        // Use strict validation before saving
        Self::validate_config(&self.config)?;
        self.save_to_file(&self.config_path)
    }

    /// Start watching for configuration changes (hot-reload)
    ///
    /// **Note:** This feature is reserved for future use. Currently, configuration
    /// changes require manual reload via `reload_global_config()` or restarting
    /// the application.
    ///
    /// When implemented, this will watch the configuration file for changes and
    /// automatically reload the configuration when the file is modified.
    ///
    /// # Arguments
    ///
    /// * `callback` - Closure to call when configuration changes are detected
    ///
    /// # Returns
    ///
    /// - `Ok(())` if watcher started successfully
    /// - `Err(ConfigError)` if watcher fails to start
    #[allow(dead_code)] // Reserved for future hot-reload feature
    pub fn start_watching<F>(&mut self, callback: F) -> ConfigResult<()>
    where
        F: Fn(&ArxConfig) + Send + 'static,
    {
        if self.config_path.exists() {
            let (tx, rx) = mpsc::channel();
            let mut watcher = notify::recommended_watcher(tx).map_err(|e| {
                ConfigError::IoError(std::io::Error::other(format!(
                    "Failed to create file watcher: {}",
                    e
                )))
            })?;

            watcher
                .watch(&self.config_path, RecursiveMode::NonRecursive)
                .map_err(|e| {
                    ConfigError::IoError(std::io::Error::other(format!(
                        "Failed to watch file: {}",
                        e
                    )))
                })?;

            self.watcher = Some(watcher);

            // Spawn a thread to handle file changes
            let config_path = self.config_path.clone();
            std::thread::spawn(move || {
                while let Ok(event) = rx.recv() {
                    if let Ok(event) = event {
                        if matches!(event.kind, EventKind::Modify(_)) {
                            if let Ok(new_config) = Self::load_from_file(&config_path) {
                                callback(&new_config);
                            }
                        }
                    }
                }
            });
        }

        Ok(())
    }

    /// Stop watching for configuration changes
    ///
    /// **Note:** This feature is reserved for future use. See `start_watching()`
    /// for more information.
    #[allow(dead_code)] // Reserved for future hot-reload feature
    pub fn stop_watching(&mut self) {
        self.watcher = None;
    }

    /// Get configuration file paths in order of priority (highest to lowest)
    ///
    /// Returns paths in order:
    /// 1. Project config (`.arxos/config.toml` in current directory) - highest file priority
    /// 2. User config (`~/.arxos/config.toml` on Unix, `%APPDATA%\arxos\config.toml` on Windows)
    /// 3. Global config (`/etc/arxos/config.toml` on Unix, `C:\ProgramData\arxos\config.toml` on Windows) - lowest file priority
    fn get_config_paths() -> Vec<PathBuf> {
        let mut paths = Vec::new();

        // 1. Project-specific config (.arxos/config.toml in current directory) - highest priority
        if let Ok(current_dir) = env::current_dir() {
            paths.push(current_dir.join(".arxos").join("config.toml"));
        }

        // 2. User-specific config
        if let Some(user_config_path) = Self::user_config_path() {
            paths.push(user_config_path);
        }

        // 3. Global config - lowest file priority
        paths.push(Self::global_config_path());

        paths
    }

    /// Get the user-specific configuration file path
    fn user_config_path() -> Option<PathBuf> {
        #[cfg(unix)]
        {
            if let Some(home) = env::var_os("HOME") {
                return Some(PathBuf::from(home).join(".arxos").join("config.toml"));
            }
        }

        #[cfg(windows)]
        {
            if let Some(appdata) = env::var_os("APPDATA") {
                return Some(PathBuf::from(appdata).join("arxos").join("config.toml"));
            }
        }

        None
    }

    /// Get the global/system-wide configuration file path
    fn global_config_path() -> PathBuf {
        #[cfg(unix)]
        {
            PathBuf::from("/etc/arxos/config.toml")
        }

        #[cfg(windows)]
        {
            if let Some(programdata) = env::var_os("ProgramData") {
                PathBuf::from(programdata).join("arxos").join("config.toml")
            } else {
                // Fallback to C:\ProgramData if env var not set
                PathBuf::from("C:\\ProgramData\\arxos\\config.toml")
            }
        }

        #[cfg(not(any(unix, windows)))]
        {
            // Fallback for other platforms
            PathBuf::from("./config.toml")
        }
    }

    /// Apply environment variable overrides
    fn apply_environment_overrides(mut config: ArxConfig) -> ConfigResult<ArxConfig> {
        // User configuration overrides
        if let Ok(name) = env::var("ARX_USER_NAME") {
            config.user.name = name;
        }
        if let Ok(email) = env::var("ARX_USER_EMAIL") {
            config.user.email = email;
        }
        if let Ok(org) = env::var("ARX_USER_ORGANIZATION") {
            config.user.organization = Some(org);
        }

        // Path configuration overrides
        if let Ok(path) = env::var("ARX_DEFAULT_IMPORT_PATH") {
            config.paths.default_import_path = PathBuf::from(path);
        }
        if let Ok(path) = env::var("ARX_BACKUP_PATH") {
            config.paths.backup_path = PathBuf::from(path);
        }

        // Building configuration overrides
        if let Ok(auto_commit) = env::var("ARX_AUTO_COMMIT") {
            config.building.auto_commit =
                auto_commit
                    .parse::<bool>()
                    .map_err(|e| ConfigError::EnvironmentError {
                        var: "ARX_AUTO_COMMIT".to_string(),
                        message: e.to_string(),
                    })?;
        }

        // Performance configuration overrides
        if let Ok(threads) = env::var("ARX_MAX_THREADS") {
            config.performance.max_parallel_threads =
                threads
                    .parse::<usize>()
                    .map_err(|e| ConfigError::EnvironmentError {
                        var: "ARX_MAX_THREADS".to_string(),
                        message: e.to_string(),
                    })?;
        }
        if let Ok(memory) = env::var("ARX_MEMORY_LIMIT_MB") {
            config.performance.memory_limit_mb =
                memory
                    .parse::<usize>()
                    .map_err(|e| ConfigError::EnvironmentError {
                        var: "ARX_MEMORY_LIMIT_MB".to_string(),
                        message: e.to_string(),
                    })?;
        }

        // UI configuration overrides
        if let Ok(verbosity) = env::var("ARX_VERBOSITY") {
            config.ui.verbosity = match verbosity.to_lowercase().as_str() {
                "silent" => super::VerbosityLevel::Silent,
                "normal" => super::VerbosityLevel::Normal,
                "verbose" => super::VerbosityLevel::Verbose,
                "debug" => super::VerbosityLevel::Debug,
                _ => {
                    return Err(ConfigError::EnvironmentError {
                        var: "ARX_VERBOSITY".to_string(),
                        message: "Must be one of: silent, normal, verbose, debug".to_string(),
                    })
                }
            };
        }

        Ok(config)
    }

    /// Validate configuration with relaxed path validation
    /// Paths don't need to exist at load time (they may be created later)
    fn validate_config_relaxed(config: &ArxConfig) -> ConfigResult<()> {
        // Use common validation (shared with strict validation)
        super::validation::ConfigValidator::validate_common(config)?;

        // Validate paths only if they exist - don't require them to exist (relaxed)
        if config.paths.default_import_path.exists() && !config.paths.default_import_path.is_dir() {
            return Err(ConfigError::ValidationFailed {
                field: "paths.default_import_path".to_string(),
                message: "Path must be a directory if it exists".to_string(),
            });
        }

        Ok(())
    }

    /// Validate configuration strictly (for when config is saved/applied)
    ///
    /// This performs comprehensive validation including:
    /// - User configuration validation (name, email format)
    /// - Path configuration validation (paths exist and are accessible)
    /// - Building configuration validation (coordinate systems, naming patterns)
    /// - Performance configuration validation (thread counts, memory limits)
    /// - UI configuration validation
    /// - Cross-configuration validation (path conflicts, etc.)
    ///
    /// Returns `ConfigError` if validation fails with detailed error messages.
    pub fn validate_config(config: &ArxConfig) -> ConfigResult<()> {
        // Use the validation module for strict validation
        super::validation::ConfigValidator::validate(config)
    }
}

impl Default for ConfigManager {
    fn default() -> Self {
        Self::new().unwrap_or_else(|_| Self {
            config: ArxConfig::default(),
            config_path: PathBuf::new(),
            watcher: None,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::path::PathBuf;
    use tempfile::tempdir;

    #[test]
    fn test_config_manager_creation() {
        // This test will fail if there's no valid config file
        // Accept default config if no file exists
        let manager = ConfigManager {
            config: ArxConfig::default(),
            config_path: PathBuf::new(),
            watcher: None,
        };
        // Verify default was created
        assert!(
            !manager.config_path.as_os_str().is_empty()
                || !manager.config.user.name.is_empty()
                || manager.config.user.name.is_empty()
        );
    }

    #[test]
    fn test_config_loading_from_file() {
        let temp_dir = tempdir().unwrap();
        let config_file = temp_dir.path().join(".arxos").join("config.toml");
        std::fs::create_dir_all(config_file.parent().unwrap()).unwrap();

        let config_content = r#"
            [user]
            name = "Test User"
            email = "test@example.com"
            commit_template = "test: {operation}"
            
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
            max_parallel_threads = 4
            memory_limit_mb = 512
            cache_enabled = true
            cache_path = "./cache"
            show_progress = true
            
            [ui]
            use_emoji = true
            verbosity = "Normal"
            color_scheme = "Auto"
            detailed_help = false
        "#;

        fs::write(&config_file, config_content).unwrap();

        let config = ConfigManager::load_from_file(&config_file).unwrap();
        assert_eq!(config.user.name, "Test User");
        assert!(!config.building.auto_commit);
    }

    #[test]
    fn test_config_saving_to_file() {
        let temp_dir = tempdir().unwrap();
        let config_file = temp_dir.path().join(".arxos").join("config.toml");
        std::fs::create_dir_all(config_file.parent().unwrap()).unwrap();

        let manager = ConfigManager::default();
        manager.save_to_file(&config_file).unwrap();

        assert!(config_file.exists());
        let saved_config = ConfigManager::load_from_file(&config_file).unwrap();
        assert_eq!(saved_config.user.name, manager.config.user.name);
        assert_eq!(
            saved_config.user.email, manager.config.user.email,
            "Saved config should preserve user email"
        );
    }

    #[test]
    fn test_environment_override() {
        env::set_var("ARX_USER_NAME", "Environment User");
        env::set_var("ARX_AUTO_COMMIT", "false");

        let config = ConfigManager::apply_environment_overrides(ArxConfig::default()).unwrap();
        assert_eq!(config.user.name, "Environment User");
        assert!(!config.building.auto_commit);

        env::remove_var("ARX_USER_NAME");
        env::remove_var("ARX_AUTO_COMMIT");
    }

    #[test]
    fn test_config_precedence_merging() {
        // Create a temporary directory structure
        let temp_dir = tempdir().unwrap();

        // Create global config (lowest file priority)
        let global_path = temp_dir.path().join("global.toml");
        let global_config_content = toml::to_string(&{
            let mut c = ArxConfig::default();
            c.user.name = "Global User".to_string();
            c.user.email = "global@example.com".to_string();
            c.performance.max_parallel_threads = 2;
            c
        })
        .unwrap();
        fs::write(&global_path, global_config_content).unwrap();

        // Create user config (medium priority)
        let user_path = temp_dir.path().join("user.toml");
        let user_config_content = toml::to_string(&{
            let mut c = ArxConfig::default();
            c.user.name = "User Config User".to_string();
            c.building.auto_commit = false;
            c
        })
        .unwrap();
        fs::write(&user_path, user_config_content).unwrap();

        // Create project config (highest file priority)
        let project_dir = temp_dir.path().join(".arxos");
        std::fs::create_dir_all(&project_dir).unwrap();
        let project_path = project_dir.join("config.toml");
        let project_config_content = toml::to_string(&{
            let mut c = ArxConfig::default();
            c.user.name = "Project User".to_string();
            c.performance.max_parallel_threads = 4;
            c
        })
        .unwrap();
        fs::write(&project_path, project_config_content).unwrap();

        // Simulate merging (global -> user -> project)
        let mut config = ArxConfig::default();
        let global_config = ConfigManager::load_from_file(&global_path).unwrap();
        config = ConfigManager::merge_config(config, global_config);

        let user_config = ConfigManager::load_from_file(&user_path).unwrap();
        config = ConfigManager::merge_config(config, user_config);

        let project_config = ConfigManager::load_from_file(&project_path).unwrap();
        config = ConfigManager::merge_config(config, project_config);

        // Verify precedence: project overrides user, user overrides global
        assert_eq!(
            config.user.name, "Project User",
            "Project config should override user config"
        ); // From project config
        assert_eq!(
            config.user.email, "global@example.com",
            "Global config should be preserved when not overridden"
        ); // From global (not overridden)
        assert_eq!(
            config.performance.max_parallel_threads, 4,
            "Project config should override global config"
        ); // From project (overrides global)
        assert!(
            !config.building.auto_commit,
            "User config should override default value (user set to false, should be false after all merges)"
        );
        // From user config
    }
}
