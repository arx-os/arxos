//! Rendering logic for spreadsheet
//!
//! Handles rendering of grid, headers, and status bar

use ratatui::{
    Frame,
    layout::{Alignment, Rect, Layout, Direction, Constraint, Margin},
    style::{Style, Color, Modifier},
    text::{Line, Span},
    widgets::{Block, Borders, Row, Table, Cell as TableCell, Paragraph, Wrap},
};
use crate::ui::Theme;
use super::types::Grid;
use super::workflow::WorkflowStatus;
use super::editor::CellEditor;
use super::save_state::SaveState;
use super::search::SearchState;

/// Extract reserved system name from address path
/// Address format: /country/state/city/building/floor/room/system/fixture
fn extract_system_from_address(path: &str) -> Option<String> {
    // Split by '/' and find the system part (usually 6th segment, 0-indexed as 5)
    let parts: Vec<&str> = path.split('/').filter(|p| !p.is_empty()).collect();
    if parts.len() >= 6 {
        Some(parts[5].to_string())
    } else {
        None
    }
}

/// Render the spreadsheet
pub fn render_spreadsheet(
    frame: &mut Frame,
    area: Rect,
    grid: &Grid,
    theme: &Theme,
    workflow_status: &WorkflowStatus,
) {
    render_spreadsheet_with_editor(frame, area, grid, theme, workflow_status, None)
}

/// Render the spreadsheet with optional editor
pub fn render_spreadsheet_with_editor(
    frame: &mut Frame,
    area: Rect,
    grid: &Grid,
    theme: &Theme,
    workflow_status: &WorkflowStatus,
    editor: Option<&CellEditor>,
) {
    render_spreadsheet_with_editor_and_save(
        frame, area, grid, theme, workflow_status, editor, None
    )
}

/// Render the spreadsheet with editor and save state
pub fn render_spreadsheet_with_editor_and_save(
    frame: &mut Frame,
    area: Rect,
    grid: &Grid,
    theme: &Theme,
    workflow_status: &WorkflowStatus,
    editor: Option<&CellEditor>,
    save_state: Option<&SaveState>,
) {
    render_spreadsheet_with_editor_save_search(
        frame, area, grid, theme, workflow_status, editor, save_state, None
    )
}

/// Render the spreadsheet with editor, save state, and search
pub fn render_spreadsheet_with_editor_save_search(
    frame: &mut Frame,
    area: Rect,
    grid: &Grid,
    theme: &Theme,
    workflow_status: &WorkflowStatus,
    editor: Option<&CellEditor>,
    save_state: Option<&SaveState>,
    search_state: Option<&SearchState>,
) {
    render_spreadsheet_with_editor_save_search_ar(
        frame, area, grid, theme, workflow_status, editor, save_state, search_state, None
    )
}

/// Render the spreadsheet with editor, save state, search, and AR scan status
pub fn render_spreadsheet_with_editor_save_search_ar(
    frame: &mut Frame,
    area: Rect,
    grid: &Grid,
    theme: &Theme,
    workflow_status: &WorkflowStatus,
    editor: Option<&CellEditor>,
    save_state: Option<&SaveState>,
    search_state: Option<&SearchState>,
    ar_scan_count: Option<usize>,
) {
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(10),    // Grid body
            Constraint::Length(2),  // Status bar (2 lines for workflow info)
        ])
        .split(area);
    
    // Render header
    render_header(frame, layout[0], grid, theme);
    
    // Render grid body
    render_grid_body(frame, layout[1], grid, theme, editor, search_state);
    
    // Render address modal if active
    if let Some(ref address_path) = grid.address_modal {
        render_address_modal(frame, area, address_path, theme);
    }
    
    // Render status bar
    render_status_bar(frame, layout[2], grid, theme, workflow_status, save_state, search_state, ar_scan_count);
}

/// Render header
fn render_header(frame: &mut Frame, area: Rect, _grid: &Grid, theme: &Theme) {
    let header_text = format!("Spreadsheet: Equipment List");
    let block = Block::default()
        .title(header_text)
        .borders(Borders::ALL)
        .style(Style::default().fg(theme.text));
    
    frame.render_widget(block, area);
}

/// Render grid body with virtual scrolling
fn render_grid_body(frame: &mut Frame, area: Rect, grid: &Grid, theme: &Theme, editor: Option<&CellEditor>, search_state: Option<&SearchState>) {
    // Calculate visible area (accounting for borders)
    let margin = Margin::new(1, 1);
    let inner_area = area.inner(&margin);
    let visible_rows = inner_area.height.saturating_sub(1); // -1 for header row
    let start_row = grid.scroll_offset_y;
    let end_row = (start_row + visible_rows as usize).min(grid.row_count());
    
    // Build table rows for visible rows only
    let mut rows = Vec::new();
    
    // Header row - only show visible columns
    let header_cells: Vec<TableCell> = grid.columns
        .iter()
        .enumerate()
        .filter_map(|(col_idx, col)| {
            if !grid.is_column_visible(col_idx) {
                return None;
            }
            let is_selected_col = col_idx == grid.selected_col;
            let style = if is_selected_col {
                Style::default()
                    .fg(theme.accent)
                    .add_modifier(ratatui::style::Modifier::BOLD | ratatui::style::Modifier::UNDERLINED)
            } else {
                Style::default()
                    .fg(theme.secondary)
                    .add_modifier(ratatui::style::Modifier::BOLD)
            };
            Some(TableCell::from(col.label.clone()).style(style))
        })
        .collect();
    rows.push(Row::new(header_cells).height(1));
    
    // Data rows - only show visible columns
    for row_idx in start_row..end_row {
        let cells: Vec<TableCell> = grid.columns
            .iter()
            .enumerate()
            .filter_map(|(col_idx, _col)| {
                if !grid.is_column_visible(col_idx) {
                    return None;
                }
                let cell = grid.get_cell(row_idx, col_idx);
                let is_editing = grid.editing_cell == Some((row_idx, col_idx));
                
                // Use editor value if editing, otherwise use cell value
                let mut text = if is_editing {
                    if let Some(ed) = editor {
                        ed.get_current_value().to_string()
                    } else {
                        String::new()
                    }
                } else {
                    cell
                        .map(|c| {
                            let mut s = c.value.to_string();
                            // Truncate long text (special handling for address column)
                            if col_idx == 0 && grid.columns[col_idx].id.contains("address") {
                                // Address column: allow longer truncation
                                if s.len() > 45 {
                                    s.truncate(42);
                                    s.push_str("...");
                                }
                            } else if s.len() > 30 {
                                s.truncate(27);
                                s.push_str("...");
                            }
                            s
                        })
                        .unwrap_or_default()
                };
                
                // Show modified indicator (only if not editing)
                if !is_editing {
                    if let Some(c) = cell {
                        if c.modified {
                            text = format!("*{}", text);
                        }
                    }
                }
                
                // Determine cell style
                let is_selected = row_idx == grid.selected_row && col_idx == grid.selected_col;
                
                // Check if this cell matches search (for highlighting)
                let is_search_match = if let Some(search) = search_state {
                    search.is_active && search.matches.contains(&(row_idx, col_idx))
                } else {
                    false
                };
                
                // Color-code address column by reserved system
                let mut base_style = if is_editing {
                    // Editing style: underline and different background
                    Style::default()
                        .bg(theme.accent)
                        .fg(theme.text)
                        .add_modifier(ratatui::style::Modifier::UNDERLINED)
                } else if is_selected {
                    Style::default().bg(theme.accent).fg(theme.text)
                } else if cell.map(|c| c.read_only).unwrap_or(false) {
                    Style::default().fg(theme.muted)
                } else if cell.map(|c| c.modified).unwrap_or(false) {
                    Style::default().fg(ratatui::style::Color::Yellow)
                } else if cell.and_then(|c| c.error.as_ref()).is_some() {
                    // Error style: red text
                    Style::default().fg(ratatui::style::Color::Red)
                } else {
                    Style::default().fg(theme.text)
                };
                
                // Apply search match highlighting
                if is_search_match && !is_selected {
                    base_style = base_style.bg(Color::Yellow).fg(Color::Black);
                }
                
                // Apply system color for address column
                if !is_editing && col_idx == 0 && grid.columns[col_idx].id.contains("address") {
                    if let Some(c) = cell {
                        let addr_path = c.value.to_string();
                        // Extract system from address path (e.g., /usa/ny/.../mech/boiler-01 -> mech)
                        if let Some(system) = extract_system_from_address(&addr_path) {
                            let system_color = Theme::system_color(&system);
                            if !is_selected {
                                base_style = base_style.fg(system_color);
                            }
                        }
                    }
                }
                
                let style = base_style;
                
                Some(TableCell::from(text).style(style))
            })
            .collect();
        rows.push(Row::new(cells).height(1));
    }
    
    // Calculate column widths - only for visible columns
    let visible_column_indices: Vec<usize> = grid.columns
        .iter()
        .enumerate()
        .filter_map(|(col_idx, _col)| {
            if grid.is_column_visible(col_idx) {
                Some(col_idx)
            } else {
                None
            }
        })
        .collect();
    
    // Calculate widths for visible columns only
    let column_widths = if visible_column_indices.len() == grid.columns.len() {
        // All columns visible - use all columns
        calculate_column_widths(&grid.columns, inner_area.width)
    } else {
        // Some columns hidden - calculate for visible ones only
        let visible_columns: Vec<&super::types::ColumnDefinition> = visible_column_indices
            .iter()
            .map(|&idx| &grid.columns[idx])
            .collect();
        // Create owned columns for the function
        let owned_columns: Vec<super::types::ColumnDefinition> = visible_columns.iter().map(|c| (*c).clone()).collect();
        calculate_column_widths(&owned_columns, inner_area.width)
    };
    
    let table = Table::new(rows)
        .block(Block::default().borders(Borders::ALL))
        .widths(&column_widths)
        .column_spacing(1);
    
    frame.render_widget(table, area);
}

/// Calculate column widths based on preferred widths and available space
fn calculate_column_widths(columns: &[super::types::ColumnDefinition], available_width: u16) -> Vec<Constraint> {
    if columns.is_empty() {
        return vec![];
    }
    
    let mut constraints = Vec::new();
    let mut total_preferred = 0u16;
    let mut flexible_count = 0;
    
    // First pass: collect preferred widths
    for col in columns {
        if let Some(width) = col.width {
            total_preferred += width;
            constraints.push(Constraint::Length(width));
        } else {
            flexible_count += 1;
            constraints.push(Constraint::Min(8)); // Minimum width
        }
    }
    
    // If we have flexible columns and space left, distribute it
    if flexible_count > 0 && available_width > total_preferred {
        let remaining = available_width.saturating_sub(total_preferred);
        let per_flexible = remaining / flexible_count as u16;
        
        for constraint in &mut constraints {
            if let Constraint::Min(_) = constraint {
                *constraint = Constraint::Min(8.max(per_flexible));
            }
        }
    }
    
    // If total preferred exceeds available, use percentages
    if total_preferred > available_width {
        let per_column = 100 / columns.len() as u16;
        constraints = vec![Constraint::Percentage(per_column); columns.len()];
    }
    
    constraints
}

/// Render status bar
fn render_status_bar(
    frame: &mut Frame,
    area: Rect,
    grid: &Grid,
    theme: &Theme,
    workflow_status: &WorkflowStatus,
    save_state: Option<&SaveState>,
    search_state: Option<&SearchState>,
    ar_scan_count: Option<usize>,
) {
    let layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .split(area);
    
    // Status line 1: Position and navigation info
    let current_col = grid.columns.get(grid.selected_col);
    let col_name = current_col.map(|c| c.label.as_str()).unwrap_or("Unknown");
    let is_editing = grid.editing_cell.is_some();
    let edit_hint = if is_editing {
        " | Editing - Enter: Apply | Esc: Cancel"
    } else {
        " | Enter: Edit"
    };
    
    let error_msg = if let Some((row, col)) = grid.editing_cell {
        grid.get_cell(row, col)
            .and_then(|c| c.error.as_ref())
            .map(|e| format!(" | Error: {}", e))
            .unwrap_or_default()
    } else {
        String::new()
    };
    
    // Add save status
    let save_status = save_state.map(|s| {
        match s {
            SaveState::Clean => String::new(),
            SaveState::Modified => " | Modified".to_string(),
            SaveState::Saving => " | Saving...".to_string(),
            SaveState::Saved => " | Saved".to_string(),
            SaveState::Error(msg) => format!(" | Error: {}", msg),
        }
    }).unwrap_or_default();
    
    // Add search status
    let search_status = if let Some(search) = search_state {
        if search.is_active {
            let match_info = if search.match_count() > 0 {
                format!(" | Search: \"{}\" ({} matches, {}/{})", 
                    search.query, 
                    search.match_count(),
                    search.current_match_index(),
                    search.match_count())
            } else {
                format!(" | Search: \"{}\" (no matches)", search.query)
            };
            format!("{}{}", if search.use_glob { " [glob]" } else { "" }, match_info)
        } else {
            String::new()
        }
    } else {
        String::new()
    };
    
    // Add AR scan status
    let ar_status = if let Some(count) = ar_scan_count {
        if count > 0 {
            format!(" | AR: {} new scan(s)", count)
        } else {
            String::new()
        }
    } else {
        String::new()
    };
    
    let status_line1 = format!(
        "Row {}/{} | Column: {} ({}/{}){} | Arrow keys: Navigate{} | Ctrl+S: Save | Ctrl+F: Search | Ctrl+A: Toggle Address{}{} | Q: Quit{}",
        grid.selected_row + 1,
        grid.row_count(),
        col_name,
        grid.selected_col + 1,
        grid.column_count(),
        edit_hint,
        error_msg,
        search_status,
        ar_status,
        if save_status.is_empty() { "" } else { &save_status }
    );
    
    // Status line 2: Workflow warnings
    let status_line2 = if workflow_status.has_active_workflows() {
        workflow_status.warnings().join(" | ")
    } else {
        String::new()
    };
    
    let block1 = Block::default()
        .title(status_line1)
        .borders(Borders::ALL)
        .style(Style::default().fg(theme.muted));
    frame.render_widget(block1, layout[0]);
    
    if !status_line2.is_empty() {
        let block2 = Block::default()
            .title(status_line2)
            .borders(Borders::ALL)
            .style(Style::default().fg(ratatui::style::Color::Yellow));
        frame.render_widget(block2, layout[1]);
    }
}

/// Render address modal showing full path
fn render_address_modal(frame: &mut Frame, area: Rect, address_path: &str, theme: &Theme) {
    // Calculate modal area (centered, 60% width, 40% height)
    let modal_width = (area.width as f32 * 0.6) as u16;
    let modal_height = (area.height as f32 * 0.4) as u16;
    let modal_x = (area.width.saturating_sub(modal_width)) / 2;
    let modal_y = (area.height.saturating_sub(modal_height)) / 2;
    
    let modal_area = Rect {
        x: area.x + modal_x,
        y: area.y + modal_y,
        width: modal_width,
        height: modal_height,
    };
    
    // Create lines for modal content
    let mut lines = vec![
        Line::from(vec![
            Span::styled(
                "Full Address Path",
                Style::default().fg(theme.accent).add_modifier(Modifier::BOLD),
            ),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled(
                address_path,
                Style::default().fg(theme.text),
            ),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled(
                "Press Esc to close",
                Style::default().fg(theme.muted),
            ),
        ]),
    ];
    
    // Extract and display system information if available
    if let Some(system) = extract_system_from_address(address_path) {
        let system_color = Theme::system_color(&system);
        let system_clone = system.clone(); // Clone to extend lifetime
        lines.insert(2, Line::from(vec![
            Span::styled("System: ", Style::default().fg(theme.muted)),
            Span::styled(
                system_clone,
                Style::default().fg(system_color).add_modifier(Modifier::BOLD),
            ),
        ]));
    }
    
    let paragraph = Paragraph::new(lines)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Address")
                .border_style(Style::default().fg(theme.accent))
        )
        .alignment(Alignment::Left)
        .wrap(Wrap { trim: true })
        .style(Style::default().fg(theme.text).bg(theme.background));
    
    frame.render_widget(paragraph, modal_area);
}

