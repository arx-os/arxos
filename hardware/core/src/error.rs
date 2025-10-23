//! Error types for hardware integration

use thiserror::Error;

/// Hardware error types
#[derive(Error, Debug)]
pub enum HardwareError {
    #[error("Sensor read error: {0}")]
    SensorRead(String),
    
    #[error("Communication error: {0}")]
    Communication(String),
    
    #[error("Configuration error: {0}")]
    Configuration(String),
    
    #[error("Data validation error: {0}")]
    DataValidation(String),
    
    #[error("Timeout error: {0}")]
    Timeout(String),
    
    #[error("Hardware initialization error: {0}")]
    Initialization(String),
}

/// Result type alias
pub type Result<T> = std::result::Result<T, HardwareError>;
