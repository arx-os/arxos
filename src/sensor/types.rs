//! Sensor data types

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;
use crate::core::spatial::Point3D;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorReading {
    pub sensor_id: Uuid,
    pub timestamp: i64,
    pub value: f64,
    pub unit: String,
    pub location: Option<Point3D>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorConfig {
    pub id: Uuid,
    pub name: String,
    pub sensor_type: String,
    pub location: Point3D,
    pub properties: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorBatch {
    pub readings: Vec<SensorReading>,
    pub batch_id: Uuid,
    pub received_at: i64,
}