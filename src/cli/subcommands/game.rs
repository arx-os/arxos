//! Gamified PR review and planning commands

use clap::Subcommand;

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
