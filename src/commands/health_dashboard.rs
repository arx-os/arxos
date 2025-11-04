//! Interactive Health Check Dashboard for ArxOS TUI
//!
//! Provides a comprehensive health monitoring interface:
//! - Status cards for each component
//! - Quick fix actions for common issues
//! - Real-time health monitoring
//! - Detailed diagnostics on demand

use crate::ui::{TerminalManager, Theme, StatusColor};
use crate::ui::layouts::{dashboard_layout, split_horizontal};
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Table, TableState, Row, Cell},
};
use std::time::Duration;

/// Component health status
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ComponentStatus {
    Healthy,
    Warning,
    Critical,
    Unknown,
}

impl ComponentStatus {
    fn color(&self) -> StatusColor {
        match self {
            ComponentStatus::Healthy => StatusColor::Healthy,
            ComponentStatus::Warning => StatusColor::Warning,
            ComponentStatus::Critical => StatusColor::Critical,
            ComponentStatus::Unknown => StatusColor::Unknown,
        }
    }
}

/// Component health information
#[derive(Debug, Clone)]
struct ComponentHealth {
    name: String,
    status: ComponentStatus,
    message: String,
    details: Vec<String>,
    quick_fix: Option<String>,
}

/// Health dashboard state
struct HealthDashboardState {
    components: Vec<ComponentHealth>,
    selected_component: usize,
    show_details: bool,
    last_check: std::time::Instant,
    auto_refresh: bool,
    refresh_interval: Duration,
}

impl HealthDashboardState {
    fn new() -> Self {
        let mut state = Self {
            components: Vec::new(),
            selected_component: 0,
            show_details: false,
            last_check: std::time::Instant::now(),
            auto_refresh: true,
            refresh_interval: Duration::from_secs(5),
        };
        state.refresh();
        state
    }
    
    fn refresh(&mut self) {
        self.components = vec![
            check_git_component(),
            check_config_component(),
            check_persistence_component(),
            check_yaml_component(),
        ];
        self.last_check = std::time::Instant::now();
    }
    
    fn next_component(&mut self) {
        if !self.components.is_empty() {
            self.selected_component = (self.selected_component + 1) % self.components.len();
        }
    }
    
    fn previous_component(&mut self) {
        if !self.components.is_empty() {
            self.selected_component = (self.selected_component + self.components.len() - 1) % self.components.len();
        }
    }
    
    fn current_component(&self) -> Option<&ComponentHealth> {
        self.components.get(self.selected_component)
    }
}

/// Check Git component health
fn check_git_component() -> ComponentHealth {
    let mut status = ComponentStatus::Healthy;
    let mut message = String::new();
    let mut details = Vec::new();
    let mut quick_fix = None;
    
    // Check Git availability
    match std::process::Command::new("git").arg("--version").output() {
        Ok(output) => {
            if output.status.success() {
                let version = String::from_utf8_lossy(&output.stdout).trim().to_string();
                message = format!("Git available: {}", version);
                details.push(format!("Version: {}", version));
            } else {
                status = ComponentStatus::Critical;
                message = "Git not available".to_string();
                quick_fix = Some("Install Git: brew install git (macOS) or apt-get install git (Linux)".to_string());
            }
        }
        Err(_) => {
            status = ComponentStatus::Critical;
            message = "Git not found in PATH".to_string();
            quick_fix = Some("Install Git and ensure it's in your PATH".to_string());
        }
    }
    
    // Check git2 crate integration
    match crate::git::BuildingGitManager::new(".", "test", crate::git::GitConfig {
        author_name: "test".to_string(),
        author_email: "test@test.com".to_string(),
        branch: "main".to_string(),
        remote_url: None,
    }) {
        Ok(_) => {
            details.push("Git2 crate integration: OK".to_string());
        }
        Err(e) => {
            if !e.to_string().contains("not a git repository") {
                if status == ComponentStatus::Healthy {
                    status = ComponentStatus::Warning;
                }
                message = format!("Git2 integration warning: {}", e);
                details.push(format!("Git2 error: {}", e));
            } else {
                details.push("Not currently in a git repository (OK)".to_string());
            }
        }
    }
    
    ComponentHealth {
        name: "Git Integration".to_string(),
        status,
        message,
        details,
        quick_fix,
    }
}

/// Check configuration component health
fn check_config_component() -> ComponentHealth {
    let mut status = ComponentStatus::Healthy;
    let mut message = String::new();
    let mut details = Vec::new();
    let mut quick_fix = None;
    
    match crate::config::ConfigManager::new() {
        Ok(config_manager) => {
            let config = config_manager.get_config();
            message = "Configuration loaded successfully".to_string();
            details.push(format!("Auto-commit: {:?}", config.building.auto_commit));
            details.push(format!("Coordinate system: {}", config.building.default_coordinate_system));
            details.push(format!("Max threads: {}", config.performance.max_parallel_threads));
        }
        Err(e) => {
            status = ComponentStatus::Warning;
            message = format!("Configuration warning: {}", e);
            details.push("Using default configuration".to_string());
            quick_fix = Some("Run 'arx config --interactive' to configure ArxOS".to_string());
        }
    }
    
    // Check environment variables
    let git_user = std::env::var("GIT_AUTHOR_NAME").ok();
    let git_email = std::env::var("GIT_AUTHOR_EMAIL").ok();
    
    if git_user.is_some() || git_email.is_some() {
        details.push("Environment variables detected".to_string());
        if let Some(ref name) = git_user {
            details.push(format!("GIT_AUTHOR_NAME: {}", name));
        }
        if let Some(ref email) = git_email {
            details.push(format!("GIT_AUTHOR_EMAIL: {}", email));
        }
    }
    
    ComponentHealth {
        name: "Configuration".to_string(),
        status,
        message,
        details,
        quick_fix,
    }
}

/// Check persistence component health
fn check_persistence_component() -> ComponentHealth {
    let mut status = ComponentStatus::Healthy;
    let mut message = String::new();
    let mut details = Vec::new();
    let mut quick_fix = None;
    
    // Check write permissions
    match std::fs::create_dir_all("test_write_check") {
        Ok(_) => {
            if let Err(e) = std::fs::remove_dir("test_write_check") {
                details.push(format!("Warning: could not clean up test directory: {}", e));
            }
            message = "Write permissions OK".to_string();
            details.push("File system access: OK".to_string());
        }
        Err(e) => {
            status = ComponentStatus::Critical;
            message = format!("Write permissions error: {}", e);
            quick_fix = Some("Check file system permissions and disk space".to_string());
        }
    }
    
    // Check YAML serialization
    use crate::yaml::{BuildingYamlSerializer, BuildingData, BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    
    let test_data = BuildingData {
        building: BuildingInfo {
            id: "test".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "test".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![],
    };
    
    let serializer = BuildingYamlSerializer::new();
    match serializer.to_yaml(&test_data) {
        Ok(_) => {
            details.push("YAML serialization: OK".to_string());
        }
        Err(e) => {
            if status == ComponentStatus::Healthy {
                status = ComponentStatus::Critical;
            }
            message = format!("YAML serialization failed: {}", e);
            quick_fix = Some("Check YAML library installation and dependencies".to_string());
        }
    }
    
    ComponentHealth {
        name: "Persistence".to_string(),
        status,
        message,
        details,
        quick_fix,
    }
}

/// Check YAML component health
fn check_yaml_component() -> ComponentHealth {
    let mut status = ComponentStatus::Healthy;
    let mut message = String::new();
    let mut details = Vec::new();
    let mut quick_fix = None;
    
    use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata, BuildingYamlSerializer};
    use chrono::Utc;
    
    let test_data = BuildingData {
        building: BuildingInfo {
            id: "test".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "test".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![],
    };
    
    let serializer = BuildingYamlSerializer::new();
    match serializer.to_yaml(&test_data) {
        Ok(yaml_str) => {
            match serde_yaml::from_str::<BuildingData>(&yaml_str) {
                Ok(_) => {
                    message = "YAML round-trip parsing OK".to_string();
                    details.push("Serialization: OK".to_string());
                    details.push("Deserialization: OK".to_string());
                }
                Err(e) => {
                    status = ComponentStatus::Critical;
                    message = format!("YAML round-trip parsing failed: {}", e);
                    quick_fix = Some("Check YAML parser installation".to_string());
                }
            }
        }
        Err(e) => {
            status = ComponentStatus::Critical;
            message = format!("YAML serialization failed: {}", e);
            quick_fix = Some("Check YAML library installation".to_string());
        }
    }
    
    ComponentHealth {
        name: "YAML Processing".to_string(),
        status,
        message,
        details,
        quick_fix,
    }
}

/// Render header
fn render_header<'a>(
    state: &'a HealthDashboardState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let healthy_count = state.components.iter()
        .filter(|c| c.status == ComponentStatus::Healthy)
        .count();
    let warning_count = state.components.iter()
        .filter(|c| c.status == ComponentStatus::Warning)
        .count();
    let critical_count = state.components.iter()
        .filter(|c| c.status == ComponentStatus::Critical)
        .count();
    
    let title = format!(
        "ArxOS Health Dashboard | Healthy: {} | Warnings: {} | Critical: {}",
        healthy_count,
        warning_count,
        critical_count
    );
    
    let last_check_text = if state.last_check.elapsed().as_secs() < 60 {
        format!("Last check: {}s ago", state.last_check.elapsed().as_secs())
    } else {
        format!("Last check: {}m ago", state.last_check.elapsed().as_secs() / 60)
    };
    
    Paragraph::new(vec![
        Line::from(vec![
            Span::styled(title, Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled(last_check_text, Style::default().fg(theme.muted)),
            if state.auto_refresh {
                Span::styled(" | Auto-refresh: ON", Style::default().fg(Color::Green))
            } else {
                Span::styled(" | Auto-refresh: OFF", Style::default().fg(Color::Yellow))
            },
        ]),
    ])
    .block(Block::default().borders(Borders::ALL).title("Health Monitor"))
    .alignment(Alignment::Left)
}

/// Render component status cards
fn render_component_cards<'a>(
    state: &'a HealthDashboardState,
    theme: &'a Theme,
    area: Rect,
) -> Vec<Paragraph<'a>> {
    let chunks = Layout::default()
        .direction(ratatui::layout::Direction::Horizontal)
        .constraints(
            state.components.iter().map(|_| Constraint::Percentage(25)).collect::<Vec<_>>()
        )
        .split(area)
        .to_vec();
    
    state.components.iter()
        .enumerate()
        .map(|(idx, component)| {
            let is_selected = idx == state.selected_component;
            let status_color = component.status.color();
            
            let border_style = if is_selected {
                Style::default().fg(theme.accent).add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(theme.muted)
            };
            
            let status_text = match component.status {
                ComponentStatus::Healthy => "✓ Healthy",
                ComponentStatus::Warning => "⚠ Warning",
                ComponentStatus::Critical => "✗ Critical",
                ComponentStatus::Unknown => "? Unknown",
            };
            
            Paragraph::new(vec![
                Line::from(vec![
                    Span::styled(component.name.clone(), Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
                ]),
                Line::from(vec![
                    Span::styled(status_text, Style::default().fg(status_color.color())),
                ]),
                Line::from(vec![
                    Span::styled(
                        component.message.clone(),
                        Style::default().fg(theme.muted),
                    ),
                ]),
            ])
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .border_style(border_style)
                    .title(if is_selected { "▶ Selected" } else { "" })
            )
            .alignment(Alignment::Center)
        })
        .collect()
}

/// Render component details
fn render_component_details<'a>(
    state: &'a HealthDashboardState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    if let Some(component) = state.current_component() {
        let mut lines = vec![
            Line::from(vec![
                Span::styled(
                    format!("{} Details", component.name),
                    Style::default().fg(theme.primary).add_modifier(Modifier::BOLD),
                ),
            ]),
            Line::from(Span::raw("")),
            Line::from(vec![
                Span::styled("Status: ", Style::default().fg(theme.muted)),
                Span::styled(
                    format!("{:?}", component.status),
                    Style::default().fg(component.status.color().color()),
                ),
            ]),
            Line::from(vec![
                Span::styled("Message: ", Style::default().fg(theme.muted)),
                Span::styled(component.message.clone(), Style::default().fg(theme.text)),
            ]),
            Line::from(Span::raw("")),
            Line::from(vec![
                Span::styled("Details:", Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
            ]),
        ];
        
        for detail in &component.details {
            lines.push(Line::from(vec![
                Span::styled("  • ", Style::default().fg(theme.muted)),
                Span::styled(detail.clone(), Style::default().fg(theme.text)),
            ]));
        }
        
        if let Some(ref fix) = component.quick_fix {
            lines.push(Line::from(Span::raw("")));
            lines.push(Line::from(vec![
                Span::styled("Quick Fix:", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
            ]));
            lines.push(Line::from(vec![
                Span::styled("  ", Style::default()),
                Span::styled(fix.clone(), Style::default().fg(Color::Yellow)),
            ]));
        }
        
        Paragraph::new(lines)
            .block(Block::default().borders(Borders::ALL).title("Component Details"))
            .alignment(Alignment::Left)
    } else {
        Paragraph::new("No component selected")
            .block(Block::default().borders(Borders::ALL).title("Component Details"))
            .alignment(Alignment::Center)
    }
}

/// Render footer
fn render_footer<'a>(theme: &'a Theme) -> Paragraph<'a> {
    let help_text = "←/→: Navigate | r: Refresh | d: Toggle Details | a: Toggle Auto-refresh | q: Quit";
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive health dashboard
pub fn handle_health_dashboard() -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();
    
    let mut state = HealthDashboardState::new();
    
    loop {
        terminal.terminal().draw(|frame| {
            let chunks = dashboard_layout(frame.size());
            
            // Header
            let header = render_header(&state, &theme);
            frame.render_widget(header, chunks[0]);
            
            // Component cards
            if !state.show_details {
                let cards = render_component_cards(&state, &theme, chunks[1]);
                let card_chunks = Layout::default()
                    .direction(ratatui::layout::Direction::Horizontal)
                    .constraints(
                        state.components.iter().map(|_| Constraint::Percentage(25)).collect::<Vec<_>>()
                    )
                    .split(chunks[1])
                    .to_vec();
                
                for (idx, card) in cards.iter().enumerate() {
                    if idx < card_chunks.len() {
                        frame.render_widget(card.clone(), card_chunks[idx]);
                    }
                }
            } else {
                // Show details view
                let detail_chunks = Layout::default()
                    .direction(ratatui::layout::Direction::Vertical)
                    .constraints([
                        Constraint::Length(6),
                        Constraint::Min(0),
                    ])
                    .split(chunks[1])
                    .to_vec();
                
                // Component cards at top
                let cards = render_component_cards(&state, &theme, detail_chunks[0]);
                let card_chunks = Layout::default()
                    .direction(ratatui::layout::Direction::Horizontal)
                    .constraints(
                        state.components.iter().map(|_| Constraint::Percentage(25)).collect::<Vec<_>>()
                    )
                    .split(detail_chunks[0])
                    .to_vec();
                
                for (idx, card) in cards.iter().enumerate() {
                    if idx < card_chunks.len() {
                        frame.render_widget(card.clone(), card_chunks[idx]);
                    }
                }
                
                // Details below
                let details = render_component_details(&state, &theme);
                frame.render_widget(details, detail_chunks[1]);
            }
            
            // Footer
            let footer = render_footer(&theme);
            frame.render_widget(footer, chunks[2]);
        })?;
        
        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) => {
                    match key_event.code {
                        KeyCode::Char('q') | KeyCode::Esc => {
                            break;
                        }
                        KeyCode::Char('r') | KeyCode::Char('R') => {
                            state.refresh();
                        }
                        KeyCode::Char('d') | KeyCode::Char('D') => {
                            state.show_details = !state.show_details;
                        }
                        KeyCode::Char('a') | KeyCode::Char('A') => {
                            state.auto_refresh = !state.auto_refresh;
                        }
                        KeyCode::Right | KeyCode::Char('l') => {
                            state.next_component();
                        }
                        KeyCode::Left | KeyCode::Char('h') => {
                            state.previous_component();
                        }
                        _ => {}
                    }
                }
                _ => {}
            }
        }
        
        // Auto-refresh
        if state.auto_refresh && state.last_check.elapsed() >= state.refresh_interval {
            state.refresh();
        }
    }
    
    Ok(())
}

