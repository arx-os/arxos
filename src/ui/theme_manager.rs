//! Theme Manager for ArxOS TUI
//!
//! Provides:
//! - Theme loading from configuration
//! - Theme persistence
//! - Built-in theme presets
//! - Custom theme creation

use crate::ui::Theme;
use crate::config::{ArxConfig, ConfigManager};
use ratatui::style::Color;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;

/// Theme configuration that can be serialized
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThemeConfig {
    /// Theme name
    pub name: String,
    /// Primary action color
    pub primary: String,
    /// Secondary info color
    pub secondary: String,
    /// Accent/highlight color
    pub accent: String,
    /// Background color
    pub background: String,
    /// Text color
    pub text: String,
    /// Muted/secondary text color
    pub muted: String,
}

impl ThemeConfig {
    /// Convert to Theme
    pub fn to_theme(&self) -> Result<Theme, Box<dyn std::error::Error>> {
        Ok(Theme {
            primary: parse_color(&self.primary)?,
            secondary: parse_color(&self.secondary)?,
            accent: parse_color(&self.accent)?,
            background: parse_color(&self.background)?,
            text: parse_color(&self.text)?,
            muted: parse_color(&self.muted)?,
        })
    }
    
    /// Create from Theme
    pub fn from_theme(theme: &Theme, name: String) -> Self {
        Self {
            name,
            primary: color_to_string(&theme.primary),
            secondary: color_to_string(&theme.secondary),
            accent: color_to_string(&theme.accent),
            background: color_to_string(&theme.background),
            text: color_to_string(&theme.text),
            muted: color_to_string(&theme.muted),
        }
    }
}

/// Built-in theme presets
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ThemePreset {
    Default,
    Dark,
    Light,
    HighContrast,
    Blue,
    Green,
    Purple,
}

impl ThemePreset {
    /// Get all available presets
    pub fn all() -> Vec<ThemePreset> {
        vec![
            ThemePreset::Default,
            ThemePreset::Dark,
            ThemePreset::Light,
            ThemePreset::HighContrast,
            ThemePreset::Blue,
            ThemePreset::Green,
            ThemePreset::Purple,
        ]
    }
    
    /// Get theme name
    pub fn name(&self) -> &'static str {
        match self {
            ThemePreset::Default => "Default",
            ThemePreset::Dark => "Dark",
            ThemePreset::Light => "Light",
            ThemePreset::HighContrast => "High Contrast",
            ThemePreset::Blue => "Blue",
            ThemePreset::Green => "Green",
            ThemePreset::Purple => "Purple",
        }
    }
    
    /// Get theme for this preset
    pub fn theme(&self) -> Theme {
        match self {
            ThemePreset::Default => Theme::default(),
            ThemePreset::Dark => Theme {
                primary: Color::Cyan,
                secondary: Color::Blue,
                accent: Color::Magenta,
                background: Color::Black,
                text: Color::White,
                muted: Color::DarkGray,
            },
            ThemePreset::Light => Theme {
                primary: Color::Blue,
                secondary: Color::Cyan,
                accent: Color::Magenta,
                background: Color::White,
                text: Color::Black,
                muted: Color::Gray,
            },
            ThemePreset::HighContrast => Theme {
                primary: Color::Yellow,
                secondary: Color::Cyan,
                accent: Color::White,
                background: Color::Black,
                text: Color::White,
                muted: Color::White,
            },
            ThemePreset::Blue => Theme {
                primary: Color::LightBlue,
                secondary: Color::Blue,
                accent: Color::Cyan,
                background: Color::Black,
                text: Color::White,
                muted: Color::DarkGray,
            },
            ThemePreset::Green => Theme {
                primary: Color::LightGreen,
                secondary: Color::Green,
                accent: Color::Yellow,
                background: Color::Black,
                text: Color::White,
                muted: Color::DarkGray,
            },
            ThemePreset::Purple => Theme {
                primary: Color::LightMagenta,
                secondary: Color::Magenta,
                accent: Color::Cyan,
                background: Color::Black,
                text: Color::White,
                muted: Color::DarkGray,
            },
        }
    }
}

/// Theme manager for loading and saving themes
pub struct ThemeManager {
    current_theme: Theme,
    theme_name: String,
    custom_themes: HashMap<String, ThemeConfig>,
}

impl ThemeManager {
    /// Create a new theme manager
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let theme = Self::load_theme_from_config()?;
        Ok(Self {
            current_theme: theme,
            theme_name: "default".to_string(),
            custom_themes: HashMap::new(),
        })
    }
    
    /// Load theme from configuration
    fn load_theme_from_config() -> Result<Theme, Box<dyn std::error::Error>> {
        // Try to load from config manager
        if let Ok(config_manager) = ConfigManager::new() {
            let config = config_manager.get_config();
            // Check if there's a theme in the config
            // For now, use default theme
            // In the future, we can add theme to UiConfig
        }
        Ok(Theme::default())
    }
    
    /// Get current theme
    pub fn current_theme(&self) -> &Theme {
        &self.current_theme
    }
    
    /// Get current theme name
    pub fn theme_name(&self) -> &str {
        &self.theme_name
    }
    
    /// Set theme from preset
    pub fn set_preset(&mut self, preset: ThemePreset) {
        self.current_theme = preset.theme();
        self.theme_name = preset.name().to_lowercase().replace(" ", "_");
    }
    
    /// Set custom theme
    pub fn set_custom_theme(&mut self, name: String, theme: Theme) {
        self.current_theme = theme;
        self.theme_name = name.clone();
        let theme_config = ThemeConfig::from_theme(&self.current_theme, name.clone());
        self.custom_themes.insert(name, theme_config);
    }
    
    /// Save current theme to configuration
    pub fn save_theme(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Save theme to a theme config file in user's config directory
        let home_dir = std::env::var("HOME")
            .or_else(|_| std::env::var("USERPROFILE")) // Windows fallback
            .map_err(|_| "Could not find home directory")?;
        let config_dir = std::path::Path::new(&home_dir)
            .join(".arx")
            .join("themes");
        
        fs::create_dir_all(&config_dir)?;
        
        let theme_file = config_dir.join(format!("{}.toml", self.theme_name));
        let theme_config = ThemeConfig::from_theme(&self.current_theme, self.theme_name.clone());
        let theme_toml = toml::to_string_pretty(&theme_config)
            .map_err(|e| format!("Failed to serialize theme: {}", e))?;
        
        fs::write(&theme_file, theme_toml)?;
        
        Ok(())
    }
    
    /// Load theme from saved configuration file
    pub fn load_theme(name: &str) -> Result<Theme, Box<dyn std::error::Error>> {
        let home_dir = std::env::var("HOME")
            .or_else(|_| std::env::var("USERPROFILE")) // Windows fallback
            .map_err(|_| "Could not find home directory")?;
        let config_dir = std::path::Path::new(&home_dir)
            .join(".arx")
            .join("themes");
        
        let theme_file = config_dir.join(format!("{}.toml", name));
        
        if !theme_file.exists() {
            return Err(format!("Theme '{}' not found", name).into());
        }
        
        let theme_content = fs::read_to_string(&theme_file)?;
        let theme_config: ThemeConfig = toml::from_str(&theme_content)
            .map_err(|e| format!("Failed to parse theme file: {}", e))?;
        
        theme_config.to_theme()
    }
    
    /// List all saved custom themes
    pub fn list_saved_themes() -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let home_dir = std::env::var("HOME")
            .or_else(|_| std::env::var("USERPROFILE"))
            .map_err(|_| "Could not find home directory")?;
        let config_dir = std::path::Path::new(&home_dir)
            .join(".arx")
            .join("themes");
        
        if !config_dir.exists() {
            return Ok(Vec::new());
        }
        
        let mut themes = Vec::new();
        for entry in fs::read_dir(&config_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("toml") {
                if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                    themes.push(stem.to_string());
                }
            }
        }
        
        themes.sort();
        Ok(themes)
    }
    
    /// Get all available theme presets
    pub fn available_presets() -> Vec<ThemePreset> {
        ThemePreset::all()
    }
    
    /// Get custom themes
    pub fn custom_themes(&self) -> &HashMap<String, ThemeConfig> {
        &self.custom_themes
    }
}

impl Default for ThemeManager {
    fn default() -> Self {
        Self::new().unwrap_or_else(|_| Self {
            current_theme: Theme::default(),
            theme_name: "default".to_string(),
            custom_themes: HashMap::new(),
        })
    }
}

/// Parse color string to Color
fn parse_color(color_str: &str) -> Result<Color, Box<dyn std::error::Error>> {
    match color_str.to_lowercase().as_str() {
        "black" => Ok(Color::Black),
        "red" => Ok(Color::Red),
        "green" => Ok(Color::Green),
        "yellow" => Ok(Color::Yellow),
        "blue" => Ok(Color::Blue),
        "magenta" => Ok(Color::Magenta),
        "cyan" => Ok(Color::Cyan),
        "white" => Ok(Color::White),
        "darkgray" | "dark_gray" => Ok(Color::DarkGray),
        "lightred" | "light_red" => Ok(Color::LightRed),
        "lightgreen" | "light_green" => Ok(Color::LightGreen),
        "lightyellow" | "light_yellow" => Ok(Color::LightYellow),
        "lightblue" | "light_blue" => Ok(Color::LightBlue),
        "lightmagenta" | "light_magenta" => Ok(Color::LightMagenta),
        "lightcyan" | "light_cyan" => Ok(Color::LightCyan),
        "gray" => Ok(Color::Gray),
        _ => Err(format!("Unknown color: {}", color_str).into()),
    }
}

/// Convert Color to string
fn color_to_string(color: &Color) -> String {
    match color {
        Color::Black => "black".to_string(),
        Color::Red => "red".to_string(),
        Color::Green => "green".to_string(),
        Color::Yellow => "yellow".to_string(),
        Color::Blue => "blue".to_string(),
        Color::Magenta => "magenta".to_string(),
        Color::Cyan => "cyan".to_string(),
        Color::White => "white".to_string(),
        Color::DarkGray => "darkgray".to_string(),
        Color::LightRed => "lightred".to_string(),
        Color::LightGreen => "lightgreen".to_string(),
        Color::LightYellow => "lightyellow".to_string(),
        Color::LightBlue => "lightblue".to_string(),
        Color::LightMagenta => "lightmagenta".to_string(),
        Color::LightCyan => "lightcyan".to_string(),
        Color::Gray => "gray".to_string(),
        Color::Rgb(r, g, b) => format!("rgb({},{},{})", r, g, b),
        Color::Indexed(i) => format!("indexed({})", i),
        _ => "unknown".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_theme_preset_names() {
        assert_eq!(ThemePreset::Default.name(), "Default");
        assert_eq!(ThemePreset::Dark.name(), "Dark");
        assert_eq!(ThemePreset::HighContrast.name(), "High Contrast");
    }
    
    #[test]
    fn test_parse_color() {
        assert_eq!(parse_color("red").unwrap(), Color::Red);
        assert_eq!(parse_color("GREEN").unwrap(), Color::Green);
        assert_eq!(parse_color("light_blue").unwrap(), Color::LightBlue);
        assert!(parse_color("invalid").is_err());
    }
    
    #[test]
    fn test_theme_config_conversion() {
        let theme = Theme::default();
        let config = ThemeConfig::from_theme(&theme, "test".to_string());
        let converted = config.to_theme().unwrap();
        
        assert_eq!(converted.primary, theme.primary);
        assert_eq!(converted.secondary, theme.secondary);
    }
    
    #[test]
    fn test_theme_manager_default() {
        let manager = ThemeManager::default();
        assert_eq!(manager.theme_name(), "default");
    }
    
    #[test]
    fn test_theme_preset_theme() {
        let preset = ThemePreset::Dark;
        let theme = preset.theme();
        assert_eq!(theme.background, Color::Black);
        assert_eq!(theme.text, Color::White);
    }
}

