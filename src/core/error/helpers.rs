//! Convenience helper functions for common error scenarios
//!
//! This module provides helper functions for creating commonly-used errors
//! with pre-filled suggestions and recovery steps.

use super::types::{ArxError, ErrorContext};

impl ArxError {
    /// Create a file not found error with helpful suggestions
    pub fn file_not_found(path: impl Into<String>) -> Self {
        let path_str = path.into();
        Self::IoError {
            message: format!("File not found: {}", path_str),
            context: Box::new(ErrorContext {
                suggestions: vec![
                    "Check that the file path is correct".to_string(),
                    "Verify the file exists and you have read permissions".to_string(),
                    "Ensure you're in the correct directory".to_string(),
                ],
                recovery_steps: vec![
                    format!("Verify the file exists: ls -la {}", path_str),
                    "Check your current directory: pwd".to_string(),
                    "Verify file permissions: ls -l".to_string(),
                ],
                file_path: Some(path_str.clone()),
                ..Default::default()
            }),
            path: Some(path_str),
        }
    }

    /// Create a permission denied error with helpful suggestions
    pub fn permission_denied(path: impl Into<String>) -> Self {
        let path_str = path.into();
        Self::IoError {
            message: format!("Permission denied: {}", path_str),
            context: Box::new(ErrorContext {
                suggestions: vec![
                    "Check file permissions".to_string(),
                    "Verify you have read/write access".to_string(),
                    "Try running with appropriate permissions if needed".to_string(),
                ],
                recovery_steps: vec![
                    format!("Check permissions: ls -l {}", path_str),
                    "Verify file ownership".to_string(),
                    "Try changing permissions: chmod".to_string(),
                ],
                file_path: Some(path_str.clone()),
                ..Default::default()
            }),
            path: Some(path_str),
        }
    }

    /// Create an invalid format error with helpful suggestions
    pub fn invalid_format(description: impl Into<String>) -> Self {
        Self::Validation {
            message: format!("Invalid format: {}", description.into()),
            context: Box::new(ErrorContext {
                suggestions: vec![
                    "Check the file format matches expected structure".to_string(),
                    "Verify encoding (UTF-8 recommended)".to_string(),
                    "Review documentation for correct format".to_string(),
                ],
                recovery_steps: vec![
                    "Validate the file format".to_string(),
                    "Check for syntax errors".to_string(),
                    "Ensure all required fields are present".to_string(),
                ],
                ..Default::default()
            }),
            file_path: None,
        }
    }

    /// Create an IFC parsing error with helpful suggestions
    pub fn ifc_parse_error(message: impl Into<String>, file_path: Option<String>) -> Self {
        Self::IfcProcessing {
            message: message.into(),
            context: Box::new(ErrorContext {
                suggestions: vec![
                    "Verify the IFC file is valid and not corrupted".to_string(),
                    "Check IFC file version compatibility".to_string(),
                    "Ensure the file is a valid IFC file format".to_string(),
                ],
                recovery_steps: vec![
                    "Validate the IFC file with an IFC viewer".to_string(),
                    "Check IFC file version and format".to_string(),
                    "Try re-exporting from source software".to_string(),
                ],
                file_path: file_path.clone(),
                help_url: Some(
                    "https://github.com/arx-os/arxos/docs/features/IFC_PROCESSING.md".to_string(),
                ),
                ..Default::default()
            }),
            source: None,
        }
    }

    /// Create a Git operation error with helpful suggestions
    pub fn git_operation_failed(operation: impl Into<String>, message: impl Into<String>) -> Self {
        Self::GitOperation {
            message: message.into(),
            context: Box::new(ErrorContext {
                suggestions: vec![
                    "Check Git repository status".to_string(),
                    "Verify Git is properly configured".to_string(),
                    "Ensure you have appropriate permissions".to_string(),
                ],
                recovery_steps: vec![
                    format!("Check Git status: git status"),
                    "Verify Git configuration: git config --list".to_string(),
                    "Check repository permissions".to_string(),
                ],
                help_url: Some(
                    "https://github.com/arx-os/arxos/docs/core/ARCHITECTURE.md#git-operations"
                        .to_string(),
                ),
                ..Default::default()
            }),
            operation: operation.into(),
        }
    }
}
