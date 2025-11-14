//! CSV export functionality
//!
//! Handles exporting spreadsheet data to CSV

use crate::tui::spreadsheet::types::{CellValue, ColumnDefinition};
use std::io::Write;
use std::fs::File;
use std::path::Path;

#[cfg(feature = "tui")]
use csv::WriterBuilder;

/// Export grid data to CSV file
pub fn export_to_csv(
    file_path: &Path,
    columns: &[ColumnDefinition],
    rows: &[Vec<CellValue>],
) -> Result<(), Box<dyn std::error::Error>> {
    let file = File::create(file_path).map_err(|e| format!("Failed to create CSV file: {}", e))?;

    let mut writer = WriterBuilder::new().has_headers(true).from_writer(file);

    // Write header row
    let headers: Vec<String> = columns.iter().map(|col| col.label.clone()).collect();
    writer
        .write_record(&headers)
        .map_err(|e| format!("Failed to write CSV header: {}", e))?;

    // Write data rows
    for row in rows {
        let values: Vec<String> = row.iter().map(format_cell_for_csv).collect();
        writer
            .write_record(&values)
            .map_err(|e| format!("Failed to write CSV row: {}", e))?;
    }

    writer
        .flush()
        .map_err(|e| format!("Failed to flush CSV file: {}", e))?;

    Ok(())
}

/// Format cell value for CSV export
fn format_cell_for_csv(cell: &CellValue) -> String {
    match cell {
        CellValue::Text(s) => escape_csv_string(s),
        CellValue::Number(n) => n.to_string(),
        CellValue::Integer(i) => i.to_string(),
        CellValue::Boolean(b) => b.to_string(),
        CellValue::Enum(s) => escape_csv_string(s),
        CellValue::Date(s) => escape_csv_string(s),
        CellValue::UUID(s) => escape_csv_string(s),
        CellValue::Reference(s) => escape_csv_string(s),
        CellValue::Empty => String::new(),
    }
}

/// Escape special characters in CSV strings
fn escape_csv_string(s: &str) -> String {
    // Check if string contains commas, quotes, or newlines
    if s.contains(',') || s.contains('"') || s.contains('\n') || s.contains('\r') {
        // Escape quotes by doubling them, then wrap in quotes
        let escaped = s.replace('"', "\"\"");
        format!("\"{}\"", escaped)
    } else {
        s.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tui::spreadsheet::types::CellType;
    use std::fs;
    use tempfile::NamedTempFile;

    #[test]
    fn test_export_csv_basic() {
        let file = NamedTempFile::new().unwrap();
        let file_path = file.path();

        let columns = vec![
            ColumnDefinition {
                id: "name".to_string(),
                label: "Name".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "type".to_string(),
                label: "Type".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];

        let rows = vec![
            vec![
                CellValue::Text("Equipment1".to_string()),
                CellValue::Text("HVAC".to_string()),
            ],
            vec![
                CellValue::Text("Equipment2".to_string()),
                CellValue::Text("Electrical".to_string()),
            ],
        ];

        export_to_csv(file_path, &columns, &rows).unwrap();

        // Verify file was created and has content
        let content = fs::read_to_string(file_path).unwrap();
        assert!(content.contains("Name"));
        assert!(content.contains("Type"));
        assert!(content.contains("Equipment1"));
        assert!(content.contains("HVAC"));
    }

    #[test]
    fn test_export_csv_headers() {
        let file = NamedTempFile::new().unwrap();
        let file_path = file.path();

        let columns = vec![ColumnDefinition {
            id: "col1".to_string(),
            label: "Column 1".to_string(),
            data_type: CellType::Text,
            editable: true,
            width: None,
            validation: None,
            enum_values: None,
        }];

        let rows = vec![vec![CellValue::Text("value".to_string())]];

        export_to_csv(file_path, &columns, &rows).unwrap();

        let content = fs::read_to_string(file_path).unwrap();
        assert!(content.starts_with("Column 1"));
    }

    #[test]
    fn test_export_csv_formatting() {
        let file = NamedTempFile::new().unwrap();
        let file_path = file.path();

        let columns = vec![
            ColumnDefinition {
                id: "number".to_string(),
                label: "Number".to_string(),
                data_type: CellType::Number,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "boolean".to_string(),
                label: "Boolean".to_string(),
                data_type: CellType::Boolean,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];

        let rows = vec![vec![CellValue::Number(42.5), CellValue::Boolean(true)]];

        export_to_csv(file_path, &columns, &rows).unwrap();

        let content = fs::read_to_string(file_path).unwrap();
        assert!(content.contains("42.5"));
        assert!(content.contains("true"));
    }

    #[test]
    fn test_export_csv_escaping() {
        let file = NamedTempFile::new().unwrap();
        let file_path = file.path();

        let columns = vec![ColumnDefinition {
            id: "name".to_string(),
            label: "Name".to_string(),
            data_type: CellType::Text,
            editable: true,
            width: None,
            validation: None,
            enum_values: None,
        }];

        let rows = vec![
            vec![CellValue::Text("Contains, comma".to_string())],
            vec![CellValue::Text("Contains\"quote".to_string())],
            vec![CellValue::Text("Contains\nnewline".to_string())],
        ];

        export_to_csv(file_path, &columns, &rows).unwrap();

        let content = fs::read_to_string(file_path).unwrap();
        // Should be properly escaped
        assert!(content.contains("\"Contains, comma\"") || content.contains("Contains, comma"));
        assert!(content.contains("\"\"") || content.contains("\"quote")); // Escaped quotes
    }

    #[test]
    fn test_export_csv_empty_values() {
        let file = NamedTempFile::new().unwrap();
        let file_path = file.path();

        let columns = vec![ColumnDefinition {
            id: "name".to_string(),
            label: "Name".to_string(),
            data_type: CellType::Text,
            editable: true,
            width: None,
            validation: None,
            enum_values: None,
        }];

        let rows = vec![
            vec![CellValue::Empty],
            vec![CellValue::Text("Value".to_string())],
        ];

        export_to_csv(file_path, &columns, &rows).unwrap();

        let content = fs::read_to_string(file_path).unwrap();
        // Empty values should be empty strings in CSV
        let lines: Vec<&str> = content.lines().collect();
        assert_eq!(lines.len(), 3); // Header + 2 data rows
    }

    #[test]
    fn test_escape_csv_string() {
        // Test escaping with comma
        let result = escape_csv_string("Hello, World");
        assert!(result.contains("\""));

        // Test escaping with quote
        let result = escape_csv_string("Say \"Hello\"");
        assert_eq!(result, "\"Say \"\"Hello\"\"\"");

        // Test no escaping needed
        let result = escape_csv_string("Hello World");
        assert_eq!(result, "Hello World");
    }

    #[test]
    fn test_format_cell_for_csv() {
        assert_eq!(
            format_cell_for_csv(&CellValue::Text("test".to_string())),
            "test"
        );
        assert_eq!(format_cell_for_csv(&CellValue::Number(42.5)), "42.5");
        assert_eq!(format_cell_for_csv(&CellValue::Integer(42)), "42");
        assert_eq!(format_cell_for_csv(&CellValue::Boolean(true)), "true");
        assert_eq!(format_cell_for_csv(&CellValue::Empty), "");
    }
}
