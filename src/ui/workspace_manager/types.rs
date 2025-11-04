//! Workspace Manager Types
//!
//! Defines core types for the workspace management system.

use std::path::PathBuf;

/// Workspace/Building information
#[derive(Debug, Clone)]
pub struct Workspace {
    /// Building name
    pub name: String,
    /// Path to building.yaml file
    pub path: PathBuf,
    /// Git repository path (if applicable)
    pub git_repo: Option<PathBuf>,
    /// Description (from building.yaml)
    pub description: Option<String>,
}

