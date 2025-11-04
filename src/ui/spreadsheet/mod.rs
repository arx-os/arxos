//! Spreadsheet TUI Module
//!
//! Provides Excel-like spreadsheet interface for viewing and editing building data.

pub mod types;
pub mod grid;
pub mod render;
pub mod editor;
pub mod navigation;
pub mod validation;
pub mod data_source;
pub mod import;
pub mod export;
pub mod filter_sort;
pub mod workflow;
pub mod undo_redo;
pub mod save_state;
pub mod search;
pub mod clipboard;

// Re-export commonly used types
pub use types::{CellValue, CellType, ColumnDefinition, ValidationRule, Cell, Grid, FilterCondition, SortOrder};
pub use workflow::{FileLock, ConflictDetector, WorkflowStatus};
pub use save_state::{SaveState, AutoSaveManager};
pub use search::SearchState;
pub use clipboard::Clipboard;

