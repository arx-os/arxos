//! Command Palette Rendering
//!
//! Provides functions for rendering the command palette UI.

use super::palette::CommandPalette;
use crate::ui::Theme;
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Modifier, Style},
    text::Line,
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Frame,
};

/// Render command palette
pub fn render_command_palette(
    frame: &mut Frame,
    area: Rect,
    palette: &mut CommandPalette,
    theme: &Theme,
    _mouse_enabled: bool,
) {
    let chunks = Layout::default()
        .direction(ratatui::layout::Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Search bar
            Constraint::Min(10),   // Command list
            Constraint::Length(3), // Footer
        ])
        .split(area);
    
    // Search input
    let search_text = if palette.query().is_empty() {
        "Type to search commands...".to_string()
    } else {
        format!("Search: {}", palette.query())
    };
    
    let search_paragraph = Paragraph::new(search_text.as_str())
        .block(Block::default()
            .borders(Borders::ALL)
            .title("Command Palette (Ctrl+P)")
            .style(Style::default().fg(theme.primary)))
        .style(if palette.query().is_empty() {
            Style::default().fg(theme.muted)
        } else {
            Style::default().fg(theme.text)
        });
    
    frame.render_widget(search_paragraph, chunks[0]);
    
    // Collect data before mutable borrow
    let filtered_indices: Vec<usize> = palette.filtered_commands().to_vec();
    let filtered_count = filtered_indices.len();
    
    // Build command info for rendering (extract needed data)
    let command_info: Vec<(String, String, String, String, String)> = {
        let commands = palette.commands();
        filtered_indices
            .iter()
            .map(|&idx| {
                let cmd = &commands[idx];
                (
                    cmd.name.clone(),
                    cmd.description.clone(),
                    cmd.full_command.clone(),
                    cmd.category.icon().to_string(),
                    cmd.category.name().to_string(),
                )
            })
            .collect()
    };
    
    // Command list
    let items: Vec<ListItem> = command_info
        .iter()
        .map(|(name, description, full_command, icon, category_name)| {
            ListItem::new(vec![
                Line::from(vec![
                    ratatui::text::Span::styled(
                        format!("{} {} ", icon, name),
                        Style::default().fg(theme.primary).add_modifier(Modifier::BOLD),
                    ),
                    ratatui::text::Span::styled(
                        format!("({})", category_name),
                        Style::default().fg(theme.muted),
                    ),
                ]),
                Line::from(vec![
                    ratatui::text::Span::styled("  ", Style::default()),
                    ratatui::text::Span::styled(description, Style::default().fg(theme.text)),
                ]),
                Line::from(vec![
                    ratatui::text::Span::styled("  ", Style::default()),
                    ratatui::text::Span::styled(
                        full_command,
                        Style::default().fg(theme.muted).add_modifier(Modifier::ITALIC),
                    ),
                ]),
            ])
        })
        .collect();
    
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Commands"))
        .highlight_style(Style::default().fg(theme.accent).add_modifier(Modifier::BOLD))
        .highlight_symbol("▶ ");
    
    frame.render_stateful_widget(list, chunks[1], palette.list_state_mut());
    
    // Footer
    let footer_text = if filtered_count == 0 {
        "No commands found. Press Esc to close.".to_string()
    } else {
        format!(
            "{} commands found. ↑↓ to navigate, Enter to select, Esc to close",
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
    if palette.help_system().show_overlay {
        let help_overlay = render_help_overlay(HelpContext::CommandPalette, area, theme);
        frame.render_widget(help_overlay, area);
    }
}

