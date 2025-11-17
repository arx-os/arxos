//! Error constructor functions
//!
//! This module provides factory methods for creating ArxError instances
//! with appropriate default contexts.

use super::types::{ArxError, ErrorContext};

impl ArxError {
    /// Create a new IFC processing error with context
    pub fn ifc_processing(message: impl Into<String>) -> Self {
        Self::IfcProcessing {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            source: None,
        }
    }

    /// Create a new configuration error with context
    pub fn configuration(message: impl Into<String>) -> Self {
        Self::Configuration {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            field: None,
        }
    }

    /// Create a new Git operation error with context
    pub fn git_operation(message: impl Into<String>, operation: impl Into<String>) -> Self {
        Self::GitOperation {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            operation: operation.into(),
        }
    }

    /// Create a new validation error with context
    pub fn validation(message: impl Into<String>) -> Self {
        Self::Validation {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            file_path: None,
        }
    }

    /// Create a new IO error with context
    pub fn io_error(message: impl Into<String>) -> Self {
        Self::IoError {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            path: None,
        }
    }

    /// Create a new YAML processing error with context
    pub fn yaml_processing(message: impl Into<String>) -> Self {
        Self::YamlProcessing {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            file_path: None,
        }
    }

    /// Create a new spatial data error with context
    pub fn spatial_data(message: impl Into<String>) -> Self {
        Self::SpatialData {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            entity_type: None,
        }
    }

    /// Create a new address validation error
    pub fn address_validation(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::AddressValidation {
            message: message.into(),
            context: Box::new(ErrorContext::default()),
            path: path.into(),
            source: None,
        }
    }

    /// Create a new counter overflow error
    pub fn counter_overflow(room: impl Into<String>, equipment_type: impl Into<String>) -> Self {
        let room = room.into();
        let equipment_type = equipment_type.into();
        Self::CounterOverflow {
            message: format!(
                "Counter overflow for room '{}' and equipment type '{}'",
                room, equipment_type
            ),
            context: Box::new(ErrorContext {
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
            }),
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
            context: Box::new(ErrorContext {
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
            }),
            path,
            expected_format,
        }
    }
}
