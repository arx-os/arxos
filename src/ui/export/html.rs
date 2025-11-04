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

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::layout::Rect;
    use ratatui::style::{Color, Modifier, Style};

    #[test]
    fn test_export_as_html() {
        let area = Rect::new(0, 0, 10, 2);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Hello", Style::default());
        buffer.set_string(0, 1, "World", Style::default());
        
        let html = export_as_html(&buffer);
        assert!(html.contains("<!DOCTYPE html>"), "Should contain DOCTYPE");
        assert!(html.contains("<html>"), "Should contain html tag");
        assert!(html.contains("Hello"), "Should contain content");
        assert!(html.contains("World"), "Should contain content");
    }

    #[test]
    fn test_export_as_html_structure() {
        let area = Rect::new(0, 0, 5, 1);
        let buffer = Buffer::empty(area);
        
        let html = export_as_html(&buffer);
        assert!(html.contains("<head>"), "Should have head section");
        assert!(html.contains("<body>"), "Should have body section");
        assert!(html.contains("<pre>"), "Should use pre tag");
        assert!(html.contains("</html>"), "Should close html tag");
    }

    #[test]
    fn test_export_as_html_colors() {
        let area = Rect::new(0, 0, 5, 1);
        let mut buffer = Buffer::empty(area);
        let red_style = Style::default().fg(Color::Red);
        buffer.set_string(0, 0, "Test", red_style);
        
        let html = export_as_html(&buffer);
        assert!(html.contains("color:"), "Should contain color style");
        assert!(html.contains("#cc0000"), "Red should be #cc0000");
        assert!(html.contains("<span"), "Should use span tags");
    }

    #[test]
    fn test_export_as_html_modifiers() {
        let area = Rect::new(0, 0, 5, 1);
        let mut buffer = Buffer::empty(area);
        let bold_style = Style::default().add_modifier(Modifier::BOLD);
        buffer.set_string(0, 0, "Test", bold_style);
        
        let html = export_as_html(&buffer);
        assert!(html.contains("font-weight: bold"), "Should contain bold style");
    }

    #[test]
    fn test_export_as_html_escape_chars() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "<>&\"", Style::default());
        
        let html = export_as_html(&buffer);
        assert!(html.contains("&lt;"), "Should escape <");
        assert!(html.contains("&gt;"), "Should escape >");
        assert!(html.contains("&amp;"), "Should escape &");
        assert!(html.contains("&quot;"), "Should escape \"");
    }

    #[test]
    fn test_export_as_html_spans() {
        let area = Rect::new(0, 0, 10, 1);
        let mut buffer = Buffer::empty(area);
        buffer.set_string(0, 0, "Red", Style::default().fg(Color::Red));
        buffer.set_string(3, 0, "Green", Style::default().fg(Color::Green));
        
        let html = export_as_html(&buffer);
        assert!(html.contains("</span>"), "Should close spans");
        assert!(html.matches("<span").count() >= 2, "Should have multiple spans");
    }

    #[test]
    fn test_export_as_html_empty_buffer() {
        let area = Rect::new(0, 0, 10, 2);
        let buffer = Buffer::empty(area);
        
        let html = export_as_html(&buffer);
        assert!(html.contains("<!DOCTYPE html>"), "Should have structure");
        assert!(html.contains("</html>"), "Should close properly");
    }
}

