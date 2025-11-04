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

