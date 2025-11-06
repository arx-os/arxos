//! Building service for business logic operations
//!
//! Provides high-level operations for building management,
//! decoupled from persistence concerns.

use super::repository::{Repository, RepositoryRef};
use crate::core::Building;
use crate::yaml::BuildingData;
use std::sync::Arc;

/// Service for building operations
pub struct BuildingService {
    repository: RepositoryRef,
}

impl BuildingService {
    /// Create a new building service with the given repository
    pub fn new(repository: RepositoryRef) -> Self {
        Self { repository }
    }
    
    /// Create a building service with file-based repository (production)
    pub fn with_file_repository() -> Self {
        use super::repository::FileRepository;
        Self::new(Arc::new(FileRepository::new()))
    }
    
    /// Create a building service with in-memory repository (testing)
    pub fn with_memory_repository() -> Self {
        use super::repository::InMemoryRepository;
        Self::new(Arc::new(InMemoryRepository::new()))
    }
    
    /// Load building data
    pub fn load_building(&self, building_name: &str) -> Result<BuildingData, Box<dyn std::error::Error + Send + Sync>> {
        self.repository.load(building_name)
    }
    
    /// Save building data
    pub fn save_building(&self, building_name: &str, data: &BuildingData, commit: bool, message: Option<&str>) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if commit {
            self.repository.save_and_commit(building_name, data, message)
        } else {
            self.repository.save(building_name, data)
        }
    }
    
    /// Check if building exists
    pub fn building_exists(&self, building_name: &str) -> bool {
        self.repository.exists(building_name)
    }
    
    /// Get building info (lightweight, doesn't load full data)
    pub fn get_building_info(&self, building_name: &str) -> Result<Building, Box<dyn std::error::Error + Send + Sync>> {
        let data = self.load_building(building_name)?;
        Ok(Building::new(
            data.building.id.clone(),
            data.building.name.clone(),
        ))
    }
}

impl Default for BuildingService {
    fn default() -> Self {
        Self::with_file_repository()
    }
}

