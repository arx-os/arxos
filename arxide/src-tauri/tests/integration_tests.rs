use arxide::{ProjectData, ArxideError, test_utils::*};
use serde_json;
use std::fs;
use tempfile::TempDir;

#[tokio::test]
async fn test_project_creation() {
    let project = create_test_project();

    // Test validation
    assert!(project.validate().is_ok());
    assert_eq!(project.name, "Test Project");
    assert_eq!(project.description, "A test project for unit testing");
    assert!(!project.id.is_empty());
}

#[tokio::test]
async fn test_project_validation() {
    // Test empty name
    let mut project = create_test_project();
    project.name = "".to_string();
    assert!(project.validate().is_err());

    // Test long description
    project.name = "Valid Name".to_string();
    project.description = "a".repeat(1001);
    assert!(project.validate().is_err());

    // Test valid project
    project.description = "Valid description".to_string();
    assert!(project.validate().is_ok());
}

#[tokio::test]
async fn test_project_serialization() {
    let project = create_test_project();

    // Test serialization
    let json = serde_json::to_string(&project).expect("Failed to serialize project");
    assert!(json.contains("Test Project"));

    // Test deserialization
    let deserialized: ProjectData = serde_json::from_str(&json).expect("Failed to deserialize project");
    assert_eq!(deserialized.name, project.name);
    assert_eq!(deserialized.description, project.description);
    assert_eq!(deserialized.id, project.id);
}

#[tokio::test]
async fn test_file_operations() {
    let temp_dir = create_temp_dir();
    let test_file = create_test_file_path(&temp_dir, "test.txt");
    let content = "Hello, ArxIDE!";

    // Test write file
    let result = arxide::commands::write_file(test_file.to_string_lossy().to_string(), content.to_string()).await;
    assert!(result.is_ok());

    // Test read file
    let result = arxide::commands::read_file(test_file.to_string_lossy().to_string()).await;
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), content);

    // Test read non-existent file
    let result = arxide::commands::read_file("non_existent_file.txt".to_string()).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_system_info() {
    let result = arxide::commands::get_system_info().await;
    assert!(result.is_ok());

    let info = result.unwrap();
    assert!(info.contains_key("platform"));
    assert!(info.contains_key("arch"));
    assert!(info.contains_key("app_version"));
}

#[tokio::test]
async fn test_greet_command() {
    // Test valid name
    let result = arxide::commands::greet("John".to_string()).await;
    assert!(result.is_ok());
    assert!(result.unwrap().contains("Hello, John!"));

    // Test empty name
    let result = arxide::commands::greet("".to_string()).await;
    assert!(result.is_err());

    // Test whitespace name
    let result = arxide::commands::greet("   ".to_string()).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_project_export_formats() {
    let project = create_test_project();

    // Test SVGX export
    let result = arxide::commands::export_to_svgx(project.clone()).await;
    assert!(result.is_ok());
    let svgx_content = result.unwrap();
    assert!(svgx_content.contains("version"));
    assert!(svgx_content.contains(&project.id));

    // Test DXF export
    let result = arxide::commands::export_to_dxf(project.clone()).await;
    assert!(result.is_ok());
    let dxf_content = result.unwrap();
    assert!(dxf_content.contains("SECTION"));
    assert!(dxf_content.contains("EOF"));

    // Test IFC export
    let result = arxide::commands::export_to_ifc(project).await;
    assert!(result.is_ok());
    let ifc_content = result.unwrap();
    assert!(ifc_content.contains("ISO-10303-21"));
    assert!(ifc_content.contains("ENDSEC"));
}

#[tokio::test]
async fn test_file_watching() {
    let temp_dir = create_temp_dir();
    let test_file = create_test_file_path(&temp_dir, "watch_test.txt");

    // Create a test file
    fs::write(&test_file, "test content").expect("Failed to create test file");

    // Test watch file
    let result = arxide::commands::watch_file(test_file.to_string_lossy().to_string()).await;
    assert!(result.is_ok());

    // Test watch non-existent file
    let result = arxide::commands::watch_file("non_existent_file.txt".to_string()).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_error_handling() {
    // Test file operations with invalid paths
    let result = arxide::commands::read_file("".to_string()).await;
    assert!(result.is_err());

    let result = arxide::commands::write_file("".to_string(), "content".to_string()).await;
    assert!(result.is_err());

    // Test project operations with invalid data
    let mut invalid_project = create_test_project();
    invalid_project.name = "".to_string();

    let result = arxide::commands::export_to_svgx(invalid_project.clone()).await;
    assert!(result.is_err());

    let result = arxide::commands::export_to_dxf(invalid_project.clone()).await;
    assert!(result.is_err());

    let result = arxide::commands::export_to_ifc(invalid_project).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_project_persistence() {
    let temp_dir = create_temp_dir();
    let project_file = create_test_file_path(&temp_dir, "test_project.json");

    let project = create_test_project();

    // Test save project
    let result = arxide::commands::save_project(project.clone(), project_file.to_string_lossy().to_string()).await;
    assert!(result.is_ok());

    // Test open project
    let result = arxide::commands::open_project(project_file.to_string_lossy().to_string()).await;
    assert!(result.is_ok());

    let opened_project = result.unwrap();
    assert_eq!(opened_project.name, project.name);
    assert_eq!(opened_project.description, project.description);
    assert_eq!(opened_project.id, project.id);
}

#[tokio::test]
async fn test_application_initialization() {
    // Test initialization
    let result = arxide::commands::initialize_arxide().await;
    assert!(result.is_ok());

    // Test get recent projects
    let result = arxide::commands::get_recent_projects().await;
    assert!(result.is_ok());
    let projects = result.unwrap();
    assert!(projects.is_empty()); // Should be empty initially
}

#[tokio::test]
async fn test_project_creation_and_management() {
    // Test create project
    let result = arxide::commands::create_project(
        "Test Project".to_string(),
        "Test Description".to_string()
    ).await;
    assert!(result.is_ok());

    let created_project = result.unwrap();
    assert_eq!(created_project.name, "Test Project");
    assert_eq!(created_project.description, "Test Description");
    assert!(!created_project.id.is_empty());

    // Test that project was added to recent projects
    let result = arxide::commands::get_recent_projects().await;
    assert!(result.is_ok());
    let projects = result.unwrap();
    assert!(!projects.is_empty());
    assert_eq!(projects[0].name, "Test Project");
}
