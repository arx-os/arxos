//! Persistence layer for ArxOS data storage
//!
//! Provides file system and Git-based persistence for building data,
//! economy snapshots, and other core data structures.

pub mod economy;
pub mod manager;

use std::error::Error;
use std::fmt;

/// Persistence error types
#[derive(Debug)]
pub enum PersistenceError {
    IoError(std::io::Error),
    SerializationError(String),
    ValidationError(String),
}

impl fmt::Display for PersistenceError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PersistenceError::IoError(err) => write!(f, "IO error: {}", err),
            PersistenceError::SerializationError(msg) => write!(f, "Serialization error: {}", msg),
            PersistenceError::ValidationError(msg) => write!(f, "Validation error: {}", msg),
        }
    }
}

impl Error for PersistenceError {}

impl From<std::io::Error> for PersistenceError {
    fn from(err: std::io::Error) -> Self {
        PersistenceError::IoError(err)
    }
}

impl From<serde_yaml::Error> for PersistenceError {
    fn from(err: serde_yaml::Error) -> Self {
        PersistenceError::SerializationError(err.to_string())
    }
}

pub type PersistenceResult<T> = Result<T, PersistenceError>;

pub use economy::{load_snapshot, save_snapshot, append_contribution};
pub use manager::PersistenceManager;