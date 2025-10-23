//! ArxOS Core - Business logic and data processing
//!
//! This crate contains the core business logic for ArxOS, including:
//! - Spatial data processing
//! - Equipment management
//! - Room management
//! - Git operations
//! - Data validation
//!
//! It's designed to be used by both the CLI and mobile applications.

pub mod spatial;
pub mod equipment;
pub mod room;
pub mod spatial_ops;
pub mod git;
pub mod error;
pub mod types;

// Include the core data structures from the moved mod.rs
pub mod core;
pub use core::*;

// Re-export commonly used types
pub use error::{ArxError, Result};
pub use types::*;

// Re-export parse functions
pub use room::parse_room_type;
pub use equipment::parse_equipment_type;

/// Core ArxOS engine
#[derive(Debug)]
pub struct ArxOSCore {
    room_manager: room::RoomManager,
    equipment_manager: equipment::EquipmentManager,
    spatial_manager: spatial_ops::SpatialManager,
    repository_path: std::path::PathBuf,
}

impl ArxOSCore {
    /// Create a new ArxOS core instance
    pub fn new() -> Result<Self> {
        Ok(Self {
            room_manager: room::RoomManager::new(),
            equipment_manager: equipment::EquipmentManager::new(),
            spatial_manager: spatial_ops::SpatialManager::new(),
            repository_path: std::env::current_dir()?,
        })
    }
    
    /// Process spatial data
    pub fn process_spatial_data(&self, data: Vec<u8>) -> Result<String> {
        spatial::process_spatial_data(data)
    }
    
    /// Sync repository
    pub fn sync_repository(&self) -> Result<()> {
        git::sync_repository(&self.repository_path, None)
    }

    /// Get room manager reference
    pub fn room_manager(&mut self) -> &mut room::RoomManager {
        &mut self.room_manager
    }

    /// Get equipment manager reference
    pub fn equipment_manager(&mut self) -> &mut equipment::EquipmentManager {
        &mut self.equipment_manager
    }

    /// Get spatial manager reference
    pub fn spatial_manager(&mut self) -> &mut spatial_ops::SpatialManager {
        &mut self.spatial_manager
    }
}