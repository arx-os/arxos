#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use std::fs;
    use std::path::Path;

    /// Test file reading functionality
    #[tokio::test]
    async fn test_read_file() {
        let temp_dir = tempdir().unwrap();
        let test_file = temp_dir.path().join("test.svgx");
        let test_content = r#"{
            "id": "test_project",
            "name": "Test Project",
            "description": "Test project for unit testing",
            "created_at": "2024-01-01T00:00:00Z",
            "last_modified": "2024-01-01T00:00:00Z",
            "objects": [],
            "constraints": [],
            "settings": {}
        }"#;
        
        fs::write(&test_file, test_content).unwrap();
        
        let result = read_file(test_file.to_string_lossy().to_string()).await;
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), test_content);
    }

    /// Test file writing functionality
    #[tokio::test]
    async fn test_write_file() {
        let temp_dir = tempdir().unwrap();
        let test_file = temp_dir.path().join("test_write.svgx");
        let test_content = r#"{
            "id": "write_test",
            "name": "Write Test",
            "description": "Test writing functionality",
            "created_at": "2024-01-01T00:00:00Z",
            "last_modified": "2024-01-01T00:00:00Z",
            "objects": [],
            "constraints": [],
            "settings": {}
        }"#;
        
        let result = write_file(test_file.to_string_lossy().to_string(), test_content.to_string()).await;
        assert!(result.is_ok());
        
        // Verify file was written
        let read_content = fs::read_to_string(&test_file).unwrap();
        assert_eq!(read_content, test_content);
    }

    /// Test DXF export functionality
    #[tokio::test]
    async fn test_export_to_dxf() {
        let temp_dir = tempdir().unwrap();
        let test_file = temp_dir.path().join("test_export.dxf");
        
        let project_data = ProjectData {
            id: "test_export".to_string(),
            name: "Test Export".to_string(),
            description: "Test DXF export".to_string(),
            created_at: "2024-01-01T00:00:00Z".to_string(),
            last_modified: "2024-01-01T00:00:00Z".to_string(),
            objects: vec![
                serde_json::json!({
                    "type": "line",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 10.0, "y": 10.0}
                }),
                serde_json::json!({
                    "type": "circle",
                    "center": {"x": 5.0, "y": 5.0},
                    "radius": 2.0
                })
            ],
            constraints: vec![],
            settings: HashMap::new(),
        };
        
        let result = export_to_dxf(test_file.to_string_lossy().to_string(), project_data).await;
        assert!(result.is_ok());
        
        // Verify DXF file was created
        assert!(test_file.exists());
        
        // Verify DXF content
        let dxf_content = fs::read_to_string(&test_file).unwrap();
        assert!(dxf_content.contains("SECTION"));
        assert!(dxf_content.contains("ENTITIES"));
        assert!(dxf_content.contains("LINE"));
        assert!(dxf_content.contains("CIRCLE"));
        assert!(dxf_content.contains("ENDSEC"));
        assert!(dxf_content.contains("EOF"));
    }

    /// Test IFC export functionality
    #[tokio::test]
    async fn test_export_to_ifc() {
        let temp_dir = tempdir().unwrap();
        let test_file = temp_dir.path().join("test_export.ifc");
        
        let project_data = ProjectData {
            id: "test_ifc_export".to_string(),
            name: "Test IFC Export".to_string(),
            description: "Test IFC export".to_string(),
            created_at: "2024-01-01T00:00:00Z".to_string(),
            last_modified: "2024-01-01T00:00:00Z".to_string(),
            objects: vec![
                serde_json::json!({
                    "type": "line",
                    "startPoint": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "endPoint": {"x": 10.0, "y": 10.0, "z": 0.0}
                }),
                serde_json::json!({
                    "type": "circle",
                    "center": {"x": 5.0, "y": 5.0, "z": 0.0},
                    "radius": 2.0
                })
            ],
            constraints: vec![],
            settings: HashMap::new(),
        };
        
        let result = export_to_ifc(test_file.to_string_lossy().to_string(), project_data).await;
        assert!(result.is_ok());
        
        // Verify IFC file was created
        assert!(test_file.exists());
        
        // Verify IFC content
        let ifc_content = fs::read_to_string(&test_file).unwrap();
        assert!(ifc_content.contains("ISO-10303-21"));
        assert!(ifc_content.contains("HEADER"));
        assert!(ifc_content.contains("DATA"));
        assert!(ifc_content.contains("IFCCARTESIANPOINT"));
        assert!(ifc_content.contains("IFCLINE"));
        assert!(ifc_content.contains("IFCCIRCLE"));
        assert!(ifc_content.contains("ENDSEC"));
        assert!(ifc_content.contains("END-ISO-10303-21"));
    }

    /// Test PDF export functionality
    #[tokio::test]
    async fn test_export_to_pdf() {
        let temp_dir = tempdir().unwrap();
        let test_file = temp_dir.path().join("test_export.pdf");
        
        let project_data = ProjectData {
            id: "test_pdf_export".to_string(),
            name: "Test PDF Export".to_string(),
            description: "Test PDF export".to_string(),
            created_at: "2024-01-01T00:00:00Z".to_string(),
            last_modified: "2024-01-01T00:00:00Z".to_string(),
            objects: vec![
                serde_json::json!({
                    "type": "line",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 10.0, "y": 10.0}
                }),
                serde_json::json!({
                    "type": "rectangle",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 5.0, "y": 5.0}
                })
            ],
            constraints: vec![],
            settings: HashMap::new(),
        };
        
        let result = export_to_pdf(test_file.to_string_lossy().to_string(), project_data).await;
        assert!(result.is_ok());
        
        // Verify PDF file was created
        assert!(test_file.exists());
        
        // Verify PDF content
        let pdf_content = fs::read_to_string(&test_file).unwrap();
        assert!(pdf_content.contains("Test PDF Export"));
        assert!(pdf_content.contains("Objects: 2"));
        assert!(pdf_content.contains("Constraints: 0"));
    }

    /// Test system information retrieval
    #[tokio::test]
    async fn test_get_system_info() {
        let result = get_system_info().await;
        assert!(result.is_ok());
        
        let info = result.unwrap();
        assert!(info.contains_key("platform"));
        assert!(info.contains_key("arch"));
        assert!(info.contains_key("app_version"));
        
        // Verify platform is one of the expected values
        let platform = info.get("platform").unwrap();
        assert!(matches!(platform.as_str(), "macos" | "windows" | "linux"));
        
        // Verify architecture is one of the expected values
        let arch = info.get("arch").unwrap();
        assert!(matches!(arch.as_str(), "x86_64" | "aarch64" | "x86"));
    }

    /// Test batch processing functionality
    #[tokio::test]
    async fn test_batch_process_files() {
        let temp_dir = tempdir().unwrap();
        
        // Create test SVGX files
        let test_files = vec![
            temp_dir.path().join("test1.svgx"),
            temp_dir.path().join("test2.svgx"),
        ];
        
        let test_content = r#"{
            "id": "batch_test",
            "name": "Batch Test",
            "description": "Test batch processing",
            "created_at": "2024-01-01T00:00:00Z",
            "last_modified": "2024-01-01T00:00:00Z",
            "objects": [
                {
                    "type": "line",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 10.0, "y": 10.0}
                }
            ],
            "constraints": [],
            "settings": {}
        }"#;
        
        for file in &test_files {
            fs::write(file, test_content).unwrap();
        }
        
        let file_paths: Vec<String> = test_files
            .iter()
            .map(|f| f.to_string_lossy().to_string())
            .collect();
        
        // Test DXF batch export
        let result = batch_process_files(file_paths.clone(), "export_dxf".to_string()).await;
        assert!(result.is_ok());
        
        let results = result.unwrap();
        assert_eq!(results.len(), 2);
        assert!(results.iter().all(|r| r.contains("Exported")));
        
        // Verify DXF files were created
        for file in &test_files {
            let dxf_file = file.with_extension("dxf");
            assert!(dxf_file.exists());
        }
    }

    /// Test file watching functionality
    #[tokio::test]
    async fn test_file_watching() {
        let temp_dir = tempdir().unwrap();
        let test_file = temp_dir.path().join("watch_test.svgx");
        let test_content = r#"{"id": "watch_test", "name": "Watch Test"}"#;
        
        fs::write(&test_file, test_content).unwrap();
        
        // Note: This test would require more complex setup with actual window events
        // For now, we just test that the function doesn't panic
        let result = watch_file(test_file.to_string_lossy().to_string(), tauri::Window::default()).await;
        // The function might fail due to window context, but shouldn't panic
        println!("Watch file result: {:?}", result);
    }

    /// Test notification functionality
    #[tokio::test]
    async fn test_show_notification() {
        let result = show_notification("Test Title".to_string(), "Test Body".to_string()).await;
        assert!(result.is_ok());
    }

    /// Test recent files functionality
    #[tokio::test]
    async fn test_recent_files() {
        // Test getting recent files
        let recent_files = get_recent_files().await;
        assert!(recent_files.is_ok());
        
        // Test adding to recent files
        let result = add_recent_file("/test/path/file.svgx".to_string()).await;
        assert!(result.is_ok());
    }

    /// Test DXF content generation
    #[test]
    fn test_generate_dxf_content() {
        let project_data = ProjectData {
            id: "dxf_test".to_string(),
            name: "DXF Test".to_string(),
            description: "Test DXF generation".to_string(),
            created_at: "2024-01-01T00:00:00Z".to_string(),
            last_modified: "2024-01-01T00:00:00Z".to_string(),
            objects: vec![
                serde_json::json!({
                    "type": "line",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 10.0, "y": 10.0}
                }),
                serde_json::json!({
                    "type": "circle",
                    "center": {"x": 5.0, "y": 5.0},
                    "radius": 2.0
                }),
                serde_json::json!({
                    "type": "rectangle",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 5.0, "y": 5.0}
                })
            ],
            constraints: vec![],
            settings: HashMap::new(),
        };
        
        let result = generate_dxf_content(&project_data);
        assert!(result.is_ok());
        
        let dxf_content = result.unwrap();
        assert!(dxf_content.contains("SECTION"));
        assert!(dxf_content.contains("HEADER"));
        assert!(dxf_content.contains("ENTITIES"));
        assert!(dxf_content.contains("LINE"));
        assert!(dxf_content.contains("CIRCLE"));
        assert!(dxf_content.contains("POLYLINE"));
        assert!(dxf_content.contains("ENDSEC"));
        assert!(dxf_content.contains("EOF"));
    }

    /// Test IFC content generation
    #[test]
    fn test_generate_ifc_content() {
        let project_data = ProjectData {
            id: "ifc_test".to_string(),
            name: "IFC Test".to_string(),
            description: "Test IFC generation".to_string(),
            created_at: "2024-01-01T00:00:00Z".to_string(),
            last_modified: "2024-01-01T00:00:00Z".to_string(),
            objects: vec![
                serde_json::json!({
                    "type": "line",
                    "startPoint": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "endPoint": {"x": 10.0, "y": 10.0, "z": 0.0}
                }),
                serde_json::json!({
                    "type": "circle",
                    "center": {"x": 5.0, "y": 5.0, "z": 0.0},
                    "radius": 2.0
                })
            ],
            constraints: vec![],
            settings: HashMap::new(),
        };
        
        let result = generate_ifc_content(&project_data);
        assert!(result.is_ok());
        
        let ifc_content = result.unwrap();
        assert!(ifc_content.contains("ISO-10303-21"));
        assert!(ifc_content.contains("HEADER"));
        assert!(ifc_content.contains("DATA"));
        assert!(ifc_content.contains("IFCCARTESIANPOINT"));
        assert!(ifc_content.contains("IFCLINE"));
        assert!(ifc_content.contains("IFCCIRCLE"));
        assert!(ifc_content.contains("ENDSEC"));
        assert!(ifc_content.contains("END-ISO-10303-21"));
    }

    /// Test PDF content generation
    #[test]
    fn test_generate_pdf_content() {
        let project_data = ProjectData {
            id: "pdf_test".to_string(),
            name: "PDF Test".to_string(),
            description: "Test PDF generation".to_string(),
            created_at: "2024-01-01T00:00:00Z".to_string(),
            last_modified: "2024-01-01T00:00:00Z".to_string(),
            objects: vec![
                serde_json::json!({
                    "type": "line",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 10.0, "y": 10.0}
                }),
                serde_json::json!({
                    "type": "rectangle",
                    "startPoint": {"x": 0.0, "y": 0.0},
                    "endPoint": {"x": 5.0, "y": 5.0}
                })
            ],
            constraints: vec![],
            settings: HashMap::new(),
        };
        
        let result = generate_pdf_content(&project_data);
        assert!(result.is_ok());
        
        let pdf_content = result.unwrap();
        assert!(pdf_content.contains("PDF Test"));
        assert!(pdf_content.contains("Test PDF generation"));
        assert!(pdf_content.contains("Objects: 2"));
        assert!(pdf_content.contains("Constraints: 0"));
        assert!(pdf_content.contains("Type: line"));
        assert!(pdf_content.contains("Type: rectangle"));
    }

    /// Test error handling for file operations
    #[tokio::test]
    async fn test_file_operation_errors() {
        // Test reading non-existent file
        let result = read_file("/non/existent/file.svgx".to_string()).await;
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Failed to read file"));
        
        // Test writing to invalid path
        let result = write_file("/invalid/path/file.svgx".to_string(), "test".to_string()).await;
        // This might succeed if the directory can be created, or fail if permissions are denied
        // We just test that it doesn't panic
        println!("Write to invalid path result: {:?}", result);
    }

    /// Test export error handling
    #[tokio::test]
    async fn test_export_errors() {
        let project_data = ProjectData {
            id: "error_test".to_string(),
            name: "Error Test".to_string(),
            description: "Test error handling".to_string(),
            created_at: "2024-01-01T00:00:00Z".to_string(),
            last_modified: "2024-01-01T00:00:00Z".to_string(),
            objects: vec![],
            constraints: vec![],
            settings: HashMap::new(),
        };
        
        // Test exporting to invalid path
        let result = export_to_dxf("/invalid/path/test.dxf".to_string(), project_data.clone()).await;
        // This might succeed if the directory can be created, or fail if permissions are denied
        println!("Export to invalid path result: {:?}", result);
    }
} 