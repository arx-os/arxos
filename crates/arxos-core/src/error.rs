//! Error handling for ArxOS Core

use thiserror::Error;

#[cfg(feature = "git")]
use git2;

/// Result type for ArxOS operations
pub type Result<T> = std::result::Result<T, ArxError>;

/// Main error type for ArxOS
#[derive(Error, Debug)]
pub enum ArxError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[cfg(feature = "git")]
    #[error("Git error: {0}")]
    Git(#[from] git2::Error),
    
    #[cfg(not(feature = "git"))]
    #[error("Git error: {0}")]
    Git(String),
    
    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    
    #[error("Configuration error: {0}")]
    Config(String),
    
    #[error("Spatial error: {0}")]
    Spatial(String),
    
    #[error("Equipment error: {0}")]
    Equipment(String),
    
    #[error("Validation error: {0}")]
    Validation(String),
    
    #[error("Unknown error: {0}")]
    Unknown(String),
}
