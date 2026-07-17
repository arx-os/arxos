//! Wing data structure and implementation

use super::{Equipment, Room, Anchor};
use super::domain::ArxAddress;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Represents a wing on a floor
#[derive(Debug, Clone)]
pub struct Wing {
    pub id: String,
    pub name: String,
    pub rooms: Vec<Room>,
    pub equipment: Vec<Equipment>,
    /// Temporary list of equipment IDs parsed during deserialization
    pub pending_equipment_ids: Vec<String>,
    pub properties: HashMap<String, String>,
    /// Hierarchical ArxOS address (durable on Building YAML SSOT)
    pub address: Option<ArxAddress>,
    /// Collection of anchors dropped in this wing
    pub anchors: Vec<Anchor>,
    /// Temporary list of anchor IDs parsed during deserialization
    pub pending_anchor_ids: Vec<String>,
}

#[derive(Serialize, Deserialize)]
struct WingDto {
    id: String,
    name: String,
    rooms: Vec<Room>,
    equipment: Vec<String>,
    #[serde(default, with = "crate::utils::sorted_map")]
    properties: HashMap<String, String>,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    address: Option<ArxAddress>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    anchors: Vec<String>,
}

impl serde::Serialize for Wing {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let equipment_ids: Vec<String> = self.equipment.iter().map(|e| e.id.clone()).collect();
        let anchor_ids: Vec<String> = self.anchors.iter().map(|a| a.id.clone()).collect();
        let dto = WingDto {
            id: self.id.clone(),
            name: self.name.clone(),
            rooms: self.rooms.clone(),
            equipment: equipment_ids,
            properties: self.properties.clone(),
            address: self.address.clone(),
            anchors: anchor_ids,
        };
        dto.serialize(serializer)
    }
}

impl<'de> serde::Deserialize<'de> for Wing {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let dto = WingDto::deserialize(deserializer)?;
        Ok(Wing {
            id: dto.id,
            name: dto.name,
            rooms: dto.rooms,
            equipment: Vec::new(),
            pending_equipment_ids: dto.equipment,
            properties: dto.properties,
            address: dto.address,
            anchors: Vec::new(),
            pending_anchor_ids: dto.anchors,
        })
    }
}

impl Wing {
    /// Create a new wing with a unique ID and default values
    ///
    /// The wing is initialized with:
    /// - A unique UUID
    /// - Empty rooms and equipment collections
    /// - Empty properties map
    ///
    /// # Arguments
    ///
    /// * `name` - Human-readable wing name
    ///
    /// # Returns
    ///
    /// A new Wing instance with default values
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::Wing;
    /// let wing = Wing::new("East Wing".to_string());
    /// assert_eq!(wing.name, "East Wing");
    /// assert_eq!(wing.rooms.len(), 0);
    /// ```
    pub fn new(name: String) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            rooms: Vec::new(),
            equipment: Vec::new(),
            pending_equipment_ids: Vec::new(),
            properties: HashMap::new(),
            address: None,
            anchors: Vec::new(),
            pending_anchor_ids: Vec::new(),
        }
    }

    /// Add a room to the wing
    ///
    /// Rooms are spaces within a wing that contain equipment
    /// and represent functional areas (offices, labs, storage, etc.).
    ///
    /// # Arguments
    ///
    /// * `room` - The room to add to this wing
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Wing, Room, RoomType};
    /// let mut wing = Wing::new("East Wing".to_string());
    /// let room = Room::new("Office 101".to_string(), RoomType::Office);
    /// wing.add_room(room);
    /// assert_eq!(wing.rooms.len(), 1);
    /// ```
    pub fn add_room(&mut self, room: Room) {
        self.rooms.push(room);
    }

    /// Find a room by name
    ///
    /// Performs case-sensitive name matching.
    ///
    /// # Arguments
    ///
    /// * `name` - The room name to search for
    ///
    /// # Returns
    ///
    /// * `Some(&Room)` - Reference to the room if found
    /// * `None` - If no room with that name exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Wing, Room, RoomType};
    /// let mut wing = Wing::new("East Wing".to_string());
    /// wing.add_room(Room::new("Office 101".to_string(), RoomType::Office));
    /// wing.add_room(Room::new("Lab 102".to_string(), RoomType::Laboratory));
    ///
    /// assert!(wing.find_room("Office 101").is_some());
    /// assert!(wing.find_room("Office 999").is_none());
    /// ```
    pub fn find_room(&self, name: &str) -> Option<&Room> {
        self.rooms.iter().find(|r| r.name == name)
    }

    /// Find a room by name (mutable reference)
    ///
    /// Performs case-sensitive name matching.
    ///
    /// # Arguments
    ///
    /// * `name` - The room name to search for
    ///
    /// # Returns
    ///
    /// * `Some(&mut Room)` - Mutable reference to the room if found
    /// * `None` - If no room with that name exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Wing, Room, RoomType};
    /// let mut wing = Wing::new("East Wing".to_string());
    /// wing.add_room(Room::new("Office 101".to_string(), RoomType::Office));
    ///
    /// if let Some(room) = wing.find_room_mut("Office 101") {
    ///     room.name = "Conference Room 101".to_string();
    /// }
    /// assert_eq!(wing.find_room("Conference Room 101").unwrap().name, "Conference Room 101");
    /// ```
    pub fn find_room_mut(&mut self, name: &str) -> Option<&mut Room> {
        self.rooms.iter_mut().find(|r| r.name == name)
    }
}
