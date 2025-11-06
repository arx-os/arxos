// Real Git operations for ArxOS
use git2::Repository;
use serde::{Serialize, Deserialize};
use crate::yaml::{BuildingData, BuildingYamlSerializer};
use super::repository::initialize_repository;
use super::export::export_building;
use super::commit::{commit_staged, commit_staged_with_user};
use super::diff::{get_status, get_diff, get_diff_stats, get_file_history, list_commits};
use super::staging::{stage_file, stage_all, unstage_file, unstage_all};

/// Git repository manager for building data version control
///
/// Manages all Git operations for building data, including commits, diffs, history,
/// and branch management. Follows Git-native philosophy for data persistence.
pub struct BuildingGitManager {
    repo: Repository,
    serializer: BuildingYamlSerializer,
    git_config: GitConfig,
}

/// Git operation results
#[derive(Debug, Clone)]
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

/// Enhanced commit metadata with user attribution
#[derive(Debug, Clone)]
pub struct CommitMetadata {
    /// Commit message
    pub message: String,
    /// User ID from registry (UUID format: "usr_...")
    pub user_id: Option<String>,
    /// Device ID from mobile device (Phase 3)
    pub device_id: Option<String>,
    /// AR scan ID if from AR scan
    pub ar_scan_id: Option<String>,
    /// GPG signature (Phase 3)
    pub signature: Option<String>,
}

impl BuildingGitManager {
    /// Initialize or open a Git repository for building data
    pub fn new(repo_path: &str, _building_name: &str, config: GitConfig) -> Result<Self, GitError> {
        let (repo, serializer) = initialize_repository(repo_path, config.clone())?;

        Ok(Self {
            repo,
            serializer,
            git_config: config,
        })
    }

    /// Export building data to Git repository
    pub fn export_building(
        &mut self,
        building_data: &BuildingData,
        commit_message: Option<&str>,
    ) -> Result<GitOperationResult, GitError> {
        // For backward compatibility, create simple metadata
        let msg = commit_message.unwrap_or("Update building data");
        let metadata = CommitMetadata {
            message: msg.to_string(),
            user_id: None,
            device_id: None,
            ar_scan_id: None,
            signature: None,
        };
        self.export_building_with_metadata(building_data, &metadata)
    }

    /// Export building data with user attribution metadata
    pub fn export_building_with_metadata(
        &mut self,
        building_data: &BuildingData,
        metadata: &CommitMetadata,
    ) -> Result<GitOperationResult, GitError> {
        // Record to error analytics if failed
        let result = export_building(
            &mut self.repo,
            &self.serializer,
            building_data,
            &self.git_config,
            metadata,
        );
        
        if let Err(ref err) = result {
            use crate::error::analytics::ErrorAnalyticsManager;
            let git_err = err.clone();
            let arx_err: crate::error::ArxError = git_err.into();
            ErrorAnalyticsManager::record_global_error(&arx_err, Some("export_building_with_metadata".to_string()));
        }
        
        result
    }

    /// Get repository status
    pub fn get_status(&self) -> Result<super::GitStatus, GitError> {
        get_status(&self.repo, &self.git_config.branch)
    }

    /// List commits in the repository
    pub fn list_commits(&self, limit: usize) -> Result<Vec<super::CommitInfo>, GitError> {
        list_commits(&self.repo, limit)
    }

    /// Get commit history for a specific file
    pub fn get_file_history(&self, file_path: &str) -> Result<Vec<super::CommitInfo>, GitError> {
        get_file_history(&self.repo, file_path)
    }
    
    /// Get diff between commits
    pub fn get_diff(&self, commit_hash: Option<&str>, file_path: Option<&str>) -> Result<super::DiffResult, GitError> {
        get_diff(&self.repo, commit_hash, file_path)
    }

    /// Get diff statistics between commits
    pub fn get_diff_stats(&self, commit_hash: Option<&str>) -> Result<super::DiffStats, GitError> {
        get_diff_stats(&self.repo, commit_hash)
    }

    /// Stage a single file for commit
    pub fn stage_file(&mut self, file_path: &str) -> Result<(), GitError> {
        stage_file(&mut self.repo, file_path)
    }

    /// Stage all modified files
    pub fn stage_all(&mut self) -> Result<usize, GitError> {
        stage_all(&mut self.repo)
    }

    /// Unstage a single file
    pub fn unstage_file(&mut self, file_path: &str) -> Result<(), GitError> {
        unstage_file(&mut self.repo, file_path)
    }

    /// Unstage all files
    pub fn unstage_all(&mut self) -> Result<usize, GitError> {
        unstage_all(&mut self.repo)
    }

    /// Commit staged changes
    pub fn commit_staged(&mut self, message: &str) -> Result<String, GitError> {
        let result = commit_staged(&mut self.repo, &self.git_config, message);
        
        // Record to error analytics if failed
        if let Err(ref err) = result {
            use crate::error::analytics::ErrorAnalyticsManager;
            let git_err = err.clone();
            let arx_err: crate::error::ArxError = git_err.into();
            ErrorAnalyticsManager::record_global_error(&arx_err, Some("commit_staged".to_string()));
        }
        
        result
    }

    /// Commit staged changes with user attribution
    pub fn commit_staged_with_user(&mut self, metadata: &CommitMetadata) -> Result<String, GitError> {
        commit_staged_with_user(&mut self.repo, &self.git_config, metadata)
    }
}

/// Git operation errors
///
/// Note: `git2::Error` doesn't implement `Clone`, so we store error messages as `String`
/// to allow cloning for error analytics integration.
#[derive(Debug, Clone, thiserror::Error)]
pub enum GitError {
    #[error("Git repository error: {0}")]
    GitError(String),
    
    #[error("IO error: {0}")]
    IoError(String),
    
    #[error("Serialization error: {0}")]
    SerializationError(String),
    
    #[error("Generic error: {0}")]
    Generic(String),
    
    #[error("Repository not found: {path}")]
    RepositoryNotFound { path: String },
    
    #[error("Invalid configuration: {reason}")]
    InvalidConfig { reason: String },
    
    #[error("Git operation failed: {operation} - {reason}")]
    OperationFailed { operation: String, reason: String },
}

impl From<git2::Error> for GitError {
    fn from(err: git2::Error) -> Self {
        GitError::GitError(err.message().to_string())
    }
}

impl From<std::io::Error> for GitError {
    fn from(err: std::io::Error) -> Self {
        GitError::IoError(err.to_string())
    }
}

impl From<serde_yaml::Error> for GitError {
    fn from(err: serde_yaml::Error) -> Self {
        GitError::SerializationError(err.to_string())
    }
}

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

    /// Load Git configuration from ArxConfig or environment variables
    /// 
    /// Priority order:
    /// 1. Environment variables (GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL)
    /// 2. ArxConfig user settings
    /// 3. Default config
    pub fn load_from_arx_config_or_env() -> GitConfig {
        use std::env;
        
        // Check environment variables first
        let author_name = env::var("GIT_AUTHOR_NAME")
            .or_else(|_| env::var("ARX_USER_NAME"))
            .unwrap_or_else(|_| {
                // Try to load from ArxConfig
                // Use helper function for consistent config access
                crate::config::get_config_or_default().user.name.clone()
            });
        
        let author_email = env::var("GIT_AUTHOR_EMAIL")
            .or_else(|_| env::var("ARX_USER_EMAIL"))
            .unwrap_or_else(|_| {
                // Try to load from ArxConfig
                // Load config with fallback to default
                // Use helper function for consistent config access
                crate::config::get_config_or_default().user.email.clone()
            });
        
        GitConfig {
            author_name,
            author_email,
            branch: "main".to_string(),
            remote_url: env::var("GIT_REMOTE_URL").ok(),
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

    #[test]
    fn test_git_config() {
        let config = GitConfigManager::default_config();
        assert_eq!(config.author_name, "ArxOS");
        assert_eq!(config.branch, "main");
    }

    #[test]
    fn test_git_manager_uses_config_for_commits() {
        let temp_dir = TempDir::new().unwrap();
        let custom_config = GitConfig {
            author_name: "Test User".to_string(),
            author_email: "test@example.com".to_string(),
            branch: "main".to_string(),
            remote_url: None,
        };
        
        let mut manager = BuildingGitManager::new(
            temp_dir.path().to_str().unwrap(),
            "Test Building",
            custom_config.clone(),
        ).unwrap();
        
        // Create a minimal building data for testing
        use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
        use chrono::Utc;
        
        let building_data = BuildingData {
            building: BuildingInfo {
                id: "test-1".to_string(),
                name: "Test Building".to_string(),
                description: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
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
        
        // Export building (this will create a commit)
        let result = manager.export_building(&building_data, Some("Test commit")).unwrap();
        
        // Verify commit was created
        assert!(!result.commit_id.is_empty());
        
        // Get the commit and verify it uses the configured author
        let status = manager.get_status().unwrap();
        assert_eq!(status.last_commit_message, "Test commit");
        
        // Verify commit author matches config
        let commits = manager.list_commits(1).unwrap();
        if let Some(commit) = commits.first() {
            assert_eq!(commit.author, custom_config.author_name);
        }
    }
}
