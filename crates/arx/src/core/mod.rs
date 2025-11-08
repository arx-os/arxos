//! Core data structures for ArxOS
//!
//! This module provides the foundational data structures and business logic
//! for representing buildings, floors, rooms, equipment, and their spatial relationships.

// Core modules
mod building;
mod equipment;
mod floor;
pub mod operations;
mod room;
mod serde_helpers;
mod types;
mod wing;

// Re-export all public types and functions
pub use crate::spatial::{GridCoordinate, GridSystem};
pub use building::{Building, BuildingMetadata, CoordinateSystemInfo};
pub use equipment::{
    Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType, SensorMapping,
    ThresholdConfig,
};
pub use floor::Floor;
pub use room::{Room, RoomType};
pub use types::{BoundingBox, Dimensions, Position, SpatialProperties, SpatialQueryResult};
pub use wing::Wing;

// Re-export all operations
pub use operations::{
    add_equipment, create_room, delete_room, delete_room_impl, get_room, list_equipment,
    list_rooms, remove_equipment, remove_equipment_impl, set_spatial_relationship, spatial_query,
    transform_coordinates, update_equipment, update_equipment_impl, update_room, update_room_impl,
    validate_spatial, SpatialValidationIssue, SpatialValidationResult,
};
