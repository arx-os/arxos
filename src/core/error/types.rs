//! Core error type definitions
//!
//! This module contains the main error types and error context structures
//! used throughout ArxOS.

use serde::{Deserialize, Serialize};
use thiserror::Error;

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
        context: Box<ErrorContext>,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },

    #[error("Configuration Error: {message}")]
    Configuration {
        message: String,
        context: Box<ErrorContext>,
        field: Option<String>,
    },

    #[error("Git Operation Error: {message}")]
    GitOperation {
        message: String,
        context: Box<ErrorContext>,
        operation: String,
    },

    #[error("Validation Error: {message}")]
    Validation {
        message: String,
        context: Box<ErrorContext>,
        file_path: Option<String>,
    },

    #[error("IO Error: {message}")]
    IoError {
        message: String,
        context: Box<ErrorContext>,
        path: Option<String>,
    },

    #[error("YAML Processing Error: {message}")]
    YamlProcessing {
        message: String,
        context: Box<ErrorContext>,
        file_path: Option<String>,
    },

    #[error("Spatial Data Error: {message}")]
    SpatialData {
        message: String,
        context: Box<ErrorContext>,
        entity_type: Option<String>,
    },

    #[error("Address Validation Error: {message}")]
    AddressValidation {
        message: String,
        context: Box<ErrorContext>,
        path: String,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },

    #[error("Counter Overflow Error: {message}")]
    CounterOverflow {
        message: String,
        context: Box<ErrorContext>,
        room: String,
        equipment_type: String,
    },

    #[error("Path Invalid Error: {message}")]
    PathInvalid {
        message: String,
        context: Box<ErrorContext>,
        path: String,
        expected_format: String,
    },
}

/// Result type alias for ArxOS operations
pub type ArxResult<T> = Result<T, ArxError>;
