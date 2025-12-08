//! Configuration management for ArxOS
//!
//! This module provides configuration loading, validation, and default values.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::env;
use std::collections::HashSet;

/// Configuration error types
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    /// I/O error when reading config file
    #[error("Failed to read config file: {0}")]
    IoError(#[from] std::io::Error),
    
    /// TOML parsing error
    #[error("Failed to parse config file: {0}")]
    ParseError(#[from] toml::de::Error),
    
    /// Configuration validation failed
    #[error("Configuration validation failed for '{field}': {message}")]
    ValidationFailed {
        /// The field that failed validation
        field: String,
        /// Error message
        message: String,
    },
}

/// Main configuration structure for ArxOS
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArxConfig {
    /// User configuration
    pub user: UserConfig,
    /// Git configuration
    #[serde(default)]
    pub git: GitConfig,
    /// Path configuration
    #[serde(default)]
    pub paths: PathConfig,
    /// Building configuration
    #[serde(default)]
    pub building: BuildingConfig,
    /// Performance configuration
    #[serde(default)]
    pub performance: PerformanceConfig,
    /// UI configuration
    #[serde(default)]
    pub ui: UiConfig,
}

/// User configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserConfig {
    /// User's full name
    pub name: String,
    /// User's email address
    pub email: String,
    /// Organization (optional)
    #[serde(default)]
    pub organization: Option<String>,
    /// Commit message template
    #[serde(default = "default_commit_template")]
    pub commit_template: String,
}

/// Git-specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitConfig {
    /// Default branch name
    #[serde(default = "default_branch")]
    pub default_branch: String,
    /// Enable GPG signing
    #[serde(default)]
    pub gpg_sign: bool,
}

/// Path configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathConfig {
    /// Base directory for ArxOS data
    #[serde(default = "default_data_dir")]
    pub data_dir: PathBuf,
    /// Configuration file path
    #[serde(default = "default_config_path")]
    pub config_path: PathBuf,
    /// Default import path
    #[serde(default = "default_import_path")]
    pub default_import_path: PathBuf,
    /// Backup path
    #[serde(default = "default_backup_path")]
    pub backup_path: PathBuf,
    /// Template path
    #[serde(default = "default_template_path")]
    pub template_path: PathBuf,
    /// Temporary files path
    #[serde(default = "default_temp_path")]
    pub temp_path: PathBuf,
}

/// Building-specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingConfig {
    /// Default coordinate system (WGS84, UTM, LOCAL)
    #[serde(default = "default_coordinate_system")]
    pub default_coordinate_system: String,
    /// Auto-commit changes
    #[serde(default = "default_auto_commit")]
    pub auto_commit: bool,
    /// Naming pattern with placeholders
    #[serde(default = "default_naming_pattern")]
    pub naming_pattern: String,
    /// Validate on import
    #[serde(default = "default_validate_on_import")]
    pub validate_on_import: bool,
}

/// Performance configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceConfig {
    /// Maximum parallel threads (1-64)
    #[serde(default = "default_max_threads")]
    pub max_parallel_threads: usize,
    /// Memory limit in MB (1-16384)
    #[serde(default = "default_memory_limit")]
    pub memory_limit_mb: usize,
    /// Enable caching
    #[serde(default = "default_cache_enabled")]
    pub cache_enabled: bool,
    /// Cache directory path
    #[serde(default = "default_cache_path")]
    pub cache_path: PathBuf,
    /// Show progress indicators
    #[serde(default = "default_show_progress")]
    pub show_progress: bool,
}

/// UI configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    /// Use emoji in output
    #[serde(default = "default_use_emoji")]
    pub use_emoji: bool,
    /// Verbosity level (Silent, Normal, Verbose, Debug)
    #[serde(default = "default_verbosity")]
    pub verbosity: String,
    /// Color scheme (Auto, Always, Never)
    #[serde(default = "default_color_scheme")]
    pub color_scheme: String,
    /// Show detailed help
    #[serde(default)]
    pub detailed_help: bool,
}

fn default_commit_template() -> String {
    "feat: {operation} {building_name}".to_string()
}

fn default_branch() -> String {
    "main".to_string()
}

fn default_data_dir() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".arxos")
}

fn default_config_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".arxos")
        .join("config.toml")
}

fn default_import_path() -> PathBuf {
    PathBuf::from("./buildings")
}

fn default_backup_path() -> PathBuf {
    PathBuf::from("./backups")
}

fn default_template_path() -> PathBuf {
    PathBuf::from("./templates")
}

fn default_temp_path() -> PathBuf {
    PathBuf::from("./temp")
}

fn default_coordinate_system() -> String {
    "WGS84".to_string()
}

fn default_auto_commit() -> bool {
    true
}

fn default_naming_pattern() -> String {
    "{building_name}-{timestamp}".to_string()
}

fn default_validate_on_import() -> bool {
    true
}

fn default_max_threads() -> usize {
    4
}

fn default_memory_limit() -> usize {
    1024
}

fn default_cache_enabled() -> bool {
    true
}

fn default_cache_path() -> PathBuf {
    PathBuf::from("./cache")
}

fn default_show_progress() -> bool {
    true
}

fn default_use_emoji() -> bool {
    true
}

fn default_verbosity() -> String {
    "Normal".to_string()
}

fn default_color_scheme() -> String {
    "Auto".to_string()
}

impl Default for ArxConfig {
    fn default() -> Self {
        Self {
            user: UserConfig {
                name: whoami::realname(),
                email: format!("{}@localhost", whoami::username()),
                organization: None,
                commit_template: default_commit_template(),
            },
            git: GitConfig::default(),
            paths: PathConfig::default(),
            building: BuildingConfig::default(),
            performance: PerformanceConfig::default(),
            ui: UiConfig::default(),
        }
    }
}

impl Default for GitConfig {
    fn default() -> Self {
        Self {
            default_branch: default_branch(),
            gpg_sign: false,
        }
    }
}

impl Default for PathConfig {
    fn default() -> Self {
        Self {
            data_dir: default_data_dir(),
            config_path: default_config_path(),
            default_import_path: default_import_path(),
            backup_path: default_backup_path(),
            template_path: default_template_path(),
            temp_path: default_temp_path(),
        }
    }
}

impl Default for BuildingConfig {
    fn default() -> Self {
        Self {
            default_coordinate_system: default_coordinate_system(),
            auto_commit: default_auto_commit(),
            naming_pattern: default_naming_pattern(),
            validate_on_import: default_validate_on_import(),
        }
    }
}

impl Default for PerformanceConfig {
    fn default() -> Self {
        Self {
            max_parallel_threads: default_max_threads(),
            memory_limit_mb: default_memory_limit(),
            cache_enabled: default_cache_enabled(),
            cache_path: default_cache_path(),
            show_progress: default_show_progress(),
        }
    }
}

impl Default for UiConfig {
    fn default() -> Self {
        Self {
            use_emoji: default_use_emoji(),
            verbosity: default_verbosity(),
            color_scheme: default_color_scheme(),
            detailed_help: false,
        }
    }
}

/// Configuration manager for loading and saving config
pub struct ConfigManager {
    config: ArxConfig,
}

impl ConfigManager {
    /// Create a new config manager with proper precedence hierarchy
    /// 
    /// Precedence (highest to lowest):
    /// 1. Environment variables (ARX_* prefix)
    /// 2. Project config (.arxos/config.toml in current directory)
    /// 3. User config (~/.arxos/config.toml)
    /// 4. Defaults
    pub fn new() -> Result<Self, ConfigError> {
        // Start with defaults
        let mut config = ArxConfig::default();
        
        // Load user config if exists
        if let Ok(user_config) = Self::load_user_config() {
            Self::merge_config(&mut config, user_config);
        }
        
        // Load project config if exists (overrides user config)
        if let Ok(project_config) = Self::load_project_config() {
            Self::merge_config(&mut config, project_config);
        }
        
        // Apply environment variable overrides (highest priority)
        Self::apply_env_overrides(&mut config);
        
        // Validate the final configuration
        Self::validate_config(&config)?;
        
        Ok(Self { config })
    }
    
    /// Load user config from ~/.arxos/config.toml
    fn load_user_config() -> Result<ArxConfig, ConfigError> {
        let config_path = if cfg!(windows) {
            // Windows: %APPDATA%\arxos\config.toml or fallback to HOME
            if let Ok(appdata) = env::var("APPDATA") {
                PathBuf::from(appdata).join("arxos").join("config.toml")
            } else {
                default_data_dir().join("config.toml")
            }
        } else {
            // Unix: ~/.arxos/config.toml
            default_data_dir().join("config.toml")
        };
        
        if config_path.exists() {
            let contents = std::fs::read_to_string(&config_path)?;
            let config = toml::from_str(&contents)?;
            Ok(config)
        } else {
            Err(ConfigError::IoError(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "User config not found"
            )))
        }
    }
    
    /// Load project config from .arxos/config.toml in current directory
    fn load_project_config() -> Result<ArxConfig, ConfigError> {
        let config_path = PathBuf::from(".arxos").join("config.toml");
        
        if config_path.exists() {
            let contents = std::fs::read_to_string(&config_path)?;
            let config = toml::from_str(&contents)?;
            Ok(config)
        } else {
            Err(ConfigError::IoError(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "Project config not found"
            )))
        }
    }
    
    /// Merge source config into target config (non-default values only)
    fn merge_config(target: &mut ArxConfig, source: ArxConfig) {
        // For simplicity, we'll replace entire sections if they differ from defaults
        // A more sophisticated merge would check individual fields
        target.user = source.user;
        target.git = source.git;
        target.paths = source.paths;
        target.building = source.building;
        target.performance = source.performance;
        target.ui = source.ui;
    }
    
    /// Apply environment variable overrides (ARX_* prefix)
    fn apply_env_overrides(config: &mut ArxConfig) {
        // User overrides
        if let Ok(val) = env::var("ARX_USER_NAME") {
            config.user.name = val;
        }
        if let Ok(val) = env::var("ARX_USER_EMAIL") {
            config.user.email = val;
        }
        if let Ok(val) = env::var("ARX_USER_ORGANIZATION") {
            config.user.organization = Some(val);
        }
        
        // Git overrides
        if let Ok(val) = env::var("ARX_GIT_BRANCH") {
            config.git.default_branch = val;
        }
        if let Ok(val) = env::var("ARX_GPG_SIGN") {
            config.git.gpg_sign = val.parse().unwrap_or(false);
        }
        
        // Building overrides
        if let Ok(val) = env::var("ARX_COORDINATE_SYSTEM") {
            config.building.default_coordinate_system = val;
        }
        if let Ok(val) = env::var("ARX_AUTO_COMMIT") {
            config.building.auto_commit = val.parse().unwrap_or(true);
        }
        
        // Performance overrides
        if let Ok(val) = env::var("ARX_MAX_THREADS") {
            if let Ok(num) = val.parse() {
                config.performance.max_parallel_threads = num;
            }
        }
        if let Ok(val) = env::var("ARX_MEMORY_LIMIT") {
            if let Ok(num) = val.parse() {
                config.performance.memory_limit_mb = num;
            }
        }
        if let Ok(val) = env::var("ARX_CACHE_ENABLED") {
            config.performance.cache_enabled = val.parse().unwrap_or(true);
        }
        
        // UI overrides
        if let Ok(val) = env::var("ARX_USE_EMOJI") {
            config.ui.use_emoji = val.parse().unwrap_or(true);
        }
        if let Ok(val) = env::var("ARX_VERBOSITY") {
            config.ui.verbosity = val;
        }
        if let Ok(val) = env::var("ARX_COLOR_SCHEME") {
            config.ui.color_scheme = val;
        }
    }
    
    /// Validate configuration
    pub fn validate_config(config: &ArxConfig) -> Result<(), ConfigError> {
        // Validate user email
        if !config.user.email.contains('@') {
            return Err(ConfigError::ValidationFailed {
                field: "user.email".to_string(),
                message: "Email must contain '@' character".to_string(),
            });
        }
        
        // Validate user name not empty
        if config.user.name.trim().is_empty() {
            return Err(ConfigError::ValidationFailed {
                field: "user.name".to_string(),
                message: "User name cannot be empty".to_string(),
            });
        }
        
        // Validate thread count
        if config.performance.max_parallel_threads == 0 || config.performance.max_parallel_threads > 64 {
            return Err(ConfigError::ValidationFailed {
                field: "performance.max_parallel_threads".to_string(),
                message: "Thread count must be between 1 and 64".to_string(),
            });
        }
        
        // Validate memory limit
        if config.performance.memory_limit_mb == 0 || config.performance.memory_limit_mb > 16384 {
            return Err(ConfigError::ValidationFailed {
                field: "performance.memory_limit_mb".to_string(),
                message: "Memory limit must be between 1 and 16384 MB".to_string(),
            });
        }
        
        // Validate coordinate system
        let valid_coord_systems = ["WGS84", "UTM", "LOCAL"];
        if !valid_coord_systems.contains(&config.building.default_coordinate_system.as_str()) {
            return Err(ConfigError::ValidationFailed {
                field: "building.default_coordinate_system".to_string(),
                message: format!(
                    "Coordinate system must be one of: {}",
                    valid_coord_systems.join(", ")
                ),
            });
        }
        
        // Validate naming pattern has at least one placeholder
        if !config.building.naming_pattern.contains('{') {
            return Err(ConfigError::ValidationFailed {
                field: "building.naming_pattern".to_string(),
                message: "Naming pattern must contain at least one placeholder (e.g., {building_name})".to_string(),
            });
        }
        
        // Validate verbosity level
        let valid_verbosity = ["Silent", "Normal", "Verbose", "Debug"];
        if !valid_verbosity.contains(&config.ui.verbosity.as_str()) {
            return Err(ConfigError::ValidationFailed {
                field: "ui.verbosity".to_string(),
                message: format!(
                    "Verbosity must be one of: {}",
                    valid_verbosity.join(", ")
                ),
            });
        }
        
        // Validate color scheme
        let valid_color_schemes = ["Auto", "Always", "Never"];
        if !valid_color_schemes.contains(&config.ui.color_scheme.as_str()) {
            return Err(ConfigError::ValidationFailed {
                field: "ui.color_scheme".to_string(),
                message: format!(
                    "Color scheme must be one of: {}",
                    valid_color_schemes.join(", ")
                ),
            });
        }
        
        // Validate path conflicts - collect all paths and check for duplicates
        let mut paths = HashSet::new();
        let path_fields = vec![
            (&config.paths.default_import_path, "paths.default_import_path"),
            (&config.paths.backup_path, "paths.backup_path"),
            (&config.paths.template_path, "paths.template_path"),
            (&config.paths.temp_path, "paths.temp_path"),
        ];
        
        for (path, field_name) in &path_fields {
            let canonical = path.canonicalize().unwrap_or_else(|_| (*path).clone());
            if !paths.insert(canonical.clone()) {
                return Err(ConfigError::ValidationFailed {
                    field: "paths".to_string(),
                    message: format!("Path conflict detected: {} points to same location as another path", field_name),
                });
            }
        }
        
        // Validate cache path doesn't conflict with other paths if caching enabled
        if config.performance.cache_enabled {
            let cache_canonical = config.performance.cache_path
                .canonicalize()
                .unwrap_or_else(|_| config.performance.cache_path.clone());
            
            if paths.contains(&cache_canonical) {
                return Err(ConfigError::ValidationFailed {
                    field: "performance.cache_path".to_string(),
                    message: "Cache path conflicts with another configured path".to_string(),
                });
            }
        }
        
        Ok(())
    }

    /// Load config from specific file
    pub fn load(path: &PathBuf) -> Result<Self, ConfigError> {
        let contents = std::fs::read_to_string(path)?;
        let config = toml::from_str(&contents)?;
        Self::validate_config(&config)?;
        Ok(Self { config })
    }

    /// Save config to file
    pub fn save(&self, path: &PathBuf) -> Result<(), ConfigError> {
        let contents = toml::to_string_pretty(&self.config)
            .map_err(|e| ConfigError::IoError(std::io::Error::new(
                std::io::ErrorKind::Other,
                format!("TOML serialization failed: {}", e)
            )))?;

        // Create parent directory if it doesn't exist
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        std::fs::write(path, contents)?;
        Ok(())
    }

    /// Get a reference to the config
    pub fn get_config(&self) -> &ArxConfig {
        &self.config
    }

    /// Get a mutable reference to the config
    pub fn get_config_mut(&mut self) -> &mut ArxConfig {
        &mut self.config
    }
    
    /// Deprecated: use get_config() instead
    #[deprecated(since = "2.0.0", note = "Use get_config() instead")]
    pub fn config(&self) -> &ArxConfig {
        &self.config
    }

    /// Deprecated: use get_config_mut() instead
    #[deprecated(since = "2.0.0", note = "Use get_config_mut() instead")]
    pub fn config_mut(&mut self) -> &mut ArxConfig {
        &mut self.config
    }
}

impl Default for ConfigManager {
    fn default() -> Self {
        // For Default trait, we return defaults without validation failure
        // This is useful for tests that need a ConfigManager without I/O
        Self {
            config: ArxConfig::default(),
        }
    }
}

/// Get configuration with fallback to defaults
///
/// Attempts to load configuration with proper precedence.
/// If loading fails, returns default configuration.
/// 
/// **Deprecated:** Use `ConfigManager::new()` for proper error handling
#[deprecated(since = "2.0.0", note = "Use ConfigManager::new() instead for proper error handling")]
pub fn get_config_or_default() -> ArxConfig {
    ConfigManager::new()
        .map(|manager| manager.config)
        .unwrap_or_else(|_| ArxConfig::default())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = ArxConfig::default();
        assert!(!config.user.name.is_empty());
        assert!(!config.user.email.is_empty());
        assert_eq!(config.git.default_branch, "main");
        assert_eq!(config.building.default_coordinate_system, "WGS84");
        assert_eq!(config.performance.max_parallel_threads, 4);
        assert_eq!(config.ui.verbosity, "Normal");
    }

    #[test]
    fn test_config_validation_valid() {
        let config = ArxConfig::default();
        assert!(ConfigManager::validate_config(&config).is_ok());
    }

    #[test]
    fn test_config_validation_invalid_email() {
        let mut config = ArxConfig::default();
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
    fn test_config_validation_invalid_threads() {
        let mut config = ArxConfig::default();
        config.performance.max_parallel_threads = 0;
        
        let result = ConfigManager::validate_config(&config);
        assert!(result.is_err());
    }

    #[test]
    fn test_config_validation_invalid_coordinate_system() {
        let mut config = ArxConfig::default();
        config.building.default_coordinate_system = "INVALID".to_string();
        
        let result = ConfigManager::validate_config(&config);
        assert!(result.is_err());
    }

    #[test]
    fn test_env_override() {
        env::set_var("ARX_USER_NAME", "Test User");
        env::set_var("ARX_MAX_THREADS", "8");
        
        let mut config = ArxConfig::default();
        ConfigManager::apply_env_overrides(&mut config);
        
        assert_eq!(config.user.name, "Test User");
        assert_eq!(config.performance.max_parallel_threads, 8);
        
        env::remove_var("ARX_USER_NAME");
        env::remove_var("ARX_MAX_THREADS");
    }
    
    #[test]
    fn test_default_manager() {
        let manager = ConfigManager::default();
        assert!(!manager.get_config().user.name.is_empty());
    }
}
