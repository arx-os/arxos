//! Markdown Export Format
//!
//! Provides Markdown export functionality.

use super::text::export_as_text;
use ratatui::buffer::Buffer;

/// Export buffer as Markdown
pub fn export_as_markdown(buffer: &Buffer) -> String {
    let mut output = String::new();
    output.push_str("```\n");
    output.push_str(&export_as_text(buffer));
    output.push_str("```\n");
    output
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::layout::Rect;

    #[test]
    fn test_export_as_markdown() {
        let area = Rect::new(0, 0, 10, 2);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Hello", ratatui::style::Style::default());
        buffer.set_string(0, 1, "World", ratatui::style::Style::default());

        let markdown = export_as_markdown(&buffer);
        assert!(markdown.starts_with("```"), "Should start with code block");
        assert!(markdown.ends_with("```\n"), "Should end with code block");
        assert!(markdown.contains("Hello"), "Should contain content");
        assert!(markdown.contains("World"), "Should contain content");
    }

    #[test]
    fn test_export_as_markdown_code_block() {
        let area = Rect::new(0, 0, 5, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Test", ratatui::style::Style::default());

        let markdown = export_as_markdown(&buffer);
        let lines: Vec<&str> = markdown.lines().collect();
        assert_eq!(lines[0], "```", "First line should be opening code block");
        assert!(
            lines.last().unwrap().starts_with("```"),
            "Last line should close code block"
        );
    }

    #[test]
    fn test_export_as_markdown_uses_text() {
        let area = Rect::new(0, 0, 10, 2);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Line1", ratatui::style::Style::default());
        buffer.set_string(0, 1, "Line2", ratatui::style::Style::default());

        let markdown = export_as_markdown(&buffer);
        // Should contain the text content (not wrapped twice)
        assert!(markdown.contains("Line1"), "Should contain first line");
        assert!(markdown.contains("Line2"), "Should contain second line");
    }
}
