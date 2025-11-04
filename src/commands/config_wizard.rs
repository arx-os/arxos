//! Interactive Configuration Wizard for ArxOS TUI
//!
//! Provides a user-friendly interface for configuring ArxOS:
//! - Tabbed interface for config sections
//! - Form fields with labels and help text
//! - Real-time validation
//! - Preview changes before saving
//! - Smart defaults with explanations

use crate::ui::{TerminalManager, Theme};
use crate::config::{ArxConfig, ConfigManager, ConfigResult};
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Tabs},
};
use std::time::Duration;

/// Configuration section
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ConfigSection {
    User,
    Path,
    Building,
    Performance,
    UI,
}

impl ConfigSection {
    fn all() -> Vec<Self> {
        vec![
            ConfigSection::User,
            ConfigSection::Path,
            ConfigSection::Building,
            ConfigSection::Performance,
            ConfigSection::UI,
        ]
    }
    
    fn name(&self) -> &'static str {
        match self {
            ConfigSection::User => "User",
            ConfigSection::Path => "Paths",
            ConfigSection::Building => "Building",
            ConfigSection::Performance => "Performance",
            ConfigSection::UI => "UI",
        }
    }
}

/// Field editor state
#[derive(Debug, Clone)]
struct FieldEditor {
    label: String,
    value: String,
    help_text: String,
    is_valid: bool,
    error_message: Option<String>,
}

/// Wizard state
struct ConfigWizardState {
    config: ArxConfig,
    original_config: ArxConfig,
    selected_section: usize,
    sections: Vec<ConfigSection>,
    fields: Vec<FieldEditor>,
    selected_field: usize,
    show_preview: bool,
    has_changes: bool,
}

impl ConfigWizardState {
    fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let config_manager = ConfigManager::new()?;
        let config = config_manager.get_config().clone();
        let original_config = config.clone();
        
        let sections = ConfigSection::all();
        let mut fields = Vec::new();
        
        // Initialize fields for first section
        Self::build_fields_for_section(&config, sections[0], &mut fields);
        
        Ok(Self {
            config,
            original_config,
            selected_section: 0,
            sections,
            fields,
            selected_field: 0,
            show_preview: false,
            has_changes: false,
        })
    }
    
    fn build_fields_for_section(
        config: &ArxConfig,
        section: ConfigSection,
        fields: &mut Vec<FieldEditor>,
    ) {
        fields.clear();
        
        match section {
            ConfigSection::User => {
                fields.push(FieldEditor {
                    label: "Name".to_string(),
                    value: config.user.name.clone(),
                    help_text: "Your name for Git commits".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Email".to_string(),
                    value: config.user.email.clone(),
                    help_text: "Your email for Git commits".to_string(),
                    is_valid: true,
                    error_message: None,
                });
            }
            ConfigSection::Path => {
                fields.push(FieldEditor {
                    label: "Default Import Path".to_string(),
                    value: config.paths.default_import_path.to_string_lossy().to_string(),
                    help_text: "Directory for importing IFC files".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Backup Path".to_string(),
                    value: config.paths.backup_path.to_string_lossy().to_string(),
                    help_text: "Directory for backup files".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Template Path".to_string(),
                    value: config.paths.template_path.to_string_lossy().to_string(),
                    help_text: "Directory for template files".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Temp Path".to_string(),
                    value: config.paths.temp_path.to_string_lossy().to_string(),
                    help_text: "Directory for temporary files".to_string(),
                    is_valid: true,
                    error_message: None,
                });
            }
            ConfigSection::Building => {
                fields.push(FieldEditor {
                    label: "Default Coordinate System".to_string(),
                    value: config.building.default_coordinate_system.clone(),
                    help_text: "Default coordinate system (WGS84, UTM, LOCAL)".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Auto Commit".to_string(),
                    value: config.building.auto_commit.to_string(),
                    help_text: "Automatically commit changes to Git (true/false)".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Naming Pattern".to_string(),
                    value: config.building.naming_pattern.clone(),
                    help_text: "Default building naming pattern".to_string(),
                    is_valid: true,
                    error_message: None,
                });
            }
            ConfigSection::Performance => {
                fields.push(FieldEditor {
                    label: "Max Parallel Threads".to_string(),
                    value: config.performance.max_parallel_threads.to_string(),
                    help_text: "Maximum threads for processing".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Memory Limit (MB)".to_string(),
                    value: config.performance.memory_limit_mb.to_string(),
                    help_text: "Memory limit in megabytes".to_string(),
                    is_valid: true,
                    error_message: None,
                });
                fields.push(FieldEditor {
                    label: "Cache Enabled".to_string(),
                    value: config.performance.cache_enabled.to_string(),
                    help_text: "Enable caching (true/false)".to_string(),
                    is_valid: true,
                    error_message: None,
                });
            }
            ConfigSection::UI => {
                fields.push(FieldEditor {
                    label: "Color Scheme".to_string(),
                    value: "default".to_string(),
                    help_text: "Color scheme for TUI (default/dark/light)".to_string(),
                    is_valid: true,
                    error_message: None,
                });
            }
        }
    }
    
    fn update_selected_section(&mut self, section_idx: usize) {
        if section_idx < self.sections.len() {
            self.selected_section = section_idx;
            Self::build_fields_for_section(&self.config, self.sections[section_idx], &mut self.fields);
            self.selected_field = 0;
        }
    }
    
    fn update_field_value(&mut self, field_idx: usize, value: String) {
        if field_idx < self.fields.len() {
            self.fields[field_idx].value = value.clone();
            
            // Validate field
            self.validate_field(field_idx);
            
            // Update config
            self.apply_field_to_config(field_idx);
            self.has_changes = true;
        }
    }
    
    fn validate_field(&mut self, field_idx: usize) {
        if field_idx >= self.fields.len() {
            return;
        }
        
        let field = &mut self.fields[field_idx];
        let section = self.sections[self.selected_section];
        
        match section {
            ConfigSection::User => {
                match field.label.as_str() {
                    "Email" => {
                        if field.value.contains('@') && field.value.contains('.') {
                            field.is_valid = true;
                            field.error_message = None;
                        } else {
                            field.is_valid = false;
                            field.error_message = Some("Invalid email format".to_string());
                        }
                    }
                    "Name" => {
                        if !field.value.is_empty() {
                            field.is_valid = true;
                            field.error_message = None;
                        } else {
                            field.is_valid = false;
                            field.error_message = Some("Name cannot be empty".to_string());
                        }
                    }
                    _ => {
                        field.is_valid = true;
                        field.error_message = None;
                    }
                }
            }
            ConfigSection::Path => {
                // Basic path validation
                if !field.value.is_empty() {
                    field.is_valid = true;
                    field.error_message = None;
                } else {
                    field.is_valid = false;
                    field.error_message = Some("Path cannot be empty".to_string());
                }
            }
            ConfigSection::Performance => {
                match field.label.as_str() {
                    "Max Parallel Threads" => {
                        if let Ok(num) = field.value.parse::<usize>() {
                            if num > 0 && num <= 128 {
                                field.is_valid = true;
                                field.error_message = None;
                            } else {
                                field.is_valid = false;
                                field.error_message = Some("Must be between 1 and 128".to_string());
                            }
                        } else {
                            field.is_valid = false;
                            field.error_message = Some("Must be a number".to_string());
                        }
                    }
                    "Memory Limit (MB)" => {
                        if let Ok(num) = field.value.parse::<usize>() {
                            if num > 0 && num <= 10000 {
                                field.is_valid = true;
                                field.error_message = None;
                            } else {
                                field.is_valid = false;
                                field.error_message = Some("Must be between 1 and 10000".to_string());
                            }
                        } else {
                            field.is_valid = false;
                            field.error_message = Some("Must be a number".to_string());
                        }
                    }
                    "Cache Enabled" => {
                        if field.value == "true" || field.value == "false" {
                            field.is_valid = true;
                            field.error_message = None;
                        } else {
                            field.is_valid = false;
                            field.error_message = Some("Must be 'true' or 'false'".to_string());
                        }
                    }
                    _ => {
                        field.is_valid = true;
                        field.error_message = None;
                    }
                }
            }
            _ => {
                field.is_valid = true;
                field.error_message = None;
            }
        }
    }
    
    fn apply_field_to_config(&mut self, field_idx: usize) {
        if field_idx >= self.fields.len() {
            return;
        }
        
        let field = &self.fields[field_idx];
        let section = self.sections[self.selected_section];
        
        match section {
            ConfigSection::User => {
                match field.label.as_str() {
                    "Name" => {
                        self.config.user.name = field.value.clone();
                    }
                    "Email" => {
                        self.config.user.email = field.value.clone();
                    }
                    _ => {}
                }
            }
            ConfigSection::Path => {
                match field.label.as_str() {
                    "Default Import Path" => {
                        self.config.paths.default_import_path = std::path::PathBuf::from(&field.value);
                    }
                    "Backup Path" => {
                        self.config.paths.backup_path = std::path::PathBuf::from(&field.value);
                    }
                    "Template Path" => {
                        self.config.paths.template_path = std::path::PathBuf::from(&field.value);
                    }
                    "Temp Path" => {
                        self.config.paths.temp_path = std::path::PathBuf::from(&field.value);
                    }
                    _ => {}
                }
            }
            ConfigSection::Building => {
                match field.label.as_str() {
                    "Default Coordinate System" => {
                        self.config.building.default_coordinate_system = field.value.clone();
                    }
                    "Auto Commit" => {
                        self.config.building.auto_commit = field.value.parse().unwrap_or(false);
                    }
                    "Naming Pattern" => {
                        self.config.building.naming_pattern = field.value.clone();
                    }
                    _ => {}
                }
            }
            ConfigSection::Performance => {
                match field.label.as_str() {
                    "Max Parallel Threads" => {
                        if let Ok(num) = field.value.parse::<usize>() {
                            self.config.performance.max_parallel_threads = num;
                        }
                    }
                    "Memory Limit (MB)" => {
                        if let Ok(num) = field.value.parse::<usize>() {
                            self.config.performance.memory_limit_mb = num;
                        }
                    }
                    "Cache Enabled" => {
                        self.config.performance.cache_enabled = field.value.parse().unwrap_or(false);
                    }
                    _ => {}
                }
            }
            _ => {}
        }
    }
    
    fn save_config(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut config_manager = ConfigManager::new()?;
        config_manager.update_config(|config| {
            *config = self.config.clone();
            Ok(())
        })?;
        // Determine save path - prefer project config, then user config
        let project_config_path = std::env::current_dir()?.join("arx.toml");
        let home_dir = std::env::var("HOME")
            .or_else(|_| std::env::var("USERPROFILE"))
            .map_err(|_| "Cannot find home directory")?;
        let user_config_dir = std::path::PathBuf::from(home_dir).join(".arx");
        std::fs::create_dir_all(&user_config_dir)?;
        let user_config_path = user_config_dir.join("config.toml");
        
        // Save to project config if it exists, otherwise user config
        let save_path = if project_config_path.exists() {
            project_config_path
        } else {
            user_config_path
        };
        
        // Use toml crate to serialize and save
        let toml_content = toml::to_string_pretty(&self.config)
            .map_err(|e| format!("Failed to serialize config: {}", e))?;
        std::fs::write(&save_path, toml_content)?;
        self.original_config = self.config.clone();
        self.has_changes = false;
        Ok(())
    }
    
    fn next_field(&mut self) {
        if !self.fields.is_empty() {
            self.selected_field = (self.selected_field + 1) % self.fields.len();
        }
    }
    
    fn previous_field(&mut self) {
        if !self.fields.is_empty() {
            self.selected_field = if self.selected_field == 0 {
                self.fields.len() - 1
            } else {
                self.selected_field - 1
            };
        }
    }
}

/// Render header with tabs
fn render_header<'a>(
    state: &'a ConfigWizardState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let tabs: Vec<String> = state.sections.iter()
        .enumerate()
        .map(|(idx, section)| {
            if idx == state.selected_section {
                format!("[{}]", section.name())
            } else {
                format!(" {} ", section.name())
            }
        })
        .collect();
    
    let tabs_text = tabs.join(" ");
    
    Paragraph::new(vec![
        Line::from(vec![
            Span::styled("ArxOS Configuration Wizard", Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Sections: ", Style::default().fg(theme.muted)),
            Span::styled(tabs_text, Style::default().fg(theme.primary)),
        ]),
    ])
    .block(Block::default().borders(Borders::ALL).title("Configuration"))
    .alignment(Alignment::Left)
}

/// Render fields list
fn render_fields<'a>(
    state: &'a ConfigWizardState,
    area: Rect,
    theme: &'a Theme,
) -> List<'a> {
    let items: Vec<ListItem> = state.fields.iter()
        .enumerate()
        .map(|(idx, field)| {
            let is_selected = idx == state.selected_field;
            let prefix = if is_selected { ">" } else { " " };
            
            let status_icon = if field.is_valid {
                "✓"
            } else {
                "✗"
            };
            
            let status_color = if field.is_valid {
                Color::Green
            } else {
                Color::Red
            };
            
            let mut line_parts = vec![
                Span::styled(prefix, Style::default().fg(theme.accent)),
                Span::styled(" ", Style::default()),
                Span::styled(status_icon, Style::default().fg(status_color)),
                Span::styled(" ", Style::default()),
                Span::styled(
                    field.label.clone(),
                    Style::default()
                        .fg(theme.text)
                        .add_modifier(if is_selected { Modifier::BOLD | Modifier::REVERSED } else { Modifier::empty() }),
                ),
                Span::styled(": ", Style::default().fg(theme.muted)),
                Span::styled(
                    field.value.clone(),
                    Style::default()
                        .fg(if is_selected { theme.accent } else { theme.text })
                        .add_modifier(if is_selected { Modifier::BOLD } else { Modifier::empty() }),
                ),
            ];
            
            if !field.is_valid {
                if let Some(ref error) = field.error_message {
                    line_parts.push(Span::styled(
                        format!(" ({})", error),
                        Style::default().fg(Color::Red),
                    ));
                }
            }
            
            ListItem::new(Line::from(line_parts))
        })
        .collect();
    
    List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Configuration Fields"))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
}

/// Render field details and help
fn render_field_details<'a>(
    state: &'a ConfigWizardState,
    area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    if state.fields.is_empty() {
        return Paragraph::new("No fields available")
            .block(Block::default().borders(Borders::ALL).title("Field Details"))
            .alignment(Alignment::Center);
    }
    
    let field = &state.fields[state.selected_field];
    let section = state.sections[state.selected_section];
    
    let mut lines = vec![
        Line::from(vec![
            Span::styled("Field: ", Style::default().fg(theme.muted)),
            Span::styled(field.label.clone(), Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Value: ", Style::default().fg(theme.muted)),
            Span::styled(field.value.clone(), Style::default().fg(theme.text)),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled("Help: ", Style::default().fg(theme.muted)),
        ]),
        Line::from(vec![
            Span::styled(field.help_text.clone(), Style::default().fg(theme.text)),
        ]),
    ];
    
    if !field.is_valid {
        lines.push(Line::from(Span::raw("")));
        let error_msg = field.error_message.as_deref().unwrap_or("Invalid value");
        lines.push(Line::from(vec![
            Span::styled("Error: ", Style::default().fg(Color::Red)),
            Span::styled(error_msg, Style::default().fg(Color::Red)),
        ]));
    }
    
    lines.push(Line::from(Span::raw("")));
    lines.push(Line::from(vec![
        Span::styled("Section: ", Style::default().fg(theme.muted)),
        Span::styled(section.name(), Style::default().fg(theme.text)),
    ]));
    
    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Field Details"))
        .alignment(Alignment::Left)
}

/// Render preview panel
fn render_preview<'a>(
    state: &'a ConfigWizardState,
    area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    if !state.show_preview {
        return Paragraph::new("Press 'p' to preview changes")
            .block(Block::default().borders(Borders::ALL).title("Preview"))
            .alignment(Alignment::Center);
    }
    
    let mut lines = vec![
        Line::from(vec![
            Span::styled("Configuration Preview", Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(Span::raw("")),
    ];
    
    // Show key differences
    if state.config.user.name != state.original_config.user.name {
        lines.push(Line::from(vec![
            Span::styled("User Name: ", Style::default().fg(theme.muted)),
            Span::styled(state.config.user.name.clone(), Style::default().fg(theme.text)),
        ]));
    }
    
    if state.config.user.email != state.original_config.user.email {
        lines.push(Line::from(vec![
            Span::styled("User Email: ", Style::default().fg(theme.muted)),
            Span::styled(state.config.user.email.clone(), Style::default().fg(theme.text)),
        ]));
    }
    
    if state.config.paths.default_import_path != state.original_config.paths.default_import_path {
        lines.push(Line::from(vec![
            Span::styled("Default Import Path: ", Style::default().fg(theme.muted)),
            Span::styled(
                state.config.paths.default_import_path.to_string_lossy().to_string(),
                Style::default().fg(theme.text),
            ),
        ]));
    }
    
    if state.config.building.default_coordinate_system != state.original_config.building.default_coordinate_system {
        lines.push(Line::from(vec![
            Span::styled("Coordinate System: ", Style::default().fg(theme.muted)),
            Span::styled(state.config.building.default_coordinate_system.clone(), Style::default().fg(theme.text)),
        ]));
    }
    
    if state.config.performance.max_parallel_threads != state.original_config.performance.max_parallel_threads {
        lines.push(Line::from(vec![
            Span::styled("Max Threads: ", Style::default().fg(theme.muted)),
            Span::styled(state.config.performance.max_parallel_threads.to_string(), Style::default().fg(theme.text)),
        ]));
    }
    
    if lines.len() == 2 {
        lines.push(Line::from(vec![
            Span::styled("No changes to preview", Style::default().fg(theme.muted)),
        ]));
    }
    
    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Preview Changes"))
        .alignment(Alignment::Left)
}

/// Render footer
fn render_footer<'a>(
    theme: &'a Theme,
    has_changes: bool,
    editing: bool,
) -> Paragraph<'a> {
    let help_text = if editing {
        "Type to edit | Enter: Save | Esc: Cancel | q: Quit"
    } else if has_changes {
        "↑/↓: Navigate | Tab/→: Next Section | s: Save | p: Preview | r: Reset | q: Quit"
    } else {
        "↑/↓: Navigate | Tab/→: Next Section | Enter: Edit | q: Quit"
    };
    
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive configuration wizard
pub fn handle_config_wizard() -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();
    
    let mut state = ConfigWizardState::new()?;
    let mut list_state = ListState::default();
    let mut editing_mode = false;
    let mut edit_buffer = String::new();
    
    loop {
        terminal.terminal().draw(|frame| {
            let chunks = Layout::default()
                .direction(ratatui::layout::Direction::Vertical)
                .constraints([
                    Constraint::Length(4),
                    Constraint::Min(0),
                    Constraint::Length(3),
                ])
                .split(frame.size())
                .to_vec();
            
            // Header
            let header = render_header(&state, &theme);
            frame.render_widget(header, chunks[0]);
            
            // Content
            let content_chunks = Layout::default()
                .direction(ratatui::layout::Direction::Horizontal)
                .constraints([
                    Constraint::Percentage(50),
                    Constraint::Percentage(50),
                ])
                .split(chunks[1])
                .to_vec();
            
            // Left: Fields list
            let fields_list = render_fields(&state, content_chunks[0], &theme);
            list_state.select(Some(state.selected_field));
            frame.render_stateful_widget(fields_list, content_chunks[0], &mut list_state);
            
            // Right: Details or preview
            if state.show_preview {
                let preview = render_preview(&state, content_chunks[1], &theme);
                frame.render_widget(preview, content_chunks[1]);
            } else {
                let details = render_field_details(&state, content_chunks[1], &theme);
                frame.render_widget(details, content_chunks[1]);
            }
            
            // Footer
            let footer = render_footer(&theme, state.has_changes, editing_mode);
            frame.render_widget(footer, chunks[2]);
            
            // Edit overlay
            if editing_mode {
                let edit_text = if edit_buffer.is_empty() {
                    format!("Editing {}: _", state.fields[state.selected_field].label)
                } else {
                    format!("Editing {}: {}_", state.fields[state.selected_field].label, edit_buffer)
                };
                let edit_paragraph = Paragraph::new(edit_text)
                    .style(Style::default().fg(theme.primary))
                    .block(Block::default().borders(Borders::ALL).title("Edit Field"));
                frame.render_widget(edit_paragraph, content_chunks[1]);
            }
        })?;
        
        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) if editing_mode => {
                    match key_event.code {
                        KeyCode::Char(c) => {
                            edit_buffer.push(c);
                        }
                        KeyCode::Backspace => {
                            edit_buffer.pop();
                        }
                        KeyCode::Enter => {
                            // Save edited value
                            state.update_field_value(state.selected_field, edit_buffer.clone());
                            editing_mode = false;
                            edit_buffer.clear();
                        }
                        KeyCode::Esc => {
                            editing_mode = false;
                            edit_buffer.clear();
                        }
                        _ => {}
                    }
                }
                Event::Key(key_event) => {
                    if key_event.code == KeyCode::Char('q') || key_event.code == KeyCode::Esc {
                        if state.has_changes {
                            // Could show confirmation dialog here
                        }
                        break;
                    } else if key_event.code == KeyCode::Down || key_event.code == KeyCode::Char('j') {
                        state.next_field();
                    } else if key_event.code == KeyCode::Up || key_event.code == KeyCode::Char('k') {
                        state.previous_field();
                    } else if key_event.code == KeyCode::Tab || key_event.code == KeyCode::Right {
                        let next_section = (state.selected_section + 1) % state.sections.len();
                        state.update_selected_section(next_section);
                    } else if key_event.code == KeyCode::BackTab || key_event.code == KeyCode::Left {
                        let prev_section = if state.selected_section == 0 {
                            state.sections.len() - 1
                        } else {
                            state.selected_section - 1
                        };
                        state.update_selected_section(prev_section);
                    } else if key_event.code == KeyCode::Enter {
                        // Start editing
                        edit_buffer = state.fields[state.selected_field].value.clone();
                        editing_mode = true;
                    } else if key_event.code == KeyCode::Char('s') || key_event.code == KeyCode::Char('S') {
                        // Save configuration
                        if state.has_changes {
                            if let Err(e) = state.save_config() {
                                // Could show error message here
                                eprintln!("Error saving config: {}", e);
                            }
                        }
                    } else if key_event.code == KeyCode::Char('p') || key_event.code == KeyCode::Char('P') {
                        // Toggle preview
                        state.show_preview = !state.show_preview;
                    } else if key_event.code == KeyCode::Char('r') || key_event.code == KeyCode::Char('R') {
                        // Reset to original
                        state.config = state.original_config.clone();
                        state.update_selected_section(state.selected_section);
                        state.has_changes = false;
                    }
                }
                _ => {}
            }
        }
    }
    
    Ok(())
}

