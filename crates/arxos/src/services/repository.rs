//! Repository trait for data access abstraction
//!
//! Provides a clean interface for data persistence that can be easily
//! mocked for testing or swapped for different storage backends.

use crate::yaml::BuildingData;

/// Repository trait for building data access
///
/// This trait abstracts data persistence, allowing services to work
/// with any storage backend (file system, database, in-memory, etc.)
pub trait Repository: Send + Sync {
    /// Load building data
    fn load(
        &self,
        building_name: &str,
    ) -> Result<BuildingData, Box<dyn std::error::Error + Send + Sync>>;

    /// Save building data
    fn save(
        &self,
        building_name: &str,
        data: &BuildingData,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;

    /// Save and commit building data (with Git integration)
    fn save_and_commit(
        &self,
        building_name: &str,
        data: &BuildingData,
        message: Option<&str>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;

    /// Check if building exists
    fn exists(&self, building_name: &str) -> bool;
}

/// In-memory repository for testing
///
/// Stores building data in memory, useful for unit tests and
/// scenarios where persistence is not needed.
pub struct InMemoryRepository {
    data: std::sync::RwLock<std::collections::HashMap<String, BuildingData>>,
}

impl InMemoryRepository {
    pub fn new() -> Self {
        Self {
            data: std::sync::RwLock::new(std::collections::HashMap::new()),
        }
    }
}

impl Default for InMemoryRepository {
    fn default() -> Self {
        Self::new()
    }
}

impl Repository for InMemoryRepository {
    fn load(
        &self,
        building_name: &str,
    ) -> Result<BuildingData, Box<dyn std::error::Error + Send + Sync>> {
        let data = self.data.read().unwrap();
        data.get(building_name)
            .cloned()
            .ok_or_else(|| format!("Building '{}' not found", building_name).into())
    }

    fn save(
        &self,
        building_name: &str,
        data: &BuildingData,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut storage = self.data.write().unwrap();
        storage.insert(building_name.to_string(), data.clone());
        Ok(())
    }

    fn save_and_commit(
        &self,
        building_name: &str,
        data: &BuildingData,
        _message: Option<&str>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // In-memory repository doesn't support Git commits
        self.save(building_name, data)
    }

    fn exists(&self, building_name: &str) -> bool {
        let data = self.data.read().unwrap();
        data.contains_key(building_name)
    }
}

/// File-based repository using PersistenceManager
///
/// This is the production implementation that uses the existing
/// PersistenceManager for file-based storage with Git integration.
pub struct FileRepository;

impl FileRepository {
    pub fn new() -> Self {
        Self
    }
}

impl Default for FileRepository {
    fn default() -> Self {
        Self::new()
    }
}

impl Repository for FileRepository {
    fn load(
        &self,
        building_name: &str,
    ) -> Result<BuildingData, Box<dyn std::error::Error + Send + Sync>> {
        use crate::persistence::PersistenceManager;
        let persistence = PersistenceManager::new(building_name).map_err(
            |e| -> Box<dyn std::error::Error + Send + Sync> {
                Box::new(std::io::Error::other(format!("{}", e)))
            },
        )?;
        persistence
            .load_building_data()
            .map_err(|e| -> Box<dyn std::error::Error + Send + Sync> {
                Box::new(std::io::Error::other(format!("{}", e)))
            })
    }

    fn save(
        &self,
        building_name: &str,
        data: &BuildingData,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        use crate::persistence::PersistenceManager;
        let persistence = PersistenceManager::new(building_name).map_err(
            |e| -> Box<dyn std::error::Error + Send + Sync> {
                Box::new(std::io::Error::other(format!("{}", e)))
            },
        )?;
        persistence.save_building_data(data).map_err(
            |e| -> Box<dyn std::error::Error + Send + Sync> {
                Box::new(std::io::Error::other(format!("{}", e)))
            },
        )
    }

    fn save_and_commit(
        &self,
        building_name: &str,
        data: &BuildingData,
        message: Option<&str>,
    ) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        use crate::persistence::PersistenceManager;
        let persistence = PersistenceManager::new(building_name).map_err(
            |e| -> Box<dyn std::error::Error + Send + Sync> {
                Box::new(std::io::Error::other(format!("{}", e)))
            },
        )?;
        persistence
            .save_and_commit(data, message)
            .map_err(|e| -> Box<dyn std::error::Error + Send + Sync> {
                Box::new(std::io::Error::other(format!("{}", e)))
            })
            .map(|_| ())
    }

    fn exists(&self, building_name: &str) -> bool {
        use crate::persistence::PersistenceManager;
        PersistenceManager::new(building_name)
            .and_then(|p| p.load_building_data().map(|_| ()))
            .is_ok()
    }
}
