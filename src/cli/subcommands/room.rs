//! Room management commands

use clap::Subcommand;

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
