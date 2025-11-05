//! Core data structures for ArxOS
//!
//! This module provides the foundational data structures and business logic
//! for representing buildings, floors, rooms, equipment, and their spatial relationships.

// Core modules
mod types;
mod building;
mod floor;
mod wing;
mod room;
mod equipment;
mod operations;

// Re-export all public types and functions
pub use types::{Position, Dimensions, BoundingBox, SpatialProperties, SpatialQueryResult};
pub use crate::spatial::{GridCoordinate, GridSystem};
pub use building::Building;
pub use floor::Floor;
pub use wing::Wing;
pub use room::{Room, RoomType};
pub use equipment::{Equipment, EquipmentType, EquipmentStatus};

// Re-export all operations
pub use operations::{
    create_room,
    add_equipment,
    spatial_query,
    list_rooms,
    get_room,
    update_room_impl,
    delete_room_impl,
    list_equipment,
    update_equipment_impl,
    remove_equipment_impl,
    set_spatial_relationship,
    transform_coordinates,
    validate_spatial,
    SpatialValidationResult,
    SpatialValidationIssue,
    update_room,
    delete_room,
    update_equipment,
    remove_equipment,
};
