//! # CLI Error Handling
//!
//! This module provides comprehensive error handling for the ArxOS CLI,
//! including custom error types and error conversion utilities.

use thiserror::Error;

/// Main error type for ArxOS CLI operations
#[derive(Error, Debug)]
pub enum CliError {
    #[error("File operation failed: {operation} on {path}")]
    FileOperation {
        operation: String,
        path: String,
        #[source]
        source: std::io::Error,
    },
    
    #[error("YAML parsing failed for file {file}")]
    YamlParse {
        file: String,
        #[source]
        source: serde_yaml::Error,
    },
    
    #[error("Invalid input: {field} = '{value}' - {reason}")]
    InvalidInput {
        field: String,
        value: String,
        reason: String,
    },
    
    #[error("No YAML files found in current directory")]
    NoYamlFiles,
    
    #[error("Not a file: {path}")]
    NotAFile { path: String },
    
    #[error("Git operation failed: {operation}")]
    GitOperation {
        operation: String,
        #[source]
        source: git2::Error,
    },
    
    #[error("Configuration error: {message}")]
    ConfigError {
        message: String,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Core operation failed: {operation}")]
    CoreOperation {
        operation: String,
        #[source]
        source: arxos_core::ArxError,
    },
    
    #[error("Unknown error: {message}")]
    Unknown {
        message: String,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
}

impl CliError {
    /// Get recovery suggestions for the error
    pub fn recovery_suggestions(&self) -> Vec<&'static str> {
        match self {
            Self::FileOperation { .. } => {
                vec![
                    "Check if the file exists and is readable",
                    "Verify file permissions",
                    "Ensure the path is correct"
                ]
            }
            Self::YamlParse { .. } => {
                vec![
                    "Check YAML syntax",
                    "Validate file format",
                    "Use a YAML validator"
                ]
            }
            Self::InvalidInput { .. } => {
                vec![
                    "Check input format",
                    "Verify required fields",
                    "Use correct data types"
                ]
            }
            Self::NoYamlFiles => {
                vec![
                    "Create YAML files in current directory",
                    "Check file extensions (.yaml)",
                    "Import building data first"
                ]
            }
            Self::GitOperation { .. } => {
                vec![
                    "Check Git repository status",
                    "Verify Git configuration",
                    "Ensure repository is initialized"
                ]
            }
            Self::ConfigError { .. } => {
                vec![
                    "Check configuration file format",
                    "Verify configuration values",
                    "Reset to default configuration"
                ]
            }
            Self::CoreOperation { .. } => {
                vec![
                    "Check core system status",
                    "Verify data integrity",
                    "Review operation parameters"
                ]
            }
            _ => vec!["Check error message for details", "Verify input parameters"]
        }
    }
}
