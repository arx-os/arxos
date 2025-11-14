//! Equipment management commands

use clap::Subcommand;

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
