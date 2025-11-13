//! Help System Event Handling
//!
//! Handles keyboard events for the help system.

use super::types::HelpSystem;
use crossterm::event::{Event, KeyCode, KeyModifiers};

/// Handle help overlay events
pub fn handle_help_event(event: Event, help_system: &mut HelpSystem) -> bool {
    if let Event::Key(key_event) = event {
        // Universal help toggle
        if key_event.code == KeyCode::Char('?')
            || (key_event.code == KeyCode::Char('h')
                && !key_event.modifiers.contains(KeyModifiers::CONTROL))
        {
            help_system.toggle_overlay();
            return true;
        }

        // Cheat sheet toggle
        if key_event.code == KeyCode::Char('h')
            && key_event.modifiers.contains(KeyModifiers::CONTROL)
        {
            help_system.toggle_cheat_sheet();
            return true;
        }

        // Close help with Esc or q (when help is showing)
        if (help_system.show_overlay || help_system.show_cheat_sheet)
            && (key_event.code == KeyCode::Esc || key_event.code == KeyCode::Char('q'))
        {
            help_system.show_overlay = false;
            help_system.show_cheat_sheet = false;
            return true;
        }
    }
    false
}

#[cfg(test)]
mod tests {
    use super::super::types::HelpContext;
    use super::*;
    use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers};

    #[test]
    fn test_handle_help_event_question_mark() {
        let mut system = HelpSystem::new(HelpContext::General);
        assert!(!system.show_overlay);

        let event = Event::Key(KeyEvent {
            code: KeyCode::Char('?'),
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let handled = handle_help_event(event, &mut system);
        assert!(handled, "Should handle question mark");
        assert!(system.show_overlay, "Should toggle overlay on");
    }

    #[test]
    fn test_handle_help_event_h_key() {
        let mut system = HelpSystem::new(HelpContext::General);
        assert!(!system.show_overlay);

        let event = Event::Key(KeyEvent {
            code: KeyCode::Char('h'),
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let handled = handle_help_event(event, &mut system);
        assert!(handled, "Should handle h key");
        assert!(system.show_overlay, "Should toggle overlay on");
    }

    #[test]
    fn test_handle_help_event_ctrl_h() {
        let mut system = HelpSystem::new(HelpContext::General);
        assert!(!system.show_cheat_sheet);

        let event = Event::Key(KeyEvent {
            code: KeyCode::Char('h'),
            modifiers: KeyModifiers::CONTROL,
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let handled = handle_help_event(event, &mut system);
        assert!(handled, "Should handle Ctrl+H");
        assert!(system.show_cheat_sheet, "Should toggle cheat sheet on");
    }

    #[test]
    fn test_handle_help_event_esc_close() {
        let mut system = HelpSystem::new(HelpContext::General);
        system.show_overlay = true;

        let event = Event::Key(KeyEvent {
            code: KeyCode::Esc,
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let handled = handle_help_event(event, &mut system);
        assert!(handled, "Should handle Esc");
        assert!(!system.show_overlay, "Should close overlay");
        assert!(!system.show_cheat_sheet, "Should close cheat sheet");
    }

    #[test]
    fn test_handle_help_event_q_close() {
        let mut system = HelpSystem::new(HelpContext::General);
        system.show_cheat_sheet = true;

        let event = Event::Key(KeyEvent {
            code: KeyCode::Char('q'),
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let handled = handle_help_event(event, &mut system);
        assert!(handled, "Should handle q key");
        assert!(!system.show_overlay, "Should close overlay");
        assert!(!system.show_cheat_sheet, "Should close cheat sheet");
    }

    #[test]
    fn test_handle_help_event_other_keys() {
        let mut system = HelpSystem::new(HelpContext::General);

        let event = Event::Key(KeyEvent {
            code: KeyCode::Char('x'),
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let handled = handle_help_event(event, &mut system);
        assert!(!handled, "Should not handle other keys");
    }

    #[test]
    fn test_handle_help_event_mouse_ignored() {
        let mut system = HelpSystem::new(HelpContext::General);

        let event = Event::Mouse(crossterm::event::MouseEvent {
            kind: crossterm::event::MouseEventKind::Down(crossterm::event::MouseButton::Left),
            column: 0,
            row: 0,
            modifiers: KeyModifiers::empty(),
        });

        let handled = handle_help_event(event, &mut system);
        assert!(!handled, "Should ignore mouse events");
    }
}
