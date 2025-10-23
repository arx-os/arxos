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
#[derive(Debug, Clone, Serialize, Deserialize)]
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
    
    /// Add suggestions to an error
    pub fn with_suggestions(mut self, suggestions: Vec<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. } |
            ArxError::Configuration { context, .. } |
            ArxError::GitOperation { context, .. } |
            ArxError::Validation { context, .. } |
            ArxError::IoError { context, .. } |
            ArxError::YamlProcessing { context, .. } |
            ArxError::SpatialData { context, .. } => {
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
            ArxError::SpatialData { context, .. } => {
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
            ArxError::SpatialData { context, .. } => {
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
            ArxError::SpatialData { context, .. } => {
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
            ArxError::SpatialData { context, .. } => {
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
            ArxError::SpatialData { context, .. } => {
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
            ArxError::SpatialData { context, .. } => context,
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

impl Default for ErrorContext {
    fn default() -> Self {
        Self {
            suggestions: Vec::new(),
            recovery_steps: Vec::new(),
            debug_info: None,
            help_url: None,
            file_path: None,
            line_number: None,
        }
    }
}

/// Result type alias for ArxOS operations
pub type ArxResult<T> = Result<T, ArxError>;

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
}
