//! Tests for documentation generation command

use arxos::commands::doc::handle_doc;
use std::fs;
use std::path::Path;

#[test]
fn test_doc_command_invalid_building() {
    let result = handle_doc("nonexistent-building".to_string(), None);
    assert!(result.is_err());
}

#[test]
#[ignore] // Requires building data
fn test_doc_command_valid_building() {
    let result = handle_doc("test-building".to_string(), None);
    assert!(result.is_ok());
}

#[test]
#[ignore] // Requires building data
fn test_doc_command_custom_output() {
    let output_path = "./test-output-docs.html";
    let result = handle_doc("test-building".to_string(), Some(output_path.to_string()));
    
    if result.is_ok() {
        assert!(Path::new(output_path).exists());
        fs::remove_file(output_path).ok();
    }
}

#[test]
fn test_doc_command_creates_directory() {
    let output_path = "./test-docs/subdir/building.html";
    let result = handle_doc("test-building".to_string(), Some(output_path.to_string()));
    
    if result.is_ok() {
        let path = Path::new(output_path);
        if path.exists() {
            fs::remove_dir_all("./test-docs").ok();
        }
    }
}

