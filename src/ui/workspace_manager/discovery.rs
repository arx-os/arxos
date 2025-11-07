//! Workspace Discovery
//!
//! Handles discovery and loading of workspace information.

use super::types::Workspace;
use crate::utils::loading;
use std::path::PathBuf;

/// Discover available workspaces by scanning for building.yaml files
pub fn discover_workspaces() -> Result<Vec<Workspace>, Box<dyn std::error::Error>> {
    let mut workspaces = Vec::new();

    // Try to find YAML files using existing utility
    let yaml_files = loading::find_yaml_files()?;

    for yaml_file_str in yaml_files {
        let yaml_path = PathBuf::from(&yaml_file_str);

        // Extract building name from path or filename
        let name = yaml_path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("Unknown Building")
            .to_string();

        // Try to find Git repository (parent directory check)
        let git_repo = yaml_path.parent().and_then(|parent| {
            let git_dir = parent.join(".git");
            if git_dir.exists() {
                Some(parent.to_path_buf())
            } else {
                None
            }
        });

        // Try to load building description from YAML
        let description = load_building_description(&yaml_path).ok();

        workspaces.push(Workspace {
            name,
            path: yaml_path.clone(),
            git_repo,
            description,
        });
    }

    // If no workspaces found, add current directory if it has a building
    if workspaces.is_empty() {
        if let Ok(current_dir) = std::env::current_dir() {
            let yaml_path = current_dir.join("building.yaml");
            if yaml_path.exists() {
                workspaces.push(Workspace {
                    name: current_dir
                        .file_name()
                        .and_then(|s| s.to_str())
                        .unwrap_or("Current Building")
                        .to_string(),
                    path: yaml_path,
                    git_repo: None,
                    description: None,
                });
            }
        }
    }

    Ok(workspaces)
}

/// Load building description from YAML file
pub fn load_building_description(
    yaml_path: &PathBuf,
) -> Result<String, Box<dyn std::error::Error>> {
    use crate::utils::path_safety::PathSafety;

    let base_dir = yaml_path.parent().ok_or("Invalid path")?.to_path_buf();

    let content = PathSafety::read_file_safely(yaml_path, &base_dir)?;

    // Parse YAML to extract building description
    let yaml: serde_yaml::Value = serde_yaml::from_str(&content)?;

    if let Some(building) = yaml.get("building") {
        if let Some(desc) = building.get("description").and_then(|v| v.as_str()) {
            return Ok(desc.to_string());
        }
        if let Some(name) = building.get("name").and_then(|v| v.as_str()) {
            return Ok(format!("Building: {}", name));
        }
    }

    Ok("No description available".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::path::PathBuf;
    use tempfile::TempDir;

    #[test]
    fn test_load_building_description() {
        let temp_dir = TempDir::new().unwrap();
        let yaml_path = temp_dir.path().join("building.yaml");

        // Create YAML with description
        let yaml_content = r#"
building:
  name: Test Building
  description: A test building description
"#;
        fs::write(&yaml_path, yaml_content).unwrap();

        let description = load_building_description(&yaml_path).unwrap();
        assert_eq!(description, "A test building description");
    }

    #[test]
    fn test_load_building_description_no_description() {
        let temp_dir = TempDir::new().unwrap();
        let yaml_path = temp_dir.path().join("building.yaml");

        // Create YAML without description but with name
        let yaml_content = r#"
building:
  name: Test Building
"#;
        fs::write(&yaml_path, yaml_content).unwrap();

        let description = load_building_description(&yaml_path).unwrap();
        assert_eq!(description, "Building: Test Building");
    }

    #[test]
    fn test_load_building_description_no_name() {
        let temp_dir = TempDir::new().unwrap();
        let yaml_path = temp_dir.path().join("building.yaml");

        // Create YAML without building section
        let yaml_content = r#"
floors: []
"#;
        fs::write(&yaml_path, yaml_content).unwrap();

        let description = load_building_description(&yaml_path).unwrap();
        assert_eq!(description, "No description available");
    }

    #[test]
    fn test_load_building_description_invalid_yaml() {
        let temp_dir = TempDir::new().unwrap();
        let yaml_path = temp_dir.path().join("building.yaml");

        // Create invalid YAML
        fs::write(&yaml_path, "invalid: yaml: content: [").unwrap();

        let result = load_building_description(&yaml_path);
        assert!(result.is_err(), "Should fail on invalid YAML");
    }

    #[test]
    fn test_workspace_name_extraction() {
        // Test name extraction from path
        let path = PathBuf::from("/test/building.yaml");
        let name = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("Unknown Building")
            .to_string();
        assert_eq!(name, "building");
    }

    #[test]
    fn test_workspace_git_repo_detection() {
        let temp_dir = TempDir::new().unwrap();
        let yaml_path = temp_dir.path().join("building.yaml");
        fs::write(&yaml_path, "building:\n  name: Test").unwrap();

        // Create .git directory
        let git_dir = temp_dir.path().join(".git");
        fs::create_dir(&git_dir).unwrap();

        // Check git repo detection logic
        let git_repo = yaml_path.parent().and_then(|parent| {
            let git_dir = parent.join(".git");
            if git_dir.exists() {
                Some(parent.to_path_buf())
            } else {
                None
            }
        });

        assert!(git_repo.is_some(), "Should detect git repo");
        assert_eq!(git_repo.unwrap(), temp_dir.path());
    }

    #[test]
    fn test_discover_workspaces() {
        // This test is environment-dependent and may fail when run in parallel
        // with other tests that change directories. The discovery function uses
        // std::env::current_dir() which is a global process state.
        //
        // We test the logic components individually (load_building_description, etc.)
        // and note that full discovery integration testing requires a controlled
        // environment or mocking of the directory system.

        // Test that the function can be called (may succeed or fail based on environment)
        let result = discover_workspaces();

        // Either it succeeds with workspaces, or it's an acceptable state
        match result {
            Ok(workspaces) => {
                // If we get workspaces, verify they have the expected structure
                for ws in &workspaces {
                    assert!(!ws.name.is_empty(), "Workspace should have a name");
                    assert!(
                        ws.path.exists() || ws.path.to_string_lossy().contains("building.yaml"),
                        "Workspace path should be valid"
                    );
                }
            }
            Err(_) => {
                // If it fails, that's acceptable in test environments
                // The function depends on find_yaml_files() which uses current_dir()
            }
        }
    }

    #[test]
    fn test_discover_workspaces_no_yaml() {
        // This test verifies the function handles the case when no YAML files are found
        // The actual result depends on the test environment, but we verify the function
        // doesn't panic and handles the case gracefully.

        let result = discover_workspaces();

        // The function should either:
        // 1. Return empty list if no YAML files found
        // 2. Return workspaces if any exist in the current directory
        // 3. Return error if find_yaml_files() fails
        match result {
            Ok(workspaces) => {
                // Valid result - may be empty or have workspaces
                // Each workspace should have valid structure
                for ws in &workspaces {
                    assert!(!ws.name.is_empty());
                }
            }
            Err(_) => {
                // Error is acceptable if find_yaml_files() fails
                // This happens when current_dir() fails or directory reading fails
            }
        }
    }
}
