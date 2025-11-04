//! Status badge widget for displaying equipment/system status

use ratatui::{
    style::Style,
    widgets::{Block, Borders, Paragraph, Widget},
};
use crate::ui::theme::{StatusColor, Theme};

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
    
    /// Create from YAML equipment status
    pub fn from_yaml_status(status: &crate::yaml::EquipmentStatus) -> Self {
        Self::new(StatusColor::from(status), format!("{:?}", status))
    }
    
    /// Create from core equipment status
    pub fn from_core_status(status: &crate::core::EquipmentStatus) -> Self {
        let status_color = match status {
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
    pub fn icon_yaml(status: &crate::yaml::EquipmentStatus) -> &'static str {
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

