//! Interactive Search Browser for ArxOS TUI
//!
//! Provides an interactive search interface with:
//! - Real-time search results
//! - Preview pane for selected results
//! - Filter by type (equipment/room/building)
//! - Navigate to related items
//! - Search history

use crate::ui::{TerminalManager, Theme};
use crate::ui::layouts::list_detail_layout;
use crate::utils::loading;
use crate::search::{SearchEngine, SearchConfig, SearchResult};
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
};
use std::time::Duration;

/// Search result item for display
#[derive(Debug, Clone)]
struct SearchResultItem {
    id: String,
    name: String,
    result_type: String,
    description: String,
    room: Option<String>,
    floor: Option<i32>,
    status: Option<String>,
}

/// Browser state
struct SearchBrowserState {
    query: String,
    results: Vec<SearchResultItem>,
    filtered_results: Vec<usize>,
    selected: usize,
    filter_type: Option<String>,
    show_details: bool,
}

impl SearchBrowserState {
    fn new() -> Self {
        Self {
            query: String::new(),
            results: Vec::new(),
            filtered_results: Vec::new(),
            selected: 0,
            filter_type: None,
            show_details: true,
        }
    }
    
    fn perform_search(&mut self, query: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.query = query.to_string();
        
        let building_data = loading::load_building_data("")?;
        let search_engine = SearchEngine::new(&building_data);
        
        let config = SearchConfig {
            query: query.to_string(),
            search_equipment: true,
            search_rooms: true,
            search_buildings: true,
            case_sensitive: false,
            use_regex: false,
            limit: 100,
            verbose: false,
        };
        
        let search_results = search_engine.search(&config)?;
        
        let mut items = Vec::new();
        
        for result in search_results {
            let item = match result.item_type.as_str() {
                "equipment" => {
                    // Find equipment details
                    let mut room_name = None;
                    let mut floor_level = None;
                    let mut status = None;
                    
                    for floor in &building_data.floors {
                        for equipment in &floor.equipment {
                            if equipment.name == result.name {
                                room_name = floor.rooms.iter()
                                    .find(|r| r.equipment.contains(&equipment.id))
                                    .map(|r| r.name.clone());
                                floor_level = Some(floor.level);
                                status = Some(format!("{:?}", equipment.status));
                                break;
                            }
                        }
                    }
                    
                    SearchResultItem {
                        id: result.path.clone(),
                        name: result.name.clone(),
                        result_type: "Equipment".to_string(),
                        description: format!("Type: {}", result.equipment_type.as_ref().map(|s| s.as_str()).unwrap_or("Unknown")),
                        room: room_name,
                        floor: floor_level,
                        status,
                    }
                }
                "room" => {
                    let mut floor_level = None;
                    for floor in &building_data.floors {
                        if let Some(room) = floor.rooms.iter().find(|r| r.name == result.name) {
                            floor_level = Some(floor.level);
                            break;
                        }
                    }
                    
                    SearchResultItem {
                        id: result.path.clone(),
                        name: result.name.clone(),
                        result_type: "Room".to_string(),
                        description: format!("Room type from building data"),
                        room: None,
                        floor: floor_level,
                        status: None,
                    }
                }
                _ => {
                    SearchResultItem {
                        id: result.path.clone(),
                        name: result.name.clone(),
                        result_type: result.item_type.clone(),
                        description: result.description.clone().unwrap_or_default(),
                        room: result.room.clone(),
                        floor: result.floor,
                        status: result.status.clone(),
                    }
                }
            };
            
            items.push(item);
        }
        
        self.results = items;
        self.apply_type_filter();
        
        Ok(())
    }
    
    fn apply_type_filter(&mut self) {
        if let Some(ref filter_type) = self.filter_type {
            self.filtered_results = self.results
                .iter()
                .enumerate()
                .filter(|(_, item)| item.result_type.to_lowercase() == filter_type.to_lowercase())
                .map(|(idx, _)| idx)
                .collect();
        } else {
            self.filtered_results = (0..self.results.len()).collect();
        }
        
        if self.selected >= self.filtered_results.len() && !self.filtered_results.is_empty() {
            self.selected = self.filtered_results.len() - 1;
        } else if self.filtered_results.is_empty() {
            self.selected = 0;
        }
    }
    
    fn selected_item(&self) -> Option<&SearchResultItem> {
        self.filtered_results.get(self.selected).map(|&idx| &self.results[idx])
    }
    
    fn next(&mut self) {
        if !self.filtered_results.is_empty() {
            self.selected = (self.selected + 1) % self.filtered_results.len();
        }
    }
    
    fn previous(&mut self) {
        if !self.filtered_results.is_empty() {
            self.selected = if self.selected == 0 {
                self.filtered_results.len() - 1
            } else {
                self.selected - 1
            };
        }
    }
    
    fn set_filter_type(&mut self, filter_type: Option<String>) {
        self.filter_type = filter_type;
        self.apply_type_filter();
    }
}

/// Render search results list
fn render_results_list<'a>(
    state: &'a SearchBrowserState,
    area: Rect,
    theme: &'a Theme,
) -> List<'a> {
    let items: Vec<ListItem> = state.filtered_results
        .iter()
        .enumerate()
        .map(|(display_idx, &result_idx)| {
            let item = &state.results[result_idx];
            let is_selected = display_idx == state.selected;
            
            let prefix = if is_selected { ">" } else { " " };
            
            let type_color = match item.result_type.as_str() {
                "Equipment" => theme.primary,
                "Room" => theme.secondary,
                _ => theme.text,
            };
            
            let mut line_parts = vec![
                Span::styled(prefix, Style::default().fg(theme.accent)),
                Span::styled(
                    format!("{} ", item.result_type),
                    Style::default().fg(type_color).add_modifier(Modifier::BOLD),
                ),
                Span::styled(
                    item.name.clone(),
                    Style::default()
                        .fg(theme.text)
                        .add_modifier(if is_selected { Modifier::BOLD | Modifier::REVERSED } else { Modifier::empty() }),
                ),
            ];
            
            if let Some(ref room) = item.room {
                line_parts.push(Span::styled(
                    format!(" | Room: {}", room),
                    Style::default().fg(theme.muted),
                ));
            }
            
            ListItem::new(Line::from(line_parts))
        })
        .collect();
    
    let title = if state.query.is_empty() {
        "Search Results (0)".to_string()
    } else {
        format!("Search: '{}' ({})", state.query, state.filtered_results.len())
    };
    
    List::new(items)
        .block(Block::default().borders(Borders::ALL).title(title))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
}

/// Render result details
fn render_result_details<'a>(
    item: &'a SearchResultItem,
    area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let mut lines = vec![
        Line::from(vec![
            Span::styled("Name: ", Style::default().fg(theme.muted)),
            Span::styled(&item.name, Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Type: ", Style::default().fg(theme.muted)),
            Span::styled(&item.result_type, Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("ID: ", Style::default().fg(theme.muted)),
            Span::styled(&item.id, Style::default().fg(theme.text)),
        ]),
    ];
    
    if !item.description.is_empty() {
        lines.push(Line::from(vec![
            Span::styled("Description: ", Style::default().fg(theme.muted)),
            Span::styled(&item.description, Style::default().fg(theme.text)),
        ]));
    }
    
    if let Some(ref room) = item.room {
        lines.push(Line::from(vec![
            Span::styled("Room: ", Style::default().fg(theme.muted)),
            Span::styled(room, Style::default().fg(theme.text)),
        ]));
    }
    
    if let Some(floor) = item.floor {
        lines.push(Line::from(vec![
            Span::styled("Floor: ", Style::default().fg(theme.muted)),
            Span::styled(floor.to_string(), Style::default().fg(theme.text)),
        ]));
    }
    
    if let Some(ref status) = item.status {
        lines.push(Line::from(vec![
            Span::styled("Status: ", Style::default().fg(theme.muted)),
            Span::styled(status, Style::default().fg(theme.text)),
        ]));
    }
    
    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Result Details"))
        .alignment(Alignment::Left)
}

/// Render footer
fn render_footer<'a>(theme: &'a Theme, search_mode: bool) -> Paragraph<'a> {
    let help_text = if search_mode {
        "Type to search | Enter: Search | Esc: Cancel | q: Quit"
    } else {
        "↑/↓: Navigate | /: New Search | e/r/b: Filter Type | Enter: Details | q: Quit"
    };
    
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive search browser
pub fn handle_search_browser(initial_query: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();
    
    let mut state = SearchBrowserState::new();
    let mut list_state = ListState::default();
    let mut search_input = initial_query.unwrap_or_default();
    let mut search_mode = search_input.is_empty();
    
    // Perform initial search if query provided
    if !search_input.is_empty() {
        state.perform_search(&search_input)?;
    }
    
    loop {
        terminal.terminal().draw(|frame| {
            let chunks = list_detail_layout(frame.size(), 50);
            
            let selected_item = state.selected_item().cloned();
            
            // Left: Results list
            let results_list = render_results_list(&state, chunks[0], &theme);
            list_state.select(Some(state.selected));
            frame.render_stateful_widget(results_list, chunks[0], &mut list_state);
            
            // Right: Details
            if state.show_details {
                if let Some(item) = &selected_item {
                    let details = render_result_details(item, chunks[1], &theme);
                    frame.render_widget(details, chunks[1]);
                } else {
                    let no_selection = Paragraph::new("No results or select a result")
                        .block(Block::default().borders(Borders::ALL).title("Details"))
                        .alignment(Alignment::Center);
                    frame.render_widget(no_selection, chunks[1]);
                }
            }
            
            // Footer
            let footer = render_footer(&theme, search_mode);
            let footer_chunk = Layout::default()
                .direction(ratatui::layout::Direction::Vertical)
                .constraints([Constraint::Min(0), Constraint::Length(3)])
                .split(frame.size())[1];
            frame.render_widget(footer, footer_chunk);
            
            // Search input overlay
            if search_mode {
                let search_text = if search_input.is_empty() {
                    "Enter search query: _".to_string()
                } else {
                    format!("Search: {}_", search_input)
                };
                let search_paragraph = Paragraph::new(search_text)
                    .style(Style::default().fg(theme.primary))
                    .block(Block::default().borders(Borders::ALL).title("Search"));
                frame.render_widget(search_paragraph, chunks[0]);
            }
        })?;
        
        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) if search_mode => {
                    match key_event.code {
                        KeyCode::Char(c) => {
                            search_input.push(c);
                        }
                        KeyCode::Backspace => {
                            search_input.pop();
                        }
                        KeyCode::Enter => {
                            if !search_input.is_empty() {
                                state.perform_search(&search_input)?;
                                search_mode = false;
                            }
                        }
                        KeyCode::Esc => {
                            search_mode = false;
                            if state.results.is_empty() {
                                search_input.clear();
                            }
                        }
                        _ => {}
                    }
                }
                Event::Key(key_event) => {
                    if TerminalManager::is_quit_key(&key_event) {
                        break;
                    } else if TerminalManager::is_nav_down(&key_event) {
                        state.next();
                    } else if TerminalManager::is_nav_up(&key_event) {
                        state.previous();
                    } else if key_event.code == KeyCode::Char('/') {
                        search_mode = true;
                        search_input.clear();
                    } else if key_event.code == KeyCode::Char('e') {
                        // Filter: Equipment
                        state.set_filter_type(Some("Equipment".to_string()));
                    } else if key_event.code == KeyCode::Char('r') {
                        // Filter: Rooms
                        state.set_filter_type(Some("Room".to_string()));
                    } else if key_event.code == KeyCode::Char('b') {
                        // Filter: All
                        state.set_filter_type(None);
                    } else if TerminalManager::is_select(&key_event) {
                        state.show_details = !state.show_details;
                    }
                }
                _ => {}
            }
        }
    }
    
    Ok(())
}

