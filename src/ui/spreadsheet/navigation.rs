//! Keyboard navigation for spreadsheet
//!
//! Handles keyboard input and navigation

use crossterm::event::{KeyEvent, KeyCode, KeyModifiers};
use super::grid::Grid;

/// Handle keyboard navigation
pub fn handle_navigation(key: KeyEvent, grid: &mut Grid) -> NavigationAction {
    // Check for Ctrl combinations
    let is_ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
    
    match (key.code, is_ctrl) {
        (KeyCode::Up, false) => {
            grid.move_up();
            NavigationAction::Continue
        }
        (KeyCode::Down, false) => {
            grid.move_down();
            NavigationAction::Continue
        }
        (KeyCode::Left, false) => {
            grid.move_left();
            NavigationAction::Continue
        }
        (KeyCode::Right, false) => {
            grid.move_right();
            NavigationAction::Continue
        }
        (KeyCode::Home, false) => {
            grid.move_to_row_start();
            NavigationAction::Continue
        }
        (KeyCode::Home, true) => {
            // Ctrl+Home: Move to first cell
            grid.move_to_home();
            NavigationAction::Continue
        }
        (KeyCode::End, false) => {
            grid.move_to_row_end();
            NavigationAction::Continue
        }
        (KeyCode::End, true) => {
            // Ctrl+End: Move to last cell
            grid.move_to_end();
            NavigationAction::Continue
        }
        (KeyCode::PageUp, _) => {
            // Scroll up one page
            let page_size = 10;
            for _ in 0..page_size {
                grid.move_up();
            }
            NavigationAction::Continue
        }
        (KeyCode::PageDown, _) => {
            // Scroll down one page
            let page_size = 10;
            for _ in 0..page_size {
                grid.move_down();
            }
            NavigationAction::Continue
        }
        (KeyCode::Tab, false) => {
            grid.move_right();
            NavigationAction::Continue
        }
        (KeyCode::BackTab, _) => {
            // Shift+Tab: Move to previous cell
            grid.move_left();
            NavigationAction::Continue
        }
        _ => NavigationAction::Continue,
    }
}

/// Navigation action result
pub enum NavigationAction {
    Continue,
    Quit,
    Save,
    SaveAndCommit,
}

