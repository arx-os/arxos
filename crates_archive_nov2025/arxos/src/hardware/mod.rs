//! Hardware integration module for ArxOS
//!
//! This module provides integration between hardware sensors and the ArxOS building data system.
//! It handles sensor data ingestion, normalization, and equipment status updates.

mod alert;
mod ingestion;
mod mapping;
mod status_updater;

#[cfg(feature = "async-sensors")]
mod http_server;
#[cfg(feature = "async-sensors")]
mod mqtt_client;
#[cfg(feature = "async-sensors")]
mod websocket_server;

pub use alert::AlertGenerator;
pub use arx::depin::{
    ArxosMetadata, EquipmentSensorMapping, SensorAlert, SensorData, SensorDataValues,
    SensorMetadata, SensorType, ThresholdCheck,
};
pub use ingestion::{SensorIngestionConfig, SensorIngestionService};
pub use mapping::MappingManager;
pub use status_updater::{EquipmentStatusUpdater, UpdateResult};

#[cfg(feature = "async-sensors")]
pub use http_server::{start_sensor_http_server, SensorHttpService};
#[cfg(feature = "async-sensors")]
pub use mqtt_client::{start_mqtt_subscriber, MqttClientConfig, MqttSensorClient};
#[cfg(feature = "async-sensors")]
pub use websocket_server::{start_websocket_server, WebSocketSensorServer};

// Hardware integration types exported from this module

/// Equipment sensor mapping configuration (legacy type)
#[derive(Debug, Clone)]
pub struct EquipmentUpdate {
    pub equipment_id: String,
    pub sensor_readings: Vec<String>, // Sensor IDs
    pub inferred_status: String,
}

/// Hardware integration error types
#[derive(Debug, thiserror::Error)]
pub enum HardwareError {
    #[error("Sensor data file not found: {path}")]
    FileNotFound { path: String },

    #[error("Invalid sensor data format: {reason}")]
    InvalidFormat { reason: String },

    #[error("Failed to map sensor to equipment: {reason}")]
    MappingError { reason: String },

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("YAML serialization error: {0}")]
    YamlError(#[from] serde_yaml::Error),

    #[error("JSON serialization error: {0}")]
    JsonError(#[from] serde_json::Error),
}

pub type HardwareResult<T> = Result<T, HardwareError>;
