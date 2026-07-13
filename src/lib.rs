//! ArxOS - Git for Buildings
//!
//! Core library providing building data management, terminal UI,
//! and collaborative workflows using Git as the foundation.
//!
//! This library can be used independently of the CLI binary.

// Core modules (always available) — building compiler spine
pub mod access;
pub mod config;
pub mod contribution;
pub mod core;
pub mod error;
pub mod export;
pub mod git;
pub mod ifc;
pub mod ingest;
pub mod persistence;
pub mod resource_limits;
pub mod spatial;
pub mod utils;
pub mod validation;
pub mod yaml;

// CLI module (public for testing)
pub mod cli;

// Feature-gated optional rings
#[cfg(feature = "tui")]
pub mod tui;

#[cfg(feature = "agent")]
pub mod agent;

#[cfg(feature = "blockchain")]
pub mod blockchain;

#[cfg(feature = "web")]
pub mod web;

// Re-export commonly used types
pub use core::{Building, Equipment, Floor, Room, Wing};
pub use error::ArxError;
