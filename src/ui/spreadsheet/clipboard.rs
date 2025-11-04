//! Clipboard functionality for copy/paste
//!
//! Handles copying and pasting cell data

use crate::ui::spreadsheet::types::CellValue;

/// Clipboard for spreadsheet
pub struct Clipboard {
    pub cells: Vec<Vec<CellValue>>,
}

impl Clipboard {
    /// Create new empty clipboard
    pub fn new() -> Self {
        Self {
            cells: Vec::new(),
        }
    }
    
    /// Copy single cell
    pub fn copy_cell(&mut self, value: CellValue) {
        self.cells = vec![vec![value]];
    }
    
    /// Copy range of cells
    pub fn copy_range(&mut self, cells: Vec<Vec<CellValue>>) {
        self.cells = cells;
    }
    
    /// Check if clipboard has data
    pub fn has_data(&self) -> bool {
        !self.cells.is_empty()
    }
    
    /// Get clipboard dimensions
    pub fn dimensions(&self) -> (usize, usize) {
        if self.cells.is_empty() {
            (0, 0)
        } else {
            (self.cells.len(), self.cells[0].len())
        }
    }
    
    /// Get cell at position
    pub fn get_cell(&self, row: usize, col: usize) -> Option<&CellValue> {
        self.cells.get(row)?.get(col)
    }
}

impl Default for Clipboard {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_clipboard_copy_cell() {
        let mut clipboard = Clipboard::new();
        
        clipboard.copy_cell(CellValue::Text("test".to_string()));
        
        assert!(clipboard.has_data());
        assert_eq!(clipboard.dimensions(), (1, 1));
    }
    
    #[test]
    fn test_clipboard_copy_range() {
        let mut clipboard = Clipboard::new();
        
        let cells = vec![
            vec![CellValue::Text("a".to_string()), CellValue::Text("b".to_string())],
            vec![CellValue::Text("c".to_string()), CellValue::Text("d".to_string())],
        ];
        
        clipboard.copy_range(cells);
        
        assert!(clipboard.has_data());
        assert_eq!(clipboard.dimensions(), (2, 2));
    }
    
    #[test]
    fn test_clipboard_has_data() {
        let clipboard = Clipboard::new();
        
        assert!(!clipboard.has_data());
    }
    
    #[test]
    fn test_clipboard_dimensions() {
        let mut clipboard = Clipboard::new();
        
        assert_eq!(clipboard.dimensions(), (0, 0));
        
        clipboard.copy_cell(CellValue::Text("test".to_string()));
        assert_eq!(clipboard.dimensions(), (1, 1));
    }
    
    #[test]
    fn test_clipboard_get_cell() {
        let mut clipboard = Clipboard::new();
        
        clipboard.copy_cell(CellValue::Text("test".to_string()));
        
        assert_eq!(clipboard.get_cell(0, 0), Some(&CellValue::Text("test".to_string())));
        assert_eq!(clipboard.get_cell(1, 0), None);
    }
}

