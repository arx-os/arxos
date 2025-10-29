//! Equipment data structure and implementation

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::collections::HashMap;
use super::types::Position;

/// Represents equipment in a building
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Equipment {
    pub id: String,
    pub name: String,
    pub path: String,
    pub equipment_type: EquipmentType,
    pub position: Position,
    pub properties: HashMap<String, String>,
    pub status: EquipmentStatus,
    pub room_id: Option<String>, // Reference to parent room
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

impl Equipment {
    pub fn new(name: String, path: String, equipment_type: EquipmentType) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            path,
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

