//! Central error management for ArxOS
//! 
//! This module provides:
//! - Rich error types with context and suggestions
//! - Error recovery mechanisms
//! - User-friendly error messages
//! - Debugging information

use serde::{Deserialize, Serialize};
use thiserror::Error;

pub mod display;
pub mod analytics;

pub use display::ErrorDisplay;
pub use analytics::ErrorAnalytics;

/// Rich error context with suggestions and recovery
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ErrorContext {
    /// Helpful suggestions for resolving the error
    pub suggestions: Vec<String>,
    /// Step-by-step recovery instructions
    pub recovery_steps: Vec<String>,
    /// Additional debugging information
    pub debug_info: Option<String>,
    /// URL to help documentation
    pub help_url: Option<String>,
    /// File path where error occurred
    pub file_path: Option<String>,
    /// Line number where error occurred
    pub line_number: Option<usize>,
}

/// Enhanced error types for ArxOS
#[derive(Error, Debug)]
pub enum ArxError {
    #[error("IFC Processing Error: {message}")]
    IfcProcessing {
        message: String,
        context: ErrorContext,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Configuration Error: {message}")]
    Configuration {
        message: String,
        context: ErrorContext,
        field: Option<String>,
    },
    
    #[error("Git Operation Error: {message}")]
    GitOperation {
        message: String,
        context: ErrorContext,
        operation: String,
    },
    
    #[error("Validation Error: {message}")]
    Validation {
        message: String,
        context: ErrorContext,
        file_path: Option<String>,
    },
    
    #[error("IO Error: {message}")]
    IoError {
        message: String,
        context: ErrorContext,
        path: Option<String>,
    },
    
    #[error("YAML Processing Error: {message}")]
    YamlProcessing {
        message: String,
        context: ErrorContext,
        file_path: Option<String>,
    },
    
    #[error("Spatial Data Error: {message}")]
    SpatialData {
        message: String,
        context: ErrorContext,
        entity_type: Option<String>,
    },
    
    #[error("Address Validation Error: {message}")]
    AddressValidation {
        message: String,
        context: ErrorContext,
        path: String,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Counter Overflow Error: {message}")]
    CounterOverflow {
        message: String,
        context: ErrorContext,
        room: String,
        equipment_type: String,
    },
    
    #[error("Path Invalid Error: {message}")]
    PathInvalid {
        message: String,
        context: ErrorContext,
        path: String,
        expected_format: String,
    },
}

impl ArxError {
    /// Create a new IFC processing error with context
    pub fn ifc_processing(message: impl Into<String>) -> Self {
        Self::IfcProcessing {
            message: message.into(),
            context: ErrorContext::default(),
            source: None,
        }
    }
    
    /// Create a new configuration error with context
    pub fn configuration(message: impl Into<String>) -> Self {
        Self::Configuration {
            message: message.into(),
            context: ErrorContext::default(),
            field: None,
        }
    }
    
    /// Create a new Git operation error with context
    pub fn git_operation(message: impl Into<String>, operation: impl Into<String>) -> Self {
        Self::GitOperation {
            message: message.into(),
            context: ErrorContext::default(),
            operation: operation.into(),
        }
    }
    
    /// Create a new validation error with context
    pub fn validation(message: impl Into<String>) -> Self {
        Self::Validation {
            message: message.into(),
            context: ErrorContext::default(),
            file_path: None,
        }
    }
    
    /// Create a new IO error with context
    pub fn io_error(message: impl Into<String>) -> Self {
        Self::IoError {
            message: message.into(),
            context: ErrorContext::default(),
            path: None,
        }
    }
    
    /// Create a new YAML processing error with context
    pub fn yaml_processing(message: impl Into<String>) -> Self {
        Self::YamlProcessing {
            message: message.into(),
            context: ErrorContext::default(),
            file_path: None,
        }
    }
    
    /// Create a new spatial data error with context
    pub fn spatial_data(message: impl Into<String>) -> Self {
        Self::SpatialData {
            message: message.into(),
            context: ErrorContext::default(),
            entity_type: None,
        }
    }
    
    /// Create a new address validation error
    pub fn address_validation(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::AddressValidation {
            message: message.into(),
            context: ErrorContext::default(),
            path: path.into(),
            source: None,
        }
    }
    
    /// Create a new counter overflow error
    pub fn counter_overflow(room: impl Into<String>, equipment_type: impl Into<String>) -> Self {
        let room = room.into();
        let equipment_type = equipment_type.into();
        Self::CounterOverflow {
            message: format!("Counter overflow for room '{}' and equipment type '{}'", room, equipment_type),
            context: ErrorContext {
                suggestions: vec![
                    "Check if counter file is corrupted".to_string(),
                    "Manually reset counter in .arxos/counters.toml".to_string(),
                ],
                recovery_steps: vec![
                    "Open .arxos/counters.toml".to_string(),
                    format!("Find entry for '{}:{}'", room, equipment_type),
                    "Reset counter value to a reasonable number".to_string(),
                ],
                ..Default::default()
            },
            room,
            equipment_type,
        }
    }
    
    /// Create a new path invalid error
    pub fn path_invalid(path: impl Into<String>, expected_format: impl Into<String>) -> Self {
        let path = path.into();
        let expected_format = expected_format.into();
        Self::PathInvalid {
            message: format!("Invalid path format: '{}'", path),
            context: ErrorContext {
                suggestions: vec![
                    format!("Expected format: {}", expected_format),
                    "Ensure path has exactly 7 segments: /country/state/city/building/floor/room/fixture".to_string(),
                ],
                recovery_steps: vec![
                    "Check path format".to_string(),
                    "Ensure all segments are present".to_string(),
                    "Verify no invalid characters".to_string(),
                ],
                ..Default::default()
            },
            path,
            expected_format,
        }
    }
    
    /// Add suggestions to an error
    pub fn with_suggestions(mut self, suggestions: Vec<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } |
            ArxError::AddressValidation { context, .. } |
            ArxError::CounterOverflow { context, .. } |
            ArxError::PathInvalid { context, .. } => {
                context.suggestions = suggestions;
            }
        }
        self
    }
    
    /// Add recovery steps to an error
    pub fn with_recovery(mut self, recovery_steps: Vec<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } |
            ArxError::AddressValidation { context, .. } |
            ArxError::CounterOverflow { context, .. } |
            ArxError::PathInvalid { context, .. } => {
                context.recovery_steps = recovery_steps;
            }
        }
        self
    }
    
    /// Add debug information to an error
    pub fn with_debug_info(mut self, debug_info: impl Into<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } |
            ArxError::AddressValidation { context, .. } |
            ArxError::CounterOverflow { context, .. } |
            ArxError::PathInvalid { context, .. } => {
                context.debug_info = Some(debug_info.into());
            }
        }
        self
    }
    
    /// Add file path context to an error
    pub fn with_file_path(mut self, file_path: impl Into<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } |
            ArxError::AddressValidation { context, .. } |
            ArxError::CounterOverflow { context, .. } |
            ArxError::PathInvalid { context, .. } => {
                context.file_path = Some(file_path.into());
            }
        }
        self
    }
    
    /// Add line number context to an error
    pub fn with_line_number(mut self, line_number: usize) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } |
            ArxError::AddressValidation { context, .. } |
            ArxError::CounterOverflow { context, .. } |
            ArxError::PathInvalid { context, .. } => {
                context.line_number = Some(line_number);
            }
        }
        self
    }
    
    /// Add help URL to an error
    pub fn with_help_url(mut self, help_url: impl Into<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } |
            ArxError::AddressValidation { context, .. } |
            ArxError::CounterOverflow { context, .. } |
            ArxError::PathInvalid { context, .. } => {
                context.help_url = Some(help_url.into());
            }
        }
        self
    }
    
    /// Get the error context
    pub fn context(&self) -> &ErrorContext {
        match self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } |
            ArxError::AddressValidation { context, .. } |
            ArxError::CounterOverflow { context, .. } |
            ArxError::PathInvalid { context, .. } => context,
        }
    }
    
    /// Check if this error has recovery suggestions
    pub fn has_recovery(&self) -> bool {
        !self.context().recovery_steps.is_empty()
    }
    
    /// Check if this error has suggestions
    pub fn has_suggestions(&self) -> bool {
        !self.context().suggestions.is_empty()
    }
}


/// Result type alias for ArxOS operations
pub type ArxResult<T> = Result<T, ArxError>;

// From trait implementations for common error types

impl From<std::io::Error> for ArxError {
    fn from(err: std::io::Error) -> Self {
        let path = err
            .raw_os_error()
            .map(|_| "System error occurred".to_string())
            .or_else(|| {
                // Try to extract path from error message if available
                let msg = err.to_string();
                if msg.contains("No such file") {
                    msg.split("No such file")
                        .nth(1)
                        .map(|s| s.trim().trim_matches(|c| c == '"' || c == '\'' || c == '(' || c == ')'))
                        .map(|s| s.to_string())
                } else {
                    None
                }
            });
        
        Self::IoError {
            message: err.to_string(),
            context: ErrorContext::default(),
            path,
        }
    }
}

impl From<serde_yaml::Error> for ArxError {
    fn from(err: serde_yaml::Error) -> Self {
        // Extract file path if available from location
        let file_path = err.location().map(|_| "YAML file".to_string());
        
        Self::YamlProcessing {
            message: err.to_string(),
            context: ErrorContext::default(),
            file_path,
        }
    }
}

impl From<serde_json::Error> for ArxError {
    fn from(err: serde_json::Error) -> Self {
        Self::YamlProcessing {
            message: format!("JSON parsing error: {}", err),
            context: ErrorContext::default(),
            file_path: None,
        }
    }
}

impl From<git2::Error> for ArxError {
    fn from(err: git2::Error) -> Self {
        Self::GitOperation {
            message: err.message().to_string(),
            context: ErrorContext::default(),
            operation: "Git operation".to_string(),
        }
    }
}

impl From<crate::git::GitError> for ArxError {
    fn from(err: crate::git::GitError) -> Self {
        match err {
            crate::git::GitError::GitError(git_err_msg) => {
                Self::GitOperation {
                    message: git_err_msg,
                    context: ErrorContext {
                        suggestions: vec![
                            "Check Git repository status".to_string(),
                            "Verify Git is properly configured".to_string(),
                            "Ensure you have appropriate permissions".to_string(),
                        ],
                        recovery_steps: vec![
                            "Run: git status".to_string(),
                            "Check: git config --list".to_string(),
                            "Verify repository permissions".to_string(),
                        ],
                        help_url: Some("https://github.com/arxos/arxos/docs/core/ARCHITECTURE.md#git-operations".to_string()),
                        ..Default::default()
                    },
                    operation: "Git operation".to_string(),
                }
            }
            crate::git::GitError::IoError(io_err) => {
                Self::IoError {
                    message: format!("Git IO error: {}", io_err),
                    context: ErrorContext {
                        suggestions: vec![
                            "Check file system permissions".to_string(),
                            "Verify disk space is available".to_string(),
                            "Ensure the repository path is accessible".to_string(),
                        ],
                        recovery_steps: vec![
                            "Check file permissions: ls -l".to_string(),
                            "Verify disk space: df -h".to_string(),
                            "Check repository path exists".to_string(),
                        ],
                        ..Default::default()
                    },
                    path: None,
                }
            }
            crate::git::GitError::SerializationError(serde_err) => {
                Self::YamlProcessing {
                    message: format!("Git serialization error: {}", serde_err),
                    context: ErrorContext {
                        suggestions: vec![
                            "Check YAML file format".to_string(),
                            "Verify file encoding (UTF-8)".to_string(),
                            "Review YAML syntax".to_string(),
                        ],
                        recovery_steps: vec![
                            "Validate YAML syntax".to_string(),
                            "Check file encoding".to_string(),
                            "Review documentation for YAML format".to_string(),
                        ],
                        ..Default::default()
                    },
                    file_path: None,
                }
            }
            crate::git::GitError::Generic(err) => {
                Self::GitOperation {
                    message: format!("Git error: {}", err),
                    context: ErrorContext::default(),
                    operation: "Git operation".to_string(),
                }
            }
            crate::git::GitError::RepositoryNotFound { path } => {
                Self::GitOperation {
                    message: format!("Git repository not found: {}", path),
                    context: ErrorContext {
                        suggestions: vec![
                            "Verify the repository path is correct".to_string(),
                            "Check if the repository exists".to_string(),
                            "Initialize a new repository if needed".to_string(),
                        ],
                        recovery_steps: vec![
                            format!("Check path exists: ls -la {}", path),
                            "Initialize repository: git init".to_string(),
                            "Verify repository path in configuration".to_string(),
                        ],
                        file_path: Some(path),
                        ..Default::default()
                    },
                    operation: "repository initialization".to_string(),
                }
            }
            crate::git::GitError::InvalidConfig { reason } => {
                Self::Configuration {
                    message: format!("Invalid Git configuration: {}", reason),
                    context: ErrorContext {
                        suggestions: vec![
                            "Review Git configuration settings".to_string(),
                            "Check environment variables".to_string(),
                            "Verify ArxConfig settings".to_string(),
                        ],
                        recovery_steps: vec![
                            "Check: git config --list".to_string(),
                            "Review environment variables (GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL)".to_string(),
                            "Verify ArxConfig user settings".to_string(),
                        ],
                        ..Default::default()
                    },
                    field: Some("git_config".to_string()),
                }
            }
            crate::git::GitError::OperationFailed { operation, reason } => {
                Self::GitOperation {
                    message: format!("Git operation failed: {}", reason),
                    context: ErrorContext {
                        suggestions: vec![
                            "Check Git repository status".to_string(),
                            "Review error details for specific issue".to_string(),
                            "Verify repository permissions".to_string(),
                        ],
                        recovery_steps: vec![
                            format!("Review operation: {}", operation),
                            "Check repository status: git status".to_string(),
                            "Verify permissions and configuration".to_string(),
                        ],
                        debug_info: Some(format!("Operation: {}, Reason: {}", operation, reason)),
                        ..Default::default()
                    },
                    operation,
                }
            }
        }
    }
}

// Convenience helper functions for common error scenarios

impl ArxError {
    /// Create a file not found error with helpful suggestions
    pub fn file_not_found(path: impl Into<String>) -> Self {
        let path_str = path.into();
        Self::IoError {
            message: format!("File not found: {}", path_str),
            context: ErrorContext {
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
            },
            path: Some(path_str),
        }
    }
    
    /// Create a permission denied error with helpful suggestions
    pub fn permission_denied(path: impl Into<String>) -> Self {
        let path_str = path.into();
        Self::IoError {
            message: format!("Permission denied: {}", path_str),
            context: ErrorContext {
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
            },
            path: Some(path_str),
        }
    }
    
    /// Create an invalid format error with helpful suggestions
    pub fn invalid_format(description: impl Into<String>) -> Self {
        Self::Validation {
            message: format!("Invalid format: {}", description.into()),
            context: ErrorContext {
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
            },
            file_path: None,
        }
    }
    
    /// Create an IFC parsing error with helpful suggestions
    pub fn ifc_parse_error(message: impl Into<String>, file_path: Option<String>) -> Self {
        Self::IfcProcessing {
            message: message.into(),
            context: ErrorContext {
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
                help_url: Some("https://github.com/arxos/arxos/docs/features/IFC_PROCESSING.md".to_string()),
                ..Default::default()
            },
            source: None,
        }
    }
    
    /// Create a Git operation error with helpful suggestions
    pub fn git_operation_failed(operation: impl Into<String>, message: impl Into<String>) -> Self {
        Self::GitOperation {
            message: message.into(),
            context: ErrorContext {
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
                help_url: Some("https://github.com/arxos/arxos/docs/core/ARCHITECTURE.md#git-operations".to_string()),
                ..Default::default()
            },
            operation: operation.into(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_error_creation() {
        let error = ArxError::ifc_processing("Test error");
        assert_eq!(error.to_string(), "IFC Processing Error: Test error");
    }
    
    #[test]
    fn test_error_with_suggestions() {
        let error = ArxError::ifc_processing("Test error")
            .with_suggestions(vec!["Suggestion 1".to_string(), "Suggestion 2".to_string()]);
        
        assert!(error.has_suggestions());
        assert_eq!(error.context().suggestions.len(), 2);
    }
    
    #[test]
    fn test_error_with_recovery() {
        let error = ArxError::ifc_processing("Test error")
            .with_recovery(vec!["Step 1".to_string(), "Step 2".to_string()]);
        
        assert!(error.has_recovery());
        assert_eq!(error.context().recovery_steps.len(), 2);
    }
    
    #[test]
    fn test_error_with_context() {
        let error = ArxError::ifc_processing("Test error")
            .with_file_path("test.ifc")
            .with_line_number(42)
            .with_debug_info("Debug information");
        
        assert_eq!(error.context().file_path, Some("test.ifc".to_string()));
        assert_eq!(error.context().line_number, Some(42));
        assert_eq!(error.context().debug_info, Some("Debug information".to_string()));
    }
    
    #[test]
    fn test_from_io_error() {
        let io_err = std::io::Error::new(std::io::ErrorKind::NotFound, "File not found");
        let arx_error: ArxError = io_err.into();
        
        match arx_error {
            ArxError::IoError { message, .. } => {
                assert!(message.contains("File not found"));
            }
            _ => panic!("Expected IoError variant"),
        }
    }
    
    #[test]
    fn test_file_not_found_helper() {
        let error = ArxError::file_not_found("/path/to/file");
        
        match error {
            ArxError::IoError { message, context, path } => {
                assert!(message.contains("File not found"));
                assert_eq!(path, Some("/path/to/file".to_string()));
                assert!(!context.suggestions.is_empty());
                assert!(!context.recovery_steps.is_empty());
            }
            _ => panic!("Expected IoError variant"),
        }
    }
    
    #[test]
    fn test_permission_denied_helper() {
        let error = ArxError::permission_denied("/path/to/file");
        
        match error {
            ArxError::IoError { message, context, .. } => {
                assert!(message.contains("Permission denied"));
                assert!(!context.suggestions.is_empty());
            }
            _ => panic!("Expected IoError variant"),
        }
    }
    
    #[test]
    fn test_invalid_format_helper() {
        let error = ArxError::invalid_format("Invalid JSON structure");
        
        match error {
            ArxError::Validation { message, context, .. } => {
                assert!(message.contains("Invalid format"));
                assert!(!context.suggestions.is_empty());
            }
            _ => panic!("Expected Validation variant"),
        }
    }
}
