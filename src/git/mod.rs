//! Git operations for ArxOS
//!
//! This module provides Git repository management for building data version control.
//! The primary interface is `BuildingGitManager`, which provides comprehensive Git operations
//! including commits, diffs, history, and branch management.

pub mod commit;
pub mod diff;
pub mod export;
pub mod manager;
pub mod repository;
pub mod staging;

// Re-export types and main manager
pub use diff::{CommitInfo, DiffResult, DiffStats, GitStatus};
pub use manager::CommitMetadata;
pub use manager::*;

