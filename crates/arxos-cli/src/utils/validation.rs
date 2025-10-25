//! # Validation Utilities
//!
//! This module provides utilities for validating input data,
//! file formats, and command arguments.

use crate::error::CliError;

/// Validate a YAML file format
pub fn validate_yaml_file(file_path: &str) -> Result<(), CliError> {
    use std::fs;
    
    let content = fs::read_to_string(file_path)
        .map_err(|e| CliError::FileOperation {
            operation: "read file".to_string(),
            path: file_path.to_string(),
            source: e,
        })?;
    
    serde_yaml::from_str::<serde_yaml::Value>(&content)
        .map_err(|e| CliError::YamlParse {
            file: file_path.to_string(),
            source: e,
        })?;
    
    Ok(())
}

/// Validate building name format
pub fn validate_building_name(name: &str) -> Result<(), CliError> {
    if name.is_empty() {
        return Err(CliError::InvalidInput {
            field: "building name".to_string(),
            value: name.to_string(),
            reason: "cannot be empty".to_string(),
        });
    }
    
    if name.len() > 100 {
        return Err(CliError::InvalidInput {
            field: "building name".to_string(),
            value: name.to_string(),
            reason: "too long (max 100 characters)".to_string(),
        });
    }
    
    Ok(())
}

/// Validate file path format
pub fn validate_file_path(path: &str) -> Result<(), CliError> {
    if path.is_empty() {
        return Err(CliError::InvalidInput {
            field: "file path".to_string(),
            value: path.to_string(),
            reason: "cannot be empty".to_string(),
        });
    }
    
    Ok(())
}
