//! Hardware traits for sensor operations

use embedded_hal::digital::v2::InputPin;
use embedded_hal::adc::OneShot;
use crate::error::HardwareError;
use crate::sensor::{SensorData, SensorConfig};

/// Trait for sensor reading operations
pub trait ReadSensor {
    type Error;
    
    /// Read sensor data
    fn read(&mut self) -> Result<SensorData, Self::Error>;
    
    /// Check if sensor is ready
    fn is_ready(&self) -> bool;
}

/// Trait for sensor configuration
pub trait ConfigureSensor {
    type Error;
    
    /// Configure sensor
    fn configure(&mut self, config: &SensorConfig) -> Result<(), Self::Error>;
    
    /// Get current configuration
    fn get_config(&self) -> Result<SensorConfig, Self::Error>;
}

/// Trait for data transmission
pub trait SendData {
    type Error;
    
    /// Send sensor data
    fn send(&mut self, data: &SensorData) -> Result<(), Self::Error>;
    
    /// Check if transmission is available
    fn is_available(&self) -> bool;
}

/// Trait for sensor calibration
pub trait CalibrateSensor {
    type Error;
    
    /// Calibrate sensor
    fn calibrate(&mut self) -> Result<(), Self::Error>;
    
    /// Get calibration status
    fn get_calibration_status(&self) -> Result<bool, Self::Error>;
}
