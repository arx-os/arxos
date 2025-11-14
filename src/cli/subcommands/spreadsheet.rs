//! Spreadsheet interface commands

use clap::Subcommand;

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
