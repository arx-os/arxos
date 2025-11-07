//! Interactive Status Dashboard for ArxOS TUI
//!
//! Provides a comprehensive building health overview with:
//! - Summary cards (equipment count, alerts, critical issues)
//! - Equipment status breakdown
//! - Recent activity timeline
//! - Real-time updates

use crate::git::manager::{BuildingGitManager, GitConfigManager};
use crate::ui::layouts::{card_grid, dashboard_layout, split_horizontal};
use crate::ui::{StatusColor, TerminalManager, Theme};
use crate::utils::loading;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
};
use std::time::Duration;

/// Dashboard statistics
struct DashboardStats {
    total_equipment: usize,
    healthy_count: usize,
    warning_count: usize,
    critical_count: usize,
    unknown_count: usize,
    // Reserved for future activity feed display
    #[allow(dead_code)]
    recent_changes: usize,
    total_rooms: usize,
    // Reserved for future floor summary display
    #[allow(dead_code)]
    total_floors: usize,
}

/// Recent activity item
#[derive(Debug, Clone)]
struct ActivityItem {
    timestamp: String,
    message: String,
    commit_hash: Option<String>,
}

/// Dashboard state
struct DashboardState {
    stats: DashboardStats,
    activities: Vec<ActivityItem>,
    building_name: String,
    refresh_interval: Duration,
}

impl DashboardState {
    fn new(building_name: String) -> Self {
        Self {
            stats: DashboardStats {
                total_equipment: 0,
                healthy_count: 0,
                warning_count: 0,
                critical_count: 0,
                unknown_count: 0,
                recent_changes: 0,
                total_rooms: 0,
                total_floors: 0,
            },
            activities: Vec::new(),
            building_name,
            refresh_interval: Duration::from_secs(5),
        }
    }

    fn refresh(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        self.load_stats()?;
        self.load_activities()?;
        Ok(())
    }

    fn load_stats(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let building_data = loading::load_building_data(&self.building_name)?;

        let mut healthy = 0;
        let mut warning = 0;
        let mut critical = 0;
        let mut unknown = 0;
        let mut total_equipment = 0;
        let mut total_rooms = 0;

        for floor in &building_data.floors {
            // Count rooms from wings
            for wing in &floor.wings {
                total_rooms += wing.rooms.len();
            }

            for equipment in &floor.equipment {
                total_equipment += 1;
                // Use health_status if available, otherwise map from status
                use crate::core::{EquipmentHealthStatus, EquipmentStatus};
                if let Some(health_status) = &equipment.health_status {
                    match health_status {
                        EquipmentHealthStatus::Healthy => healthy += 1,
                        EquipmentHealthStatus::Warning => warning += 1,
                        EquipmentHealthStatus::Critical => critical += 1,
                        EquipmentHealthStatus::Unknown => unknown += 1,
                    }
                } else {
                    // Map operational status to health status for counting
                    match equipment.status {
                        EquipmentStatus::Active => healthy += 1,
                        EquipmentStatus::Maintenance => warning += 1,
                        EquipmentStatus::OutOfOrder => critical += 1,
                        EquipmentStatus::Inactive | EquipmentStatus::Unknown => unknown += 1,
                    }
                }
            }
        }

        self.stats = DashboardStats {
            total_equipment,
            healthy_count: healthy,
            warning_count: warning,
            critical_count: critical,
            unknown_count: unknown,
            recent_changes: 0,
            total_rooms,
            total_floors: building_data.floors.len(),
        };

        Ok(())
    }

    fn load_activities(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut current_path = std::env::current_dir()?;
        let mut repo_path = None;

        loop {
            let git_path = current_path.join(".git");
            if git_path.exists() {
                repo_path = Some(current_path.to_string_lossy().to_string());
                break;
            }

            if !current_path.pop() {
                break;
            }
        }

        let mut activities = Vec::new();

        if let Some(repo_path) = repo_path {
            let config = GitConfigManager::default_config();
            if let Ok(manager) = BuildingGitManager::new(&repo_path, &self.building_name, config) {
                if let Ok(commits) = manager.list_commits(5) {
                    for commit in commits {
                        let timestamp = chrono::DateTime::from_timestamp(commit.time, 0)
                            .unwrap_or_default()
                            .format("%Y-%m-%d %H:%M")
                            .to_string();

                        activities.push(ActivityItem {
                            timestamp,
                            message: commit
                                .message
                                .lines()
                                .next()
                                .unwrap_or("No message")
                                .to_string(),
                            commit_hash: Some(commit.id[..8].to_string()),
                        });
                    }
                }
            }
        }

        self.activities = activities;
        Ok(())
    }
}

/// Render header widget
fn render_header<'a>(building_name: &str, theme: &'a Theme) -> Paragraph<'a> {
    let title = format!("ArxOS Building Dashboard - {}", building_name);
    Paragraph::new(title)
        .style(Style::default().fg(theme.text).add_modifier(Modifier::BOLD))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::ALL).title("Dashboard"))
}

/// Render summary cards
fn render_summary_cards<'a>(
    stats: &DashboardStats,
    area: Rect,
    theme: &'a Theme,
) -> Vec<Paragraph<'a>> {
    let card_areas = card_grid(area, 4);
    let mut cards = Vec::new();

    if card_areas.len() >= 4 {
        // Equipment card
        cards.push(
            Paragraph::new(vec![
                Line::from(vec![Span::styled(
                    stats.total_equipment.to_string(),
                    Style::default()
                        .fg(theme.primary)
                        .add_modifier(Modifier::BOLD),
                )]),
                Line::from(vec![Span::styled(
                    "Equipment",
                    Style::default().fg(theme.muted),
                )]),
            ])
            .block(Block::default().borders(Borders::ALL).title("Equipment"))
            .alignment(Alignment::Center),
        );

        // Alerts card
        let alert_color = if stats.warning_count + stats.critical_count > 0 {
            Color::Yellow
        } else {
            Color::Green
        };
        cards.push(
            Paragraph::new(vec![
                Line::from(vec![Span::styled(
                    (stats.warning_count + stats.critical_count).to_string(),
                    Style::default()
                        .fg(alert_color)
                        .add_modifier(Modifier::BOLD),
                )]),
                Line::from(vec![Span::styled(
                    "Alerts",
                    Style::default().fg(theme.muted),
                )]),
            ])
            .block(Block::default().borders(Borders::ALL).title("Alerts"))
            .alignment(Alignment::Center),
        );

        // Critical card
        let critical_color = if stats.critical_count > 0 {
            Color::Red
        } else {
            Color::Green
        };
        cards.push(
            Paragraph::new(vec![
                Line::from(vec![Span::styled(
                    stats.critical_count.to_string(),
                    Style::default()
                        .fg(critical_color)
                        .add_modifier(Modifier::BOLD),
                )]),
                Line::from(vec![Span::styled(
                    "Critical",
                    Style::default().fg(theme.muted),
                )]),
            ])
            .block(Block::default().borders(Borders::ALL).title("Critical"))
            .alignment(Alignment::Center),
        );

        // Rooms card
        cards.push(
            Paragraph::new(vec![
                Line::from(vec![Span::styled(
                    stats.total_rooms.to_string(),
                    Style::default()
                        .fg(theme.secondary)
                        .add_modifier(Modifier::BOLD),
                )]),
                Line::from(vec![Span::styled(
                    "Rooms",
                    Style::default().fg(theme.muted),
                )]),
            ])
            .block(Block::default().borders(Borders::ALL).title("Rooms"))
            .alignment(Alignment::Center),
        );
    }

    cards
}

/// Render equipment status breakdown
fn render_status_breakdown<'a>(
    stats: &DashboardStats,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let lines = vec![
        Line::from(vec![Span::styled(
            "Equipment Status",
            Style::default().fg(theme.text).add_modifier(Modifier::BOLD),
        )]),
        Line::from(vec![
            Span::styled(
                StatusColor::Healthy.icon(),
                Style::default().fg(StatusColor::Healthy.color()),
            ),
            Span::styled(" Healthy: ", Style::default().fg(theme.text)),
            Span::styled(
                stats.healthy_count.to_string(),
                Style::default().fg(StatusColor::Healthy.color()),
            ),
        ]),
        Line::from(vec![
            Span::styled(
                StatusColor::Warning.icon(),
                Style::default().fg(StatusColor::Warning.color()),
            ),
            Span::styled(" Warning: ", Style::default().fg(theme.text)),
            Span::styled(
                stats.warning_count.to_string(),
                Style::default().fg(StatusColor::Warning.color()),
            ),
        ]),
        Line::from(vec![
            Span::styled(
                StatusColor::Critical.icon(),
                Style::default().fg(StatusColor::Critical.color()),
            ),
            Span::styled(" Critical: ", Style::default().fg(theme.text)),
            Span::styled(
                stats.critical_count.to_string(),
                Style::default().fg(StatusColor::Critical.color()),
            ),
        ]),
        Line::from(vec![
            Span::styled(
                StatusColor::Unknown.icon(),
                Style::default().fg(StatusColor::Unknown.color()),
            ),
            Span::styled(" Unknown: ", Style::default().fg(theme.text)),
            Span::styled(
                stats.unknown_count.to_string(),
                Style::default().fg(StatusColor::Unknown.color()),
            ),
        ]),
    ];

    Paragraph::new(lines)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Status Breakdown"),
        )
        .alignment(Alignment::Left)
}

/// Render recent activity list
fn render_activity_list<'a>(
    activities: &[ActivityItem],
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let lines: Vec<Line> = activities
        .iter()
        .take(10)
        .map(|activity| {
            let commit_info = if let Some(ref hash) = activity.commit_hash {
                format!("[{}] ", hash)
            } else {
                String::new()
            };

            Line::from(vec![
                Span::styled(activity.timestamp.clone(), Style::default().fg(theme.muted)),
                Span::styled(" ", Style::default()),
                Span::styled(commit_info, Style::default().fg(theme.secondary)),
                Span::styled(activity.message.clone(), Style::default().fg(theme.text)),
            ])
        })
        .collect();

    let content = if lines.is_empty() {
        vec![Line::from(vec![Span::styled(
            "No recent activity",
            Style::default().fg(theme.muted),
        )])]
    } else {
        lines
    };

    Paragraph::new(content)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Recent Activity"),
        )
        .alignment(Alignment::Left)
}

/// Render footer with controls
fn render_footer<'a>(theme: &'a Theme) -> Paragraph<'a> {
    let help_text = "r: Refresh | q: Quit | Auto-refresh every 5s";
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive status dashboard
pub fn handle_status_dashboard(
    building_name: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();

    let building = building_name.unwrap_or_else(|| {
        // Try to find building name from YAML files
        if let Ok(files) = crate::utils::loading::find_yaml_files() {
            if let Some(first_file) = files.first() {
                std::path::Path::new(first_file)
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("Default Building")
                    .to_string()
            } else {
                "Default Building".to_string()
            }
        } else {
            "Default Building".to_string()
        }
    });

    let mut state = DashboardState::new(building);
    state.refresh()?;

    let mut last_refresh = std::time::Instant::now();

    loop {
        terminal.terminal().draw(|frame| {
            let chunks = dashboard_layout(frame.size());

            // Header
            let header = render_header(&state.building_name, &theme);
            frame.render_widget(header, chunks[0]);

            // Content area
            let content_chunks = split_horizontal(chunks[1], 40, 60);

            // Left: Summary cards and status breakdown
            let left_chunks = Layout::default()
                .direction(ratatui::layout::Direction::Vertical)
                .constraints([Constraint::Length(8), Constraint::Min(0)])
                .split(content_chunks[0])
                .to_vec();

            // Summary cards
            let cards = render_summary_cards(&state.stats, left_chunks[0], &theme);
            let card_areas = card_grid(left_chunks[0], 4);
            for (i, card) in cards.into_iter().enumerate() {
                if i < card_areas.len() {
                    frame.render_widget(card, card_areas[i]);
                }
            }

            // Status breakdown
            let breakdown = render_status_breakdown(&state.stats, left_chunks[1], &theme);
            frame.render_widget(breakdown, left_chunks[1]);

            // Right: Recent activity
            let activity = render_activity_list(&state.activities, content_chunks[1], &theme);
            frame.render_widget(activity, content_chunks[1]);

            // Footer
            let footer = render_footer(&theme);
            frame.render_widget(footer, chunks[2]);
        })?;

        // Handle events
        if let Some(Event::Key(key_event)) = terminal.poll_event(Duration::from_millis(100))? {
            if TerminalManager::is_quit_key(&key_event) {
                break;
            } else if key_event.code == KeyCode::Char('r') || key_event.code == KeyCode::Char('R') {
                state.refresh()?;
                last_refresh = std::time::Instant::now();
            }
        }

        // Auto-refresh
        if last_refresh.elapsed() >= state.refresh_interval {
            state.refresh()?;
            last_refresh = std::time::Instant::now();
        }
    }

    Ok(())
}
