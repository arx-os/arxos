//! Sensor command handlers for SSH remote control
//! 
//! Supports hybrid real-time (hardware) and historical (Git) queries.

use anyhow::Result;
use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;

use crate::hardware::{HardwareManager, SensorReading as HwReading};
use crate::sensor::storage::{SensorSnapshot, SensorStorage, SensorValue, StorageConfig};

/// Query mode for sensor commands
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum QueryMode {
    Realtime,   // Query hardware directly (fast)
    Historical, // Query from Git (slower, for trends)
}

/// Query options
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryOptions {
    pub mode: QueryMode,
    pub log: bool,                      // Log to Git?
    pub duration: Option<Duration>,     // For historical queries
    pub from: Option<DateTime<Utc>>,    // For historical queries
    pub to: Option<DateTime<Utc>>,      // For historical queries
}

impl Default for QueryOptions {
    fn default() -> Self {
        Self {
            mode: QueryMode::Realtime,
            log: false,
            duration: None,
            from: None,
            to: None,
        }
    }
}

/// Sensor command result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorResult {
    pub location: String,
    pub sensor_type: String,
    pub value: f64,
    pub unit: String,
    pub timestamp: DateTime<Utc>,
    pub source: String, // "realtime" or "historical"
}

/// Sensor command handler
pub struct SensorCommands {
    hardware: Arc<HardwareManager>,
    storage: SensorStorage,
}

impl SensorCommands {
    pub fn new(hardware: Arc<HardwareManager>, repo_root: PathBuf) -> Self {
        let storage = SensorStorage::new(repo_root, StorageConfig::default());
        Self { hardware, storage }
    }

    /// Get temperature reading
    pub async fn get_temp(
        &self,
        location: &str,
        options: QueryOptions,
    ) -> Result<SensorResult> {
        match options.mode {
            QueryMode::Realtime => {
                // Query hardware directly
                let reading = self.hardware.read_sensor(location, "temperature").await?;
                
                // Optionally log to Git
                if options.log {
                    self.log_reading(location, "temperature", &reading).await?;
                }
                
                Ok(SensorResult {
                    location: location.to_string(),
                    sensor_type: "temperature".to_string(),
                    value: reading.value,
                    unit: reading.unit,
                    timestamp: reading.timestamp,
                    source: "realtime".to_string(),
                })
            }
            QueryMode::Historical => {
                // Query from Git
                self.get_historical(location, "temperature", options).await
            }
        }
    }

    /// Set temperature setpoint
    pub async fn set_temp(
        &self,
        location: &str,
        value: f64,
        log: bool,
    ) -> Result<String> {
        // Always write to hardware immediately
        self.hardware.write_control(location, "temperature_setpoint", value).await?;
        
        // Optionally log to Git
        if log {
            let mut readings = HashMap::new();
            readings.insert(
                format!("{}:setpoint", location),
                SensorValue {
                    value,
                    unit: "°F".to_string(),
                    quality: "set".to_string(),
                },
            );
            
            let snapshot = SensorSnapshot {
                timestamp: Utc::now(),
                source: "set_command".to_string(),
                user: None, // TODO: Get from SSH session
                readings,
            };
            
            self.storage.write_snapshot(&snapshot, true)?;
        }
        
        Ok(format!("Temperature setpoint set to {}°F", value))
    }

    /// Get all sensor readings
    pub async fn get_sensors(&self) -> Result<Vec<SensorResult>> {
        let sensor_list = self.hardware.list_sensors().await?;
        let mut results = Vec::new();
        
        for sensor_id in sensor_list {
            // Parse sensor ID (format: "location:sensor_type")
            let parts: Vec<&str> = sensor_id.split(':').collect();
            if parts.len() >= 2 {
                let location = parts[..parts.len()-1].join(":");
                let sensor_type = parts[parts.len()-1];
                
                if let Ok(reading) = self.hardware.read_sensor(&location, sensor_type).await {
                    results.push(SensorResult {
                        location: location.clone(),
                        sensor_type: sensor_type.to_string(),
                        value: reading.value,
                        unit: reading.unit,
                        timestamp: reading.timestamp,
                        source: "realtime".to_string(),
                    });
                }
            }
        }
        
        Ok(results)
    }

    /// Get historical sensor data
    async fn get_historical(
        &self,
        location: &str,
        sensor_type: &str,
        options: QueryOptions,
    ) -> Result<SensorResult> {
        // Determine time range
        let (from, to) = if let (Some(from), Some(to)) = (options.from, options.to) {
            (from, to)
        } else if let Some(duration) = options.duration {
            (Utc::now() - duration, Utc::now())
        } else {
            // Default to last 24 hours
            (Utc::now() - Duration::hours(24), Utc::now())
        };
        
        // Read snapshots from Git
        let snapshots = self.storage.read_snapshots(from, to)?;
        
        // Extract readings for this location/sensor
        let sensor_key = format!("{}:{}", location, sensor_type);
        let mut values = Vec::new();
        
        for snapshot in snapshots {
            if let Some(reading) = snapshot.readings.get(&sensor_key) {
                values.push((snapshot.timestamp, reading.value));
            }
        }
        
        if values.is_empty() {
            anyhow::bail!("No historical data found for {}", sensor_key);
        }
        
        // Return average (or latest, depending on use case)
        let avg_value = values.iter().map(|(_, v)| v).sum::<f64>() / values.len() as f64;
        let latest_timestamp = values.iter().map(|(t, _)| t).max().unwrap();
        
        Ok(SensorResult {
            location: location.to_string(),
            sensor_type: sensor_type.to_string(),
            value: avg_value,
            unit: "°F".to_string(), // TODO: Get from snapshot
            timestamp: *latest_timestamp,
            source: "historical".to_string(),
        })
    }

    /// Log a sensor reading to Git
    async fn log_reading(
        &self,
        location: &str,
        sensor_type: &str,
        reading: &HwReading,
    ) -> Result<()> {
        let mut readings = HashMap::new();
        readings.insert(
            format!("{}:{}", location, sensor_type),
            SensorValue {
                value: reading.value,
                unit: reading.unit.clone(),
                quality: format!("{:?}", reading.quality),
            },
        );
        
        let snapshot = SensorSnapshot {
            timestamp: reading.timestamp,
            source: "realtime_query".to_string(),
            user: None, // TODO: Get from SSH session
            readings,
        };
        
        self.storage.write_snapshot(&snapshot, true)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_sensor_commands() {
        let temp = TempDir::new().unwrap();
        let hardware = Arc::new(HardwareManager::new());
        let commands = SensorCommands::new(hardware, temp.path().to_path_buf());

        // Test get_temp (will use placeholder hardware)
        let result = commands.get_temp("floor:2:room:201", QueryOptions::default()).await;
        assert!(result.is_ok());
    }
}
