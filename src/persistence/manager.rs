//! Persistence manager for building data and other core entities

use super::{PersistenceError, PersistenceResult};
use std::path::{Path, PathBuf};

/// Manager for persisting building and related data
pub struct PersistenceManager {
    base_path: PathBuf,
    building_name: String,
}

impl PersistenceManager {
    pub fn new(building_name: &str) -> PersistenceResult<Self> {
        let base_path = std::env::current_dir()
            .map_err(|e| PersistenceError::IoError(e))?;
        
        Ok(Self {
            base_path,
            building_name: building_name.to_string(),
        })
    }

    pub fn with_path<P: AsRef<Path>>(base_path: P, building_name: &str) -> Self {
        Self {
            base_path: base_path.as_ref().to_path_buf(),
            building_name: building_name.to_string(),
        }
    }

    pub fn building_path(&self) -> PathBuf {
        self.base_path.join(&self.building_name)
    }

    /// Save building data to YAML file
    pub fn save_building_data(&self, data: &crate::yaml::BuildingData) -> PersistenceResult<()> {
        use std::fs;

        // Ensure the building directory exists
        let building_dir = self.building_path();
        if !building_dir.exists() {
            fs::create_dir_all(&building_dir)?;
        }

        // Serialize building data to YAML
        let yaml_content = serde_yaml::to_string(data)?;

        // Write to building.yaml file
        let file_path = building_dir.join("building.yaml");
        fs::write(&file_path, yaml_content)?;

        Ok(())
    }

    /// Load building data from YAML file
    pub fn load_building_data(&self) -> PersistenceResult<crate::yaml::BuildingData> {
        use std::fs;

        // Try to load from building.yaml first
        let file_path = self.building_path().join("building.yaml");

        if file_path.exists() {
            let yaml_content = fs::read_to_string(&file_path)?;
            let building_data = serde_yaml::from_str(&yaml_content)?;
            return Ok(building_data);
        }

        // If building.yaml doesn't exist, search for any YAML file in the directory
        let building_dir = self.building_path();
        if building_dir.exists() && building_dir.is_dir() {
            for entry in fs::read_dir(&building_dir)? {
                let entry = entry?;
                let path = entry.path();

                if path.is_file() {
                    if let Some(extension) = path.extension() {
                        if extension == "yaml" || extension == "yml" {
                            if let Ok(yaml_content) = fs::read_to_string(&path) {
                                if let Ok(building_data) = serde_yaml::from_str::<crate::yaml::BuildingData>(&yaml_content) {
                                    return Ok(building_data);
                                }
                            }
                        }
                    }
                }
            }
        }

        // If no valid file found, return validation error
        Err(PersistenceError::ValidationError(
            format!("No valid building data found at {}", file_path.display())
        ))
    }

    /// Save and commit building data with optional commit message
    ///
    /// Saves the building data to disk and, if a Git repository exists,
    /// stages and commits the changes.
    pub fn save_and_commit(&self, data: &crate::yaml::BuildingData, message: Option<&str>) -> PersistenceResult<()> {
        // First, save the data to disk
        self.save_building_data(data)?;

        // If there's a Git repository, commit the changes
        if self.has_git_repo() {
            self.commit_changes(message)?;
        }

        Ok(())
    }

    /// Commit changes to Git repository
    fn commit_changes(&self, message: Option<&str>) -> PersistenceResult<()> {
        use git2::{Repository, Signature};

        let repo = Repository::open(&self.base_path)
            .map_err(|e| PersistenceError::SerializationError(format!("Failed to open Git repository: {}", e)))?;

        // Stage all changes
        let mut index = repo.index()
            .map_err(|e| PersistenceError::SerializationError(format!("Failed to get Git index: {}", e)))?;

        index.add_all(["*"].iter(), git2::IndexAddOption::DEFAULT, None)
            .map_err(|e| PersistenceError::SerializationError(format!("Failed to stage changes: {}", e)))?;

        index.write()
            .map_err(|e| PersistenceError::SerializationError(format!("Failed to write Git index: {}", e)))?;

        let tree_id = index.write_tree()
            .map_err(|e| PersistenceError::SerializationError(format!("Failed to write tree: {}", e)))?;

        let tree = repo.find_tree(tree_id)
            .map_err(|e| PersistenceError::SerializationError(format!("Failed to find tree: {}", e)))?;

        // Get or create signature
        let signature = match Signature::now("ArxOS", "arxos@example.com") {
            Ok(sig) => sig,
            Err(_) => {
                // If signature creation fails, try to get from config
                let config = repo.config()
                    .map_err(|e| PersistenceError::SerializationError(format!("Failed to get Git config: {}", e)))?;

                let name = config.get_string("user.name").unwrap_or_else(|_| "ArxOS".to_string());
                let email = config.get_string("user.email").unwrap_or_else(|_| "arxos@example.com".to_string());

                Signature::now(&name, &email)
                    .map_err(|e| PersistenceError::SerializationError(format!("Failed to create signature: {}", e)))?
            }
        };

        // Get parent commits
        let parents: Vec<git2::Commit> = match repo.head() {
            Ok(head) => {
                if let Some(target) = head.target() {
                    match repo.find_commit(target) {
                        Ok(parent) => vec![parent],
                        Err(_) => vec![],
                    }
                } else {
                    vec![]
                }
            }
            Err(_) => vec![],
        };

        let parent_refs: Vec<&git2::Commit> = parents.iter().collect();

        // Create commit
        let commit_message = message.unwrap_or("Update building data");
        repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            commit_message,
            &tree,
            &parent_refs,
        ).map_err(|e| PersistenceError::SerializationError(format!("Failed to create commit: {}", e)))?;

        Ok(())
    }

    /// Check if the base path has a Git repository
    pub fn has_git_repo(&self) -> bool {
        self.base_path.join(".git").exists()
    }

    /// Get the working file path (building.yaml or similar)
    pub fn working_file(&self) -> PathBuf {
        self.building_path().join("building.yaml")
    }
}