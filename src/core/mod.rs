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
pub mod spatial;
mod types;
mod wing;

// Re-export all public types and functions
pub use building::Building;
pub use equipment::{
    Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType,
};
pub use floor::Floor;
pub use room::{Room, RoomType};
pub use types::{BoundingBox, Dimensions, Position, SpatialProperties};
pub use wing::Wing;

// Re-export all operations
