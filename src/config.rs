//! Configuration management for ArxOS
//!
//! This module provides configuration loading, validation, and default values.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

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
}

/// User configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserConfig {
    /// User's full name
    pub name: String,
    /// User's email address
    pub email: String,
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

impl Default for ArxConfig {
    fn default() -> Self {
        Self {
            user: UserConfig {
                name: whoami::realname(),
                email: format!("{}@localhost", whoami::username()),
            },
            git: GitConfig::default(),
            paths: PathConfig::default(),
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
        }
    }
}

/// Get configuration with fallback to defaults
///
/// Attempts to load configuration from the standard config file location.
/// If the file doesn't exist or can't be read, returns default configuration.
pub fn get_config_or_default() -> ArxConfig {
    let config_path = default_config_path();

    if config_path.exists() {
        match std::fs::read_to_string(&config_path) {
            Ok(contents) => match toml::from_str::<ArxConfig>(&contents) {
                Ok(config) => return config,
                Err(e) => {
                    eprintln!("Warning: Failed to parse config file: {}", e);
                }
            },
            Err(e) => {
                eprintln!("Warning: Failed to read config file: {}", e);
            }
        }
    }

    ArxConfig::default()
}

/// Configuration manager for loading and saving config
pub struct ConfigManager {
    config: ArxConfig,
}

impl ConfigManager {
    /// Create a new config manager with default config
    pub fn new() -> Self {
        Self {
            config: get_config_or_default(),
        }
    }

    /// Load config from file
    pub fn load(path: &PathBuf) -> Result<Self, Box<dyn std::error::Error>> {
        let contents = std::fs::read_to_string(path)?;
        let config = toml::from_str(&contents)?;
        Ok(Self { config })
    }

    /// Save config to file
    pub fn save(&self, path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        let contents = toml::to_string_pretty(&self.config)?;

        // Create parent directory if it doesn't exist
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        std::fs::write(path, contents)?;
        Ok(())
    }

    /// Get a reference to the config
    pub fn config(&self) -> &ArxConfig {
        &self.config
    }

    /// Get a mutable reference to the config
    pub fn config_mut(&mut self) -> &mut ArxConfig {
        &mut self.config
    }
}

impl Default for ConfigManager {
    fn default() -> Self {
        Self::new()
    }
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
    }

    #[test]
    fn test_get_config_or_default() {
        let config = get_config_or_default();
        assert!(!config.user.name.is_empty());
    }

    #[test]
    fn test_config_manager() {
        let manager = ConfigManager::new();
        assert!(!manager.config().user.name.is_empty());
    }
}
