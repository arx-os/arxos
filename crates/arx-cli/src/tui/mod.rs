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
pub mod mouse;
pub mod spreadsheet;
pub mod terminal;
pub mod theme;
pub mod theme_manager;
pub mod users;
pub mod widgets;
pub mod workspace_manager;

pub use command_palette::{handle_command_palette, CommandCategory, CommandEntry, CommandPalette};
pub use error_integration::{
    handle_error_with_modal, process_error_modal_event, render_error_modal_in_frame,
};
pub use error_modal::{
    calculate_modal_area, handle_error_modal_event, render_error_modal, ErrorAction, ErrorModal,
};
pub use export::{export_buffer, export_current_view, ExportFormat};
pub use help::{
    get_all_shortcuts, get_context_help, handle_help_event, render_help_overlay,
    render_shortcut_cheat_sheet, HelpContext, HelpSystem, Shortcut, ShortcutCategory,
};
pub use layouts::*;
pub use mouse::{
    disable_mouse_support, enable_mouse_support, find_clicked_list_item, find_clicked_table_cell,
    is_point_in_rect, parse_mouse_event, MouseAction, MouseConfig,
};
pub use terminal::TerminalManager;
pub use theme::{StatusColor, Theme};
pub use theme_manager::{ThemeConfig, ThemeManager, ThemePreset};
pub use users::handle_user_browser;
pub use widgets::{StatusBadge, SummaryCard};
pub use workspace_manager::{handle_workspace_manager, Workspace, WorkspaceManager};
