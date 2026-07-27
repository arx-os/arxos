use thiserror::Error;

#[derive(Debug, Error)]
pub enum IfcError {
    #[error("ifc format error: {0}")]
    Format(String),
    #[error("core error: {0}")]
    Core(String),
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("not found: {0}")]
    NotFound(String),
}

impl From<arxos_core::Error> for IfcError {
    fn from(e: arxos_core::Error) -> Self {
        IfcError::Core(e.to_string())
    }
}

pub type Result<T> = std::result::Result<T, IfcError>;
