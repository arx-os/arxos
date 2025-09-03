//! Centralized error handling for ArxOS
//! 
//! Using thiserror for ergonomic error types that work well with ? operator

use thiserror::Error;
use std::fmt;

/// Main ArxOS error type
#[derive(Error, Debug)]
pub enum ArxError {
    // Transport errors
    #[error("Transport error: {0}")]
    Transport(#[from] crate::transport::TransportError),
    
    // ArxObject errors
    #[error("Invalid ArxObject: {0}")]
    InvalidArxObject(String),
    
    #[error("ArxObject validation failed: {0}")]
    ValidationError(String),
    
    // Compression errors
    #[error("Compression failed: {0}")]
    CompressionError(String),
    
    #[error("Decompression failed: {0}")]
    DecompressionError(String),
    
    #[error("Compression ratio {0:.1}:1 below minimum {1}:1")]
    InsufficientCompression(f64, u32),
    
    // Database errors
    #[cfg(feature = "std")]
    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),
    
    // Game engine errors
    #[error("Game error: {0}")]
    GameError(String),
    
    #[error("Invalid move: {0}")]
    InvalidMove(String),
    
    #[error("Object not found: {0}")]
    ObjectNotFound(String),
    
    #[error("Not found: {0}")]
    NotFound(String),
    
    // Input errors
    #[error("Invalid input: {0}")]
    InvalidInput(String),
    
    // Parsing errors
    #[error("Parse error: {0}")]
    ParseError(String),
    
    #[error("Invalid ASCII format: {0}")]
    InvalidAscii(String),
    
    // IO errors
    #[cfg(feature = "std")]
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    // Configuration errors
    #[error("Configuration error: {0}")]
    Config(String),
    
    // Generic errors
    #[error("Operation not supported: {0}")]
    NotSupported(String),
    
    #[error("Not implemented: {0}")]
    NotImplemented(String),
    
    #[error("Internal error: {0}")]
    Internal(String),
}

/// Result type alias for ArxOS operations
pub type Result<T> = std::result::Result<T, ArxError>;

/// Extension trait for adding context to errors
pub trait ErrorContext<T> {
    /// Add context to an error
    fn context<C>(self, context: C) -> Result<T>
    where
        C: fmt::Display + Send + Sync + 'static;
    
    /// Add context with a closure (lazy evaluation)
    fn with_context<C, F>(self, f: F) -> Result<T>
    where
        C: fmt::Display + Send + Sync + 'static,
        F: FnOnce() -> C;
}

impl<T, E> ErrorContext<T> for std::result::Result<T, E>
where
    E: Into<ArxError>,
{
    fn context<C>(self, context: C) -> Result<T>
    where
        C: fmt::Display + Send + Sync + 'static,
    {
        self.map_err(|e| {
            let base_error = e.into();
            ArxError::Internal(format!("{}: {}", context, base_error))
        })
    }
    
    fn with_context<C, F>(self, f: F) -> Result<T>
    where
        C: fmt::Display + Send + Sync + 'static,
        F: FnOnce() -> C,
    {
        self.map_err(|e| {
            let base_error = e.into();
            ArxError::Internal(format!("{}: {}", f(), base_error))
        })
    }
}

/// Validation error for ArxObjects
#[derive(Error, Debug, Clone)]
pub enum ValidationError {
    #[error("Invalid building ID: {0}")]
    InvalidBuildingId(u16),
    
    #[error("Invalid object type: {0:#04x}")]
    InvalidObjectType(u8),
    
    #[error("Coordinate out of range: {axis}={value} (max: {max})")]
    CoordinateOutOfRange {
        axis: char,
        value: u16,
        max: u16,
    },
    
    #[error("Invalid properties for object type {0:#04x}")]
    InvalidProperties(u8),
    
    #[error("Checksum mismatch: expected {expected:#04x}, got {actual:#04x}")]
    ChecksumMismatch {
        expected: u8,
        actual: u8,
    },
}

/// Ensure errors work in no_std environments
#[cfg(not(feature = "std"))]
impl From<core::fmt::Error> for ArxError {
    fn from(e: core::fmt::Error) -> Self {
        ArxError::Internal("Formatting error".into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_error_context() {
        fn failing_operation() -> Result<()> {
            Err(ArxError::InvalidArxObject("test".into()))
        }
        
        let result = failing_operation()
            .context("While processing building 42");
        
        assert!(result.is_err());
        let error = result.unwrap_err();
        assert!(format!("{}", error).contains("While processing building 42"));
    }
    
    #[test]
    fn test_error_conversion() {
        use crate::transport::TransportError;
        
        fn transport_operation() -> std::result::Result<(), TransportError> {
            Err(TransportError::NotConnected)
        }
        
        let result: Result<()> = transport_operation()
            .map_err(|e| e.into());
        
        assert!(result.is_err());
        matches!(result.unwrap_err(), ArxError::Transport(_));
    }
}