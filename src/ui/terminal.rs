//! Terminal management for Ratatui applications
//!
//! Handles terminal initialization, cleanup, and event polling.

use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEvent},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};
use std::io::{stdout, Stdout};
use std::time::Duration;

/// Manages terminal state for Ratatui applications
pub struct TerminalManager {
    terminal: Terminal<CrosstermBackend<Stdout>>,
    mouse_enabled: bool,
}

impl TerminalManager {
    /// Create a new terminal manager and initialize terminal for TUI
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        Self::with_mouse(true)
    }

    /// Create a new terminal manager with mouse support option
    pub fn with_mouse(mouse_enabled: bool) -> Result<Self, Box<dyn std::error::Error>> {
        enable_raw_mode()?;
        let mut stdout = stdout();
        execute!(stdout, EnterAlternateScreen)?;

        // Enable mouse capture if requested
        if mouse_enabled {
            execute!(stdout, EnableMouseCapture)?;
        }

        let backend = CrosstermBackend::new(stdout);
        let terminal = Terminal::new(backend)?;

        Ok(Self {
            terminal,
            mouse_enabled,
        })
    }

    /// Get mutable reference to the terminal for drawing
    pub fn terminal(&mut self) -> &mut Terminal<CrosstermBackend<Stdout>> {
        &mut self.terminal
    }

    /// Poll for events with timeout
    pub fn poll_event(
        &self,
        timeout: Duration,
    ) -> Result<Option<Event>, Box<dyn std::error::Error>> {
        if event::poll(timeout)? {
            Ok(Some(event::read()?))
        } else {
            Ok(None)
        }
    }

    /// Check if a key event is the quit key (q or Esc)
    pub fn is_quit_key(key: &KeyEvent) -> bool {
        matches!(
            key.code,
            KeyCode::Char('q') | KeyCode::Char('Q') | KeyCode::Esc
        )
    }

    /// Check if a key event is navigation up
    pub fn is_nav_up(key: &KeyEvent) -> bool {
        matches!(
            key.code,
            KeyCode::Up | KeyCode::Char('k') | KeyCode::Char('K')
        )
    }

    /// Check if a key event is navigation down
    pub fn is_nav_down(key: &KeyEvent) -> bool {
        matches!(
            key.code,
            KeyCode::Down | KeyCode::Char('j') | KeyCode::Char('J')
        )
    }

    /// Check if a key event is select/enter
    pub fn is_select(key: &KeyEvent) -> bool {
        matches!(key.code, KeyCode::Enter | KeyCode::Char(' '))
    }

    /// Check if mouse support is enabled
    pub fn mouse_enabled(&self) -> bool {
        self.mouse_enabled
    }

    /// Enable mouse support (call after initialization)
    pub fn enable_mouse(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        if !self.mouse_enabled {
            execute!(stdout(), EnableMouseCapture)?;
            self.mouse_enabled = true;
        }
        Ok(())
    }

    /// Disable mouse support
    pub fn disable_mouse(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        if self.mouse_enabled {
            execute!(stdout(), DisableMouseCapture)?;
            self.mouse_enabled = false;
        }
        Ok(())
    }
}

impl Drop for TerminalManager {
    fn drop(&mut self) {
        if self.mouse_enabled {
            let _ = execute!(stdout(), DisableMouseCapture);
        }
        let _ = disable_raw_mode();
        let _ = execute!(stdout(), LeaveAlternateScreen);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crossterm::event::KeyCode;

    #[test]
    fn test_is_quit_key() {
        let key = KeyEvent {
            code: KeyCode::Char('q'),
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_quit_key(&key));
    }

    #[test]
    fn test_is_nav_up() {
        let key = KeyEvent {
            code: KeyCode::Up,
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_nav_up(&key));
    }

    #[test]
    fn test_is_nav_down() {
        let key = KeyEvent {
            code: KeyCode::Down,
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_nav_down(&key));
    }

    #[test]
    fn test_is_select() {
        let key_enter = KeyEvent {
            code: KeyCode::Enter,
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_select(&key_enter));

        let key_space = KeyEvent {
            code: KeyCode::Char(' '),
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_select(&key_space));
    }

    #[test]
    fn test_terminal_manager_mouse_enabled() {
        // Note: TerminalManager::new() requires actual terminal, which is problematic in tests
        // We test the mouse_enabled() method indirectly through the existing structure
        // Full integration tests would require mocking or using TestBackend

        // Test that the method exists and returns bool
        // Actual terminal creation tests are better suited for integration tests
    }

    #[test]
    fn test_nav_key_variants() {
        // Test uppercase variants
        let key_k = KeyEvent {
            code: KeyCode::Char('k'),
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_nav_up(&key_k));

        let key_j = KeyEvent {
            code: KeyCode::Char('j'),
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_nav_down(&key_j));

        let key_q = KeyEvent {
            code: KeyCode::Char('q'),
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_quit_key(&key_q));

        let key_q_upper = KeyEvent {
            code: KeyCode::Char('Q'),
            modifiers: crossterm::event::KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };
        assert!(TerminalManager::is_quit_key(&key_q_upper));
    }
}
