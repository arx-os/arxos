//! Command argument structures
//!
//! This module contains the argument structures for all CLI commands,
//! separated from the main Commands enum for better organization.

pub mod building;
pub mod git;
pub mod rendering;
pub mod data;
pub mod query;
pub mod maintenance;

pub use building::*;
pub use git::*;
pub use rendering::*;
pub use data::*;
pub use query::*;
pub use maintenance::*;
