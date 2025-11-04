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

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::layout::Rect;

    #[test]
    fn test_split_horizontal() {
        let area = Rect::new(0, 0, 100, 50);
        let chunks = split_horizontal(area, 30, 70);
        
        assert_eq!(chunks.len(), 2, "Should create 2 chunks");
        assert_eq!(chunks[0].width, 30, "Left should be 30%");
        assert_eq!(chunks[1].width, 70, "Right should be 70%");
    }

    #[test]
    fn test_split_vertical_three() {
        let area = Rect::new(0, 0, 100, 50);
        let chunks = split_vertical_three(area, 5, 3);
        
        assert_eq!(chunks.len(), 3, "Should create 3 chunks");
        assert_eq!(chunks[0].height, 5, "Top should be 5");
        assert_eq!(chunks[2].height, 3, "Bottom should be 3");
        assert!(chunks[1].height > 0, "Middle should have remaining space");
    }

    #[test]
    fn test_dashboard_layout() {
        let area = Rect::new(0, 0, 100, 50);
        let chunks = dashboard_layout(area);
        
        assert_eq!(chunks.len(), 3, "Should create 3 chunks");
        assert_eq!(chunks[0].height, 3, "Header should be 3");
        assert_eq!(chunks[2].height, 3, "Footer should be 3");
        assert!(chunks[1].height > 0, "Content should have remaining space");
    }

    #[test]
    fn test_list_detail_layout() {
        let area = Rect::new(0, 0, 100, 50);
        let chunks = list_detail_layout(area, 40);
        
        assert_eq!(chunks.len(), 2, "Should create 2 chunks");
        assert_eq!(chunks[0].width, 40, "List should be 40%");
        assert_eq!(chunks[1].width, 60, "Detail should be 60%");
    }

    #[test]
    fn test_card_grid() {
        let area = Rect::new(0, 0, 100, 50);
        let chunks = card_grid(area, 3);
        
        assert_eq!(chunks.len(), 3, "Should create 3 columns");
        // Each should be approximately 33% (ratatui may round)
        assert!(chunks[0].width > 0, "First column should have width");
        assert!(chunks[1].width > 0, "Second column should have width");
        assert!(chunks[2].width > 0, "Third column should have width");
    }

    #[test]
    fn test_card_grid_2_columns() {
        let area = Rect::new(0, 0, 100, 50);
        let chunks = card_grid(area, 2);
        
        assert_eq!(chunks.len(), 2, "Should create 2 columns");
        assert_eq!(chunks[0].width, 50, "Each should be 50%");
        assert_eq!(chunks[1].width, 50, "Each should be 50%");
    }

    #[test]
    fn test_layout_constraints() {
        // Test that layouts handle edge cases
        let small_area = Rect::new(0, 0, 10, 5);
        let chunks = split_horizontal(small_area, 50, 50);
        assert_eq!(chunks.len(), 2, "Should work with small areas");
        
        let chunks = dashboard_layout(small_area);
        assert_eq!(chunks.len(), 3, "Dashboard should work with small areas");
    }

    #[test]
    fn test_split_layout() {
        // Test that split layouts work correctly
        let area = Rect::new(10, 5, 80, 40);
        let chunks = split_horizontal(area, 25, 75);
        
        assert_eq!(chunks[0].x, 10, "Should preserve x position");
        assert_eq!(chunks[0].y, 5, "Should preserve y position");
        assert_eq!(chunks[1].x, 10 + chunks[0].width, "Second chunk should be adjacent");
    }
}

