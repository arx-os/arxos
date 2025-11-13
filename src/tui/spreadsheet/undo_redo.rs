//! Undo/Redo functionality for spreadsheet
//!
//! Provides operation history for undo/redo operations

use super::types::{CellValue, Grid};

/// Operation in history
#[derive(Debug, Clone)]
pub struct Operation {
    pub row: usize,
    pub col: usize,
    pub old_value: CellValue,
    pub new_value: CellValue,
}

/// Undo/Redo manager
pub struct UndoRedoManager {
    undo_stack: Vec<Operation>,
    redo_stack: Vec<Operation>,
    max_history: usize,
}

impl UndoRedoManager {
    /// Create a new undo/redo manager
    pub fn new(max_history: usize) -> Self {
        Self {
            undo_stack: Vec::new(),
            redo_stack: Vec::new(),
            max_history,
        }
    }

    /// Record an operation
    pub fn record_operation(
        &mut self,
        row: usize,
        col: usize,
        old_value: CellValue,
        new_value: CellValue,
    ) {
        // Clear redo stack when new operation is recorded
        self.redo_stack.clear();

        // Add to undo stack
        self.undo_stack.push(Operation {
            row,
            col,
            old_value,
            new_value,
        });

        // Limit history size
        if self.undo_stack.len() > self.max_history {
            self.undo_stack.remove(0);
        }
    }

    /// Undo last operation
    pub fn undo(&mut self, grid: &mut Grid) -> bool {
        if let Some(op) = self.undo_stack.pop() {
            // Get current value before undo (should match op.new_value)
            let _current_value = grid
                .get_cell(op.row, op.col)
                .map(|c| c.value.clone())
                .unwrap_or(CellValue::Empty);

            // Apply undo - restore old value
            if let Some(cell) = grid.get_cell_mut(op.row, op.col) {
                cell.value = op.old_value.clone();
                cell.modified = op.old_value != CellValue::Empty;
            }

            // Push to redo stack - to redo, we need to go from old_value back to new_value
            self.redo_stack.push(Operation {
                row: op.row,
                col: op.col,
                old_value: op.old_value.clone(),
                new_value: op.new_value.clone(),
            });

            true
        } else {
            false
        }
    }

    /// Redo last undone operation
    pub fn redo(&mut self, grid: &mut Grid) -> bool {
        if let Some(op) = self.redo_stack.pop() {
            // Get current value before redo
            let current_value = grid
                .get_cell(op.row, op.col)
                .map(|c| c.value.clone())
                .unwrap_or(CellValue::Empty);

            // Apply redo
            if let Some(cell) = grid.get_cell_mut(op.row, op.col) {
                cell.value = op.new_value.clone();
                cell.modified = op.new_value != CellValue::Empty;
            }

            // Push to undo stack
            self.undo_stack.push(Operation {
                row: op.row,
                col: op.col,
                old_value: current_value,
                new_value: op.new_value,
            });

            true
        } else {
            false
        }
    }

    /// Check if undo is available
    pub fn can_undo(&self) -> bool {
        !self.undo_stack.is_empty()
    }

    /// Check if redo is available
    pub fn can_redo(&self) -> bool {
        !self.redo_stack.is_empty()
    }

    /// Clear all history
    pub fn clear(&mut self) {
        self.undo_stack.clear();
        self.redo_stack.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tui::spreadsheet::types::{CellType, CellValue, ColumnDefinition, Grid};

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
    fn test_undo_operation() {
        let mut manager = UndoRedoManager::new(50);
        let mut grid = create_test_grid();

        // Record an operation
        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("new".to_string()));

        // Set the value in grid
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Text("new".to_string());
        }

        // Undo
        assert!(manager.undo(&mut grid));

        // Value should be restored
        if let Some(cell) = grid.get_cell(0, 0) {
            assert_eq!(cell.value, CellValue::Empty);
        }
    }

    #[test]
    fn test_redo_operation() {
        let mut manager = UndoRedoManager::new(50);
        let mut grid = create_test_grid();

        // Set initial value in grid
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Empty;
        }

        // Record and undo
        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("new".to_string()));
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Text("new".to_string());
        }
        manager.undo(&mut grid);

        // Verify undo worked
        if let Some(cell) = grid.get_cell(0, 0) {
            assert_eq!(cell.value, CellValue::Empty);
        }

        // Redo
        assert!(manager.redo(&mut grid));

        // Value should be restored
        if let Some(cell) = grid.get_cell(0, 0) {
            assert_eq!(cell.value, CellValue::Text("new".to_string()));
        }
    }

    #[test]
    fn test_undo_multiple() {
        let mut manager = UndoRedoManager::new(50);
        let mut grid = create_test_grid();

        // Record multiple operations
        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("first".to_string()));
        manager.record_operation(
            1,
            0,
            CellValue::Empty,
            CellValue::Text("second".to_string()),
        );

        // Undo twice
        assert!(manager.undo(&mut grid));
        assert!(manager.undo(&mut grid));

        // Both should be undone
        assert!(!manager.can_undo());
    }

    #[test]
    fn test_redo_multiple() {
        let mut manager = UndoRedoManager::new(50);
        let mut grid = create_test_grid();

        // Record, undo twice, then redo twice
        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("first".to_string()));
        manager.record_operation(
            1,
            0,
            CellValue::Empty,
            CellValue::Text("second".to_string()),
        );

        manager.undo(&mut grid);
        manager.undo(&mut grid);

        assert!(manager.redo(&mut grid));
        assert!(manager.redo(&mut grid));

        assert!(!manager.can_redo());
    }

    #[test]
    fn test_undo_history_limit() {
        let mut manager = UndoRedoManager::new(3);

        // Record 5 operations
        for i in 0..5 {
            manager.record_operation(i, 0, CellValue::Empty, CellValue::Text(format!("{}", i)));
        }

        // Should only keep last 3
        assert_eq!(manager.undo_stack.len(), 3);
    }

    #[test]
    fn test_undo_after_edit_clears_redo() {
        let mut manager = UndoRedoManager::new(50);
        let mut grid = create_test_grid();

        // Record, undo, then record new operation
        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("first".to_string()));
        manager.undo(&mut grid);

        assert!(manager.can_redo());

        manager.record_operation(
            0,
            0,
            CellValue::Empty,
            CellValue::Text("second".to_string()),
        );

        // Redo should be cleared
        assert!(!manager.can_redo());
    }

    #[test]
    fn test_undo_applies_to_grid() {
        let mut manager = UndoRedoManager::new(50);
        let mut grid = create_test_grid();

        // Set initial value
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Text("old".to_string());
        }

        // Record change
        manager.record_operation(
            0,
            0,
            CellValue::Text("old".to_string()),
            CellValue::Text("new".to_string()),
        );

        // Set new value
        if let Some(cell) = grid.get_cell_mut(0, 0) {
            cell.value = CellValue::Text("new".to_string());
        }

        // Undo
        manager.undo(&mut grid);

        // Grid should be updated
        if let Some(cell) = grid.get_cell(0, 0) {
            assert_eq!(cell.value, CellValue::Text("old".to_string()));
        }
    }

    #[test]
    fn test_can_undo() {
        let mut manager = UndoRedoManager::new(50);

        assert!(!manager.can_undo());

        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("test".to_string()));

        assert!(manager.can_undo());
    }

    #[test]
    fn test_can_redo() {
        let mut manager = UndoRedoManager::new(50);
        let mut grid = create_test_grid();

        assert!(!manager.can_redo());

        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("test".to_string()));
        manager.undo(&mut grid);

        assert!(manager.can_redo());
    }

    #[test]
    fn test_clear() {
        let mut manager = UndoRedoManager::new(50);

        manager.record_operation(0, 0, CellValue::Empty, CellValue::Text("test".to_string()));
        manager.clear();

        assert!(!manager.can_undo());
        assert!(!manager.can_redo());
    }
}
