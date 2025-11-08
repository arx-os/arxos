//! Spreadsheet TUI Module
//!
//! Provides Excel-like spreadsheet interface for viewing and editing building data.

pub mod clipboard;
pub mod data_source;
pub mod editor;
pub mod export;
pub mod filter_sort;
pub mod grid;
pub mod import;
pub mod navigation;
pub mod render;
pub mod save_state;
pub mod search;
pub mod types;
pub mod undo_redo;
pub mod validation;
pub mod workflow;

// Re-export commonly used types
pub use clipboard::Clipboard;
pub use save_state::{AutoSaveManager, SaveState};
pub use search::SearchState;
pub use types::{
    Cell, CellType, CellValue, ColumnDefinition, FilterCondition, Grid, SortOrder, ValidationRule,
};
pub use workflow::{ConflictDetector, FileLock, WorkflowStatus};
