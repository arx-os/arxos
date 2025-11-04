//! Help System Event Handling
//!
//! Handles keyboard events for the help system.

use super::types::HelpSystem;
use crossterm::event::{Event, KeyCode, KeyModifiers};

/// Handle help overlay events
pub fn handle_help_event(
    event: Event,
    help_system: &mut HelpSystem,
) -> bool {
    match event {
        Event::Key(key_event) => {
            // Universal help toggle
            if key_event.code == KeyCode::Char('?') || 
               (key_event.code == KeyCode::Char('h') && !key_event.modifiers.contains(KeyModifiers::CONTROL)) {
                help_system.toggle_overlay();
                return true;
            }
            
            // Cheat sheet toggle
            if key_event.code == KeyCode::Char('h') && key_event.modifiers.contains(KeyModifiers::CONTROL) {
                help_system.toggle_cheat_sheet();
                return true;
            }
            
            // Close help with Esc or q (when help is showing)
            if (help_system.show_overlay || help_system.show_cheat_sheet) &&
               (key_event.code == KeyCode::Esc || key_event.code == KeyCode::Char('q')) {
                help_system.show_overlay = false;
                help_system.show_cheat_sheet = false;
                return true;
            }
        }
        _ => {}
    }
    false
}

