//! Workspace Management for ArxOS TUI
//!
//! Provides:
//! - List available buildings/workspaces
//! - Switch active workspace
//! - Multi-building navigation

pub mod discovery;
pub mod handler;
pub mod manager;
pub mod render;
pub mod types;

// Re-export public API
pub use handler::handle_workspace_manager;
pub use manager::WorkspaceManager;
pub use types::Workspace;
