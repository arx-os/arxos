//! # Command Handlers
//!
//! This module provides handlers for different CLI commands,
//! organized by functionality (Git, Config, Room, Equipment, etc.).

pub mod git;
pub mod config;
pub mod room;
pub mod equipment;
pub mod spatial;
pub mod watch;

pub use git::*;
pub use config::*;
pub use room::*;
pub use equipment::*;
pub use spatial::*;
pub use watch::*;
