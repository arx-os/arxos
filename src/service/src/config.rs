//! Service Configuration
//!
//! Configuration management for ArxOS Service

use anyhow::Result;
use config::{Config, ConfigError, File};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ServiceConfig {
    pub meshtastic: MeshtasticConfig,
    pub building: BuildingConfig,
    pub database: DatabaseConfig,
    pub terminal: TerminalConfig,
    pub service: ServiceSettings,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MeshtasticConfig {
    pub port: String,
    pub baud_rate: u32,
    pub node_id: u16,
    pub timeout_seconds: u64,
    pub retry_attempts: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BuildingConfig {
    pub id: String,
    pub name: String,
    pub location: Location,
    pub description: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Location {
    pub lat: f64,
    pub lon: f64,
    pub altitude: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DatabaseConfig {
    pub path: String,
    pub max_size: String,
    pub backup_interval: u64,
    pub retention_days: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TerminalConfig {
    pub prompt: String,
    pub history_size: usize,
    pub auto_complete: bool,
    pub syntax_highlighting: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ServiceSettings {
    pub log_level: String,
    pub max_connections: u32,
    pub heartbeat_interval: u64,
    pub cleanup_interval: u64,
}

impl Default for ServiceConfig {
    fn default() -> Self {
        Self {
            meshtastic: MeshtasticConfig {
                port: "/dev/ttyUSB0".to_string(),
                baud_rate: 9600,
                node_id: 0x0001,
                timeout_seconds: 30,
                retry_attempts: 3,
            },
            building: BuildingConfig {
                id: "building-001".to_string(),
                name: "Crystal Tower".to_string(),
                location: Location {
                    lat: 40.7128,
                    lon: -74.0060,
                    altitude: Some(10.0),
                },
                description: Some("Default building configuration".to_string()),
            },
            database: DatabaseConfig {
                path: "/var/lib/arxos/building.db".to_string(),
                max_size: "100MB".to_string(),
                backup_interval: 3600, // 1 hour
                retention_days: 30,
            },
            terminal: TerminalConfig {
                prompt: "arx>".to_string(),
                history_size: 1000,
                auto_complete: true,
                syntax_highlighting: true,
            },
            service: ServiceSettings {
                log_level: "info".to_string(),
                max_connections: 100,
                heartbeat_interval: 60, // 1 minute
                cleanup_interval: 3600, // 1 hour
            },
        }
    }
}

impl ServiceConfig {
    /// Load configuration from file
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, ConfigError> {
        let mut config = Config::new();

        // Start with default configuration
        config.merge(Config::try_from(&ServiceConfig::default())?)?;

        // Override with file configuration if it exists
        if path.as_ref().exists() {
            config.merge(File::from(path.as_ref()))?;
        }

        config.try_into()
    }

    /// Save configuration to file
    pub fn save<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        let toml = toml::to_string_pretty(self)?;
        std::fs::write(path, toml)?;
        Ok(())
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<()> {
        // Validate Meshtastic configuration
        if self.meshtastic.port.is_empty() {
            anyhow::bail!("Meshtastic port cannot be empty");
        }

        if self.meshtastic.baud_rate == 0 {
            anyhow::bail!("Meshtastic baud rate must be greater than 0");
        }

        if self.meshtastic.node_id == 0 {
            anyhow::bail!("Meshtastic node ID cannot be 0");
        }

        // Validate building configuration
        if self.building.id.is_empty() {
            anyhow::bail!("Building ID cannot be empty");
        }

        if self.building.name.is_empty() {
            anyhow::bail!("Building name cannot be empty");
        }

        // Validate location
        if !(-90.0..=90.0).contains(&self.building.location.lat) {
            anyhow::bail!("Latitude must be between -90 and 90 degrees");
        }

        if !(-180.0..=180.0).contains(&self.building.location.lon) {
            anyhow::bail!("Longitude must be between -180 and 180 degrees");
        }

        // Validate database configuration
        if self.database.path.is_empty() {
            anyhow::bail!("Database path cannot be empty");
        }

        Ok(())
    }
}
