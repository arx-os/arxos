//! Networking error types.

use thiserror::Error;

/// Networking / sync error.
#[derive(Debug, Error)]
pub enum NetError {
    #[error("protocol error: {0}")]
    Protocol(String),

    #[error("peer not found: {0}")]
    PeerNotFound(String),

    #[error("object missing on peer: {0}")]
    ObjectMissing(String),

    #[error("transport error: {0}")]
    Transport(String),

    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("core error: {0}")]
    Core(String),

    #[error("timeout: {0}")]
    Timeout(String),

    #[error("discovery error: {0}")]
    Discovery(String),

    #[error("serialization error: {0}")]
    Serialization(String),
}

impl From<arxos_core::Error> for NetError {
    fn from(e: arxos_core::Error) -> Self {
        NetError::Core(e.to_string())
    }
}

/// Result alias for networking.
pub type Result<T> = std::result::Result<T, NetError>;
