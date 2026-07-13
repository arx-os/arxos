//! Spatial query and validation commands (implemented verbs only).
//!
//! Unimplemented grid/relate theater was removed from the clap surface (CLI review C3).
//! Address-based discovery: `arx query`.

use clap::Subcommand;

#[derive(Subcommand)]
pub enum SpatialCommands {
    /// Query spatial relationships / nearest entities
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
    /// Transform coordinates for an entity between systems
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
