//! Configuration management for ArxOS
//! 
//! This module provides a comprehensive configuration system that supports:
//! - Hierarchical configuration (global, project, command-specific)
//! - Environment variable overrides
//! - Hot reload capabilities
//! - Type-safe configuration with validation
//! - Sensible defaults

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use thiserror::Error;

pub mod manager;
pub mod validation;

pub use manager::ConfigManager;
pub use validation::ConfigValidator;

/// Main configuration structure for ArxOS
#[derive(Debug, Clone, Serialize, Deserialize)]
#[derive(Default)]
pub struct ArxConfig {
    /// User information and preferences
    pub user: UserConfig,
    /// File and directory paths
    pub paths: PathConfig,
    /// Building-specific settings
    pub building: BuildingConfig,
    /// Performance and optimization settings
    pub performance: PerformanceConfig,
    /// User interface preferences
    pub ui: UiConfig,
}

/// User information and preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserConfig {
    /// User's full name
    pub name: String,
    /// User's email address
    pub email: String,
    /// User's organization (optional)
    pub organization: Option<String>,
    /// Default commit message template
    pub commit_template: String,
}

/// File and directory path configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathConfig {
    /// Default directory for importing IFC files
    pub default_import_path: PathBuf,
    /// Directory for backup files
    pub backup_path: PathBuf,
    /// Directory for template files
    pub template_path: PathBuf,
    /// Directory for temporary files
    pub temp_path: PathBuf,
}

/// Building-specific configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingConfig {
    /// Default coordinate system for new buildings
    pub default_coordinate_system: String,
    /// Whether to auto-commit changes
    pub auto_commit: bool,
    /// Default building naming pattern
    pub naming_pattern: String,
    /// Whether to validate IFC files on import
    pub validate_on_import: bool,
}

/// Performance and optimization settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceConfig {
    /// Maximum number of parallel threads for processing
    pub max_parallel_threads: usize,
    /// Memory limit in MB
    pub memory_limit_mb: usize,
    /// Whether to enable caching
    pub cache_enabled: bool,
    /// Cache directory path
    pub cache_path: PathBuf,
    /// Whether to show progress bars
    pub show_progress: bool,
}

/// User interface preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    /// Whether to use emoji in output
    pub use_emoji: bool,
    /// Output verbosity level
    pub verbosity: VerbosityLevel,
    /// Color scheme preference
    pub color_scheme: ColorScheme,
    /// Whether to show detailed help by default
    pub detailed_help: bool,
}

/// Verbosity levels for output
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum VerbosityLevel {
    /// Silent mode - minimal output
    Silent,
    /// Normal mode - standard output
    Normal,
    /// Verbose mode - detailed output
    Verbose,
    /// Debug mode - maximum output
    Debug,
}

/// Color scheme preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ColorScheme {
    /// Auto-detect based on terminal
    Auto,
    /// Always use colors
    Always,
    /// Never use colors
    Never,
}

/// Configuration errors
#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("Configuration file not found: {path}")]
    FileNotFound { path: String },
    
    #[error("Invalid configuration format: {message}")]
    InvalidFormat { message: String },
    
    #[error("Configuration validation failed: {field} - {message}")]
    ValidationFailed { field: String, message: String },
    
    #[error("Path does not exist: {path}")]
    InvalidPath { path: PathBuf },
    
    #[error("Permission denied: {path}")]
    PermissionDenied { path: PathBuf },
    
    #[error("Environment variable error: {var} - {message}")]
    EnvironmentError { var: String, message: String },
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("TOML parsing error: {0}")]
    TomlError(#[from] toml::de::Error),
    
    #[error("TOML serialization error: {0}")]
    TomlSerializeError(#[from] toml::ser::Error),
}

/// Configuration result type
pub type ConfigResult<T> = Result<T, ConfigError>;


impl Default for UserConfig {
    fn default() -> Self {
        Self {
            name: "ArxOS User".to_string(),
            email: "user@arxos.com".to_string(),
            organization: None,
            commit_template: "feat: {operation} {building_name}".to_string(),
        }
    }
}

impl Default for PathConfig {
    fn default() -> Self {
        Self {
            default_import_path: PathBuf::from("./buildings"),
            backup_path: PathBuf::from("./backups"),
            template_path: PathBuf::from("./templates"),
            temp_path: PathBuf::from("./temp"),
        }
    }
}

impl Default for BuildingConfig {
    fn default() -> Self {
        Self {
            default_coordinate_system: "WGS84".to_string(),
            auto_commit: true,
            naming_pattern: "{building_name}-{timestamp}".to_string(),
            validate_on_import: true,
        }
    }
}

impl Default for PerformanceConfig {
    fn default() -> Self {
        Self {
            max_parallel_threads: num_cpus::get(),
            memory_limit_mb: 1024,
            cache_enabled: true,
            cache_path: PathBuf::from("./cache"),
            show_progress: true,
        }
    }
}

impl Default for UiConfig {
    fn default() -> Self {
        Self {
            use_emoji: true,
            verbosity: VerbosityLevel::Normal,
            color_scheme: ColorScheme::Auto,
            detailed_help: false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_default_config_creation() {
        let config = ArxConfig::default();
        assert_eq!(config.user.name, "ArxOS User");
        assert!(config.building.auto_commit);
        assert!(config.performance.show_progress);
    }
    
    #[test]
    fn test_config_serialization() {
        let config = ArxConfig::default();
        let toml = toml::to_string(&config).unwrap();
        assert!(toml.contains("name = \"ArxOS User\""));
        assert!(toml.contains("auto_commit = true"));
    }
    
    #[test]
    fn test_config_deserialization() {
        let toml = r#"
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
        
        let config: ArxConfig = toml::from_str(toml).unwrap();
        assert_eq!(config.user.name, "Test User");
        assert!(!config.building.auto_commit);
    }
}
