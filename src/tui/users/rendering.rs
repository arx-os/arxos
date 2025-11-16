//! Rendering functions for user registry TUI

use super::types::{format_relative_time, User, UserActivityItem, UserBrowserState, ViewMode};
use crate::tui::Theme;
use ratatui::{
    layout::{Alignment, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
};

/// Render user list widget
pub fn render_user_list<'a>(
    state: &'a UserBrowserState,
    theme: &'a Theme,
    _area: Rect,
) -> List<'a> {
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
pub fn render_user_details<'a>(user: &'a User, theme: &'a Theme, _area: Rect) -> Paragraph<'a> {
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

    lines.push(Line::from(vec![
        Span::styled("Role: ", Style::default().fg(theme.muted)),
        Span::styled(&user.role, Style::default().fg(theme.text)),
    ]));

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
pub fn render_user_activity<'a>(
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
pub fn render_organization_view<'a>(
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
pub fn render_footer<'a>(
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
