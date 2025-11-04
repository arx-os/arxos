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
        let git_repo = yaml_path
            .parent()
            .and_then(|parent| {
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
pub fn load_building_description(yaml_path: &PathBuf) -> Result<String, Box<dyn std::error::Error>> {
    use crate::utils::path_safety::PathSafety;
    
    let base_dir = yaml_path.parent()
        .ok_or("Invalid path")?
        .to_path_buf();
    
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

