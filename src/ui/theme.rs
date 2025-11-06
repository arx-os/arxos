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
    
    /// Create a modern, professional color scheme
    /// Uses muted blues/cyans for primary, warm oranges for accents, greens for success
    pub fn modern() -> Self {
        Self {
            primary: Color::Cyan,        // Muted cyan for primary actions
            secondary: Color::Blue,      // Blue for secondary info
            accent: Color::Yellow,       // Warm orange/yellow for accents
            background: Color::Black,    // Black background
            text: Color::White,          // White text
            muted: Color::DarkGray,      // Dark gray for muted text
        }
    }
    
    /// Get color for reserved system type
    pub fn system_color(system: &str) -> Color {
        match system.to_lowercase().as_str() {
            "hvac" => Color::Cyan,           // #00ffff - Cyan for HVAC
            "plumbing" => Color::Blue,       // #0088ff - Blue for plumbing
            "electrical" => Color::Yellow,   // #ffaa00 - Yellow for electrical
            "fire" => Color::Red,            // Red for fire systems
            "lighting" => Color::Yellow,     // Yellow for lighting
            "security" => Color::Magenta,    // Magenta for security
            "elevators" => Color::LightBlue, // Light blue for elevators
            "roof" => Color::Green,          // Green for roof
            "windows" => Color::LightGreen,  // Light green for windows
            "doors" => Color::LightMagenta,  // Light magenta for doors
            "structure" => Color::Gray,      // Gray for structure
            "envelope" => Color::DarkGray,   // Dark gray for envelope
            "it" => Color::Cyan,             // Cyan for IT
            "furniture" => Color::Magenta,   // Magenta for furniture
            _ => Color::White,               // White for custom items
        }
    }
    
    /// Detect system theme preference
    /// Returns true for dark mode, false for light mode
    fn detect_system_theme() -> bool {
        #[cfg(target_os = "macos")]
        {
            // macOS: Check system appearance
            use std::process::Command;
            if let Ok(output) = Command::new("defaults")
                .args(&["read", "-g", "AppleInterfaceStyle"])
                .output()
            {
                if let Ok(style) = String::from_utf8(output.stdout) {
                    return style.trim().to_lowercase() == "dark";
                }
            }
        }
        
        #[cfg(target_os = "linux")]
        {
            // Linux: Check COLORFGBG environment variable
            // Format: foreground;background where 0-7 = dark, 8-15 = light
            if let Ok(color_fgbg) = std::env::var("COLORFGBG") {
                if let Some(parts) = color_fgbg.split(';').nth(1) {
                    if let Ok(bg) = parts.parse::<u8>() {
                        // Background color: 0-7 = dark, 8-15 = light
                        return bg < 8;
                    }
                }
            }
            
            // Alternative: Check gsettings (GNOME)
            use std::process::Command;
            if let Ok(output) = Command::new("gsettings")
                .args(&["get", "org.gnome.desktop.interface", "gtk-theme"])
                .output()
            {
                if let Ok(theme) = String::from_utf8(output.stdout) {
                    let theme_lower = theme.to_lowercase();
                    return theme_lower.contains("dark") || theme_lower.contains("adwaita-dark");
                }
            }
        }
        
        #[cfg(target_os = "windows")]
        {
            // Windows: Check registry for theme preference
            use std::process::Command;
            if let Ok(output) = Command::new("reg")
                .args(&["query", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "/v", "AppsUseLightTheme"])
                .output()
            {
                if let Ok(result) = String::from_utf8(output.stdout) {
                    // If AppsUseLightTheme is 0, dark mode is enabled
                    return result.contains("0x0") || result.contains("REG_DWORD    0x0");
                }
            }
        }
        
        // Default: assume dark mode for terminals (most terminals use dark backgrounds)
        true
    }
    
    /// Detect terminal theme from environment
    /// Checks COLORFGBG and other terminal-specific variables
    fn detect_terminal_theme() -> Option<bool> {
        // Check COLORFGBG (common in terminals)
        if let Ok(color_fgbg) = std::env::var("COLORFGBG") {
            if let Some(parts) = color_fgbg.split(';').nth(1) {
                if let Ok(bg) = parts.parse::<u8>() {
                    // Background color: 0-7 = dark, 8-15 = light
                    return Some(bg < 8);
                }
            }
        }
        
        // Check TERM_PROGRAM for specific terminal apps
        if let Ok(term_program) = std::env::var("TERM_PROGRAM") {
            match term_program.as_str() {
                "iTerm.app" | "Apple_Terminal" => {
                    // These default to dark on macOS
                    return Some(true);
                }
                _ => {}
            }
        }
        
        None
    }
    
    /// Create theme from terminal/system detection
    pub fn from_terminal() -> Self {
        // First try terminal-specific detection
        let is_dark = Self::detect_terminal_theme()
            .or_else(|| Some(Self::detect_system_theme()))
            .unwrap_or(true); // Default to dark
        
        if is_dark {
            Self::modern() // Modern dark theme
        } else {
            // Light theme variant
            Self {
                primary: Color::Blue,
                secondary: Color::Cyan,
                accent: Color::Magenta,
                background: Color::White,
                text: Color::Black,
                muted: Color::DarkGray,
            }
        }
    }
    
    /// Get theme based on user configuration
    pub fn from_config() -> Self {
        // Try to load from config first
        if let Ok(tm) = ThemeManager::new() {
            let configured_theme = tm.current_theme().clone();
            // If theme is explicitly set in config, use it
            // Otherwise, detect from terminal/system
            if tm.theme_name() != "default" {
                return configured_theme;
            }
        }
        
        // Auto-detect from terminal/system
        Self::from_terminal()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_terminal_theme() {
        // Test that from_terminal returns a valid theme
        let theme = Theme::from_terminal();
        assert!(matches!(theme.background, Color::Black | Color::White));
        assert!(matches!(theme.text, Color::Black | Color::White));
    }
    
    #[test]
    fn test_from_config_uses_terminal_detection() {
        // Test that from_config falls back to terminal detection
        let theme = Theme::from_config();
        assert!(matches!(theme.background, Color::Black | Color::White));
    }

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

