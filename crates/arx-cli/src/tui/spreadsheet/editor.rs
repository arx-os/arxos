//! Cell editing functionality
//!
//! Handles inline cell editing and input handling

use super::types::{CellValue, ColumnDefinition};
use crossterm::event::KeyEvent;

/// Cell editor state
pub enum EditState {
    Navigation,
    Editing,
    Validating,
    Error(String),
}

/// Cell editor
pub struct CellEditor {
    pub original_value: String,
    pub current_value: String,
    pub cursor_position: usize,
    pub column: ColumnDefinition,
    pub state: EditState,
}

impl CellEditor {
    pub fn new(column: ColumnDefinition, initial_value: CellValue) -> Self {
        let value_str = initial_value.to_string();
        Self {
            original_value: value_str.clone(),
            current_value: value_str,
            cursor_position: 0,
            column,
            state: EditState::Editing,
        }
    }

    pub fn handle_key(&mut self, key: KeyEvent) -> EditorAction {
        match key.code {
            crossterm::event::KeyCode::Char(c) => {
                self.insert_char(c);
                EditorAction::Continue
            }
            crossterm::event::KeyCode::Backspace => {
                self.delete_char();
                EditorAction::Continue
            }
            crossterm::event::KeyCode::Delete => {
                self.delete_char_at_cursor();
                EditorAction::Continue
            }
            crossterm::event::KeyCode::Enter => EditorAction::ValidateAndApply,
            crossterm::event::KeyCode::Esc => EditorAction::Cancel,
            crossterm::event::KeyCode::Left => {
                self.move_cursor_left();
                EditorAction::Continue
            }
            crossterm::event::KeyCode::Right => {
                self.move_cursor_right();
                EditorAction::Continue
            }
            crossterm::event::KeyCode::Home => {
                self.move_cursor_to_start();
                EditorAction::Continue
            }
            crossterm::event::KeyCode::End => {
                self.move_cursor_to_end();
                EditorAction::Continue
            }
            _ => EditorAction::Continue,
        }
    }

    fn insert_char(&mut self, c: char) {
        self.current_value.insert(self.cursor_position, c);
        self.cursor_position += 1;
    }

    fn delete_char(&mut self) {
        if self.cursor_position > 0 {
            self.cursor_position -= 1;
            self.current_value.remove(self.cursor_position);
        }
    }

    fn move_cursor_left(&mut self) {
        if self.cursor_position > 0 {
            self.cursor_position -= 1;
        }
    }

    fn move_cursor_right(&mut self) {
        if self.cursor_position < self.current_value.len() {
            self.cursor_position += 1;
        }
    }

    fn delete_char_at_cursor(&mut self) {
        if self.cursor_position < self.current_value.len() {
            self.current_value.remove(self.cursor_position);
        }
    }

    fn move_cursor_to_start(&mut self) {
        self.cursor_position = 0;
    }

    fn move_cursor_to_end(&mut self) {
        self.cursor_position = self.current_value.len();
    }

    pub fn has_changes(&self) -> bool {
        self.current_value != self.original_value
    }

    pub fn get_current_value(&self) -> &str {
        &self.current_value
    }

    pub fn reset_cursor(&mut self) {
        self.cursor_position = self.current_value.len();
    }
}

/// Editor action result
pub enum EditorAction {
    Continue,
    ValidateAndApply,
    Cancel,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tui::spreadsheet::types::{CellType, CellValue};
    use crossterm::event::{KeyCode, KeyModifiers};

    fn create_test_editor() -> CellEditor {
        let column = ColumnDefinition {
            id: "test".to_string(),
            label: "Test".to_string(),
            data_type: CellType::Text,
            editable: true,
            width: None,
            validation: None,
            enum_values: None,
        };

        CellEditor::new(column, CellValue::Text("initial".to_string()))
    }

    #[test]
    fn test_editor_initialization() {
        let editor = create_test_editor();

        assert_eq!(editor.original_value, "initial");
        assert_eq!(editor.current_value, "initial");
        assert_eq!(editor.cursor_position, 0);
    }

    #[test]
    fn test_editor_insert_char() {
        let mut editor = create_test_editor();
        editor.reset_cursor(); // Move to end

        let key = KeyEvent {
            code: KeyCode::Char('x'),
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(key);

        assert_eq!(editor.current_value, "initialx");
    }

    #[test]
    fn test_editor_backspace() {
        let mut editor = create_test_editor();
        editor.reset_cursor(); // Move to end

        let key = KeyEvent {
            code: KeyCode::Backspace,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(key);

        assert_eq!(editor.current_value, "initia");
    }

    #[test]
    fn test_editor_delete() {
        let mut editor = create_test_editor();
        editor.cursor_position = 3; // Position 3 in "initial" is 't' (i=0, n=1, i=2, t=3)

        let key = KeyEvent {
            code: KeyCode::Delete,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(key);

        // Deleting 't' at position 3 should give "iniial"
        assert_eq!(editor.current_value, "iniial");
    }

    #[test]
    fn test_editor_cursor_movement() {
        let mut editor = create_test_editor();
        editor.reset_cursor(); // Move to end

        let left_key = KeyEvent {
            code: KeyCode::Left,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(left_key);
        assert!(editor.cursor_position < editor.current_value.len());

        let right_key = KeyEvent {
            code: KeyCode::Right,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(right_key);
        assert_eq!(editor.cursor_position, editor.current_value.len());
    }

    #[test]
    fn test_editor_cursor_home_end() {
        let mut editor = create_test_editor();
        editor.reset_cursor(); // Move to end

        let home_key = KeyEvent {
            code: KeyCode::Home,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(home_key);
        assert_eq!(editor.cursor_position, 0);

        let end_key = KeyEvent {
            code: KeyCode::End,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(end_key);
        assert_eq!(editor.cursor_position, editor.current_value.len());
    }

    #[test]
    fn test_editor_has_changes() {
        let mut editor = create_test_editor();

        assert!(!editor.has_changes());

        let key = KeyEvent {
            code: KeyCode::Char('x'),
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        editor.handle_key(key);
        assert!(editor.has_changes());
    }

    #[test]
    fn test_editor_get_current_value() {
        let editor = create_test_editor();

        assert_eq!(editor.get_current_value(), "initial");
    }

    #[test]
    fn test_editor_escape_cancels() {
        let mut editor = create_test_editor();

        let key = KeyEvent {
            code: KeyCode::Esc,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        let action = editor.handle_key(key);
        assert!(matches!(action, EditorAction::Cancel));
    }

    #[test]
    fn test_editor_enter_applies() {
        let mut editor = create_test_editor();

        let key = KeyEvent {
            code: KeyCode::Enter,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        };

        let action = editor.handle_key(key);
        assert!(matches!(action, EditorAction::ValidateAndApply));
    }

    #[test]
    fn test_editor_reset_cursor() {
        let mut editor = create_test_editor();
        editor.cursor_position = 0;

        editor.reset_cursor();

        assert_eq!(editor.cursor_position, editor.current_value.len());
    }
}
