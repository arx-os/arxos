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
    /// Initialize a new building from scratch
    Init {
        /// Building name (required)
        #[arg(long)]
        name: String,
        /// Building description
        #[arg(long)]
        description: Option<String>,
        /// Location/address
        #[arg(long)]
        location: Option<String>,
        /// Initialize Git repository
        #[arg(long = "git-init")]
        git_init: bool,
        /// Commit initial building.yaml
        #[arg(long)]
        commit: bool,
        /// Coordinate system (default: World)
        #[arg(long, default_value = "World")]
        coordinate_system: String,
        /// Units (default: meters)
        #[arg(long, default_value = "meters")]
        units: String,
    },
    /// Import IFC file to Git repository
    Import {
        /// Path to IFC file
        ifc_file: String,
        /// Git repository URL
        #[arg(long)]
        repo: Option<String>,
        /// Dry run - show what would be done without making changes
        #[arg(long)]
        dry_run: bool,
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
        /// Output format (ascii, advanced, json, yaml)
        #[arg(long, default_value = "ascii")]
        format: String,
        /// Projection type for 3D rendering (isometric, orthographic, perspective)
        #[arg(long, default_value = "isometric")]
        projection: String,
        /// View angle for 3D rendering (topdown, front, side, isometric)
        #[arg(long, default_value = "isometric")]
        view_angle: String,
        /// Scale factor for 3D rendering
        #[arg(long, default_value = "1.0")]
        scale: f64,
        /// Enable spatial index integration for enhanced queries
        #[arg(long)]
        spatial_index: bool,
    },
    /// Interactive 3D building visualization with real-time controls
    Interactive {
        /// Building identifier
        #[arg(long)]
        building: String,
        /// Projection type (isometric, orthographic, perspective)
        #[arg(long, default_value = "isometric")]
        projection: String,
        /// View angle (topdown, front, side, isometric)
        #[arg(long, default_value = "isometric")]
        view_angle: String,
        /// Scale factor for rendering
        #[arg(long, default_value = "1.0")]
        scale: f64,
        /// Canvas width in characters
        #[arg(long, default_value = "120")]
        width: usize,
        /// Canvas height in characters
        #[arg(long, default_value = "40")]
        height: usize,
        /// Enable spatial index integration
        #[arg(long)]
        spatial_index: bool,
        /// Show equipment status indicators
        #[arg(long)]
        show_status: bool,
        /// Show room boundaries
        #[arg(long)]
        show_rooms: bool,
        /// Show equipment connections
        #[arg(long)]
        show_connections: bool,
        /// Target FPS for rendering
        #[arg(long, default_value = "30")]
        fps: u32,
        /// Show FPS counter
        #[arg(long)]
        show_fps: bool,
        /// Show help overlay by default
        #[arg(long)]
        show_help: bool,
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
    /// Stage changes in the working directory
    Stage {
        /// Stage all modified files (default behavior)
        #[arg(long)]
        all: bool,
        /// Specific file to stage
        file: Option<String>,
    },
    /// Commit staged changes
    Commit {
        /// Commit message
        message: String,
    },
    /// Unstage changes
    Unstage {
        /// Unstage all files
        #[arg(long)]
        all: bool,
        /// Specific file to unstage
        file: Option<String>,
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
    /// AR integration commands
    Ar {
        #[command(subcommand)]
        subcommand: ArCommands,
    },
    /// Process sensor data and update equipment status
    ProcessSensors {
        /// Directory containing sensor data files
        #[arg(long, default_value = "./sensor-data")]
        sensor_dir: String,
        
        /// Building name to update
        #[arg(long)]
        building: String,
        
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
        
        /// Watch mode: continuously monitor for new sensor data
        #[arg(long)]
        watch: bool,
    },
    /// IFC file processing commands
    IFC {
        #[command(subcommand)]
        subcommand: IFCCommands,
    },
    /// Run system health diagnostics
    Health {
        /// Check specific component (all, git, config, persistence, yaml)
        #[arg(long)]
        component: Option<String>,
        /// Show detailed diagnostics
        #[arg(long)]
        verbose: bool,
    },
    /// Generate HTML documentation for a building
    Doc {
        /// Building name to document
        #[arg(long)]
        building: String,
        /// Output file path (default: ./docs/{building}.html)
        #[arg(long)]
        output: Option<String>,
    },
    /// Gamified PR review and planning commands
    Game {
        #[command(subcommand)]
        subcommand: GameCommands,
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
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
    },
}

#[derive(Subcommand)]
pub enum GameCommands {
    /// Review a PR in game mode
    Review {
        /// PR ID to review
        pr_id: String,
        /// PR directory path (default: ./prs/pr_{pr_id})
        #[arg(long)]
        pr_dir: Option<String>,
        /// Building name
        #[arg(long)]
        building: String,
        /// Interactive mode with 3D visualization
        #[arg(long)]
        interactive: bool,
        /// Export review results to IFC file
        #[arg(long)]
        export_ifc: Option<String>,
    },
    /// Plan equipment placement in game mode
    Plan {
        /// Building name
        #[arg(long)]
        building: String,
        /// Interactive mode with 3D visualization
        #[arg(long)]
        interactive: bool,
        /// Export plan as PR to directory
        #[arg(long)]
        export_pr: Option<String>,
        /// Export plan to IFC file
        #[arg(long)]
        export_ifc: Option<String>,
    },
    /// Learn from historical PRs
    Learn {
        /// PR ID to learn from
        pr_id: String,
        /// PR directory path (default: ./prs/pr_{pr_id})
        #[arg(long)]
        pr_dir: Option<String>,
        /// Building name
        #[arg(long)]
        building: String,
    },
}

#[derive(Subcommand)]
pub enum IFCCommands {
    /// Extract building hierarchy from IFC file
    ExtractHierarchy {
        /// IFC file path
        #[arg(long)]
        file: String,
        /// Output YAML file path (optional)
        #[arg(long)]
        output: Option<String>,
    },
}

#[derive(Subcommand)]
pub enum ArCommands {
    /// Pending equipment management
    Pending {
        #[command(subcommand)]
        subcommand: PendingCommands,
    },
}

#[derive(Subcommand)]
pub enum PendingCommands {
    /// List all pending equipment
    List {
        /// Building name
        #[arg(long)]
        building: String,
        /// Filter by floor level
        #[arg(long)]
        floor: Option<i32>,
        /// Show detailed information
        #[arg(long)]
        verbose: bool,
    },
    /// Confirm pending equipment
    Confirm {
        /// Pending equipment ID
        pending_id: String,
        /// Building name
        #[arg(long)]
        building: String,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
    },
    /// Reject pending equipment
    Reject {
        /// Pending equipment ID
        pending_id: String,
    },
    /// Batch confirm multiple pending items
    BatchConfirm {
        /// Comma-separated list of pending IDs
        pending_ids: Vec<String>,
        /// Building name
        #[arg(long)]
        building: String,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
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
