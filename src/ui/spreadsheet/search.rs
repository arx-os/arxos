//! Search/find functionality for spreadsheet
//!
//! Handles searching across cells and navigating to matches

use crate::ui::spreadsheet::data_source::SpreadsheetDataSource;
use crate::ui::spreadsheet::types::Grid;

/// Check if a pattern contains glob wildcards
fn is_glob_pattern(pattern: &str) -> bool {
    pattern.contains('*') || pattern.contains('?')
}

/// Search state
#[derive(Debug)]
pub struct SearchState {
    pub query: String,
    pub case_sensitive: bool,
    pub current_match: Option<(usize, usize)>, // (row, col)
    pub matches: Vec<(usize, usize)>,          // All matches
    pub match_index: usize,
    pub is_active: bool, // Whether search is currently active
    pub use_glob: bool,  // Whether to use glob pattern matching
}

impl SearchState {
    /// Create new search state
    pub fn new(query: String, case_sensitive: bool) -> Self {
        let use_glob = is_glob_pattern(&query);
        Self {
            query,
            case_sensitive,
            current_match: None,
            matches: Vec::new(),
            match_index: 0,
            is_active: false,
            use_glob,
        }
    }

    /// Update query and detect glob pattern
    pub fn update_query(&mut self, query: String) {
        self.query = query.clone();
        self.use_glob = is_glob_pattern(&query);
        self.matches.clear();
        self.current_match = None;
        self.match_index = 0;
    }

    /// Activate search mode
    pub fn activate(&mut self) {
        self.is_active = true;
    }

    /// Deactivate search mode
    pub fn deactivate(&mut self) {
        self.is_active = false;
    }

    /// Find all matches in grid
    pub fn find_matches(&mut self, grid: &Grid, data_source: &dyn SpreadsheetDataSource) {
        self.matches.clear();

        if self.query.is_empty() {
            self.current_match = None;
            return;
        }

        let query = if self.case_sensitive {
            self.query.clone()
        } else {
            self.query.to_lowercase()
        };

        // Try to compile glob pattern if using glob
        let glob_pattern = if self.use_glob {
            glob::Pattern::new(&query).ok()
        } else {
            None
        };

        for row_idx in 0..grid.row_count() {
            let original_row = grid.get_original_row(row_idx).unwrap_or(row_idx);
            for col_idx in 0..grid.column_count() {
                if let Ok(cell_value) = data_source.get_cell(original_row, col_idx) {
                    let cell_str = if self.case_sensitive {
                        cell_value.to_string()
                    } else {
                        cell_value.to_string().to_lowercase()
                    };

                    let matches = if self.use_glob {
                        // Use glob pattern matching
                        if let Some(ref pattern) = glob_pattern {
                            pattern.matches(&cell_str)
                        } else {
                            false
                        }
                    } else {
                        // Simple string contains
                        cell_str.contains(&query)
                    };

                    if matches {
                        self.matches.push((row_idx, col_idx));
                    }
                }
            }
        }

        if !self.matches.is_empty() {
            self.match_index = 0;
            self.current_match = Some(self.matches[0]);
        } else {
            self.current_match = None;
            self.match_index = 0;
        }
    }

    /// Navigate to next match
    pub fn next_match(&mut self) -> Option<(usize, usize)> {
        if self.matches.is_empty() {
            return None;
        }

        self.match_index = (self.match_index + 1) % self.matches.len();
        self.current_match = Some(self.matches[self.match_index]);
        self.current_match
    }

    /// Navigate to previous match
    pub fn previous_match(&mut self) -> Option<(usize, usize)> {
        if self.matches.is_empty() {
            return None;
        }

        if self.match_index == 0 {
            self.match_index = self.matches.len() - 1;
        } else {
            self.match_index -= 1;
        }
        self.current_match = Some(self.matches[self.match_index]);
        self.current_match
    }

    /// Get current match count
    pub fn match_count(&self) -> usize {
        self.matches.len()
    }

    /// Get current match index (1-based)
    pub fn current_match_index(&self) -> usize {
        self.match_index + 1
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::spreadsheet::types::{CellType, CellValue, ColumnDefinition, Grid};

    // Mock data source for testing
    struct MockDataSource {
        data: Vec<Vec<String>>,
    }

    impl SpreadsheetDataSource for MockDataSource {
        fn columns(&self) -> Vec<ColumnDefinition> {
            vec![ColumnDefinition {
                id: "col1".to_string(),
                label: "Column 1".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            }]
        }

        fn row_count(&self) -> usize {
            self.data.len()
        }

        fn get_cell(
            &self,
            row: usize,
            col: usize,
        ) -> Result<CellValue, Box<dyn std::error::Error>> {
            Ok(CellValue::Text(
                self.data
                    .get(row)
                    .and_then(|r| r.get(col))
                    .cloned()
                    .unwrap_or_else(|| "".to_string()),
            ))
        }

        fn set_cell(
            &mut self,
            _row: usize,
            _col: usize,
            _value: CellValue,
        ) -> Result<(), Box<dyn std::error::Error>> {
            Ok(())
        }

        fn save(&mut self, _commit: bool) -> Result<(), Box<dyn std::error::Error>> {
            Ok(())
        }

        fn reload(&mut self) -> Result<(), Box<dyn std::error::Error>> {
            Ok(())
        }
    }

    fn create_test_grid() -> Grid {
        let columns = vec![ColumnDefinition {
            id: "col1".to_string(),
            label: "Column 1".to_string(),
            data_type: CellType::Text,
            editable: true,
            width: None,
            validation: None,
            enum_values: None,
        }];

        Grid::new(columns, 5)
    }

    #[test]
    fn test_search_find_matches() {
        let mut search = SearchState::new("test".to_string(), false);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![
                vec!["test1".to_string()],
                vec!["other".to_string()],
                vec!["test2".to_string()],
            ],
        };

        search.find_matches(&grid, &data_source);

        assert_eq!(search.match_count(), 2);
    }

    #[test]
    fn test_search_next_match() {
        let mut search = SearchState::new("test".to_string(), false);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![
                vec!["test1".to_string()],
                vec!["test2".to_string()],
                vec!["test3".to_string()],
            ],
        };

        search.find_matches(&grid, &data_source);

        let match1 = search.next_match();
        assert!(match1.is_some());

        let match2 = search.next_match();
        assert!(match2.is_some());
    }

    #[test]
    fn test_search_previous_match() {
        let mut search = SearchState::new("test".to_string(), false);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![
                vec!["test1".to_string()],
                vec!["test2".to_string()],
                vec!["test3".to_string()],
            ],
        };

        search.find_matches(&grid, &data_source);
        search.next_match(); // Move to second match

        let prev_match = search.previous_match();
        assert!(prev_match.is_some());
    }

    #[test]
    fn test_search_case_sensitive() {
        let mut search = SearchState::new("TEST".to_string(), true);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![vec!["test".to_string()], vec!["TEST".to_string()]],
        };

        search.find_matches(&grid, &data_source);

        // Case-sensitive should only find "TEST"
        assert_eq!(search.match_count(), 1);
    }

    #[test]
    fn test_search_case_insensitive() {
        let mut search = SearchState::new("TEST".to_string(), false);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![vec!["test".to_string()], vec!["TEST".to_string()]],
        };

        search.find_matches(&grid, &data_source);

        // Case-insensitive should find both
        assert_eq!(search.match_count(), 2);
    }

    #[test]
    fn test_search_wraps_around() {
        let mut search = SearchState::new("test".to_string(), false);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![vec!["test1".to_string()], vec!["test2".to_string()]],
        };

        search.find_matches(&grid, &data_source);

        // Navigate to end
        search.next_match();

        // Next should wrap around
        let wrapped = search.next_match();
        assert!(wrapped.is_some());
    }

    #[test]
    fn test_match_count() {
        let mut search = SearchState::new("test".to_string(), false);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![
                vec!["test1".to_string()],
                vec!["test2".to_string()],
                vec!["test3".to_string()],
            ],
        };

        search.find_matches(&grid, &data_source);

        assert_eq!(search.match_count(), 3);
    }

    #[test]
    fn test_current_match_index() {
        let mut search = SearchState::new("test".to_string(), false);
        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![vec!["test1".to_string()], vec!["test2".to_string()]],
        };

        search.find_matches(&grid, &data_source);

        assert_eq!(search.current_match_index(), 1);

        search.next_match();
        assert_eq!(search.current_match_index(), 2);
    }

    #[test]
    fn test_search_glob_pattern() {
        let mut search = SearchState::new("/usa/ny/*/boiler-*".to_string(), false);
        assert!(search.use_glob);

        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![
                vec!["/usa/ny/brooklyn/boiler-01".to_string()],
                vec!["/usa/ny/manhattan/boiler-02".to_string()],
                vec!["/usa/ca/boiler-03".to_string()],
            ],
        };

        search.find_matches(&grid, &data_source);

        // Should match first two (NY boilers) but not CA
        assert_eq!(search.match_count(), 2);
    }

    #[test]
    fn test_search_simple_string_not_glob() {
        let mut search = SearchState::new("boiler".to_string(), false);
        assert!(!search.use_glob);

        let grid = create_test_grid();
        let data_source = MockDataSource {
            data: vec![vec!["boiler-01".to_string()], vec!["other".to_string()]],
        };

        search.find_matches(&grid, &data_source);
        assert_eq!(search.match_count(), 1);
    }

    #[test]
    fn test_search_update_query() {
        let mut search = SearchState::new("test".to_string(), false);
        assert!(!search.use_glob);

        search.update_query("/usa/*/boiler-*".to_string());
        assert!(search.use_glob);
        assert_eq!(search.query, "/usa/*/boiler-*");
    }

    #[test]
    fn test_search_activate_deactivate() {
        let mut search = SearchState::new("test".to_string(), false);
        assert!(!search.is_active);

        search.activate();
        assert!(search.is_active);

        search.deactivate();
        assert!(!search.is_active);
    }
}
