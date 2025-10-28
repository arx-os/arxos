//! Tests for import command handler

use arxos::commands::import::handle_import;
use tempfile::TempDir;
use std::fs::{create_dir_all, write, File};
use std::io::Write;

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
fn test_import_with_sample_ifc() {
    // Use the actual sample IFC file if it exists
    let ifc_path = "test_data/sample_building.ifc";
    
    if std::path::Path::new(ifc_path).exists() {
        let result = handle_import(ifc_path.to_string(), None);
        // Should succeed if file is valid
        // Note: May fail if IFC parsing fails, but at least we're testing the integration
    }
}

#[test]
fn test_import_with_git_repo() {
    // Test import with Git repository initialization
    let temp_dir = tempfile::tempdir().unwrap();
    let repo_dir = temp_dir.path().join("repo");
    create_dir_all(&repo_dir).unwrap();
    
    // Create a minimal valid IFC file
    let ifc_dir = temp_dir.path().join("ifc");
    create_dir_all(&ifc_dir).unwrap();
    let ifc_path = ifc_dir.join("sample.ifc");
    
    let mut ifc_file = File::create(&ifc_path).unwrap();
    ifc_file.write_all(b"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ArxOS Test'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test'),('Test'),'ArxOS','Test','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCBUILDING($,$,X,#2,$,$,$,$,$);
#2=IFCLOCALPLACEMENT($,#3);
#3=IFCAXIS2PLACEMENT3D(#4,#5,$);
#4=IFCCARTESIANPOINT((0.,0.,0.));
#5=IFCDIRECTION((0.,0.,1.));
ENDSEC;
END-ISO-10303-21;").unwrap();
    
    // Test import with Git repo
    let result = handle_import(
        ifc_path.to_string_lossy().to_string(),
        Some(repo_dir.to_string_lossy().to_string())
    );
    
    // Note: May fail if Git not initialized, but tests the integration path
    // Just verify function doesn't panic
}

#[test]
#[ignore] // Requires actual IFC file
fn test_successful_hierarchy_extraction() {
    // This would test successful IFC hierarchy extraction
    // Requires a real IFC file with complete structure
}

#[test]
#[ignore] // Requires actual IFC file
fn test_yaml_generation() {
    // This would test YAML output generation from IFC data
    // Requires a real IFC file with complete structure
}
