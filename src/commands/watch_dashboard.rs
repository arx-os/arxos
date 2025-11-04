//! Enhanced Watch Dashboard for ArxOS TUI
//!
//! Provides comprehensive live monitoring with:
//! - Sensor data tables with real-time updates
//! - Alert feed with severity indicators
//! - Equipment status grid
//! - Multi-building support
//! - Filtering capabilities

use crate::ui::{TerminalManager, Theme, StatusColor};
use crate::ui::layouts::{dashboard_layout, split_horizontal};
use crate::utils::loading;
use crate::hardware::{SensorData, SensorAlert, AlertGenerator};
use crate::yaml::{BuildingData, EquipmentData};
use crate::identity::{UserRegistry, User};
use crate::git::{BuildingGitManager, GitConfigManager};
use crate::commands::git_ops::{find_git_repository, extract_user_id_from_commit, extract_email_from_author};
use chrono::{DateTime, Utc};
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Table, TableState, Row, Cell},
};
use std::time::Duration;
use std::collections::HashMap;

/// Sensor reading for display
#[derive(Debug, Clone)]
struct SensorReading {
    sensor_id: String,
    sensor_type: String,
    value: f64,
    unit: String,
    timestamp: String,
    equipment_id: Option<String>,
    room: Option<String>,
    status: StatusColor,
}

/// Alert item for display
#[derive(Debug, Clone)]
struct AlertItem {
    timestamp: String,
    severity: StatusColor,
    message: String,
    equipment_id: Option<String>,
    sensor_id: Option<String>,
}

/// User activity item for recent changes
#[derive(Debug, Clone)]
struct UserActivityItem {
    timestamp: String,
    relative_time: String,
    commit_hash: String,
    commit_message: String,
    user: Option<UserInfo>,
    email: String,
}

/// User info for display
#[derive(Debug, Clone)]
struct UserInfo {
    name: String,
    email: String,
    organization: Option<String>,
    verified: bool,
}

/// Dashboard state
struct WatchDashboardState {
    building_data: BuildingData,
    sensor_readings: Vec<SensorReading>,
    alerts: Vec<AlertItem>,
    equipment_status: HashMap<String, StatusColor>,
    recent_changes: Vec<UserActivityItem>,
    user_registry: Option<UserRegistry>,
    selected_tab: usize,
    tabs: Vec<String>,
    refresh_interval: Duration,
    runtime: Duration,
    start_time: std::time::Instant,
    filter_building: Option<String>,
    filter_floor: Option<i32>,
    filter_room: Option<String>,
}

impl WatchDashboardState {
    fn new(building_name: Option<String>) -> Result<Self, Box<dyn std::error::Error>> {
        let building = building_name.unwrap_or_else(|| {
            if let Ok(files) = loading::find_yaml_files() {
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
        
        let building_data = loading::load_building_data(&building)?;
        
        let tabs = vec![
            "Overview".to_string(),
            "Sensors".to_string(),
            "Alerts".to_string(),
            "Equipment".to_string(),
            "Activity".to_string(),
        ];
        
        // Try to load user registry (optional)
        let user_registry = find_git_repository()
            .ok()
            .flatten()
            .and_then(|repo_path| {
                UserRegistry::load(std::path::Path::new(&repo_path)).ok()
            });
        
        Ok(Self {
            building_data,
            sensor_readings: Vec::new(),
            alerts: Vec::new(),
            equipment_status: HashMap::new(),
            recent_changes: Vec::new(),
            user_registry,
            selected_tab: 0,
            tabs,
            refresh_interval: Duration::from_secs(5),
            runtime: Duration::ZERO,
            start_time: std::time::Instant::now(),
            filter_building: None,
            filter_floor: None,
            filter_room: None,
        })
    }
    
    fn refresh(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        self.runtime = self.start_time.elapsed();
        self.load_sensor_data()?;
        self.load_alerts()?;
        self.load_equipment_status()?;
        self.load_recent_changes()?;
        Ok(())
    }
    
    fn load_sensor_data(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // In a real implementation, this would load from sensor data files or live streams
        // For now, we'll simulate with equipment data
        let mut readings = Vec::new();
        
        for floor in &self.building_data.floors {
            for equipment in &floor.equipment {
                // Simulate sensor readings based on equipment status
                let (value, unit, sensor_type) = match equipment.status {
                    crate::yaml::EquipmentStatus::Healthy => (22.5, "°C".to_string(), "Temperature".to_string()),
                    crate::yaml::EquipmentStatus::Warning => (25.5, "°C".to_string(), "Temperature".to_string()),
                    crate::yaml::EquipmentStatus::Critical => (30.0, "°C".to_string(), "Temperature".to_string()),
                    _ => (20.0, "°C".to_string(), "Temperature".to_string()),
                };
                
                let room_name = floor.rooms.iter()
                    .find(|r| r.equipment.contains(&equipment.id))
                    .map(|r| r.name.clone());
                
                readings.push(SensorReading {
                    sensor_id: format!("sensor-{}", equipment.id),
                    sensor_type,
                    value,
                    unit,
                    timestamp: chrono::Utc::now().format("%H:%M:%S").to_string(),
                    equipment_id: Some(equipment.id.clone()),
                    room: room_name,
                    status: StatusColor::from(&equipment.status),
                });
            }
        }
        
        self.sensor_readings = readings;
        Ok(())
    }
    
    fn load_alerts(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut alerts = Vec::new();
        
        for floor in &self.building_data.floors {
            for equipment in &floor.equipment {
                match equipment.status {
                    crate::yaml::EquipmentStatus::Warning => {
                        alerts.push(AlertItem {
                            timestamp: chrono::Utc::now().format("%H:%M:%S").to_string(),
                            severity: StatusColor::Warning,
                            message: format!("{}: Warning condition detected", equipment.name),
                            equipment_id: Some(equipment.id.clone()),
                            sensor_id: None,
                        });
                    }
                    crate::yaml::EquipmentStatus::Critical => {
                        alerts.push(AlertItem {
                            timestamp: chrono::Utc::now().format("%H:%M:%S").to_string(),
                            severity: StatusColor::Critical,
                            message: format!("{}: Critical condition requires attention", equipment.name),
                            equipment_id: Some(equipment.id.clone()),
                            sensor_id: None,
                        });
                    }
                    _ => {}
                }
            }
        }
        
        // Sort by severity (Critical first, then Warning)
        alerts.sort_by(|a, b| {
            match (a.severity, b.severity) {
                (StatusColor::Critical, StatusColor::Critical) => a.timestamp.cmp(&b.timestamp).reverse(),
                (StatusColor::Critical, _) => std::cmp::Ordering::Less,
                (_, StatusColor::Critical) => std::cmp::Ordering::Greater,
                (StatusColor::Warning, StatusColor::Warning) => a.timestamp.cmp(&b.timestamp).reverse(),
                (StatusColor::Warning, _) => std::cmp::Ordering::Less,
                (_, StatusColor::Warning) => std::cmp::Ordering::Greater,
                _ => std::cmp::Ordering::Equal,
            }
        });
        
        self.alerts = alerts;
        Ok(())
    }
    
    fn load_equipment_status(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut status_map = HashMap::new();
        
        for floor in &self.building_data.floors {
            for equipment in &floor.equipment {
                status_map.insert(equipment.id.clone(), StatusColor::from(&equipment.status));
            }
        }
        
        self.equipment_status = status_map;
        Ok(())
    }
    
    fn filtered_sensor_readings(&self) -> Vec<&SensorReading> {
        self.sensor_readings.iter()
            .filter(|reading| {
                if let Some(ref filter_room) = self.filter_room {
                    reading.room.as_ref().map_or(false, |r| r.contains(filter_room))
                } else {
                    true
                }
            })
            .collect()
    }
    
    fn filtered_alerts(&self) -> Vec<&AlertItem> {
        self.alerts.iter()
            .filter(|alert| {
                if let Some(ref filter_room) = self.filter_room {
                    // Filter by room if equipment is in that room
                    true // Simplified for now
                } else {
                    true
                }
            })
            .collect()
    }
    
    fn load_recent_changes(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Find Git repository
        let repo_path_str = find_git_repository()?
            .ok_or("Not in a Git repository")?;
        
        // Load commit history
        let config = GitConfigManager::default_config();
        let manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
        let commits = manager.list_commits(10)?; // Last 10 commits
        
        // Build activity items with user info
        let mut activities = Vec::new();
        for commit in commits {
            // Extract user_id from commit message
            let user_id = extract_user_id_from_commit(&commit.message);
            let email = extract_email_from_author(&commit.author)
                .unwrap_or_else(|| commit.author.clone());
            
            // Look up user in registry
            let user_info = if let Some(registry) = &self.user_registry {
                if let Some(uid) = user_id {
                    registry.find_by_id(&uid)
                } else {
                    registry.find_by_email(&email)
                }
                .map(|user| UserInfo {
                    name: user.name.clone(),
                    email: user.email.clone(),
                    organization: user.organization.clone(),
                    verified: user.verified,
                })
            } else {
                None
            };
            
            let timestamp = chrono::DateTime::from_timestamp(commit.time, 0)
                .unwrap_or_else(|| Utc::now());
            let relative_time = format_relative_time(&timestamp);
            
            activities.push(UserActivityItem {
                timestamp: timestamp.format("%Y-%m-%d %H:%M:%S").to_string(),
                relative_time,
                commit_hash: commit.id[..8].to_string(),
                commit_message: commit.message.clone(),
                user: user_info,
                email,
            });
        }
        
        self.recent_changes = activities;
        Ok(())
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

/// Render header with tabs
fn render_header<'a>(
    state: &'a WatchDashboardState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let tabs_text: String = state.tabs.iter()
        .enumerate()
        .map(|(idx, tab)| {
            if idx == state.selected_tab {
                format!("[{}]", tab)
            } else {
                format!(" {} ", tab)
            }
        })
        .collect::<Vec<_>>()
        .join(" ");
    
    let title = format!(
        "ArxOS Live Monitor - {} | Runtime: {}s | Refresh: {}s",
        state.building_data.building.name,
        state.runtime.as_secs(),
        state.refresh_interval.as_secs()
    );
    
    Paragraph::new(vec![
        Line::from(vec![
            Span::styled(title, Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Tabs: ", Style::default().fg(theme.muted)),
            Span::styled(tabs_text, Style::default().fg(theme.primary)),
        ]),
    ])
    .block(Block::default().borders(Borders::ALL).title("Live Monitoring"))
    .alignment(Alignment::Left)
}

/// Render overview tab - returns widgets for summary cards
fn render_overview_cards<'a>(
    state: &'a WatchDashboardState,
    theme: &'a Theme,
) -> Vec<Paragraph<'a>> {
    // Summary cards
    let healthy_count = state.equipment_status.values()
        .filter(|&&status| status == StatusColor::Healthy)
        .count();
    let warning_count = state.equipment_status.values()
        .filter(|&&status| status == StatusColor::Warning)
        .count();
    let critical_count = state.equipment_status.values()
        .filter(|&&status| status == StatusColor::Critical)
        .count();
    
    let cards = vec![
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled(
                    state.equipment_status.len().to_string(),
                    Style::default().fg(theme.primary).add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(vec![
                Span::styled("Total Equipment", Style::default().fg(theme.muted)),
            ]),
        ])
        .block(Block::default().borders(Borders::ALL).title("Equipment"))
        .alignment(Alignment::Center),
        
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled(
                    healthy_count.to_string(),
                    Style::default().fg(StatusColor::Healthy.color()).add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(vec![
                Span::styled("Healthy", Style::default().fg(theme.muted)),
            ]),
        ])
        .block(Block::default().borders(Borders::ALL).title("Healthy"))
        .alignment(Alignment::Center),
        
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled(
                    warning_count.to_string(),
                    Style::default().fg(StatusColor::Warning.color()).add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(vec![
                Span::styled("Warning", Style::default().fg(theme.muted)),
            ]),
        ])
        .block(Block::default().borders(Borders::ALL).title("Warning"))
        .alignment(Alignment::Center),
        
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled(
                    critical_count.to_string(),
                    Style::default().fg(StatusColor::Critical.color()).add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(vec![
                Span::styled("Critical", Style::default().fg(theme.muted)),
            ]),
        ])
        .block(Block::default().borders(Borders::ALL).title("Critical"))
        .alignment(Alignment::Center),
    ];
    
    vec![cards[0].clone(), cards[1].clone(), cards[2].clone(), cards[3].clone()]
}

/// Render recent changes with user attribution
fn render_recent_changes<'a>(
    state: &'a WatchDashboardState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let mut lines = Vec::new();
    
    lines.push(Line::from(vec![
        Span::styled("📝 Recent Changes", Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
    ]));
    lines.push(Line::from(""));
    
    if state.recent_changes.is_empty() {
        lines.push(Line::from(vec![
            Span::styled("No recent changes", Style::default().fg(theme.muted)),
        ]));
    } else {
        for activity in state.recent_changes.iter().take(8) {
            // Commit message (truncated)
            let message_preview = if activity.commit_message.len() > 40 {
                format!("{}...", &activity.commit_message[..37])
            } else {
                activity.commit_message.clone()
            };
            
            lines.push(Line::from(vec![
                Span::styled("🔵 ", Style::default().fg(Color::Blue)),
                Span::styled(message_preview, Style::default().fg(theme.text)),
            ]));
            
            // User info
            if let Some(ref user) = activity.user {
                let badge = if user.verified { "✅" } else { "⚠️" };
                lines.push(Line::from(vec![
                    Span::styled("   By: ", Style::default().fg(theme.muted)),
                    Span::styled(badge, Style::default()),
                    Span::styled(" ", Style::default()),
                    Span::styled(&user.name, Style::default().fg(theme.text)),
                ]));
                
                if let Some(ref org) = user.organization {
                    lines.push(Line::from(vec![
                        Span::styled("   🏢 ", Style::default().fg(theme.muted)),
                        Span::styled(org, Style::default().fg(theme.text)),
                    ]));
                }
                
                lines.push(Line::from(vec![
                    Span::styled("   📧 ", Style::default().fg(theme.muted)),
                    Span::styled(&user.email, Style::default().fg(theme.muted)),
                ]));
            } else {
                // Unknown user
                lines.push(Line::from(vec![
                    Span::styled("   By: ", Style::default().fg(theme.muted)),
                    Span::styled("❓ ", Style::default().fg(Color::Yellow)),
                    Span::styled("Unknown: ", Style::default().fg(theme.muted)),
                    Span::styled(&activity.email, Style::default().fg(theme.muted)),
                ]));
            }
            
            // Timestamp
            lines.push(Line::from(vec![
                Span::styled("   ⏰ ", Style::default().fg(theme.muted)),
                Span::styled(&activity.relative_time, Style::default().fg(theme.muted)),
            ]));
            
            lines.push(Line::from(""));
        }
    }
    
    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Recent Changes"))
        .alignment(Alignment::Left)
}

/// Render alerts paragraph for overview
fn render_overview_alerts<'a>(
    state: &'a WatchDashboardState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let recent_alerts: Vec<Line> = state.filtered_alerts()
        .iter()
        .take(5)
        .map(|alert| {
            Line::from(vec![
                Span::styled(alert.severity.icon(), Style::default().fg(alert.severity.color())),
                Span::styled(" ", Style::default()),
                Span::styled(alert.timestamp.clone(), Style::default().fg(theme.muted)),
                Span::styled(" ", Style::default()),
                Span::styled(alert.message.clone(), Style::default().fg(theme.text)),
            ])
        })
        .collect();
    
    if recent_alerts.is_empty() {
        Paragraph::new(vec![Line::from(vec![
            Span::styled("No active alerts", Style::default().fg(theme.muted)),
        ])])
        .block(Block::default().borders(Borders::ALL).title("Recent Alerts"))
        .alignment(Alignment::Center)
    } else {
        Paragraph::new(recent_alerts)
            .block(Block::default().borders(Borders::ALL).title("Recent Alerts"))
            .alignment(Alignment::Left)
    }
}

/// Render sensors tab
fn render_sensors<'a>(
    state: &'a WatchDashboardState,
    area: Rect,
    theme: &'a Theme,
) -> Table<'a> {
    let readings = state.filtered_sensor_readings();
    
    let rows: Vec<Row> = readings.iter().map(|reading| {
        Row::new(vec![
            Cell::from(reading.sensor_id.clone()),
            Cell::from(reading.sensor_type.clone()),
            Cell::from(format!("{:.1} {}", reading.value, reading.unit)),
            Cell::from(reading.room.as_ref().map(|r| r.as_str()).unwrap_or("N/A")),
            Cell::from(reading.status.icon().to_string()),
            Cell::from(reading.timestamp.clone()),
        ])
    }).collect();
    
    Table::new(rows)
        .widths(&[
            Constraint::Percentage(20),
            Constraint::Percentage(15),
            Constraint::Percentage(15),
            Constraint::Percentage(20),
            Constraint::Percentage(10),
            Constraint::Percentage(20),
        ])
    .header(Row::new(vec![
        Cell::from("Sensor ID").style(Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        Cell::from("Type").style(Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        Cell::from("Value").style(Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        Cell::from("Room").style(Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        Cell::from("Status").style(Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        Cell::from("Time").style(Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
    ]))
    .block(Block::default().borders(Borders::ALL).title("Sensor Data"))
    .style(Style::default().fg(theme.text))
    .column_spacing(1)
}

/// Render alerts tab
fn render_alerts<'a>(
    state: &'a WatchDashboardState,
    area: Rect,
    theme: &'a Theme,
) -> List<'a> {
    let alerts = state.filtered_alerts();
    
    let items: Vec<ListItem> = alerts.iter().map(|alert| {
        ListItem::new(Line::from(vec![
            Span::styled(alert.severity.icon(), Style::default().fg(alert.severity.color())),
            Span::styled(" ", Style::default()),
            Span::styled(alert.timestamp.clone(), Style::default().fg(theme.muted)),
            Span::styled(" ", Style::default()),
            Span::styled(alert.message.clone(), Style::default().fg(theme.text)),
        ]))
    }).collect();
    
    List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Active Alerts"))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
}

/// Render equipment tab
fn render_equipment<'a>(
    state: &'a WatchDashboardState,
    area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let equipment_list: Vec<Line> = state.building_data.floors.iter()
        .flat_map(|floor| {
            floor.equipment.iter().map(move |equipment| {
                let status = state.equipment_status.get(&equipment.id)
                    .copied()
                    .unwrap_or(StatusColor::Unknown);
                
                Line::from(vec![
                    Span::styled(status.icon(), Style::default().fg(status.color())),
                    Span::styled(" ", Style::default()),
                    Span::styled(equipment.name.clone(), Style::default().fg(theme.text)),
                    Span::styled(" - ", Style::default().fg(theme.muted)),
                    Span::styled(equipment.equipment_type.clone(), Style::default().fg(theme.muted)),
                ])
            })
        })
        .collect();
    
    Paragraph::new(equipment_list)
        .block(Block::default().borders(Borders::ALL).title("Equipment Status"))
        .alignment(Alignment::Left)
}

/// Render footer
fn render_footer<'a>(theme: &'a Theme) -> Paragraph<'a> {
    let help_text = "Tab/→: Next Tab | Shift+Tab/←: Prev Tab | r: Refresh | q: Quit";
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle enhanced watch dashboard
pub fn handle_watch_dashboard(
    building: Option<String>,
    _floor: Option<i32>,
    _room: Option<String>,
    refresh_interval: u64,
    _sensors_only: bool,
    _alerts_only: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();
    
    let mut state = WatchDashboardState::new(building)?;
    state.refresh_interval = Duration::from_secs(refresh_interval);
    state.refresh()?;
    
    let mut last_refresh = std::time::Instant::now();
    
    loop {
        terminal.terminal().draw(|frame| {
            let chunks = dashboard_layout(frame.size());
            
            // Header
            let header = render_header(&state, &theme);
            frame.render_widget(header, chunks[0]);
            
            // Content based on selected tab
            match state.selected_tab {
                0 => {
                    // Overview tab
                    let overview_chunks = Layout::default()
                        .direction(ratatui::layout::Direction::Vertical)
                        .constraints([
                            Constraint::Length(6),
                            Constraint::Min(0),
                        ])
                        .split(chunks[1])
                        .to_vec();
                    
                    // Summary cards
                    let summary_chunks = Layout::default()
                        .direction(ratatui::layout::Direction::Horizontal)
                        .constraints([
                            Constraint::Percentage(25),
                            Constraint::Percentage(25),
                            Constraint::Percentage(25),
                            Constraint::Percentage(25),
                        ])
                        .split(overview_chunks[0])
                        .to_vec();
                    
                    let cards = render_overview_cards(&state, &theme);
                    for (i, card) in cards.into_iter().enumerate() {
                        if i < summary_chunks.len() {
                            frame.render_widget(card, summary_chunks[i]);
                        }
                    }
                    
                    // Split remaining space between alerts and recent changes
                    let bottom_chunks = Layout::default()
                        .direction(ratatui::layout::Direction::Horizontal)
                        .constraints([
                            Constraint::Percentage(50),
                            Constraint::Percentage(50),
                        ])
                        .split(overview_chunks[1])
                        .to_vec();
                    
                    let alerts_widget = render_overview_alerts(&state, &theme);
                    frame.render_widget(alerts_widget, bottom_chunks[0]);
                    
                    let changes_widget = render_recent_changes(&state, &theme);
                    frame.render_widget(changes_widget, bottom_chunks[1]);
                }
                1 => {
                    // Sensors tab
                    let sensors_table = render_sensors(&state, chunks[1], &theme);
                    frame.render_widget(sensors_table, chunks[1]);
                }
                2 => {
                    // Alerts tab
                    let alerts_list = render_alerts(&state, chunks[1], &theme);
                    frame.render_widget(alerts_list, chunks[1]);
                }
                3 => {
                    // Equipment tab
                    let equipment_paragraph = render_equipment(&state, chunks[1], &theme);
                    frame.render_widget(equipment_paragraph, chunks[1]);
                }
                4 => {
                    // Activity tab
                    let activity_widget = render_recent_changes(&state, &theme);
                    frame.render_widget(activity_widget, chunks[1]);
                }
                _ => {}
            }
            
            // Footer
            let footer = render_footer(&theme);
            frame.render_widget(footer, chunks[2]);
        })?;
        
        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) => {
                    if key_event.code == KeyCode::Char('q') || key_event.code == KeyCode::Esc {
                        break;
                    } else if key_event.code == KeyCode::Tab {
                        state.selected_tab = (state.selected_tab + 1) % state.tabs.len();
                    } else if key_event.code == KeyCode::BackTab {
                        state.selected_tab = if state.selected_tab == 0 {
                            state.tabs.len() - 1
                        } else {
                            state.selected_tab - 1
                        };
                    } else if key_event.code == KeyCode::Right {
                        state.selected_tab = (state.selected_tab + 1) % state.tabs.len();
                    } else if key_event.code == KeyCode::Left {
                        state.selected_tab = if state.selected_tab == 0 {
                            state.tabs.len() - 1
                        } else {
                            state.selected_tab - 1
                        };
                    } else if key_event.code == KeyCode::Char('r') || key_event.code == KeyCode::Char('R') {
                        state.refresh()?;
                        last_refresh = std::time::Instant::now();
                    }
                }
                _ => {}
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

