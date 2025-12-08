//! Interactive fuzzy search browser for ArxOS TUI
//!
//! Provides fast, keyboard-driven search across all building entities:
//! - Rooms (name, type, tags)
//! - Equipment (name, type, location)
//! - Floors and Buildings
//! - Git commit messages (optional)

use crate::core::{Equipment, Room};
use crate::yaml::BuildingData;
use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
    Frame,
};
use std::collections::VecDeque;

#[cfg(feature = "tui")]
use fuzzy_matcher::FuzzyMatcher;
#[cfg(feature = "tui")]
use fuzzy_matcher::skim::SkimMatcherV2;

/// Types of searchable entities
#[derive(Debug, Clone, PartialEq)]
pub enum SearchResultType {
    Room,
    Equipment,
    Floor,
    Building,
    Tag,
}

/// A single search result with metadata
#[derive(Debug, Clone)]
pub struct SearchResult {
    pub result_type: SearchResultType,
    pub title: String,
    pub subtitle: String,
    pub id: String,
    pub score: i64,
    /// Character indices that matched the query (for highlighting)
    pub match_indices: Vec<usize>,
}

impl SearchResult {
    pub fn icon(&self) -> &'static str {
        match self.result_type {
            SearchResultType::Room => "🚪",
            SearchResultType::Equipment => "⚙️ ",
            SearchResultType::Floor => "🏢",
            SearchResultType::Building => "🏠",
            SearchResultType::Tag => "#️⃣ ",
        }
    }
}

/// Search filter options
#[derive(Debug, Clone, PartialEq)]
pub struct SearchFilter {
    pub result_type: Option<SearchResultType>,
    pub floor_level: Option<i32>,
}

/// Interactive search browser state
pub struct SearchBrowser {
    query: String,
    results: Vec<SearchResult>,
    selected: usize,
    list_state: ListState,
    building_data: BuildingData,
    matcher: SkimMatcherV2,
    max_results: usize,
    /// LRU search history (most recent first)
    search_history: VecDeque<String>,
    history_index: Option<usize>,
    /// Active filters
    filter: SearchFilter,
}

impl SearchBrowser {
    pub fn new(building_data: BuildingData) -> Self {
        let mut browser = Self {
            query: String::new(),
            results: Vec::new(),
            selected: 0,
            list_state: ListState::default(),
            building_data,
            matcher: SkimMatcherV2::default(),
            max_results: 50,
            search_history: VecDeque::with_capacity(50),
            history_index: None,
            filter: SearchFilter {
                result_type: None,
                floor_level: None,
            },
        };
        browser.update_results();
        browser
    }

    /// Set filter by result type
    pub fn set_type_filter(&mut self, result_type: Option<SearchResultType>) {
        self.filter.result_type = result_type;
        self.update_results();
    }

    /// Set filter by floor level
    pub fn set_floor_filter(&mut self, floor_level: Option<i32>) {
        self.filter.floor_level = floor_level;
        self.update_results();
    }

    /// Clear all filters
    pub fn clear_filters(&mut self) {
        self.filter = SearchFilter {
            result_type: None,
            floor_level: None,
        };
        self.update_results();
    }

    /// Handle keyboard input
    pub fn handle_key(&mut self, key: KeyEvent) -> SearchAction {
        match (key.code, key.modifiers) {
            // Exit
            (KeyCode::Esc, _) | (KeyCode::Char('q'), KeyModifiers::NONE) => SearchAction::Exit,
            
            // Navigation (with history on Up/Down when query is empty)
            (KeyCode::Down, _) | (KeyCode::Char('j'), KeyModifiers::NONE) => {
                if self.query.is_empty() && self.history_index.is_none() {
                    // Start navigating history
                    if !self.search_history.is_empty() {
                        self.history_index = Some(0);
                        self.query = self.search_history[0].clone();
                        self.update_results();
                    }
                } else {
                    self.select_next();
                }
                SearchAction::Continue
            }
            (KeyCode::Up, _) | (KeyCode::Char('k'), KeyModifiers::NONE) => {
                if let Some(idx) = self.history_index {
                    // Navigate through history
                    if idx + 1 < self.search_history.len() {
                        self.history_index = Some(idx + 1);
                        self.query = self.search_history[idx + 1].clone();
                        self.update_results();
                    }
                } else {
                    self.select_previous();
                }
                SearchAction::Continue
            }
            (KeyCode::Char('n'), KeyModifiers::CONTROL) => {
                self.select_next();
                SearchAction::Continue
            }
            (KeyCode::Char('p'), KeyModifiers::CONTROL) => {
                self.select_previous();
                SearchAction::Continue
            }
            
            // Select result
            (KeyCode::Enter, _) => {
                let query = self.query.clone();
                let selected_idx = self.selected;
                
                if let Some(result) = self.results.get(selected_idx).cloned() {
                    // Add to search history
                    if !query.is_empty() {
                        self.add_to_history(query);
                    }
                    SearchAction::Select(result)
                } else {
                    SearchAction::Continue
                }
            }
            
            // Query editing
            (KeyCode::Backspace, _) => {
                self.query.pop();
                self.history_index = None; // Exit history mode
                self.update_results();
                SearchAction::Continue
            }
            (KeyCode::Char(c), KeyModifiers::NONE) | (KeyCode::Char(c), KeyModifiers::SHIFT) => {
                self.query.push(c);
                self.history_index = None; // Exit history mode
                self.update_results();
                SearchAction::Continue
            }
            
            // Clear query
            (KeyCode::Char('u'), KeyModifiers::CONTROL) => {
                self.query.clear();
                self.history_index = None;
                self.update_results();
                SearchAction::Continue
            }
            
            // Filter toggles
            (KeyCode::Char('r'), KeyModifiers::CONTROL) => {
                // Toggle room filter
                self.filter.result_type = if self.filter.result_type == Some(SearchResultType::Room) {
                    None
                } else {
                    Some(SearchResultType::Room)
                };
                self.update_results();
                SearchAction::Continue
            }
            (KeyCode::Char('e'), KeyModifiers::CONTROL) => {
                // Toggle equipment filter
                self.filter.result_type = if self.filter.result_type == Some(SearchResultType::Equipment) {
                    None
                } else {
                    Some(SearchResultType::Equipment)
                };
                self.update_results();
                SearchAction::Continue
            }
            (KeyCode::Char('f'), KeyModifiers::CONTROL) => {
                // Toggle floor filter
                self.filter.result_type = if self.filter.result_type == Some(SearchResultType::Floor) {
                    None
                } else {
                    Some(SearchResultType::Floor)
                };
                self.update_results();
                SearchAction::Continue
            }
            (KeyCode::Char('x'), KeyModifiers::CONTROL) => {
                // Clear all filters
                self.clear_filters();
                SearchAction::Continue
            }
            
            _ => SearchAction::Continue,
        }
    }

    /// Add query to search history (LRU)
    fn add_to_history(&mut self, query: String) {
        // Remove if already exists
        self.search_history.retain(|q| q != &query);
        // Add to front
        self.search_history.push_front(query);
        // Limit size
        if self.search_history.len() > 50 {
            self.search_history.pop_back();
        }
    }

    /// Update search results based on current query
    fn update_results(&mut self) {
        self.results.clear();
        self.selected = 0;
        self.list_state.select(Some(0));

        if self.query.is_empty() {
            // Show recent/all items when no query
            self.add_all_items();
            return;
        }

        // Search rooms (nested in wings)
        for floor in &self.building_data.building.floors {
            // Apply floor filter
            if let Some(filter_level) = self.filter.floor_level {
                if floor.level != filter_level {
                    continue;
                }
            }
            
            for wing in &floor.wings {
                for room in &wing.rooms {
                    if let Some((score, indices)) = self.match_room_with_indices(room) {
                        // Apply type filter
                        if let Some(ref filter_type) = self.filter.result_type {
                            if filter_type != &SearchResultType::Room {
                                continue;
                            }
                        }
                        
                        self.results.push(SearchResult {
                            result_type: SearchResultType::Room,
                            title: room.name.clone(),
                            subtitle: format!("Floor {}, {}", floor.level, wing.name),
                            id: room.id.clone(),
                            score,
                            match_indices: indices,
                        });
                    }
                }
            }
        }

        // Search equipment (floor-level and room-level)
        for floor in &self.building_data.building.floors {
            // Apply floor filter
            if let Some(filter_level) = self.filter.floor_level {
                if floor.level != filter_level {
                    continue;
                }
            }
            
            for equip in &floor.equipment {
                if let Some((score, indices)) = self.match_equipment_with_indices(equip) {
                    // Apply type filter
                    if let Some(ref filter_type) = self.filter.result_type {
                        if filter_type != &SearchResultType::Equipment {
                            continue;
                        }
                    }
                    
                    let location = format!("Floor {}", floor.level);
                    self.results.push(SearchResult {
                        result_type: SearchResultType::Equipment,
                        title: equip.name.clone(),
                        subtitle: format!("{:?} - {}", equip.equipment_type, location),
                        id: equip.id.clone(),
                        score,
                        match_indices: indices,
                    });
                }
            }
        }

        // Search floors
        for floor in &self.building_data.building.floors {
            // Apply type filter
            if let Some(ref filter_type) = self.filter.result_type {
                if filter_type != &SearchResultType::Floor {
                    continue;
                }
            }
            
            // Apply floor filter
            if let Some(filter_level) = self.filter.floor_level {
                if floor.level != filter_level {
                    continue;
                }
            }
            
            let floor_text = format!("Floor {}", floor.level);
            if let Some((score, indices)) = self.matcher.fuzzy_indices(&floor_text, &self.query) {
                let room_count: usize = floor.wings.iter().map(|w| w.rooms.len()).sum();
                self.results.push(SearchResult {
                    result_type: SearchResultType::Floor,
                    title: floor_text,
                    subtitle: format!("{} rooms", room_count),
                    id: floor.id.clone(),
                    score,
                    match_indices: indices,
                });
            }
        }

        // Search building
        // Apply type filter
        if self.filter.result_type.is_none() || self.filter.result_type == Some(SearchResultType::Building) {
            if let Some((score, indices)) = self.matcher.fuzzy_indices(&self.building_data.building.name, &self.query) {
                self.results.push(SearchResult {
                    result_type: SearchResultType::Building,
                    title: self.building_data.building.name.clone(),
                    subtitle: format!("{} floors", self.building_data.building.floors.len()),
                    id: "building".to_string(),
                    score,
                    match_indices: indices,
                });
            }
        }

        // Sort by score descending
        self.results.sort_by(|a, b| b.score.cmp(&a.score));
        self.results.truncate(self.max_results);
    }

    fn match_room_with_indices(&self, room: &Room) -> Option<(i64, Vec<usize>)> {
        let searchable = format!("{} {:?}", room.name, room.room_type);
        self.matcher.fuzzy_indices(&searchable, &self.query)
    }

    fn match_equipment_with_indices(&self, equipment: &Equipment) -> Option<(i64, Vec<usize>)> {
        let searchable = format!("{} {:?}", equipment.name, equipment.equipment_type);
        self.matcher.fuzzy_indices(&searchable, &self.query)
    }

    fn add_all_items(&mut self) {
        // Show all rooms
        for floor in &self.building_data.building.floors {
            for wing in &floor.wings {
                for room in &wing.rooms {
                    self.results.push(SearchResult {
                        result_type: SearchResultType::Room,
                        title: room.name.clone(),
                        subtitle: format!("Floor {}, {}", floor.level, wing.name),
                        id: room.id.clone(),
                        score: 0,
                        match_indices: Vec::new(),
                    });
                }
            }
        }

        // Show all equipment
        for floor in &self.building_data.building.floors {
            for equip in &floor.equipment {
                self.results.push(SearchResult {
                    result_type: SearchResultType::Equipment,
                    title: equip.name.clone(),
                    subtitle: format!("{:?} - Floor {}", equip.equipment_type, floor.level),
                    id: equip.id.clone(),
                    score: 0,
                    match_indices: Vec::new(),
                });
            }
        }

        self.results.truncate(self.max_results);
    }

    fn select_next(&mut self) {
        if self.results.is_empty() {
            return;
        }
        self.selected = (self.selected + 1).min(self.results.len() - 1);
        self.list_state.select(Some(self.selected));
    }

    fn select_previous(&mut self) {
        if self.selected > 0 {
            self.selected -= 1;
            self.list_state.select(Some(self.selected));
        }
    }

    /// Render the search browser UI
    pub fn render(&mut self, frame: &mut Frame, area: Rect) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(3), // Search input
                Constraint::Min(1),     // Results list
                Constraint::Length(4),  // Help + filters
            ])
            .split(area);

        // Search input box with filter status
        let mut title = "🔍 Search".to_string();
        if let Some(ref filter_type) = self.filter.result_type {
            title.push_str(&format!(" [Filter: {:?}]", filter_type));
        }
        if let Some(floor) = self.filter.floor_level {
            title.push_str(&format!(" [Floor: {}]", floor));
        }
        
        let input = Paragraph::new(self.query.as_str())
            .style(Style::default().fg(Color::Yellow))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title(title)
                    .border_style(Style::default().fg(Color::Cyan)),
            );
        frame.render_widget(input, chunks[0]);

        // Results list with syntax highlighting
        let items: Vec<ListItem> = self
            .results
            .iter()
            .enumerate()
            .map(|(idx, result)| {
                let is_selected = idx == self.selected;
                let base_style = if is_selected {
                    Style::default()
                        .fg(Color::Black)
                        .bg(Color::Cyan)
                        .add_modifier(Modifier::BOLD)
                } else {
                    Style::default().fg(Color::White)
                };

                // Build title with syntax highlighting for matched characters
                let mut title_spans = Vec::new();
                if !result.match_indices.is_empty() && !self.query.is_empty() {
                    let title_chars: Vec<char> = result.title.chars().collect();
                    for (i, ch) in title_chars.iter().enumerate() {
                        if result.match_indices.contains(&i) {
                            // Highlight matched character
                            let highlight_style = if is_selected {
                                Style::default()
                                    .fg(Color::Yellow)
                                    .bg(Color::Cyan)
                                    .add_modifier(Modifier::BOLD | Modifier::UNDERLINED)
                            } else {
                                Style::default()
                                    .fg(Color::Yellow)
                                    .add_modifier(Modifier::BOLD)
                            };
                            title_spans.push(Span::styled(ch.to_string(), highlight_style));
                        } else {
                            title_spans.push(Span::styled(ch.to_string(), base_style));
                        }
                    }
                } else {
                    title_spans.push(Span::styled(&result.title, base_style));
                }

                let content = vec![Line::from({
                    let mut spans = vec![
                        Span::raw(if is_selected { "▸ " } else { "  " }),
                        Span::raw(result.icon()),
                        Span::raw(" "),
                    ];
                    spans.extend(title_spans);
                    spans.push(Span::raw("  "));
                    spans.push(Span::styled(
                        &result.subtitle,
                        Style::default().fg(Color::DarkGray),
                    ));
                    spans
                })];

                ListItem::new(content)
            })
            .collect();

        let results_list = List::new(items)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title(format!("Results ({}/{})", self.results.len(), self.max_results))
                    .border_style(Style::default().fg(Color::White)),
            )
            .highlight_style(
                Style::default()
                    .fg(Color::Black)
                    .bg(Color::Cyan)
                    .add_modifier(Modifier::BOLD),
            );

        frame.render_stateful_widget(results_list, chunks[1], &mut self.list_state);

        // Help text with filter shortcuts
        let help_text = vec![
            Line::from("↑↓ Navigate │ Enter: Select │ Esc: Cancel │ Ctrl+U: Clear"),
            Line::from("Ctrl+R: Rooms │ Ctrl+E: Equipment │ Ctrl+F: Floors │ Ctrl+X: Clear Filters"),
        ];
        let help = Paragraph::new(help_text)
            .style(Style::default().fg(Color::DarkGray))
            .block(Block::default().borders(Borders::ALL).title("Help"));
        frame.render_widget(help, chunks[2]);
    }
}

/// Actions returned by search browser
#[derive(Debug)]
pub enum SearchAction {
    Continue,
    Select(SearchResult),
    Exit,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_search_result_type() {
        let result = SearchResult {
            result_type: SearchResultType::Room,
            title: "Test Room".to_string(),
            subtitle: "Floor 1".to_string(),
            id: "room1".to_string(),
            score: 100,
            match_indices: vec![0, 5],
        };
        
        assert_eq!(result.icon(), "🚪");
        assert_eq!(result.result_type, SearchResultType::Room);
    }

    #[test]
    fn test_equipment_icon() {
        let result = SearchResult {
            result_type: SearchResultType::Equipment,
            title: "AHU-01".to_string(),
            subtitle: "HVAC".to_string(),
            id: "eq1".to_string(),
            score: 90,
            match_indices: Vec::new(),
        };
        
        assert_eq!(result.icon(), "⚙️ ");
    }
}
