//! Color Conversion Utilities
//!
//! Provides functions for converting Ratatui colors to various formats.

/// Convert Color to ANSI escape code
pub fn color_to_ansi(color: ratatui::style::Color, is_fg: bool) -> String {
    let base = if is_fg { 30 } else { 40 };
    match color {
        ratatui::style::Color::Black => format!("\x1b[{}m", base),
        ratatui::style::Color::Red => format!("\x1b[{}m", base + 1),
        ratatui::style::Color::Green => format!("\x1b[{}m", base + 2),
        ratatui::style::Color::Yellow => format!("\x1b[{}m", base + 3),
        ratatui::style::Color::Blue => format!("\x1b[{}m", base + 4),
        ratatui::style::Color::Magenta => format!("\x1b[{}m", base + 5),
        ratatui::style::Color::Cyan => format!("\x1b[{}m", base + 6),
        ratatui::style::Color::White => format!("\x1b[{}m", base + 7),
        ratatui::style::Color::DarkGray => format!("\x1b[{};1m", base),
        ratatui::style::Color::LightRed => format!("\x1b[{};1m", base + 1),
        ratatui::style::Color::LightGreen => format!("\x1b[{};1m", base + 2),
        ratatui::style::Color::LightYellow => format!("\x1b[{};1m", base + 3),
        ratatui::style::Color::LightBlue => format!("\x1b[{};1m", base + 4),
        ratatui::style::Color::LightMagenta => format!("\x1b[{};1m", base + 5),
        ratatui::style::Color::LightCyan => format!("\x1b[{};1m", base + 6),
        ratatui::style::Color::Gray => format!("\x1b[{}m", base + 7),
        ratatui::style::Color::Rgb(r, g, b) => {
            if is_fg {
                format!("\x1b[38;2;{};{};{}m", r, g, b)
            } else {
                format!("\x1b[48;2;{};{};{}m", r, g, b)
            }
        }
        ratatui::style::Color::Indexed(i) => {
            if is_fg {
                format!("\x1b[38;5;{}m", i)
            } else {
                format!("\x1b[48;5;{}m", i)
            }
        }
        _ => String::new(),
    }
}

/// Convert modifiers to ANSI codes
pub fn modifiers_to_ansi(modifiers: ratatui::style::Modifier) -> String {
    let mut codes = Vec::new();
    if modifiers.contains(ratatui::style::Modifier::BOLD) {
        codes.push("1");
    }
    if modifiers.contains(ratatui::style::Modifier::ITALIC) {
        codes.push("3");
    }
    if modifiers.contains(ratatui::style::Modifier::UNDERLINED) {
        codes.push("4");
    }
    if codes.is_empty() {
        String::new()
    } else {
        format!("\x1b[{}m", codes.join(";"))
    }
}

/// Convert Color to CSS color string
pub fn color_to_css(color: ratatui::style::Color) -> String {
    match color {
        ratatui::style::Color::Black => "#000000".to_string(),
        ratatui::style::Color::Red => "#cc0000".to_string(),
        ratatui::style::Color::Green => "#00cc00".to_string(),
        ratatui::style::Color::Yellow => "#cccc00".to_string(),
        ratatui::style::Color::Blue => "#0000cc".to_string(),
        ratatui::style::Color::Magenta => "#cc00cc".to_string(),
        ratatui::style::Color::Cyan => "#00cccc".to_string(),
        ratatui::style::Color::White => "#cccccc".to_string(),
        ratatui::style::Color::DarkGray => "#666666".to_string(),
        ratatui::style::Color::LightRed => "#ff0000".to_string(),
        ratatui::style::Color::LightGreen => "#00ff00".to_string(),
        ratatui::style::Color::LightYellow => "#ffff00".to_string(),
        ratatui::style::Color::LightBlue => "#0000ff".to_string(),
        ratatui::style::Color::LightMagenta => "#ff00ff".to_string(),
        ratatui::style::Color::LightCyan => "#00ffff".to_string(),
        ratatui::style::Color::Gray => "#888888".to_string(),
        ratatui::style::Color::Rgb(r, g, b) => format!("#{:02x}{:02x}{:02x}", r, g, b),
        ratatui::style::Color::Indexed(i) => {
            // Convert indexed color to approximate RGB
            format!("#{:02x}{:02x}{:02x}", i, i, i)
        }
        _ => "#ffffff".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::style::Color;

    #[test]
    fn test_color_to_ansi_basic() {
        let fg = color_to_ansi(Color::Red, true);
        assert!(fg.contains("31"), "Red foreground should be 31");
        
        let bg = color_to_ansi(Color::Green, false);
        assert!(bg.contains("42"), "Green background should be 42");
    }

    #[test]
    fn test_color_to_ansi_rgb() {
        let fg = color_to_ansi(Color::Rgb(255, 128, 64), true);
        assert!(fg.contains("38;2"), "RGB should use 38;2 sequence");
        assert!(fg.contains("255"));
        assert!(fg.contains("128"));
        assert!(fg.contains("64"));
        
        let bg = color_to_ansi(Color::Rgb(10, 20, 30), false);
        assert!(bg.contains("48;2"), "RGB background should use 48;2 sequence");
    }

    #[test]
    fn test_color_to_ansi_indexed() {
        let fg = color_to_ansi(Color::Indexed(42), true);
        assert!(fg.contains("38;5"), "Indexed should use 38;5 sequence");
        assert!(fg.contains("42"));
        
        let bg = color_to_ansi(Color::Indexed(100), false);
        assert!(bg.contains("48;5"), "Indexed background should use 48;5 sequence");
    }

    #[test]
    fn test_color_to_ansi_foreground() {
        let colors = vec![
            (Color::Black, 30),
            (Color::Red, 31),
            (Color::Green, 32),
            (Color::Yellow, 33),
            (Color::Blue, 34),
            (Color::Magenta, 35),
            (Color::Cyan, 36),
            (Color::White, 37),
        ];
        
        for (color, code) in colors {
            let ansi = color_to_ansi(color, true);
            assert!(ansi.contains(&code.to_string()), 
                "Color {:?} should have code {}", color, code);
        }
    }

    #[test]
    fn test_color_to_ansi_background() {
        let colors = vec![
            (Color::Black, 40),
            (Color::Red, 41),
            (Color::Green, 42),
            (Color::Yellow, 43),
            (Color::Blue, 44),
            (Color::Magenta, 45),
            (Color::Cyan, 46),
            (Color::White, 47),
        ];
        
        for (color, code) in colors {
            let ansi = color_to_ansi(color, false);
            assert!(ansi.contains(&code.to_string()), 
                "Background color {:?} should have code {}", color, code);
        }
    }

    #[test]
    fn test_modifiers_to_ansi() {
        let modifiers = ratatui::style::Modifier::empty();
        let ansi = modifiers_to_ansi(modifiers);
        assert!(ansi.is_empty(), "Empty modifiers should produce empty string");
    }

    #[test]
    fn test_modifiers_to_ansi_bold() {
        let modifiers = ratatui::style::Modifier::BOLD;
        let ansi = modifiers_to_ansi(modifiers);
        assert!(ansi.contains("1"), "Bold should use code 1");
        assert!(ansi.contains("\x1b["), "Should contain ANSI escape");
    }

    #[test]
    fn test_modifiers_to_ansi_italic() {
        let modifiers = ratatui::style::Modifier::ITALIC;
        let ansi = modifiers_to_ansi(modifiers);
        assert!(ansi.contains("3"), "Italic should use code 3");
    }

    #[test]
    fn test_modifiers_to_ansi_underlined() {
        let modifiers = ratatui::style::Modifier::UNDERLINED;
        let ansi = modifiers_to_ansi(modifiers);
        assert!(ansi.contains("4"), "Underlined should use code 4");
    }

    #[test]
    fn test_modifiers_to_ansi_combined() {
        let modifiers = ratatui::style::Modifier::BOLD | ratatui::style::Modifier::ITALIC;
        let ansi = modifiers_to_ansi(modifiers);
        assert!(ansi.contains("1"), "Should contain bold");
        assert!(ansi.contains("3"), "Should contain italic");
        assert!(ansi.contains(";"), "Combined should use semicolon separator");
    }

    #[test]
    fn test_color_to_css_basic() {
        assert_eq!(color_to_css(Color::Black), "#000000");
        assert_eq!(color_to_css(Color::Red), "#cc0000");
        assert_eq!(color_to_css(Color::Green), "#00cc00");
        assert_eq!(color_to_css(Color::White), "#cccccc");
    }

    #[test]
    fn test_color_to_css_rgb() {
        let css = color_to_css(Color::Rgb(255, 128, 64));
        assert_eq!(css, "#ff8040", "RGB should convert to hex");
        
        let css2 = color_to_css(Color::Rgb(0, 0, 0));
        assert_eq!(css2, "#000000", "Black RGB should be #000000");
        
        let css3 = color_to_css(Color::Rgb(255, 255, 255));
        assert_eq!(css3, "#ffffff", "White RGB should be #ffffff");
    }

    #[test]
    fn test_color_to_css_indexed() {
        let css = color_to_css(Color::Indexed(128));
        assert_eq!(css, "#808080", "Indexed color should convert to hex");
        
        let css2 = color_to_css(Color::Indexed(255));
        assert_eq!(css2, "#ffffff", "Indexed 255 should be white");
    }

    #[test]
    fn test_color_to_css_hex_format() {
        let css = color_to_css(Color::Rgb(10, 20, 30));
        assert_eq!(css.len(), 7, "Hex should be 7 characters");
        assert!(css.starts_with("#"), "Should start with #");
        // Verify hex format (lowercase)
        assert!(css.chars().skip(1).all(|c| c.is_ascii_hexdigit()),
            "Should contain only hex digits");
    }
}

