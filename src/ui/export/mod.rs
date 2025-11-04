//! Export Views for ArxOS TUI
//!
//! Provides:
//! - Screenshot/export current TUI view
//! - Export to various formats (text, ANSI, HTML)
//! - Save widget state to file
//!
//! Note: Buffer export requires capturing the buffer during the draw() closure.
//! Use frame.buffer() inside terminal.draw() to get the buffer for export.

pub mod format;
pub mod colors;
pub mod text;
pub mod ansi;
pub mod html;
pub mod markdown;
pub mod buffer;

// Re-export public API
pub use format::ExportFormat;
pub use buffer::{export_buffer, export_current_view};

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::buffer::Buffer;
    use ratatui::layout::Rect;
    
    #[test]
    fn test_export_format_names() {
        assert_eq!(ExportFormat::Text.name(), "Text");
        assert_eq!(ExportFormat::Html.name(), "HTML");
        assert_eq!(ExportFormat::Ansi.extension(), "ansi");
    }
    
    #[test]
    fn test_color_to_css() {
        use super::colors::color_to_css;
        assert_eq!(color_to_css(ratatui::style::Color::Red), "#cc0000");
        assert_eq!(color_to_css(ratatui::style::Color::Green), "#00cc00");
    }
}

