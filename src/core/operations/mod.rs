//! Business logic operations for building, room, and equipment management
//!
//! This module provides CRUD operations and spatial queries for buildings, rooms,
//! equipment, and their spatial relationships.
//!
//! # Module Organization
//!
//! - `room` - Room CRUD operations
//! - `equipment` - Equipment CRUD operations
//! - `spatial` - Spatial queries and validation
//!
//! # Usage
//!
//! ```ignore
//! use crate::core::operations::{create_room, add_equipment, spatial_query};
//!
//! // Create a room
//! create_room("my_building", 1, room, Some("East Wing"), true)?;
//!
//! // Add equipment
//! add_equipment("my_building", Some("Room 101"), equipment, true)?;
//!
//! // Spatial query
//! let results = spatial_query("nearest", "room", vec!["0.0", "0.0", "0.0"])?;
//! ```

pub mod room;
pub mod equipment;
pub mod spatial;
#[cfg(test)]
mod spatial_tests;

// Re-export room operations
pub use room::{
    create_room, delete_room, delete_room_impl, get_room, list_rooms, update_room,
    update_room_impl,
};

// Re-export equipment operations
pub use equipment::{
    add_equipment, list_equipment, remove_equipment, remove_equipment_impl, update_equipment,
    update_equipment_impl,
};

// Re-export spatial operations and types
pub use spatial::{
    set_spatial_relationship, spatial_query, transform_coordinates, validate_spatial,
    SpatialValidationIssue, SpatialValidationResult,
};
