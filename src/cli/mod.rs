// CLI module for ArxOS
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "arx")]
#[command(about = "ArxOS - Git for Buildings")]
#[command(version = env!("CARGO_PKG_VERSION"))]
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
    /// Export building data to Git repository or other formats
    Export {
        /// Export format (git, ifc, gltf, usdz)
        #[arg(long, default_value = "git")]
        format: String,
        /// Output file path (required for non-git formats)
        #[arg(long)]
        output: Option<String>,
        /// Git repository URL (required for git format)
        #[arg(long)]
        repo: Option<String>,
        /// Export only changes (delta mode)
        #[arg(long)]
        delta: bool,
    },
    /// Sync building data to IFC file (continuous or one-time)
    Sync {
        /// Path to IFC file
        #[arg(long)]
        ifc: Option<String>,
        /// Enable watch mode (daemon) for continuous sync
        #[arg(long)]
        watch: bool,
        /// Export only changes (delta mode)
        #[arg(long)]
        delta: bool,
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
        /// Target FPS for rendering (1-240)
        #[arg(long, default_value = "30", value_parser = |s: &str| -> Result<u32, String> {
            let val: u32 = s.parse().map_err(|_| format!("must be a number between 1 and 240"))?;
            if val < 1 || val > 240 {
                Err(format!("FPS must be between 1 and 240, got {}", val))
            } else {
                Ok(val)
            }
        })]
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
        /// Open interactive dashboard
        #[arg(long)]
        interactive: bool,
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
        /// Open interactive viewer
        #[arg(long)]
        interactive: bool,
    },
    /// Show commit history
    History {
        /// Number of commits to show (1-1000)
        #[arg(long, default_value = "10", value_parser = |s: &str| -> Result<usize, String> {
            let val: usize = s.parse().map_err(|_| format!("must be a number between 1 and 1000"))?;
            if val < 1 || val > 1000 {
                Err(format!("Limit must be between 1 and 1000, got {}", val))
            } else {
                Ok(val)
            }
        })]
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
        /// Open interactive wizard
        #[arg(long)]
        interactive: bool,
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
        /// Refresh interval in seconds (1-3600)
        #[arg(long, default_value = "5", value_parser = |s: &str| -> Result<u64, String> {
            let val: u64 = s.parse().map_err(|_| format!("must be a number between 1 and 3600"))?;
            if val < 1 || val > 3600 {
                Err(format!("Refresh interval must be between 1 and 3600 seconds, got {}", val))
            } else {
                Ok(val)
            }
        })]
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
        /// Maximum number of results (1-10000)
        #[arg(long, default_value = "50", value_parser = |s: &str| -> Result<usize, String> {
            let val: usize = s.parse().map_err(|_| format!("must be a number between 1 and 10000"))?;
            if val < 1 || val > 10000 {
                Err(format!("Limit must be between 1 and 10000, got {}", val))
            } else {
                Ok(val)
            }
        })]
        limit: usize,
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
        /// Open interactive browser
        #[arg(long)]
        interactive: bool,
    },
    /// Query equipment by ArxAddress glob pattern
    /// 
    /// Query equipment matching an ArxAddress path pattern using glob wildcards (*).
    /// Supports hierarchical path queries: /country/state/city/building/floor/room/fixture
    /// 
    /// # Examples
    /// 
    /// ```bash
    /// # Find all boilers in mech rooms on any floor
    /// arx query "/usa/ny/*/floor-*/mech/boiler-*"
    /// 
    /// # Find all equipment in kitchen on floor 02
    /// arx query "/usa/ny/brooklyn/ps-118/floor-02/kitchen/*"
    /// 
    /// # Find all HVAC equipment in any city
    /// arx query "/usa/ny/*/ps-118/floor-*/hvac/*"
    /// ```
    Query {
        /// ArxAddress glob pattern with wildcards (e.g., "/usa/ny/*/floor-*/mech/boiler-*")
        pattern: String,
        /// Output format (table, json, yaml)
        #[arg(long, default_value = "table")]
        format: String,
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
    },
    /// Integrate AR scan data
    /// 
    /// **Note:** This command directly integrates AR scans without user review.
    /// For mobile apps, consider using `ar pending` workflow instead.
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
    /// Start HTTP server for real-time sensor data ingestion
    SensorsHttp {
        /// Building name to update
        #[arg(long)]
        building: String,
        
        /// Host address to bind to
        #[arg(long, default_value = "127.0.0.1")]
        host: String,
        
        /// Port to listen on (1-65535)
        #[arg(long, default_value = "3000", value_parser = |s: &str| -> Result<u16, String> {
            let val: u16 = s.parse().map_err(|_| format!("must be a number between 1 and 65535"))?;
            if val == 0 {
                Err(format!("Port must be between 1 and 65535, got 0"))
            } else {
                Ok(val)
            }
        })]
        port: u16,
    },
    /// Start MQTT subscriber for real-time sensor data ingestion
    SensorsMqtt {
        /// Building name to update
        #[arg(long)]
        building: String,
        
        /// MQTT broker URL
        #[arg(long, default_value = "localhost")]
        broker: String,
        
        /// MQTT broker port
        #[arg(long, default_value = "1883")]
        port: u16,
        
        /// MQTT username (optional)
        #[arg(long)]
        username: Option<String>,
        
        /// MQTT password (optional)
        #[arg(long)]
        password: Option<String>,
        
        /// MQTT topics to subscribe to (comma-separated)
        #[arg(long, default_value = "arxos/sensors/#")]
        topics: String,
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
        /// Open interactive dashboard
        #[arg(long)]
        interactive: bool,
        /// Generate comprehensive diagnostic report
        #[arg(long)]
        diagnostic: bool,
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
    /// Spreadsheet interface for editing building data
    Spreadsheet {
        #[command(subcommand)]
        subcommand: SpreadsheetCommands,
    },
    /// User management commands (admin permissions required for verify/revoke)
    /// 
    /// The first user added to the registry automatically becomes an admin with
    /// 'verify_users' and 'revoke_users' permissions. Only admins can verify or
    /// revoke other users.
    Users {
        #[command(subcommand)]
        subcommand: UsersCommands,
    },
    /// Verify GPG signatures on Git commits
    /// 
    /// Checks commit signatures and displays verification status.
    /// Requires GPG to be configured and public keys to be available.
    Verify {
        /// Commit hash to verify (default: HEAD)
        #[arg(long)]
        commit: Option<String>,
        /// Verify all commits in current branch
        #[arg(long)]
        all: bool,
        /// Show detailed verification information
        #[arg(long)]
        verbose: bool,
    },
    /// Migrate existing fixtures to ArxAddress format
    /// 
    /// One-shot migration that fills address: for every existing fixture
    /// in building YAML files by inferring from grid/floor/room data.
    /// Old data becomes instantly searchable with the new address system.
    Migrate {
        /// Show what would be migrated without making changes
        #[arg(long)]
        dry_run: bool,
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
    /// Export building to AR format (glTF/USDZ)
    Export {
        /// Building name
        #[arg(long)]
        building: String,
        /// AR format (gltf, usdz)
        #[arg(long, default_value = "gltf")]
        format: String,
        /// Output file path
        #[arg(long, default_value = "output.gltf")]
        output: String,
        /// Include spatial anchors
        #[arg(long)]
        anchors: bool,
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
        /// Open interactive manager
        #[arg(long)]
        interactive: bool,
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

#[derive(Subcommand)]
pub enum SpreadsheetCommands {
    /// Open equipment spreadsheet
    Equipment {
        /// Building name (default: current directory)
        #[arg(long)]
        building: Option<String>,
        /// Pre-filter data (e.g., "status=Active")
        #[arg(long)]
        filter: Option<String>,
        /// Auto-commit on save (default: stage only)
        #[arg(long)]
        commit: bool,
        /// Disable Git integration (read-only mode)
        #[arg(long = "no-git")]
        no_git: bool,
    },
    /// Open room spreadsheet
    Rooms {
        /// Building name (default: current directory)
        #[arg(long)]
        building: Option<String>,
        /// Pre-filter data (e.g., "floor=2")
        #[arg(long)]
        filter: Option<String>,
        /// Auto-commit on save (default: stage only)
        #[arg(long)]
        commit: bool,
        /// Disable Git integration (read-only mode)
        #[arg(long = "no-git")]
        no_git: bool,
    },
    /// Open sensor data spreadsheet
    Sensors {
        /// Building name (default: current directory)
        #[arg(long)]
        building: Option<String>,
        /// Pre-filter data
        #[arg(long)]
        filter: Option<String>,
        /// Auto-commit on save (default: stage only)
        #[arg(long)]
        commit: bool,
        /// Disable Git integration (read-only mode)
        #[arg(long = "no-git")]
        no_git: bool,
    },
    /// Import CSV and open as spreadsheet
    Import {
        /// CSV file path
        #[arg(long)]
        file: String,
        /// Building name (for saving)
        #[arg(long)]
        building: Option<String>,
        /// Auto-commit on save (default: stage only)
        #[arg(long)]
        commit: bool,
    },
}

#[derive(Subcommand)]
pub enum UsersCommands {
    /// Add user to registry
    /// 
    /// If --verify is used, requires 'verify_users' permission (admin only).
    /// The first user added automatically becomes an admin with all permissions.
    Add {
        /// User's full name
        #[arg(long)]
        name: String,
        /// User's email address
        #[arg(long)]
        email: String,
        /// Organization (optional)
        #[arg(long)]
        organization: Option<String>,
        /// Role (optional)
        #[arg(long)]
        role: Option<String>,
        /// Phone number (optional, for privacy)
        #[arg(long)]
        phone: Option<String>,
        /// Verify user immediately (requires 'verify_users' permission)
        #[arg(long)]
        verify: bool,
    },
    /// List all registered users
    List,
    /// Interactive user browser (TUI)
    Browse,
    /// Show user details
    Show {
        /// User email
        email: String,
    },
    /// Verify a user (admin only - requires 'verify_users' permission)
    /// 
    /// Only users with the 'verify_users' permission can verify other users.
    /// The first user in the registry automatically receives admin permissions.
    Verify {
        /// User email to verify
        email: String,
    },
    /// Revoke user access (admin only - requires 'revoke_users' permission)
    /// 
    /// Only users with the 'revoke_users' permission can revoke user access.
    /// The first user in the registry automatically receives admin permissions.
    Revoke {
        /// User email to revoke
        email: String,
    },
    /// Approve a pending user registration request (admin only)
    /// 
    /// Approves a pending request from a mobile user and adds them to the user registry.
    /// Requires 'verify_users' permission.
    Approve {
        /// User email from pending request
        email: String,
    },
    /// Deny a pending user registration request (admin only)
    /// 
    /// Denies a pending request from a mobile user.
    /// Requires 'verify_users' permission.
    Deny {
        /// User email from pending request
        email: String,
        /// Reason for denial (optional)
        #[arg(long)]
        reason: Option<String>,
    },
    /// List all pending user registration requests
    Pending,
}

#[derive(Subcommand)]
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
