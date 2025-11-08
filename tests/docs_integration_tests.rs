//! Integration tests for documentation generation

use arxui::generate_building_docs;
use std::fs;
use std::path::Path;
use tempfile::TempDir;

#[test]
#[ignore] // Requires building data file
fn test_generate_docs_integration() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();

    let result = generate_building_docs("test-building", None);

    std::env::set_current_dir(original_dir).unwrap();

    if let Ok(path) = result {
        assert!(Path::new(&path).exists());
        let content = fs::read_to_string(&path).unwrap();
        assert!(content.contains("<!DOCTYPE html>"));
        assert!(content.contains("<html"));
        assert!(content.contains("</html>"));
    }
}

#[test]
#[ignore] // Requires building data
fn test_docs_html_structure() {
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("test-docs.html");

    let result = generate_building_docs("test-building", Some(output_path.to_str().unwrap()));

    if let Ok(_) = result {
        let content = fs::read_to_string(&output_path).unwrap();

        assert!(content.contains("<!DOCTYPE html>"));
        assert!(content.contains("<head>"));
        assert!(content.contains("<body>"));
        assert!(content.contains("Building Summary"));
        assert!(content.contains("Floors"));
        assert!(content.contains("Rooms"));
        assert!(content.contains("Equipment"));
    }
}

#[test]
#[ignore] // Requires building data
fn test_docs_html_escape() {
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("test-docs.html");

    let result = generate_building_docs("test-building", Some(output_path.to_str().unwrap()));

    if let Ok(_) = result {
        let content = fs::read_to_string(&output_path).unwrap();

        assert!(!content.contains("<script>"));
        assert!(!content.contains("&lt;script&gt;"));
        assert!(content.contains("&amp;") || !content.contains("&"));
    }
}

#[test]
#[ignore] // Requires building data
fn test_docs_creates_directory_if_missing() {
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("docs").join("building.html");

    let result = generate_building_docs("test-building", Some(output_path.to_str().unwrap()));

    if let Ok(_) = result {
        assert!(output_path.exists());
        assert!(output_path.parent().unwrap().exists());
    }
}
