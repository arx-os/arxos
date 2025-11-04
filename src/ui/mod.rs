//! ArxOS Terminal User Interface Module
//!
//! Provides reusable Ratatui components and patterns for interactive terminal experiences.
//! Designed for non-technical building management professionals.

pub mod terminal;
pub mod layouts;
pub mod theme;
pub mod widgets;
pub mod help;
pub mod error_modal;
pub mod error_integration;
pub mod mouse;
pub mod theme_manager;
pub mod export;
pub mod command_palette;
pub mod workspace_manager;

pub use terminal::TerminalManager;
pub use layouts::*;
pub use theme::{Theme, StatusColor};
pub use widgets::{StatusBadge, SummaryCard};
pub use help::{HelpSystem, HelpContext, Shortcut, ShortcutCategory, get_context_help, get_all_shortcuts, render_help_overlay, render_shortcut_cheat_sheet, handle_help_event};
pub use error_modal::{ErrorModal, ErrorAction, render_error_modal, handle_error_modal_event, calculate_modal_area};
pub use error_integration::{render_error_modal_in_frame, handle_error_with_modal, process_error_modal_event};
pub use mouse::{MouseAction, MouseConfig, parse_mouse_event, is_point_in_rect, find_clicked_list_item, find_clicked_table_cell, enable_mouse_support, disable_mouse_support};
pub use theme_manager::{ThemeManager, ThemeConfig, ThemePreset};
pub use export::{ExportFormat, export_buffer, export_current_view};
pub use command_palette::{CommandPalette, CommandEntry, CommandCategory, handle_command_palette};
pub use workspace_manager::{WorkspaceManager, Workspace, handle_workspace_manager};

