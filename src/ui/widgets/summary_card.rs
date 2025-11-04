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

