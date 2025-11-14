//! IFC file processing commands

use clap::Subcommand;

#[derive(Subcommand)]
pub enum IfcCommands {
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
