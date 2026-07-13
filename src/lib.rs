//! ArxOS - Git for Buildings
//!
//! Core library providing building data management, 3D visualization,
//! and collaborative workflows using Git as the foundation.
//!
//! This library can be used independently of the CLI binary.

// Core modules (always available)
pub mod config;
pub mod contribution;
pub mod core;
pub mod error;
pub mod export;
pub mod git;
pub mod hardware;
pub mod ifc;
pub mod ingest;
pub mod persistence;
pub mod sensor;
pub mod spatial;
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

#[cfg(feature = "blockchain")]
pub mod blockchain;

#[cfg(feature = "web")]
pub mod web;

// Re-export commonly used types
pub use core::{Building, Equipment, Floor, Room, Wing};
pub use error::ArxError;
