//! Data management command arguments
//!
//! Argument structures for data-related CLI commands including
//! room management, equipment management, and spatial operations.

use clap::Subcommand;

/// Room management commands
#[derive(Debug, Clone, Subcommand)]
pub enum RoomCommands {
    /// Create a new room
    Create {
        /// Building name
        #[arg(long)]
        building: String,
        /// Floor level
        #[arg(long)]
        floor: i32,
        /// Wing name
        #[arg(long)]
        wing: String,
        /// Room name
        #[arg(long)]
        name: String,
        /// Room type
        #[arg(long)]
        room_type: String,
        /// Room dimensions (width x depth x height)
        #[arg(long)]
        dimensions: Option<String>,
        /// Room position (x,y,z)
        #[arg(long)]
        position: Option<String>,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
    },
    /// List rooms
    List {
        /// Building name
        #[arg(long)]
        building: Option<String>,
        /// Floor level
        #[arg(long)]
        floor: Option<i32>,
        /// Wing name
        #[arg(long)]
        wing: Option<String>,
        /// Show detailed information
        #[arg(long)]
        verbose: bool,
        /// Open interactive explorer
        #[arg(long)]
        interactive: bool,
    },
    /// Show room details
    Show {
        /// Room ID or name
        room: String,
        /// Show equipment in room
        #[arg(long)]
        equipment: bool,
    },
    /// Update room properties
    Update {
        /// Room ID or name
        room: String,
        /// Property to update (key=value)
        #[arg(long)]
        property: Vec<String>,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
    },
    /// Delete a room
    Delete {
        /// Room ID or name
        room: String,
        /// Confirm deletion
        #[arg(long)]
        confirm: bool,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
    },
}

/// Equipment management commands
#[derive(Debug, Clone, Subcommand)]
pub enum EquipmentCommands {
    /// Add equipment to a room
    Add {
        /// Room ID or name
        #[arg(long)]
        room: String,
        /// Equipment name
        #[arg(long)]
        name: String,
        /// Equipment type
        #[arg(long)]
        equipment_type: String,
        /// Equipment position (x,y,z)
        #[arg(long)]
        position: Option<String>,
        /// ArxOS Address path (e.g., /usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01)
        /// If not provided, address will be auto-generated from context.
        /// Supports 7-part hierarchical format: /country/state/city/building/floor/room/fixture
        #[arg(long)]
        at: Option<String>,
        /// Equipment properties (key=value)
        #[arg(long)]
        property: Vec<String>,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
    },
    /// List equipment
    List {
        /// Room ID or name
        #[arg(long)]
        room: Option<String>,
        /// Equipment type filter
        #[arg(long)]
        equipment_type: Option<String>,
        /// Show detailed information
        #[arg(long)]
        verbose: bool,
        /// Open interactive browser
        #[arg(long)]
        interactive: bool,
    },
    /// Update equipment
    Update {
        /// Equipment ID or name
        equipment: String,
        /// Property to update (key=value)
        #[arg(long)]
        property: Vec<String>,
        /// New position (x,y,z)
        #[arg(long)]
        position: Option<String>,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
    },
    /// Remove equipment
    Remove {
        /// Equipment ID or name
        equipment: String,
        /// Confirm removal
        #[arg(long)]
        confirm: bool,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
    },
}

/// Spatial operations and queries
#[derive(Debug, Clone, Subcommand)]
pub enum SpatialCommands {
    /// Convert grid coordinates to real coordinates
    GridToReal {
        /// Grid coordinate (e.g., "D-4")
        grid: String,
        /// Building name
        building: Option<String>,
    },
    /// Convert real coordinates to grid coordinates
    RealToGrid {
        /// X coordinate
        x: f64,
        /// Y coordinate
        y: f64,
        /// Z coordinate (optional)
        z: Option<f64>,
        /// Building name
        building: Option<String>,
    },
    /// Query spatial relationships
    Query {
        /// Query type
        #[arg(long)]
        query_type: String,
        /// Target entity (room or equipment)
        #[arg(long)]
        entity: String,
        /// Additional parameters
        #[arg(long)]
        params: Vec<String>,
    },
    /// Set spatial relationships
    Relate {
        /// First entity
        #[arg(long)]
        entity1: String,
        /// Second entity
        #[arg(long)]
        entity2: String,
        /// Relationship type
        #[arg(long)]
        relationship: String,
    },
    /// Transform coordinates
    Transform {
        /// Source coordinate system
        #[arg(long)]
        from: String,
        /// Target coordinate system
        #[arg(long)]
        to: String,
        /// Entity to transform
        #[arg(long)]
        entity: String,
    },
    /// Validate spatial data
    Validate {
        /// Entity to validate
        #[arg(long)]
        entity: Option<String>,
        /// Validation tolerance
        #[arg(long)]
        tolerance: Option<f64>,
    },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_room_commands_derive() {
        // Verify that the Subcommand derive works correctly
        // Actual parsing would need clap's testing utilities
    }

    #[test]
    fn test_equipment_commands_derive() {
        // Verify that the Subcommand derive works correctly
    }

    #[test]
    fn test_spatial_commands_derive() {
        // Verify that the Subcommand derive works correctly
    }
}
