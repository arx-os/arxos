//! Maintenance and operational command arguments
//!
//! Argument structures for maintenance-related CLI commands including
//! validation, configuration, monitoring, and system health.

use clap::Args;

/// Arguments for the Validate command
///
/// Validate building data.
#[derive(Debug, Clone, Args)]
pub struct ValidateArgs {
    /// Path to building data
    #[arg(long)]
    pub path: Option<String>,
}

/// Arguments for the Config command
///
/// Manage configuration.
#[derive(Debug, Clone, Args)]
pub struct ConfigArgs {
    /// Show current configuration
    #[arg(long)]
    pub show: bool,

    /// Set configuration value (format: section.key=value)
    #[arg(long)]
    pub set: Option<String>,

    /// Reset to defaults
    #[arg(long)]
    pub reset: bool,

    /// Edit configuration file
    #[arg(long)]
    pub edit: bool,

    /// Open interactive wizard
    #[arg(long)]
    pub interactive: bool,
}

/// Arguments for the Watch command
///
/// Live monitoring dashboard.
#[derive(Debug, Clone, Args)]
pub struct WatchArgs {
    /// Building to monitor
    #[arg(long)]
    pub building: Option<String>,

    /// Floor to monitor
    #[arg(long)]
    pub floor: Option<i32>,

    /// Room to monitor
    #[arg(long)]
    pub room: Option<String>,

    /// Refresh interval in seconds (1-3600)
    #[arg(long, default_value = "5", value_parser = validate_refresh_interval)]
    pub refresh_interval: u64,

    /// Show sensors only
    #[arg(long)]
    pub sensors_only: bool,

    /// Show alerts only
    #[arg(long)]
    pub alerts_only: bool,

    /// Log level filter
    #[arg(long)]
    pub log_level: Option<String>,
}

/// Arguments for the Health command
///
/// Run system health diagnostics.
#[derive(Debug, Clone, Args)]
pub struct HealthArgs {
    /// Check specific component (all, git, config, persistence, yaml)
    #[arg(long)]
    pub component: Option<String>,

    /// Show detailed diagnostics
    #[arg(long)]
    pub verbose: bool,

    /// Open interactive dashboard
    #[arg(long)]
    pub interactive: bool,

    /// Generate comprehensive diagnostic report
    #[arg(long)]
    pub diagnostic: bool,
}

/// Arguments for the Filter command
///
/// Filter building data.
#[derive(Debug, Clone, Args)]
pub struct FilterArgs {
    /// Equipment type filter
    #[arg(long)]
    pub equipment_type: Option<String>,

    /// Equipment status filter
    #[arg(long)]
    pub status: Option<String>,

    /// Floor filter
    #[arg(long)]
    pub floor: Option<i32>,

    /// Room filter
    #[arg(long)]
    pub room: Option<String>,

    /// Building filter
    #[arg(long)]
    pub building: Option<String>,

    /// Show only critical equipment
    #[arg(long)]
    pub critical_only: bool,

    /// Show only healthy equipment
    #[arg(long)]
    pub healthy_only: bool,

    /// Show only equipment with alerts
    #[arg(long)]
    pub alerts_only: bool,

    /// Output format (table, json, yaml)
    #[arg(long, default_value = "table")]
    pub format: String,

    /// Maximum number of results
    #[arg(long, default_value = "100")]
    pub limit: usize,

    /// Show detailed results
    #[arg(long)]
    pub verbose: bool,
}

/// Arguments for the Doc command
///
/// Generate HTML documentation for a building.
#[derive(Debug, Clone, Args)]
pub struct DocArgs {
    /// Building name to document
    #[arg(long)]
    pub building: String,

    /// Output file path (default: ./docs/{building}.html)
    #[arg(long)]
    pub output: Option<String>,
}

/// Arguments for the ProcessSensors command
///
/// Process sensor data and update equipment status.
#[derive(Debug, Clone, Args)]
pub struct ProcessSensorsArgs {
    /// Directory containing sensor data files
    #[arg(long, default_value = "./sensor-data")]
    pub sensor_dir: String,

    /// Building name to update
    #[arg(long)]
    pub building: String,

    /// Commit changes to Git
    #[arg(long)]
    pub commit: bool,

    /// Watch mode: continuously monitor for new sensor data
    #[arg(long)]
    pub watch: bool,
}

/// Arguments for the SensorsHttp command
///
/// Start HTTP server for real-time sensor data ingestion.
#[derive(Debug, Clone, Args)]
pub struct SensorsHttpArgs {
    /// Building name to update
    #[arg(long)]
    pub building: String,

    /// Host address to bind to
    #[arg(long, default_value = "127.0.0.1")]
    pub host: String,

    /// Port to listen on (1-65535)
    #[arg(long, default_value = "3000", value_parser = validate_port)]
    pub port: u16,
}

/// Arguments for the SensorsMqtt command
///
/// Start MQTT subscriber for real-time sensor data ingestion.
#[derive(Debug, Clone, Args)]
pub struct SensorsMqttArgs {
    /// Building name to update
    #[arg(long)]
    pub building: String,

    /// MQTT broker URL
    #[arg(long, default_value = "localhost")]
    pub broker: String,

    /// MQTT broker port
    #[arg(long, default_value = "1883")]
    pub port: u16,

    /// MQTT username (optional)
    #[arg(long)]
    pub username: Option<String>,

    /// MQTT password (optional)
    #[arg(long)]
    pub password: Option<String>,

    /// MQTT topics to subscribe to (comma-separated)
    #[arg(long, default_value = "arxos/sensors/#")]
    pub topics: String,
}

/// Arguments for the Migrate command
///
/// Migrate existing fixtures to ArxAddress format.
#[derive(Debug, Clone, Args)]
pub struct MigrateArgs {
    /// Show what would be migrated without making changes
    #[arg(long)]
    pub dry_run: bool,
}

/// Arguments for the Verify command
///
/// Verify GPG signatures on Git commits.
#[derive(Debug, Clone, Args)]
pub struct VerifyArgs {
    /// Commit hash to verify (default: HEAD)
    #[arg(long)]
    pub commit: Option<String>,

    /// Verify all commits in current branch
    #[arg(long)]
    pub all: bool,

    /// Show detailed verification information
    #[arg(long)]
    pub verbose: bool,
}

/// Validate refresh interval is between 1 and 3600 seconds
fn validate_refresh_interval(s: &str) -> Result<u64, String> {
    let val: u64 = s
        .parse()
        .map_err(|_| "must be a number between 1 and 3600".to_string())?;
    if !(1..=3600).contains(&val) {
        Err(format!(
            "Refresh interval must be between 1 and 3600 seconds, got {}",
            val
        ))
    } else {
        Ok(val)
    }
}

/// Validate port is between 1 and 65535
fn validate_port(s: &str) -> Result<u16, String> {
    let val: u16 = s
        .parse()
        .map_err(|_| "must be a number between 1 and 65535".to_string())?;
    if val == 0 {
        Err("Port must be between 1 and 65535, got 0".to_string())
    } else {
        Ok(val)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_refresh_interval() {
        assert!(validate_refresh_interval("5").is_ok());
        assert!(validate_refresh_interval("1").is_ok());
        assert!(validate_refresh_interval("3600").is_ok());
        assert!(validate_refresh_interval("0").is_err());
        assert!(validate_refresh_interval("3601").is_err());
        assert!(validate_refresh_interval("invalid").is_err());
    }

    #[test]
    fn test_validate_port() {
        assert!(validate_port("3000").is_ok());
        assert!(validate_port("1").is_ok());
        assert!(validate_port("65535").is_ok());
        assert!(validate_port("0").is_err());
        assert!(validate_port("65536").is_err());
        assert!(validate_port("invalid").is_err());
    }

    #[test]
    fn test_validate_args_defaults() {
        // Verify that the Args derive works correctly
        // Actual parsing would need clap's testing utilities
    }
}
