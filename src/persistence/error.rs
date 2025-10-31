//! Persistence error types for building data operations

use thiserror::Error;

#[derive(Debug, Error)]
pub enum PersistenceError {
    #[error("Building data file not found: {path}")]
    FileNotFound { path: String },
    
    #[error("Failed to read building data: {reason}")]
    ReadError { reason: String },
    
    #[error("Failed to write building data: {reason}")]
    WriteError { reason: String },
    
    #[error("Failed to serialize building data: {0}")]
    SerializationError(#[from] serde_yaml::Error),
    
    #[error("Failed to parse building data: {reason}")]
    DeserializationError { reason: String },
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Git operation failed: {0}")]
    GitError(String),
    
    #[error("Invalid building data structure: {reason}")]
    InvalidData { reason: String },
    
    #[error("Entity not found: {entity_type} with id {id}")]
    EntityNotFound { entity_type: String, id: String },
    
    #[error("File too large: {size}MB exceeds maximum of {max}MB")]
    FileTooLarge { size: u64, max: u64 },
}

pub type PersistenceResult<T> = Result<T, PersistenceError>;

