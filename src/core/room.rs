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
/// * `created_at` - Creation timestamp (optional, omitted from YAML)
/// * `updated_at` - Last modification timestamp (optional, omitted from YAML)
#[derive(Debug, Clone)]
pub struct Room {
    /// Unique identifier for the room
    pub id: String,
    /// Human-readable room name
    pub name: String,
    /// Type categorization of the room
    pub room_type: RoomType,
    /// Collection of equipment in the room
    ///
    /// When serializing to YAML, this serializes as Vec<String> (equipment IDs only).
    /// When deserializing from YAML, equipment IDs are read but equipment objects
    /// must be populated separately from building data (equipment is stored at floor level in YAML).
    pub equipment: Vec<Equipment>,
    /// Position, dimensions, and bounding box
    pub spatial_properties: SpatialProperties,
    /// Key-value metadata
    pub properties: HashMap<String, String>,
    /// Creation timestamp (optional, omitted from YAML for backward compatibility)
    pub created_at: Option<DateTime<Utc>>,
    /// Last modification timestamp (optional, omitted from YAML for backward compatibility)
    pub updated_at: Option<DateTime<Utc>>,
}

// Custom Serialize implementation for Room
impl serde::Serialize for Room {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use serde::ser::SerializeStruct;
        let field_count = 5 + if self.created_at.is_some() { 1 } else { 0 } + if self.updated_at.is_some() { 1 } else { 0 };
        let mut state = serializer.serialize_struct("Room", field_count)?;
        state.serialize_field("id", &self.id)?;
        state.serialize_field("name", &self.name)?;
        state.serialize_field("room_type", &self.room_type)?;
        // Serialize equipment as IDs
        let equipment_ids: Vec<String> = self.equipment.iter().map(|e| e.id.clone()).collect();
        state.serialize_field("equipment", &equipment_ids)?;
        state.serialize_field("spatial_properties", &self.spatial_properties)?;
        state.serialize_field("properties", &self.properties)?;
        if let Some(ref created_at) = self.created_at {
            state.serialize_field("created_at", created_at)?;
        }
        if let Some(ref updated_at) = self.updated_at {
            state.serialize_field("updated_at", updated_at)?;
        }
        state.end()
    }
}

// Custom Deserialize implementation for Room
impl<'de> serde::Deserialize<'de> for Room {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        use serde::de::{self, Visitor, MapAccess};
        use std::fmt;
        
        #[derive(Deserialize)]
        #[serde(field_identifier, rename_all = "snake_case")]
        enum Field {
            Id,
            Name,
            RoomType,
            Equipment,
            SpatialProperties,
            Properties,
            CreatedAt,
            UpdatedAt,
        }
        
        struct RoomVisitor;
        
        impl<'de> Visitor<'de> for RoomVisitor {
            type Value = Room;
            
            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct Room")
            }
            
            fn visit_map<V>(self, mut map: V) -> Result<Room, V::Error>
            where
                V: MapAccess<'de>,
            {
                let mut id = None;
                let mut name = None;
                let mut room_type = None;
                let mut equipment = None;
                let mut spatial_properties = None;
                let mut properties = None;
                let mut created_at = None;
                let mut updated_at = None;
                
                while let Some(key) = map.next_key()? {
                    match key {
                        Field::Id => {
                            if id.is_some() {
                                return Err(de::Error::duplicate_field("id"));
                            }
                            id = Some(map.next_value()?);
                        }
                        Field::Name => {
                            if name.is_some() {
                                return Err(de::Error::duplicate_field("name"));
                            }
                            name = Some(map.next_value()?);
                        }
                        Field::RoomType => {
                            if room_type.is_some() {
                                return Err(de::Error::duplicate_field("room_type"));
                            }
                            room_type = Some(map.next_value()?);
                        }
                        Field::Equipment => {
                            if equipment.is_some() {
                                return Err(de::Error::duplicate_field("equipment"));
                            }
                            // Deserialize as Vec<String> (equipment IDs)
                            let _ids: Vec<String> = map.next_value()?;
                            // Equipment will be populated separately from building data
                            equipment = Some(Vec::new());
                        }
                        Field::SpatialProperties => {
                            if spatial_properties.is_some() {
                                return Err(de::Error::duplicate_field("spatial_properties"));
                            }
                            spatial_properties = Some(map.next_value()?);
                        }
                        Field::Properties => {
                            if properties.is_some() {
                                return Err(de::Error::duplicate_field("properties"));
                            }
                            properties = Some(map.next_value()?);
                        }
                        Field::CreatedAt => {
                            if created_at.is_some() {
                                return Err(de::Error::duplicate_field("created_at"));
                            }
                            created_at = map.next_value()?;
                        }
                        Field::UpdatedAt => {
                            if updated_at.is_some() {
                                return Err(de::Error::duplicate_field("updated_at"));
                            }
                            updated_at = map.next_value()?;
                        }
                    }
                }
                
                let id = id.ok_or_else(|| de::Error::missing_field("id"))?;
                let name = name.ok_or_else(|| de::Error::missing_field("name"))?;
                let room_type = room_type.ok_or_else(|| de::Error::missing_field("room_type"))?;
                let equipment = equipment.unwrap_or_default();
                let spatial_properties = spatial_properties.ok_or_else(|| de::Error::missing_field("spatial_properties"))?;
                let properties = properties.unwrap_or_default();
                
                Ok(Room {
                    id,
                    name,
                    room_type,
                    equipment,
                    spatial_properties,
                    properties,
                    created_at,
                    updated_at,
                })
            }
        }
        
        const FIELDS: &[&str] = &["id", "name", "room_type", "equipment", "spatial_properties", "properties", "created_at", "updated_at"];
        deserializer.deserialize_struct("Room", FIELDS, RoomVisitor)
    }
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
        let now = Some(Utc::now());
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
        self.updated_at = Some(Utc::now());
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
        self.updated_at = Some(Utc::now());
    }
}

