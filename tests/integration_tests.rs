// Integration tests for ArxOS IFC processing

#[cfg(test)]
mod ifc_tests {
    use std::fs;
    use arxos::ifc::IFCProcessor;
    
    #[test]
    fn test_ifc_processor_creation() {
        // Test that IFC processor can be created
        let _processor = IFCProcessor::new();
        // This should not panic
    }
    
    #[test]
    fn test_nonexistent_file_handling() {
        // Test error handling for non-existent files
        let processor = IFCProcessor::new();
        let result = processor.process_file("nonexistent.ifc");
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("IFC file not found"));
    }
    
    #[test]
    fn test_ifc_validation() {
        let processor = IFCProcessor::new();
        
        // Test valid IFC file
        let result = processor.validate_ifc_file("test_data/sample_building.ifc");
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), true);
        
        // Test non-existent file
        let result = processor.validate_ifc_file("nonexistent.ifc");
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("IFC file not found"));
        
        // Test file with wrong extension - create a temporary file
        let test_file = "test_file.txt";
        fs::write(test_file, "Some content").unwrap();
        
        let result = processor.validate_ifc_file(test_file);
        
        // Clean up
        fs::remove_file(test_file).unwrap();
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("File must have .ifc extension"));
    }
    
    #[test]
    fn test_invalid_ifc_format() {
        let processor = IFCProcessor::new();
        
        // Create temporary invalid IFC file
        let test_file = "invalid_test.ifc";
        std::fs::write(test_file, "INVALID IFC CONTENT").unwrap();
        
        let result = processor.validate_ifc_file(test_file);
        
        // Clean up
        std::fs::remove_file(test_file).unwrap();
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("Missing ISO-10303-21 header"));
    }
}

#[cfg(test)]
mod cli_tests {
    use std::process::Command;
    
    #[test]
    fn test_render_command_with_real_data() {
        // Test that render command works with real YAML data
        let output = Command::new("cargo")
            .args(&["run", "--", "render", "--building", "Floor-1", "--floor", "0"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should contain real building data
        assert!(stdout.contains("Building Floor-1"));
        assert!(stdout.contains("Floor 0"));
        assert!(stdout.contains("VAV-301"));
        assert!(stdout.contains("HVAC"));
        assert!(stdout.contains("Data Source: YAML building data"));
    }
    
    #[test]
    fn test_validate_command_yaml_files() {
        // Test that validate command works with YAML files
        let output = Command::new("cargo")
            .args(&["run", "--", "validate"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should find and validate YAML files
        assert!(stdout.contains("Validating current directory"));
        assert!(stdout.contains("Found 2 YAML file(s) to validate"));
        assert!(stdout.contains("validation passed"));
    }
    
    #[test]
    fn test_validate_command_ifc_file() {
        // Test that validate command works with IFC files
        let output = Command::new("cargo")
            .args(&["run", "--", "validate", "--path", "test_data/sample_building.ifc"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should validate IFC file successfully
        assert!(stdout.contains("Validating data at: test_data/sample_building.ifc"));
        assert!(stdout.contains("IFC file validation passed"));
    }
    
    #[test]
    fn test_validate_command_error_handling() {
        // Test error handling for non-existent files
        let output = Command::new("cargo")
            .args(&["run", "--", "validate", "--path", "nonexistent.ifc"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show proper error message
        assert!(stdout.contains("Validating data at: nonexistent.ifc"));
        assert!(stdout.contains("IFC file validation failed"));
        assert!(stdout.contains("IFC file not found"));
    }
    
    #[test]
    fn test_status_command_basic() {
        // Test that status command works in a Git repository
        let output = Command::new("cargo")
            .args(&["run", "--", "status"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show repository status
        assert!(stdout.contains("ArxOS Repository Status"));
        assert!(stdout.contains("Branch:"));
        assert!(stdout.contains("Last commit:"));
        assert!(stdout.contains("Working Directory Status:"));
    }
    
    #[test]
    fn test_status_command_verbose() {
        // Test that status command works with verbose flag
        let output = Command::new("cargo")
            .args(&["run", "--", "status", "--verbose"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show detailed information
        assert!(stdout.contains("ArxOS Repository Status"));
        assert!(stdout.contains("Recent Commits:"));
        assert!(stdout.contains("Working Directory Status:"));
    }
    
    #[test]
    fn test_status_command_outside_repo() {
        // Test status command outside a Git repository
        // Create a temporary directory without Git
        let temp_dir = tempfile::tempdir().unwrap();
        let temp_path = temp_dir.path();
        
        // Use the compiled binary directly
        let binary_path = std::env::current_dir()
            .unwrap()
            .join("target/debug/arxos");
        
        // Ensure binary exists
        if !binary_path.exists() {
            // Build the binary first
            let build_output = Command::new("cargo")
                .args(&["build"])
                .output()
                .expect("Failed to build binary");
            
            if !build_output.status.success() {
                panic!("Failed to build binary: {}", String::from_utf8_lossy(&build_output.stderr));
            }
        }
        
        let output = Command::new(&binary_path)
            .args(&["status"])
            .current_dir(temp_path)
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show appropriate error message
        assert!(stdout.contains("Not in a Git repository"));
        assert!(stdout.contains("Run 'arx import <file.ifc>' to initialize"));
        
        // temp_dir will be automatically cleaned up when it goes out of scope
    }
    
    #[test]
    fn test_diff_command_basic() {
        // Test that diff command works in a Git repository
        let output = Command::new("cargo")
            .args(&["run", "--", "diff"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show diff information
        assert!(stdout.contains("ArxOS Diff"));
        assert!(stdout.contains("Commit:"));
        assert!(stdout.contains("files changed"));
    }
    
    #[test]
    fn test_diff_command_stat() {
        // Test that diff command works with stat flag
        let output = Command::new("cargo")
            .args(&["run", "--", "diff", "--stat"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show statistics
        assert!(stdout.contains("ArxOS Diff"));
        assert!(stdout.contains("Diff Statistics:"));
        assert!(stdout.contains("Files changed:"));
        assert!(stdout.contains("Insertions:"));
        assert!(stdout.contains("Deletions:"));
    }
    
    #[test]
    fn test_diff_command_outside_repo() {
        // Test diff command outside a Git repository
        let temp_dir = tempfile::tempdir().unwrap();
        let temp_path = temp_dir.path();
        
        let binary_path = std::env::current_dir()
            .unwrap()
            .join("target/debug/arxos");
        
        // Ensure binary exists
        if !binary_path.exists() {
            // Build the binary first
            let build_output = Command::new("cargo")
                .args(&["build"])
                .output()
                .expect("Failed to build binary");
            
            if !build_output.status.success() {
                panic!("Failed to build binary: {}", String::from_utf8_lossy(&build_output.stderr));
            }
        }
        
        let output = Command::new(&binary_path)
            .args(&["diff"])
            .current_dir(temp_path)
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show appropriate error message
        assert!(stdout.contains("Not in a Git repository"));
        assert!(stdout.contains("Run 'arx import <file.ifc>' to initialize"));
        
        // temp_dir will be automatically cleaned up when it goes out of scope
    }
    
    #[test]
    fn test_history_command_basic() {
        // Test that history command works in a Git repository
        let output = Command::new("cargo")
            .args(&["run", "--", "history"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show history information
        assert!(stdout.contains("ArxOS History"));
        assert!(stdout.contains("Recent Commits"));
        assert!(stdout.contains("showing 10"));
    }
    
    #[test]
    fn test_history_command_verbose() {
        // Test that history command works with verbose flag
        let output = Command::new("cargo")
            .args(&["run", "--", "history", "--verbose", "--limit", "3"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show detailed information
        assert!(stdout.contains("ArxOS History"));
        assert!(stdout.contains("Commit #"));
        assert!(stdout.contains("Hash:"));
        assert!(stdout.contains("Author:"));
        assert!(stdout.contains("Date:"));
        assert!(stdout.contains("Message:"));
    }
    
    #[test]
    fn test_history_command_limit() {
        // Test that history command respects limit
        let output = Command::new("cargo")
            .args(&["run", "--", "history", "--limit", "5"])
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show limited number of commits
        assert!(stdout.contains("ArxOS History"));
        assert!(stdout.contains("showing 5"));
    }
    
    #[test]
    fn test_history_command_outside_repo() {
        // Test history command outside a Git repository
        let temp_dir = tempfile::tempdir().unwrap();
        let temp_path = temp_dir.path();
        
        let binary_path = std::env::current_dir()
            .unwrap()
            .join("target/debug/arxos");
        
        // Ensure binary exists
        if !binary_path.exists() {
            // Build the binary first
            let build_output = Command::new("cargo")
                .args(&["build"])
                .output()
                .expect("Failed to build binary");
            
            if !build_output.status.success() {
                panic!("Failed to build binary: {}", String::from_utf8_lossy(&build_output.stderr));
            }
        }
        
        let output = Command::new(&binary_path)
            .args(&["history"])
            .current_dir(temp_path)
            .output()
            .expect("Failed to execute command");
        
        let stdout = String::from_utf8_lossy(&output.stdout);
        
        // Should show appropriate error message
        assert!(stdout.contains("Not in a Git repository"));
        assert!(stdout.contains("Run 'arx import <file.ifc>' to initialize"));
        
        // temp_dir will be automatically cleaned up when it goes out of scope
    }
}

#[cfg(test)]
mod spatial_tests {
    use arxos::{SpatialEntity, BoundingBox3D, Point3D};
    
    #[test]
    fn test_spatial_entity_creation() {
        let entity = SpatialEntity {
            id: "test-123".to_string(),
            name: "Test Equipment".to_string(),
            entity_type: "HVAC".to_string(),
            position: Point3D::new(10.5, 8.2, 2.7),
            bounding_box: BoundingBox3D::new(
                Point3D::new(9.5, 7.2, 1.7),
                Point3D::new(11.5, 9.2, 3.7),
            ),
            coordinate_system: None,
        };
        
        assert_eq!(entity.id, "test-123");
        assert_eq!(entity.name, "Test Equipment");
        assert_eq!(entity.position.x, 10.5);
        assert_eq!(entity.position.y, 8.2);
        assert_eq!(entity.position.z, 2.7);
    }
}
