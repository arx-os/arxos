//! Spatial query and coordinate transformation commands

use clap::Subcommand;

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
