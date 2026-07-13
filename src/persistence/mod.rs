//! Persistence layer for ArxOS data storage
//!
//! Durable Building SSOT: `{dir}/building.yaml` via `BuildingYamlSerializer`.

pub mod economy;
pub mod manager;

use thiserror::Error;

/// Persistence error types
#[derive(Debug, Error)]
pub enum PersistenceError {
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Validation error: {0}")]
    ValidationError(String),
}

impl From<serde_yaml::Error> for PersistenceError {
    fn from(err: serde_yaml::Error) -> Self {
        PersistenceError::SerializationError(err.to_string())
    }
}

pub type PersistenceResult<T> = Result<T, PersistenceError>;

pub use manager::{PersistenceManager, BUILDING_YAML};

/// Load the canonical Building from `./building.yaml`.
pub fn load_building_data_from_dir() -> Result<crate::core::Building, Box<dyn std::error::Error>> {
    let pm = PersistenceManager::from_cwd()?;
    Ok(pm.load_building_data()?)
}

/// Load Building from `{base}/building.yaml`.
pub fn load_building_at(
    base: impl AsRef<std::path::Path>,
) -> Result<crate::core::Building, Box<dyn std::error::Error>> {
    let pm = PersistenceManager::at(base.as_ref());
    Ok(pm.load_building_data()?)
}

/// Save Building to `{base}/building.yaml` with validation hard-gate.
pub fn save_building_at(
    base: impl AsRef<std::path::Path>,
    building: &crate::core::Building,
) -> Result<(), Box<dyn std::error::Error>> {
    let pm = PersistenceManager::at(base.as_ref());
    pm.save_building_validated(building)?;
    Ok(())
}

/// Serialize-only save (no validation). Prefer `save_building_at` for production.
pub fn save_building_unchecked_at(
    base: impl AsRef<std::path::Path>,
    building: &crate::core::Building,
) -> Result<(), Box<dyn std::error::Error>> {
    let pm = PersistenceManager::at(base.as_ref());
    pm.save_building_unchecked(building)?;
    Ok(())
}
