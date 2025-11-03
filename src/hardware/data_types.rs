//! Data types for hardware integration

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Sensor type enumeration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SensorType {
    Temperature,
    Humidity,
    AirQuality,
    Motion,
    Light,
    Pressure,
    Other(String),
}

/// Equipment-sensor mapping
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquipmentSensorMapping {
    pub equipment_id: String,
    pub sensor_id: String,
    pub sensor_type: SensorType,
    pub threshold_min: Option<f64>,
    pub threshold_max: Option<f64>,
    pub alert_on_out_of_range: bool,
}

impl EquipmentSensorMapping {
    pub fn check_thresholds(&self, value: f64) -> ThresholdCheck {
        match (self.threshold_min, self.threshold_max) {
            (Some(min), Some(max)) if value < min || value > max => ThresholdCheck::OutOfRange,
            (Some(min), None) if value < min => ThresholdCheck::OutOfRange,
            (None, Some(max)) if value > max => ThresholdCheck::OutOfRange,
            _ => ThresholdCheck::Normal,
        }
    }
}

/// Threshold check result
#[derive(Debug, Clone, PartialEq)]
pub enum ThresholdCheck {
    Normal,
    OutOfRange,
    Critical,
}

/// Sensor data container
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorData {
    pub api_version: String,
    pub kind: String,
    pub metadata: SensorMetadata,
    pub data: SensorDataValues,
    pub alerts: Vec<SensorAlert>,
    pub arxos: Option<ArxosMetadata>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorMetadata {
    pub sensor_id: String,
    pub sensor_type: String,
    pub room_path: Option<String>,
    pub timestamp: String,
    pub source: String,
    pub building_id: Option<String>,
    pub equipment_id: Option<String>,
    #[serde(flatten)]
    pub extra: HashMap<String, serde_yaml::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorDataValues {
    #[serde(flatten)]
    pub values: HashMap<String, serde_yaml::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorAlert {
    pub level: String,
    pub message: String,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArxosMetadata {
    pub processed: bool,
    pub validated: bool,
    pub device_id: String,
}

