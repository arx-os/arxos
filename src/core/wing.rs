//! Wing data structure and implementation

use super::{Equipment, Room};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Represents a wing on a floor
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Wing {
    pub id: String,
    pub name: String,
    pub rooms: Vec<Room>,
    pub equipment: Vec<Equipment>,
    pub properties: HashMap<String, String>,
}

impl Wing {
    pub fn new(name: String) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            rooms: Vec::new(),
            equipment: Vec::new(),
            properties: HashMap::new(),
        }
    }

    /// Add a room to the wing
    pub fn add_room(&mut self, room: Room) {
        self.rooms.push(room);
    }

    /// Find a room by name
    pub fn find_room(&self, name: &str) -> Option<&Room> {
        self.rooms.iter().find(|r| r.name == name)
    }

    /// Find a room by name (mutable)
    pub fn find_room_mut(&mut self, name: &str) -> Option<&mut Room> {
        self.rooms.iter_mut().find(|r| r.name == name)
    }
}
