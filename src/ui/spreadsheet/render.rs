//! Rendering logic for spreadsheet
//!
//! Handles rendering of grid, headers, and status bar

use ratatui::{
    Frame,
    layout::{Rect, Layout, Direction, Constraint, Margin},
    style::Style,
    widgets::{Block, Borders, Row, Table, Cell as TableCell},
};
use crate::ui::Theme;
use super::types::Grid;
use super::workflow::WorkflowStatus;
use super::editor::CellEditor;
use super::save_state::SaveState;

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
    render_grid_body(frame, layout[1], grid, theme, editor);
    
    // Render status bar
    render_status_bar(frame, layout[2], grid, theme, workflow_status, save_state);
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
fn render_grid_body(frame: &mut Frame, area: Rect, grid: &Grid, theme: &Theme, editor: Option<&CellEditor>) {
    // Calculate visible area (accounting for borders)
    let margin = Margin::new(1, 1);
    let inner_area = area.inner(&margin);
    let visible_rows = inner_area.height.saturating_sub(1); // -1 for header row
    let start_row = grid.scroll_offset_y;
    let end_row = (start_row + visible_rows as usize).min(grid.row_count());
    
    // Build table rows for visible rows only
    let mut rows = Vec::new();
    
    // Header row
    let header_cells: Vec<TableCell> = grid.columns
        .iter()
        .enumerate()
        .map(|(col_idx, col)| {
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
            TableCell::from(col.label.clone()).style(style)
        })
        .collect();
    rows.push(Row::new(header_cells).height(1));
    
    // Data rows
    for row_idx in start_row..end_row {
        let cells: Vec<TableCell> = grid.columns
            .iter()
            .enumerate()
            .map(|(col_idx, _col)| {
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
                            // Truncate long text
                            if s.len() > 30 {
                                s.truncate(27);
                                s.push_str("...");
                            }
                            s
                        })
                        .unwrap_or_else(|| String::new())
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
                let style = if is_editing {
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
                
                TableCell::from(text).style(style)
            })
            .collect();
        rows.push(Row::new(cells).height(1));
    }
    
    // Calculate column widths
    let column_widths = calculate_column_widths(&grid.columns, inner_area.width);
    
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
    
    let status_line1 = format!(
        "Row {}/{} | Column: {} ({}/{}){} | Arrow keys: Navigate{} | Ctrl+S: Save{} | Q: Quit",
        grid.selected_row + 1,
        grid.row_count(),
        col_name,
        grid.selected_col + 1,
        grid.column_count(),
        edit_hint,
        error_msg,
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

