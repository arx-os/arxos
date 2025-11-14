//! Error types for ArxOS
//!
//! Provides unified error handling across all ArxOS modules.

use std::fmt;

/// Error context with suggestions and recovery steps
#[derive(Debug, Clone, Default)]
pub struct ErrorContext {
    pub suggestions: Vec<String>,
    pub recovery_steps: Vec<String>,
}

/// Core ArxOS error types
#[derive(Debug)]
pub enum ArxError {
    /// Path validation error
    PathInvalid { path: String, expected: String },
    /// Address validation error
    AddressValidation { address: String, message: String },
    /// IO error
    Io(std::io::Error),
    /// Serialization error
    Serialization(String),
    /// Git operation error
    Git(String),
    /// IFC parsing error
    Ifc(String),
    /// Configuration error
    Config(String),
    /// General error with message
    General(String),

    // Additional structured error variants for TUI error handling
    /// Git operation error with context
    GitOperation { message: String, context: Option<String> },
    /// Configuration error with details
    Configuration { message: String, details: Option<String> },
    /// Validation error
    Validation { message: String, field: Option<String> },
    /// IFC processing error with context
    IfcProcessing { message: String, line: Option<usize> },
    /// IO error with context
    IoError { message: String, path: Option<String> },
    /// YAML processing error
    YamlProcessing { message: String, line: Option<usize> },
    /// Spatial data error
    SpatialData { message: String, entity: Option<String> },
    /// Counter overflow error
    CounterOverflow { counter_name: String },
}

impl fmt::Display for ArxError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ArxError::PathInvalid { path, expected } => {
                write!(f, "Invalid path '{}', expected format: {}", path, expected)
            }
            ArxError::AddressValidation { address, message } => {
                write!(f, "Address validation failed for '{}': {}", address, message)
            }
            ArxError::Io(err) => write!(f, "IO error: {}", err),
            ArxError::Serialization(msg) => write!(f, "Serialization error: {}", msg),
            ArxError::Git(msg) => write!(f, "Git error: {}", msg),
            ArxError::Ifc(msg) => write!(f, "IFC error: {}", msg),
            ArxError::Config(msg) => write!(f, "Configuration error: {}", msg),
            ArxError::General(msg) => write!(f, "{}", msg),
            ArxError::GitOperation { message, context } => {
                write!(f, "Git operation error: {}{}", message, context.as_ref().map(|c| format!(" ({})", c)).unwrap_or_default())
            }
            ArxError::Configuration { message, details } => {
                write!(f, "Configuration error: {}{}", message, details.as_ref().map(|d| format!(" - {}", d)).unwrap_or_default())
            }
            ArxError::Validation { message, field } => {
                write!(f, "Validation error{}: {}", field.as_ref().map(|fld| format!(" for field '{}'", fld)).unwrap_or_default(), message)
            }
            ArxError::IfcProcessing { message, line } => {
                write!(f, "IFC processing error{}: {}", line.map(|l| format!(" at line {}", l)).unwrap_or_default(), message)
            }
            ArxError::IoError { message, path } => {
                write!(f, "IO error{}: {}", path.as_ref().map(|p| format!(" at '{}'", p)).unwrap_or_default(), message)
            }
            ArxError::YamlProcessing { message, line } => {
                write!(f, "YAML processing error{}: {}", line.map(|l| format!(" at line {}", l)).unwrap_or_default(), message)
            }
            ArxError::SpatialData { message, entity } => {
                write!(f, "Spatial data error{}: {}", entity.as_ref().map(|e| format!(" for entity '{}'", e)).unwrap_or_default(), message)
            }
            ArxError::CounterOverflow { counter_name } => {
                write!(f, "Counter overflow: {}", counter_name)
            }
        }
    }
}

impl std::error::Error for ArxError {}

impl From<std::io::Error> for ArxError {
    fn from(err: std::io::Error) -> Self {
        ArxError::Io(err)
    }
}

impl From<serde_yaml::Error> for ArxError {
    fn from(err: serde_yaml::Error) -> Self {
        ArxError::Serialization(err.to_string())
    }
}

impl From<crate::git::manager::GitError> for ArxError {
    fn from(err: crate::git::manager::GitError) -> Self {
        ArxError::Git(err.to_string())
    }
}

impl ArxError {
    /// Get error context with suggestions and recovery steps
    pub fn context(&self) -> ErrorContext {
        match self {
            ArxError::GitOperation { .. } => ErrorContext {
                suggestions: vec![
                    "Check Git repository status".to_string(),
                    "Ensure you have the necessary permissions".to_string(),
                ],
                recovery_steps: vec![
                    "Run 'git status' to check repository state".to_string(),
                    "Verify your Git configuration".to_string(),
                ],
            },
            ArxError::Configuration { .. } => ErrorContext {
                suggestions: vec![
                    "Check configuration file syntax".to_string(),
                    "Verify all required fields are present".to_string(),
                ],
                recovery_steps: vec![
                    "Review the configuration documentation".to_string(),
                    "Use 'arx show-config' to see current settings".to_string(),
                ],
            },
            ArxError::Validation { field, .. } => {
                let mut suggestions = vec!["Check input value format".to_string()];
                if field.is_some() {
                    suggestions.push(format!("Verify the '{}' field", field.as_ref().unwrap()));
                }
                ErrorContext {
                    suggestions,
                    recovery_steps: vec![
                        "Correct the validation error and try again".to_string(),
                    ],
                }
            },
            ArxError::IfcProcessing { line, .. } => {
                let mut suggestions = vec!["Check IFC file format".to_string()];
                if let Some(l) = line {
                    suggestions.push(format!("Review line {} in the IFC file", l));
                }
                ErrorContext {
                    suggestions,
                    recovery_steps: vec![
                        "Validate the IFC file with an IFC validator".to_string(),
                        "Try re-exporting from the source application".to_string(),
                    ],
                }
            },
            ArxError::IoError { path, .. } => {
                let mut suggestions = vec!["Check file permissions".to_string()];
                if path.is_some() {
                    suggestions.push("Verify the file path exists".to_string());
                }
                ErrorContext {
                    suggestions,
                    recovery_steps: vec![
                        "Ensure you have read/write permissions".to_string(),
                        "Check available disk space".to_string(),
                    ],
                }
            },
            ArxError::YamlProcessing { line, .. } => {
                let mut suggestions = vec!["Check YAML syntax".to_string()];
                if let Some(l) = line {
                    suggestions.push(format!("Review line {} in the YAML file", l));
                }
                ErrorContext {
                    suggestions,
                    recovery_steps: vec![
                        "Validate YAML with a YAML linter".to_string(),
                        "Check for proper indentation".to_string(),
                    ],
                }
            },
            ArxError::SpatialData { entity, .. } => {
                let mut suggestions = vec!["Verify spatial coordinates".to_string()];
                if entity.is_some() {
                    suggestions.push(format!("Check entity '{}'", entity.as_ref().unwrap()));
                }
                ErrorContext {
                    suggestions,
                    recovery_steps: vec![
                        "Review entity placement and dimensions".to_string(),
                        "Validate coordinate system configuration".to_string(),
                    ],
                }
            },
            ArxError::CounterOverflow { counter_name } => ErrorContext {
                suggestions: vec![
                    format!("The {} counter has reached its maximum value", counter_name),
                ],
                recovery_steps: vec![
                    "Contact support for assistance".to_string(),
                ],
            },
            _ => ErrorContext::default(),
        }
    }
}

impl ArxError {
    pub fn path_invalid<S: Into<String>>(path: S, expected: S) -> Self {
        ArxError::PathInvalid {
            path: path.into(),
            expected: expected.into(),
        }
    }

    pub fn address_validation<S: Into<String>>(address: S, message: S) -> Self {
        ArxError::AddressValidation {
            address: address.into(),
            message: message.into(),
        }
    }

    pub fn general<S: Into<String>>(message: S) -> Self {
        ArxError::General(message.into())
    }

    pub fn io_error<S: Into<String>>(message: S) -> Self {
        ArxError::Io(std::io::Error::new(std::io::ErrorKind::Other, message.into()))
    }

    pub fn ifc_processing<S: Into<String>>(message: S) -> Self {
        ArxError::Ifc(message.into())
    }

    pub fn spatial_data<S: Into<String>>(message: S) -> Self {
        ArxError::General(format!("Spatial data error: {}", message.into()))
    }

    /// Add file path context to an error
    pub fn with_file_path<S: Into<String>>(self, _file_path: S) -> Self {
        // For now, return self - could be extended to add file path to the error message
        self
    }

    /// Add debug info context to an error
    pub fn with_debug_info<S: Into<String>>(self, _debug_info: S) -> Self {
        // For now, return self - could be extended to add debug info to the error message
        self
    }

    /// Add suggestions context to an error
    pub fn with_suggestions(self, _suggestions: Vec<String>) -> Self {
        // For now, return self - could be extended to add suggestions to the error message
        self
    }

    /// Add line number context to an error
    pub fn with_line_number(self, _line_number: usize) -> Self {
        // For now, return self - could be extended to add line number to the error message
        self
    }

    /// Add recovery options to an error
    pub fn with_recovery(self, _recovery_options: Vec<String>) -> Self {
        // For now, return self - could be extended to add recovery options to the error message
        self
    }
}

/// Result type alias for ArxOS operations
pub type ArxResult<T> = Result<T, ArxError>;

/// Analytics module for error tracking and reporting
pub mod analytics {
    use super::ArxError;

    /// Manager for error analytics and reporting
    pub struct ErrorAnalyticsManager;

    impl ErrorAnalyticsManager {
        /// Record a global error for analytics
        pub fn record_global_error(error: &ArxError, context: Option<String>) {
            // For now, just log the error - could be extended to send to analytics service
            eprintln!("Error Analytics: {:?} | Context: {:?}", error, context);
        }
    }
}