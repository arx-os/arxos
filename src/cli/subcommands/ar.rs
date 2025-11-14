//! AR integration and pending equipment commands

use clap::Subcommand;

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
