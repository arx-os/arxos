//! Core data structures for ArxOS
//!
//! This module provides the foundational data structures and business logic
//! for representing buildings, floors, rooms, equipment, and their spatial relationships.

// Core modules
mod anchor;
mod building;
pub mod domain;
mod equipment;
mod floor;
pub mod identity;
pub mod operations;
pub mod review;
mod room;
mod serde_helpers;
pub mod spatial;
mod types;
mod wing;

// Re-export all public types and functions
pub use anchor::{Anchor, RelativePose, PoseType, MapRef};
pub use building::{Building, BuildingMetadata, CoordinateSystemInfo};
pub use equipment::{Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType};
pub use floor::Floor;
pub use identity::ArxId;
pub use review::{
    filter_building_for_export, mark_proposed, review_status_from_props, summarize_review,
    ReviewStatus, ReviewSummary, PROP_REVIEW_STATUS,
};
pub use room::{Room, RoomType};
pub use types::{BoundingBox, Dimensions, LidarEnrichment, Position, SpatialProperties};
pub use wing::Wing;

// Re-export all operations

