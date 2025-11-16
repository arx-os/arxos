//! ArxOS - Git for Buildings
//!
//! Core library providing building data management, 3D visualization,
//! and collaborative workflows using Git as the foundation.
//!
//! This library can be used independently of the CLI binary.

// Core modules (always available)
pub mod config;
pub mod core;
pub mod error;
pub mod ifc;
pub mod git;
pub mod persistence;
pub mod sensor;
pub mod utils;
pub mod validation;
pub mod yaml;

// CLI module (public for testing)
pub mod cli;

// Feature-gated modules
#[cfg(feature = "tui")]
pub mod tui;

#[cfg(feature = "render3d")]
pub mod render3d;

#[cfg(feature = "agent")]
pub mod agent;

// Re-export commonly used types
pub use error::ArxError;
pub use core::{Building, Equipment, Floor, Room, Wing};
