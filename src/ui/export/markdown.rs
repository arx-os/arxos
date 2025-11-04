//! Markdown Export Format
//!
//! Provides Markdown export functionality.

use ratatui::buffer::Buffer;
use super::text::export_as_text;

/// Export buffer as Markdown
pub fn export_as_markdown(buffer: &Buffer) -> String {
    let mut output = String::new();
    output.push_str("```\n");
    output.push_str(&export_as_text(buffer));
    output.push_str("```\n");
    output
}

