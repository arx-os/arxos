//! Main user browser implementation

use super::input_handlers::{
    handle_clipboard_copy, handle_navigation, handle_search_input, handle_user_selection,
    handle_view_switching,
};
use super::rendering::{
    render_footer, render_organization_view, render_user_activity, render_user_details,
    render_user_list,
};
use super::types::{find_git_repository, UserBrowserState, UserRegistry, ViewMode};
use crate::tui::layouts::{dashboard_layout, list_detail_layout};
use crate::tui::{TerminalManager, Theme};
use arboard::Clipboard;
use chrono::Utc;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Modifier, Style},
    widgets::{Block, Borders, ListState, Paragraph},
};
use std::time::Duration;

/// Handle interactive user browser
pub fn handle_user_browser() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize
    let (mut state, mut terminal, theme, mut clipboard) = initialize_browser()?;
    let mut list_state = ListState::default();
    let mut search_input = String::new();
    let mut status_message: Option<String> = None;
    let mut status_message_timeout: Option<chrono::DateTime<Utc>> = None;

    // Set initial selection
    if !state.filtered_users.is_empty() {
        list_state.select(Some(0));
    }

    // Load initial user activity
    if let Some(user) = state.selected_user() {
        let user_email = user.email.clone();
        if let Err(e) = state.load_user_activity(&user_email) {
            eprintln!("Warning: Could not load user activity: {}", e);
        }
    }

    // Main event loop
    loop {
        // Render UI
        terminal.terminal().draw(|frame| {
            render_ui(
                frame,
                &state,
                &theme,
                &mut list_state,
                &search_input,
                status_message.as_deref(),
            );
        })?;

        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) if state.search_mode => {
                    // Search mode input handling
                    handle_search_input(&mut state, &mut search_input, &mut list_state, key_event.code)?;
                }
                Event::Key(key_event) => {
                    // Normal mode input handling
                    let should_quit = handle_normal_input(
                        &mut state,
                        &mut list_state,
                        &mut clipboard,
                        &mut status_message,
                        &mut status_message_timeout,
                        &mut search_input,
                        key_event.code,
                    )?;
                    if should_quit {
                        break;
                    }
                }
                _ => {}
            }
        }

        // Clear status message after timeout
        if let Some(timeout) = status_message_timeout {
            if Utc::now() > timeout {
                status_message = None;
                status_message_timeout = None;
            }
        }
    }

    Ok(())
}

/// Initialize browser state and terminal
fn initialize_browser() -> Result<
    (UserBrowserState, TerminalManager, Theme, Option<Clipboard>),
    Box<dyn std::error::Error>,
> {
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);

    // Load registry
    let registry = UserRegistry::load(repo_path.to_path_buf())?;
    let state = UserBrowserState::new(registry);

    // Initialize terminal and theme
    let terminal = TerminalManager::new()?;
    let theme = Theme::default();

    // Initialize clipboard (may fail on some systems)
    let clipboard = Clipboard::new().ok();

    Ok((state, terminal, theme, clipboard))
}

/// Render the UI
fn render_ui(
    frame: &mut ratatui::Frame,
    state: &UserBrowserState,
    theme: &Theme,
    list_state: &mut ListState,
    search_input: &str,
    status_message: Option<&str>,
) {
    let chunks = dashboard_layout(frame.size());

    // Header
    let header = Paragraph::new("User Registry")
        .style(Style::default().fg(theme.text).add_modifier(Modifier::BOLD))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::ALL).title("User Browser"));
    frame.render_widget(header, chunks[0]);

    // Content based on view mode
    match state.view_mode {
        ViewMode::List => {
            render_list_view(frame, state, theme, list_state, search_input, chunks[1]);
        }
        ViewMode::Organizations => {
            let org_view = render_organization_view(state, theme, chunks[1]);
            frame.render_widget(org_view, chunks[1]);
        }
        ViewMode::Activity => {
            if let Some(_user) = state.selected_user() {
                let activity = render_user_activity(&state.selected_user_activity, theme, chunks[1]);
                frame.render_widget(activity, chunks[1]);
            }
        }
    }

    // Footer
    let footer = render_footer(state.view_mode, state.search_mode, theme, status_message);
    frame.render_widget(footer, chunks[2]);
}

/// Render list view with user list and details
fn render_list_view(
    frame: &mut ratatui::Frame,
    state: &UserBrowserState,
    theme: &Theme,
    list_state: &mut ListState,
    search_input: &str,
    area: Rect,
) {
    let content_chunks = list_detail_layout(area, 40);

    // Extract data before rendering to avoid borrow conflicts
    let selected_activity = state.selected_user_activity.clone();

    // User list
    let user_list = render_user_list(state, theme, content_chunks[0]);
    list_state.select(Some(state.selected_index)); // Sync before render
    frame.render_stateful_widget(user_list, content_chunks[0], list_state);

    // Search input overlay
    if state.search_mode {
        let search_text = if search_input.is_empty() {
            "Enter search query: _".to_string()
        } else {
            format!("Search: {}_", search_input)
        };
        let search_paragraph = Paragraph::new(search_text)
            .style(Style::default().fg(theme.primary))
            .block(Block::default().borders(Borders::ALL).title("Search Users"));
        frame.render_widget(search_paragraph, content_chunks[0]);
    }

    // Details panel
    if state.show_details {
        let detail_chunks = Layout::default()
            .direction(ratatui::layout::Direction::Vertical)
            .constraints([Constraint::Length(25), Constraint::Min(0)])
            .split(content_chunks[1])
            .to_vec();

        if let Some(user) = state.selected_user() {
            let details = render_user_details(user, theme, detail_chunks[0]);
            frame.render_widget(details, detail_chunks[0]);

            let activity = render_user_activity(&selected_activity, theme, detail_chunks[1]);
            frame.render_widget(activity, detail_chunks[1]);
        }
    }
}

/// Handle normal mode input
fn handle_normal_input(
    state: &mut UserBrowserState,
    list_state: &mut ListState,
    clipboard: &mut Option<Clipboard>,
    status_message: &mut Option<String>,
    status_message_timeout: &mut Option<chrono::DateTime<Utc>>,
    search_input: &mut String,
    key_code: KeyCode,
) -> Result<bool, Box<dyn std::error::Error>> {
    // Check for quit
    if matches!(key_code, KeyCode::Char('q') | KeyCode::Esc) && state.view_mode == ViewMode::List {
        return Ok(true); // Quit
    }

    // Handle navigation
    if handle_navigation(state, list_state, key_code) {
        return Ok(false);
    }

    // Handle view switching
    if handle_view_switching(state, key_code) {
        if state.search_mode {
            search_input.clear();
        }
        return Ok(false);
    }

    // Handle other keys
    match key_code {
        KeyCode::Enter => {
            handle_user_selection(state)?;
        }
        KeyCode::Char('c') | KeyCode::Char('C') => {
            // Copy email to clipboard
            if let Some(user) = state.selected_user() {
                let (msg, timeout) = handle_clipboard_copy(&user.email, "email", clipboard);
                *status_message = Some(msg);
                *status_message_timeout = Some(timeout);
            }
        }
        KeyCode::Char('p') | KeyCode::Char('P') => {
            // Copy phone to clipboard
            if let Some(user) = state.selected_user() {
                if let Some(ref phone) = user.phone {
                    let (msg, timeout) = handle_clipboard_copy(phone, "phone", clipboard);
                    *status_message = Some(msg);
                    *status_message_timeout = Some(timeout);
                } else {
                    *status_message = Some("✗ No phone number available".to_string());
                    *status_message_timeout = Some(Utc::now() + chrono::Duration::seconds(2));
                }
            }
        }
        _ => {}
    }

    Ok(false) // Don't quit
}
