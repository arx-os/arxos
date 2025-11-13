//! ANSI Export Format
//!
//! Provides ANSI-colored text export functionality.

use super::colors::{color_to_ansi, modifiers_to_ansi};
use ratatui::buffer::Buffer;
use ratatui::style::Modifier;

/// Export buffer as ANSI colored text
pub fn export_as_ansi(buffer: &Buffer) -> String {
    let mut output = String::new();
    for y in 0..buffer.area.height {
        let mut line = String::new();
        let mut current_fg = None;
        let mut current_bg = None;
        let mut current_modifiers = Modifier::empty();

        for x in 0..buffer.area.width {
            let cell = buffer.get(x, y);
            let symbol = &cell.symbol;
            let style = cell.style();

            // Check if we need to reset or change styles
            let needs_reset = style.fg != current_fg
                || style.bg != current_bg
                || style.add_modifier != current_modifiers;

            if needs_reset {
                // Reset if switching styles
                if current_fg.is_some() || current_bg.is_some() || !current_modifiers.is_empty() {
                    line.push_str("\x1b[0m");
                }

                // Apply new foreground color
                if style.fg != current_fg {
                    if let Some(fg) = style.fg {
                        line.push_str(&color_to_ansi(fg, true));
                    }
                    current_fg = style.fg;
                }

                // Apply new background color
                if style.bg != current_bg {
                    if let Some(bg) = style.bg {
                        line.push_str(&color_to_ansi(bg, false));
                    }
                    current_bg = style.bg;
                }

                // Apply modifiers
                if style.add_modifier != current_modifiers {
                    line.push_str(&modifiers_to_ansi(style.add_modifier));
                    current_modifiers = style.add_modifier;
                }
            }

            line.push_str(symbol);
        }

        // Reset at end of line
        line.push_str("\x1b[0m");

        // Trim trailing whitespace
        line = line.trim_end().to_string();
        if !line.is_empty() || y < buffer.area.height - 1 {
            output.push_str(&line);
            output.push('\n');
        }
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::layout::Rect;
    use ratatui::style::{Color, Modifier, Style};

    #[test]
    fn test_export_as_ansi() {
        let area = Rect::new(0, 0, 10, 2);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Hello", Style::default());
        buffer.set_string(0, 1, "World", Style::default());

        let ansi = export_as_ansi(&buffer);
        assert!(ansi.contains("Hello"), "Should contain Hello");
        assert!(ansi.contains("World"), "Should contain World");
    }

    #[test]
    fn test_export_as_ansi_colors() {
        let area = Rect::new(0, 0, 5, 1);
        let mut buffer = Buffer::empty(area);
        let red_style = Style::default().fg(Color::Red);
        buffer.set_string(0, 0, "Test", red_style);

        let ansi = export_as_ansi(&buffer);
        assert!(ansi.contains("\x1b["), "Should contain ANSI escape codes");
        assert!(ansi.contains("31"), "Red should use code 31");
    }

    #[test]
    fn test_export_as_ansi_reset_codes() {
        let area = Rect::new(0, 0, 5, 1);
        let mut buffer = Buffer::empty(area);
        let styled = Style::default().fg(Color::Green);
        buffer.set_string(0, 0, "Test", styled);

        let ansi = export_as_ansi(&buffer);
        assert!(ansi.contains("\x1b[0m"), "Should contain reset code at end");
    }

    #[test]
    fn test_export_as_ansi_modifiers() {
        let area = Rect::new(0, 0, 5, 1);
        let mut buffer = Buffer::empty(area);
        let bold_style = Style::default().add_modifier(Modifier::BOLD);
        buffer.set_string(0, 0, "Test", bold_style);

        let ansi = export_as_ansi(&buffer);
        assert!(ansi.contains("1"), "Bold should use code 1");
    }

    #[test]
    fn test_export_as_ansi_style_changes() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Red", Style::default().fg(Color::Red));
        buffer.set_string(3, 0, "Green", Style::default().fg(Color::Green));

        let ansi = export_as_ansi(&buffer);
        assert!(ansi.contains("31"), "Should contain red code");
        assert!(ansi.contains("32"), "Should contain green code");
        assert!(ansi.contains("\x1b[0m"), "Should reset between changes");
    }

    #[test]
    fn test_export_as_ansi_empty_buffer() {
        let area = Rect::new(0, 0, 10, 2);
        let buffer = Buffer::empty(area);

        let ansi = export_as_ansi(&buffer);
        // Should still have newlines
        assert!(ansi.contains('\n'), "Should contain newlines");
    }
}
