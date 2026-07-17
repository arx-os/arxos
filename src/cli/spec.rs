//! Clap command schema for `arx`.
//!
//! Help order is intentional: compiler spine → model → git → UI → lab → agent.
//! Keep dispatch in `cli::mod` so this file stays schema-only.

use clap::Subcommand;

#[cfg(feature = "agent")]
use crate::cli::commands::RemoteCommand;
use crate::cli::subcommands::{EquipmentCommands, RoomCommands, SpatialCommands};

/// Top-level `arx` subcommands (order = `--help` order).
#[derive(Subcommand)]
pub enum Commands {
    // ── Compiler spine (L1) ─────────────────────────────────────────────
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
        /// Legacy flag (Git init is now the default). Kept so old scripts do not fail.
        #[arg(long = "git-init", hide = true)]
        git_init: bool,
        /// Skip Git repository initialization
        #[arg(long = "no-git")]
        no_git: bool,
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
    /// Import IFC, LiDAR, or text script into building.yaml
    Import {
        #[command(subcommand)]
        subcommand: ImportSubcommand,
    },
    /// Apply text / AR command script to a building YAML
    Edit {
        /// Script file path, or "-" for stdin
        script: String,
        /// Building YAML path or name
        #[arg(long)]
        building: Option<String>,
        /// Show result without writing
        #[arg(long)]
        dry_run: bool,
    },
    /// Validate building.yaml
    Validate {
        /// Path to project root containing building.yaml
        #[arg(long)]
        path: Option<String>,
        /// Enable strict address prefix checking
        #[arg(long)]
        strict_addresses: bool,
    },
    /// Export building SSOT (IFC is the compiler interchange spine)
    ///
    /// IFC export uses `export::ifc` only — review-gated, deterministic GlobalIds.
    /// Vendor BIM: export clean IFC from the CAD tool, then `arx import ifc`.
    /// No CAD plugins. Agent/daemon is not the L1 export authority.
    #[command(long_about = "\
Export the durable Building model (building.yaml).

IFC (`--format ifc`) is the only official industry interchange path. It runs
through export::ifc with review warnings and optional --approved-only.

BIM policy: ArxOS is IFC-only — no Revit/ArchiCAD plugins. Vendor tools must
export clean IFC for import.

Official pilot handoffs: `arx export --format ifc` (not agent auto-export).
Use --path to select a project root without changing cwd.")]
    Export {
        /// Export format: ifc (recommended), yaml, json
        #[arg(long, default_value = "ifc")]
        format: String,
        /// Output file path
        #[arg(long)]
        output: Option<String>,
        /// Project root containing building.yaml (default: cwd)
        #[arg(long)]
        path: Option<String>,
        /// Git repository URL (legacy; prefer arx commit for SSOT)
        #[arg(long)]
        repo: Option<String>,
        /// Exclude proposed/rejected LiDAR auto entities from IFC export
        #[arg(long)]
        approved_only: bool,
        /// Commercial export: require access-receipt.json proving $AXD payment (N7 host gate)
        #[arg(long)]
        commercial: bool,
        /// Path to access receipt JSON (default: access-receipt.json)
        #[arg(long)]
        access_receipt: Option<String>,
    },
    /// Query equipment by durable ArxAddress glob
    ///
    /// Examples:
    ///   arx query "/usa/ny/*/floor-*/mech/boiler-*"
    ///   arx query "/local/local/local/*/*/*/*"
    Query {
        /// ArxAddress glob pattern with wildcards
        pattern: String,
        /// Output format (table, json, yaml)
        #[arg(long, default_value = "table")]
        format: String,
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
    },
    /// Backfill missing ArxAddress fields on equipment
    Migrate {
        /// Preview changes without writing
        #[arg(long)]
        dry_run: bool,
    },

    // ── Model CRUD ──────────────────────────────────────────────────────
    /// Room management
    Room {
        #[command(subcommand)]
        command: RoomCommands,
    },
    /// Equipment management
    Equipment {
        #[command(subcommand)]
        command: EquipmentCommands,
    },
    /// Spatial query / transform / validate (implemented verbs only)
    Spatial {
        #[command(subcommand)]
        command: SpatialCommands,
    },

    // ── Git ─────────────────────────────────────────────────────────────
    /// Show repository status
    Status {
        /// Show detailed status information
        #[arg(long)]
        verbose: bool,
        /// Open interactive dashboard (requires tui+agent)
        #[arg(long)]
        interactive: bool,
    },
    /// Stage changes
    Stage {
        /// Stage all modified files (default behavior)
        #[arg(long)]
        all: bool,
        /// Specific file to stage
        file: Option<String>,
    },
    /// Unstage changes
    Unstage {
        /// Unstage all files
        #[arg(long)]
        all: bool,
        /// Specific file to unstage
        file: Option<String>,
    },
    /// Commit staged changes
    Commit {
        /// Commit message (positional)
        #[arg(value_name = "MESSAGE")]
        message: Option<String>,
        /// Commit message (git-style; preferred for field techs)
        #[arg(short = 'm', long = "message", value_name = "MESSAGE")]
        message_flag: Option<String>,
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

    // ── UI (default feature `tui`) ──────────────────────────────────────
    /// Search building data by name
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
    /// Print building hierarchy as text (not LiDAR point-cloud viz)
    #[cfg(feature = "tui")]
    Render {
        /// Building name or id (loaded from cwd building.yaml)
        #[arg(long)]
        building: String,
    },
    /// Resolve merge conflicts interactively
    #[cfg(feature = "tui")]
    Merge(crate::cli::commands::MergeCommand),
    /// Launch agent dashboard
    #[cfg(all(feature = "tui", feature = "agent"))]
    Dashboard,

    // ── Lab economy (not L1 success criteria) ───────────────────────────
    /// Package verified building data as a contribution claim (lab; not L1-required)
    Contribute {
        /// Output JSON path
        #[arg(long, default_value = "contribution.json")]
        output: String,
        /// Optional site latitude for location hash
        #[arg(long)]
        latitude: Option<f64>,
        /// Optional site longitude for location hash
        #[arg(long)]
        longitude: Option<f64>,
        /// Bind package to an explicit Git commit oid (default: HEAD if repo)
        #[arg(long)]
        git_commit: Option<String>,
        /// Allow packaging even if validation has errors (not for mint path)
        #[arg(long)]
        allow_invalid: bool,
        /// Print package summary without writing a file
        #[arg(long)]
        dry_run: bool,
        /// EIP-712 sign package (requires --features blockchain)
        #[arg(long)]
        sign: bool,
        /// Private key hex or env var name (default: ARX_PRIVATE_KEY or Anvil #0)
        #[arg(long)]
        private_key: Option<String>,
        /// Oracle contract address for EIP-712 domain / submit
        #[arg(long)]
        oracle: Option<String>,
        /// Chain id (31337 = Anvil local)
        #[arg(long, default_value = "31337")]
        chain_id: u64,
        /// Submit proposeContribution via RPC (oracle role + stake required)
        #[arg(long)]
        submit: bool,
        /// Worker wallet that performed the field labor
        #[arg(long)]
        worker: Option<String>,
        /// Whole $AXD amount to propose for mint
        #[arg(long, default_value = "100")]
        amount: u64,
        /// RPC URL for --submit
        #[arg(long)]
        rpc_url: Option<String>,
    },
    /// Buyer market: quote / grant receipt / pay $AXD (lab; not L1-required)
    Access {
        #[command(subcommand)]
        subcommand: AccessSubcommand,
    },

    // ── Agent ring ──────────────────────────────────────────────────────
    /// Manage remote building connections via SSH
    #[cfg(feature = "agent")]
    Remote(RemoteCommand),
    /// Manage building ownership claims and review pending grace contributions
    #[cfg(feature = "agent")]
    Claim {
        /// Building ID/UUID
        #[arg(long)]
        building_id: String,
        /// Approve (true) or reject (false) the pending contribution
        #[arg(long)]
        approve: Option<bool>,
        /// Index of the pending contribution to review
        #[arg(long)]
        pending_index: Option<usize>,
        /// Enable live blockchain reward distribution
        #[arg(long)]
        live: bool,
    },
}

#[derive(Subcommand)]
pub enum AccessSubcommand {
    /// Create an access request JSON (building id + nonce) for the data market
    Quote {
        /// Building UUID (default: load from building.yaml)
        #[arg(long)]
        building_id: Option<String>,
        /// Whole $AXD to offer
        #[arg(long, default_value = "1")]
        amount: u64,
        /// Output path
        #[arg(long, default_value = "access-request.json")]
        output: String,
    },
    /// Record access-receipt.json from a known payment tx (N7 host gate)
    Grant {
        /// Building UUID (default: from building.yaml)
        #[arg(long)]
        building_id: Option<String>,
        /// Payment transaction hash
        #[arg(long)]
        tx_hash: String,
        /// Output path
        #[arg(long, default_value = "access-receipt.json")]
        output: String,
    },
    /// Pay $AXD on-chain via ArxPaymentRouter (requires --features blockchain)
    Pay {
        /// Building UUID (or use --request)
        #[arg(long)]
        building_id: Option<String>,
        /// Whole $AXD amount
        #[arg(long, default_value = "1")]
        amount: u64,
        /// Hex nonce (or from --request)
        #[arg(long)]
        nonce: Option<String>,
        /// Path to access-request.json from `arx access quote`
        #[arg(long)]
        request: Option<String>,
        /// Buyer private key or env name
        #[arg(long)]
        private_key: Option<String>,
        /// Payment router address
        #[arg(long)]
        router: Option<String>,
        /// $AXD token address
        #[arg(long)]
        token: Option<String>,
        /// RPC URL
        #[arg(long)]
        rpc_url: Option<String>,
        /// Chain id
        #[arg(long, default_value = "31337")]
        chain_id: u64,
    },
}

#[derive(Subcommand)]
pub enum ImportSubcommand {
    /// Import IFC (vendor BIM → clean IFC export → arx)
    Ifc {
        /// Path to IFC file
        ifc_file: String,
        /// Git repository URL
        #[arg(long)]
        repo: Option<String>,
        /// Dry run - show what would be done without making changes
        #[arg(long)]
        dry_run: bool,
        /// Enable strict validation (fail on missing spatial entities)
        #[arg(long)]
        strict: bool,
        /// Enable strict address prefix checking
        #[arg(long)]
        strict_addresses: bool,
    },
    /// Import LiDAR point cloud (assistive structure; review proposed entities)
    Lidar {
        /// Path to PLY, LAS, or CSV/XYZ file
        file_path: String,
        /// Voxel size in meters for downsampling
        #[arg(long, default_value = "0.05")]
        voxel_size: f64,
        /// Enable light mode (aggressive downsampling & lower memory limits)
        #[arg(long)]
        light: bool,
        /// Dry run - parse and downsample without writing to disk
        #[arg(long)]
        dry_run: bool,
        /// Merge into an existing building instead of creating new
        #[arg(long)]
        merge: bool,
        /// Name of the existing building to merge into
        #[arg(long)]
        building: Option<String>,
    },
    /// Apply a text / AR command script (same as `arx edit`)
    Text {
        /// Script file path, or "-" for stdin
        script: String,
        /// Building YAML path or name
        #[arg(long)]
        building: Option<String>,
        /// Show result without writing
        #[arg(long)]
        dry_run: bool,
    },
}
