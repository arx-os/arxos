//! Error types for arxos-core.

use thiserror::Error;

/// Core library error.
#[derive(Debug, Error)]
pub enum Error {
    #[error("serialization error: {0}")]
    Serialization(String),

    #[error("deserialization error: {0}")]
    Deserialization(String),

    #[error("invalid CID: {0}")]
    InvalidCid(String),

    #[error("object not found: {0}")]
    NotFound(String),

    #[error("store error: {0}")]
    Store(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("signature error: {0}")]
    Signature(String),

    /// Author is not in the building controller set (or controllers could not be resolved).
    #[error("authorization error: {0}")]
    Authorization(String),

    #[error("validation error: {0}")]
    Validation(String),

    #[error("schema error: {0}")]
    Schema(String),

    #[error("crypto error: {0}")]
    Crypto(String),
}

/// Result alias for arxos-core.
pub type Result<T> = std::result::Result<T, Error>;
