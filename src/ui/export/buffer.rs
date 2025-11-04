//! Buffer Export Functions
//!
//! Provides main export functions for terminal buffers.

use super::format::ExportFormat;
use super::text::export_as_text;
use super::ansi::export_as_ansi;
use super::html::export_as_html;
use super::markdown::export_as_markdown;
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
    fn test_export_as_text() {
        let area = Rect::new(0, 0, 5, 2);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Hello", ratatui::style::Style::default());
        buffer.set_string(0, 1, "World", ratatui::style::Style::default());
        
        let text = export_as_text(&buffer);
        assert!(text.contains('H'));
        assert!(text.contains('W'));
    }
}

