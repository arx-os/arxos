//! Equipment data structure and implementation

use super::types::Position;
use crate::core::domain::ArxAddress;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;
use uuid::Uuid;

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
    /// Optional mesh geometry
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mesh: Option<crate::core::spatial::mesh::Mesh>,
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
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Hash)]
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
            mesh: None,
            properties: HashMap::new(),
            status: EquipmentStatus::Unknown,
            health_status: None,
            room_id: None,
            sensor_mappings: None,
        }
    }
}

impl Equipment {
    /// Create new equipment with a unique ID and default values
    ///
    /// The equipment is initialized with:
    /// - A unique UUID
    /// - Default position (0, 0, 0) in "building_local" coordinate system
    /// - Active operational status
    /// - Empty properties map
    /// - No room assignment
    ///
    /// # Arguments
    ///
    /// * `name` - Human-readable equipment name
    /// * `path` - Universal path identifier (legacy)
    /// * `equipment_type` - Type categorization
    ///
    /// # Returns
    ///
    /// A new Equipment instance with default values
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Equipment, EquipmentType};
    /// let equipment = Equipment::new(
    ///     "Chiller-01".to_string(),
    ///     "/building/mechanical/chiller-01".to_string(),
    ///     EquipmentType::HVAC,
    /// );
    /// assert_eq!(equipment.name, "Chiller-01");
    /// assert_eq!(equipment.equipment_type, EquipmentType::HVAC);
    /// ```
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
            mesh: None,
            properties: HashMap::new(),
            status: EquipmentStatus::Active,
            health_status: None,
            room_id: None,
            sensor_mappings: None,
        }
    }

    /// Set the 3D spatial position of the equipment
    ///
    /// # Arguments
    ///
    /// * `position` - The new position with coordinates and coordinate system
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Equipment, EquipmentType, Position};
    /// let mut equipment = Equipment::new(
    ///     "Chiller-01".to_string(),
    ///     "/chiller".to_string(),
    ///     EquipmentType::HVAC,
    /// );
    /// equipment.set_position(Position {
    ///     x: 100.0,
    ///     y: 200.0,
    ///     z: 10.0,
    ///     coordinate_system: "world".to_string(),
    /// });
    /// assert_eq!(equipment.position.x, 100.0);
    /// ```
    pub fn set_position(&mut self, position: Position) {
        self.position = position;
    }

    /// Assign this equipment to a room
    ///
    /// # Arguments
    ///
    /// * `room_id` - The unique identifier of the parent room
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Equipment, EquipmentType};
    /// let mut equipment = Equipment::new(
    ///     "Chiller-01".to_string(),
    ///     "/chiller".to_string(),
    ///     EquipmentType::HVAC,
    /// );
    /// equipment.set_room("room-123".to_string());
    /// assert_eq!(equipment.room_id, Some("room-123".to_string()));
    /// ```
    pub fn set_room(&mut self, room_id: String) {
        self.room_id = Some(room_id);
    }

    /// Add a custom property to the equipment metadata
    ///
    /// Properties are stored as key-value pairs and can represent
    /// any equipment-specific metadata (manufacturer, model, serial number, etc.)
    ///
    /// # Arguments
    ///
    /// * `key` - Property name
    /// * `value` - Property value
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Equipment, EquipmentType};
    /// let mut equipment = Equipment::new(
    ///     "Chiller-01".to_string(),
    ///     "/chiller".to_string(),
    ///     EquipmentType::HVAC,
    /// );
    /// equipment.add_property("manufacturer".to_string(), "Carrier".to_string());
    /// equipment.add_property("model".to_string(), "30XA".to_string());
    /// assert_eq!(equipment.properties.get("manufacturer"), Some(&"Carrier".to_string()));
    /// ```
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
        }
        .to_string()
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
        }
        .to_string()
    }
}

impl fmt::Display for EquipmentType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EquipmentType::HVAC => write!(f, "HVAC"),
            EquipmentType::Electrical => write!(f, "Electrical"),
            EquipmentType::AV => write!(f, "AV"),
            EquipmentType::Furniture => write!(f, "Furniture"),
            EquipmentType::Safety => write!(f, "Safety"),
            EquipmentType::Plumbing => write!(f, "Plumbing"),
            EquipmentType::Network => write!(f, "Network"),
            EquipmentType::Other(name) => write!(f, "{name}"),
        }
    }
}

impl fmt::Display for EquipmentStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EquipmentStatus::Active => write!(f, "Active"),
            EquipmentStatus::Inactive => write!(f, "Inactive"),
            EquipmentStatus::Maintenance => write!(f, "Maintenance"),
            EquipmentStatus::OutOfOrder => write!(f, "Out of Order"),
            EquipmentStatus::Unknown => write!(f, "Unknown"),
        }
    }
}
