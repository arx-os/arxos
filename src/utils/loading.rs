// Building data loading utilities
// This module handles loading and validating building data from YAML files

use crate::yaml::BuildingData;
use crate::persistence::PersistenceManager;
use std::path::Path;

/// Load building data from current directory using PersistenceManager
/// 
/// This function attempts to find and load building data from YAML files
/// in the current directory. It provides detailed error messages for common issues.
/// 
/// # Parameters
/// 
/// * `building_name` - Name of the building to load (can be empty for auto-detection)
/// 
/// # Returns
/// 
/// Returns a `Result` containing:
/// - `Ok(BuildingData)` - Successfully loaded building data
/// - `Err(Box<dyn std::error::Error>)` - Error with detailed context and suggestions
/// 
/// # Errors
/// 
/// This function can return various errors:
/// - **No YAML files**: No building data files found
/// - **Parse error**: Invalid YAML format
/// - **Permission error**: Cannot read file due to permissions
/// - **IO error**: General file system errors
pub fn load_building_data(building_name: &str) -> Result<BuildingData, Box<dyn std::error::Error>> {
    // Use PersistenceManager if we have a building name
    if !building_name.is_empty() {
        let persistence = PersistenceManager::new(building_name)?;
        return Ok(persistence.load_building_data()?);
    }
    
    // Otherwise, look for YAML files in current directory (fallback)
    find_and_load_yaml_file()
}

/// Find and load first YAML file in current directory
fn find_and_load_yaml_file() -> Result<BuildingData, Box<dyn std::error::Error>> {
    let yaml_files: Vec<String> = std::fs::read_dir(".")
        .map_err(|e| {
            format!(
                "Failed to read current directory: {}. \
                Please ensure you have read permissions and are in the correct directory.",
                e
            )
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
        return Err(format!(
            "No YAML files found in current directory. \
            Available options:\n\
            1. Run 'arxos import <ifc-file>' to import building data\n\
            2. Check if you're in the correct directory\n\
            3. Verify that YAML files exist and have .yaml extension"
        ).into());
    }
    
    // Use the first YAML file found
    let yaml_file = yaml_files.first().unwrap();
    
    println!("📄 Loading building data from: {}", yaml_file);
    
    // Read and parse the YAML file with detailed error handling
    let yaml_content = std::fs::read_to_string(yaml_file)
        .map_err(|e| {
            format!(
                "Failed to read file '{}': {}. \
                Please check file permissions and ensure the file is not corrupted.",
                yaml_file, e
            )
        })?;
    let building_data: BuildingData = serde_yaml::from_str(&yaml_content)
        .map_err(|e| {
            format!(
                "Failed to parse YAML file '{}': {}. \
                The file may be corrupted or have invalid YAML syntax. \
                Please check the file format and try importing again.",
                yaml_file, e
            )
        })?;
    
    Ok(building_data)
}

/// Validate YAML building data file
/// 
/// This function validates that a YAML file contains valid building data
/// structure including proper floor and room definitions.
/// 
/// # Parameters
/// 
/// * `file_path` - Path to the YAML file to validate
/// 
/// # Returns
/// 
/// Returns a `Result` containing:
/// - `Ok(())` - File is valid
/// - `Err(Box<dyn std::error::Error>)` - Validation errors
/// 
/// # Errors
/// 
/// This function can return errors for:
/// - Empty building name
/// - No floors defined
/// - Empty floor names
/// - Duplicate floor levels
pub fn validate_yaml_file(file_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Validate file exists
    if !Path::new(file_path).exists() {
        return Err(format!("File not found: {}", file_path).into());
    }
    
    // Read and parse the YAML file
    let yaml_content = std::fs::read_to_string(file_path)?;
    let building_data: BuildingData = serde_yaml::from_str(&yaml_content)?;
    
    // Validate building data structure
    if building_data.building.name.is_empty() {
        return Err("Building name cannot be empty".into());
    }
    
    if building_data.floors.is_empty() {
        return Err("Building must have at least one floor".into());
    }
    
    // Validate each floor
    for floor in &building_data.floors {
        if floor.name.is_empty() {
            return Err(format!("Floor {} has empty name", floor.level).into());
        }
        
        // Check for duplicate floor levels
        let duplicate_floors = building_data.floors.iter()
            .filter(|f| f.level == floor.level)
            .count();
        if duplicate_floors > 1 {
            return Err(format!("Duplicate floor level {} found", floor.level).into());
        }
    }
    
    Ok(())
}

/// Find YAML files in current directory
/// 
/// Returns a list of all .yaml and .yml files found in the current directory.
pub fn find_yaml_files() -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let yaml_files: Vec<String> = std::fs::read_dir(".")
        .map_err(|e| format!("Failed to read current directory: {}", e))?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            let ext = path.extension()?.to_str()?;
            if ext == "yaml" || ext == "yml" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();
    
    Ok(yaml_files)
}

/// Find IFC files in current directory
/// 
/// Returns a list of all .ifc files found in the current directory.
pub fn find_ifc_files() -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let ifc_files: Vec<String> = std::fs::read_dir(".")
        .map_err(|e| format!("Failed to read current directory: {}", e))?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()?.to_str()?.to_lowercase() == "ifc" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();
    
    Ok(ifc_files)
}

