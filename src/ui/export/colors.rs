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

