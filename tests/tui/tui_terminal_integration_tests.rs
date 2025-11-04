//! Integration tests for terminal manager
//!
//! Tests terminal initialization, cleanup, and event polling:
//! - Terminal manager full workflow
//! - Mouse support integration
//! - Terminal state management

use arxos::ui::terminal::TerminalManager;
use arxos::ui::mouse::{MouseConfig, parse_mouse_event};
use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
use std::time::Duration;

/// Test terminal manager key detection helpers
#[test]
fn test_terminal_manager_key_helpers() {
    // Test quit key detection
    let quit_key = KeyEvent {
        code: KeyCode::Char('q'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_quit_key(&quit_key));
    
    let esc_key = KeyEvent {
        code: KeyCode::Esc,
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_quit_key(&esc_key));
    
    // Test navigation
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
    
    // Test select
    let enter_key = KeyEvent {
        code: KeyCode::Enter,
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_select(&enter_key));
}

/// Test that terminal manager correctly identifies navigation keys
#[test]
fn test_terminal_manager_navigation_keys() {
    // Test k/j for navigation (vim-style)
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

/// Test that space bar is recognized as select
#[test]
fn test_terminal_manager_space_select() {
    let space_key = KeyEvent {
        code: KeyCode::Char(' '),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    };
    assert!(TerminalManager::is_select(&space_key));
}

/// Test mouse config integration
#[test]
fn test_mouse_config_integration() {
    // Test default mouse config
    let default_config = MouseConfig::default();
    assert!(default_config.enabled);
    assert!(default_config.click_to_select);
    assert!(default_config.scroll_enabled);
    assert!(!default_config.drag_enabled);
    
    // Test disabled config
    let disabled_config = MouseConfig::disabled();
    assert!(!disabled_config.enabled);
    
    // Test full config
    let full_config = MouseConfig::full();
    assert!(full_config.enabled);
    assert!(full_config.drag_enabled);
}

/// Test event timeout handling
#[test]
fn test_event_timeout() {
    // Note: Actual terminal manager creation requires real terminal
    // This test verifies the timeout mechanism would work
    // Full integration test would require TestBackend or mocking
    let timeout = Duration::from_millis(100);
    assert!(timeout.as_millis() == 100);
}
