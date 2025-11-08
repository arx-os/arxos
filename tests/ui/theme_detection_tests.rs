//! Tests for theme detection functionality
//!
//! Tests platform-specific theme detection (macOS, Linux, Windows)
//! and terminal environment variable detection

use arxui::tui::Theme;

/// Test theme detection returns valid theme
#[test]
fn test_theme_detection_returns_valid_theme() {
    let theme = Theme::from_terminal();
    
    // Verify theme has valid colors
    assert!(matches!(theme.background, ratatui::style::Color::Black | ratatui::style::Color::White));
    assert!(matches!(theme.text, ratatui::style::Color::Black | ratatui::style::Color::White));
    assert!(matches!(theme.primary, 
        ratatui::style::Color::Cyan | 
        ratatui::style::Color::Blue | 
        ratatui::style::Color::LightBlue |
        ratatui::style::Color::LightGreen |
        ratatui::style::Color::LightMagenta |
        ratatui::style::Color::Yellow));
}

/// Test theme detection from config
#[test]
fn test_theme_from_config() {
    let theme = Theme::from_config();
    
    // Should return a valid theme (either from config or auto-detected)
    assert!(matches!(theme.background, ratatui::style::Color::Black | ratatui::style::Color::White));
    assert!(matches!(theme.text, ratatui::style::Color::Black | ratatui::style::Color::White));
}

/// Test modern theme creation
#[test]
fn test_modern_theme() {
    let theme = Theme::modern();
    
    // Modern theme should have dark background
    assert_eq!(theme.background, ratatui::style::Color::Black);
    assert_eq!(theme.text, ratatui::style::Color::White);
    assert_eq!(theme.primary, ratatui::style::Color::Cyan);
    assert_eq!(theme.secondary, ratatui::style::Color::Blue);
    assert_eq!(theme.accent, ratatui::style::Color::Yellow);
}

/// Test system color mapping
#[test]
fn test_system_color_mapping() {
    // Test all reserved systems have colors
    let systems = vec![
        "hvac", "plumbing", "electrical", "fire", "lighting",
        "security", "elevators", "roof", "windows", "doors",
        "structure", "envelope", "it", "furniture",
    ];
    
    for system in systems {
        let color = Theme::system_color(system);
        // Verify color is valid (not default/unknown)
        assert!(!matches!(color, ratatui::style::Color::Reset));
    }
    
    // Test custom system gets default color
    let custom_color = Theme::system_color("custom-system");
    assert_eq!(custom_color, ratatui::style::Color::White);
}

/// Test COLORFGBG environment variable parsing (if set)
#[test]
fn test_colorfgbg_parsing() {
    // Save original value
    let original = std::env::var("COLORFGBG").ok();
    
    // Test dark background (0-7)
    std::env::set_var("COLORFGBG", "15;0"); // White text on black background
    let theme1 = Theme::from_terminal();
    // Should detect dark mode (background < 8)
    assert_eq!(theme1.background, ratatui::style::Color::Black);
    
    // Test light background (8-15)
    std::env::set_var("COLORFGBG", "0;15"); // Black text on white background
    let theme2 = Theme::from_terminal();
    // Should detect light mode (background >= 8)
    assert_eq!(theme2.background, ratatui::style::Color::White);
    
    // Restore original value
    if let Some(orig) = original {
        std::env::set_var("COLORFGBG", orig);
    } else {
        std::env::remove_var("COLORFGBG");
    }
}

/// Test TERM_PROGRAM detection
#[test]
fn test_term_program_detection() {
    // Save original value
    let original = std::env::var("TERM_PROGRAM").ok();
    
    // Test iTerm detection
    std::env::set_var("TERM_PROGRAM", "iTerm.app");
    let theme1 = Theme::from_terminal();
    // Should default to dark (iTerm is typically dark)
    assert_eq!(theme1.background, ratatui::style::Color::Black);
    
    // Test Apple_Terminal detection
    std::env::set_var("TERM_PROGRAM", "Apple_Terminal");
    let theme2 = Theme::from_terminal();
    // Should default to dark (Apple Terminal is typically dark)
    assert_eq!(theme2.background, ratatui::style::Color::Black);
    
    // Restore original value
    if let Some(orig) = original {
        std::env::set_var("TERM_PROGRAM", orig);
    } else {
        std::env::remove_var("TERM_PROGRAM");
    }
}

/// Test theme consistency
#[test]
fn test_theme_consistency() {
    // Multiple calls should return consistent themes
    let theme1 = Theme::from_terminal();
    let theme2 = Theme::from_terminal();
    
    // Themes should be consistent (same detection logic)
    assert_eq!(theme1.background, theme2.background);
    assert_eq!(theme1.text, theme2.text);
}

/// Test theme defaults when detection fails
#[test]
fn test_theme_defaults() {
    // Save original values
    let original_colorfgbg = std::env::var("COLORFGBG").ok();
    let original_term = std::env::var("TERM_PROGRAM").ok();
    
    // Remove environment variables
    std::env::remove_var("COLORFGBG");
    std::env::remove_var("TERM_PROGRAM");
    
    // Should still return a valid theme (defaults to dark)
    let theme = Theme::from_terminal();
    assert!(matches!(theme.background, ratatui::style::Color::Black | ratatui::style::Color::White));
    
    // Restore original values
    if let Some(orig) = original_colorfgbg {
        std::env::set_var("COLORFGBG", orig);
    }
    if let Some(orig) = original_term {
        std::env::set_var("TERM_PROGRAM", orig);
    }
}

