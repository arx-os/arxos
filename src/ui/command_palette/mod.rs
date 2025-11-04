//! Command Palette for ArxOS TUI
//!
//! Provides:
//! - Command search and filtering (Ctrl+P)
//! - Fuzzy matching of commands
//! - Command execution from palette
//! - Command descriptions and categories

pub mod types;
pub mod commands;
pub mod palette;
pub mod render;
pub mod handler;

// Re-export public API
pub use types::{CommandEntry, CommandCategory};
pub use palette::CommandPalette;
pub use handler::handle_command_palette;

