//! User UI components for identity registry
//!
//! Provides interactive TUI interfaces for:
//! - Browsing user registry
//! - Viewing user details and activity
//! - Organization grouping
//! - Contact information display

// Git operations functions are integrated inline or in git module
// extract_email_from_author, extract_user_id_from_commit, find_git_repository
use crate::tui::layouts::{dashboard_layout, list_detail_layout};
use crate::tui::{TerminalManager, Theme};
use arboard::Clipboard;
use crate::git::{BuildingGitManager, GitConfigManager};
// User management types are defined inline
use chrono::{DateTime, Utc};
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
};
use std::collections::HashMap;
use std::time::Duration;

/// User activity item for timeline
#[derive(Debug, Clone)]
struct UserActivityItem {
    timestamp: DateTime<Utc>,
    relative_time: String,
    commit_hash: String,
    commit_message: String,
    #[allow(dead_code)] // Reserved for future enhancement
    files_changed: Vec<String>,
}

/// User browser state
struct UserBrowserState {
    registry: UserRegistry,
    users: Vec<User>,
    filtered_users: Vec<usize>, // Indices into users vector
    selected_index: usize,
    view_mode: ViewMode,
    search_query: String,
    search_mode: bool,
    selected_user_activity: Vec<UserActivityItem>,
    organization_groups: HashMap<String, Vec<usize>>,
    show_details: bool,
}

/// View mode for user browser
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ViewMode {
    List,
    Organizations,
    Activity,
}

impl UserBrowserState {
    fn new(registry: UserRegistry) -> Self {
        let users = registry.all_users().to_vec();
        let filtered_users: Vec<usize> = (0..users.len()).collect();

        // Group users by organization
        let mut organization_groups: HashMap<String, Vec<usize>> = HashMap::new();
        for (idx, user) in users.iter().enumerate() {
            let org = user
                .organization
                .as_ref()
                .cloned()
                .unwrap_or_else(|| "Unaffiliated".to_string());
            organization_groups.entry(org).or_default().push(idx);
        }

        Self {
            registry,
            users,
            filtered_users,
            selected_index: 0,
            view_mode: ViewMode::List,
            search_query: String::new(),
            search_mode: false,
            selected_user_activity: Vec::new(),
            organization_groups,
            show_details: true,
        }
    }

    fn selected_user(&self) -> Option<&User> {
        if let Some(&idx) = self.filtered_users.get(self.selected_index) {
            self.users.get(idx)
        } else {
            None
        }
    }

    fn filter_users(&mut self, query: &str) {
        self.search_query = query.to_lowercase();
        if query.is_empty() {
            self.filtered_users = (0..self.users.len()).collect();
        } else {
            self.filtered_users = self
                .users
                .iter()
                .enumerate()
                .filter(|(_, user)| {
                    user.name.to_lowercase().contains(&self.search_query)
                        || user.email.to_lowercase().contains(&self.search_query)
                        || user
                            .organization
                            .as_ref()
                            .map(|org| org.to_lowercase().contains(&self.search_query))
                            .unwrap_or(false)
                })
                .map(|(idx, _)| idx)
                .collect();
        }

        // Update selection
        if self.selected_index >= self.filtered_users.len() {
            self.selected_index = self.filtered_users.len().saturating_sub(1);
        }
    }

    fn load_user_activity(&mut self, user_email: &str) -> Result<(), Box<dyn std::error::Error>> {
        // Find Git repository
        let repo_path_str = find_git_repository()?.ok_or("Not in a Git repository")?;

        // Load commit history
        let config = GitConfigManager::default_config();
        let manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
        let commits = manager.list_commits(50)?; // Last 50 commits

        // Extract user_id from registry
        let user = self.registry.find_by_email(user_email);
        let user_id = user.as_ref().map(|u| u.id.clone());

        // Filter commits by user
        let mut activities = Vec::new();
        for commit in commits {
            // Check if commit belongs to this user
            let belongs_to_user = if let Some(ref uid) = user_id {
                // Check for ArxOS-User-ID trailer
                extract_user_id_from_commit(&commit.message)
                    .map(|committed_uid| committed_uid == *uid)
                    .unwrap_or(false)
            } else {
                // Fallback: check author email
                extract_email_from_author(&commit.author)
                    .map(|email| email.to_lowercase() == user_email.to_lowercase())
                    .unwrap_or(false)
            };

            if belongs_to_user {
                let timestamp =
                    chrono::DateTime::from_timestamp(commit.time, 0).unwrap_or_else(Utc::now);
                let relative_time = format_relative_time(&timestamp);

                // Extract files changed (simplified - just count for now)
                let files_changed = Vec::new(); // Could enhance later

                activities.push(UserActivityItem {
                    timestamp,
                    relative_time,
                    commit_hash: commit.id[..8].to_string(),
                    commit_message: commit.message.clone(),
                    files_changed,
                });
            }
        }

        // Sort by timestamp (newest first)
        activities.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        self.selected_user_activity = activities;

        Ok(())
    }

    fn move_up(&mut self) {
        if self.selected_index > 0 {
            self.selected_index -= 1;
        }
    }

    fn move_down(&mut self) {
        if self.selected_index < self.filtered_users.len().saturating_sub(1) {
            self.selected_index += 1;
        }
    }
}

/// Format relative time (e.g., "2 hours ago")
fn format_relative_time(timestamp: &DateTime<Utc>) -> String {
    let now = Utc::now();
    let duration = now.signed_duration_since(*timestamp);

    if duration.num_seconds() < 60 {
        "Just now".to_string()
    } else if duration.num_minutes() < 60 {
        format!("{} minutes ago", duration.num_minutes())
    } else if duration.num_hours() < 24 {
        format!("{} hours ago", duration.num_hours())
    } else if duration.num_days() < 7 {
        format!("{} days ago", duration.num_days())
    } else {
        timestamp.format("%Y-%m-%d").to_string()
    }
}

/// Render user list widget
fn render_user_list<'a>(state: &'a UserBrowserState, theme: &'a Theme, _area: Rect) -> List<'a> {
    let items: Vec<ListItem> = state
        .filtered_users
        .iter()
        .map(|&idx| {
            let user = &state.users[idx];
            let verification_badge = if user.verified { "✅" } else { "⚠️" };

            let org_display = user
                .organization
                .as_ref()
                .map(|org| format!(" 🏢 {}", org))
                .unwrap_or_default();

            let name_line = format!("{} {} {}", verification_badge, user.name, org_display);
            let email_line = format!("   📧 {}", user.email);

            ListItem::new(vec![
                Line::from(vec![Span::styled(
                    name_line,
                    Style::default().fg(theme.text),
                )]),
                Line::from(vec![Span::styled(
                    email_line,
                    Style::default().fg(theme.muted),
                )]),
            ])
        })
        .collect();

    let title = if state.search_query.is_empty() {
        format!("👥 Users ({})", state.filtered_users.len())
    } else {
        format!(
            "👥 Users ({}) - '{}'",
            state.filtered_users.len(),
            state.search_query
        )
    };

    List::new(items)
        .block(Block::default().borders(Borders::ALL).title(title))
        .highlight_style(
            Style::default()
                .fg(theme.accent)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol("> ")
}

/// Render user details widget
fn render_user_details<'a>(user: &'a User, theme: &'a Theme, _area: Rect) -> Paragraph<'a> {
    let mut lines = vec![
        Line::from(vec![Span::styled(
            "👤 User Details",
            Style::default()
                .fg(theme.primary)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(""),
        Line::from(vec![
            Span::styled("Name: ", Style::default().fg(theme.muted)),
            Span::styled(&user.name, Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("Email: ", Style::default().fg(theme.muted)),
            Span::styled(&user.email, Style::default().fg(theme.text)),
            Span::styled("  [C] Copy", Style::default().fg(theme.muted)),
        ]),
        Line::from(vec![
            Span::styled("ID: ", Style::default().fg(theme.muted)),
            Span::styled(&user.id, Style::default().fg(theme.muted)),
        ]),
    ];

    if let Some(ref org) = user.organization {
        lines.push(Line::from(vec![
            Span::styled("Organization: ", Style::default().fg(theme.muted)),
            Span::styled(org, Style::default().fg(theme.text)),
        ]));
    }

    if let Some(ref role) = user.role {
        lines.push(Line::from(vec![
            Span::styled("Role: ", Style::default().fg(theme.muted)),
            Span::styled(role, Style::default().fg(theme.text)),
        ]));
    }

    if let Some(ref phone) = user.phone {
        lines.push(Line::from(vec![
            Span::styled("Phone: ", Style::default().fg(theme.muted)),
            Span::styled(phone, Style::default().fg(theme.text)),
            Span::styled("  [P] Copy", Style::default().fg(theme.muted)),
        ]));
    }

    lines.push(Line::from(""));
    lines.push(Line::from(vec![
        Span::styled("Status: ", Style::default().fg(theme.muted)),
        Span::styled(
            format!("{:?}", user.status),
            Style::default().fg(theme.text),
        ),
    ]));

    lines.push(Line::from(vec![
        Span::styled("Verified: ", Style::default().fg(theme.muted)),
        Span::styled(
            if user.verified { "✅ Yes" } else { "❌ No" },
            Style::default().fg(if user.verified {
                Color::Green
            } else {
                Color::Yellow
            }),
        ),
    ]));

    if user.verified {
        if let Some(ref verified_by) = user.verified_by {
            lines.push(Line::from(vec![
                Span::styled("Verified by: ", Style::default().fg(theme.muted)),
                Span::styled(verified_by, Style::default().fg(theme.text)),
            ]));
        }
        if let Some(verified_at) = user.verified_at {
            lines.push(Line::from(vec![
                Span::styled("Verified at: ", Style::default().fg(theme.muted)),
                Span::styled(
                    verified_at.format("%Y-%m-%d %H:%M:%S UTC").to_string(),
                    Style::default().fg(theme.text),
                ),
            ]));
        }
    }

    if !user.permissions.is_empty() {
        lines.push(Line::from(""));
        lines.push(Line::from(vec![Span::styled(
            "🔑 Permissions:",
            Style::default().fg(theme.muted),
        )]));
        for perm in &user.permissions {
            lines.push(Line::from(vec![
                Span::styled("   - ", Style::default().fg(theme.muted)),
                Span::styled(perm, Style::default().fg(theme.text)),
            ]));
        }
    }

    if let Some(ref last_active) = user.last_active {
        lines.push(Line::from(""));
        lines.push(Line::from(vec![
            Span::styled("⏰ Last Active: ", Style::default().fg(theme.muted)),
            Span::styled(
                format_relative_time(last_active),
                Style::default().fg(theme.text),
            ),
        ]));
    }

    lines.push(Line::from(vec![
        Span::styled("📅 Added: ", Style::default().fg(theme.muted)),
        Span::styled(
            user.added_at.format("%Y-%m-%d %H:%M:%S UTC").to_string(),
            Style::default().fg(theme.text),
        ),
    ]));

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL))
        .alignment(Alignment::Left)
}

/// Render user activity timeline
fn render_user_activity<'a>(
    activities: &'a [UserActivityItem],
    theme: &'a Theme,
    _area: Rect,
) -> Paragraph<'a> {
    let mut lines = Vec::new();

    lines.push(Line::from(vec![Span::styled(
        "📊 Recent Activity",
        Style::default()
            .fg(theme.primary)
            .add_modifier(Modifier::BOLD),
    )]));
    lines.push(Line::from(""));

    if activities.is_empty() {
        lines.push(Line::from(vec![Span::styled(
            "No activity found",
            Style::default().fg(theme.muted),
        )]));
    } else {
        for activity in activities.iter().take(10) {
            lines.push(Line::from(vec![
                Span::styled("🔵 ", Style::default().fg(Color::Blue)),
                Span::styled(&activity.commit_message, Style::default().fg(theme.text)),
            ]));
            lines.push(Line::from(vec![
                Span::styled("   ", Style::default()),
                Span::styled(&activity.relative_time, Style::default().fg(theme.muted)),
                Span::styled(
                    format!(" ({})", activity.commit_hash),
                    Style::default().fg(theme.muted),
                ),
            ]));
            lines.push(Line::from(""));
        }
    }

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL))
        .alignment(Alignment::Left)
}

/// Render organization view
fn render_organization_view<'a>(
    state: &'a UserBrowserState,
    theme: &'a Theme,
    _area: Rect,
) -> Paragraph<'a> {
    let mut lines = Vec::new();

    lines.push(Line::from(vec![Span::styled(
        "🏢 Organizations",
        Style::default()
            .fg(theme.primary)
            .add_modifier(Modifier::BOLD),
    )]));
    lines.push(Line::from(""));

    let mut orgs: Vec<_> = state.organization_groups.iter().collect();
    orgs.sort_by(|a, b| a.0.cmp(b.0));

    for (org_name, user_indices) in orgs {
        let verified_count = user_indices
            .iter()
            .filter(|&&idx| state.users[idx].verified)
            .count();

        lines.push(Line::from(vec![Span::styled(
            format!(
                "🏢 {} ({} users, {} verified)",
                org_name,
                user_indices.len(),
                verified_count
            ),
            Style::default().fg(theme.text).add_modifier(Modifier::BOLD),
        )]));

        for &idx in user_indices.iter().take(5) {
            let user = &state.users[idx];
            let badge = if user.verified { "✅" } else { "⚠️" };
            lines.push(Line::from(vec![
                Span::styled(format!("   {} ", badge), Style::default()),
                Span::styled(&user.name, Style::default().fg(theme.text)),
                Span::styled(
                    format!(" <{}>", user.email),
                    Style::default().fg(theme.muted),
                ),
            ]));
        }

        if user_indices.len() > 5 {
            lines.push(Line::from(vec![Span::styled(
                format!("   ... ({} more)", user_indices.len() - 5),
                Style::default().fg(theme.muted),
            )]));
        }

        lines.push(Line::from(""));
    }

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL))
        .alignment(Alignment::Left)
}

/// Render footer with keyboard shortcuts or status message
fn render_footer<'a>(
    view_mode: ViewMode,
    search_mode: bool,
    theme: &'a Theme,
    status_message: Option<&'a str>,
) -> Paragraph<'a> {
    let text = if let Some(msg) = status_message {
        msg
    } else if search_mode {
        "Type to search | Enter: Apply | Esc: Cancel"
    } else {
        match view_mode {
            ViewMode::List => "[Q] Quit  [Enter] Details  [O] Organizations  [A] Activity  [S] Search  [C] Copy Email  [P] Copy Phone",
            ViewMode::Organizations => "[Q] Back  [Enter] Select User",
            ViewMode::Activity => "[Q] Back",
        }
    };

    Paragraph::new(text)
        .style(Style::default().fg(theme.muted))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::TOP))
}

/// Handle interactive user browser
pub fn handle_user_browser() -> Result<(), Box<dyn std::error::Error>> {
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);

    // Load registry
    let registry = UserRegistry::load(repo_path)?;

    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();

    let mut state = UserBrowserState::new(registry);
    let mut list_state = ListState::default();
    let mut clipboard = Clipboard::new().ok(); // Initialize clipboard (may fail on some systems)
    let mut status_message: Option<String> = None;
    let mut status_message_timeout: Option<chrono::DateTime<Utc>> = None;
    let mut search_input = String::new();

    // Initialize list_state
    if !state.filtered_users.is_empty() {
        list_state.select(Some(0));
    }

    // Load activity for first user if available
    if let Some(user) = state.selected_user() {
        let user_email = user.email.clone();
        if let Err(e) = state.load_user_activity(&user_email) {
            eprintln!("Warning: Could not load user activity: {}", e);
        }
    }

    loop {
        terminal.terminal().draw(|frame| {
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
                    let content_chunks = list_detail_layout(chunks[1], 40);

                    // Extract data before rendering to avoid borrow conflicts
                    let selected_activity = state.selected_user_activity.clone();

                    // User list
                    let user_list = render_user_list(&state, &theme, content_chunks[0]);
                    list_state.select(Some(state.selected_index)); // Sync before render
                    frame.render_stateful_widget(user_list, content_chunks[0], &mut list_state);

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
                            let details = render_user_details(user, &theme, detail_chunks[0]);
                            frame.render_widget(details, detail_chunks[0]);

                            let activity =
                                render_user_activity(&selected_activity, &theme, detail_chunks[1]);
                            frame.render_widget(activity, detail_chunks[1]);
                        }
                    }
                }
                ViewMode::Organizations => {
                    let org_view = render_organization_view(&state, &theme, chunks[1]);
                    frame.render_widget(org_view, chunks[1]);
                }
                ViewMode::Activity => {
                    if let Some(_user) = state.selected_user() {
                        let activity =
                            render_user_activity(&state.selected_user_activity, &theme, chunks[1]);
                        frame.render_widget(activity, chunks[1]);
                    }
                }
            }

            // Footer with status message overlay
            let footer = render_footer(
                state.view_mode,
                state.search_mode,
                &theme,
                status_message.as_deref(),
            );
            frame.render_widget(footer, chunks[2]);
        })?;

        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                // Handle search mode input
                Event::Key(key_event) if state.search_mode => {
                    match key_event.code {
                        KeyCode::Char(c) => {
                            search_input.push(c);
                        }
                        KeyCode::Backspace => {
                            search_input.pop();
                        }
                        KeyCode::Enter => {
                            if !search_input.is_empty() {
                                state.filter_users(&search_input);
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
                        }
                        KeyCode::Esc => {
                            state.search_mode = false;
                            if state.search_query.is_empty() {
                                search_input.clear();
                            } else {
                                search_input = state.search_query.clone();
                            }
                        }
                        _ => {}
                    }
                }
                Event::Key(key_event) => {
                    match key_event.code {
                        KeyCode::Char('q') | KeyCode::Esc => {
                            if state.view_mode == ViewMode::List {
                                break;
                            } else {
                                state.view_mode = ViewMode::List;
                            }
                        }
                        KeyCode::Up => {
                            state.move_up();
                            list_state.select(Some(state.selected_index));
                        }
                        KeyCode::Down => {
                            state.move_down();
                            list_state.select(Some(state.selected_index));
                        }
                        KeyCode::Char('o') => {
                            if state.view_mode == ViewMode::List {
                                state.view_mode = ViewMode::Organizations;
                            }
                        }
                        KeyCode::Char('a') => {
                            if state.view_mode == ViewMode::List {
                                state.view_mode = ViewMode::Activity;
                            }
                        }
                        KeyCode::Char('s') | KeyCode::Char('S') => {
                            if state.view_mode == ViewMode::List && !state.search_mode {
                                state.search_mode = true;
                                search_input.clear();
                            }
                        }
                        KeyCode::Enter => {
                            if let Some(user) = state.selected_user() {
                                let email = &user.email;
                                if state.view_mode == ViewMode::List {
                                    // Reload activity for selected user
                                    if let Err(e) = state.load_user_activity(email) {
                                        eprintln!("Warning: Could not load user activity: {}", e);
                                    }
                                }
                            }
                        }
                        KeyCode::Char('c') | KeyCode::Char('C') => {
                            // Copy email to clipboard
                            if let Some(user) = state.selected_user() {
                                if let Some(ref mut cb) = clipboard {
                                    match cb.set_text(&user.email) {
                                        Ok(_) => {
                                            status_message =
                                                Some(format!("✓ Copied email: {}", user.email));
                                            status_message_timeout =
                                                Some(Utc::now() + chrono::Duration::seconds(2));
                                        }
                                        Err(e) => {
                                            status_message =
                                                Some(format!("✗ Failed to copy: {}", e));
                                            status_message_timeout =
                                                Some(Utc::now() + chrono::Duration::seconds(2));
                                        }
                                    }
                                } else {
                                    status_message = Some("✗ Clipboard not available".to_string());
                                    status_message_timeout =
                                        Some(Utc::now() + chrono::Duration::seconds(2));
                                }
                            }
                        }
                        KeyCode::Char('p') | KeyCode::Char('P') => {
                            // Copy phone to clipboard
                            if let Some(user) = state.selected_user() {
                                if let Some(ref phone) = user.phone {
                                    if let Some(ref mut cb) = clipboard {
                                        match cb.set_text(phone) {
                                            Ok(_) => {
                                                status_message =
                                                    Some(format!("✓ Copied phone: {}", phone));
                                                status_message_timeout =
                                                    Some(Utc::now() + chrono::Duration::seconds(2));
                                            }
                                            Err(e) => {
                                                status_message =
                                                    Some(format!("✗ Failed to copy: {}", e));
                                                status_message_timeout =
                                                    Some(Utc::now() + chrono::Duration::seconds(2));
                                            }
                                        }
                                    } else {
                                        status_message =
                                            Some("✗ Clipboard not available".to_string());
                                        status_message_timeout =
                                            Some(Utc::now() + chrono::Duration::seconds(2));
                                    }
                                } else {
                                    status_message =
                                        Some("✗ No phone number available".to_string());
                                    status_message_timeout =
                                        Some(Utc::now() + chrono::Duration::seconds(2));
                                }
                            }
                        }
                        _ => {}
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

        // Display status message if present
        if let Some(ref _msg) = status_message {
            // Status message is displayed in the next render cycle
        }
    }

    Ok(())
}
