//! Help System Rendering
//!
//! Provides functions for rendering help overlays and cheat sheets.

use super::types::{HelpContext, Shortcut, ShortcutCategory};
use crate::ui::Theme;
use ratatui::{
    layout::Alignment,
    style::{Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
};

/// Render help overlay (centered modal)
pub fn render_help_overlay<'a>(
    context: HelpContext,
    area: ratatui::layout::Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    use super::content::get_context_help;
    
    let help_content = get_context_help(context);
    
    Paragraph::new(help_content)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Help (Press ? or h to close)")
                .border_style(Style::default().fg(theme.accent))
        )
        .alignment(Alignment::Left)
        .style(Style::default().fg(theme.text))
}

/// Render keyboard shortcut cheat sheet
pub fn render_shortcut_cheat_sheet<'a>(
    shortcuts: &'a [Shortcut],
    search_query: &'a str,
    selected_category: Option<ShortcutCategory>,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let mut lines = vec![
        Line::from(vec![
            Span::styled(
                "Keyboard Shortcuts",
                Style::default().fg(theme.primary).add_modifier(Modifier::BOLD),
            ),
        ]),
        Line::from(Span::raw("")),
    ];
    
    // Filter shortcuts by category and search
    let filtered: Vec<&Shortcut> = shortcuts.iter()
        .filter(|s| {
            // Filter by category if selected
            if let Some(cat) = selected_category {
                if s.category != cat {
                    return false;
                }
            }
            // Filter by search query
            if !search_query.is_empty() {
                let query_lower = search_query.to_lowercase();
                s.key.to_lowercase().contains(&query_lower) ||
                s.description.to_lowercase().contains(&query_lower)
            } else {
                true
            }
        })
        .collect();
    
    // Group by category
    let mut current_category: Option<ShortcutCategory> = None;
    for shortcut in filtered {
        if current_category != Some(shortcut.category) {
            if current_category.is_some() {
                lines.push(Line::from(Span::raw("")));
            }
            let cat_name = match shortcut.category {
                ShortcutCategory::Navigation => "Navigation",
                ShortcutCategory::Actions => "Actions",
                ShortcutCategory::Views => "Views",
                ShortcutCategory::Filters => "Filters",
                ShortcutCategory::General => "General",
            };
            lines.push(Line::from(vec![
                Span::styled(
                    format!("{}:", cat_name),
                    Style::default().fg(theme.accent).add_modifier(Modifier::BOLD),
                ),
            ]));
            current_category = Some(shortcut.category);
        }
        
        lines.push(Line::from(vec![
            Span::styled("  ", Style::default()),
            Span::styled(
                format!("{:<20}", shortcut.key),
                Style::default().fg(theme.primary),
            ),
            Span::styled("  ", Style::default()),
            Span::styled(
                shortcut.description.clone(),
                Style::default().fg(theme.text),
            ),
        ]));
    }
    
    if search_query.is_empty() {
        lines.push(Line::from(Span::raw("")));
        lines.push(Line::from(vec![
            Span::styled(
                "Press / to search shortcuts",
                Style::default().fg(theme.muted),
            ),
        ]));
    }
    
    Paragraph::new(lines)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Shortcut Cheat Sheet (Press Ctrl+H or ? to close)")
                .border_style(Style::default().fg(theme.accent))
        )
        .alignment(Alignment::Left)
        .style(Style::default().fg(theme.text))
}

