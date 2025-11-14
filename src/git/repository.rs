//! Repository initialization and lifecycle management

use super::{GitConfig, GitError};
use crate::utils::path_safety::PathSafety;
use crate::yaml::BuildingYamlSerializer;
use git2::Repository;
use std::path::Path;

/// Initialize a Git repository for building data
///
/// Validates the repository path, creates the directory if needed,
/// and opens or initializes the repository.
pub fn initialize_repository(
    repo_path: &str,
    _config: GitConfig,
) -> Result<(Repository, BuildingYamlSerializer), GitError> {
    let repo_path_buf = Path::new(repo_path);

    // Validate repository path format (no traversal, no null bytes)
    PathSafety::validate_path_format(repo_path).map_err(|e| GitError::OperationFailed {
        operation: "validate repository path".to_string(),
        reason: format!("Path validation failed: {}", e),
    })?;

    // Detect path traversal attempts in relative paths
    if !repo_path_buf.is_absolute() {
        PathSafety::detect_path_traversal(repo_path).map_err(|e| {
            GitError::OperationFailed {
                operation: "validate repository path".to_string(),
                reason: format!("Path traversal detected: {}", e),
            }
        })?;
    }

    // Canonicalize the path
    let validated_repo_path = if repo_path_buf.is_absolute() {
        repo_path_buf
            .canonicalize()
            .map_err(|e| GitError::IoError(format!("Cannot canonicalize repository path: {}", e)))?
    } else {
        let current_dir = std::env::current_dir().map_err(GitError::from)?;
        let joined = current_dir.join(repo_path_buf);
        joined
            .canonicalize()
            .map_err(|e| GitError::IoError(format!("Cannot canonicalize repository path: {}", e)))?
    };

    // Ensure the directory exists
    if !validated_repo_path.exists() {
        std::fs::create_dir_all(&validated_repo_path)?;
    }

    let repo = if validated_repo_path.join(".git").exists() {
        Repository::open(&validated_repo_path)
            .map_err(|e| GitError::GitError(e.message().to_string()))?
    } else {
        Repository::init(&validated_repo_path)
            .map_err(|e| GitError::GitError(e.message().to_string()))?
    };

    let serializer = BuildingYamlSerializer::new();

    Ok((repo, serializer))
}
