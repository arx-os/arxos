//! # Error Handling for ArxOS Core
//!
//! This module provides comprehensive error handling for ArxOS operations,
//! including domain-specific error types, error context, and recovery suggestions.
//!
//! ## Error Categories
//!
//! - **Spatial Errors**: Coordinate system, spatial operations, and geometry errors
//! - **Equipment Errors**: Equipment management and validation errors
//! - **Room Errors**: Room operations and spatial organization errors
//! - **Git Errors**: Version control and repository operation errors
//! - **Configuration Errors**: Settings and configuration validation errors
//! - **Validation Errors**: Data integrity and format validation errors
//!
//! ## Error Context and Recovery
//!
//! Each error type includes context information and recovery suggestions
//! to help users understand and resolve issues quickly.

use thiserror::Error;

#[cfg(feature = "git")]
use git2;

/// Result type for ArxOS operations
pub type Result<T> = std::result::Result<T, ArxError>;

/// Main error type for ArxOS with comprehensive error categories
#[derive(Error, Debug)]
pub enum ArxError {
    // Standard library errors
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    // Serialization errors
    #[error("YAML parsing error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    
    #[error("JSON parsing error: {0}")]
    Json(#[from] serde_json::Error),
    
    // Git errors
    #[cfg(feature = "git")]
    #[error("Git operation failed: {0}")]
    Git(#[from] git2::Error),
    
    #[cfg(not(feature = "git"))]
    #[error("Git operation failed: {0}")]
    Git(String),
    
    // Spatial errors
    #[error("Spatial operation failed: {message}")]
    SpatialError { 
        message: String,
        #[source] 
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Invalid coordinate system: {system}. Expected one of: {valid_systems}")]
    InvalidCoordinateSystem { 
        system: String, 
        valid_systems: String 
    },
    
    #[error("Spatial query failed: {query}. Reason: {reason}")]
    SpatialQueryFailed { 
        query: String, 
        reason: String 
    },
    
    #[error("Coordinate transformation error: {from} -> {to}. Reason: {reason}")]
    CoordinateTransformationFailed { 
        from: String, 
        to: String, 
        reason: String 
    },
    
    // Equipment errors
    #[error("Equipment operation failed: {message}")]
    EquipmentError { 
        message: String,
        #[source] 
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Invalid equipment type: {equipment_type}. Valid types: {valid_types}")]
    InvalidEquipmentType { 
        equipment_type: String, 
        valid_types: String 
    },
    
    #[error("Equipment not found: {equipment_id}")]
    EquipmentNotFound { equipment_id: String },
    
    #[error("Equipment validation failed: {field} - {message}")]
    EquipmentValidationFailed { 
        field: String, 
        message: String 
    },
    
    // Room errors
    #[error("Room operation failed: {message}")]
    RoomError { 
        message: String,
        #[source] 
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Invalid room type: {room_type}. Valid types: {valid_types}")]
    InvalidRoomType { 
        room_type: String, 
        valid_types: String 
    },
    
    #[error("Room not found: {room_id}")]
    RoomNotFound { room_id: String },
    
    #[error("Room validation failed: {field} - {message}")]
    RoomValidationFailed { 
        field: String, 
        message: String 
    },
    
    #[error("Duplicate room level: {level}")]
    DuplicateRoomLevel { level: i32 },
    
    // Configuration errors
    #[error("Configuration error: {message}")]
    ConfigError { 
        message: String,
        #[source] 
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Configuration validation failed: {field} - {message}")]
    ConfigValidationFailed { 
        field: String, 
        message: String 
    },
    
    #[error("Configuration file not found: {path}")]
    ConfigFileNotFound { path: String },
    
    // Validation errors
    #[error("Data validation failed: {message}")]
    ValidationError { 
        message: String,
        #[source] 
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Required field missing: {field}")]
    RequiredFieldMissing { field: String },
    
    #[error("Invalid data format: {field} - {expected_format}")]
    InvalidDataFormat { 
        field: String, 
        expected_format: String 
    },
    
    // Terminal errors
    #[cfg(feature = "terminal")]
    #[error("Terminal operation failed: {message}")]
    TerminalError { 
        message: String,
        #[source] 
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    // Generic errors
    #[error("Unknown error: {message}")]
    Unknown { 
        message: String,
        #[source] 
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
}

// Convenience constructors for common error types
impl ArxError {
    /// Create a spatial error with context
    pub fn spatial_error(message: impl Into<String>) -> Self {
        Self::SpatialError { 
            message: message.into(), 
            source: None 
        }
    }
    
    /// Create an equipment error with context
    pub fn equipment_error(message: impl Into<String>) -> Self {
        Self::EquipmentError { 
            message: message.into(), 
            source: None 
        }
    }
    
    /// Create a room error with context
    pub fn room_error(message: impl Into<String>) -> Self {
        Self::RoomError { 
            message: message.into(), 
            source: None 
        }
    }
    
    /// Create a configuration error with context
    pub fn config_error(message: impl Into<String>) -> Self {
        Self::ConfigError { 
            message: message.into(), 
            source: None 
        }
    }
    
    /// Create a validation error with context
    pub fn validation_error(message: impl Into<String>) -> Self {
        Self::ValidationError { 
            message: message.into(), 
            source: None 
        }
    }
    
    /// Get recovery suggestions for the error
    pub fn recovery_suggestions(&self) -> Vec<&'static str> {
        match self {
            Self::InvalidCoordinateSystem { .. } => {
                vec![
                    "Check the coordinate system specification",
                    "Use one of the supported coordinate systems",
                    "Verify the input data format"
                ]
            }
            Self::EquipmentNotFound { .. } => {
                vec![
                    "Verify the equipment ID exists",
                    "Check if the equipment was deleted",
                    "Use 'equipment list' to see available equipment"
                ]
            }
            Self::RoomNotFound { .. } => {
                vec![
                    "Verify the room ID exists",
                    "Check if the room was deleted",
                    "Use 'room list' to see available rooms"
                ]
            }
            Self::ConfigFileNotFound { .. } => {
                vec![
                    "Create a configuration file using 'config --edit'",
                    "Check the file path is correct",
                    "Use default configuration with 'config --reset'"
                ]
            }
            Self::RequiredFieldMissing { .. } => {
                vec![
                    "Check the input data includes all required fields",
                    "Verify the data format matches expectations",
                    "Use validation tools to check data integrity"
                ]
            }
            _ => vec!["Check the error message for specific details", "Verify input data format"]
        }
    }
}
