//! Help Content
//!
//! Provides context-specific help content for all screens.

use super::types::HelpContext;
use ratatui::{
    style::{Color, Modifier, Style},
    text::{Line, Span},
};

/// Get context-specific help content
pub fn get_context_help(context: HelpContext) -> Vec<Line<'static>> {
    match context {
        HelpContext::EquipmentBrowser => equipment_browser_help(),
        HelpContext::RoomExplorer => room_explorer_help(),
        HelpContext::StatusDashboard => status_dashboard_help(),
        HelpContext::SearchBrowser => search_browser_help(),
        HelpContext::WatchDashboard => watch_dashboard_help(),
        HelpContext::ConfigWizard => config_wizard_help(),
        HelpContext::ArPendingManager => ar_pending_manager_help(),
        HelpContext::DiffViewer => diff_viewer_help(),
        HelpContext::HealthDashboard => health_dashboard_help(),
        HelpContext::CommandPalette => command_palette_help(),
        HelpContext::Interactive3D => interactive_3d_help(),
        HelpContext::General => general_help(),
    }
}

fn equipment_browser_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Equipment Browser Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ↑/↓ or j/k - Navigate equipment list")),
        Line::from(Span::raw("  Enter - View equipment details")),
        Line::from(Span::raw("  / - Search equipment")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  f - Filter by type/status")),
        Line::from(Span::raw("  s - Sort by column")),
        Line::from(Span::raw("  e - Edit selected equipment")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn room_explorer_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Room Explorer Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  → or l - Expand node")),
        Line::from(Span::raw("  ← or h - Collapse node")),
        Line::from(Span::raw("  ↑/↓ or j/k - Navigate tree")),
        Line::from(Span::raw("  Enter - View room details")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  f - Filter by room type")),
        Line::from(Span::raw("  / - Search rooms")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn status_dashboard_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Status Dashboard Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  Tab - Switch between sections")),
        Line::from(Span::raw("  ↑/↓ - Navigate items")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  r - Refresh data")),
        Line::from(Span::raw("  Enter - View details")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn search_browser_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Search Browser Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ↑/↓ or j/k - Navigate results")),
        Line::from(Span::raw("  Enter - View result details")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  / - New search")),
        Line::from(Span::raw("  f - Filter by type")),
        Line::from(Span::raw("  e - Export selected")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn watch_dashboard_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Watch Dashboard Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  Tab/←/→ - Switch tabs")),
        Line::from(Span::raw("  ↑/↓ - Navigate items")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  r - Refresh data")),
        Line::from(Span::raw("  f - Filter by room/floor")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn config_wizard_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Configuration Wizard Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  Tab/Shift+Tab - Switch sections")),
        Line::from(Span::raw("  ↑/↓ - Navigate fields")),
        Line::from(Span::raw("  Enter - Edit field")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  s - Save configuration")),
        Line::from(Span::raw("  p - Preview changes")),
        Line::from(Span::raw("  r - Reset to defaults")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn ar_pending_manager_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("AR Pending Manager Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ↑/↓ or j/k - Navigate pending items")),
        Line::from(Span::raw("  Enter - View details")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  y - Confirm selected")),
        Line::from(Span::raw("  n - Reject selected")),
        Line::from(Span::raw("  e - Edit before confirming")),
        Line::from(Span::raw("  b - Batch select multiple")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn diff_viewer_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Diff Viewer Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ←/→ or n/p - Navigate hunks")),
        Line::from(Span::raw("  ↑/↓ or j/k - Navigate files")),
        Line::from(Span::raw("  Enter - Select file")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  t - Toggle view mode (side-by-side/unified)")),
        Line::from(Span::raw("  c - Collapse/expand hunk")),
        Line::from(Span::raw("  f - Toggle file tree")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn health_dashboard_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Health Dashboard Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ←/→ or h/l - Navigate components")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  r - Refresh checks")),
        Line::from(Span::raw("  d - Toggle details view")),
        Line::from(Span::raw("  a - Toggle auto-refresh")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn command_palette_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("Command Palette Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(Span::raw("  Type to search commands")),
        Line::from(Span::raw("  ↑↓ - Navigate results")),
        Line::from(Span::raw("  Enter - Select command")),
        Line::from(Span::raw("  Esc - Close palette")),
        Line::from(Span::raw("  ? - Show this help")),
    ]
}

fn interactive_3d_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("3D Renderer Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Camera:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  WASD/Arrows - Move camera")),
        Line::from(Span::raw("  Q/E - Zoom in/out")),
        Line::from(Span::raw("  Mouse drag - Rotate (if supported)")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Actions:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  v - Cycle view modes")),
        Line::from(Span::raw("  s - Select equipment")),
        Line::from(Span::raw("  i - Toggle info panel")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("General:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  h - Toggle help")),
        Line::from(Span::raw("  Ctrl+H - Show all shortcuts")),
        Line::from(Span::raw("  q or Esc - Quit")),
    ]
}

fn general_help() -> Vec<Line<'static>> {
    vec![
        Line::from(vec![Span::styled("ArxOS General Help", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Universal Shortcuts:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  ? or h - Show help overlay")),
        Line::from(Span::raw("  Ctrl+H - Show shortcut cheat sheet")),
        Line::from(Span::raw("  q or Esc - Quit/Close")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("Navigation:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))]),
        Line::from(Span::raw("  Arrow keys - Navigate")),
        Line::from(Span::raw("  j/k - Navigate up/down")),
        Line::from(Span::raw("  h/l - Navigate left/right")),
        Line::from(Span::raw("  Enter - Select/Activate")),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled("For context-specific help, press ? in any screen", Style::default())]),
    ]
}

