//! Configuration validation for ArxOS
//!
//! This module provides configuration validation utilities to ensure
//! that configuration values are valid and consistent.
//!
//! Validation is performed using:
//! - Rule-based validation (fast, compile-time checked)
//! - Schema-based validation (comprehensive, runtime schema validation - optional)

use super::{
    ArxConfig, BuildingConfig, ConfigError, ConfigResult, PathConfig, PerformanceConfig, UiConfig,
    UserConfig,
};
use std::path::PathBuf;

/// Configuration validator for ArxOS
pub struct ConfigValidator;

impl ConfigValidator {
    /// Validate the entire configuration
    pub fn validate(config: &ArxConfig) -> ConfigResult<()> {
        Self::validate_user_config(&config.user)?;
        Self::validate_path_config(&config.paths)?;
        Self::validate_building_config(&config.building)?;
        Self::validate_performance_config(&config.performance)?;
        Self::validate_ui_config(&config.ui)?;

        // Cross-configuration validation
        Self::validate_cross_config(config)?;

        Ok(())
    }

    /// Validate common configuration rules (shared between relaxed and strict validation)
    ///
    /// This performs validation checks that are common to both relaxed and strict
    /// validation modes, reducing code duplication.
    pub fn validate_common(config: &ArxConfig) -> ConfigResult<()> {
        // Validate user configuration
        if config.user.name.len() > 100 {
            return Err(super::ConfigError::ValidationFailed {
                field: "user.name".to_string(),
                message: "User name cannot exceed 100 characters".to_string(),
            });
        }

        if !config.user.email.is_empty() && !Self::is_valid_email(&config.user.email) {
            return Err(super::ConfigError::ValidationFailed {
                field: "user.email".to_string(),
                message: "Email must be valid format".to_string(),
            });
        }

        // Validate performance settings
        if config.performance.max_parallel_threads == 0 {
            return Err(super::ConfigError::ValidationFailed {
                field: "performance.max_parallel_threads".to_string(),
                message: "Must be greater than 0".to_string(),
            });
        }

        if config.performance.max_parallel_threads > 64 {
            return Err(super::ConfigError::ValidationFailed {
                field: "performance.max_parallel_threads".to_string(),
                message: "Cannot exceed 64 threads".to_string(),
            });
        }

        if config.performance.memory_limit_mb == 0 {
            return Err(super::ConfigError::ValidationFailed {
                field: "performance.memory_limit_mb".to_string(),
                message: "Must be greater than 0".to_string(),
            });
        }

        if config.performance.memory_limit_mb > 16384 {
            return Err(super::ConfigError::ValidationFailed {
                field: "performance.memory_limit_mb".to_string(),
                message: "Cannot exceed 16GB (16384 MB)".to_string(),
            });
        }

        // Validate building configuration
        let valid_coordinate_systems = ["WGS84", "UTM", "LOCAL"];
        if !valid_coordinate_systems.contains(&config.building.default_coordinate_system.as_str()) {
            return Err(super::ConfigError::ValidationFailed {
                field: "building.default_coordinate_system".to_string(),
                message: format!("Must be one of: {}", valid_coordinate_systems.join(", ")),
            });
        }

        Ok(())
    }

    /// Validate user configuration
    fn validate_user_config(user: &UserConfig) -> ConfigResult<()> {
        if user.name.trim().is_empty() {
            return Err(ConfigError::ValidationFailed {
                field: "user.name".to_string(),
                message: "User name cannot be empty or whitespace only".to_string(),
            });
        }

        if user.name.len() > 100 {
            return Err(ConfigError::ValidationFailed {
                field: "user.name".to_string(),
                message: "User name cannot exceed 100 characters".to_string(),
            });
        }

        if !Self::is_valid_email(&user.email) {
            return Err(ConfigError::ValidationFailed {
                field: "user.email".to_string(),
                message: "Email must be valid format".to_string(),
            });
        }

        if let Some(ref org) = user.organization {
            if org.trim().is_empty() {
                return Err(ConfigError::ValidationFailed {
                    field: "user.organization".to_string(),
                    message: "Organization cannot be empty or whitespace only".to_string(),
                });
            }
        }

        if user.commit_template.trim().is_empty() {
            return Err(ConfigError::ValidationFailed {
                field: "user.commit_template".to_string(),
                message: "Commit template cannot be empty".to_string(),
            });
        }

        Ok(())
    }

    /// Validate path configuration
    /// Paths don't need to exist at validation time (relaxed validation)
    fn validate_path_config(paths: &PathConfig) -> ConfigResult<()> {
        // Check if paths exist and are valid directories (if they exist)
        // Don't require paths to exist - they may be created later
        if paths.default_import_path.exists() {
            Self::validate_path_exists(&paths.default_import_path, "paths.default_import_path")?;
        }
        if paths.backup_path.exists() {
            Self::validate_path_exists(&paths.backup_path, "paths.backup_path")?;
        }
        if paths.template_path.exists() {
            Self::validate_path_exists(&paths.template_path, "paths.template_path")?;
        }
        if paths.temp_path.exists() {
            Self::validate_path_exists(&paths.temp_path, "paths.temp_path")?;
        }

        // Check for path conflicts (only if paths resolve to the same location)
        let path_vec = [
            &paths.default_import_path,
            &paths.backup_path,
            &paths.template_path,
            &paths.temp_path,
        ];

        for (i, path1) in path_vec.iter().enumerate() {
            for (j, path2) in path_vec.iter().enumerate() {
                if i != j {
                    // Normalize paths for comparison
                    let p1 = path1.canonicalize().unwrap_or_else(|_| path1.to_path_buf());
                    let p2 = path2.canonicalize().unwrap_or_else(|_| path2.to_path_buf());
                    if p1 == p2 {
                        return Err(ConfigError::ValidationFailed {
                            field: "paths".to_string(),
                            message: format!("Duplicate paths found: {:?}", path1),
                        });
                    }
                }
            }
        }

        Ok(())
    }

    /// Validate building configuration
    fn validate_building_config(building: &BuildingConfig) -> ConfigResult<()> {
        let valid_coordinate_systems = ["WGS84", "UTM", "LOCAL"];
        if !valid_coordinate_systems.contains(&building.default_coordinate_system.as_str()) {
            return Err(ConfigError::ValidationFailed {
                field: "building.default_coordinate_system".to_string(),
                message: format!("Must be one of: {}", valid_coordinate_systems.join(", ")),
            });
        }

        if building.naming_pattern.trim().is_empty() {
            return Err(ConfigError::ValidationFailed {
                field: "building.naming_pattern".to_string(),
                message: "Naming pattern cannot be empty".to_string(),
            });
        }

        // Validate naming pattern contains required placeholders
        if !building.naming_pattern.contains("{building_name}") {
            return Err(ConfigError::ValidationFailed {
                field: "building.naming_pattern".to_string(),
                message: "Naming pattern must contain {building_name} placeholder".to_string(),
            });
        }

        Ok(())
    }

    /// Validate performance configuration
    fn validate_performance_config(performance: &PerformanceConfig) -> ConfigResult<()> {
        if performance.max_parallel_threads == 0 {
            return Err(ConfigError::ValidationFailed {
                field: "performance.max_parallel_threads".to_string(),
                message: "Must be greater than 0".to_string(),
            });
        }

        if performance.max_parallel_threads > 64 {
            return Err(ConfigError::ValidationFailed {
                field: "performance.max_parallel_threads".to_string(),
                message: "Cannot exceed 64 threads".to_string(),
            });
        }

        if performance.memory_limit_mb == 0 {
            return Err(ConfigError::ValidationFailed {
                field: "performance.memory_limit_mb".to_string(),
                message: "Must be greater than 0".to_string(),
            });
        }

        if performance.memory_limit_mb > 16384 {
            return Err(ConfigError::ValidationFailed {
                field: "performance.memory_limit_mb".to_string(),
                message: "Cannot exceed 16GB (16384 MB)".to_string(),
            });
        }

        if performance.cache_enabled && performance.cache_path.exists() {
            Self::validate_path_exists(&performance.cache_path, "performance.cache_path")?;
        }

        Ok(())
    }

    /// Validate UI configuration
    fn validate_ui_config(_ui: &UiConfig) -> ConfigResult<()> {
        // UI configuration is generally safe, but we can add validation here if needed
        Ok(())
    }

    /// Validate cross-configuration dependencies
    fn validate_cross_config(config: &ArxConfig) -> ConfigResult<()> {
        // Check if cache path conflicts with other paths
        if config.performance.cache_enabled {
            let cache_path = &config.performance.cache_path;
            let other_paths = vec![
                &config.paths.default_import_path,
                &config.paths.backup_path,
                &config.paths.template_path,
                &config.paths.temp_path,
            ];

            for path in other_paths {
                if cache_path == path {
                    return Err(ConfigError::ValidationFailed {
                        field: "performance.cache_path".to_string(),
                        message: "Cache path cannot be the same as other configured paths"
                            .to_string(),
                    });
                }
            }
        }

        Ok(())
    }

    /// Validate if a path exists and is accessible
    fn validate_path_exists(path: &PathBuf, field_name: &str) -> ConfigResult<()> {
        if !path.exists() {
            return Err(ConfigError::InvalidPath { path: path.clone() });
        }

        if !path.is_dir() {
            return Err(ConfigError::ValidationFailed {
                field: field_name.to_string(),
                message: "Path must be a directory".to_string(),
            });
        }

        // Check if we can read the directory
        std::fs::read_dir(path)
            .map_err(|_| ConfigError::PermissionDenied { path: path.clone() })?;

        Ok(())
    }

    /// Check if email format is valid
    fn is_valid_email(email: &str) -> bool {
        let email = email.trim();
        if email.is_empty() {
            return false;
        }

        let parts: Vec<&str> = email.split('@').collect();
        if parts.len() != 2 {
            return false;
        }

        let (local, domain) = (parts[0], parts[1]);
        if local.is_empty() || domain.is_empty() {
            return false;
        }

        if !domain.contains('.') {
            return false;
        }

        // Basic character validation
        for ch in local.chars() {
            if !ch.is_alphanumeric() && ch != '.' && ch != '_' && ch != '-' {
                return false;
            }
        }

        for ch in domain.chars() {
            if !ch.is_alphanumeric() && ch != '.' && ch != '-' {
                return false;
            }
        }

        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_config_validation() {
        let mut config = ArxConfig::default();
        // Create temporary directories for testing
        let temp_dir = std::env::temp_dir().join("arxos_test");
        std::fs::create_dir_all(&temp_dir).unwrap();

        config.paths.default_import_path = temp_dir.join("buildings");
        config.paths.backup_path = temp_dir.join("backups");
        config.paths.template_path = temp_dir.join("templates");
        config.paths.temp_path = temp_dir.join("temp");
        config.performance.cache_path = temp_dir.join("cache");

        std::fs::create_dir_all(&config.paths.default_import_path).unwrap();
        std::fs::create_dir_all(&config.paths.backup_path).unwrap();
        std::fs::create_dir_all(&config.paths.template_path).unwrap();
        std::fs::create_dir_all(&config.paths.temp_path).unwrap();
        std::fs::create_dir_all(&config.performance.cache_path).unwrap();

        let result = ConfigValidator::validate(&config);
        if let Err(e) = &result {
            println!("Validation error: {:?}", e);
        }
        assert!(result.is_ok());

        // Cleanup
        std::fs::remove_dir_all(&temp_dir).unwrap();
    }

    #[test]
    fn test_invalid_user_name() {
        let mut config = ArxConfig::default();
        config.user.name = "".to_string();

        let result = ConfigValidator::validate(&config);
        assert!(result.is_err());
    }

    #[test]
    fn test_invalid_email() {
        let mut config = ArxConfig::default();
        config.user.email = "invalid-email".to_string();

        let result = ConfigValidator::validate(&config);
        assert!(result.is_err());
    }

    #[test]
    fn test_invalid_coordinate_system() {
        let mut config = ArxConfig::default();
        config.building.default_coordinate_system = "INVALID".to_string();

        let result = ConfigValidator::validate(&config);
        assert!(result.is_err());
    }

    #[test]
    fn test_invalid_thread_count() {
        let mut config = ArxConfig::default();
        config.performance.max_parallel_threads = 0;

        let result = ConfigValidator::validate(&config);
        assert!(result.is_err());
    }

    #[test]
    fn test_email_validation() {
        assert!(ConfigValidator::is_valid_email("user@example.com"));
        assert!(ConfigValidator::is_valid_email("test.user@domain.org"));
        assert!(!ConfigValidator::is_valid_email("invalid-email"));
        assert!(!ConfigValidator::is_valid_email(""));
        assert!(!ConfigValidator::is_valid_email("@domain.com"));
        assert!(!ConfigValidator::is_valid_email("user@"));
    }
}
