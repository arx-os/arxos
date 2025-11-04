//! Workspace Management for ArxOS TUI
//!
//! Provides:
//! - List available buildings/workspaces
//! - Switch active workspace
//! - Multi-building navigation

pub mod types;
pub mod discovery;
pub mod manager;
pub mod render;
pub mod handler;

// Re-export public API
pub use types::Workspace;
pub use manager::WorkspaceManager;
pub use handler::handle_workspace_manager;

