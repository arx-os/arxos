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

pub use manager::PersistenceManager;

/// Load building data from the current directory
///
/// Searches the current directory for a building YAML file and loads it.
/// Returns the first valid building file found.
pub fn load_building_data_from_dir() -> Result<crate::yaml::BuildingData, Box<dyn std::error::Error>> {
    use std::fs;
    

    let current_dir = std::env::current_dir()?;

    // Look for YAML files in the current directory
    let entries = fs::read_dir(&current_dir)?;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();

        // Check if it's a YAML file
        if path.is_file() {
            if let Some(extension) = path.extension() {
                if extension == "yaml" || extension == "yml" {
                    // Try to load it as building data
                    if let Ok(contents) = fs::read_to_string(&path) {
                        if let Ok(building_data) = serde_yaml::from_str::<crate::yaml::BuildingData>(&contents) {
                            return Ok(building_data);
                        }
                    }
                }
            }
        }
    }

    Err("No valid building YAML file found in current directory".into())
}