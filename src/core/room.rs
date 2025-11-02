//! Room data structure and implementation

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use super::{Equipment, SpatialProperties};

/// Represents a room in a building
///
/// Rooms are containers for equipment within wings on floors.
///
/// # Fields
///
/// * `id` - Unique identifier (UUID)
/// * `name` - Human-readable room name
/// * `room_type` - Type categorization
/// * `equipment` - Collection of equipment in the room
/// * `spatial_properties` - Position, dimensions, and bounding box
/// * `properties` - Key-value metadata
/// * `created_at` - Creation timestamp
/// * `updated_at` - Last modification timestamp
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Room {
    /// Unique identifier for the room
    pub id: String,
    /// Human-readable room name
    pub name: String,
    /// Type categorization of the room
    pub room_type: RoomType,
    /// Collection of equipment in the room
    pub equipment: Vec<Equipment>,
    /// Position, dimensions, and bounding box
    pub spatial_properties: SpatialProperties,
    /// Key-value metadata
    pub properties: HashMap<String, String>,
    /// Creation timestamp
    pub created_at: DateTime<Utc>,
    /// Last modification timestamp
    pub updated_at: DateTime<Utc>,
}

/// Types of rooms in a building
#[derive(Debug, Clone, Serialize, Deserialize)]
#[derive(Default)]
pub enum RoomType {
    Classroom,
    Laboratory,
    #[default]
    Office,
    Gymnasium,
    Cafeteria,
    Library,
    Auditorium,
    Hallway,
    Restroom,
    Storage,
    Mechanical,
    Electrical,
    Other(String),
}

impl RoomType {
    pub fn to_string(&self) -> String {
        match self {
            RoomType::Classroom => "Classroom".to_string(),
            RoomType::Laboratory => "Laboratory".to_string(),
            RoomType::Office => "Office".to_string(),
            RoomType::Gymnasium => "Gymnasium".to_string(),
            RoomType::Cafeteria => "Cafeteria".to_string(),
            RoomType::Library => "Library".to_string(),
            RoomType::Auditorium => "Auditorium".to_string(),
            RoomType::Hallway => "Hallway".to_string(),
            RoomType::Restroom => "Restroom".to_string(),
            RoomType::Storage => "Storage".to_string(),
            RoomType::Mechanical => "Mechanical".to_string(),
            RoomType::Electrical => "Electrical".to_string(),
            RoomType::Other(name) => name.clone(),
        }
    }
    
    pub fn from_string(s: &str) -> Self {
        match s {
            "Classroom" => RoomType::Classroom,
            "Laboratory" => RoomType::Laboratory,
            "Office" => RoomType::Office,
            "Gymnasium" => RoomType::Gymnasium,
            "Cafeteria" => RoomType::Cafeteria,
            "Library" => RoomType::Library,
            "Auditorium" => RoomType::Auditorium,
            "Hallway" => RoomType::Hallway,
            "Restroom" => RoomType::Restroom,
            "Storage" => RoomType::Storage,
            "Mechanical" => RoomType::Mechanical,
            "Electrical" => RoomType::Electrical,
            _ => RoomType::Other(s.to_string()),
        }
    }
}


impl Room {
    pub fn new(name: String, room_type: RoomType) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            room_type,
            equipment: Vec::new(),
            spatial_properties: SpatialProperties::default(),
            properties: HashMap::new(),
            created_at: now,
            updated_at: now,
        }
    }
    
    /// Add equipment to the room
    pub fn add_equipment(&mut self, equipment: Equipment) {
        self.equipment.push(equipment);
        self.updated_at = Utc::now();
    }
    
    /// Find equipment by name
    pub fn find_equipment(&self, name: &str) -> Option<&Equipment> {
        self.equipment.iter().find(|e| e.name == name)
    }
    
    /// Find equipment by name (mutable)
    pub fn find_equipment_mut(&mut self, name: &str) -> Option<&mut Equipment> {
        self.equipment.iter_mut().find(|e| e.name == name)
    }
    
    /// Update spatial properties
    pub fn update_spatial_properties(&mut self, spatial_properties: SpatialProperties) {
        self.spatial_properties = spatial_properties;
        self.updated_at = Utc::now();
    }
}

