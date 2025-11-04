//! Common layout patterns for ArxOS TUI
//!
//! Provides reusable layout builders for consistent UI patterns.

use ratatui::layout::{Constraint, Direction, Layout, Rect};

/// Create a horizontal split with left and right panels
pub fn split_horizontal(area: Rect, left_percent: u16, right_percent: u16) -> Vec<Rect> {
    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(left_percent),
            Constraint::Percentage(right_percent),
        ])
        .split(area)
        .to_vec()
}

/// Create a vertical split with top, middle, and bottom sections
pub fn split_vertical_three(area: Rect, top_height: u16, bottom_height: u16) -> Vec<Rect> {
    Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(top_height),
            Constraint::Min(0),
            Constraint::Length(bottom_height),
        ])
        .split(area)
        .to_vec()
}

/// Create a dashboard layout with header, content, and footer
pub fn dashboard_layout(area: Rect) -> Vec<Rect> {
    Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(0),     // Content
            Constraint::Length(3), // Footer
        ])
        .split(area)
        .to_vec()
}

/// Create a split layout with list on left and details on right
pub fn list_detail_layout(area: Rect, list_percent: u16) -> Vec<Rect> {
    split_horizontal(area, list_percent, 100 - list_percent)
}

/// Create a grid layout for dashboard cards
pub fn card_grid(area: Rect, columns: usize) -> Vec<Rect> {
    let constraints: Vec<Constraint> = (0..columns)
        .map(|_| Constraint::Percentage(100 / columns as u16))
        .collect();
    
    Layout::default()
        .direction(Direction::Horizontal)
        .constraints(constraints)
        .split(area)
        .to_vec()
}

