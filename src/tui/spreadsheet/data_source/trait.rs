//! SpreadsheetDataSource trait definition
//!
//! Defines the core trait for data sources that provide spreadsheet data.

use super::super::types::{CellValue, ColumnDefinition};
use std::error::Error;

/// Trait for data sources that provide spreadsheet data
///
/// This trait defines the interface for any data source that can be displayed
/// and edited in the spreadsheet interface. Implementations handle:
/// - Column definitions and metadata
/// - Cell value retrieval and updates
/// - Data persistence (save/reload)
/// - Row counting
///
/// # Examples
///
/// ```ignore
/// use crate::tui::spreadsheet::data_source::SpreadsheetDataSource;
///
/// struct MyDataSource {
///     data: Vec<MyData>,
/// }
///
/// impl SpreadsheetDataSource for MyDataSource {
///     fn columns(&self) -> Vec<ColumnDefinition> {
///         // Define columns
///     }
///
///     fn row_count(&self) -> usize {
///         self.data.len()
///     }
///
///     // ... implement other methods
/// }
/// ```
pub trait SpreadsheetDataSource: Send + Sync {
    /// Get the column definitions for this data source
    ///
    /// Returns a vector of column definitions that describe the structure
    /// of the spreadsheet, including column IDs, labels, data types,
    /// editability, and validation rules.
    fn columns(&self) -> Vec<ColumnDefinition>;

    /// Get the number of rows in this data source
    ///
    /// Returns the total count of data rows available.
    fn row_count(&self) -> usize;

    /// Get cell value at (row, col)
    ///
    /// # Arguments
    ///
    /// * `row` - Zero-based row index
    /// * `col` - Zero-based column index
    ///
    /// # Returns
    ///
    /// Returns the cell value or an error if the indices are out of bounds.
    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn Error>>;

    /// Set cell value at (row, col)
    ///
    /// # Arguments
    ///
    /// * `row` - Zero-based row index
    /// * `col` - Zero-based column index
    /// * `value` - New cell value to set
    ///
    /// # Returns
    ///
    /// Returns Ok(()) if successful, or an error if:
    /// - Indices are out of bounds
    /// - Column is read-only
    /// - Value fails validation
    fn set_cell(
        &mut self,
        row: usize,
        col: usize,
        value: CellValue,
    ) -> Result<(), Box<dyn Error>>;

    /// Save changes to building.yaml and optionally commit to Git
    ///
    /// # Arguments
    ///
    /// * `commit` - If true, create a Git commit after saving
    ///
    /// # Returns
    ///
    /// Returns Ok(()) if successful, or an error if save fails.
    fn save(&mut self, commit: bool) -> Result<(), Box<dyn Error>>;

    /// Reload data from building.yaml
    ///
    /// Discards any unsaved changes and reloads from the persistent store.
    ///
    /// # Returns
    ///
    /// Returns Ok(()) if successful, or an error if reload fails.
    fn reload(&mut self) -> Result<(), Box<dyn Error>>;
}
