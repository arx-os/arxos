//! Command Palette for ArxOS TUI
//!
//! Provides:
//! - Command search and filtering (Ctrl+P)
//! - Fuzzy matching of commands
//! - Command execution from palette
//! - Command descriptions and categories

pub mod commands;
pub mod handler;
pub mod palette;
pub mod render;
pub mod types;

// Re-export public API
pub use handler::handle_command_palette;
pub use palette::CommandPalette;
pub use types::{CommandCategory, CommandEntry};
