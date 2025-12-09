//! Integration tests for TUI event flow and propagation
//!
//! Tests event handling and propagation:
//! - Keyboard event flow through components
//! - Mouse event flow through components
//! - Help event interception
//! - Error event handling flow

use arxos::tui::help::{handle_help_event, HelpContext, HelpSystem};
use arxos::tui::mouse::{parse_mouse_event, MouseAction, MouseConfig};
use arxos::tui::terminal::TerminalManager;
use crossterm::event::{
    Event, KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers, MouseButton, MouseEvent,
    MouseEventKind,
};

/// Test keyboard event flow through help system
#[test]
fn test_keyboard_event_flow_help() {
    let mut help_system = HelpSystem::new(HelpContext::General);

    // Test that '?' key toggles help overlay
    let question_mark_event = Event::Key(KeyEvent {
        code: KeyCode::Char('?'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    });

    assert!(!help_system.show_overlay);
    handle_help_event(question_mark_event, &mut help_system);
    assert!(help_system.show_overlay);

    // Test that Esc closes help
    let esc_event = Event::Key(KeyEvent {
        code: KeyCode::Esc,
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    });

    handle_help_event(esc_event, &mut help_system);
    assert!(!help_system.show_overlay);
}

/// Test mouse event flow through mouse parser
#[test]
fn test_mouse_event_flow() {
    let config = MouseConfig::default();

    // Test left click flow
    let mouse_event = Event::Mouse(MouseEvent {
        kind: MouseEventKind::Down(MouseButton::Left),
        column: 10,
        row: 5,
        modifiers: KeyModifiers::empty(),
    });

    let action = parse_mouse_event(&mouse_event, &config);
    assert!(action.is_some());
    if let Some(MouseAction::LeftClick { x, y }) = action {
        assert_eq!(x, 10);
        assert_eq!(y, 5);
    } else {
        panic!("Expected LeftClick action");
    }

    // Test scroll flow
    let scroll_event = Event::Mouse(MouseEvent {
        kind: MouseEventKind::ScrollDown,
        column: 0,
        row: 0,
        modifiers: KeyModifiers::empty(),
    });

    let action = parse_mouse_event(&scroll_event, &config);
    assert_eq!(action, Some(MouseAction::ScrollDown));
}

/// Test that help events are intercepted correctly
#[test]
fn test_help_event_interception() {
    let mut help_system = HelpSystem::new(HelpContext::General);

    // Test 'h' key interception
    let h_event = Event::Key(KeyEvent {
        code: KeyCode::Char('h'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    });

    assert!(!help_system.show_overlay);
    handle_help_event(h_event, &mut help_system);
    assert!(help_system.show_overlay);

    // Test Ctrl+H for cheat sheet
    let ctrl_h_event = Event::Key(KeyEvent {
        code: KeyCode::Char('h'),
        modifiers: KeyModifiers::CONTROL,
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    });

    assert!(!help_system.show_cheat_sheet);
    handle_help_event(ctrl_h_event, &mut help_system);
    assert!(help_system.show_cheat_sheet);
}

/// Test that non-help events don't affect help system
#[test]
fn test_non_help_events_ignored() {
    let mut help_system = HelpSystem::new(HelpContext::General);
    let initial_state = help_system.show_overlay;

    // Test that regular key events don't affect help
    let regular_event = Event::Key(KeyEvent {
        code: KeyCode::Char('a'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    });

    handle_help_event(regular_event, &mut help_system);
    assert_eq!(help_system.show_overlay, initial_state);
}

/// Test mouse event flow with disabled mouse
#[test]
fn test_mouse_event_flow_disabled() {
    let config = MouseConfig::disabled();

    let mouse_event = Event::Mouse(MouseEvent {
        kind: MouseEventKind::Down(MouseButton::Left),
        column: 10,
        row: 5,
        modifiers: KeyModifiers::empty(),
    });

    let action = parse_mouse_event(&mouse_event, &config);
    assert!(
        action.is_none(),
        "Mouse events should be ignored when disabled"
    );
}

/// Test navigation key event flow
#[test]
fn test_navigation_key_flow() {
    // Test that terminal manager correctly identifies navigation keys
    let up_key = KeyEvent {
        code: KeyCode::Up,
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_nav_up(&up_key));

    let down_key = KeyEvent {
        code: KeyCode::Down,
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_nav_down(&down_key));

    // Test vim-style navigation
    let k_key = KeyEvent {
        code: KeyCode::Char('k'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_nav_up(&k_key));

    let j_key = KeyEvent {
        code: KeyCode::Char('j'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_nav_down(&j_key));
}

/// Test quit key event flow
#[test]
fn test_quit_key_flow() {
    let q_key = KeyEvent {
        code: KeyCode::Char('q'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_quit_key(&q_key));

    let esc_key = KeyEvent {
        code: KeyCode::Esc,
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_quit_key(&esc_key));
}

/// Test select key event flow
#[test]
fn test_select_key_flow() {
    let enter_key = KeyEvent {
        code: KeyCode::Enter,
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_select(&enter_key));

    let space_key = KeyEvent {
        code: KeyCode::Char(' '),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_select(&space_key));
}
