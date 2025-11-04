//! Summary card widget for dashboard displays

use ratatui::{
    style::{Color, Modifier, Style},
    widgets::{Block, Borders, Paragraph, Widget},
    text::{Line, Span},
};
use crate::ui::theme::Theme;

/// Widget for displaying summary information in a card format
pub struct SummaryCard {
    title: String,
    value: String,
    subtitle: Option<String>,
    theme: Theme,
    color: Option<Color>,
}

impl SummaryCard {
    /// Create a new summary card
    pub fn new(title: impl Into<String>, value: impl Into<String>) -> Self {
        Self {
            title: title.into(),
            value: value.into(),
            subtitle: None,
            theme: Theme::default(),
            color: None,
        }
    }
    
    /// Add a subtitle
    pub fn with_subtitle(mut self, subtitle: impl Into<String>) -> Self {
        self.subtitle = Some(subtitle.into());
        self
    }
    
    /// Set theme
    pub fn with_theme(mut self, theme: Theme) -> Self {
        self.theme = theme;
        self
    }
    
    /// Set color
    pub fn with_color(mut self, color: Color) -> Self {
        self.color = Some(color);
        self
    }
}

impl Widget for SummaryCard {
    fn render(self, area: ratatui::layout::Rect, buf: &mut ratatui::buffer::Buffer) {
        let value_color = self.color.unwrap_or(self.theme.primary);
        let title = self.title.clone();
        
        let lines: Vec<Line> = vec![
            Line::from(vec![
                Span::styled(
                    self.value,
                    Style::default()
                        .fg(value_color)
                        .add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(vec![
                Span::styled(
                    title.clone(),
                    Style::default().fg(self.theme.muted),
                ),
            ]),
        ];
        
        let mut lines = lines;
        if let Some(subtitle) = self.subtitle {
            lines.push(Line::from(vec![
                Span::styled(
                    subtitle,
                    Style::default().fg(self.theme.muted),
                ),
            ]));
        }
        
        let paragraph = Paragraph::new(lines)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title(title),
            )
            .alignment(ratatui::layout::Alignment::Center);
        
        paragraph.render(area, buf);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::layout::Rect;
    use ratatui::widgets::Widget;

    #[test]
    fn test_summary_card_creation() {
        let card = SummaryCard::new("Title", "100");
        assert_eq!(card.title, "Title");
        assert_eq!(card.value, "100");
        assert!(card.subtitle.is_none());
    }

    #[test]
    fn test_summary_card_with_subtitle() {
        let card = SummaryCard::new("Title", "100")
            .with_subtitle("Subtitle");
        assert_eq!(card.subtitle, Some("Subtitle".to_string()));
    }

    #[test]
    fn test_summary_card_with_theme() {
        let mut theme = Theme::default();
        theme.primary = Color::Blue;
        
        let card = SummaryCard::new("Title", "100")
            .with_theme(theme.clone());
        
        assert_eq!(card.theme.primary, Color::Blue);
    }

    #[test]
    fn test_summary_card_with_color() {
        let card = SummaryCard::new("Title", "100")
            .with_color(Color::Red);
        
        assert_eq!(card.color, Some(Color::Red));
    }

    #[test]
    fn test_summary_card_rendering() {
        let card = SummaryCard::new("Equipment Count", "42");
        let area = Rect::new(0, 0, 30, 10);
        let mut buffer = ratatui::buffer::Buffer::empty(area);
        
        card.render(area, &mut buffer);
        
        // Verify content was rendered
        let has_content = (0..area.height).any(|y| {
            (0..area.width).any(|x| {
                buffer.get(x, y).symbol != " "
            })
        });
        assert!(has_content, "Card should render content");
    }

    #[test]
    fn test_summary_card_data() {
        let card = SummaryCard::new("Total Equipment", "150")
            .with_subtitle("Active systems");
        
        assert_eq!(card.title, "Total Equipment");
        assert_eq!(card.value, "150");
        assert_eq!(card.subtitle, Some("Active systems".to_string()));
    }

    #[test]
    fn test_summary_card_with_all_options() {
        let card = SummaryCard::new("Status", "OK")
            .with_subtitle("All systems operational")
            .with_theme(Theme::default())
            .with_color(Color::Green);
        
        assert_eq!(card.title, "Status");
        assert_eq!(card.value, "OK");
        assert_eq!(card.subtitle, Some("All systems operational".to_string()));
        assert_eq!(card.color, Some(Color::Green));
    }
}

