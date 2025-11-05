//! Git operations for ArxOS
//!
//! This module provides Git repository management for building data version control.
//! The primary interface is `BuildingGitManager`, which provides comprehensive Git operations
//! including commits, diffs, history, and branch management.

pub mod manager;
pub use manager::*;
pub use manager::CommitMetadata;

/// Legacy Git client wrapper (deprecated)
///
/// **Note:** This type is deprecated. Use `BuildingGitManager` instead, which provides
/// comprehensive Git operations with proper error handling, path safety, and user attribution.
///
/// # Deprecation
///
/// `GitClient` is maintained for backward compatibility but is not recommended for new code.
/// It has limitations:
/// - Basic functionality only
/// - Less comprehensive error handling
/// - No path safety validation
/// - No user attribution support
///
/// # Migration
///
/// Instead of:
/// ```rust
/// let client = GitClient::new("path/to/repo")?;
/// client.write_file("file.txt", "content")?;
/// client.commit("message")?;
/// ```
///
/// Use:
/// ```rust
/// let config = GitConfigManager::load_from_arx_config_or_env();
/// let mut manager = BuildingGitManager::new("path/to/repo", "building", config)?;
/// // ... use manager methods ...
/// ```
#[deprecated(note = "Use BuildingGitManager instead. This type will be removed in a future version.")]
#[allow(dead_code)]
pub(crate) struct GitClient {
    repository: git2::Repository,
}

#[allow(deprecated, dead_code)]
impl GitClient {
    /// Create a new Git client for an existing repository
    ///
    /// # Arguments
    ///
    /// * `repo_path` - Path to the Git repository
    ///
    /// # Returns
    ///
    /// Returns a `GitClient` instance or an error if the repository cannot be opened.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - The repository path doesn't exist
    /// - The path is not a valid Git repository
    /// - The repository cannot be opened
    #[deprecated(note = "Use BuildingGitManager::new() instead")]
    pub fn new(repo_path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let repository = git2::Repository::open(repo_path)?;
        Ok(Self { repository })
    }
    
    /// Write a file to the repository working directory
    ///
    /// # Arguments
    ///
    /// * `path` - Relative path to the file (from repository root)
    /// * `content` - File content to write
    ///
    /// # Returns
    ///
    /// Returns `Ok(())` on success, or an error if the file cannot be written.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - The repository is a bare repository (no working directory)
    /// - The file path is invalid
    /// - The file cannot be written
    #[deprecated(note = "Use BuildingGitManager::export_building() or BuildingGitManager::stage_file() instead")]
    pub fn write_file(&self, path: &str, content: &str) -> Result<(), Box<dyn std::error::Error>> {
        // Fix: Use workdir() instead of path() to write to working directory, not .git/
        let workdir = self.repository.workdir()
            .ok_or_else(|| "Repository is bare (no working directory)".to_string())?;
        let file_path = workdir.join(path);
        
        // Create parent directories if needed
        if let Some(parent) = file_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        
        std::fs::write(&file_path, content)?;
        Ok(())
    }
    
    /// Commit all changes in the repository
    ///
    /// # Arguments
    ///
    /// * `message` - Commit message
    ///
    /// # Returns
    ///
    /// Returns `Ok(())` on success, or an error if the commit fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - Git operations fail
    /// - The repository is in an invalid state
    #[deprecated(note = "Use BuildingGitManager::commit_staged() or BuildingGitManager::commit_staged_with_user() instead")]
    pub fn commit(&self, message: &str) -> Result<(), Box<dyn std::error::Error>> {
        let mut index = self.repository.index()?;
        index.add_all(["*"], git2::IndexAddOption::DEFAULT, None)?;
        index.write()?;
        
        let tree_id = index.write_tree()?;
        let tree = self.repository.find_tree(tree_id)?;
        
        // Use default Git config for consistency
        use crate::git::GitConfigManager;
        let config = GitConfigManager::default_config();
        let signature = git2::Signature::now(&config.author_name, &config.author_email)?;
        
        // Handle initial commit (no HEAD) or detached HEAD gracefully
        let parents: Vec<git2::Commit> = match self.repository.head() {
            Ok(head) => {
                if let Some(target) = head.target() {
                    match self.repository.find_commit(target) {
                        Ok(parent) => vec![parent],
                        Err(_) => vec![], // Invalid commit reference, treat as initial commit
                    }
                } else {
                    vec![] // No target, treat as initial commit
                }
            }
            Err(_) => vec![], // No HEAD, initial commit
        };
        
        let parent_refs: Vec<&git2::Commit> = parents.iter().collect();
        
        self.repository.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &parent_refs,
        )?;
        
        Ok(())
    }
}
