use serde::{Deserialize, Serialize};
use serde_yaml::Value;
use std::collections::HashMap;

/// Supported sensor modalities.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SensorType {
    Temperature,
    Humidity,
    AirQuality,
    Motion,
    Light,
    Pressure,
    Voltage,
    Current,
    Other(String),
}

/// Result of comparing a reading against configured thresholds.
#[derive(Debug, Clone, PartialEq)]
pub enum ThresholdCheck {
    Normal,
    OutOfRange,
    Critical,
}

/// Mapping between a building equipment asset and an external sensor.
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
    /// Evaluate a raw value against the configured thresholds with basic guards.
    pub fn check_thresholds(&self, value: f64) -> ThresholdCheck {
        match (self.threshold_min, self.threshold_max) {
            (Some(min), Some(max)) if value < min || value > max => ThresholdCheck::OutOfRange,
            (Some(min), None) if value < min => ThresholdCheck::OutOfRange,
            (None, Some(max)) if value > max => ThresholdCheck::OutOfRange,
            _ => ThresholdCheck::Normal,
        }
    }
}

/// Serialized sensor payload produced by field devices.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorData {
    pub api_version: String,
    pub kind: String,
    pub metadata: SensorMetadata,
    pub data: SensorDataValues,
    pub alerts: Vec<SensorAlert>,
    pub arxos: Option<ArxosMetadata>,
}

/// Metadata describing a single sensor reading.
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
    pub extra: HashMap<String, Value>,
}

/// Arbitrary value bag associated with a reading.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorDataValues {
    #[serde(flatten)]
    pub values: HashMap<String, Value>,
}

/// Alert emitted by the originating sensor.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorAlert {
    pub level: String,
    pub message: String,
    pub timestamp: String,
}

/// Processing metadata populated by ArxOS once the reading has been ingested.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArxosMetadata {
    pub processed: bool,
    pub validated: bool,
    pub device_id: String,
}
