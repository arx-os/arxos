//! Interactive AR Pending Equipment Manager for ArxOS TUI
//!
//! Provides an efficient interface for reviewing and confirming AR-detected equipment:
//! - Split view with list and details
//! - Quick actions (y/n/e)
//! - Batch operations
//! - Visual indicators (confidence, scan time, location)
//! - Preview changes before confirming

use crate::ui::{TerminalManager, Theme};
use crate::ar_integration::pending::{PendingEquipmentManager, PendingEquipment};
use crate::persistence::PersistenceManager;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
};
use std::time::Duration;
use std::collections::HashSet;

/// Manager state for the pending equipment TUI
struct PendingManagerState {
    manager: PendingEquipmentManager,
    pending_items: Vec<PendingEquipment>,
    selected_index: usize,
    selected_ids: HashSet<String>,
    building_name: String,
    storage_file: std::path::PathBuf,
    show_preview: bool,
    // Reserved for future inline editing feature
    #[allow(dead_code)]
    editing_item: Option<usize>,
}

impl PendingManagerState {
    fn new(building_name: String) -> Result<Self, Box<dyn std::error::Error>> {
        let mut manager = PendingEquipmentManager::new(building_name.clone());
        let storage_file = std::path::PathBuf::from(format!("pending-equipment-{}.json", building_name));
        
        // Load pending equipment from storage
        manager.load_from_storage(&storage_file)?;
        
        // Get pending items
        let pending_refs = manager.list_pending();
        let pending_items: Vec<PendingEquipment> = pending_refs.iter().map(|p| (*p).clone()).collect();
        
        Ok(Self {
            manager,
            pending_items,
            selected_index: 0,
            selected_ids: HashSet::new(),
            building_name,
            storage_file,
            show_preview: false,
            editing_item: None,
        })
    }
    
    fn refresh(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Reload from storage
        self.manager.load_from_storage(&self.storage_file)?;
        let pending_refs = self.manager.list_pending();
        self.pending_items = pending_refs.iter().map(|p| (*p).clone()).collect();
        
        // Adjust selected index if needed
        if self.selected_index >= self.pending_items.len() && !self.pending_items.is_empty() {
            self.selected_index = self.pending_items.len() - 1;
        }
        
        Ok(())
    }
    
    fn selected_item(&self) -> Option<&PendingEquipment> {
        self.pending_items.get(self.selected_index)
    }
    
    fn toggle_selection(&mut self) {
        if let Some(item_id) = self.pending_items.get(self.selected_index).map(|item| item.id.clone()) {
            if self.selected_ids.contains(&item_id) {
                self.selected_ids.remove(&item_id);
            } else {
                self.selected_ids.insert(item_id);
            }
        }
    }
    
    fn select_all(&mut self) {
        self.selected_ids.clear();
        for item in &self.pending_items {
            self.selected_ids.insert(item.id.clone());
        }
    }
    
    fn clear_selection(&mut self) {
        self.selected_ids.clear();
    }
    
    fn next(&mut self) {
        if !self.pending_items.is_empty() {
            self.selected_index = (self.selected_index + 1) % self.pending_items.len();
        }
    }
    
    fn previous(&mut self) {
        if !self.pending_items.is_empty() {
            self.selected_index = if self.selected_index == 0 {
                self.pending_items.len() - 1
            } else {
                self.selected_index - 1
            };
        }
    }
    
    fn confirm_selected(&mut self) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let ids_to_confirm: Vec<String> = if self.selected_ids.is_empty() {
            // Confirm currently selected item if nothing is multi-selected
            if let Some(item) = self.selected_item() {
                vec![item.id.clone()]
            } else {
                return Ok(Vec::new());
            }
        } else {
            self.selected_ids.iter().cloned().collect()
        };
        
        let persistence = PersistenceManager::new(&self.building_name)?;
        let mut building_data = persistence.load_building_data()?;
        
        let mut confirmed_equipment_ids = Vec::new();
        
        for pending_id in &ids_to_confirm {
            match self.manager.confirm_pending(pending_id, &mut building_data) {
                Ok(equipment_id) => {
                    confirmed_equipment_ids.push(equipment_id);
                    // Remove from selection
                    self.selected_ids.remove(pending_id);
                }
                Err(e) => {
                    eprintln!("Error confirming {}: {}", pending_id, e);
                }
            }
        }
        
        // Save pending equipment state
        self.manager.save_to_storage()?;
        
        // Save building data
        persistence.save_building_data(&building_data)?;
        
        // Refresh list
        self.refresh()?;
        
        Ok(confirmed_equipment_ids)
    }
    
    fn reject_selected(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let ids_to_reject: Vec<String> = if self.selected_ids.is_empty() {
            // Reject currently selected item if nothing is multi-selected
            if let Some(item) = self.selected_item() {
                vec![item.id.clone()]
            } else {
                return Ok(());
            }
        } else {
            self.selected_ids.iter().cloned().collect()
        };
        
        for pending_id in &ids_to_reject {
            if let Err(e) = self.manager.reject_pending(pending_id) {
                eprintln!("Error rejecting {}: {}", pending_id, e);
            } else {
                // Remove from selection
                self.selected_ids.remove(pending_id);
            }
        }
        
        // Save pending equipment state
        self.manager.save_to_storage()?;
        
        // Refresh list
        self.refresh()?;
        
        Ok(())
    }
}

/// Render header
fn render_header<'a>(
    state: &'a PendingManagerState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let title = format!(
        "AR Pending Equipment Manager - {} ({})",
        state.building_name,
        state.pending_items.len()
    );
    
    Paragraph::new(title)
        .style(Style::default().fg(theme.text).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::ALL).title("Pending Equipment"))
        .alignment(Alignment::Left)
}

/// Render pending items list
fn render_pending_list<'a>(
    state: &'a PendingManagerState,
    _area: Rect,
    theme: &'a Theme,
) -> List<'a> {
    let items: Vec<ListItem> = state.pending_items.iter()
        .enumerate()
        .map(|(idx, item)| {
            let is_selected = idx == state.selected_index;
            let is_multi_selected = state.selected_ids.contains(&item.id);
            
            let prefix = if is_selected { ">" } else { " " };
            let selection_indicator = if is_multi_selected { "[✓]" } else { "[ ]" };
            
            // Confidence color
            let confidence_color = if item.confidence >= 0.8 {
                Color::Green
            } else if item.confidence >= 0.6 {
                Color::Yellow
            } else {
                Color::Red
            };
            
            let confidence_bar = format!("{:.0}%", item.confidence * 100.0);
            
            // Detection method icon
            let method_icon = match item.detection_method {
                crate::ar_integration::pending::DetectionMethod::ARKit => "📱",
                crate::ar_integration::pending::DetectionMethod::ARCore => "🤖",
                crate::ar_integration::pending::DetectionMethod::LiDAR => "📡",
                crate::ar_integration::pending::DetectionMethod::Manual => "✋",
                crate::ar_integration::pending::DetectionMethod::AI => "🧠",
            };
            
            let line_parts = vec![
                Span::styled(prefix, Style::default().fg(theme.accent)),
                Span::styled(" ", Style::default()),
                Span::styled(selection_indicator, Style::default().fg(if is_multi_selected { Color::Green } else { theme.muted })),
                Span::styled(" ", Style::default()),
                Span::styled(method_icon, Style::default()),
                Span::styled(" ", Style::default()),
                Span::styled(
                    item.name.clone(),
                    Style::default()
                        .fg(theme.text)
                        .add_modifier(if is_selected { Modifier::BOLD | Modifier::REVERSED } else { Modifier::empty() }),
                ),
                Span::styled(" (", Style::default().fg(theme.muted)),
                Span::styled(item.equipment_type.clone(), Style::default().fg(theme.muted)),
                Span::styled(") ", Style::default().fg(theme.muted)),
                Span::styled(
                    confidence_bar,
                    Style::default().fg(confidence_color),
                ),
            ];
            
            ListItem::new(Line::from(line_parts))
        })
        .collect();
    
    List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Pending Items"))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
}

/// Render item details
fn render_item_details<'a>(
    state: &'a PendingManagerState,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    if state.pending_items.is_empty() {
        return Paragraph::new("No pending equipment items")
            .block(Block::default().borders(Borders::ALL).title("Details"))
            .alignment(Alignment::Center);
    }
    
    if let Some(item) = state.selected_item() {
        let mut lines = vec![
            Line::from(vec![
                Span::styled("Name: ", Style::default().fg(theme.muted)),
                Span::styled(item.name.clone(), Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(vec![
                Span::styled("Type: ", Style::default().fg(theme.muted)),
                Span::styled(item.equipment_type.clone(), Style::default().fg(theme.text)),
            ]),
            Line::from(vec![
                Span::styled("ID: ", Style::default().fg(theme.muted)),
                Span::styled(item.id.clone(), Style::default().fg(theme.text)),
            ]),
            Line::from(Span::raw("")),
            Line::from(vec![
                Span::styled("Position: ", Style::default().fg(theme.muted)),
                Span::styled(
                    format!("({:.2}, {:.2}, {:.2})", item.position.x, item.position.y, item.position.z),
                    Style::default().fg(theme.text),
                ),
            ]),
            Line::from(vec![
                Span::styled("Floor: ", Style::default().fg(theme.muted)),
                Span::styled(item.floor_level.to_string(), Style::default().fg(theme.text)),
            ]),
            if let Some(ref room) = item.room_name {
                Line::from(vec![
                    Span::styled("Room: ", Style::default().fg(theme.muted)),
                    Span::styled(room.clone(), Style::default().fg(theme.text)),
                ])
            } else {
                Line::from(vec![
                    Span::styled("Room: ", Style::default().fg(theme.muted)),
                    Span::styled("N/A", Style::default().fg(theme.muted)),
                ])
            },
            Line::from(Span::raw("")),
            Line::from(vec![
                Span::styled("Confidence: ", Style::default().fg(theme.muted)),
                Span::styled(
                    format!("{:.1}%", item.confidence * 100.0),
                    Style::default().fg(if item.confidence >= 0.8 { Color::Green } else if item.confidence >= 0.6 { Color::Yellow } else { Color::Red }),
                ),
            ]),
            Line::from(vec![
                Span::styled("Detection: ", Style::default().fg(theme.muted)),
                Span::styled(
                    format!("{:?}", item.detection_method),
                    Style::default().fg(theme.text),
                ),
            ]),
            Line::from(vec![
                Span::styled("Detected: ", Style::default().fg(theme.muted)),
                Span::styled(
                    item.detected_at.format("%Y-%m-%d %H:%M:%S").to_string(),
                    Style::default().fg(theme.text),
                ),
            ]),
            Line::from(vec![
                Span::styled("Scan ID: ", Style::default().fg(theme.muted)),
                Span::styled(item.scan_id.clone(), Style::default().fg(theme.text)),
            ]),
        ];
        
        if !item.properties.is_empty() {
            lines.push(Line::from(Span::raw("")));
            lines.push(Line::from(vec![
                Span::styled("Properties:", Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
            ]));
            for (key, value) in &item.properties {
                lines.push(Line::from(vec![
                    Span::styled(format!("  {}: ", key), Style::default().fg(theme.muted)),
                    Span::styled(value.clone(), Style::default().fg(theme.text)),
                ]));
            }
        }
        
        Paragraph::new(lines)
            .block(Block::default().borders(Borders::ALL).title("Equipment Details"))
            .alignment(Alignment::Left)
    } else {
        Paragraph::new("Select an item to view details")
            .block(Block::default().borders(Borders::ALL).title("Details"))
            .alignment(Alignment::Center)
    }
}

/// Render preview panel
fn render_preview<'a>(
    state: &'a PendingManagerState,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    if !state.show_preview {
        return Paragraph::new("Press 'p' to preview changes")
            .block(Block::default().borders(Borders::ALL).title("Preview"))
            .alignment(Alignment::Center);
    }
    
    let items_to_confirm: Vec<&PendingEquipment> = if state.selected_ids.is_empty() {
        if let Some(item) = state.selected_item() {
            vec![item]
        } else {
            Vec::new()
        }
    } else {
        state.pending_items.iter()
            .filter(|item| state.selected_ids.contains(&item.id))
            .collect()
    };
    
    if items_to_confirm.is_empty() {
        return Paragraph::new("No items selected for confirmation")
            .block(Block::default().borders(Borders::ALL).title("Preview"))
            .alignment(Alignment::Center);
    }
    
    let mut lines = vec![
        Line::from(vec![
            Span::styled("Preview: Confirming Equipment", Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled(format!("Items to confirm: {}", items_to_confirm.len()), Style::default().fg(theme.text)),
        ]),
        Line::from(Span::raw("")),
    ];
    
    for item in items_to_confirm.iter().take(10) {
        lines.push(Line::from(vec![
            Span::styled("  • ", Style::default().fg(theme.accent)),
            Span::styled(item.name.clone(), Style::default().fg(theme.text)),
            Span::styled(" (", Style::default().fg(theme.muted)),
            Span::styled(item.equipment_type.clone(), Style::default().fg(theme.muted)),
            Span::styled(")", Style::default().fg(theme.muted)),
        ]));
        lines.push(Line::from(vec![
            Span::styled("    Floor: ", Style::default().fg(theme.muted)),
            Span::styled(item.floor_level.to_string(), Style::default().fg(theme.text)),
            Span::styled(" | Position: (", Style::default().fg(theme.muted)),
            Span::styled(format!("{:.1}, {:.1}, {:.1}", item.position.x, item.position.y, item.position.z), Style::default().fg(theme.text)),
            Span::styled(")", Style::default().fg(theme.muted)),
        ]));
    }
    
    if items_to_confirm.len() > 10 {
        lines.push(Line::from(vec![
            Span::styled(format!("  ... and {} more", items_to_confirm.len() - 10), Style::default().fg(theme.muted)),
        ]));
    }
    
    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Preview Changes"))
        .alignment(Alignment::Left)
}

/// Render footer
fn render_footer<'a>(
    theme: &'a Theme,
    selected_count: usize,
) -> Paragraph<'a> {
    let help_text = if selected_count > 0 {
        format!("↑/↓: Navigate | Space: Select | y: Confirm {} | n: Reject {} | p: Preview | a: Select All | c: Clear | q: Quit", selected_count, selected_count)
    } else {
        "↑/↓: Navigate | Space: Select | y: Confirm | n: Reject | p: Preview | a: Select All | q: Quit".to_string()
    };
    
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive AR pending equipment manager
pub fn handle_ar_pending_manager(building_name: String) -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();
    
    let mut state = PendingManagerState::new(building_name)?;
    let mut list_state = ListState::default();
    
    loop {
        terminal.terminal().draw(|frame| {
            let chunks = Layout::default()
                .direction(ratatui::layout::Direction::Vertical)
                .constraints([
                    Constraint::Length(3),
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
                    Constraint::Percentage(40),
                    Constraint::Percentage(60),
                ])
                .split(chunks[1])
                .to_vec();
            
            // Left: Pending list
            let pending_list = render_pending_list(&state, content_chunks[0], &theme);
            list_state.select(Some(state.selected_index));
            frame.render_stateful_widget(pending_list, content_chunks[0], &mut list_state);
            
            // Right: Details or preview
            if state.show_preview {
                let preview = render_preview(&state, content_chunks[1], &theme);
                frame.render_widget(preview, content_chunks[1]);
            } else {
                let details = render_item_details(&state, content_chunks[1], &theme);
                frame.render_widget(details, content_chunks[1]);
            }
            
            // Footer
            let footer = render_footer(&theme, state.selected_ids.len());
            frame.render_widget(footer, chunks[2]);
        })?;
        
        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) => {
                    if key_event.code == KeyCode::Char('q') || key_event.code == KeyCode::Esc {
                        break;
                    } else if key_event.code == KeyCode::Down || key_event.code == KeyCode::Char('j') {
                        state.next();
                    } else if key_event.code == KeyCode::Up || key_event.code == KeyCode::Char('k') {
                        state.previous();
                    } else if key_event.code == KeyCode::Char(' ') {
                        state.toggle_selection();
                    } else if key_event.code == KeyCode::Char('a') || key_event.code == KeyCode::Char('A') {
                        state.select_all();
                    } else if key_event.code == KeyCode::Char('c') || key_event.code == KeyCode::Char('C') {
                        state.clear_selection();
                    } else if key_event.code == KeyCode::Char('y') || key_event.code == KeyCode::Char('Y') {
                        // Confirm selected items
                        match state.confirm_selected() {
                            Ok(equipment_ids) => {
                                if !equipment_ids.is_empty() {
                                    // Show success message briefly
                                    // Could add a message overlay here
                                }
                            }
                            Err(e) => {
                                eprintln!("Error confirming: {}", e);
                            }
                        }
                    } else if key_event.code == KeyCode::Char('n') || key_event.code == KeyCode::Char('N') {
                        // Reject selected items
                        if let Err(e) = state.reject_selected() {
                            eprintln!("Error rejecting: {}", e);
                        }
                    } else if key_event.code == KeyCode::Char('p') || key_event.code == KeyCode::Char('P') {
                        // Toggle preview
                        state.show_preview = !state.show_preview;
                    } else if key_event.code == KeyCode::Char('r') || key_event.code == KeyCode::Char('R') {
                        // Refresh
                        state.refresh()?;
                    }
                }
                _ => {}
            }
        }
    }
    
    Ok(())
}

