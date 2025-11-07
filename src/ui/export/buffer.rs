//! Buffer Export Functions
//!
//! Provides main export functions for terminal buffers.

use super::ansi::export_as_ansi;
use super::format::ExportFormat;
use super::html::export_as_html;
use super::markdown::export_as_markdown;
use super::text::export_as_text;
use ratatui::buffer::Buffer;
use std::fs;
use std::path::PathBuf;

/// Export a buffer to a file
///
/// Usage: Inside terminal.draw() closure, use frame.buffer() to get the buffer
/// ```rust,no_run
/// terminal.draw(|frame| {
///     // ... render widgets ...
///     let buffer = frame.buffer();
///     export_buffer(buffer, ExportFormat::Text, PathBuf::from("output.txt"))?;
/// })
/// ```
pub fn export_buffer(
    buffer: &Buffer,
    format: ExportFormat,
    output_path: PathBuf,
) -> Result<(), Box<dyn std::error::Error>> {
    let content = match format {
        ExportFormat::Text => export_as_text(buffer),
        ExportFormat::Ansi => export_as_ansi(buffer),
        ExportFormat::Html => export_as_html(buffer),
        ExportFormat::Markdown => export_as_markdown(buffer),
    };

    fs::write(&output_path, content)?;
    Ok(())
}

/// Export current terminal view
///
/// **Note:** Due to Ratatui's architecture, the terminal buffer is only accessible
/// within the `draw()` closure. This function provides a helper pattern, but for
/// direct buffer access, use `export_buffer()` with `frame.buffer()` inside your
/// render loop.
///
/// **Recommended Usage Pattern:**
/// ```rust,no_run
/// use crate::ui::{TerminalManager, export_buffer, ExportFormat};
///
/// let mut terminal = TerminalManager::new()?;
/// terminal.terminal().draw(|frame| {
///     // ... render your widgets ...
///     
///     // Export buffer after rendering
///     let buffer = frame.buffer();
///     export_buffer(buffer, ExportFormat::Text, PathBuf::from("output.txt"))?;
/// })?;
/// ```
///
/// This function exists for API completeness but delegates to the pattern above.
pub fn export_current_view(
    _terminal: &mut ratatui::Terminal<ratatui::backend::CrosstermBackend<std::io::Stdout>>,
    _format: ExportFormat,
    _output_path: PathBuf,
) -> Result<(), Box<dyn std::error::Error>> {
    // This is a design limitation of Ratatui - the buffer is only accessible
    // within the draw() closure. We provide clear documentation on the correct pattern.
    Err(
        "Terminal buffer access requires use within draw() closure.\n\n\
        Use this pattern instead:\n\
        terminal.draw(|frame| {\n\
            // ... render widgets ...\n\
            let buffer = frame.buffer();\n\
            export_buffer(buffer, ExportFormat::Text, PathBuf::from(\"output.txt\"))?;\n\
        })?;\n\n\
        See export_buffer() documentation for details."
            .into(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::buffer::Buffer;
    use ratatui::layout::Rect;

    #[test]
    fn test_export_buffer_text() {
        let area = Rect::new(0, 0, 10, 2);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Hello", ratatui::style::Style::default());
        buffer.set_string(0, 1, "World", ratatui::style::Style::default());

        let temp_file = std::env::temp_dir().join("test_export_text.txt");
        let result = export_buffer(&buffer, ExportFormat::Text, temp_file.clone());
        assert!(result.is_ok(), "Should export successfully");

        let content = std::fs::read_to_string(&temp_file).unwrap();
        assert!(content.contains("Hello"), "File should contain content");
        assert!(content.contains("World"), "File should contain content");

        // Cleanup
        let _ = std::fs::remove_file(&temp_file);
    }

    #[test]
    fn test_export_buffer_ansi() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Test", ratatui::style::Style::default());

        let temp_file = std::env::temp_dir().join("test_export_ansi.ansi");
        let result = export_buffer(&buffer, ExportFormat::Ansi, temp_file.clone());
        assert!(result.is_ok(), "Should export ANSI successfully");

        let content = std::fs::read_to_string(&temp_file).unwrap();
        assert!(content.contains("Test"), "File should contain content");

        // Cleanup
        let _ = std::fs::remove_file(&temp_file);
    }

    #[test]
    fn test_export_buffer_html() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Test", ratatui::style::Style::default());

        let temp_file = std::env::temp_dir().join("test_export_html.html");
        let result = export_buffer(&buffer, ExportFormat::Html, temp_file.clone());
        assert!(result.is_ok(), "Should export HTML successfully");

        let content = std::fs::read_to_string(&temp_file).unwrap();
        assert!(content.contains("<!DOCTYPE html>"), "File should be HTML");
        assert!(content.contains("Test"), "File should contain content");

        // Cleanup
        let _ = std::fs::remove_file(&temp_file);
    }

    #[test]
    fn test_export_buffer_markdown() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Test", ratatui::style::Style::default());

        let temp_file = std::env::temp_dir().join("test_export_md.md");
        let result = export_buffer(&buffer, ExportFormat::Markdown, temp_file.clone());
        assert!(result.is_ok(), "Should export Markdown successfully");

        let content = std::fs::read_to_string(&temp_file).unwrap();
        assert!(
            content.starts_with("```"),
            "File should start with code block"
        );
        assert!(content.contains("Test"), "File should contain content");

        // Cleanup
        let _ = std::fs::remove_file(&temp_file);
    }

    #[test]
    fn test_export_buffer_file_write() {
        let area = Rect::new(0, 0, 15, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Test Content", ratatui::style::Style::default());

        let temp_file = std::env::temp_dir().join("test_export_write.txt");
        let result = export_buffer(&buffer, ExportFormat::Text, temp_file.clone());

        assert!(result.is_ok(), "Should write file successfully");
        assert!(temp_file.exists(), "File should exist");

        let content = std::fs::read_to_string(&temp_file).unwrap();
        assert!(content.contains("Test"), "Content should contain 'Test'");
        assert!(
            content.contains("Content"),
            "Content should contain 'Content'"
        );

        // Cleanup
        let _ = std::fs::remove_file(&temp_file);
    }

    #[test]
    fn test_export_current_view_error() {
        use ratatui::backend::CrosstermBackend;
        let mut terminal =
            ratatui::Terminal::new(CrosstermBackend::new(std::io::stdout())).unwrap();

        let result = export_current_view(
            &mut terminal,
            ExportFormat::Text,
            std::path::PathBuf::from("test.txt"),
        );

        assert!(
            result.is_err(),
            "Should return error for Ratatui limitation"
        );
        let error_msg = result.unwrap_err().to_string();
        assert!(
            error_msg.contains("draw() closure"),
            "Error should mention draw() closure"
        );
        assert!(
            error_msg.contains("export_buffer"),
            "Error should mention export_buffer"
        );
    }
}
