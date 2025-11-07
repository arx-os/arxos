//! Interactive Equipment Browser for ArxOS TUI
//!
//! Provides an interactive table view for browsing equipment with:
//! - Keyboard navigation
//! - Color-coded status indicators
//! - Detail panel on selection
//! - Filtering capabilities

use crate::ui::layouts::list_detail_layout;
use crate::ui::{
    handle_help_event, render_help_overlay, HelpContext, HelpSystem, MouseConfig, StatusColor,
    TerminalManager, Theme,
};
use crate::utils::loading;
use crossterm::event::{Event, KeyCode, KeyModifiers};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
};
use std::time::Duration;

/// Equipment item for display in the browser
#[derive(Debug, Clone)]
struct EquipmentItem {
    id: String,
    name: String,
    equipment_type: String,
    room: String,
    floor: i32,
    status: String, // Status as string for display
    position: crate::spatial::Point3D,
}

/// Browser state
struct BrowserState {
    items: Vec<EquipmentItem>,
    filtered_items: Vec<usize>,
    selected: usize,
    filter: String,
    show_details: bool,
    help_system: HelpSystem,
    // Reserved for future mouse interaction support
    #[allow(dead_code)]
    mouse_config: MouseConfig,
}

impl BrowserState {
    fn new(items: Vec<EquipmentItem>) -> Self {
        let filtered: Vec<usize> = (0..items.len()).collect();
        Self {
            items,
            filtered_items: filtered,
            selected: 0,
            filter: String::new(),
            show_details: true,
            help_system: HelpSystem::new(HelpContext::EquipmentBrowser),
            mouse_config: MouseConfig::default(),
        }
    }

    fn selected_item(&self) -> Option<&EquipmentItem> {
        self.filtered_items
            .get(self.selected)
            .map(|&idx| &self.items[idx])
    }

    fn next(&mut self) {
        if !self.filtered_items.is_empty() {
            self.selected = (self.selected + 1) % self.filtered_items.len();
        }
    }

    fn previous(&mut self) {
        if !self.filtered_items.is_empty() {
            self.selected = if self.selected == 0 {
                self.filtered_items.len() - 1
            } else {
                self.selected - 1
            };
        }
    }

    fn apply_filter(&mut self, filter: &str) {
        self.filter = filter.to_lowercase();
        if filter.is_empty() {
            self.filtered_items = (0..self.items.len()).collect();
        } else {
            self.filtered_items = self
                .items
                .iter()
                .enumerate()
                .filter(|(_, item)| {
                    item.name.to_lowercase().contains(&self.filter)
                        || item.equipment_type.to_lowercase().contains(&self.filter)
                        || item.room.to_lowercase().contains(&self.filter)
                        || item.id.to_lowercase().contains(&self.filter)
                })
                .map(|(idx, _)| idx)
                .collect();
        }
        if self.selected >= self.filtered_items.len() && !self.filtered_items.is_empty() {
            self.selected = self.filtered_items.len() - 1;
        } else if self.filtered_items.is_empty() {
            self.selected = 0;
        }
    }
}

/// Load equipment data from building files
fn load_equipment_items(
    room_filter: Option<String>,
    equipment_type_filter: Option<String>,
) -> Result<Vec<EquipmentItem>, Box<dyn std::error::Error>> {
    let building_data = loading::load_building_data("")?;
    let mut items = Vec::new();

    for floor in &building_data.floors {
        for equipment in &floor.equipment {
            // Find room containing this equipment (rooms are now in wings, and equipment is Vec<Equipment>)
            let room_name = floor
                .wings
                .iter()
                .flat_map(|w| &w.rooms)
                .find(|r| r.equipment.iter().any(|e| e.id == equipment.id))
                .map(|r| r.name.clone())
                .unwrap_or_else(|| "Unknown".to_string());

            if let Some(ref room_filter) = room_filter {
                if !room_name
                    .to_lowercase()
                    .contains(&room_filter.to_lowercase())
                {
                    continue;
                }
            }

            if let Some(ref type_filter) = equipment_type_filter {
                let eq_type_str = format!("{:?}", equipment.equipment_type);
                if !eq_type_str
                    .to_lowercase()
                    .contains(&type_filter.to_lowercase())
                {
                    continue;
                }
            }

            // Format equipment_type enum to string
            let eq_type_str = format!("{:?}", equipment.equipment_type);
            // Use health_status if available, otherwise use status
            use crate::core::{EquipmentHealthStatus, EquipmentStatus};
            let status_str = if let Some(health_status) = &equipment.health_status {
                match health_status {
                    EquipmentHealthStatus::Healthy => "Healthy".to_string(),
                    EquipmentHealthStatus::Warning => "Warning".to_string(),
                    EquipmentHealthStatus::Critical => "Critical".to_string(),
                    EquipmentHealthStatus::Unknown => "Unknown".to_string(),
                }
            } else {
                match equipment.status {
                    EquipmentStatus::Active => "Active".to_string(),
                    EquipmentStatus::Inactive => "Inactive".to_string(),
                    EquipmentStatus::Maintenance => "Maintenance".to_string(),
                    EquipmentStatus::OutOfOrder => "OutOfOrder".to_string(),
                    EquipmentStatus::Unknown => "Unknown".to_string(),
                }
            };

            // Convert Position to Point3D for EquipmentItem
            use crate::spatial::Point3D;
            let position_3d = Point3D {
                x: equipment.position.x,
                y: equipment.position.y,
                z: equipment.position.z,
            };

            items.push(EquipmentItem {
                id: equipment.id.clone(),
                name: equipment.name.clone(),
                equipment_type: eq_type_str,
                room: room_name,
                floor: floor.level,
                status: status_str,
                position: position_3d,
            });
        }
    }

    Ok(items)
}

/// Render equipment list widget
fn render_equipment_list<'a>(state: &'a BrowserState, _area: Rect, theme: &'a Theme) -> List<'a> {
    let items: Vec<ListItem> = state
        .filtered_items
        .iter()
        .enumerate()
        .map(|(display_idx, &item_idx)| {
            let item = &state.items[item_idx];
            let status_color = StatusColor::from(item.status.as_str()).color();
            let icon = StatusColor::from(item.status.as_str()).icon();
            let is_selected = display_idx == state.selected;

            let prefix = if is_selected { ">" } else { " " };

            let line = Line::from(vec![
                Span::styled(prefix, Style::default().fg(theme.accent)),
                Span::styled(
                    format!(" {} {} ", icon, item.name),
                    Style::default()
                        .fg(status_color)
                        .add_modifier(if is_selected {
                            Modifier::BOLD | Modifier::REVERSED
                        } else {
                            Modifier::empty()
                        }),
                ),
                Span::styled(
                    format!("| {} | Floor {}", item.equipment_type, item.floor),
                    Style::default().fg(theme.muted),
                ),
            ]);

            ListItem::new(line)
        })
        .collect();

    let title = if state.filter.is_empty() {
        format!("Equipment ({})", state.filtered_items.len())
    } else {
        format!(
            "Equipment (filtered: {}/{})",
            state.filtered_items.len(),
            state.items.len()
        )
    };

    List::new(items)
        .block(Block::default().borders(Borders::ALL).title(title))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
}

/// Render equipment details widget
fn render_equipment_details<'a>(
    item: &'a EquipmentItem,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let status_color = StatusColor::from(&item.status).color();
    let icon = StatusColor::from(&item.status).icon();

    let lines = vec![
        Line::from(vec![
            Span::styled("Name: ", Style::default().fg(theme.muted)),
            Span::styled(
                &item.name,
                Style::default().fg(theme.text).add_modifier(Modifier::BOLD),
            ),
        ]),
        Line::from(vec![
            Span::styled("ID: ", Style::default().fg(theme.muted)),
            Span::styled(&item.id, Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("Type: ", Style::default().fg(theme.muted)),
            Span::styled(&item.equipment_type, Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("Status: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!("{} {:?}", icon, item.status),
                Style::default().fg(status_color),
            ),
        ]),
        Line::from(vec![
            Span::styled("Room: ", Style::default().fg(theme.muted)),
            Span::styled(&item.room, Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("Floor: ", Style::default().fg(theme.muted)),
            Span::styled(item.floor.to_string(), Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("Position: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!(
                    "({:.1}, {:.1}, {:.1})",
                    item.position.x, item.position.y, item.position.z
                ),
                Style::default().fg(theme.text),
            ),
        ]),
    ];

    Paragraph::new(lines)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Equipment Details"),
        )
        .alignment(Alignment::Left)
}

/// Render footer with help text
fn render_footer<'a>(
    _area: Rect,
    theme: &'a Theme,
    filter_mode: bool,
    mouse_enabled: bool,
) -> Paragraph<'a> {
    let help_text = if filter_mode {
        "Type to filter | Enter: Apply | Esc: Cancel | q: Quit"
    } else if mouse_enabled {
        "↑/↓ or Click: Navigate | Scroll: Move | /: Search | Enter: Details | q: Quit"
    } else {
        "↑/↓: Navigate | /: Search | Enter: Details | q: Quit"
    };

    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive equipment browser
pub fn handle_equipment_browser(
    room_filter: Option<String>,
    equipment_type_filter: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();

    let items = load_equipment_items(room_filter, equipment_type_filter)?;

    if items.is_empty() {
        println!("No equipment found matching filters");
        return Ok(());
    }

    let mut state = BrowserState::new(items);
    let mut list_state = ListState::default();
    let mut filter_input = String::new();
    let mut filter_mode = false;
    let mouse_enabled = terminal.mouse_enabled();

    loop {
        terminal.terminal().draw(|frame| {
            let chunks = list_detail_layout(frame.size(), 50);

            let list = render_equipment_list(&state, chunks[0], &theme);
            list_state.select(Some(state.selected));
            frame.render_stateful_widget(list, chunks[0], &mut list_state);

            if state.show_details {
                if let Some(item) = state.selected_item() {
                    let details = render_equipment_details(item, chunks[1], &theme);
                    frame.render_widget(details, chunks[1]);
                } else {
                    let no_selection = Paragraph::new("No equipment selected")
                        .block(Block::default().borders(Borders::ALL).title("Details"))
                        .alignment(Alignment::Center);
                    frame.render_widget(no_selection, chunks[1]);
                }
            }

            let footer = render_footer(frame.size(), &theme, filter_mode, mouse_enabled);
            let footer_chunk = Layout::default()
                .direction(ratatui::layout::Direction::Vertical)
                .constraints([Constraint::Min(0), Constraint::Length(3)])
                .split(frame.size())[1];
            frame.render_widget(footer, footer_chunk);

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

            // Render help overlay if enabled
            if state.help_system.show_overlay {
                let help_overlay =
                    render_help_overlay(state.help_system.current_context, frame.size(), &theme);
                frame.render_widget(help_overlay, frame.size());
            }
        })?;

        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) if filter_mode => match key_event.code {
                    KeyCode::Char(c) => {
                        filter_input.push(c);
                    }
                    KeyCode::Backspace => {
                        filter_input.pop();
                    }
                    KeyCode::Enter => {
                        state.apply_filter(&filter_input);
                        filter_mode = false;
                        filter_input.clear();
                    }
                    KeyCode::Esc => {
                        filter_mode = false;
                        filter_input.clear();
                    }
                    _ => {}
                },
                Event::Key(key_event) => {
                    // Handle help events first
                    if handle_help_event(event.clone(), &mut state.help_system) {
                        continue;
                    }

                    // Handle cheat sheet toggle
                    if key_event.code == KeyCode::Char('h')
                        && key_event.modifiers.contains(KeyModifiers::CONTROL)
                    {
                        state.help_system.toggle_cheat_sheet();
                        continue;
                    }

                    if TerminalManager::is_quit_key(&key_event)
                        && !state.help_system.show_overlay
                        && !state.help_system.show_cheat_sheet
                    {
                        break;
                    } else if state.help_system.show_overlay || state.help_system.show_cheat_sheet {
                        // In help mode, only allow closing help
                        if key_event.code == KeyCode::Esc || key_event.code == KeyCode::Char('q') {
                            state.help_system.show_overlay = false;
                            state.help_system.show_cheat_sheet = false;
                        }
                    } else if TerminalManager::is_nav_down(&key_event) {
                        state.next();
                    } else if TerminalManager::is_nav_up(&key_event) {
                        state.previous();
                    } else if key_event.code == KeyCode::Char('/') {
                        filter_mode = true;
                        filter_input.clear();
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
