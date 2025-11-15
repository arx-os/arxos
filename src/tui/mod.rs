//! ArxOS Terminal User Interface Module
//!
//! Provides reusable Ratatui components and patterns for interactive terminal experiences.
//! Designed for non-technical building management professionals.

pub mod command_palette;
pub mod error_integration;
pub mod error_modal;
pub mod export;
pub mod help;
pub mod layouts;
pub mod merge_tool;
pub mod mouse;
pub mod spreadsheet;
pub mod terminal;
pub mod theme;
pub mod theme_manager;
pub mod users;
pub mod widgets;
pub mod workspace_manager;

pub use error_modal::{
    handle_error_modal_event, render_error_modal, ErrorAction, ErrorModal,
};
pub use help::{
    handle_help_event, render_help_overlay, HelpContext, HelpSystem,
};
pub use terminal::TerminalManager;
pub use theme::{StatusColor, Theme};

/// Simple building renderer for ASCII output
pub fn render_building(building_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("🏠 Rendering building: {}", building_name);
    println!("📐 ASCII mode renderer placeholder");
    Ok(())
}
