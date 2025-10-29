//! Floor data structure and implementation

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::collections::HashMap;
use super::{Wing, Equipment};

/// Represents a floor in a building
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Floor {
    pub id: String,
    pub name: String,
    pub level: i32,
    pub wings: Vec<Wing>,
    pub equipment: Vec<Equipment>,
    pub properties: HashMap<String, String>,
}

impl Floor {
    pub fn new(name: String, level: i32) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            level,
            wings: Vec::new(),
            equipment: Vec::new(),
            properties: HashMap::new(),
        }
    }
    
    /// Add a wing to the floor
    pub fn add_wing(&mut self, wing: Wing) {
        self.wings.push(wing);
    }
    
    /// Find a wing by name
    pub fn find_wing(&self, name: &str) -> Option<&Wing> {
        self.wings.iter().find(|w| w.name == name)
    }
    
    /// Find a wing by name (mutable)
    pub fn find_wing_mut(&mut self, name: &str) -> Option<&mut Wing> {
        self.wings.iter_mut().find(|w| w.name == name)
    }
}

