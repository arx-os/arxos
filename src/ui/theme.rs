//! Theme and styling system for ArxOS TUI
//!
//! Provides consistent color schemes and styling for building management context.

use ratatui::style::Color;
use crate::ui::theme_manager::ThemeManager;

/// Status colors for equipment and system health
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StatusColor {
    Healthy,
    Warning,
    Critical,
    Unknown,
}

impl StatusColor {
    /// Get the color for this status
    pub fn color(&self) -> Color {
        match self {
            StatusColor::Healthy => Color::Green,
            StatusColor::Warning => Color::Yellow,
            StatusColor::Critical => Color::Red,
            StatusColor::Unknown => Color::Gray,
        }
    }
    
    /// Get icon/symbol for this status
    pub fn icon(&self) -> &'static str {
        match self {
            StatusColor::Healthy => "🟢",
            StatusColor::Warning => "🟡",
            StatusColor::Critical => "🔴",
            StatusColor::Unknown => "⚪",
        }
    }
}

impl From<&crate::yaml::EquipmentStatus> for StatusColor {
    fn from(status: &crate::yaml::EquipmentStatus) -> Self {
        match status {
            crate::yaml::EquipmentStatus::Healthy => StatusColor::Healthy,
            crate::yaml::EquipmentStatus::Warning => StatusColor::Warning,
            crate::yaml::EquipmentStatus::Critical => StatusColor::Critical,
            crate::yaml::EquipmentStatus::Unknown => StatusColor::Unknown,
        }
    }
}

/// Theme configuration for ArxOS TUI
#[derive(Debug, Clone)]
pub struct Theme {
    /// Primary action color
    pub primary: Color,
    /// Secondary info color
    pub secondary: Color,
    /// Accent/highlight color
    pub accent: Color,
    /// Background color
    pub background: Color,
    /// Text color
    pub text: Color,
    /// Muted/secondary text color
    pub muted: Color,
}

impl Default for Theme {
    fn default() -> Self {
        Self {
            primary: Color::Cyan,
            secondary: Color::Blue,
            accent: Color::Magenta,
            background: Color::Black,
            text: Color::White,
            muted: Color::DarkGray,
        }
    }
}

impl Theme {
    /// Create a new theme with default colors
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Get theme based on user configuration
    pub fn from_config() -> Self {
        // Use ThemeManager to load from config
        ThemeManager::new()
            .map(|tm| tm.current_theme().clone())
            .unwrap_or_else(|_| Self::default())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_theme_new() {
        let theme = Theme::new();
        assert_eq!(theme.primary, Color::Cyan);
        assert_eq!(theme.background, Color::Black);
    }

    #[test]
    fn test_theme_default() {
        let theme = Theme::default();
        assert_eq!(theme.primary, Color::Cyan);
        assert_eq!(theme.secondary, Color::Blue);
        assert_eq!(theme.accent, Color::Magenta);
        assert_eq!(theme.background, Color::Black);
        assert_eq!(theme.text, Color::White);
        assert_eq!(theme.muted, Color::DarkGray);
    }

    #[test]
    fn test_theme_from_config() {
        // This should work even if config loading fails
        let theme = Theme::from_config();
        // Should have valid colors
        assert!(matches!(theme.primary, Color::Cyan | Color::Blue | Color::LightBlue | Color::LightGreen | Color::LightMagenta | Color::Yellow));
    }

    #[test]
    fn test_status_color() {
        assert_eq!(StatusColor::Healthy.color(), Color::Green);
        assert_eq!(StatusColor::Warning.color(), Color::Yellow);
        assert_eq!(StatusColor::Critical.color(), Color::Red);
        assert_eq!(StatusColor::Unknown.color(), Color::Gray);
    }

    #[test]
    fn test_status_color_icons() {
        assert_eq!(StatusColor::Healthy.icon(), "🟢");
        assert_eq!(StatusColor::Warning.icon(), "🟡");
        assert_eq!(StatusColor::Critical.icon(), "🔴");
        assert_eq!(StatusColor::Unknown.icon(), "⚪");
    }

    #[test]
    fn test_status_color_equality() {
        assert_eq!(StatusColor::Healthy, StatusColor::Healthy);
        assert_ne!(StatusColor::Healthy, StatusColor::Warning);
        assert_ne!(StatusColor::Critical, StatusColor::Unknown);
    }
}

