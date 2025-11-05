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

impl std::fmt::Display for RoomType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RoomType::Classroom => write!(f, "Classroom"),
            RoomType::Laboratory => write!(f, "Laboratory"),
            RoomType::Office => write!(f, "Office"),
            RoomType::Gymnasium => write!(f, "Gymnasium"),
            RoomType::Cafeteria => write!(f, "Cafeteria"),
            RoomType::Library => write!(f, "Library"),
            RoomType::Auditorium => write!(f, "Auditorium"),
            RoomType::Hallway => write!(f, "Hallway"),
            RoomType::Restroom => write!(f, "Restroom"),
            RoomType::Storage => write!(f, "Storage"),
            RoomType::Mechanical => write!(f, "Mechanical"),
            RoomType::Electrical => write!(f, "Electrical"),
            RoomType::Other(name) => write!(f, "{}", name),
        }
    }
}

impl std::str::FromStr for RoomType {
    type Err = std::convert::Infallible;
    
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(match s {
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
        })
    }
}

impl RoomType {
    /// Convert to string (for backward compatibility)
    /// 
    /// **Note:** Prefer using `Display` trait (`format!("{}", room_type)`) instead.
    #[deprecated(note = "Use Display trait instead: format!(\"{}\", room_type)")]
    pub fn to_string(&self) -> String {
        format!("{}", self)
    }
    
    /// Parse from string (for backward compatibility)
    /// 
    /// **Note:** Prefer using `FromStr` trait (`room_type.parse()`) instead.
    #[deprecated(note = "Use FromStr trait instead: room_type.parse()")]
    pub fn from_string(s: &str) -> Self {
        s.parse().unwrap_or_else(|_| RoomType::Other(s.to_string()))
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

