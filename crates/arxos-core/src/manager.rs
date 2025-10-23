// Git operations for ArxOS Core - Conditional compilation based on features

#[cfg(feature = "git")]
mod git_impl {
    use git2::{Repository, Signature};
    use std::path::Path;
    use std::collections::HashMap;
    use serde::{Serialize, Deserialize};
    use log::info;
    use crate::path::PathGenerator;
    use crate::yaml::{BuildingData, BuildingYamlSerializer};

    /// Git repository manager for building data
    pub struct BuildingGitManager {
        repo: Repository,
        serializer: BuildingYamlSerializer,
        #[allow(dead_code)]
        path_generator: PathGenerator,
    }

    /// Git operation results
    #[derive(Debug)]
    pub struct GitOperationResult {
        pub commit_id: String,
        pub files_changed: usize,
        pub message: String,
    }

    /// Git repository configuration
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct GitConfig {
        pub author_name: String,
        pub author_email: String,
        pub branch: String,
        pub remote_url: Option<String>,
    }

    impl BuildingGitManager {
        /// Initialize or open a Git repository for building data
        pub fn new(repo_path: &str, building_name: &str, _config: GitConfig) -> Result<Self, GitError> {
            let repo_path_buf = Path::new(repo_path);
            
            // Ensure the directory exists
            if !repo_path_buf.exists() {
                std::fs::create_dir_all(repo_path_buf)?;
            }
            
            let repo = if repo_path_buf.join(".git").exists() {
                Repository::open(repo_path)?
            } else {
                Repository::init(repo_path)?
            };

            let serializer = BuildingYamlSerializer::new();
            let path_generator = PathGenerator::new(building_name);

            Ok(Self {
                repo,
                serializer,
                path_generator,
            })
        }

        /// Export building data to Git repository
        pub fn export_building(
            &mut self,
            building_data: &BuildingData,
            commit_message: Option<&str>,
        ) -> Result<GitOperationResult, GitError> {
            info!("Exporting building data to Git repository");

            // Create directory structure
            let file_structure = self.create_file_structure(building_data)?;
            
            // Write files to repository
            let mut files_changed = 0;
            let file_paths: Vec<String> = file_structure.keys().cloned().collect();
            
            for (file_path, content) in file_structure {
                let full_path = self.repo.path().parent().unwrap().join(&file_path);
                
                // Create parent directories if they don't exist
                if let Some(parent) = full_path.parent() {
                    std::fs::create_dir_all(parent)?;
                }
                
                std::fs::write(&full_path, content)?;
                files_changed += 1;
            }

            // Commit changes
            let commit_id = self.commit_changes(
                commit_message.unwrap_or("Update building data"),
                &file_paths,
            )?;

            info!("Successfully exported building data: {} files changed", files_changed);

            Ok(GitOperationResult {
                commit_id,
                files_changed,
                message: commit_message.unwrap_or("Update building data").to_string(),
            })
        }

        /// Create file structure for building data
        fn create_file_structure(&mut self, building_data: &BuildingData) -> Result<HashMap<String, String>, GitError> {
            let mut files = HashMap::new();

            // Main building file
            let building_yaml = self.serializer.to_yaml(building_data)?;
            files.insert("building.yml".to_string(), building_yaml);

            // Floor files
            for floor in &building_data.floors {
                let floor_path = format!("floors/floor-{}.yml", floor.level);
                let floor_yaml = self.serializer.to_yaml(floor)?;
                files.insert(floor_path, floor_yaml);

                // Room files
                for room in &floor.rooms {
                    let room_path = format!("floors/floor-{}/rooms/{}.yml", floor.level, room.name.to_lowercase().replace(" ", "-"));
                    let room_yaml = self.serializer.to_yaml(room)?;
                    files.insert(room_path, room_yaml);
                }

                // Equipment files
                for equipment in &floor.equipment {
                    let equipment_path = format!("floors/floor-{}/equipment/{}/{}.yml", 
                        floor.level, 
                        equipment.system_type.to_lowercase(), 
                        equipment.name.to_lowercase().replace(" ", "-")
                    );
                    let equipment_yaml = self.serializer.to_yaml(equipment)?;
                    files.insert(equipment_path, equipment_yaml);
                }
            }

            // Create index file for easy navigation
            let index_content = self.create_index_file(building_data)?;
            files.insert("index.yml".to_string(), index_content);

            Ok(files)
        }

        /// Create index file for building navigation
        fn create_index_file(&self, building_data: &BuildingData) -> Result<String, GitError> {
            let mut index = serde_yaml::to_string(&serde_yaml::Value::Mapping(serde_yaml::Mapping::new()))?;
            
            // Add building metadata
            index.push_str(&format!("building:\n"));
            index.push_str(&format!("  name: {}\n", building_data.building.name));
            index.push_str(&format!("  id: {}\n", building_data.building.id));
            index.push_str(&format!("  floors: {}\n", building_data.floors.len()));
            
            // Add floor information
            index.push_str(&format!("floors:\n"));
            for floor in &building_data.floors {
                index.push_str(&format!("  - level: {}\n", floor.level));
                index.push_str(&format!("    name: {}\n", floor.name));
                index.push_str(&format!("    rooms: {}\n", floor.rooms.len()));
                index.push_str(&format!("    equipment: {}\n", floor.equipment.len()));
            }

            Ok(index)
        }

        /// Commit changes to Git repository
        fn commit_changes(&self, message: &str, file_paths: &[String]) -> Result<String, GitError> {
            let mut index = self.repo.index()?;
            
            // Add all files to index
            for file_path in file_paths {
                index.add_path(Path::new(file_path))?;
            }
            
            let tree_id = index.write_tree()?;
            let tree = self.repo.find_tree(tree_id)?;

            // Get HEAD commit (if exists) - handle unborn repository
            let parent_commit = match self.repo.head() {
                Ok(head) => {
                    if head.is_branch() {
                        Some(head.peel_to_commit()?)
                    } else {
                        None
                    }
                }
                Err(_) => {
                    // No HEAD exists (unborn repository), this is the first commit
                    None
                }
            };

            // Create signature
            let signature = Signature::now("ArxOS", "arxos@arxos.io")?;

            // Create commit
            let commit_id = self.repo.commit(
                Some("HEAD"),
                &signature,
                &signature,
                message,
                &tree,
                &parent_commit.iter().collect::<Vec<_>>(),
            )?;

            Ok(commit_id.to_string())
        }

        /// Get repository status
        pub fn get_status(&self) -> Result<GitStatus, GitError> {
            match self.repo.head() {
                Ok(head) => {
                    let commit = head.peel_to_commit()?;
                    Ok(GitStatus {
                        current_branch: head.shorthand().unwrap_or("HEAD").to_string(),
                        last_commit: commit.id().to_string(),
                        last_commit_message: commit.message().unwrap_or("").to_string(),
                        last_commit_time: commit.time().seconds(),
                    })
                }
                Err(_) => {
                    // Unborn repository - no commits yet
                    Ok(GitStatus {
                        current_branch: "main".to_string(),
                        last_commit: "".to_string(),
                        last_commit_message: "No commits yet".to_string(),
                        last_commit_time: 0,
                    })
                }
            }
        }

        /// List all commits
        pub fn list_commits(&self, limit: usize) -> Result<Vec<CommitInfo>, GitError> {
            let mut revwalk = self.repo.revwalk()?;
            revwalk.push_head()?;
            
            let mut commits = Vec::new();
            for (i, oid) in revwalk.enumerate() {
                if i >= limit {
                    break;
                }
                
                let oid = oid?;
                let commit = self.repo.find_commit(oid)?;
                
                commits.push(CommitInfo {
                    id: oid.to_string(),
                    message: commit.message().unwrap_or("").to_string(),
                    author: commit.author().name().unwrap_or("").to_string(),
                    time: commit.time().seconds(),
                });
            }
            
            Ok(commits)
        }

        /// Get file history
        pub fn get_file_history(&self, file_path: &str) -> Result<Vec<CommitInfo>, GitError> {
            let mut revwalk = self.repo.revwalk()?;
            revwalk.push_head()?;
            
            let mut commits = Vec::new();
            for oid in revwalk {
                let oid = oid?;
                let commit = self.repo.find_commit(oid)?;
                
                // Check if file was modified in this commit
                if let Ok(tree) = commit.tree() {
                    if tree.get_path(Path::new(file_path)).is_ok() {
                        commits.push(CommitInfo {
                            id: oid.to_string(),
                            message: commit.message().unwrap_or("").to_string(),
                            author: commit.author().name().unwrap_or("").to_string(),
                            time: commit.time().seconds(),
                        });
                    }
                }
            }
            
            Ok(commits)
        }
        
        /// Get diff between commits
        pub fn get_diff(&self, commit_hash: Option<&str>, file_path: Option<&str>) -> Result<DiffResult, GitError> {
            let head_commit = self.repo.head()?.peel_to_commit()?;
            
            let compare_commit = if let Some(hash) = commit_hash {
                // Parse commit hash
                let oid = git2::Oid::from_str(hash)?;
                self.repo.find_commit(oid)?
            } else {
                // Compare with previous commit
                let mut revwalk = self.repo.revwalk()?;
                revwalk.push_head()?;
                revwalk.next().map(|oid| {
                    let oid = oid?;
                    self.repo.find_commit(oid)
                }).transpose()?.unwrap_or(head_commit.clone())
            };
            
            let head_tree = head_commit.tree()?;
            let compare_tree = compare_commit.tree()?;
            
            // Generate diff
            let diff = self.repo.diff_tree_to_tree(
                Some(&compare_tree),
                Some(&head_tree),
                None,
            )?;
            
            let mut diff_result = DiffResult {
                commit_hash: head_commit.id().to_string(),
                compare_hash: compare_commit.id().to_string(),
                files_changed: 0,
                insertions: 0,
                deletions: 0,
                file_diffs: Vec::new(),
            };
            
            // Process diff
            diff.foreach(
                &mut |delta, _| {
                    if let Some(file_path_filter) = file_path {
                        if let Some(path) = delta.new_file().path() {
                            if path.to_string_lossy() != file_path_filter {
                                return true; // Skip this file
                            }
                        } else {
                            return true; // Skip if no path
                        }
                    }
                    
                    diff_result.files_changed += 1;
                    true
                },
                None,
                Some(&mut |_delta, hunk| {
                    diff_result.insertions += hunk.new_lines() as usize;
                    diff_result.deletions += hunk.old_lines() as usize;
                    true
                }),
                Some(&mut |delta, _hunk, line| {
                    let file_path = delta.new_file().path()
                        .map(|p| p.to_string_lossy().to_string())
                        .unwrap_or_else(|| "unknown".to_string());
                    let line_content = String::from_utf8_lossy(line.content()).to_string();
                    
                    diff_result.file_diffs.push(FileDiff {
                        file_path,
                        line_number: line.new_lineno().unwrap_or(0) as usize,
                        line_type: match line.origin() {
                            '+' => DiffLineType::Addition,
                            '-' => DiffLineType::Deletion,
                            ' ' => DiffLineType::Context,
                            _ => DiffLineType::Context,
                        },
                        content: line_content.trim_end().to_string(),
                    });
                    
                    true
                }),
            )?;
            
            Ok(diff_result)
        }
        
        /// Get diff statistics only
        pub fn get_diff_stats(&self, commit_hash: Option<&str>) -> Result<DiffStats, GitError> {
            let diff_result = self.get_diff(commit_hash, None)?;
            
            Ok(DiffStats {
                files_changed: diff_result.files_changed,
                insertions: diff_result.insertions,
                deletions: diff_result.deletions,
            })
        }
    }

    /// Git operation errors
    #[derive(Debug, thiserror::Error)]
    pub enum GitError {
        #[error("Git repository error: {0}")]
        GitError(#[from] git2::Error),
        
        #[error("IO error: {0}")]
        IoError(#[from] std::io::Error),
        
        #[error("Serialization error: {0}")]
        SerializationError(#[from] serde_yaml::Error),
        
        #[error("Generic error: {0}")]
        Generic(#[from] Box<dyn std::error::Error>),
        
        #[error("Repository not found: {path}")]
        RepositoryNotFound { path: String },
        
        #[error("Invalid configuration: {reason}")]
        InvalidConfig { reason: String },
    }
}

#[cfg(not(feature = "git"))]
mod git_impl {
    use serde::{Serialize, Deserialize};
    use crate::yaml::BuildingData;

    /// Stub Git repository manager for when Git is disabled
    pub struct BuildingGitManager {
        // Empty struct when Git is disabled
    }

    /// Git operation results
    #[derive(Debug)]
    pub struct GitOperationResult {
        pub commit_id: String,
        pub files_changed: usize,
        pub message: String,
    }

    /// Git repository configuration
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct GitConfig {
        pub author_name: String,
        pub author_email: String,
        pub branch: String,
        pub remote_url: Option<String>,
    }

    /// Git operation errors
    #[derive(Debug, thiserror::Error)]
    pub enum GitError {
        #[error("Git functionality disabled: {0}")]
        GitDisabled(String),
        
        #[error("IO error: {0}")]
        IoError(#[from] std::io::Error),
        
        #[error("Serialization error: {0}")]
        SerializationError(#[from] serde_yaml::Error),
    }

    impl BuildingGitManager {
        pub fn new(_repo_path: &str, _building_name: &str, _config: GitConfig) -> Result<Self, GitError> {
            Err(GitError::GitDisabled("Git functionality is disabled in this build".to_string()))
        }

        pub fn export_building(
            &mut self,
            _building_data: &BuildingData,
            _commit_message: Option<&str>,
        ) -> Result<GitOperationResult, GitError> {
            Err(GitError::GitDisabled("Git functionality is disabled in this build".to_string()))
        }

        pub fn get_status(&self) -> Result<GitStatus, GitError> {
            Err(GitError::GitDisabled("Git functionality is disabled in this build".to_string()))
        }

        pub fn list_commits(&self, _limit: usize) -> Result<Vec<CommitInfo>, GitError> {
            Err(GitError::GitDisabled("Git functionality is disabled in this build".to_string()))
        }

        pub fn get_file_history(&self, _file_path: &str) -> Result<Vec<CommitInfo>, GitError> {
            Err(GitError::GitDisabled("Git functionality is disabled in this build".to_string()))
        }

        pub fn get_diff(&self, _commit_hash: Option<&str>, _file_path: Option<&str>) -> Result<DiffResult, GitError> {
            Err(GitError::GitDisabled("Git functionality is disabled in this build".to_string()))
        }

        pub fn get_diff_stats(&self, _commit_hash: Option<&str>) -> Result<DiffStats, GitError> {
            Err(GitError::GitDisabled("Git functionality is disabled in this build".to_string()))
        }
    }
}

// Common types that are always available
use serde::{Serialize, Deserialize};

/// Git repository status
#[derive(Debug)]
pub struct GitStatus {
    pub current_branch: String,
    pub last_commit: String,
    pub last_commit_message: String,
    pub last_commit_time: i64,
}

/// Commit information
#[derive(Debug)]
pub struct CommitInfo {
    pub id: String,
    pub message: String,
    pub author: String,
    pub time: i64,
}

/// Diff result between commits
#[derive(Debug)]
pub struct DiffResult {
    pub commit_hash: String,
    pub compare_hash: String,
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
    pub file_diffs: Vec<FileDiff>,
}

/// Individual file diff line
#[derive(Debug)]
pub struct FileDiff {
    pub file_path: String,
    pub line_number: usize,
    pub line_type: DiffLineType,
    pub content: String,
}

/// Type of diff line
#[derive(Debug)]
pub enum DiffLineType {
    Addition,
    Deletion,
    Context,
}

/// Diff statistics
#[derive(Debug)]
pub struct DiffStats {
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
}

/// Git repository configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitConfig {
    pub author_name: String,
    pub author_email: String,
    pub branch: String,
    pub remote_url: Option<String>,
}

/// Git operation results
#[derive(Debug)]
pub struct GitOperationResult {
    pub commit_id: String,
    pub files_changed: usize,
    pub message: String,
}

// Re-export the implementation-specific types
pub use git_impl::{BuildingGitManager, GitError};

/// Git configuration utilities
pub struct GitConfigManager;

impl GitConfigManager {
    /// Create default Git configuration
    pub fn default_config() -> GitConfig {
        GitConfig {
            author_name: "ArxOS".to_string(),
            author_email: "arxos@arxos.io".to_string(),
            branch: "main".to_string(),
            remote_url: None,
        }
    }

    /// Load configuration from file
    pub fn load_config(config_path: &str) -> Result<GitConfig, GitError> {
        let content = std::fs::read_to_string(config_path)?;
        let config: GitConfig = serde_yaml::from_str(&content)?;
        Ok(config)
    }

    /// Save configuration to file
    pub fn save_config(config: &GitConfig, config_path: &str) -> Result<(), GitError> {
        let content = serde_yaml::to_string(config)?;
        std::fs::write(config_path, content)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_git_config() {
        let config = GitConfigManager::default_config();
        assert_eq!(config.author_name, "ArxOS");
        assert_eq!(config.branch, "main");
    }

    #[cfg(feature = "git")]
    #[test]
    fn test_git_manager_creation() {
        let temp_dir = TempDir::new().unwrap();
        let config = GitConfigManager::default_config();
        
        let manager = BuildingGitManager::new(
            temp_dir.path().to_str().unwrap(),
            "Test Building",
            config,
        );
        
        // The manager creation should succeed
        match manager {
            Ok(_) => {
                // Success - this is what we expect
            }
            Err(e) => {
                // If it fails, let's see what the error is
                panic!("Git manager creation failed: {}", e);
            }
        }
    }

    #[cfg(not(feature = "git"))]
    #[test]
    fn test_git_manager_disabled() {
        let temp_dir = TempDir::new().unwrap();
        let config = GitConfigManager::default_config();
        
        let manager = BuildingGitManager::new(
            temp_dir.path().to_str().unwrap(),
            "Test Building",
            config,
        );
        
        // The manager creation should fail when Git is disabled
        assert!(manager.is_err());
        assert!(manager.unwrap_err().to_string().contains("Git functionality is disabled"));
    }
}