//! Room data structure and implementation

use super::{Equipment, SpatialProperties};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

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
    /// Collection of equipment physically located in the room.
    ///
    /// When serializing to YAML, this serializes as `Vec<String>` (equipment IDs only).
    /// When deserializing from YAML, call `BuildingData::rehydrate_room_equipment()` after
    /// deserialization to populate this list from the global `BuildingData.equipment` list.
    pub equipment: Vec<Equipment>,
    /// Equipment IDs captured during YAML deserialization (before rehydration).
    ///
    /// After calling `BuildingData::rehydrate_room_equipment()` these IDs have been
    /// resolved into full `Equipment` objects in `self.equipment` and can be ignored.
    #[doc(hidden)]
    pub pending_equipment_ids: Vec<String>,
    /// Position, dimensions, and bounding box
    pub spatial_properties: SpatialProperties,
    /// Key-value metadata
    pub properties: HashMap<String, String>,
    /// Creation timestamp (optional, omitted from YAML for backward compatibility)
    pub created_at: Option<DateTime<Utc>>,
    /// Last modification timestamp (optional, omitted from YAML for backward compatibility)
    pub updated_at: Option<DateTime<Utc>>,
    /// LiDAR-specific enrichments (optional)
    pub lidar_enrichment: Option<super::LidarEnrichment>,
    /// IFC product GlobalId when known (stable interchange identity)
    pub ifc_global_id: Option<String>,
}

/// DTO for Room serialization to preserve YAML and Git layout
#[derive(Serialize, Deserialize)]
struct RoomDto {
    id: String,
    name: String,
    room_type: RoomType,
    equipment: Vec<String>,
    spatial_properties: super::SpatialProperties,
    properties: HashMap<String, String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    created_at: Option<DateTime<Utc>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    updated_at: Option<DateTime<Utc>>,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    lidar_enrichment: Option<super::LidarEnrichment>,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    ifc_global_id: Option<String>,
}

// Custom Serialize implementation for Room via RoomDto
impl serde::Serialize for Room {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let equipment_ids: Vec<String> = self.equipment.iter().map(|e| e.id.clone()).collect();
        let dto = RoomDto {
            id: self.id.clone(),
            name: self.name.clone(),
            room_type: self.room_type.clone(),
            equipment: equipment_ids,
            spatial_properties: self.spatial_properties.clone(),
            properties: self.properties.clone(),
            created_at: self.created_at,
            updated_at: self.updated_at,
            lidar_enrichment: self.lidar_enrichment.clone(),
            ifc_global_id: self.ifc_global_id.clone(),
        };
        dto.serialize(serializer)
    }
}

// Custom Deserialize implementation for Room via RoomDto
impl<'de> serde::Deserialize<'de> for Room {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let dto = RoomDto::deserialize(deserializer)?;
        Ok(Room {
            id: dto.id,
            name: dto.name,
            room_type: dto.room_type,
            equipment: Vec::new(),
            pending_equipment_ids: dto.equipment,
            spatial_properties: dto.spatial_properties,
            properties: dto.properties,
            created_at: dto.created_at,
            updated_at: dto.updated_at,
            lidar_enrichment: dto.lidar_enrichment,
            ifc_global_id: dto.ifc_global_id,
        })
    }
}

/// Types of rooms in a building
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
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
    /// Parse from string (for backward compatibility)
    ///
    /// **Note:** Prefer using `FromStr` trait (`room_type.parse()`) instead.
    #[deprecated(note = "Use FromStr trait instead: room_type.parse()")]
    pub fn from_string(s: &str) -> Self {
        s.parse().unwrap_or_else(|_| RoomType::Other(s.to_string()))
    }
}

impl Room {
    /// Create a new room with a unique ID and default values
    ///
    /// The room is initialized with:
    /// - A unique UUID
    /// - Empty equipment collection
    /// - Default spatial properties (origin position, zero dimensions)
    /// - Empty properties map
    /// - Creation and update timestamps
    ///
    /// # Arguments
    ///
    /// * `name` - Human-readable room name
    /// * `room_type` - Type categorization (Office, Laboratory, etc.)
    ///
    /// # Returns
    ///
    /// A new Room instance with default values
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Room, RoomType};
    /// let room = Room::new("Office 101".to_string(), RoomType::Office);
    /// assert_eq!(room.name, "Office 101");
    /// assert_eq!(room.room_type.to_string(), "Office");
    /// assert_eq!(room.equipment.len(), 0);
    /// ```
    pub fn new(name: String, room_type: RoomType) -> Self {
        let now = Some(Utc::now());
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            room_type,
            equipment: Vec::new(),
            pending_equipment_ids: Vec::new(),
            spatial_properties: SpatialProperties::default(),
            properties: HashMap::new(),
            created_at: now,
            updated_at: now,
            lidar_enrichment: None,
            ifc_global_id: None,
        }
    }

    /// Add equipment to the room
    ///
    /// Updates the room's `updated_at` timestamp automatically.
    ///
    /// # Arguments
    ///
    /// * `equipment` - The equipment to add to this room
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Room, RoomType, Equipment, EquipmentType};
    /// let mut room = Room::new("Office 101".to_string(), RoomType::Office);
    /// let equipment = Equipment::new(
    ///     "Desk Lamp".to_string(),
    ///     "/equipment/lamp".to_string(),
    ///     EquipmentType::Furniture,
    /// );
    /// room.add_equipment(equipment);
    /// assert_eq!(room.equipment.len(), 1);
    /// ```
    pub fn add_equipment(&mut self, equipment: Equipment) {
        self.equipment.push(equipment);
        self.updated_at = Some(Utc::now());
    }

    /// Find equipment by name
    ///
    /// Performs case-sensitive name matching.
    ///
    /// # Arguments
    ///
    /// * `name` - The equipment name to search for
    ///
    /// # Returns
    ///
    /// * `Some(&Equipment)` - Reference to the equipment if found
    /// * `None` - If no equipment with that name exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Room, RoomType, Equipment, EquipmentType};
    /// let mut room = Room::new("Office 101".to_string(), RoomType::Office);
    /// room.add_equipment(Equipment::new(
    ///     "Desk Lamp".to_string(),
    ///     "/lamp".to_string(),
    ///     EquipmentType::Furniture,
    /// ));
    ///
    /// assert!(room.find_equipment("Desk Lamp").is_some());
    /// assert!(room.find_equipment("Missing").is_none());
    /// ```
    pub fn find_equipment(&self, name: &str) -> Option<&Equipment> {
        self.equipment.iter().find(|e| e.name == name)
    }

    /// Find equipment by name (mutable reference)
    ///
    /// Performs case-sensitive name matching.
    ///
    /// # Arguments
    ///
    /// * `name` - The equipment name to search for
    ///
    /// # Returns
    ///
    /// * `Some(&mut Equipment)` - Mutable reference to the equipment if found
    /// * `None` - If no equipment with that name exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Room, RoomType, Equipment, EquipmentType};
    /// let mut room = Room::new("Office 101".to_string(), RoomType::Office);
    /// room.add_equipment(Equipment::new(
    ///     "Desk Lamp".to_string(),
    ///     "/lamp".to_string(),
    ///     EquipmentType::Furniture,
    /// ));
    ///
    /// if let Some(equipment) = room.find_equipment_mut("Desk Lamp") {
    ///     equipment.name = "Floor Lamp".to_string();
    /// }
    /// assert_eq!(room.find_equipment("Floor Lamp").unwrap().name, "Floor Lamp");
    /// ```
    pub fn find_equipment_mut(&mut self, name: &str) -> Option<&mut Equipment> {
        self.equipment.iter_mut().find(|e| e.name == name)
    }

    /// Update the room's spatial properties
    ///
    /// Sets the position, dimensions, and bounding box for the room.
    /// Updates the room's `updated_at` timestamp automatically.
    ///
    /// # Arguments
    ///
    /// * `spatial_properties` - The new spatial properties
    ///
    /// # Examples
    ///
    /// ```rust,ignore
    /// use arxos::core::{Room, RoomType, SpatialProperties, Position, Dimensions, BoundingBox};
    /// let mut room = Room::new("Office 101".to_string(), RoomType::Office);
    /// let spatial_props = SpatialProperties {
    ///     position: Position { x: 10.0, y: 20.0, z: 0.0, coordinate_system: "building".to_string() },
    ///     dimensions: Dimensions { width: 5.0, height: 3.0, depth: 4.0 },
    ///     bounding_box: BoundingBox::new(
    ///         Position { x: 10.0, y: 20.0, z: 0.0, coordinate_system: "building".to_string() },
    ///         Position { x: 15.0, y: 23.0, z: 4.0, coordinate_system: "building".to_string() },
    ///     ),
    ///     coordinate_system: "building".to_string(),
    /// };
    /// room.update_spatial_properties(spatial_props);
    /// assert_eq!(room.spatial_properties.dimensions.width, 5.0);
    /// ```
    pub fn update_spatial_properties(&mut self, spatial_properties: SpatialProperties) {
        self.spatial_properties = spatial_properties;
        self.updated_at = Some(Utc::now());
    }
}
