//! Equipment data structure and implementation

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::collections::HashMap;
use super::types::Position;
use crate::domain::ArxAddress;

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
/// * `status` - Operational status
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
    /// Operational status
    pub status: EquipmentStatus,
    /// Reference to parent room (if assigned)
    pub room_id: Option<String>,
}

/// Types of equipment
#[derive(Debug, Clone, Serialize, Deserialize)]
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

/// Status of equipment
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EquipmentStatus {
    Active,
    Inactive,
    Maintenance,
    OutOfOrder,
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
            room_id: None,
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
            room_id: None,
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
}

