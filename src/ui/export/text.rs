//! Text Export Format
//!
//! Provides plain text export functionality.

use ratatui::buffer::Buffer;

/// Export buffer as plain text (no colors)
pub fn export_as_text(buffer: &Buffer) -> String {
    let mut output = String::new();
    for y in 0..buffer.area.height {
        let mut line = String::new();
        for x in 0..buffer.area.width {
            let cell = buffer.get(x, y);
            // Access cell content - in ratatui, cells store content
            let ch = cell.symbol.chars().next().unwrap_or(' ');
            line.push(ch);
        }
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

    #[test]
    fn test_export_as_text() {
        let area = Rect::new(0, 0, 10, 2);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Hello", ratatui::style::Style::default());
        buffer.set_string(0, 1, "World", ratatui::style::Style::default());
        
        let text = export_as_text(&buffer);
        assert!(text.contains("Hello"), "Should contain Hello");
        assert!(text.contains("World"), "Should contain World");
        assert!(text.contains('\n'), "Should contain newlines");
    }

    #[test]
    fn test_export_as_text_empty() {
        let area = Rect::new(0, 0, 10, 2);
        let buffer = Buffer::empty(area);
        
        let text = export_as_text(&buffer);
        // Should have newlines even for empty buffer
        assert!(text.contains('\n'), "Should contain newlines");
    }

    #[test]
    fn test_export_as_text_multiline() {
        let area = Rect::new(0, 0, 10, 3);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Line 1", ratatui::style::Style::default());
        buffer.set_string(0, 1, "Line 2", ratatui::style::Style::default());
        buffer.set_string(0, 2, "Line 3", ratatui::style::Style::default());
        
        let text = export_as_text(&buffer);
        let lines: Vec<&str> = text.lines().collect();
        assert!(lines.len() >= 3, "Should have at least 3 lines");
    }

    #[test]
    fn test_export_as_text_trim_whitespace() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Hello   ", ratatui::style::Style::default());
        
        let text = export_as_text(&buffer);
        let line = text.lines().next().unwrap();
        assert!(!line.ends_with(' '), "Trailing whitespace should be trimmed");
        assert_eq!(line.trim_end(), "Hello", "Should match trimmed content");
    }

    #[test]
    fn test_export_as_text_special_chars() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Test!@#$%", ratatui::style::Style::default());
        
        let text = export_as_text(&buffer);
        assert!(text.contains('!'), "Should preserve special characters");
        assert!(text.contains('@'), "Should preserve @");
        assert!(text.contains('#'), "Should preserve #");
    }
}

