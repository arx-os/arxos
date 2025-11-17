//! Error context builder methods
//!
//! This module provides builder methods for adding context, suggestions,
//! and recovery information to ArxError instances.

use super::types::{ArxError, ErrorContext};

impl ArxError {
    /// Add suggestions to an error
    pub fn with_suggestions(mut self, suggestions: Vec<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. }
            | ArxError::Configuration { context, .. }
            | ArxError::GitOperation { context, .. }
            | ArxError::Validation { context, .. }
            | ArxError::IoError { context, .. }
            | ArxError::YamlProcessing { context, .. }
            | ArxError::SpatialData { context, .. }
            | ArxError::AddressValidation { context, .. }
            | ArxError::CounterOverflow { context, .. }
            | ArxError::PathInvalid { context, .. } => {
                context.suggestions = suggestions;
            }
        }
        self
    }

    /// Add recovery steps to an error
    pub fn with_recovery(mut self, recovery_steps: Vec<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. }
            | ArxError::Configuration { context, .. }
            | ArxError::GitOperation { context, .. }
            | ArxError::Validation { context, .. }
            | ArxError::IoError { context, .. }
            | ArxError::YamlProcessing { context, .. }
            | ArxError::SpatialData { context, .. }
            | ArxError::AddressValidation { context, .. }
            | ArxError::CounterOverflow { context, .. }
            | ArxError::PathInvalid { context, .. } => {
                context.recovery_steps = recovery_steps;
            }
        }
        self
    }

    /// Add debug information to an error
    pub fn with_debug_info(mut self, debug_info: impl Into<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. }
            | ArxError::Configuration { context, .. }
            | ArxError::GitOperation { context, .. }
            | ArxError::Validation { context, .. }
            | ArxError::IoError { context, .. }
            | ArxError::YamlProcessing { context, .. }
            | ArxError::SpatialData { context, .. }
            | ArxError::AddressValidation { context, .. }
            | ArxError::CounterOverflow { context, .. }
            | ArxError::PathInvalid { context, .. } => {
                context.debug_info = Some(debug_info.into());
            }
        }
        self
    }

    /// Add file path context to an error
    pub fn with_file_path(mut self, file_path: impl Into<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. }
            | ArxError::Configuration { context, .. }
            | ArxError::GitOperation { context, .. }
            | ArxError::Validation { context, .. }
            | ArxError::IoError { context, .. }
            | ArxError::YamlProcessing { context, .. }
            | ArxError::SpatialData { context, .. }
            | ArxError::AddressValidation { context, .. }
            | ArxError::CounterOverflow { context, .. }
            | ArxError::PathInvalid { context, .. } => {
                context.file_path = Some(file_path.into());
            }
        }
        self
    }

    /// Add line number context to an error
    pub fn with_line_number(mut self, line_number: usize) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. }
            | ArxError::Configuration { context, .. }
            | ArxError::GitOperation { context, .. }
            | ArxError::Validation { context, .. }
            | ArxError::IoError { context, .. }
            | ArxError::YamlProcessing { context, .. }
            | ArxError::SpatialData { context, .. }
            | ArxError::AddressValidation { context, .. }
            | ArxError::CounterOverflow { context, .. }
            | ArxError::PathInvalid { context, .. } => {
                context.line_number = Some(line_number);
            }
        }
        self
    }

    /// Add help URL to an error
    pub fn with_help_url(mut self, help_url: impl Into<String>) -> Self {
        match &mut self {
            ArxError::IfcProcessing { context, .. }
            | ArxError::Configuration { context, .. }
            | ArxError::GitOperation { context, .. }
            | ArxError::Validation { context, .. }
            | ArxError::IoError { context, .. }
            | ArxError::YamlProcessing { context, .. }
            | ArxError::SpatialData { context, .. }
            | ArxError::AddressValidation { context, .. }
            | ArxError::CounterOverflow { context, .. }
            | ArxError::PathInvalid { context, .. } => {
                context.help_url = Some(help_url.into());
            }
        }
        self
    }

    /// Get the error context
    pub fn context(&self) -> &ErrorContext {
        match self {
            ArxError::IfcProcessing { context, .. }
            | ArxError::Configuration { context, .. }
            | ArxError::GitOperation { context, .. }
            | ArxError::Validation { context, .. }
            | ArxError::IoError { context, .. }
            | ArxError::YamlProcessing { context, .. }
            | ArxError::SpatialData { context, .. }
            | ArxError::AddressValidation { context, .. }
            | ArxError::CounterOverflow { context, .. }
            | ArxError::PathInvalid { context, .. } => context.as_ref(),
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
