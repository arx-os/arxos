//! ArxUI crate - terminal UI and rendering components built atop ArxOS core.
//! Provides ASCII/TUI dashboards, interactive 3D rendering, and documentation
//! generation utilities that operate on `arx` data structures.

pub mod cli;
pub mod commands;
pub mod docs;
pub mod render;
#[cfg(feature = "render3d")]
pub mod render3d;
pub mod tui;

pub use arx::{
    config, core, depin, domain, error, git, identity, ifc, persistence, spatial, utils, yaml,
};
pub use arxos::{ar_integration, export, game, hardware, mobile_ffi, query, search, services};

pub use docs::generate_building_docs;
pub use render::BuildingRenderer;
#[cfg(feature = "render3d")]
pub use render3d::{
    animation, effects, events, info_panel, interactive, particles, state, Building3DRenderer,
};
pub use tui::{
    command_palette, error_integration, error_modal, export as ui_export, help, layouts, mouse,
    spreadsheet, terminal::TerminalManager, theme::Theme, theme_manager::ThemeManager, users,
    widgets, workspace_manager, CommandEntry, CommandPalette, ExportFormat, HelpContext,
    HelpSystem, Shortcut, StatusBadge, SummaryCard, ThemeConfig, ThemePreset,
};
