//! ANSI Export Format
//!
//! Provides ANSI-colored text export functionality.

use ratatui::buffer::Buffer;
use ratatui::style::Modifier;
use super::colors::{color_to_ansi, modifiers_to_ansi};

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
            let needs_reset = style.fg != current_fg || 
                             style.bg != current_bg || 
                             style.add_modifier != current_modifiers;
            
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

