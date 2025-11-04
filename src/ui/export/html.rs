//! HTML Export Format
//!
//! Provides HTML export functionality with color preservation.

use ratatui::buffer::Buffer;
use ratatui::style::Modifier;
use super::colors::color_to_css;

/// Export buffer as HTML
pub fn export_as_html(buffer: &Buffer) -> String {
    let mut output = String::new();
    output.push_str("<!DOCTYPE html>\n<html>\n<head>\n");
    output.push_str("<meta charset=\"utf-8\">\n");
    output.push_str("<title>ArxOS TUI Export</title>\n");
    output.push_str("<style>\n");
    output.push_str("body { font-family: 'Courier New', monospace; background: #000; color: #fff; }\n");
    output.push_str("pre { margin: 0; }\n");
    output.push_str("</style>\n");
    output.push_str("</head>\n<body>\n<pre>\n");
    
    for y in 0..buffer.area.height {
        let mut line = String::new();
        let mut current_fg = None;
        let mut current_bg = None;
        let mut current_modifiers = Modifier::empty();
        
        for x in 0..buffer.area.width {
            let cell = buffer.get(x, y);
            let symbol = &cell.symbol;
            let style = cell.style();
            
            // Check if we need a new span
            let needs_span = style.fg != current_fg || 
                            style.bg != current_bg || 
                            style.add_modifier != current_modifiers;
            
            if needs_span {
                // Close previous span if any
                if current_fg.is_some() || current_bg.is_some() || !current_modifiers.is_empty() {
                    line.push_str("</span>");
                }
                
                // Open new span with styles
                let mut span_style = String::new();
                if let Some(fg) = style.fg {
                    span_style.push_str(&format!("color: {}; ", color_to_css(fg)));
                }
                if let Some(bg) = style.bg {
                    span_style.push_str(&format!("background-color: {}; ", color_to_css(bg)));
                }
                if style.add_modifier.contains(Modifier::BOLD) {
                    span_style.push_str("font-weight: bold; ");
                }
                if style.add_modifier.contains(Modifier::ITALIC) {
                    span_style.push_str("font-style: italic; ");
                }
                if style.add_modifier.contains(Modifier::UNDERLINED) {
                    span_style.push_str("text-decoration: underline; ");
                }
                
                if !span_style.is_empty() {
                    line.push_str(&format!("<span style=\"{}\">", span_style.trim_end()));
                }
                
                current_fg = style.fg;
                current_bg = style.bg;
                current_modifiers = style.add_modifier;
            }
            
            // Escape HTML special characters
            let escaped = symbol
                .replace('&', "&amp;")
                .replace('<', "&lt;")
                .replace('>', "&gt;")
                .replace('"', "&quot;");
            line.push_str(&escaped);
        }
        
        // Close any open span
        if current_fg.is_some() || current_bg.is_some() || !current_modifiers.is_empty() {
            line.push_str("</span>");
        }
        
        output.push_str(&line);
        output.push('\n');
    }
    
    output.push_str("</pre>\n</body>\n</html>");
    output
}

