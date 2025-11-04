//! Interactive Room Explorer for ArxOS TUI
//!
//! Provides a tree view for exploring building structure:
//! - Building → Floors → Wings → Rooms hierarchy
//! - Expand/collapse navigation
//! - Equipment counts per room
//! - Visual room type indicators
//! - Quick filters

use crate::ui::{TerminalManager, Theme};
use crate::ui::layouts::list_detail_layout;
use crate::utils::loading;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
};
use std::time::Duration;
use std::collections::HashMap;

/// Tree node representing a building structure element
#[derive(Debug, Clone)]
enum TreeNode {
    Building {
        name: String,
        floors: Vec<TreeNode>,
    },
    Floor {
        level: i32,
        name: String,
        rooms: Vec<RoomNode>,
        equipment_count: usize,
    },
    Room {
        id: String,
        name: String,
        room_type: String,
        floor: i32,
        equipment_count: usize,
        area: Option<f64>,
        volume: Option<f64>,
    },
}

/// Room node for tree structure
#[derive(Debug, Clone)]
struct RoomNode {
    id: String,
    name: String,
    room_type: String,
    equipment_count: usize,
    area: Option<f64>,
    volume: Option<f64>,
}

/// Explorer state
struct ExplorerState {
    tree: Vec<TreeNode>,
    expanded: std::collections::HashSet<String>,
    selected_path: Vec<usize>,
    filter: String,
    show_details: bool,
}

impl ExplorerState {
    fn new(tree: Vec<TreeNode>) -> Self {
        Self {
            tree,
            expanded: std::collections::HashSet::new(),
            selected_path: vec![0],
            filter: String::new(),
            show_details: true,
        }
    }
    
    fn get_selected_node(&self) -> Option<TreeNode> {
        let mut current = &self.tree;
        for &idx in &self.selected_path[..self.selected_path.len().saturating_sub(1)] {
            if let Some(TreeNode::Building { floors, .. }) = current.get(idx) {
                current = floors;
            } else {
                return None;
            }
        }
        current.get(*self.selected_path.last()?).cloned()
    }
    
    fn is_expanded(&self, path: &[usize]) -> bool {
        let key = path.iter().map(|i| i.to_string()).collect::<Vec<_>>().join("/");
        self.expanded.contains(&key)
    }
    
    fn toggle_expand(&mut self, path: &[usize]) {
        let key = path.iter().map(|i| i.to_string()).collect::<Vec<_>>().join("/");
        if self.expanded.contains(&key) {
            self.expanded.remove(&key);
        } else {
            self.expanded.insert(key);
        }
    }
    
    fn next(&mut self) {
        // Navigate to next visible item
        if let Some(flat_items) = self.get_flat_items() {
            if !flat_items.is_empty() {
                let current_idx = self.get_current_flat_index();
                let next_idx = (current_idx + 1) % flat_items.len();
                self.selected_path = flat_items[next_idx].path.clone();
            }
        }
    }
    
    fn previous(&mut self) {
        // Navigate to previous visible item
        if let Some(flat_items) = self.get_flat_items() {
            if !flat_items.is_empty() {
                let current_idx = self.get_current_flat_index();
                let prev_idx = if current_idx == 0 {
                    flat_items.len() - 1
                } else {
                    current_idx - 1
                };
                self.selected_path = flat_items[prev_idx].path.clone();
            }
        }
    }
    
    fn get_flat_items(&self) -> Option<Vec<FlatItem>> {
        let mut items = Vec::new();
        self.build_flat_list(&self.tree, &[], &mut items);
        Some(items)
    }
    
    fn build_flat_list(&self, nodes: &[TreeNode], path: &[usize], items: &mut Vec<FlatItem>) {
        for (idx, node) in nodes.iter().enumerate() {
            let current_path = [path, &[idx]].concat();
            let depth = current_path.len();
            
            match node {
                TreeNode::Building { name, floors } => {
                    items.push(FlatItem {
                        path: current_path.clone(),
                        depth,
                        label: name.clone(),
                        node_type: "building",
                        equipment_count: None,
                        room_type: None,
                    });
                    
                    if self.is_expanded(&current_path) {
                        self.build_flat_list(floors, &current_path, items);
                    }
                }
                TreeNode::Floor { level, name, rooms, equipment_count } => {
                    items.push(FlatItem {
                        path: current_path.clone(),
                        depth,
                        label: format!("Floor {}: {}", level, name),
                        node_type: "floor",
                        equipment_count: Some(*equipment_count),
                        room_type: None,
                    });
                    
                    if self.is_expanded(&current_path) {
                        for (room_idx, room) in rooms.iter().enumerate() {
                            let room_path = [&current_path[..], &[room_idx]].concat();
                            items.push(FlatItem {
                                path: room_path,
                                depth: depth + 1,
                                label: room.name.clone(),
                                node_type: "room",
                                equipment_count: Some(room.equipment_count),
                                room_type: Some(room.room_type.clone()),
                            });
                        }
                    }
                }
                TreeNode::Room { name, room_type, equipment_count, .. } => {
                    items.push(FlatItem {
                        path: current_path.clone(),
                        depth,
                        label: name.clone(),
                        node_type: "room",
                        equipment_count: Some(*equipment_count),
                        room_type: Some(room_type.clone()),
                    });
                }
            }
        }
    }
    
    fn get_current_flat_index(&self) -> usize {
        if let Some(flat_items) = self.get_flat_items() {
            flat_items.iter()
                .position(|item| item.path == self.selected_path)
                .unwrap_or(0)
        } else {
            0
        }
    }
}

/// Flat item for rendering
struct FlatItem {
    path: Vec<usize>,
    depth: usize,
    label: String,
    node_type: &'static str,
    equipment_count: Option<usize>,
    room_type: Option<String>,
}

/// Build tree structure from building data
fn build_room_tree(building_name: &str) -> Result<Vec<TreeNode>, Box<dyn std::error::Error>> {
    let building_data = loading::load_building_data(building_name)?;
    let mut trees = Vec::new();
    
    let mut floor_map: HashMap<i32, Vec<RoomNode>> = HashMap::new();
    
    // Collect all rooms by floor
    for floor in &building_data.floors {
        let mut rooms = Vec::new();
        for room in &floor.rooms {
            let equipment_count = room.equipment.len();
            rooms.push(RoomNode {
                id: room.id.clone(),
                name: room.name.clone(),
                room_type: room.room_type.clone(),
                equipment_count,
                area: room.area,
                volume: room.volume,
            });
        }
        
        let total_equipment = floor.equipment.len();
        floor_map.insert(floor.level, rooms);
        
        trees.push(TreeNode::Floor {
            level: floor.level,
            name: floor.name.clone(),
            rooms: floor_map.remove(&floor.level).unwrap_or_default(),
            equipment_count: total_equipment,
        });
    }
    
    // Sort floors by level
    trees.sort_by(|a, b| {
        match (a, b) {
            (TreeNode::Floor { level: a_level, .. }, TreeNode::Floor { level: b_level, .. }) => {
                a_level.cmp(b_level)
            }
            _ => std::cmp::Ordering::Equal,
        }
    });
    
    // Wrap in building node
    Ok(vec![TreeNode::Building {
        name: building_data.building.name.clone(),
        floors: trees,
    }])
}

/// Render tree view
fn render_tree_view<'a>(
    state: &'a ExplorerState,
    area: Rect,
    theme: &'a Theme,
) -> List<'a> {
    let items: Vec<ListItem> = state.get_flat_items()
        .unwrap_or_default()
        .iter()
        .enumerate()
        .map(|(display_idx, item)| {
            let is_selected = item.path == state.selected_path;
            let prefix = if is_selected { ">" } else { " " };
            
            // Indentation based on depth
            let indent = "  ".repeat(item.depth);
            
            // Icon based on node type
            let icon = match item.node_type {
                "building" => "🏢",
                "floor" => "🏗️",
                "room" => "🚪",
                _ => "  ",
            };
            
            let mut line_parts = vec![
                Span::styled(prefix, Style::default().fg(theme.accent)),
                Span::styled(" ", Style::default()),
                Span::styled(format!("{} {} ", icon, indent), Style::default().fg(theme.muted)),
            ];
            
            // Room type indicator
            if let Some(ref room_type) = item.room_type {
                let type_color = match room_type.to_lowercase().as_str() {
                    "classroom" | "office" => Color::Cyan,
                    "laboratory" | "lab" => Color::Magenta,
                    "bathroom" | "restroom" => Color::Blue,
                    "kitchen" | "cafeteria" => Color::Yellow,
                    _ => theme.text,
                };
                line_parts.push(Span::styled(
                    format!("[{}] ", room_type),
                    Style::default().fg(type_color),
                ));
            }
            
            line_parts.push(Span::styled(
                item.label.clone(),
                Style::default()
                    .fg(theme.text)
                    .add_modifier(if is_selected { Modifier::BOLD | Modifier::REVERSED } else { Modifier::empty() }),
            ));
            
            // Equipment count
            if let Some(count) = item.equipment_count {
                if count > 0 {
                    line_parts.push(Span::styled(
                        format!(" ({} equipment)", count),
                        Style::default().fg(theme.muted),
                    ));
                }
            }
            
            ListItem::new(Line::from(line_parts))
        })
        .collect();
    
    let title = if state.filter.is_empty() {
        "Building Explorer".to_string()
    } else {
        format!("Building Explorer (filtered)")
    };
    
    List::new(items)
        .block(Block::default().borders(Borders::ALL).title(title))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
}

/// Render room details
fn render_room_details<'a>(
    node: &'a TreeNode,
    area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let lines = match node {
        TreeNode::Building { name, floors } => {
            vec![
                Line::from(vec![
                    Span::styled("Building: ", Style::default().fg(theme.muted)),
                    Span::styled(name, Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
                ]),
                Line::from(vec![
                    Span::styled("Floors: ", Style::default().fg(theme.muted)),
                    Span::styled(floors.len().to_string(), Style::default().fg(theme.text)),
                ]),
            ]
        }
        TreeNode::Floor { level, name, rooms, equipment_count } => {
            vec![
                Line::from(vec![
                    Span::styled("Floor: ", Style::default().fg(theme.muted)),
                    Span::styled(format!("{} - {}", level, name), Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
                ]),
                Line::from(vec![
                    Span::styled("Rooms: ", Style::default().fg(theme.muted)),
                    Span::styled(rooms.len().to_string(), Style::default().fg(theme.text)),
                ]),
                Line::from(vec![
                    Span::styled("Equipment: ", Style::default().fg(theme.muted)),
                    Span::styled(equipment_count.to_string(), Style::default().fg(theme.text)),
                ]),
            ]
        }
        TreeNode::Room { name, room_type, equipment_count, area, volume, .. } => {
            let mut room_lines = vec![
                Line::from(vec![
                    Span::styled("Room: ", Style::default().fg(theme.muted)),
                    Span::styled(name.clone(), Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
                ]),
                Line::from(vec![
                    Span::styled("Type: ", Style::default().fg(theme.muted)),
                    Span::styled(room_type.clone(), Style::default().fg(theme.text)),
                ]),
                Line::from(vec![
                    Span::styled("Equipment: ", Style::default().fg(theme.muted)),
                    Span::styled(equipment_count.to_string(), Style::default().fg(theme.text)),
                ]),
            ];
            
            if let Some(area) = area {
                room_lines.push(Line::from(vec![
                    Span::styled("Area: ", Style::default().fg(theme.muted)),
                    Span::styled(format!("{:.1} m²", area), Style::default().fg(theme.text)),
                ]));
            }
            
            if let Some(volume) = volume {
                room_lines.push(Line::from(vec![
                    Span::styled("Volume: ", Style::default().fg(theme.muted)),
                    Span::styled(format!("{:.1} m³", volume), Style::default().fg(theme.text)),
                ]));
            }
            
            room_lines
        }
    };
    
    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Details"))
        .alignment(Alignment::Left)
}

/// Render footer
fn render_footer<'a>(theme: &'a Theme, filter_mode: bool) -> Paragraph<'a> {
    let help_text = if filter_mode {
        "Type to filter | Enter: Apply | Esc: Cancel | q: Quit"
    } else {
        "→/Space: Expand | ←: Collapse | ↑/↓: Navigate | Enter: Toggle | /: Search | q: Quit"
    };
    
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive room explorer
pub fn handle_room_explorer(building_name: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();
    
    let building = building_name.unwrap_or_else(|| {
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
    
    let tree = build_room_tree(&building)?;
    
    if tree.is_empty() {
        println!("No building data found");
        return Ok(());
    }
    
    let mut state = ExplorerState::new(tree);
    // Expand building node by default
    state.toggle_expand(&[0]);
    
    let mut list_state = ListState::default();
    let mut filter_input = String::new();
    let mut filter_mode = false;
    
    loop {
        terminal.terminal().draw(|frame| {
            let chunks = list_detail_layout(frame.size(), 50);
            
            // Get current index and selected node before rendering
            let current_idx = state.get_current_flat_index();
            let selected_node = state.get_selected_node();
            
            // Left: Tree view
            let tree_list = render_tree_view(&state, chunks[0], &theme);
            list_state.select(Some(current_idx));
            frame.render_stateful_widget(tree_list, chunks[0], &mut list_state);
            
            // Right: Details
            if state.show_details {
                if let Some(node) = &selected_node {
                    let details = render_room_details(node, chunks[1], &theme);
                    frame.render_widget(details, chunks[1]);
                } else {
                    let no_selection = Paragraph::new("No item selected")
                        .block(Block::default().borders(Borders::ALL).title("Details"))
                        .alignment(Alignment::Center);
                    frame.render_widget(no_selection, chunks[1]);
                }
            }
            
            // Footer
            let footer = render_footer(&theme, filter_mode);
            let footer_chunk = Layout::default()
                .direction(ratatui::layout::Direction::Vertical)
                .constraints([Constraint::Min(0), Constraint::Length(3)])
                .split(frame.size())[1];
            frame.render_widget(footer, footer_chunk);
            
            // Filter input overlay
            if filter_mode {
                let filter_text = if filter_input.is_empty() {
                    "Enter filter: _".to_string()
                } else {
                    format!("Filter: {}_", filter_input)
                };
                let filter_paragraph = Paragraph::new(filter_text)
                    .style(Style::default().fg(theme.primary))
                    .block(Block::default().borders(Borders::ALL).title("Search"));
                frame.render_widget(filter_paragraph, chunks[0]);
            }
        })?;
        
        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) if filter_mode => {
                    match key_event.code {
                        KeyCode::Char(c) => {
                            filter_input.push(c);
                        }
                        KeyCode::Backspace => {
                            filter_input.pop();
                        }
                        KeyCode::Enter => {
                            // Apply filter (for now, just clear filter mode)
                            filter_mode = false;
                            filter_input.clear();
                        }
                        KeyCode::Esc => {
                            filter_mode = false;
                            filter_input.clear();
                        }
                        _ => {}
                    }
                }
                Event::Key(key_event) => {
                    if key_event.code == KeyCode::Char('q') || key_event.code == KeyCode::Esc {
                        break;
                    } else if key_event.code == KeyCode::Down || key_event.code == KeyCode::Char('j') {
                        state.next();
                    } else if key_event.code == KeyCode::Up || key_event.code == KeyCode::Char('k') {
                        state.previous();
                    } else if key_event.code == KeyCode::Char('/') {
                        filter_mode = true;
                        filter_input.clear();
                    } else if key_event.code == KeyCode::Char(' ') || key_event.code == KeyCode::Right {
                        // Expand/collapse
                        let path_to_toggle = state.selected_path.clone();
                        state.toggle_expand(&path_to_toggle);
                    } else if key_event.code == KeyCode::Left {
                        // Collapse
                        let path_to_toggle = state.selected_path.clone();
                        if state.is_expanded(&path_to_toggle) {
                            state.toggle_expand(&path_to_toggle);
                        }
                    } else if key_event.code == KeyCode::Enter {
                        state.show_details = !state.show_details;
                    }
                }
                _ => {}
            }
        }
    }
    
    Ok(())
}

