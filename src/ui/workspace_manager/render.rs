//! Workspace Manager Rendering
//!
//! Provides functions for rendering the workspace manager UI.

use super::manager::WorkspaceManager;
use crate::ui::Theme;
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Frame,
};

/// Render workspace manager
pub fn render_workspace_manager(
    frame: &mut Frame,
    area: Rect,
    manager: &mut WorkspaceManager,
    theme: &Theme,
    _mouse_enabled: bool,
) {
    let chunks = Layout::default()
        .direction(ratatui::layout::Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Search bar
            Constraint::Min(10),   // Workspace list
            Constraint::Length(3), // Footer
        ])
        .split(area);
    
    // Search input
    let search_text = if manager.query().is_empty() {
        "Type to search workspaces...".to_string()
    } else {
        format!("Search: {}", manager.query())
    };
    
    let search_paragraph = Paragraph::new(search_text.as_str())
        .block(Block::default()
            .borders(Borders::ALL)
            .title("Workspace Manager (Ctrl+W)")
            .style(Style::default().fg(theme.primary)))
        .style(if manager.query().is_empty() {
            Style::default().fg(theme.muted)
        } else {
            Style::default().fg(theme.text)
        });
    
    frame.render_widget(search_paragraph, chunks[0]);
    
    // Collect workspace info first to avoid borrow conflicts
    let filtered_indices = manager.filtered_workspaces().to_vec();
    let filtered_count = filtered_indices.len();
    
    // Extract all workspace data before mutable borrow
    let workspace_data: Vec<(String, Option<String>, String, bool, bool)> = {
        let workspaces = manager.workspaces();
        filtered_indices
            .iter()
            .map(|&idx| {
                let ws = &workspaces[idx];
                let is_active = manager.is_active(ws);
                (
                    ws.name.clone(),
                    ws.description.clone(),
                    ws.path.display().to_string(),
                    ws.git_repo.is_some(),
                    is_active,
                )
            })
            .collect()
    };
    
    // Workspace list
    let items: Vec<ListItem> = workspace_data
        .iter()
        .map(|(name, desc, path_str, has_git, is_active)| {
            let is_active = *is_active;
            let active_indicator = if is_active { "● " } else { "  " };
            let active_color = if is_active { theme.accent } else { theme.text };
            let indicator_color = if is_active { theme.accent } else { theme.muted };
            
            let mut spans = vec![
                Span::styled(
                    active_indicator,
                    Style::default().fg(indicator_color),
                ),
                Span::styled(
                    name,
                    Style::default()
                        .fg(active_color)
                        .add_modifier(if is_active { Modifier::BOLD } else { Modifier::empty() }),
                ),
            ];
            
            if is_active {
                spans.push(Span::styled(
                    " [ACTIVE]",
                    Style::default().fg(theme.accent).add_modifier(Modifier::BOLD),
                ));
            }
            
            let mut lines = vec![Line::from(spans)];
            
            if let Some(desc) = desc {
                lines.push(Line::from(vec![
                    Span::styled("  ", Style::default()),
                    Span::styled(desc, Style::default().fg(theme.muted)),
                ]));
            }
            
            lines.push(Line::from(vec![
                Span::styled("  ", Style::default()),
                Span::styled(
                    format!("Path: {}", path_str),
                    Style::default().fg(theme.muted).add_modifier(Modifier::ITALIC),
                ),
            ]));
            
            if *has_git {
                lines.push(Line::from(vec![
                    Span::styled("  ", Style::default()),
                    Span::styled(
                        "📦 Git repository",
                        Style::default().fg(theme.secondary),
                    ),
                ]));
            }
            
            ListItem::new(lines)
        })
        .collect();
    
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Available Workspaces"))
        .highlight_style(Style::default().fg(theme.accent).add_modifier(Modifier::BOLD))
        .highlight_symbol("▶ ");
    
    frame.render_stateful_widget(list, chunks[1], manager.list_state_mut());
    
    // Footer
    let footer_text = if filtered_count == 0 {
        "No workspaces found. Press Esc to close.".to_string()
    } else {
        format!(
            "{} workspaces found. ↑↓ to navigate, Enter to switch, Esc to close",
            filtered_count
        )
    };
    
    let footer = Paragraph::new(footer_text)
        .block(Block::default().borders(Borders::ALL))
        .alignment(Alignment::Center)
        .style(Style::default().fg(theme.muted));
    
    frame.render_widget(footer, chunks[2]);
    
    // Render help overlay if needed
    use crate::ui::{render_help_overlay, HelpContext};
    if manager.help_system().show_overlay {
        let help_overlay = render_help_overlay(HelpContext::General, area, theme);
        // Center help overlay (60% width, 20% height)
        let help_width = (area.width as f32 * 0.6) as u16;
        let help_height = (area.height as f32 * 0.2) as u16;
        let help_x = (area.width.saturating_sub(help_width)) / 2;
        let help_y = (area.height.saturating_sub(help_height)) / 2;
        let help_area = Rect::new(help_x, help_y, help_width, help_height);
        frame.render_widget(help_overlay, help_area);
    }
}

