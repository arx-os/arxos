//! Error types for ArxOS
//!
//! Provides unified error handling across all ArxOS modules.

use std::fmt;

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