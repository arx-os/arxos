// Error types for ArxOS IFC processing
use thiserror::Error;

#[derive(Error, Debug)]
pub enum IFCError {
    #[error("IFC file not found: {path}")]
    FileNotFound { path: String },

    #[error("Invalid IFC file format: {reason}")]
    InvalidFormat { reason: String },

    #[error("IFC parsing error: {message}")]
    ParsingError { message: String },

    #[error("Spatial data extraction failed: {reason}")]
    SpatialExtractionError { reason: String },

    #[error("Coordinate transformation failed: {reason}")]
    CoordinateTransformError { reason: String },

    #[error("IFC file too large: {size}MB exceeds maximum of {max}MB")]
    FileTooLarge { size: u64, max: u64 },

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Generic error: {0}")]
    Generic(#[from] anyhow::Error),
}

pub type IFCResult<T> = Result<T, IFCError>;
