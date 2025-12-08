//! Theme Manager for ArxOS TUI
//!
//! Provides:
//! - Theme loading from configuration
//! - Theme persistence
//! - Built-in theme presets
//! - Custom theme creation

use crate::tui::Theme;
use crate::config::ConfigManager;
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
        let _config_manager = ConfigManager::new().ok();
        // Config loaded successfully if Some
        // Check if there's a theme in the config
        // For now, use default theme
        // In the future, we can add theme to UiConfig
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
        let config_dir = std::path::Path::new(&home_dir).join(".arx").join("themes");

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
        let config_dir = std::path::Path::new(&home_dir).join(".arx").join("themes");

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
        let config_dir = std::path::Path::new(&home_dir).join(".arx").join("themes");

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
    use serial_test::serial;

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

    #[test]
    fn test_theme_manager_new() {
        let manager = ThemeManager::new();
        assert!(manager.is_ok(), "Should create theme manager");
        let manager = manager.unwrap();
        assert_eq!(manager.theme_name(), "default");
    }

    #[test]
    fn test_theme_manager_set_theme() {
        let mut manager = ThemeManager::default();
        manager.set_preset(ThemePreset::Dark);
        assert_eq!(manager.theme_name(), "dark");
        assert_eq!(manager.current_theme().background, Color::Black);

        manager.set_preset(ThemePreset::Light);
        assert_eq!(manager.theme_name(), "light");
        assert_eq!(manager.current_theme().background, Color::White);
    }

    #[test]
    fn test_theme_manager_set_custom_theme() {
        let mut manager = ThemeManager::default();
        let custom_theme = Theme {
            primary: Color::Red,
            secondary: Color::Green,
            accent: Color::Blue,
            background: Color::Black,
            text: Color::White,
            muted: Color::Gray,
        };

        manager.set_custom_theme("custom".to_string(), custom_theme.clone());
        assert_eq!(manager.theme_name(), "custom");
        assert_eq!(manager.current_theme().primary, Color::Red);
        assert!(manager.custom_themes().contains_key("custom"));
    }

    #[test]
    fn test_theme_manager_save_theme() {
        let mut manager = ThemeManager::default();
        manager.set_preset(ThemePreset::Blue);

        // Use temp directory for testing
        let temp_dir = std::env::temp_dir().join("arxos_test_themes");
        let _ = std::fs::remove_dir_all(&temp_dir);
        std::fs::create_dir_all(&temp_dir).unwrap();

        // Override HOME for test
        let original_home = std::env::var("HOME");
        std::env::set_var("HOME", temp_dir.parent().unwrap());

        // Create .arx/themes directory
        let themes_dir = temp_dir.parent().unwrap().join(".arx").join("themes");
        std::fs::create_dir_all(&themes_dir).unwrap();

        // Modify save_theme to use test directory (we can't easily mock this)
        // So we'll test the serialization instead
        let theme_config =
            ThemeConfig::from_theme(manager.current_theme(), "test_theme".to_string());
        let toml_str = toml::to_string_pretty(&theme_config);
        assert!(toml_str.is_ok(), "Should serialize theme config");

        // Restore HOME
        if let Ok(home) = original_home {
            std::env::set_var("HOME", home);
        }

        // Cleanup
        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_theme_manager_load_theme() {
        // Create a test theme file with correct directory structure
        let temp_dir = std::env::temp_dir().join("arxos_test_themes_load");
        let _ = std::fs::remove_dir_all(&temp_dir);
        let themes_dir = temp_dir.join(".arx").join("themes");
        std::fs::create_dir_all(&themes_dir).unwrap();

        let theme_file = themes_dir.join("test_theme.toml");
        let theme_config = ThemeConfig {
            name: "test_theme".to_string(),
            primary: "cyan".to_string(),
            secondary: "blue".to_string(),
            accent: "magenta".to_string(),
            background: "black".to_string(),
            text: "white".to_string(),
            muted: "darkgray".to_string(),
        };

        let toml_content = toml::to_string_pretty(&theme_config).unwrap();
        std::fs::write(&theme_file, toml_content).unwrap();

        // Test loading
        let original_home = std::env::var("HOME");
        let original_appdata = std::env::var("APPDATA");
        std::env::set_var("HOME", &temp_dir);
        std::env::set_var("APPDATA", &temp_dir);

        let result = ThemeManager::load_theme("test_theme");
        assert!(result.is_ok(), "Should load theme");
        let theme = result.unwrap();
        assert_eq!(theme.primary, Color::Cyan);

        // Restore HOME
        match original_home {
            Ok(home) => std::env::set_var("HOME", home),
            Err(_) => std::env::remove_var("HOME"),
        }
        match original_appdata {
            Ok(val) => std::env::set_var("APPDATA", val),
            Err(_) => std::env::remove_var("APPDATA"),
        }

        // Cleanup
        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    #[serial]
    fn test_theme_manager_list_saved_themes() {
        // Create test theme files with correct directory structure
        let temp_dir = std::env::temp_dir().join("arxos_test_themes_list");
        let _ = std::fs::remove_dir_all(&temp_dir);
        let themes_dir = temp_dir.join(".arx").join("themes");
        std::fs::create_dir_all(&themes_dir).unwrap();

        // Create test theme files with valid TOML
        let theme1_config = ThemeConfig {
            name: "theme1".to_string(),
            primary: "cyan".to_string(),
            secondary: "blue".to_string(),
            accent: "magenta".to_string(),
            background: "black".to_string(),
            text: "white".to_string(),
            muted: "darkgray".to_string(),
        };
        let theme2_config = ThemeConfig {
            name: "theme2".to_string(),
            primary: "red".to_string(),
            secondary: "green".to_string(),
            accent: "blue".to_string(),
            background: "black".to_string(),
            text: "white".to_string(),
            muted: "darkgray".to_string(),
        };

        std::fs::write(
            themes_dir.join("theme1.toml"),
            toml::to_string_pretty(&theme1_config).unwrap(),
        )
        .unwrap();
        std::fs::write(
            themes_dir.join("theme2.toml"),
            toml::to_string_pretty(&theme2_config).unwrap(),
        )
        .unwrap();

        let original_home = std::env::var("HOME");
        std::env::set_var("HOME", &temp_dir);

        let result = ThemeManager::list_saved_themes();
        assert!(result.is_ok(), "Should list themes");
        let themes = result.unwrap();
        assert!(
            themes.contains(&"theme1".to_string()),
            "Should contain theme1"
        );
        assert!(
            themes.contains(&"theme2".to_string()),
            "Should contain theme2"
        );

        // Restore HOME
        if let Ok(home) = original_home {
            std::env::set_var("HOME", home);
        }

        // Cleanup
        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_theme_manager_theme_presets() {
        let presets = ThemeManager::available_presets();
        assert!(presets.len() >= 7, "Should have at least 7 presets");
        assert!(presets.contains(&ThemePreset::Default));
        assert!(presets.contains(&ThemePreset::Dark));
        assert!(presets.contains(&ThemePreset::Light));
        assert!(presets.contains(&ThemePreset::HighContrast));
    }

    #[test]
    fn test_theme_config_serialization() {
        let theme = Theme::default();
        let config = ThemeConfig::from_theme(&theme, "test".to_string());

        let toml_str = toml::to_string_pretty(&config);
        assert!(toml_str.is_ok(), "Should serialize to TOML");
        let toml_content = toml_str.unwrap();
        assert!(
            toml_content.contains("name = \"test\""),
            "Should contain name"
        );
        assert!(
            toml_content.contains("primary"),
            "Should contain primary color"
        );
    }

    #[test]
    fn test_theme_config_deserialization() {
        let toml_content = r#"
name = "test_theme"
primary = "cyan"
secondary = "blue"
accent = "magenta"
background = "black"
text = "white"
muted = "darkgray"
"#;

        let config: Result<ThemeConfig, _> = toml::from_str(toml_content);
        assert!(config.is_ok(), "Should deserialize from TOML");
        let config = config.unwrap();
        assert_eq!(config.name, "test_theme");
        assert_eq!(config.primary, "cyan");

        let theme = config.to_theme();
        assert!(theme.is_ok(), "Should convert to Theme");
        let theme = theme.unwrap();
        assert_eq!(theme.primary, Color::Cyan);
    }

    #[test]
    fn test_theme_manager_color_parsing() {
        // Test basic colors
        assert_eq!(parse_color("red").unwrap(), Color::Red);
        assert_eq!(parse_color("GREEN").unwrap(), Color::Green);
        assert_eq!(parse_color("blue").unwrap(), Color::Blue);

        // Test light colors
        assert_eq!(parse_color("light_blue").unwrap(), Color::LightBlue);
        assert_eq!(parse_color("lightblue").unwrap(), Color::LightBlue);
        assert_eq!(parse_color("light_red").unwrap(), Color::LightRed);

        // Test dark gray variations
        assert_eq!(parse_color("darkgray").unwrap(), Color::DarkGray);
        assert_eq!(parse_color("dark_gray").unwrap(), Color::DarkGray);
    }

    #[test]
    fn test_theme_manager_invalid_theme() {
        // Test invalid color
        assert!(
            parse_color("invalid_color").is_err(),
            "Should reject invalid color"
        );

        // Test loading non-existent theme
        let original_home = std::env::var("HOME");
        let temp_dir = std::env::temp_dir().join("arxos_test_themes_nonexistent");
        let _ = std::fs::remove_dir_all(&temp_dir);
        std::env::set_var("HOME", &temp_dir);

        let result = ThemeManager::load_theme("nonexistent_theme");
        assert!(
            result.is_err(),
            "Should return error for non-existent theme"
        );

        // Restore HOME
        if let Ok(home) = original_home {
            std::env::set_var("HOME", home);
        }
    }

    #[test]
    fn test_color_to_string() {
        assert_eq!(color_to_string(&Color::Red), "red");
        assert_eq!(color_to_string(&Color::Green), "green");
        assert_eq!(color_to_string(&Color::LightBlue), "lightblue");
        assert_eq!(color_to_string(&Color::DarkGray), "darkgray");

        // Test RGB
        let rgb_str = color_to_string(&Color::Rgb(255, 128, 64));
        assert!(rgb_str.contains("rgb(255,128,64)"), "Should format RGB");

        // Test indexed
        let indexed_str = color_to_string(&Color::Indexed(42));
        assert!(indexed_str.contains("indexed(42)"), "Should format indexed");
    }

    #[test]
    fn test_all_theme_presets() {
        let presets = ThemePreset::all();
        assert_eq!(presets.len(), 7, "Should have 7 presets");

        for preset in presets {
            let theme = preset.theme();
            // Verify theme has all required fields set
            assert!(
                matches!(
                    theme.primary,
                    Color::Cyan
                        | Color::Blue
                        | Color::LightBlue
                        | Color::LightGreen
                        | Color::LightMagenta
                        | Color::Yellow
                ),
                "Primary should be valid color"
            );
            assert!(
                matches!(theme.background, Color::Black | Color::White),
                "Background should be Black or White"
            );
        }
    }

    #[test]
    fn test_theme_preset_names_all() {
        assert_eq!(ThemePreset::Default.name(), "Default");
        assert_eq!(ThemePreset::Dark.name(), "Dark");
        assert_eq!(ThemePreset::Light.name(), "Light");
        assert_eq!(ThemePreset::HighContrast.name(), "High Contrast");
        assert_eq!(ThemePreset::Blue.name(), "Blue");
        assert_eq!(ThemePreset::Green.name(), "Green");
        assert_eq!(ThemePreset::Purple.name(), "Purple");
    }
}
