//! Persistence layer for building data operations
//! 
//! This module handles loading, saving, and committing building data to YAML files and Git.

mod error;

pub use error::{PersistenceError, PersistenceResult};

use crate::yaml::{BuildingData, BuildingYamlSerializer};
use crate::git::{BuildingGitManager, GitConfigManager};
use std::path::{Path, PathBuf};
use log::{info, debug};

/// Manages persistence of building data to YAML files and Git
pub struct PersistenceManager {
    building_name: String,
    working_file: PathBuf,
    git_repo: Option<PathBuf>,
}

impl PersistenceManager {
    /// Create a new persistence manager for a building
    pub fn new(building_name: &str) -> PersistenceResult<Self> {
        let working_file = find_building_file(building_name)?;
        let git_repo = find_git_repository();
        
        debug!("Persistence manager initialized for building: {}", building_name);
        debug!("Working file: {:?}", working_file);
        debug!("Git repo: {:?}", git_repo);
        
        Ok(Self {
            building_name: building_name.to_string(),
            working_file,
            git_repo,
        })
    }
    
    /// Load building data from YAML file
    pub fn load_building_data(&self) -> PersistenceResult<BuildingData> {
        use crate::utils::path_safety::PathSafety;
        
        info!("Loading building data from: {:?}", self.working_file);
        
        // Use path-safe file reading
        let base_dir = self.working_file.parent()
            .unwrap_or_else(|| Path::new("."));
        
        let content = PathSafety::read_file_safely(&self.working_file, base_dir)
            .map_err(|e| PersistenceError::ReadError {
                reason: format!("Failed to read file {:?}: {}", self.working_file, e),
            })?;
        
        let building_data: BuildingData = serde_yaml::from_str(&content)
            .map_err(|e| PersistenceError::DeserializationError {
                reason: format!("Failed to parse YAML: {}", e),
            })?;
        
        debug!("Loaded building: {} with {} floors", 
               building_data.building.name, building_data.floors.len());
        
        Ok(building_data)
    }
    
    /// Save building data to YAML file
    pub fn save_building_data(&self, data: &BuildingData) -> PersistenceResult<()> {
        info!("Saving building data to: {:?}", self.working_file);
        
        let serializer = BuildingYamlSerializer::new();
        let yaml_content = serializer.to_yaml(data)
            .map_err(|e| PersistenceError::WriteError { 
                reason: format!("Failed to serialize building data: {}", e) 
            })?;
        
        // Use path-safe operations for file writes
        let base_dir = self.working_file.parent()
            .unwrap_or_else(|| Path::new("."));
        
        // Validate working file path before writing
        let _validated_path = crate::utils::path_safety::PathSafety::canonicalize_and_validate(
            &self.working_file,
            base_dir
        ).map_err(|e| PersistenceError::WriteError {
            reason: format!("Path validation failed: {}", e),
        })?;
        
        // Create backup of current file if it exists
        if self.working_file.exists() {
            let backup_path = self.working_file.with_extension("yaml.bak");
            // Validate backup path is within base
            let _validated_backup = crate::utils::path_safety::PathSafety::canonicalize_and_validate(
                &backup_path,
                base_dir
            ).map_err(|e| PersistenceError::WriteError {
                reason: format!("Backup path validation failed: {}", e),
            })?;
            std::fs::copy(&self.working_file, &backup_path)?;
            debug!("Created backup: {:?}", backup_path);
        }
        
        // Write new data
        std::fs::write(&self.working_file, yaml_content)
            .map_err(|e| PersistenceError::WriteError {
                reason: format!("Failed to write file {:?}: {}", self.working_file, e),
            })?;
        
        info!("Building data saved successfully");
        Ok(())
    }
    
    /// Save building data and commit to Git (if repository exists)
    pub fn save_and_commit(&self, data: &BuildingData, message: Option<&str>) -> PersistenceResult<String> {
        // First save to YAML file
        self.save_building_data(data)?;
        
        // Commit to Git if repository exists
        if let Some(ref repo_path) = self.git_repo {
            info!("Committing changes to Git repository: {:?}", repo_path);
            
            let config = GitConfigManager::default_config();
            let mut git_manager = BuildingGitManager::new(
                &repo_path.to_string_lossy(),
                &self.building_name,
                config
            ).map_err(|e| PersistenceError::GitError(e.to_string()))?;
            
            let result = git_manager.export_building(data, message)
                .map_err(|e| PersistenceError::GitError(e.to_string()))?;
            
            info!("Changes committed to Git: {}", &result.commit_id[..8]);
            Ok(result.commit_id)
        } else {
            info!("No Git repository found, changes saved to file only");
            Ok("no-git-repo".to_string())
        }
    }
    
    /// Get the working file path
    pub fn working_file(&self) -> &Path {
        &self.working_file
    }
    
    /// Check if Git repository exists
    pub fn has_git_repo(&self) -> bool {
        self.git_repo.is_some()
    }
}

/// Find building YAML file in current directory
fn find_building_file(building_name: &str) -> PersistenceResult<PathBuf> {
    use crate::utils::path_safety::PathSafety;
    
    let current_dir = std::env::current_dir()
        .map_err(|e| PersistenceError::IoError(e))?;
    
    // Look for YAML files in current directory with path safety
    let yaml_files: Vec<PathBuf> = PathSafety::read_dir_safely(std::path::Path::new("."), &current_dir)
        .map_err(|e| PersistenceError::ReadError {
            reason: format!("Failed to read directory: {}", e),
        })?
        .into_iter()
        .filter(|path| {
            path.extension()
                .and_then(|s| s.to_str())
                .map(|ext| ext == "yaml" || ext == "yml")
                .unwrap_or(false)
        })
        .collect();
    
    // Try to find a file that matches the building name
    let matching_file = yaml_files.iter()
        .find(|path| {
            path.file_stem()
                .and_then(|s| s.to_str())
                .map(|s| s.to_lowercase().contains(&building_name.to_lowercase()))
                .unwrap_or(false)
        })
        .or_else(|| yaml_files.first())
        .ok_or_else(|| PersistenceError::FileNotFound {
            path: format!("No YAML files found for building '{}' in current directory", building_name),
        })?;
    
    Ok(matching_file.clone())
}

/// Find Git repository in current directory or parent directories
fn find_git_repository() -> Option<PathBuf> {
    let mut current_path = std::env::current_dir().ok()?;
    
    loop {
        let git_path = current_path.join(".git");
        if git_path.exists() {
            return Some(current_path);
        }
        
        if !current_path.pop() {
            break;
        }
    }
    
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    
    #[test]
    fn test_save_and_load_building_data() {
        let temp_dir = TempDir::new().unwrap();
        std::env::set_current_dir(temp_dir.path()).unwrap();
        
        // Create a test building file
        let test_file = temp_dir.path().join("test_building.yaml");
        let building_data = BuildingData {
            building: BuildingInfo {
                id: "test-1".to_string(),
                name: "Test Building".to_string(),
                description: Some("Test".to_string()),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: Some("test.ifc".to_string()),
                parser_version: "1.0".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "World".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![],
        };
        
        // Save the test file
        let serializer = BuildingYamlSerializer::new();
        let yaml_content = serializer.to_yaml(&building_data).unwrap();
        std::fs::write(&test_file, yaml_content).unwrap();
        
        // Load using persistence manager
        let persistence = PersistenceManager::new("Test Building").unwrap();
        let loaded_data = persistence.load_building_data().unwrap();
        
        assert_eq!(loaded_data.building.name, "Test Building");
    }
}

