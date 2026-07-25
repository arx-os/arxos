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

pub mod address;
pub mod address_mutate;
pub mod address_nav;
pub mod equipment;
pub mod room;
pub mod spatial;
#[cfg(test)]
mod spatial_tests;

pub use address::{backfill_equipment_addresses, reroot_addresses};
pub use address_mutate::{add_under_address, allocate_child_address, next_numeric_id, AddKind, AddResult};
pub use address_nav::{
    build_tree, collect_all_addressed, format_ls, format_show, format_tree, list_children,
    parse_address, resolve, ChildEntry, EntityKind, EntityRef, TreeNode,
};

// Re-export room operations
pub use room::{
    create_room, delete_room, delete_room_impl, get_room, list_rooms, update_room, update_room_impl,
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
