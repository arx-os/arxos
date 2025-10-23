//! Sensor abstractions and types

use serde::{Deserialize, Serialize};
use crate::error::HardwareError;

/// Sensor data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorData {
    pub sensor_id: String,
    pub sensor_type: String,
    pub room_path: String,
    pub timestamp: String,
    pub source: String,
    pub building_id: String,
    pub value: f32,
    pub unit: String,
    pub status: String,
    pub confidence: f32,
}

impl SensorData {
    pub fn new(
        sensor_id: String,
        sensor_type: String,
        room_path: String,
        value: f32,
        unit: String,
    ) -> Self {
        Self {
            sensor_id,
            sensor_type,
            room_path,
            timestamp: get_current_timestamp(),
            source: "hardware".to_string(),
            building_id: "B1".to_string(),
            value,
            unit,
            status: "normal".to_string(),
            confidence: 0.95,
        }
    }
}

/// Sensor configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorConfig {
    pub sensor_id: String,
    pub sensor_type: String,
    pub room_path: String,
    pub building_id: String,
    pub update_interval_ms: u32,
    pub alert_thresholds: AlertThresholds,
}

/// Alert thresholds
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertThresholds {
    pub warning_min: f32,
    pub warning_max: f32,
    pub critical_min: f32,
    pub critical_max: f32,
}

impl Default for AlertThresholds {
    fn default() -> Self {
        Self {
            warning_min: 0.0,
            warning_max: 100.0,
            critical_min: -10.0,
            critical_max: 110.0,
        }
    }
}

fn get_current_timestamp() -> String {
    // Real timestamp generation using chrono
    chrono::Utc::now().to_rfc3339()
}
