//! Test utilities for TUI integration tests
//!
//! Provides helper functions and mock implementations for testing TUI components
//! without requiring actual terminal access.

use ratatui::{
    backend::TestBackend,
    layout::Rect,
    style::{Color, Style},
    buffer::Buffer,
    Terminal,
};
use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
use arxos::ui::Theme;

/// Create a test theme for testing
pub fn create_test_theme() -> Theme {
    Theme::default()
}

/// Create a test buffer with specified dimensions
pub fn create_test_buffer(width: u16, height: u16) -> Buffer {
    Buffer::empty(Rect::new(0, 0, width, height))
}

/// Create a test terminal with TestBackend
pub fn create_test_terminal(width: u16, height: u16) -> Terminal<TestBackend> {
    let backend = TestBackend::new(width, height);
    Terminal::new(backend).unwrap()
}

/// Simulate a key event
pub fn simulate_key_event(code: KeyCode, modifiers: KeyModifiers) -> Event {
    Event::Key(KeyEvent {
        code,
        modifiers,
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    })
}

/// Simulate a mouse event
pub fn simulate_mouse_event(
    kind: MouseEventKind,
    column: u16,
    row: u16,
    modifiers: KeyModifiers,
) -> Event {
    Event::Mouse(MouseEvent {
        kind,
        column,
        row,
        modifiers,
    })
}

/// Simulate a left click
pub fn simulate_left_click(column: u16, row: u16) -> Event {
    simulate_mouse_event(
        MouseEventKind::Down(MouseButton::Left),
        column,
        row,
        KeyModifiers::empty(),
    )
}

/// Simulate a scroll up event
pub fn simulate_scroll_up(column: u16, row: u16) -> Event {
    simulate_mouse_event(
        MouseEventKind::ScrollUp,
        column,
        row,
        KeyModifiers::empty(),
    )
}

/// Simulate a scroll down event
pub fn simulate_scroll_down(column: u16, row: u16) -> Event {
    simulate_mouse_event(
        MouseEventKind::ScrollDown,
        column,
        row,
        KeyModifiers::empty(),
    )
}

/// Helper to create a test frame area
pub fn create_test_area(width: u16, height: u16) -> Rect {
    Rect::new(0, 0, width, height)
}

/// Helper to create a centered rectangle within a larger area
pub fn create_centered_rect(outer: Rect, width: u16, height: u16) -> Rect {
    let x = outer.x + (outer.width.saturating_sub(width)) / 2;
    let y = outer.y + (outer.height.saturating_sub(height)) / 2;
    Rect::new(x, y, width.min(outer.width), height.min(outer.height))
}

/// RAII guard for test terminal - ensures proper cleanup
pub struct TestTerminalGuard {
    terminal: Terminal<TestBackend>,
}

impl TestTerminalGuard {
    /// Create a new test terminal guard
    pub fn new(width: u16, height: u16) -> Self {
        Self {
            terminal: create_test_terminal(width, height),
        }
    }

    /// Get mutable reference to terminal
    pub fn terminal_mut(&mut self) -> &mut Terminal<TestBackend> {
        &mut self.terminal
    }

    /// Draw to terminal and get the buffer for inspection
    pub fn draw<F>(&mut self, f: F) -> Buffer
    where
        F: FnOnce(&mut ratatui::Frame),
    {
        self.terminal.get_frame().size();
        // For now, return empty buffer - full implementation would require
        // capturing the frame during draw
        Buffer::empty(Rect::new(0, 0, 80, 24))
    }
}

/// Setup a test environment with temporary directory
/// Returns the temp directory and a guard that cleans up on drop
pub fn setup_test_env() -> (tempfile::TempDir, TestTerminalGuard) {
    let temp_dir = tempfile::tempdir().expect("Failed to create temp directory");
    let terminal_guard = TestTerminalGuard::new(80, 24);
    (temp_dir, terminal_guard)
}

/// Verify that buffer contains expected text (case-insensitive)
pub fn buffer_contains_text(buffer: &Buffer, text: &str) -> bool {
    let buffer_text: String = buffer
        .content
        .iter()
        .map(|cell| cell.symbol())
        .collect::<String>();
    buffer_text.to_lowercase().contains(&text.to_lowercase())
}

/// Get text content from a buffer region
pub fn get_buffer_text(buffer: &Buffer, area: Rect) -> String {
    let mut text = String::new();
    for y in area.y..(area.y + area.height) {
        for x in area.x..(area.x + area.width) {
            if let Some(cell) = buffer.get(x, y) {
                text.push_str(cell.symbol());
            }
        }
        if y < area.y + area.height - 1 {
            text.push('\n');
        }
    }
    text
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_test_theme() {
        let theme = create_test_theme();
        assert_eq!(theme.primary, Color::Cyan);
    }

    #[test]
    fn test_create_test_buffer() {
        let buffer = create_test_buffer(80, 24);
        assert_eq!(buffer.area.width, 80);
        assert_eq!(buffer.area.height, 24);
    }

    #[test]
    fn test_create_test_terminal() {
        let terminal = create_test_terminal(80, 24);
        // Terminal creation should succeed
        assert!(terminal.get_frame().size().width == 80);
        assert!(terminal.get_frame().size().height == 24);
    }

    #[test]
    fn test_simulate_key_event() {
        let event = simulate_key_event(KeyCode::Char('q'), KeyModifiers::empty());
        match event {
            Event::Key(key) => {
                assert_eq!(key.code, KeyCode::Char('q'));
            }
            _ => panic!("Expected Key event"),
        }
    }

    #[test]
    fn test_simulate_left_click() {
        let event = simulate_left_click(10, 5);
        match event {
            Event::Mouse(mouse) => {
                assert_eq!(mouse.column, 10);
                assert_eq!(mouse.row, 5);
                match mouse.kind {
                    MouseEventKind::Down(MouseButton::Left) => {}
                    _ => panic!("Expected Left click"),
                }
            }
            _ => panic!("Expected Mouse event"),
        }
    }
}

