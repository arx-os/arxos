//! Central error management for ArxOS
//!
//! This module provides:
//! - Rich error types with context and suggestions
//! - Error recovery mechanisms
//! - User-friendly error messages
//! - Debugging information

// Submodules
pub mod analytics;
pub mod builders;
pub mod constructors;
pub mod conversions;
pub mod display;
pub mod helpers;
pub mod types;

// Re-exports from submodules
pub use analytics::ErrorAnalytics;
pub use display::ErrorDisplay;
pub use types::{ArxError, ArxResult, ErrorContext};

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
        assert_eq!(
            error.context().debug_info,
            Some("Debug information".to_string())
        );
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
            ArxError::IoError {
                message,
                context,
                path,
            } => {
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
            ArxError::IoError {
                message, context, ..
            } => {
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
            ArxError::Validation {
                message, context, ..
            } => {
                assert!(message.contains("Invalid format"));
                assert!(!context.suggestions.is_empty());
            }
            _ => panic!("Expected Validation variant"),
        }
    }
}
