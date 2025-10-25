//! # CLI Module for ArxOS CLI
//!
//! This module defines the command-line interface structure using clap,
//! including all commands, subcommands, and their arguments.

use clap::{Parser, Subcommand};

/// Main CLI structure for ArxOS
#[derive(Parser)]
#[command(name = "arx")]
#[command(about = "ArxOS - Git for Buildings")]
#[command(version = "0.1.0")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

/// Main command enumeration
#[derive(Subcommand)]
pub enum Commands {
    /// Import IFC file to Git repository
    Import {
        /// Path to IFC file
        file: String,
    },
    /// Export building data to Git repository
    Export {
        /// Git repository URL
        repo: String,
    },
    /// Render building visualization
    Render {
        /// Building identifier
        building: String,
    },
    /// Interactive 3D building visualization with real-time controls
    Interactive {
        /// Building identifier
        building: String,
    },
    /// Validate building data
    Validate {
        /// Path to building data
        path: Option<String>,
    },
    /// Show repository status and changes
    Status {
        /// Show detailed status information
        #[arg(long)]
        verbose: bool,
    },
    /// Show differences between commits
    Diff {
        /// Compare with specific commit hash
        commit: Option<String>,
        /// Show diff for specific file
        file: Option<String>,
        /// Show file statistics only
        #[arg(long)]
        stat: bool,
    },
    /// Show commit history
    History {
        /// Number of commits to show
        #[arg(long, default_value = "10")]
        limit: Option<usize>,
        /// Show detailed commit information
        #[arg(long)]
        verbose: bool,
        /// Show history for specific file
        file: Option<String>,
    },
    /// Manage configuration
    Config {
        /// Show current configuration
        #[arg(long)]
        show: bool,
        /// Set configuration value (format: section.key=value)
        #[arg(long)]
        set: Option<String>,
        /// Reset to defaults
        #[arg(long)]
        reset: bool,
        /// Edit configuration file
        #[arg(long)]
        edit: bool,
    },
    /// Room management commands
    Room {
        #[command(subcommand)]
        command: RoomCommands,
    },
    /// Equipment management commands
    Equipment {
        #[command(subcommand)]
        command: EquipmentCommands,
    },
    /// Spatial operations and queries
    Spatial {
        #[command(subcommand)]
        command: SpatialCommands,
    },
    /// Live monitoring dashboard
    Watch {
        #[arg(long)]
        building: Option<String>,
        #[arg(long)]
        floor: Option<i32>,
        #[arg(long)]
        room: Option<String>,
        #[arg(long, default_value = "5")]
        refresh_interval: u64,
    },
}

/// Room management subcommands
#[derive(Subcommand)]
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
    },
    /// Show room details
    Show {
        /// Room ID or name
        room_id: String,
        /// Show equipment in room
        #[arg(long)]
        equipment: bool,
    },
    /// Update room properties
    Update {
        /// Room ID or name
        room_id: String,
        /// New room name
        #[arg(long)]
        new_name: Option<String>,
        /// Room type
        #[arg(long)]
        room_type: Option<String>,
        /// Room dimensions (width x depth x height)
        #[arg(long)]
        dimensions: Option<String>,
        /// Room position (x,y,z)
        #[arg(long)]
        position: Option<String>,
    },
    /// Delete a room
    Delete {
        /// Room ID or name
        room_id: String,
        /// Confirm deletion
        #[arg(long)]
        confirm: bool,
    },
}

/// Equipment management subcommands
#[derive(Subcommand)]
pub enum EquipmentCommands {
    /// Add equipment to a room
    Add {
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
    },
    /// List equipment
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
        /// Room name
        #[arg(long)]
        room: Option<String>,
        /// Equipment type filter
        #[arg(long)]
        equipment_type: Option<String>,
        /// Show detailed information
        #[arg(long)]
        verbose: bool,
    },
    /// Show equipment details
    Show {
        /// Equipment ID or name
        equipment_id: String,
        /// Show room information
        #[arg(long)]
        room: bool,
    },
    /// Update equipment
    Update {
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
        room: String,
        /// Equipment name
        #[arg(long)]
        name: String,
        /// New equipment name
        #[arg(long)]
        new_name: Option<String>,
        /// Equipment type
        #[arg(long)]
        equipment_type: Option<String>,
        /// New position (x,y,z)
        #[arg(long)]
        position: Option<String>,
    },
    /// Remove equipment
    Remove {
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
        room: String,
        /// Equipment name
        #[arg(long)]
        name: String,
        /// Confirm removal
        #[arg(long)]
        confirm: bool,
    },
}

/// Spatial operations subcommands
#[derive(Subcommand)]
pub enum SpatialCommands {
    /// Query spatial relationships
    Query {
        /// Building name
        #[arg(long)]
        building: String,
        /// Query type
        #[arg(long)]
        query_type: String,
        /// Additional parameters
        #[arg(long)]
        parameters: Vec<String>,
    },
    /// Set spatial relationships
    Relate {
        /// Building name
        #[arg(long)]
        building: String,
        /// First entity
        #[arg(long)]
        entity1: String,
        /// Second entity
        #[arg(long)]
        entity2: String,
    },
    /// Transform coordinates
    Transform {
        /// Building name
        #[arg(long)]
        building: String,
        /// Entity to transform
        #[arg(long)]
        entity: String,
        /// Transformation type
        #[arg(long)]
        transformation: String,
    },
    /// Validate spatial data
    Validate {
        /// Building name
        #[arg(long)]
        building: String,
    },
}
