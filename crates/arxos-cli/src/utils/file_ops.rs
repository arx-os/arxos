//! # File Operations Utilities
//!
//! This module provides utilities for file operations, including
//! building data loading, YAML file validation, and Git repository detection.

use std::fs;
use std::path::Path;
use arxos_core::{BuildingData, Result as ArxResult};
use crate::error::CliError;

/// Load building data from YAML files in the current directory
///
/// # Arguments
///
/// * `building_name` - Name of the building to load
///
/// # Returns
///
/// * `Result<BuildingData, CliError>` - Loaded building data or error
///
/// # Examples
///
/// ```rust
/// use arxos_cli::utils::file_ops::load_building_data;
///
/// let building_data = load_building_data("Main Building")?;
/// ```
pub fn load_building_data(building_name: &str) -> Result<BuildingData, CliError> {
    // Look for YAML files in current directory
    let yaml_files: Vec<String> = fs::read_dir(".")
        .map_err(|e| CliError::FileOperation {
            operation: "read directory".to_string(),
            path: ".".to_string(),
            source: e,
        })?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()? == "yaml" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();

    if yaml_files.is_empty() {
        return Err(CliError::NoYamlFiles);
    }

    // Try to find a YAML file that matches the building name
    for yaml_file in &yaml_files {
        if let Ok(content) = fs::read_to_string(yaml_file) {
            if content.contains(building_name) {
                return BuildingData::from_yaml(&content)
                    .map_err(|e| CliError::YamlParse {
                        file: yaml_file.clone(),
                        source: e,
                    });
            }
        }
    }

    // If no specific match, try the first YAML file
    if let Some(first_file) = yaml_files.first() {
        let content = fs::read_to_string(first_file)
            .map_err(|e| CliError::FileOperation {
                operation: "read file".to_string(),
                path: first_file.clone(),
                source: e,
            })?;
        
        BuildingData::from_yaml(&content)
            .map_err(|e| CliError::YamlParse {
                file: first_file.clone(),
                source: e,
            })
    } else {
        Err(CliError::NoYamlFiles)
    }
}

/// Find Git repository in current directory or parent directories
///
/// # Returns
///
/// * `Result<Option<String>, CliError>` - Path to Git repository or None
pub fn find_git_repository() -> Result<Option<String>, CliError> {
    let mut current_dir = std::env::current_dir()
        .map_err(|e| CliError::FileOperation {
            operation: "get current directory".to_string(),
            path: ".".to_string(),
            source: e,
        })?;

    loop {
        let git_dir = current_dir.join(".git");
        if git_dir.exists() && git_dir.is_dir() {
            return Ok(Some(current_dir.to_string_lossy().to_string()));
        }

        if !current_dir.pop() {
            break;
        }
    }

    Ok(None)
}

/// Check if a file exists and is readable
///
/// # Arguments
///
/// * `file_path` - Path to the file to check
///
/// # Returns
///
/// * `Result<bool, CliError>` - True if file exists and is readable
pub fn file_exists_and_readable(file_path: &str) -> Result<bool, CliError> {
    let path = Path::new(file_path);
    
    if !path.exists() {
        return Ok(false);
    }
    
    if !path.is_file() {
        return Err(CliError::NotAFile {
            path: file_path.to_string(),
        });
    }
    
    // Try to read the file to check if it's readable
    fs::read_to_string(file_path)
        .map_err(|e| CliError::FileOperation {
            operation: "read file".to_string(),
            path: file_path.to_string(),
            source: e,
        })?;
    
    Ok(true)
}

/// Get file size in bytes
///
/// # Arguments
///
/// * `file_path` - Path to the file
///
/// # Returns
///
/// * `Result<u64, CliError>` - File size in bytes
pub fn get_file_size(file_path: &str) -> Result<u64, CliError> {
    let metadata = fs::metadata(file_path)
        .map_err(|e| CliError::FileOperation {
            operation: "get metadata".to_string(),
            path: file_path.to_string(),
            source: e,
        })?;
    
    Ok(metadata.len())
}

/// Create a backup of a file
///
/// # Arguments
///
/// * `file_path` - Path to the file to backup
///
/// # Returns
///
/// * `Result<String, CliError>` - Path to the backup file
pub fn create_file_backup(file_path: &str) -> Result<String, CliError> {
    let backup_path = format!("{}.backup", file_path);
    
    fs::copy(file_path, &backup_path)
        .map_err(|e| CliError::FileOperation {
            operation: "copy file".to_string(),
            path: file_path.to_string(),
            source: e,
        })?;
    
    Ok(backup_path)
}
