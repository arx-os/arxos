//! Command Palette Event Handler
//!
//! Handles user interaction with the command palette.

use super::palette::CommandPalette;
use crate::ui::{TerminalManager, Theme};
use crossterm::event::{Event, KeyCode, KeyModifiers};
use std::time::Duration;

/// Handle command palette interaction
pub fn handle_command_palette(
    terminal: &mut TerminalManager,
    theme: &Theme,
) -> Result<Option<String>, Box<dyn std::error::Error>> {
    use super::render::render_command_palette;
    
    let mut palette = CommandPalette::new();
    
    loop {
        let mouse_enabled = terminal.mouse_enabled();
        terminal.terminal().draw(|frame| {
            let area = frame.size();
            render_command_palette(frame, area, &mut palette, theme, mouse_enabled);
        })?;
        
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) => {
                    // Handle help
                    if crate::ui::handle_help_event(event.clone(), palette.help_system_mut()) {
                        continue;
                    }
                    
                    match key_event.code {
                        KeyCode::Esc | KeyCode::Char('q') => {
                            return Ok(None);
                        }
                        KeyCode::Enter => {
                            if let Some(cmd) = palette.selected_command() {
                                return Ok(Some(cmd.full_command.clone()));
                            }
                        }
                        KeyCode::Up => {
                            palette.previous();
                        }
                        KeyCode::Down => {
                            palette.next();
                        }
                        KeyCode::Char(c) => {
                            if key_event.modifiers.contains(KeyModifiers::CONTROL) && c == 'p' {
                                // Ctrl+P to open palette (already open)
                                continue;
                            } else {
                                // Add to search query
                                let mut query = palette.query().to_string();
                                query.push(c);
                                palette.update_query(query);
                            }
                        }
                        KeyCode::Backspace => {
                            let mut query = palette.query().to_string();
                            query.pop();
                            palette.update_query(query);
                        }
                        _ => {}
                    }
                }
                _ => {}
            }
        }
    }
}

