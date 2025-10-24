// CLI module for ArxOS
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "arx")]
#[command(about = "ArxOS - Git for Buildings")]
#[command(version = "0.1.0")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Import IFC file to Git repository
    Import {
        /// Path to IFC file
        ifc_file: String,
        /// Git repository URL
        #[arg(long)]
        repo: Option<String>,
    },
    /// Export building data to Git repository
    Export {
        /// Git repository URL
        #[arg(long)]
        repo: String,
    },
    /// Render building visualization
    Render {
        /// Building identifier
        #[arg(long)]
        building: String,
        /// Floor number
        #[arg(long)]
        floor: Option<i32>,
        /// Enable 3D multi-floor visualization
        #[arg(long)]
        three_d: bool,
        /// Show equipment status indicators
        #[arg(long)]
        show_status: bool,
        /// Show room boundaries
        #[arg(long)]
        show_rooms: bool,
        /// Output format (ascii, json, yaml)
        #[arg(long, default_value = "ascii")]
        format: String,
    },
    /// Validate building data
    Validate {
        /// Path to building data
        #[arg(long)]
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
        #[arg(long)]
        commit: Option<String>,
        /// Show diff for specific file
        #[arg(long)]
        file: Option<String>,
        /// Show file statistics only
        #[arg(long)]
        stat: bool,
    },
    /// Show commit history
    History {
        /// Number of commits to show
        #[arg(long, default_value = "10")]
        limit: usize,
        /// Show detailed commit information
        #[arg(long)]
        verbose: bool,
        /// Show history for specific file
        #[arg(long)]
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
        #[arg(long)]
        sensors_only: bool,
        #[arg(long)]
        alerts_only: bool,
        #[arg(long)]
        log_level: Option<String>,
    },
    /// Search building data
    Search {
        /// Search query
        query: String,
        /// Search in equipment names
        #[arg(long)]
        equipment: bool,
        /// Search in room names
        #[arg(long)]
        rooms: bool,
        /// Search in building names
        #[arg(long)]
        buildings: bool,
        /// Case-sensitive search
        #[arg(long)]
        case_sensitive: bool,
        /// Use regex pattern matching
        #[arg(long)]
        regex: bool,
        /// Maximum number of results
        #[arg(long, default_value = "50")]
        limit: usize,
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
    },
    /// Integrate AR scan data
    ArIntegrate {
        /// AR scan data file (JSON)
        #[arg(long)]
        scan_file: String,
        /// Room name for the scan
        #[arg(long)]
        room: String,
        /// Floor level
        #[arg(long)]
        floor: i32,
        /// Building identifier
        #[arg(long)]
        building: String,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
        /// Commit message
        #[arg(long)]
        message: Option<String>,
    },
    /// Filter building data
    Filter {
        /// Equipment type filter
        #[arg(long)]
        equipment_type: Option<String>,
        /// Equipment status filter
        #[arg(long)]
        status: Option<String>,
        /// Floor filter
        #[arg(long)]
        floor: Option<i32>,
        /// Room filter
        #[arg(long)]
        room: Option<String>,
        /// Building filter
        #[arg(long)]
        building: Option<String>,
        /// Show only critical equipment
        #[arg(long)]
        critical_only: bool,
        /// Show only healthy equipment
        #[arg(long)]
        healthy_only: bool,
        /// Show only equipment with alerts
        #[arg(long)]
        alerts_only: bool,
        /// Output format (table, json, yaml)
        #[arg(long, default_value = "table")]
        format: String,
        /// Maximum number of results
        #[arg(long, default_value = "100")]
        limit: usize,
    },
}

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
    },
    /// Delete a room
    Delete {
        /// Room ID or name
        room: String,
        /// Confirm deletion
        #[arg(long)]
        confirm: bool,
    },
}

#[derive(Subcommand)]
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
        /// Equipment properties (key=value)
        #[arg(long)]
        property: Vec<String>,
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
    },
    /// Remove equipment
    Remove {
        /// Equipment ID or name
        equipment: String,
        /// Confirm removal
        #[arg(long)]
        confirm: bool,
    },
}

#[derive(Subcommand)]
pub enum SpatialCommands {
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
