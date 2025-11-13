//! Status badge widget for displaying equipment/system status

use crate::tui::theme::{StatusColor, Theme};
use ratatui::{
    style::Style,
    widgets::{Block, Borders, Paragraph, Widget},
};

/// Widget for displaying status with color and icon
pub struct StatusBadge {
    status: StatusColor,
    label: String,
    theme: Theme,
}

impl StatusBadge {
    /// Create a new status badge
    pub fn new(status: StatusColor, label: impl Into<String>) -> Self {
        Self {
            status,
            label: label.into(),
            theme: Theme::default(),
        }
    }

    /// Create from YAML equipment status (placeholder)
    pub fn from_yaml_status(status: &str) -> Self {
        Self::new(StatusColor::Unknown, status.to_string())
    }

    /// Create from core equipment status
    pub fn from_core_status(status: &crate::core::EquipmentStatus) -> Self {
        let color = match status {
            crate::core::EquipmentStatus::Active => StatusColor::Healthy,
            crate::core::EquipmentStatus::Maintenance => StatusColor::Warning,
            crate::core::EquipmentStatus::OutOfOrder => StatusColor::Critical,
            crate::core::EquipmentStatus::Inactive => StatusColor::Unknown,
            crate::core::EquipmentStatus::Unknown => StatusColor::Unknown,
        };
        Self::new(status_color, format!("{:?}", status))
    }

    /// Set theme
    pub fn with_theme(mut self, theme: Theme) -> Self {
        self.theme = theme;
        self
    }

    /// Get the icon for YAML equipment status
    pub fn icon_yaml(status: &str) -> &'static str {
        StatusColor::from(status).icon()
    }

    /// Get the icon for core equipment status
    pub fn icon_core(status: &crate::core::EquipmentStatus) -> &'static str {
        match status {
            crate::core::EquipmentStatus::Active => StatusColor::Healthy.icon(),
            crate::core::EquipmentStatus::Maintenance => StatusColor::Warning.icon(),
            crate::core::EquipmentStatus::OutOfOrder => StatusColor::Critical.icon(),
            crate::core::EquipmentStatus::Inactive => StatusColor::Unknown.icon(),
            crate::core::EquipmentStatus::Unknown => StatusColor::Unknown.icon(),
        }
    }
}

impl Widget for StatusBadge {
    fn render(self, area: ratatui::layout::Rect, buf: &mut ratatui::buffer::Buffer) {
        let color = self.status.color();
        let icon = self.status.icon();
        let text = format!("{} {}", icon, self.label);

        let paragraph = Paragraph::new(text)
            .style(Style::default().fg(color))
            .block(Block::default().borders(Borders::NONE));

        paragraph.render(area, buf);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::layout::Rect;
    use ratatui::style::Color;
    use ratatui::widgets::Widget;

    #[test]
    fn test_status_badge_creation() {
        let badge = StatusBadge::new(StatusColor::Healthy, "Active");
        assert_eq!(badge.status, StatusColor::Healthy);
        assert_eq!(badge.label, "Active");
    }

    #[test]
    fn test_status_badge_colors() {
        let healthy = StatusBadge::new(StatusColor::Healthy, "Healthy");
        assert_eq!(healthy.status.color(), Color::Green);

        let warning = StatusBadge::new(StatusColor::Warning, "Warning");
        assert_eq!(warning.status.color(), Color::Yellow);

        let critical = StatusBadge::new(StatusColor::Critical, "Critical");
        assert_eq!(critical.status.color(), Color::Red);

        let unknown = StatusBadge::new(StatusColor::Unknown, "Unknown");
        assert_eq!(unknown.status.color(), Color::Gray);
    }

    #[test]
    fn test_status_badge_rendering() {
        let badge = StatusBadge::new(StatusColor::Healthy, "Test");
        let area = Rect::new(0, 0, 20, 1);
        let mut buffer = ratatui::buffer::Buffer::empty(area);

        badge.render(area, &mut buffer);

        // Verify content was rendered
        let has_content =
            (0..area.height).any(|y| (0..area.width).any(|x| buffer.get(x, y).symbol != " "));
        assert!(has_content, "Badge should render content");
    }

    #[test]
    fn test_status_badge_with_theme() {
        let theme = Theme {
            primary: Color::Blue,
            ..Theme::default()
        };

        let badge = StatusBadge::new(StatusColor::Warning, "Test").with_theme(theme.clone());

        assert_eq!(badge.theme.primary, Color::Blue);
    }

    #[test]
    fn test_status_badge_icon_yaml() {
        use arx::yaml::EquipmentStatus;

        let icon = StatusBadge::icon_yaml(&EquipmentStatus::Healthy);
        assert_eq!(icon, "🟢");

        let icon = StatusBadge::icon_yaml(&EquipmentStatus::Warning);
        assert_eq!(icon, "🟡");

        let icon = StatusBadge::icon_yaml(&EquipmentStatus::Critical);
        assert_eq!(icon, "🔴");
    }

    #[test]
    fn test_status_badge_icon_core() {
        use arx::core::EquipmentStatus;

        let icon = StatusBadge::icon_core(&EquipmentStatus::Active);
        assert_eq!(icon, "🟢");

        let icon = StatusBadge::icon_core(&EquipmentStatus::Maintenance);
        assert_eq!(icon, "🟡");

        let icon = StatusBadge::icon_core(&EquipmentStatus::OutOfOrder);
        assert_eq!(icon, "🔴");
    }
}
