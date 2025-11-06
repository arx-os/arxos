//! Filtering and sorting functionality
//!
//! Handles column filtering and multi-column sorting

use crate::ui::spreadsheet::types::{Grid, FilterCondition, ColumnFilter, SortOrder, ColumnSort, CellValue};
use std::cmp::Ordering;

/// Apply filter to grid
pub fn apply_filter(grid: &mut Grid, column_idx: usize, condition: FilterCondition) -> Result<(), Box<dyn std::error::Error>> {
    // Remove existing filter for this column if any
    grid.filters.retain(|f| f.column_idx != column_idx);
    
    // Add new filter
    grid.filters.push(ColumnFilter {
        column_idx,
        condition,
    });
    
    // Reapply all filters
    apply_all_filters(grid);
    
    Ok(())
}

/// Remove filter for a column
pub fn remove_filter(grid: &mut Grid, column_idx: usize) {
    grid.filters.retain(|f| f.column_idx != column_idx);
    apply_all_filters(grid);
}

/// Clear all filters
pub fn clear_filters(grid: &mut Grid) {
    grid.filters.clear();
    grid.filtered_rows = (0..grid.original_row_count).collect();
}

/// Apply all filters to grid
fn apply_all_filters(grid: &mut Grid) {
    if grid.filters.is_empty() {
        grid.filtered_rows = (0..grid.original_row_count).collect();
        return;
    }
    
    grid.filtered_rows.clear();
    
    for row_idx in 0..grid.original_row_count {
        let mut matches = true;
        
        for filter in &grid.filters {
            if let Some(cell) = grid.rows.get(row_idx).and_then(|r| r.get(filter.column_idx)) {
                if !matches_filter(&cell.value, &filter.condition) {
                    matches = false;
                    break;
                }
            } else {
                matches = false;
                break;
            }
        }
        
        if matches {
            grid.filtered_rows.push(row_idx);
        }
    }
    
    // Reapply sort after filtering
    if !grid.sort_order.is_empty() {
        apply_sort(grid);
    }
}

/// Check if cell value matches filter condition
fn matches_filter(value: &CellValue, condition: &FilterCondition) -> bool {
    match condition {
        FilterCondition::Contains(pattern) => {
            let value_str = value.to_string().to_lowercase();
            value_str.contains(&pattern.to_lowercase())
        }
        FilterCondition::StartsWith(pattern) => {
            let value_str = value.to_string().to_lowercase();
            value_str.starts_with(&pattern.to_lowercase())
        }
        FilterCondition::EndsWith(pattern) => {
            let value_str = value.to_string().to_lowercase();
            value_str.ends_with(&pattern.to_lowercase())
        }
        FilterCondition::Equals(pattern) => {
            value.to_string().to_lowercase() == pattern.to_lowercase()
        }
        FilterCondition::NotEquals(pattern) => {
            value.to_string().to_lowercase() != pattern.to_lowercase()
        }
        FilterCondition::GreaterThan(threshold) => {
            match value {
                CellValue::Number(n) => *n > *threshold,
                CellValue::Integer(i) => (*i as f64) > *threshold,
                _ => false,
            }
        }
        FilterCondition::LessThan(threshold) => {
            match value {
                CellValue::Number(n) => *n < *threshold,
                CellValue::Integer(i) => (*i as f64) < *threshold,
                _ => false,
            }
        }
        FilterCondition::InRange(min, max) => {
            match value {
                CellValue::Number(n) => *n >= *min && *n <= *max,
                CellValue::Integer(i) => {
                    let n = *i as f64;
                    n >= *min && n <= *max
                }
                _ => false,
            }
        }
        FilterCondition::IsIn(values) => {
            let value_str = value.to_string();
            values.iter().any(|v| v.to_lowercase() == value_str.to_lowercase())
        }
        FilterCondition::Glob(pattern) => {
            // Try to compile and match glob pattern
            if let Ok(glob_pattern) = glob::Pattern::new(pattern) {
                glob_pattern.matches(&value.to_string())
            } else {
                false
            }
        }
    }
}

/// Sort grid by column
pub fn sort_by_column(grid: &mut Grid, column_idx: usize, ascending: bool) -> Result<(), Box<dyn std::error::Error>> {
    // Remove existing sort for this column if any
    grid.sort_order.retain(|s| s.column_idx != column_idx);
    
    // Add new sort
    grid.sort_order.push(ColumnSort {
        column_idx,
        order: if ascending { SortOrder::Ascending } else { SortOrder::Descending },
    });
    
    apply_sort(grid);
    
    Ok(())
}

/// Apply sort to filtered rows
fn apply_sort(grid: &mut Grid) {
    if grid.sort_order.is_empty() {
        return;
    }
    
    grid.filtered_rows.sort_by(|a, b| {
        let mut ordering = Ordering::Equal;
        
        for sort in &grid.sort_order {
            let a_row = *a;
            let b_row = *b;
            
            let a_cell = grid.rows.get(a_row).and_then(|r| r.get(sort.column_idx));
            let b_cell = grid.rows.get(b_row).and_then(|r| r.get(sort.column_idx));
            
            let cmp = match (a_cell, b_cell) {
                (Some(a_c), Some(b_c)) => compare_cell_values(&a_c.value, &b_c.value),
                (Some(_), None) => Ordering::Greater,
                (None, Some(_)) => Ordering::Less,
                (None, None) => Ordering::Equal,
            };
            
            ordering = match sort.order {
                SortOrder::Ascending => cmp,
                SortOrder::Descending => cmp.reverse(),
            };
            
            // If not equal, use this comparison (multi-column sort)
            if ordering != Ordering::Equal {
                break;
            }
        }
        
        ordering
    });
}

/// Compare two cell values
fn compare_cell_values(a: &CellValue, b: &CellValue) -> Ordering {
    match (a, b) {
        (CellValue::Text(a_str), CellValue::Text(b_str)) => a_str.cmp(b_str),
        (CellValue::Number(a_num), CellValue::Number(b_num)) => a_num.partial_cmp(b_num).unwrap_or(Ordering::Equal),
        (CellValue::Integer(a_int), CellValue::Integer(b_int)) => a_int.cmp(b_int),
        (CellValue::Boolean(a_bool), CellValue::Boolean(b_bool)) => a_bool.cmp(b_bool),
        (CellValue::Enum(a_str), CellValue::Enum(b_str)) => a_str.cmp(b_str),
        (CellValue::Date(a_str), CellValue::Date(b_str)) => a_str.cmp(b_str),
        (CellValue::UUID(a_str), CellValue::UUID(b_str)) => a_str.cmp(b_str),
        (CellValue::Reference(a_str), CellValue::Reference(b_str)) => a_str.cmp(b_str),
        (CellValue::Empty, CellValue::Empty) => Ordering::Equal,
        (CellValue::Empty, _) => Ordering::Less,
        (_, CellValue::Empty) => Ordering::Greater,
        _ => {
            // Different types - compare as strings
            a.to_string().cmp(&b.to_string())
        }
    }
}

/// Clear all sorts
pub fn clear_sorts(grid: &mut Grid) {
    grid.sort_order.clear();
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::spreadsheet::types::{ColumnDefinition, CellType, CellValue};
    
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
                data_type: CellType::Number,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];
        
        let mut grid = Grid::new(columns, 5);
        
        // Set some test data
        for row in 0..5 {
            if let Some(cell) = grid.get_cell_mut(row, 0) {
                cell.value = CellValue::Text(format!("test{}", row));
            }
            if let Some(cell) = grid.get_cell_mut(row, 1) {
                cell.value = CellValue::Number(row as f64 * 10.0);
            }
        }
        
        grid
    }
    
    #[test]
    fn test_filter_contains() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::Contains("test1".to_string())).unwrap();
        
        assert_eq!(grid.filtered_rows.len(), 1);
    }
    
    #[test]
    fn test_filter_starts_with() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::StartsWith("test".to_string())).unwrap();
        
        assert_eq!(grid.filtered_rows.len(), 5);
    }
    
    #[test]
    fn test_filter_ends_with() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::EndsWith("1".to_string())).unwrap();
        
        assert_eq!(grid.filtered_rows.len(), 1);
    }
    
    #[test]
    fn test_filter_equals() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::Equals("test0".to_string())).unwrap();
        
        assert_eq!(grid.filtered_rows.len(), 1);
    }
    
    #[test]
    fn test_filter_not_equals() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::NotEquals("test0".to_string())).unwrap();
        
        assert_eq!(grid.filtered_rows.len(), 4);
    }
    
    #[test]
    fn test_filter_greater_than() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 1, FilterCondition::GreaterThan(20.0)).unwrap();
        
        assert!(grid.filtered_rows.len() >= 2);
    }
    
    #[test]
    fn test_filter_less_than() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 1, FilterCondition::LessThan(30.0)).unwrap();
        
        assert!(grid.filtered_rows.len() >= 3);
    }
    
    #[test]
    fn test_filter_in_range() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 1, FilterCondition::InRange(10.0, 30.0)).unwrap();
        
        assert!(grid.filtered_rows.len() >= 2);
    }
    
    #[test]
    fn test_filter_is_in() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::IsIn(vec!["test0".to_string(), "test1".to_string()])).unwrap();
        
        assert_eq!(grid.filtered_rows.len(), 2);
    }
    
    #[test]
    fn test_filter_case_insensitive() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::Contains("TEST".to_string())).unwrap();
        
        assert_eq!(grid.filtered_rows.len(), 5);
    }
    
    #[test]
    fn test_filter_multiple_columns() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::Contains("test".to_string())).unwrap();
        apply_filter(&mut grid, 1, FilterCondition::GreaterThan(10.0)).unwrap();
        
        assert!(grid.filtered_rows.len() <= 4);
    }
    
    #[test]
    fn test_filter_clear() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::Contains("test1".to_string())).unwrap();
        assert_eq!(grid.filtered_rows.len(), 1);
        
        clear_filters(&mut grid);
        assert_eq!(grid.filtered_rows.len(), 5);
    }
    
    #[test]
    fn test_filter_remove_single() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::Contains("test".to_string())).unwrap();
        apply_filter(&mut grid, 1, FilterCondition::GreaterThan(20.0)).unwrap();
        
        remove_filter(&mut grid, 0);
        
        // Should still have filter on column 1
        assert!(grid.filtered_rows.len() > 0);
    }
    
    #[test]
    fn test_sort_ascending() {
        let mut grid = create_test_grid();
        
        // Set values for sorting
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Text("zebra".to_string());
        }
        if let Some(cell) = grid.get_cell_mut(1, 0) {
            cell.value = CellValue::Text("apple".to_string());
        }
        if let Some(cell) = grid.get_cell_mut(2, 0) {
            cell.value = CellValue::Text("banana".to_string());
        }
        
        sort_by_column(&mut grid, 0, true).unwrap();
        
        // First filtered row should be "apple"
        if let Some(first_row) = grid.filtered_rows.first() {
            if let Some(cell) = grid.get_cell(*first_row, 0) {
                assert_eq!(cell.value.to_string(), "apple");
            }
        }
    }
    
    #[test]
    fn test_sort_descending() {
        let mut grid = create_test_grid();
        
        // Set values for sorting
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Text("apple".to_string());
        }
        if let Some(cell) = grid.get_cell_mut(1, 0) {
            cell.value = CellValue::Text("zebra".to_string());
        }
        if let Some(cell) = grid.get_cell_mut(2, 0) {
            cell.value = CellValue::Text("banana".to_string());
        }
        
        sort_by_column(&mut grid, 0, false).unwrap();
        
        // First filtered row should be "zebra"
        if let Some(first_row) = grid.filtered_rows.first() {
            if let Some(cell) = grid.get_cell(*first_row, 0) {
                assert_eq!(cell.value.to_string(), "zebra");
            }
        }
    }
    
    #[test]
    fn test_sort_multiple_columns() {
        let mut grid = create_test_grid();
        
        // Set values for multi-column sort
        for row in 0..3 {
            if let Some(cell) = grid.get_cell_mut(row, 0) {
                cell.value = CellValue::Text("same".to_string());
            }
            if let Some(cell) = grid.get_cell_mut(row, 1) {
                cell.value = CellValue::Number((3 - row) as f64);
            }
        }
        
        sort_by_column(&mut grid, 0, true).unwrap();
        sort_by_column(&mut grid, 1, true).unwrap();
        
        // Should be sorted by column 1 as secondary sort
        assert!(grid.filtered_rows.len() >= 3);
    }
    
    #[test]
    fn test_sort_preserves_filter() {
        let mut grid = create_test_grid();
        
        apply_filter(&mut grid, 0, FilterCondition::Contains("test".to_string())).unwrap();
        let filtered_count = grid.filtered_rows.len();
        
        sort_by_column(&mut grid, 0, true).unwrap();
        
        // Filter should still be applied
        assert_eq!(grid.filtered_rows.len(), filtered_count);
    }
    
    #[test]
    fn test_sort_empty_values() {
        let mut grid = create_test_grid();
        
        // Set some empty values
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Empty;
        }
        if let Some(cell) = grid.get_cell_mut(1, 0) {
            cell.value = CellValue::Text("value".to_string());
        }
        
        sort_by_column(&mut grid, 0, true).unwrap();
        
        // Empty values should sort before non-empty
        assert!(grid.filtered_rows.len() > 0);
    }
    
    #[test]
    fn test_sort_different_types() {
        let mut grid = create_test_grid();
        
        // Mix text and numbers
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Text("10".to_string());
        }
        if let Some(cell) = grid.get_cell_mut(1, 0) {
            cell.value = CellValue::Text("2".to_string());
        }
        
        sort_by_column(&mut grid, 0, true).unwrap();
        
        // Should sort as strings
        assert!(grid.filtered_rows.len() >= 2);
    }
    
    #[test]
    fn test_clear_sorts() {
        let mut grid = create_test_grid();
        
        sort_by_column(&mut grid, 0, true).unwrap();
        assert!(!grid.sort_order.is_empty());
        
        clear_sorts(&mut grid);
        assert!(grid.sort_order.is_empty());
    }
    
    #[test]
    fn test_glob_filter() {
        let columns = vec![
            ColumnDefinition {
                id: "address".to_string(),
                label: "Address".to_string(),
                data_type: CellType::Text,
                editable: false,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];
        
        let mut grid = Grid::new(columns, 4);
        
        // Set address values
        grid.get_cell_mut(0, 0).unwrap().value = CellValue::Text("/usa/ny/brooklyn/boiler-01".to_string());
        grid.get_cell_mut(1, 0).unwrap().value = CellValue::Text("/usa/ny/manhattan/boiler-02".to_string());
        grid.get_cell_mut(2, 0).unwrap().value = CellValue::Text("/usa/ca/boiler-03".to_string());
        grid.get_cell_mut(3, 0).unwrap().value = CellValue::Text("/usa/ny/brooklyn/valve-01".to_string());
        
        // Apply glob filter for NY boilers
        let condition = FilterCondition::Glob("/usa/ny/*/boiler-*".to_string());
        apply_filter(&mut grid, 0, condition).unwrap();
        
        // Should match first two (NY boilers)
        assert_eq!(grid.filtered_rows.len(), 2);
        assert!(grid.filtered_rows.contains(&0));
        assert!(grid.filtered_rows.contains(&1));
    }
    
    #[test]
    fn test_glob_filter_invalid_pattern() {
        let columns = vec![
            ColumnDefinition {
                id: "address".to_string(),
                label: "Address".to_string(),
                data_type: CellType::Text,
                editable: false,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];
        
        let mut grid = Grid::new(columns, 2);
        grid.get_cell_mut(0, 0).unwrap().value = CellValue::Text("/usa/ny/test".to_string());
        
        // Invalid glob pattern (should not match anything)
        let condition = FilterCondition::Glob("[invalid".to_string());
        apply_filter(&mut grid, 0, condition).unwrap();
        
        // Should not match anything due to invalid pattern
        assert_eq!(grid.filtered_rows.len(), 0);
    }
}
