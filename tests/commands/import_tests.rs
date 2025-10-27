//! Tests for import command handler

use arxos::commands::import::handle_import;
use tempfile::TempDir;
use std::fs::{create_dir_all, write};

#[test]
fn test_import_ifc_file_not_found() {
    let temp_dir = tempfile::tempdir().unwrap();
    let ifc_path = temp_dir.path().join("nonexistent.ifc");
    
    let result = handle_import(ifc_path.to_string_lossy().to_string(), None);
    assert!(result.is_err());
    let error = result.unwrap_err();
    assert!(error.to_string().contains("not found") || error.to_string().contains("No such file"));
}

#[test]
#[ignore] // Requires actual IFC file
fn test_successful_hierarchy_extraction() {
    // This would test successful IFC hierarchy extraction
    // Requires a real IFC file
}

#[test]
#[ignore] // Requires actual IFC file
fn test_yaml_generation() {
    // This would test YAML output generation from IFC data
    // Requires a real IFC file
}

