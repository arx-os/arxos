//! CSV import functionality
//!
//! Handles importing CSV files into spreadsheet

use crate::ui::spreadsheet::types::{CellValue, ColumnDefinition};
use crate::ui::spreadsheet::validation::validate_cell;
use csv::ReaderBuilder;
use std::collections::HashMap;
use std::fs::File;
use std::path::Path;

/// Import result
#[derive(Debug)]
pub struct ImportResult {
    pub rows: Vec<Vec<CellValue>>,
    pub row_count: usize,
    pub errors: Vec<ImportError>,
}

/// Import error
#[derive(Debug, Clone)]
pub struct ImportError {
    pub row: usize,
    pub column: usize,
    pub message: String,
}

/// Import CSV file and return data as rows
pub fn import_csv_file(
    file_path: &Path,
    columns: &[ColumnDefinition],
) -> Result<ImportResult, Box<dyn std::error::Error>> {
    let file = File::open(file_path).map_err(|e| format!("Failed to open CSV file: {}", e))?;

    let mut reader = ReaderBuilder::new().has_headers(true).from_reader(file);

    // Read headers and create column mapping
    let headers = reader
        .headers()
        .map_err(|e| format!("Failed to read CSV headers: {}", e))?;

    let column_map: HashMap<String, usize> = headers
        .iter()
        .enumerate()
        .map(|(idx, header)| (header.to_string(), idx))
        .collect();

    // Map CSV columns to our column definitions
    let mut column_indices: Vec<Option<usize>> = Vec::new();
    for col_def in columns {
        let csv_idx = column_map.get(&col_def.label).copied();
        column_indices.push(csv_idx);
    }

    // Read data rows
    let mut rows = Vec::new();
    let mut errors = Vec::new();
    let mut row_num = 0;

    for result in reader.records() {
        let record = result.map_err(|e| format!("Failed to read CSV record: {}", e))?;
        row_num += 1;

        let mut row = Vec::new();
        let mut col_idx = 0;

        for (csv_idx_opt, col_def) in column_indices.iter().zip(columns.iter()) {
            if let Some(csv_idx) = csv_idx_opt {
                if *csv_idx < record.len() {
                    let value_str = record.get(*csv_idx).unwrap_or("");

                    // Validate and parse
                    match validate_cell(value_str, col_def) {
                        Ok(cell_value) => {
                            row.push(cell_value);
                        }
                        Err(e) => {
                            // Use empty value on validation error, but record error
                            row.push(CellValue::Empty);
                            errors.push(ImportError {
                                row: row_num,
                                column: col_idx,
                                message: e.message,
                            });
                        }
                    }
                } else {
                    row.push(CellValue::Empty);
                }
            } else {
                // Column not found in CSV - use empty value
                row.push(CellValue::Empty);
            }
            col_idx += 1;
        }

        rows.push(row);
    }

    Ok(ImportResult {
        rows,
        row_count: row_num,
        errors,
    })
}

/// Preview CSV file (first N rows)
pub fn preview_csv_file(
    file_path: &Path,
    max_rows: usize,
) -> Result<Vec<Vec<String>>, Box<dyn std::error::Error>> {
    let file = File::open(file_path).map_err(|e| format!("Failed to open CSV file: {}", e))?;

    let mut reader = ReaderBuilder::new().has_headers(true).from_reader(file);

    let mut preview = Vec::new();

    // Read headers
    let headers = reader
        .headers()
        .map_err(|e| format!("Failed to read CSV headers: {}", e))?;
    preview.push(headers.iter().map(|s| s.to_string()).collect());

    // Read first N data rows
    for (idx, result) in reader.records().enumerate() {
        if idx >= max_rows {
            break;
        }
        let record = result.map_err(|e| format!("Failed to read CSV record: {}", e))?;
        preview.push(record.iter().map(|s| s.to_string()).collect());
    }

    Ok(preview)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::spreadsheet::types::CellType;
    use std::io::Write;
    use tempfile::NamedTempFile;

    fn create_test_csv_file(content: &str) -> NamedTempFile {
        let mut file = NamedTempFile::new().unwrap();
        write!(file, "{}", content).unwrap();
        file.flush().unwrap();
        file
    }

    #[test]
    fn test_import_csv_basic() {
        let csv_content = "Name,Type\nEquipment1,HVAC\nEquipment2,Electrical\n";
        let file = create_test_csv_file(csv_content);

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

        let result = import_csv_file(file.path(), &columns).unwrap();

        assert_eq!(result.row_count, 2);
        assert_eq!(result.rows.len(), 2);
        assert_eq!(result.errors.len(), 0);
    }

    #[test]
    fn test_import_csv_headers() {
        let csv_content = "Name,Type,Status\nEquipment1,HVAC,Active\n";
        let file = create_test_csv_file(csv_content);

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

        let result = import_csv_file(file.path(), &columns).unwrap();

        // Should map Name and Type columns correctly
        assert_eq!(result.row_count, 1);
        assert_eq!(result.rows[0].len(), 2);
    }

    #[test]
    fn test_import_csv_validation() {
        let csv_content = "Name,Number\nValid,42.5\nInvalid,not_a_number\n";
        let file = create_test_csv_file(csv_content);

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
                id: "number".to_string(),
                label: "Number".to_string(),
                data_type: CellType::Number,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];

        let result = import_csv_file(file.path(), &columns).unwrap();

        // Should have validation error for invalid number
        assert!(result.errors.len() > 0);
        assert!(result
            .errors
            .iter()
            .any(|e| e.message.contains("number") || e.message.contains("Invalid")));
    }

    #[test]
    fn test_import_csv_errors() {
        let csv_content = "Name,Type\nEquipment1,InvalidType\n";
        let file = create_test_csv_file(csv_content);

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
                data_type: CellType::Enum(vec!["HVAC".to_string(), "Electrical".to_string()]),
                editable: true,
                width: None,
                validation: None,
                enum_values: Some(vec!["HVAC".to_string(), "Electrical".to_string()]),
            },
        ];

        let result = import_csv_file(file.path(), &columns).unwrap();

        // Should have error for invalid enum value
        assert!(result.errors.len() > 0);
    }

    #[test]
    fn test_import_csv_preview() {
        let csv_content = "Name,Type\nEquipment1,HVAC\nEquipment2,Electrical\nEquipment3,AV\n";
        let file = create_test_csv_file(csv_content);

        let preview = preview_csv_file(file.path(), 2).unwrap();

        // Should have headers + 2 data rows
        assert_eq!(preview.len(), 3);
        assert_eq!(preview[0], vec!["Name".to_string(), "Type".to_string()]);
    }

    #[test]
    fn test_import_csv_special_chars() {
        let csv_content = "Name,Description\nEquipment1,\"Contains, comma\"\n";
        let file = create_test_csv_file(csv_content);

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
                id: "desc".to_string(),
                label: "Description".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: None,
                validation: None,
                enum_values: None,
            },
        ];

        let result = import_csv_file(file.path(), &columns).unwrap();

        // Should handle quoted strings with commas
        assert_eq!(result.row_count, 1);
        assert!(result.rows[0][1].to_string().contains("comma"));
    }

    #[test]
    fn test_import_csv_missing_columns() {
        let csv_content = "Name\nEquipment1\n";
        let file = create_test_csv_file(csv_content);

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

        let result = import_csv_file(file.path(), &columns).unwrap();

        // Should handle missing Type column (use empty value)
        assert_eq!(result.row_count, 1);
        assert_eq!(result.rows[0].len(), 2);
        assert_eq!(result.rows[0][1], CellValue::Empty);
    }

    #[test]
    fn test_import_csv_empty_values() {
        let csv_content = "Name,Type\n,Electrical\nEquipment2,\n";
        let file = create_test_csv_file(csv_content);

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

        let result = import_csv_file(file.path(), &columns).unwrap();

        // Should handle empty values
        assert_eq!(result.row_count, 2);
        assert_eq!(result.rows[0][0], CellValue::Text("".to_string()));
    }
}
