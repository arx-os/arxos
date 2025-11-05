//! Building data structure and implementation

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use super::{Floor, Room};

/// Represents a building in ArxOS
///
/// The `Building` struct is the root entity in the ArxOS hierarchy:
/// Building → Floor → Wing → Room → Equipment
///
/// # Fields
///
/// * `id` - Unique identifier (UUID)
/// * `name` - Human-readable building name
/// * `path` - Universal path identifier for the building
/// * `created_at` - Timestamp when the building was created
/// * `updated_at` - Timestamp of last modification
/// * `floors` - Collection of floors in the building
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Building {
    /// Unique identifier for the building
    pub id: String,
    /// Human-readable building name
    pub name: String,
    /// Universal path identifier
    pub path: String,
    /// Creation timestamp
    pub created_at: DateTime<Utc>,
    /// Last modification timestamp
    pub updated_at: DateTime<Utc>,
    /// Collection of floors in the building
    pub floors: Vec<Floor>,
    // Equipment lives in floors -> wings -> rooms hierarchy
}

impl Building {
    /// Create a new building with a unique ID and timestamps
    ///
    /// # Arguments
    ///
    /// * `name` - Human-readable building name
    /// * `path` - Universal path identifier
    ///
    /// # Returns
    ///
    /// A new `Building` instance with empty floors collection
    pub fn new(name: String, path: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            path,
            created_at: now,
            updated_at: now,
            floors: Vec::new(),
        }
    }
    
    /// Add a floor to the building
    /// 
    /// # Panics
    /// 
    /// Panics in debug builds if a floor with the same level already exists.
    /// In release builds, duplicate floors are allowed but may cause issues.
    pub fn add_floor(&mut self, floor: Floor) {
        debug_assert!(
            !self.floors.iter().any(|f| f.level == floor.level),
            "Floor with level {} already exists in building",
            floor.level
        );
        self.floors.push(floor);
        self.updated_at = Utc::now();
    }
    
    /// Add a floor to the building with validation
    /// 
    /// Returns `Err` if a floor with the same level already exists.
    pub fn try_add_floor(&mut self, floor: Floor) -> Result<(), String> {
        if self.floors.iter().any(|f| f.level == floor.level) {
            return Err(format!("Floor with level {} already exists", floor.level));
        }
        self.floors.push(floor);
        self.updated_at = Utc::now();
        Ok(())
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

