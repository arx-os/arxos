//! Hardware configuration

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareConfig {
    pub bacnet: Option<BacnetConfig>,
    pub modbus: Option<ModbusConfig>,
    pub mqtt: Option<MqttConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacnetConfig {
    pub host: String,
    pub port: u16,
    pub device_id: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModbusConfig {
    pub host: String,
    pub port: u16,
    pub slave_id: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MqttConfig {
    pub broker: String,
    pub port: u16,
    pub client_id: String,
    pub username: Option<String>,
    pub password: Option<String>,
}

impl Default for HardwareConfig {
    fn default() -> Self {
        Self {
            bacnet: None,
            modbus: None,
            mqtt: None,
        }
    }
}
