//! Floor data structure and implementation

use super::{Equipment, Wing};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Represents a floor in a building
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Floor {
    pub id: String,
    pub name: String,
    pub level: i32,
    /// Elevation of the floor (in meters, relative to building origin)
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub elevation: Option<f64>,
    /// Bounding box for the entire floor
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub bounding_box: Option<crate::core::spatial::BoundingBox3D>,
    pub wings: Vec<Wing>,
    /// Collection of equipment in common areas (hallways, lobbies)
    ///
    /// Equipment located inside specific rooms should be stored in `Room.equipment`.
    /// This collection is for equipment that doesn't belong to a specific room.
    pub equipment: Vec<Equipment>,
    pub properties: HashMap<String, String>,
}

impl Floor {
    /// Create a new floor with a unique ID and default values
    ///
    /// The floor is initialized with:
    /// - A unique UUID
    /// - Empty wings and equipment collections
    /// - No elevation or bounding box (to be set later)
    /// - Empty properties map
    ///
    /// # Arguments
    ///
    /// * `name` - Human-readable floor name
    /// * `level` - Floor level number (0 = ground, 1 = first floor, etc.)
    ///
    /// # Returns
    ///
    /// A new Floor instance with default values
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::Floor;
    /// let floor = Floor::new("Ground Floor".to_string(), 0);
    /// assert_eq!(floor.name, "Ground Floor");
    /// assert_eq!(floor.level, 0);
    /// assert_eq!(floor.wings.len(), 0);
    /// ```
    pub fn new(name: String, level: i32) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            level,
            elevation: None,
            bounding_box: None,
            wings: Vec::new(),
            equipment: Vec::new(),
            properties: HashMap::new(),
        }
    }

    /// Add a wing to the floor
    ///
    /// Wings are organizational subdivisions within a floor
    /// (e.g., "East Wing", "West Wing", "North Tower").
    ///
    /// # Arguments
    ///
    /// * `wing` - The wing to add to this floor
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Floor, Wing};
    /// let mut floor = Floor::new("Ground Floor".to_string(), 0);
    /// let wing = Wing::new("East Wing".to_string());
    /// floor.add_wing(wing);
    /// assert_eq!(floor.wings.len(), 1);
    /// ```
    pub fn add_wing(&mut self, wing: Wing) {
        self.wings.push(wing);
    }

    /// Find a wing by name
    ///
    /// Performs case-sensitive name matching.
    ///
    /// # Arguments
    ///
    /// * `name` - The wing name to search for
    ///
    /// # Returns
    ///
    /// * `Some(&Wing)` - Reference to the wing if found
    /// * `None` - If no wing with that name exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Floor, Wing};
    /// let mut floor = Floor::new("Ground Floor".to_string(), 0);
    /// floor.add_wing(Wing::new("East Wing".to_string()));
    /// floor.add_wing(Wing::new("West Wing".to_string()));
    ///
    /// assert!(floor.find_wing("East Wing").is_some());
    /// assert!(floor.find_wing("South Wing").is_none());
    /// ```
    pub fn find_wing(&self, name: &str) -> Option<&Wing> {
        self.wings.iter().find(|w| w.name == name)
    }

    /// Find a wing by name (mutable reference)
    ///
    /// Performs case-sensitive name matching.
    ///
    /// # Arguments
    ///
    /// * `name` - The wing name to search for
    ///
    /// # Returns
    ///
    /// * `Some(&mut Wing)` - Mutable reference to the wing if found
    /// * `None` - If no wing with that name exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Floor, Wing};
    /// let mut floor = Floor::new("Ground Floor".to_string(), 0);
    /// floor.add_wing(Wing::new("East Wing".to_string()));
    ///
    /// if let Some(wing) = floor.find_wing_mut("East Wing") {
    ///     wing.name = "Northeast Wing".to_string();
    /// }
    /// assert_eq!(floor.find_wing("Northeast Wing").unwrap().name, "Northeast Wing");
    /// ```
    pub fn find_wing_mut(&mut self, name: &str) -> Option<&mut Wing> {
        self.wings.iter_mut().find(|w| w.name == name)
    }
}
