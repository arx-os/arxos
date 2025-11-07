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
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Command Palette (Ctrl+P)")
                .style(Style::default().fg(theme.primary)),
        )
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
                        Style::default()
                            .fg(theme.primary)
                            .add_modifier(Modifier::BOLD),
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
                        Style::default()
                            .fg(theme.muted)
                            .add_modifier(Modifier::ITALIC),
                    ),
                ]),
            ])
        })
        .collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Commands"))
        .highlight_style(
            Style::default()
                .fg(theme.accent)
                .add_modifier(Modifier::BOLD),
        )
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

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::backend::TestBackend;
    use ratatui::layout::Rect;

    #[test]
    fn test_render_command_palette() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        let theme = Theme::default();

        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // If no panic, rendering succeeded
    }

    #[test]
    fn test_render_empty_search() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        let theme = Theme::default();

        assert!(palette.query().is_empty(), "Query should be empty");
        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // Command palette renders with empty query state
    }

    #[test]
    fn test_render_with_query() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        palette.update_query("test".to_string());
        let theme = Theme::default();

        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // Should render with query
    }

    #[test]
    fn test_render_filtered_commands() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        palette.update_query("equipment".to_string());
        let theme = Theme::default();

        let filtered_count = palette.filtered_commands().len();
        assert!(filtered_count > 0, "Should have filtered commands");

        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // Should render filtered list
    }

    #[test]
    fn test_render_no_results() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        palette.update_query("nonexistentxyz123".to_string());
        let theme = Theme::default();

        assert_eq!(
            palette.filtered_commands().len(),
            0,
            "Should have no results"
        );
        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // Should render "No commands found" message
    }

    #[test]
    fn test_render_command_items() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        let theme = Theme::default();

        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // Command items should be formatted correctly (no panic means success)
    }

    #[test]
    fn test_render_command_categories() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        let theme = Theme::default();

        // Verify categories exist
        let commands = palette.commands();
        assert!(
            commands.iter().any(|c| c.category.icon() != ""),
            "Commands should have category icons"
        );

        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // Categories should be displayed
    }

    #[test]
    fn test_render_footer_info() {
        let area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();
        let mut palette = CommandPalette::new();
        let theme = Theme::default();

        let filtered_count = palette.filtered_commands().len();
        assert!(filtered_count > 0, "Should have commands");

        terminal
            .draw(|frame| {
                render_command_palette(frame, area, &mut palette, &theme, false);
            })
            .unwrap();
        // Footer should show command count
    }
}
