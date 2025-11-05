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
    _area: ratatui::layout::Rect,
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

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::layout::Rect;
    use ratatui::widgets::Widget;
    use crate::ui::Theme;

    fn create_test_theme() -> Theme {
        Theme::default()
    }

    #[test]
    fn test_render_help_overlay() {
        let theme = create_test_theme();
        let area = Rect::new(0, 0, 50, 20);
        let overlay = render_help_overlay(HelpContext::General, area, &theme);
        
        // Should create a Paragraph widget - test by rendering to buffer
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        overlay.render(area, &mut buffer);
        // Check that buffer has content
        let has_content = (0..area.height).any(|y| {
            (0..area.width).any(|x| {
                buffer.get(x, y).symbol != " "
            })
        });
        assert!(has_content, "Overlay should render content");
    }

    #[test]
    fn test_render_help_overlay_all_contexts() {
        let theme = create_test_theme();
        let area = Rect::new(0, 0, 50, 20);
        let contexts = vec![
            HelpContext::EquipmentBrowser,
            HelpContext::RoomExplorer,
            HelpContext::StatusDashboard,
            HelpContext::SearchBrowser,
            HelpContext::WatchDashboard,
            HelpContext::ConfigWizard,
            HelpContext::ArPendingManager,
            HelpContext::DiffViewer,
            HelpContext::HealthDashboard,
            HelpContext::CommandPalette,
            HelpContext::Interactive3D,
            HelpContext::General,
        ];
        
        for context in contexts {
            let overlay = render_help_overlay(context, area, &theme);
            // Test by rendering to buffer
            let mut buffer = ratatui::buffer::Buffer::empty(area);
            overlay.render(area, &mut buffer);
            let has_content = (0..area.height).any(|y| {
                (0..area.width).any(|x| {
                    buffer.get(x, y).symbol != " "
                })
            });
            assert!(has_content, "Overlay should have content for {:?}", context);
        }
    }

    #[test]
    fn test_render_shortcut_cheat_sheet() {
        let theme = create_test_theme();
        let shortcuts = super::super::shortcuts::get_all_shortcuts();
        let cheat_sheet = render_shortcut_cheat_sheet(&shortcuts, "", None, &theme);
        
        // Test by rendering to buffer
        let area = Rect::new(0, 0, 50, 30);
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        cheat_sheet.render(area, &mut buffer);
        let has_content = (0..area.height).any(|y| {
            (0..area.width).any(|x| {
                buffer.get(x, y).symbol != " "
            })
        });
        assert!(has_content, "Cheat sheet should have content");
    }

    #[test]
    fn test_render_shortcut_cheat_sheet_filtered() {
        let theme = create_test_theme();
        let shortcuts = super::super::shortcuts::get_all_shortcuts();
        
        // Filter by search query
        let cheat_sheet = render_shortcut_cheat_sheet(&shortcuts, "navigate", None, &theme);
        let area = Rect::new(0, 0, 50, 30);
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        cheat_sheet.render(area, &mut buffer);
        let has_content = (0..area.height).any(|y| {
            (0..area.width).any(|x| {
                buffer.get(x, y).symbol != " "
            })
        });
        assert!(has_content, "Filtered cheat sheet should have content");
        
        // Filter with no matches
        let cheat_sheet_empty = render_shortcut_cheat_sheet(&shortcuts, "nonexistentxyz", None, &theme);
        let mut buffer2 = ratatui::buffer::Buffer::empty(area);
        cheat_sheet_empty.render(area, &mut buffer2);
        let has_title = (0..area.height).any(|y| {
            (0..area.width).any(|x| {
                buffer2.get(x, y).symbol != " "
            })
        });
        assert!(has_title, "Empty filtered cheat sheet should have title");
    }

    #[test]
    fn test_render_shortcut_cheat_sheet_by_category() {
        let theme = create_test_theme();
        let shortcuts = super::super::shortcuts::get_all_shortcuts();
        
        // Filter by category
        let cheat_sheet = render_shortcut_cheat_sheet(
            &shortcuts,
            "",
            Some(ShortcutCategory::Navigation),
            &theme
        );
        let area = Rect::new(0, 0, 50, 30);
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        cheat_sheet.render(area, &mut buffer);
        let has_content = (0..area.height).any(|y| {
            (0..area.width).any(|x| {
                buffer.get(x, y).symbol != " "
            })
        });
        assert!(has_content, "Category-filtered cheat sheet should have content");
    }

    #[test]
    fn test_render_shortcut_cheat_sheet_empty() {
        let theme = create_test_theme();
        let shortcuts = vec![];
        let cheat_sheet = render_shortcut_cheat_sheet(&shortcuts, "", None, &theme);
        
        // Should still have title - test by rendering
        let area = Rect::new(0, 0, 50, 10);
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        cheat_sheet.render(area, &mut buffer);
        let has_title = (0..area.height).any(|y| {
            (0..area.width).any(|x| {
                buffer.get(x, y).symbol != " "
            })
        });
        assert!(has_title, "Empty cheat sheet should have title");
    }

    #[test]
    fn test_help_overlay_styling() {
        let theme = create_test_theme();
        let area = Rect::new(0, 0, 50, 20);
        let overlay = render_help_overlay(HelpContext::General, area, &theme);
        
        // Test by rendering to buffer and checking borders are rendered
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        overlay.render(area, &mut buffer);
        // Check that borders are rendered (corners or sides)
        let has_borders = buffer.get(0, 0).symbol != " " || // top-left corner
                         buffer.get(area.width - 1, 0).symbol != " " || // top-right
                         buffer.get(0, area.height - 1).symbol != " "; // bottom-left
        assert!(has_borders, "Overlay should render borders");
    }

    #[test]
    fn test_cheat_sheet_styling() {
        let theme = create_test_theme();
        let shortcuts = super::super::shortcuts::get_all_shortcuts();
        let cheat_sheet = render_shortcut_cheat_sheet(&shortcuts, "", None, &theme);
        
        // Test by rendering to buffer and checking borders
        let area = Rect::new(0, 0, 50, 30);
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        cheat_sheet.render(area, &mut buffer);
        let has_borders = buffer.get(0, 0).symbol != " " ||
                         buffer.get(area.width - 1, 0).symbol != " " ||
                         buffer.get(0, area.height - 1).symbol != " ";
        assert!(has_borders, "Cheat sheet should render borders");
    }
}

