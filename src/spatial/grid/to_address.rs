//! Grid to Address mapping utilities
//!
//! Provides functions to infer room names from grid coordinates and generate
//! addresses automatically from building context.

use anyhow::{bail, Result};
use std::collections::HashMap;

/// Context required to generate an ArxAddress.
#[derive(Debug)]
pub struct AddressContext<'a> {
    pub building: &'a str,
    pub floor: &'a str,
    pub equipment_type: &'a str,
    pub country: &'a str,
    pub state: &'a str,
    pub city: &'a str,
    pub room: Option<&'a str>,
    pub grid: Option<&'a str>,
}

impl<'a> AddressContext<'a> {
    /// Create a new context with defaults for optional location values.
    pub fn new(building: &'a str, floor: &'a str, equipment_type: &'a str) -> Self {
        Self {
            building,
            floor,
            equipment_type,
            country: "US",
            state: "CA",
            city: "San Francisco",
            room: None,
            grid: None,
        }
    }

    /// Override the country/state/city information.
    pub fn with_location(mut self, country: &'a str, state: &'a str, city: &'a str) -> Self {
        self.country = country;
        self.state = state;
        self.city = city;
        self
    }

    /// Provide an explicit room name.
    pub fn with_room(mut self, room: &'a str) -> Self {
        self.room = Some(room);
        self
    }

    /// Provide a grid coordinate so the room can be inferred.
    pub fn with_grid(mut self, grid: &'a str) -> Self {
        self.grid = Some(grid);
        self
    }
}

/// Infer room name from grid coordinate
///
/// This is a simple mapping that can be extended with site-specific data.
/// In production, this would likely load from building configuration or
/// spatial database.
///
/// # Arguments
/// * `grid` - Grid coordinate string (e.g., "D-4", "C-8")
///
/// # Returns
/// * Room name string (e.g., "mech", "kitchen")
pub fn infer_room_from_grid(grid: &str) -> Result<String> {
    let grid_mapping: HashMap<&str, &str> = [
        ("D-4", "mech"),
        ("C-8", "kitchen"),
        ("A-1", "lobby"),
        ("B-2", "office"),
        ("E-5", "storage"),
    ]
    .iter()
    .cloned()
    .collect();

    if let Some(room) = grid_mapping.get(grid) {
        Ok(room.to_string())
    } else {
        // Default room naming scheme
        let room = format!("room_{}", grid.replace('-', "_").to_lowercase());
        Ok(room)
    }
}

/// Get next available ID for a fixture in a room
///
/// This would typically query the building database to find the next
/// available ID for the given equipment type in the specified room.
pub fn get_next_fixture_id(room: &str, equipment_type: &str) -> Result<String> {
    // Simplified implementation - in reality this would query a database
    let fixture_id = format!("{}_{}_001", equipment_type, room);
    Ok(fixture_id)
}