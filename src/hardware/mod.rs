//! Hardware interface layer for building control systems
//! 
//! Provides abstract interfaces for various building automation protocols:
//! - BACnet (HVAC, lighting, access control)
//! - Modbus (sensors, meters)
//! - MQTT (IoT devices)

use anyhow::Result;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[cfg(feature = "agent")]
pub mod bacnet;
#[cfg(feature = "agent")]
pub mod modbus;
#[cfg(feature = "agent")]
pub mod mqtt;
#[cfg(feature = "agent")]
pub mod config;

/// Sensor reading with timestamp
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorReading {
    pub value: f64,
    pub unit: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub quality: ReadingQuality,
}

/// Quality indicator for sensor readings
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum ReadingQuality {
    Good,
    Uncertain,
    Bad,
}

/// Generic hardware interface trait
#[async_trait]
pub trait HardwareInterface: Send + Sync {
    /// Read a sensor value
    async fn read_sensor(&self, location: &str, sensor_type: &str) -> Result<SensorReading>;
    
    /// Write a control value
    async fn write_control(&self, location: &str, control_type: &str, value: f64) -> Result<()>;
    
    /// Get all available sensors
    async fn list_sensors(&self) -> Result<Vec<String>>;
    
    /// Check if the interface is connected
    async fn is_connected(&self) -> bool;
    
    /// Connect to the hardware
    async fn connect(&mut self) -> Result<()>;
    
    /// Disconnect from the hardware
    async fn disconnect(&mut self) -> Result<()>;
}

/// Hardware protocol enum for static dispatch
pub enum HardwareProtocol {
    #[cfg(feature = "agent")]
    Bacnet(bacnet::BacnetInterface),
    #[cfg(feature = "agent")]
    Modbus(modbus::ModbusInterface),
    #[cfg(feature = "agent")]
    Mqtt(mqtt::MqttInterface),
}

impl HardwareProtocol {
    pub async fn read_sensor(&self, location: &str, sensor_type: &str) -> Result<SensorReading> {
        match self {
            #[cfg(feature = "agent")]
            Self::Bacnet(i) => i.read_sensor(location, sensor_type).await,
            #[cfg(feature = "agent")]
            Self::Modbus(i) => i.read_sensor(location, sensor_type).await,
            #[cfg(feature = "agent")]
            Self::Mqtt(i) => i.read_sensor(location, sensor_type).await,
            #[cfg(not(feature = "agent"))]
            _ => anyhow::bail!("Agent feature disabled"),
        }
    }

    pub async fn write_control(&self, location: &str, control_type: &str, value: f64) -> Result<()> {
        match self {
            #[cfg(feature = "agent")]
            Self::Bacnet(i) => i.write_control(location, control_type, value).await,
            #[cfg(feature = "agent")]
            Self::Modbus(i) => i.write_control(location, control_type, value).await,
            #[cfg(feature = "agent")]
            Self::Mqtt(i) => i.write_control(location, control_type, value).await,
            #[cfg(not(feature = "agent"))]
            _ => anyhow::bail!("Agent feature disabled"),
        }
    }

    pub async fn is_connected(&self) -> bool {
        match self {
            #[cfg(feature = "agent")]
            Self::Bacnet(i) => i.is_connected().await,
            #[cfg(feature = "agent")]
            Self::Modbus(i) => i.is_connected().await,
            #[cfg(feature = "agent")]
            Self::Mqtt(i) => i.is_connected().await,
            #[cfg(not(feature = "agent"))]
            _ => false,
        }
    }

    pub async fn list_sensors(&self) -> Result<Vec<String>> {
         match self {
            #[cfg(feature = "agent")]
            Self::Bacnet(i) => i.list_sensors().await,
            #[cfg(feature = "agent")]
            Self::Modbus(i) => i.list_sensors().await,
            #[cfg(feature = "agent")]
            Self::Mqtt(i) => i.list_sensors().await,
            #[cfg(not(feature = "agent"))]
            _ => Ok(vec![]),
        }
    }
}

/// Hardware manager that aggregates multiple interfaces
pub struct HardwareManager {
    interfaces: HashMap<String, HardwareProtocol>,
}

impl HardwareManager {
    pub fn new() -> Self {
        Self {
            interfaces: HashMap::new(),
        }
    }
    
    pub fn add_interface(&mut self, name: String, interface: HardwareProtocol) {
        self.interfaces.insert(name, interface);
    }
    
    pub async fn read_sensor(&self, location: &str, sensor_type: &str) -> Result<SensorReading> {
        // Try each interface until one succeeds
        for (name, interface) in &self.interfaces {
            if interface.is_connected().await {
                match interface.read_sensor(location, sensor_type).await {
                    Ok(reading) => return Ok(reading),
                    Err(e) => {
                        tracing::warn!("Interface {} failed to read sensor: {}", name, e);
                        continue;
                    }
                }
            }
        }
        
        anyhow::bail!("No interface could read sensor at {}", location)
    }
    
    pub async fn write_control(&self, location: &str, control_type: &str, value: f64) -> Result<()> {
        // Try each interface until one succeeds
        for (name, interface) in &self.interfaces {
            if interface.is_connected().await {
                match interface.write_control(location, control_type, value).await {
                    Ok(()) => return Ok(()),
                    Err(e) => {
                        tracing::warn!("Interface {} failed to write control: {}", name, e);
                        continue;
                    }
                }
            }
        }
        
        anyhow::bail!("No interface could write control at {}", location)
    }

    pub async fn list_sensors(&self) -> Result<Vec<String>> {
        let mut all_sensors = Vec::new();
        for interface in self.interfaces.values() {
            // We ignore errors from individual interfaces and just return what we found
            if let Ok(sensors) = interface.list_sensors().await {
                all_sensors.extend(sensors);
            }
        }
        Ok(all_sensors)
    }
}

impl Default for HardwareManager {
    fn default() -> Self {
        Self::new()
    }
}
