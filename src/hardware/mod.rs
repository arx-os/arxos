//! Hardware integration module for ArxOS
//! 
//! This module provides integration between hardware sensors and the ArxOS building data system.
//! It handles sensor data ingestion, normalization, and equipment status updates.

mod ingestion;
mod data_types;
mod status_updater;

pub use ingestion::{SensorIngestionService, SensorIngestionConfig};
pub use data_types::{SensorData, SensorType, EquipmentSensorMapping, SensorMetadata, SensorDataValues};
pub use status_updater::{EquipmentStatusUpdater, UpdateResult};

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

