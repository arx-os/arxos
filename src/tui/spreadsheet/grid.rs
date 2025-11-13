//! Grid state management
//!
//! Handles grid state, selection, and scrolling

pub use super::types::Grid;

/// Grid state management
impl Grid {
    /// Move selection up
    pub fn move_up(&mut self) {
        if self.selected_row > 0 {
            self.selected_row -= 1;
        }
    }

    /// Move selection down
    pub fn move_down(&mut self) {
        let max_row = self.row_count().saturating_sub(1);
        if self.selected_row < max_row {
            self.selected_row += 1;
        }
    }

    /// Move selection left
    pub fn move_left(&mut self) {
        if self.selected_col > 0 {
            self.selected_col -= 1;
        }
    }

    /// Move selection right
    pub fn move_right(&mut self) {
        if self.selected_col < self.column_count().saturating_sub(1) {
            self.selected_col += 1;
        }
    }

    /// Move to first cell
    pub fn move_to_home(&mut self) {
        self.selected_row = 0;
        self.selected_col = 0;
        self.scroll_offset_y = 0;
        self.scroll_offset_x = 0;
    }

    /// Move to last cell
    pub fn move_to_end(&mut self) {
        if self.row_count() > 0 {
            self.selected_row = self.row_count() - 1;
        }
        if self.column_count() > 0 {
            self.selected_col = self.column_count() - 1;
        }
    }

    /// Move to first column in current row
    pub fn move_to_row_start(&mut self) {
        self.selected_col = 0;
        self.scroll_offset_x = 0;
    }

    /// Move to last column in current row
    pub fn move_to_row_end(&mut self) {
        if self.column_count() > 0 {
            self.selected_col = self.column_count() - 1;
        }
    }

    /// Scroll to ensure selected cell is visible
    pub fn ensure_selection_visible(&mut self, visible_rows: usize, visible_cols: usize) {
        // Vertical scrolling
        if self.selected_row < self.scroll_offset_y {
            self.scroll_offset_y = self.selected_row;
        } else if self.selected_row >= self.scroll_offset_y + visible_rows {
            self.scroll_offset_y = self.selected_row.saturating_sub(visible_rows - 1);
        }

        // Horizontal scrolling
        if self.selected_col < self.scroll_offset_x {
            self.scroll_offset_x = self.selected_col;
        } else if self.selected_col >= self.scroll_offset_x + visible_cols {
            self.scroll_offset_x = self.selected_col.saturating_sub(visible_cols - 1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tui::spreadsheet::types::{CellType, ColumnDefinition};

    fn create_test_grid() -> Grid {
        let columns = vec![
            ColumnDefinition {
                id: "col1".to_string(),
                label: "Column 1".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "col2".to_string(),
                label: "Column 2".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];

        Grid::new(columns, 10)
    }

    #[test]
    fn test_move_selection() {
        let mut grid = create_test_grid();

        assert_eq!(grid.selected_row, 0);
        assert_eq!(grid.selected_col, 0);

        grid.move_down();
        assert_eq!(grid.selected_row, 1);

        grid.move_right();
        assert_eq!(grid.selected_col, 1);

        grid.move_up();
        assert_eq!(grid.selected_row, 0);

        grid.move_left();
        assert_eq!(grid.selected_col, 0);
    }

    #[test]
    fn test_move_to_home() {
        let mut grid = create_test_grid();
        grid.selected_row = 5;
        grid.selected_col = 1;
        grid.scroll_offset_y = 3;
        grid.scroll_offset_x = 1;

        grid.move_to_home();

        assert_eq!(grid.selected_row, 0);
        assert_eq!(grid.selected_col, 0);
        assert_eq!(grid.scroll_offset_y, 0);
        assert_eq!(grid.scroll_offset_x, 0);
    }

    #[test]
    fn test_ensure_selection_visible() {
        let mut grid = create_test_grid();
        grid.selected_row = 5;
        grid.scroll_offset_y = 0;

        grid.ensure_selection_visible(3, 2);

        // Should scroll to show row 5
        assert!(grid.scroll_offset_y <= 5);
    }

    #[test]
    fn test_move_to_end() {
        let mut grid = create_test_grid();
        grid.move_to_end();

        assert_eq!(grid.selected_row, 9); // Last row (0-indexed from 10 rows)
        assert_eq!(grid.selected_col, 1); // Last column
    }

    #[test]
    fn test_move_to_row_start() {
        let mut grid = create_test_grid();
        grid.selected_col = 1;
        grid.scroll_offset_x = 5;

        grid.move_to_row_start();

        assert_eq!(grid.selected_col, 0);
        assert_eq!(grid.scroll_offset_x, 0);
    }

    #[test]
    fn test_move_to_row_end() {
        let mut grid = create_test_grid();
        grid.selected_col = 0;

        grid.move_to_row_end();

        assert_eq!(grid.selected_col, 1); // Last column
    }

    #[test]
    fn test_selection_boundaries() {
        let mut grid = create_test_grid();

        // Test upper boundaries
        grid.move_up();
        assert_eq!(grid.selected_row, 0);
        grid.move_left();
        assert_eq!(grid.selected_col, 0);

        // Test lower boundaries
        grid.move_to_end();
        let max_row = grid.row_count() - 1;
        let max_col = grid.column_count() - 1;
        grid.move_down();
        assert_eq!(grid.selected_row, max_row);
        grid.move_right();
        assert_eq!(grid.selected_col, max_col);
    }

    #[test]
    fn test_scrolling_behavior() {
        let mut grid = create_test_grid();

        // Move selection beyond visible area
        grid.selected_row = 10;
        grid.selected_col = 5;
        grid.scroll_offset_y = 0;
        grid.scroll_offset_x = 0;

        grid.ensure_selection_visible(3, 2);

        // Should have scrolled
        assert!(grid.scroll_offset_y > 0 || grid.selected_row < 3);
        assert!(grid.scroll_offset_x > 0 || grid.selected_col < 2);
    }

    #[test]
    fn test_get_cell_with_filters() {
        use crate::tui::spreadsheet::filter_sort;
        use crate::tui::spreadsheet::types::FilterCondition;

        let mut grid = create_test_grid();

        // Set some cell values
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = crate::tui::spreadsheet::types::CellValue::Text("test".to_string());
        }
        if let Some(cell) = grid.get_cell_mut(1, 0) {
            cell.value = crate::tui::spreadsheet::types::CellValue::Text("other".to_string());
        }

        // Apply filter
        filter_sort::apply_filter(&mut grid, 0, FilterCondition::Contains("test".to_string()))
            .unwrap();

        // Get cell should work with filtered rows
        assert!(grid.get_cell(0, 0).is_some());
    }

    #[test]
    fn test_row_count_with_filters() {
        use crate::tui::spreadsheet::filter_sort;
        use crate::tui::spreadsheet::types::FilterCondition;

        let mut grid = create_test_grid();

        // Apply filter
        filter_sort::apply_filter(&mut grid, 0, FilterCondition::Contains("test".to_string()))
            .unwrap();

        // Row count should reflect filtered rows
        let filtered_count = grid.row_count();
        assert!(filtered_count <= grid.original_row_count);
    }
}
