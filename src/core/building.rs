//! Building data structure and implementation

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use super::{Floor, Room, Equipment};

/// Represents a building in ArxOS
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Building {
    pub id: String,
    pub name: String,
    pub path: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub floors: Vec<Floor>,
    pub equipment: Vec<Equipment>, // Legacy - will be moved to floors
}

impl Building {
    pub fn new(name: String, path: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            path,
            created_at: now,
            updated_at: now,
            floors: Vec::new(),
            equipment: Vec::new(), // Legacy
        }
    }
    
    /// Add a floor to the building
    pub fn add_floor(&mut self, floor: Floor) {
        self.floors.push(floor);
        self.updated_at = Utc::now();
    }
    
    /// Find a floor by level
    pub fn find_floor(&self, level: i32) -> Option<&Floor> {
        self.floors.iter().find(|f| f.level == level)
    }
    
    /// Find a floor by level (mutable)
    pub fn find_floor_mut(&mut self, level: i32) -> Option<&mut Floor> {
        self.floors.iter_mut().find(|f| f.level == level)
    }
    
    /// Get all rooms in the building
    pub fn get_all_rooms(&self) -> Vec<&Room> {
        self.floors.iter()
            .flat_map(|floor| floor.wings.iter())
            .flat_map(|wing| wing.rooms.iter())
            .collect()
    }
    
    /// Find a room by ID
    pub fn find_room(&self, room_id: &str) -> Option<&Room> {
        self.get_all_rooms().into_iter().find(|room| room.id == room_id)
    }
}

