//! # CLI Utilities
//!
//! This module provides utility functions and common patterns used across
//! the ArxOS CLI application, including file operations, data loading,
//! and common display formatting.

pub mod file_ops;
pub mod display;
pub mod validation;

pub use file_ops::*;
pub use display::*;
pub use validation::*;
