//! Data structures for hardware integration

use serde::{Deserialize, Serialize};

/// ArxOS data format
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArxOSData {
    pub api_version: String,
    pub kind: String,
    pub metadata: Metadata,
    pub data: Data,
    pub alerts: Vec<Alert>,
    pub arxos: ArxOS,
}

/// Metadata structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metadata {
    pub sensor_id: String,
    pub sensor_type: String,
    pub room_path: String,
    pub timestamp: String,
    pub source: String,
    pub building_id: String,
}

/// Data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Data {
    pub value: f32,
    pub unit: String,
    pub status: String,
    pub confidence: f32,
}

/// Alert structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub level: String,
    pub message: String,
    pub timestamp: String,
}

/// ArxOS metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArxOS {
    pub processed: bool,
    pub validated: bool,
    pub device_id: String,
}
