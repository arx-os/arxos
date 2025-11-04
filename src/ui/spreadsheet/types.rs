//! Core types for spreadsheet functionality
//!
//! Defines cell values, column definitions, validation rules, and grid structures.

use serde::{Serialize, Deserialize};

/// Cell value types
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum CellValue {
    Text(String),
    Number(f64),
    Integer(i64),
    Boolean(bool),
    Enum(String),
    Date(String),
    UUID(String),
    Reference(String),
    Empty,
}

impl CellValue {
    /// Convert to string representation for display
    pub fn to_string(&self) -> String {
        match self {
            CellValue::Text(s) => s.clone(),
            CellValue::Number(n) => n.to_string(),
            CellValue::Integer(i) => i.to_string(),
            CellValue::Boolean(b) => b.to_string(),
            CellValue::Enum(s) => s.clone(),
            CellValue::Date(s) => s.clone(),
            CellValue::UUID(s) => s.clone(),
            CellValue::Reference(s) => s.clone(),
            CellValue::Empty => String::new(),
        }
    }
    
    /// Check if value is empty
    pub fn is_empty(&self) -> bool {
        matches!(self, CellValue::Empty)
    }
}

/// Cell data types
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum CellType {
    Text,
    Number,
    Integer,
    Boolean,
    Enum(Vec<String>),
    Date,
    UUID,
    Reference,
}

/// Validation rules
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ValidationRule {
    Required,
    MinLength(usize),
    MaxLength(usize),
    MinValue(f64),
    MaxValue(f64),
    Pattern(String),
    EnumValue(Vec<String>),
    UUID,
    Reference(String),
}

/// Column definition
#[derive(Debug, Clone)]
pub struct ColumnDefinition {
    pub id: String,
    pub label: String,
    pub data_type: CellType,
    pub editable: bool,
    pub width: Option<u16>,
    pub validation: Option<ValidationRule>,
    pub enum_values: Option<Vec<String>>,
}

/// Cell structure
#[derive(Debug, Clone)]
pub struct Cell {
    pub value: CellValue,
    pub modified: bool,
    pub error: Option<String>,
    pub read_only: bool,
}

impl Cell {
    pub fn new(value: CellValue) -> Self {
        Self {
            value,
            modified: false,
            error: None,
            read_only: false,
        }
    }
    
    pub fn with_read_only(value: CellValue, read_only: bool) -> Self {
        Self {
            value,
            modified: false,
            error: None,
            read_only,
        }
    }
}

/// Filter condition
#[derive(Debug, Clone)]
pub enum FilterCondition {
    Contains(String),
    StartsWith(String),
    EndsWith(String),
    Equals(String),
    NotEquals(String),
    GreaterThan(f64),
    LessThan(f64),
    InRange(f64, f64),
    IsIn(Vec<String>),
}

/// Column filter
#[derive(Debug, Clone)]
pub struct ColumnFilter {
    pub column_idx: usize,
    pub condition: FilterCondition,
}

/// Sort order
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum SortOrder {
    Ascending,
    Descending,
}

/// Column sort
#[derive(Debug, Clone)]
pub struct ColumnSort {
    pub column_idx: usize,
    pub order: SortOrder,
}

/// Grid structure
#[derive(Debug)]
pub struct Grid {
    pub rows: Vec<Vec<Cell>>,
    pub columns: Vec<ColumnDefinition>,
    pub selected_row: usize,
    pub selected_col: usize,
    pub scroll_offset_y: usize,
    pub scroll_offset_x: usize,
    pub editing_cell: Option<(usize, usize)>, // (row, col) if editing
    pub filters: Vec<ColumnFilter>,
    pub sort_order: Vec<ColumnSort>,
    pub filtered_rows: Vec<usize>, // Original row indices after filtering
    pub original_row_count: usize, // Original row count before filtering
}

impl Grid {
    pub fn new(columns: Vec<ColumnDefinition>, row_count: usize) -> Self {
        let rows: Vec<Vec<Cell>> = (0..row_count)
            .map(|_| {
                columns.iter()
                    .map(|col| {
                        Cell::with_read_only(
                            CellValue::Empty,
                            !col.editable
                        )
                    })
                    .collect()
            })
            .collect();
        
        let original_row_count = rows.len();
        let filtered_rows: Vec<usize> = (0..original_row_count).collect();
        
        Self {
            rows,
            columns,
            selected_row: 0,
            selected_col: 0,
            scroll_offset_y: 0,
            scroll_offset_x: 0,
            editing_cell: None,
            filters: Vec::new(),
            sort_order: Vec::new(),
            filtered_rows,
            original_row_count,
        }
    }
    
    pub fn row_count(&self) -> usize {
        if self.filters.is_empty() {
            self.rows.len()
        } else {
            self.filtered_rows.len()
        }
    }
    
    /// Get original row index from filtered row index
    pub fn get_original_row(&self, filtered_row: usize) -> Option<usize> {
        self.filtered_rows.get(filtered_row).copied()
    }
    
    /// Check if grid has active filters
    pub fn has_filters(&self) -> bool {
        !self.filters.is_empty()
    }
    
    /// Check if grid has active sort
    pub fn has_sort(&self) -> bool {
        !self.sort_order.is_empty()
    }
    
    pub fn column_count(&self) -> usize {
        self.columns.len()
    }
    
    pub fn get_cell(&self, row: usize, col: usize) -> Option<&Cell> {
        self.rows.get(row)?.get(col)
    }
    
    pub fn get_cell_mut(&mut self, row: usize, col: usize) -> Option<&mut Cell> {
        self.rows.get_mut(row)?.get_mut(col)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_cell_value_to_string() {
        assert_eq!(CellValue::Text("hello".to_string()).to_string(), "hello");
        assert_eq!(CellValue::Number(42.5).to_string(), "42.5");
        assert_eq!(CellValue::Boolean(true).to_string(), "true");
        assert_eq!(CellValue::Empty.to_string(), "");
    }
    
    #[test]
    fn test_cell_value_is_empty() {
        assert!(CellValue::Empty.is_empty());
        assert!(!CellValue::Text("hello".to_string()).is_empty());
    }
    
    #[test]
    fn test_grid_new() {
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
        ];
        
        let grid = Grid::new(columns.clone(), 5);
        assert_eq!(grid.row_count(), 5);
        assert_eq!(grid.column_count(), 1);
        assert_eq!(grid.selected_row, 0);
        assert_eq!(grid.selected_col, 0);
    }
    
    #[test]
    fn test_grid_get_cell() {
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
        ];
        
        let grid = Grid::new(columns, 3);
        assert!(grid.get_cell(0, 0).is_some());
        assert!(grid.get_cell(10, 0).is_none());
        assert!(grid.get_cell(0, 10).is_none());
    }
}

