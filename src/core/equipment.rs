//! Equipment data structure and implementation

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::collections::HashMap;
use super::types::Position;
use crate::domain::ArxAddress;

/// Sensor mapping structure for equipment
///
/// Maps sensors to equipment with threshold configurations.
/// This is a YAML-only field that is preserved during serialization.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SensorMapping {
    /// Unique identifier for the sensor
    pub sensor_id: String,
    /// Type of sensor (e.g., "temperature", "humidity", "pressure")
    pub sensor_type: String,
    /// Threshold configurations for this sensor
    pub thresholds: HashMap<String, ThresholdConfig>,
}

/// Threshold configuration for sensor values
///
/// Defines min/max values and warning/critical thresholds for sensor readings.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ThresholdConfig {
    /// Minimum acceptable value
    pub min: Option<f64>,
    /// Maximum acceptable value
    pub max: Option<f64>,
    /// Minimum value for warning state
    pub warning_min: Option<f64>,
    /// Maximum value for warning state
    pub warning_max: Option<f64>,
    /// Minimum value for critical state
    pub critical_min: Option<f64>,
    /// Maximum value for critical state
    pub critical_max: Option<f64>,
}

/// Represents equipment in a building
///
/// Equipment is the leaf entity in the ArxOS hierarchy:
/// Building → Floor → Wing → Room → **Equipment**
///
/// # Fields
///
/// * `id` - Unique identifier (UUID)
/// * `name` - Human-readable equipment name
/// * `path` - Universal path identifier
/// * `equipment_type` - Type categorization
/// * `position` - 3D spatial position with coordinate system
/// * `properties` - Key-value metadata
/// * `status` - Operational status (Active, Inactive, Maintenance, OutOfOrder)
/// * `health_status` - Health status (Healthy, Warning, Critical) - optional for backward compatibility
/// * `room_id` - Reference to parent room (if assigned)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Equipment {
    /// Unique identifier for the equipment
    pub id: String,
    /// Human-readable equipment name
    pub name: String,
    /// Universal path identifier (legacy, kept for backward compatibility)
    pub path: String,
    /// ArxOS Address (new hierarchical addressing system)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub address: Option<ArxAddress>,
    /// Type categorization of the equipment
    pub equipment_type: EquipmentType,
    /// 3D spatial position with coordinate system
    pub position: Position,
    /// Key-value metadata
    pub properties: HashMap<String, String>,
    /// Operational status (whether equipment is running/active)
    pub status: EquipmentStatus,
    /// Health status (equipment condition/health) - optional for backward compatibility
    ///
    /// When serializing to YAML, this field is serialized as "status" for backward compatibility.
    /// When deserializing from YAML, the "status" field is mapped to health_status if present.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub health_status: Option<EquipmentHealthStatus>,
    /// Reference to parent room (if assigned)
    pub room_id: Option<String>,
    /// Sensor mappings for this equipment (YAML-only field)
    ///
    /// Maps sensors to equipment with threshold configurations.
    /// This field is optional and omitted from YAML when None.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sensor_mappings: Option<Vec<SensorMapping>>,
}

/// Types of equipment
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum EquipmentType {
    HVAC,
    Electrical,
    AV,
    Furniture,
    Safety,
    Plumbing,
    Network,
    Other(String),
}

/// Operational status of equipment
///
/// This represents whether the equipment is running, stopped, in maintenance, etc.
/// This is separate from health status, which represents the equipment's condition.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum EquipmentStatus {
    /// Equipment is active and running
    Active,
    /// Equipment is inactive (not running, but functional)
    Inactive,
    /// Equipment is in maintenance mode
    Maintenance,
    /// Equipment is out of order (broken/disabled)
    OutOfOrder,
    /// Status is unknown
    Unknown,
}

/// Health status of equipment
///
/// This represents the equipment's condition/health, separate from operational status.
/// Equipment can be operationally active but have a health warning (e.g., running but needs maintenance).
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum EquipmentHealthStatus {
    /// Equipment is healthy and functioning correctly
    Healthy,
    /// Equipment has a warning condition (needs attention)
    Warning,
    /// Equipment has a critical issue
    Critical,
    /// Health status is unknown
    Unknown,
}

impl Default for Equipment {
    fn default() -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name: "Unnamed Equipment".to_string(),
            path: "/".to_string(),
            address: None,
            equipment_type: EquipmentType::Other("Unknown".to_string()),
            position: Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            },
            properties: HashMap::new(),
            status: EquipmentStatus::Unknown,
            health_status: None,
            room_id: None,
            sensor_mappings: None,
        }
    }
}

impl Equipment {
    pub fn new(name: String, path: String, equipment_type: EquipmentType) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            path,
            address: None,
            equipment_type,
            position: Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            },
            properties: HashMap::new(),
            status: EquipmentStatus::Active,
            health_status: None,
            room_id: None,
            sensor_mappings: None,
        }
    }
    
    /// Set the position of the equipment
    pub fn set_position(&mut self, position: Position) {
        self.position = position;
    }
    
    /// Set the room this equipment belongs to
    pub fn set_room(&mut self, room_id: String) {
        self.room_id = Some(room_id);
    }
    
    /// Add a property to the equipment
    pub fn add_property(&mut self, key: String, value: String) {
        self.properties.insert(key, value);
    }
    
    /// Get system type from equipment type
    ///
    /// This computes the system_type string from the equipment_type enum.
    /// Used during serialization to add system_type field to YAML output.
    pub fn system_type(&self) -> String {
        match &self.equipment_type {
            EquipmentType::HVAC => "HVAC",
            EquipmentType::Electrical => "ELECTRICAL",
            EquipmentType::Plumbing => "PLUMBING",
            EquipmentType::Safety => "SAFETY",
            EquipmentType::Network => "NETWORK",
            EquipmentType::AV => "AV",
            EquipmentType::Furniture => "FURNITURE",
            EquipmentType::Other(_) => "OTHER",
        }.to_string()
    }
}

impl EquipmentType {
    /// Get system type string from equipment type
    ///
    /// This is a helper function to convert EquipmentType to system_type string.
    pub fn to_system_type(&self) -> String {
        match self {
            EquipmentType::HVAC => "HVAC",
            EquipmentType::Electrical => "ELECTRICAL",
            EquipmentType::Plumbing => "PLUMBING",
            EquipmentType::Safety => "SAFETY",
            EquipmentType::Network => "NETWORK",
            EquipmentType::AV => "AV",
            EquipmentType::Furniture => "FURNITURE",
            EquipmentType::Other(_) => "OTHER",
        }.to_string()
    }
}

