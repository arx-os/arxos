//! Building command arguments
//!
//! Argument structures for building-related CLI commands including
//! initialization, export, and synchronization.

use clap::Args;

/// Arguments for the Init command
///
/// Initialize a new building from scratch with optional Git integration.
#[derive(Debug, Clone, Args)]
pub struct InitArgs {
    /// Building name (required)
    #[arg(long)]
    pub name: String,

    /// Building description
    #[arg(long)]
    pub description: Option<String>,

    /// Location/address
    #[arg(long)]
    pub location: Option<String>,

    /// Initialize Git repository
    #[arg(long = "git-init")]
    pub git_init: bool,

    /// Commit initial building.yaml
    #[arg(long)]
    pub commit: bool,

    /// Coordinate system (default: World)
    #[arg(long, default_value = "World")]
    pub coordinate_system: String,

    /// Units (default: meters)
    #[arg(long, default_value = "meters")]
    pub units: String,
}

/// Arguments for the Export command
///
/// Export building data to Git repository or other formats.
#[derive(Debug, Clone, Args)]
pub struct ExportArgs {
    /// Export format (git, ifc, gltf, usdz)
    #[arg(long, default_value = "git")]
    pub format: String,

    /// Output file path (required for non-git formats)
    #[arg(long)]
    pub output: Option<String>,

    /// Git repository URL (required for git format)
    #[arg(long)]
    pub repo: Option<String>,

    /// Export only changes (delta mode)
    #[arg(long)]
    pub delta: bool,
}

/// Arguments for the Sync command
///
/// Sync building data to IFC file (continuous or one-time).
#[derive(Debug, Clone, Args)]
pub struct SyncArgs {
    /// Path to IFC file
    #[arg(long)]
    pub ifc: Option<String>,

    /// Enable watch mode (daemon) for continuous sync
    #[arg(long)]
    pub watch: bool,

    /// Export only changes (delta mode)
    #[arg(long)]
    pub delta: bool,
}

/// Arguments for the Import command
///
/// Import IFC file to Git repository.
#[derive(Debug, Clone, Args)]
pub struct ImportArgs {
    /// Path to IFC file
    pub ifc_file: String,

    /// Git repository URL
    #[arg(long)]
    pub repo: Option<String>,

    /// Dry run - show what would be done without making changes
    #[arg(long)]
    pub dry_run: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_init_args_defaults() {
        // This test verifies that the Args derive works correctly
        // Actual parsing would need clap's testing utilities
    }
}
