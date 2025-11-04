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

