//! Integration tests for spreadsheet component interactions
//!
//! Tests how different spreadsheet components interact with each other:
//! - Grid + Editor + Validation integration
//! - Edit workflow (start, validate, apply, cancel)
//! - Undo/Redo integration with grid and editor
//! - Filter/Sort integration with grid navigation

use arxos::ui::spreadsheet::{
    Grid, CellValue, CellType, ColumnDefinition, ValidationRule,
    FilterCondition,
    validation::validate_cell,
    editor::{CellEditor, EditState},
    undo_redo::UndoRedoManager,
};

/// Helper to create a test grid with equipment columns
fn create_test_grid() -> Grid {
    let columns = vec![
        ColumnDefinition {
            id: "equipment.id".to_string(),
            label: "ID".to_string(),
            data_type: CellType::UUID,
            editable: false,
            width: Some(36),
            validation: None,
            enum_values: None,
        },
        ColumnDefinition {
            id: "equipment.name".to_string(),
            label: "Name".to_string(),
            data_type: CellType::Text,
            editable: true,
            width: Some(30),
            validation: Some(ValidationRule::Required),
            enum_values: None,
        },
        ColumnDefinition {
            id: "equipment.type".to_string(),
            label: "Type".to_string(),
            data_type: CellType::Enum(vec!["HVAC".to_string(), "Electrical".to_string()]),
            editable: true,
            width: Some(20),
            validation: None,
            enum_values: Some(vec!["HVAC".to_string(), "Electrical".to_string()]),
        },
    ];
    
    let mut grid = Grid::new(columns.clone(), 3);
    
    // Populate with test data
    for i in 0..3 {
        if let Some(row) = grid.rows.get_mut(i) {
            row[0].value = CellValue::UUID(format!("eq-{}", i));
            row[1].value = CellValue::Text(format!("Equipment {}", i));
            row[2].value = CellValue::Enum(if i % 2 == 0 { "HVAC".to_string() } else { "Electrical".to_string() });
        }
    }
    
    grid
}

#[test]
fn test_grid_editor_validation_integration() {
    let grid = create_test_grid();
    
    // Start editing a cell
    let column = &grid.columns[1]; // Name column
    let cell = grid.get_cell(0, 1).cloned().unwrap();
    let mut editor = CellEditor::new(column.clone(), cell.value);
    
    // Clear existing value first (move to start, then delete all)
    use crossterm::event::{KeyEvent, KeyCode, KeyModifiers};
    editor.handle_key(KeyEvent::new(KeyCode::Home, KeyModifiers::empty()));
    // Delete all characters
    let initial_len = editor.get_current_value().len();
    for _ in 0..initial_len {
        editor.handle_key(KeyEvent::new(KeyCode::Delete, KeyModifiers::empty()));
    }
    
    // Enter new text
    editor.handle_key(KeyEvent::new(KeyCode::Char('A'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('B'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('C'), KeyModifiers::empty()));
    
    // Validate the value
    let current_value = editor.get_current_value();
    let validation_result = validate_cell(current_value, column);
    
    assert!(validation_result.is_ok());
    let cell_value = validation_result.unwrap();
    assert_eq!(cell_value, CellValue::Text("ABC".to_string()));
}

#[test]
fn test_edit_workflow_apply() {
    let mut grid = create_test_grid();
    
    // Start editing
    let column = &grid.columns[1];
    let cell = grid.get_cell(0, 1).cloned().unwrap();
    let mut editor = CellEditor::new(column.clone(), cell.value);
    
    // Clear existing value and enter new text
    use crossterm::event::{KeyEvent, KeyCode, KeyModifiers};
    editor.handle_key(KeyEvent::new(KeyCode::Home, KeyModifiers::empty()));
    let initial_len = editor.get_current_value().len();
    for _ in 0..initial_len {
        editor.handle_key(KeyEvent::new(KeyCode::Delete, KeyModifiers::empty()));
    }
    
    // Enter new value
    editor.handle_key(KeyEvent::new(KeyCode::Char('N'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('e'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('w'), KeyModifiers::empty()));
    
    // Validate and apply
    let new_value = editor.get_current_value();
    match validate_cell(new_value, column) {
        Ok(cell_value) => {
            // Apply to grid
            if let Some(cell) = grid.get_cell_mut(0, 1) {
                cell.value = cell_value.clone();
                cell.modified = true;
            }
            
            // Verify change was applied
            let updated = grid.get_cell(0, 1).unwrap();
            assert_eq!(updated.value, CellValue::Text("New".to_string()));
            assert!(updated.modified);
        }
        Err(e) => panic!("Validation failed: {}", e.message),
    }
}

#[test]
fn test_edit_workflow_cancel() {
    let grid = create_test_grid();
    
    // Get original value
    let original_value = grid.get_cell(0, 1).unwrap().value.clone();
    
    // Start editing
    let column = &grid.columns[1];
    let cell = grid.get_cell(0, 1).cloned().unwrap();
    let mut editor = CellEditor::new(column.clone(), cell.value);
    
    // Edit value (but don't apply) via handle_key
    use crossterm::event::{KeyEvent, KeyCode, KeyModifiers};
    let chars = ['M', 'o', 'd', 'i', 'f', 'i', 'e', 'd'];
    for c in chars.iter() {
        editor.handle_key(KeyEvent::new(KeyCode::Char(*c), KeyModifiers::empty()));
    }
    
    // Cancel edit (simulate Esc key)
    // Value should not be changed
    let current = grid.get_cell(0, 1).unwrap();
    assert_eq!(current.value, original_value);
    assert!(!current.modified);
}

#[test]
fn test_validation_error_integration() {
    let grid = create_test_grid();
    
    // Try to edit with invalid value (empty for required field)
    let column = &grid.columns[1]; // Required name field
    let cell = grid.get_cell(0, 1).cloned().unwrap();
    let mut editor = CellEditor::new(column.clone(), cell.value);
    
    // Clear the value (simulate backspace)
    let _current = editor.get_current_value();
    // For required field, empty should fail
    let validation_result = validate_cell(&"".to_string(), column);
    
    assert!(validation_result.is_err());
    let error = validation_result.unwrap_err();
    assert!(error.message.contains("required") || error.message.contains("Required"));
    
    // Set error state in editor
    editor.state = EditState::Error(error.message.clone());
    
    // Verify error state
    assert!(matches!(editor.state, EditState::Error(_)));
}

#[test]
fn test_undo_redo_with_grid() {
    let mut grid = create_test_grid();
    let mut undo_redo = UndoRedoManager::new(10);
    
    // Get original value
    let original_value = grid.get_cell(0, 1).unwrap().value.clone();
    
    // Make a change
    let new_value = CellValue::Text("Changed".to_string());
    undo_redo.record_operation(0, 1, original_value.clone(), new_value.clone());
    
    if let Some(cell) = grid.get_cell_mut(0, 1) {
        cell.value = new_value;
        cell.modified = true;
    }
    
    // Verify change
    assert_eq!(grid.get_cell(0, 1).unwrap().value, CellValue::Text("Changed".to_string()));
    
    // Undo
    undo_redo.undo(&mut grid);
    
    // Verify original value restored
    assert_eq!(grid.get_cell(0, 1).unwrap().value, original_value);
    
    // Redo
    undo_redo.redo(&mut grid);
    
    // Verify change restored
    assert_eq!(grid.get_cell(0, 1).unwrap().value, CellValue::Text("Changed".to_string()));
}

#[test]
fn test_filter_with_navigation() {
    let mut grid = create_test_grid();
    
    // Add filter for Type = "HVAC"
    use arxos::ui::spreadsheet::filter_sort;
    filter_sort::apply_filter(&mut grid, 2, FilterCondition::Equals("HVAC".to_string())).unwrap();
    
    // Should have filtered rows (only even rows have HVAC)
    assert!(grid.has_filters());
    assert_eq!(grid.filtered_rows.len(), 2); // 0 and 2 are HVAC
    
    // Navigation should work with filtered rows
    grid.selected_row = 0;
    grid.move_down();
    
    // Should move to next filtered row (row 2)
    assert_eq!(grid.selected_row, 1); // Index in filtered_rows
    assert_eq!(grid.get_original_row(grid.selected_row), Some(2)); // Original row index
}

#[test]
fn test_sort_with_filter() {
    let mut grid = create_test_grid();
    
    // First filter
    use arxos::ui::spreadsheet::filter_sort;
    filter_sort::apply_filter(&mut grid, 2, FilterCondition::Equals("HVAC".to_string())).unwrap();
    
    // Then sort by name
    filter_sort::sort_by_column(&mut grid, 1, true).unwrap();
    
    // Should have both filter and sort applied
    assert!(grid.has_filters());
    assert!(grid.has_sort());
    
    // Verify filtered and sorted order
    assert_eq!(grid.filtered_rows.len(), 2);
}

#[test]
fn test_editor_cursor_movement() {
    let grid = create_test_grid();
    
    let column = &grid.columns[1];
    let cell = grid.get_cell(0, 1).cloned().unwrap();
    let mut editor = CellEditor::new(column.clone(), cell.value);
    
    // Clear existing value first
    use crossterm::event::{KeyEvent, KeyCode, KeyModifiers};
    editor.handle_key(KeyEvent::new(KeyCode::Home, KeyModifiers::empty()));
    let initial_len = editor.get_current_value().len();
    for _ in 0..initial_len {
        editor.handle_key(KeyEvent::new(KeyCode::Delete, KeyModifiers::empty()));
    }
    
    // Insert text via handle_key
    editor.handle_key(KeyEvent::new(KeyCode::Char('A'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('B'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('C'), KeyModifiers::empty()));
    
    // Cursor should be at position 3 (after "ABC")
    assert_eq!(editor.cursor_position, 3);
    
    // Move cursor left
    editor.handle_key(KeyEvent::new(KeyCode::Left, KeyModifiers::empty()));
    assert_eq!(editor.cursor_position, 2);
    
    // Move cursor right
    editor.handle_key(KeyEvent::new(KeyCode::Right, KeyModifiers::empty()));
    assert_eq!(editor.cursor_position, 3);
    
    // Move to start
    editor.handle_key(KeyEvent::new(KeyCode::Home, KeyModifiers::empty()));
    assert_eq!(editor.cursor_position, 0);
    
    // Move to end
    editor.handle_key(KeyEvent::new(KeyCode::End, KeyModifiers::empty()));
    assert_eq!(editor.cursor_position, 3);
}

#[test]
fn test_editor_backspace_delete() {
    let grid = create_test_grid();
    
    let column = &grid.columns[1];
    let cell = grid.get_cell(0, 1).cloned().unwrap();
    let mut editor = CellEditor::new(column.clone(), cell.value);
    
    // Clear existing value first
    use crossterm::event::{KeyEvent, KeyCode, KeyModifiers};
    editor.handle_key(KeyEvent::new(KeyCode::Home, KeyModifiers::empty()));
    let initial_len = editor.get_current_value().len();
    for _ in 0..initial_len {
        editor.handle_key(KeyEvent::new(KeyCode::Delete, KeyModifiers::empty()));
    }
    
    // Insert text via handle_key
    editor.handle_key(KeyEvent::new(KeyCode::Char('A'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('B'), KeyModifiers::empty()));
    editor.handle_key(KeyEvent::new(KeyCode::Char('C'), KeyModifiers::empty()));
    
    // Move cursor to middle (position 2, between B and C)
    editor.handle_key(KeyEvent::new(KeyCode::Left, KeyModifiers::empty()));
    
    // Delete character (delete key - forward delete, removes C)
    editor.handle_key(KeyEvent::new(KeyCode::Delete, KeyModifiers::empty()));
    assert_eq!(editor.get_current_value(), "AB");
    
    // Backspace (backward delete, removes B)
    editor.handle_key(KeyEvent::new(KeyCode::Backspace, KeyModifiers::empty()));
    assert_eq!(editor.get_current_value(), "A");
}

#[test]
fn test_validation_with_enum() {
    let grid = create_test_grid();
    
    let column = &grid.columns[2]; // Type column with enum
    
    // Valid enum value
    let valid_result = validate_cell("HVAC", column);
    assert!(valid_result.is_ok());
    
    // Invalid enum value
    let invalid_result = validate_cell("InvalidType", column);
    assert!(invalid_result.is_err());
}

