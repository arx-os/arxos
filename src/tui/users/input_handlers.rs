//! Input event handlers for user registry TUI

use super::types::{UserBrowserState, ViewMode};
use arboard::Clipboard;
use chrono::Utc;
use crossterm::event::KeyCode;
use ratatui::widgets::ListState;

/// Handle search mode input
pub fn handle_search_input(
    state: &mut UserBrowserState,
    search_input: &mut String,
    list_state: &mut ListState,
    key_code: KeyCode,
) -> Result<bool, Box<dyn std::error::Error>> {
    match key_code {
        KeyCode::Char(c) => {
            search_input.push(c);
            Ok(false) // Continue search mode
        }
        KeyCode::Backspace => {
            search_input.pop();
            Ok(false) // Continue search mode
        }
        KeyCode::Enter => {
            if !search_input.is_empty() {
                state.filter_users(search_input);
                state.selected_index = 0;
                list_state.select(Some(0));
                // Reload activity for first filtered user
                if let Some(user) = state.selected_user() {
                    let user_email = user.email.clone();
                    if let Err(e) = state.load_user_activity(&user_email) {
                        eprintln!("Warning: Could not load user activity: {}", e);
                    }
                }
            }
            state.search_mode = false;
            Ok(false) // Exit search mode
        }
        KeyCode::Esc => {
            state.search_mode = false;
            if state.search_query.is_empty() {
                search_input.clear();
            } else {
                *search_input = state.search_query.clone();
            }
            Ok(false) // Exit search mode
        }
        _ => Ok(false),
    }
}

/// Handle navigation keys
pub fn handle_navigation(
    state: &mut UserBrowserState,
    list_state: &mut ListState,
    key_code: KeyCode,
) -> bool {
    match key_code {
        KeyCode::Up => {
            state.move_up();
            list_state.select(Some(state.selected_index));
            true
        }
        KeyCode::Down => {
            state.move_down();
            list_state.select(Some(state.selected_index));
            true
        }
        _ => false,
    }
}

/// Handle view mode switching
pub fn handle_view_switching(state: &mut UserBrowserState, key_code: KeyCode) -> bool {
    match key_code {
        KeyCode::Char('o') => {
            if state.view_mode == ViewMode::List {
                state.view_mode = ViewMode::Organizations;
                true
            } else {
                false
            }
        }
        KeyCode::Char('a') => {
            if state.view_mode == ViewMode::List {
                state.view_mode = ViewMode::Activity;
                true
            } else {
                false
            }
        }
        KeyCode::Char('s') | KeyCode::Char('S') => {
            if state.view_mode == ViewMode::List && !state.search_mode {
                state.search_mode = true;
                true
            } else {
                false
            }
        }
        KeyCode::Char('q') | KeyCode::Esc => {
            if state.view_mode != ViewMode::List {
                state.view_mode = ViewMode::List;
                true
            } else {
                false
            }
        }
        _ => false,
    }
}

/// Handle clipboard copy operations
pub fn handle_clipboard_copy(
    text: &str,
    field_name: &str,
    clipboard: &mut Option<Clipboard>,
) -> (String, chrono::DateTime<Utc>) {
    if let Some(ref mut cb) = clipboard {
        match cb.set_text(text) {
            Ok(_) => (
                format!("✓ Copied {}: {}", field_name, text),
                Utc::now() + chrono::Duration::seconds(2),
            ),
            Err(e) => (
                format!("✗ Failed to copy: {}", e),
                Utc::now() + chrono::Duration::seconds(2),
            ),
        }
    } else {
        (
            "✗ Clipboard not available".to_string(),
            Utc::now() + chrono::Duration::seconds(2),
        )
    }
}

/// Handle user selection (Enter key)
pub fn handle_user_selection(state: &mut UserBrowserState) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(user) = state.selected_user() {
        let email = user.email.clone();
        if state.view_mode == ViewMode::List {
            // Reload activity for selected user
            if let Err(e) = state.load_user_activity(&email) {
                eprintln!("Warning: Could not load user activity: {}", e);
            }
        }
    }
    Ok(())
}
