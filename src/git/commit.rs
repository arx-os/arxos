//! Commit operations for Git repository

use super::{CommitMetadata, GitConfig, GitError};
use git2::{Repository, Signature};
use std::path::Path;

/// Commit changes to Git repository with metadata
pub fn commit_changes_with_metadata(
    repo: &Repository,
    config: &GitConfig,
    metadata: &CommitMetadata,
    file_paths: &[String],
) -> Result<String, GitError> {
    let mut index = repo
        .index()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    // Add all files to index
    for file_path in file_paths {
        index
            .add_path(Path::new(file_path))
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
    }

    let tree_id = index
        .write_tree()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    let tree = repo
        .find_tree(tree_id)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    // Get HEAD commit (if exists)
    let parent_commit = match repo.head() {
        Ok(head) => {
            if head.is_branch() {
                Some(
                    head.peel_to_commit()
                        .map_err(|e| GitError::GitError(e.message().to_string()))?,
                )
            } else {
                None
            }
        }
        Err(_) => {
            // No HEAD exists (unborn repository)
            None
        }
    };

    // Create signature using configured Git author
    let signature = Signature::now(&config.author_name, &config.author_email)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    // Build enhanced commit message with Git trailers
    let enhanced_message = build_commit_message(metadata);

    // Create commit
    let commit_id = repo
        .commit(
            Some("HEAD"),
            &signature,
            &signature,
            &enhanced_message,
            &tree,
            &parent_commit.iter().collect::<Vec<_>>(),
        )
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    Ok(commit_id.to_string())
}

/// Commit staged changes
pub fn commit_staged(
    repo: &mut Repository,
    config: &GitConfig,
    message: &str,
) -> Result<String, GitError> {
    let metadata = CommitMetadata {
        message: message.to_string(),
        user_id: None,
        device_id: None,
        ar_scan_id: None,
        signature: None,
    };
    commit_staged_with_user(repo, config, &metadata)
}

/// Commit staged changes with user attribution
pub fn commit_staged_with_user(
    repo: &mut Repository,
    config: &GitConfig,
    metadata: &CommitMetadata,
) -> Result<String, GitError> {
    let mut index = repo
        .index()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    let tree_id = index
        .write_tree()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    let tree = repo
        .find_tree(tree_id)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    // Get parent commit (if exists)
    let parent_commit = match repo.head() {
        Ok(head) => {
            if head.is_branch() {
                Some(
                    head.peel_to_commit()
                        .map_err(|e| GitError::GitError(e.message().to_string()))?,
                )
            } else {
                None
            }
        }
        Err(_) => None,
    };

    // Create signature using configured Git author
    let signature = Signature::now(&config.author_name, &config.author_email)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    // Build enhanced commit message with Git trailers
    let enhanced_message = build_commit_message(metadata);

    // Create commit
    let commit_id = repo
        .commit(
            Some("HEAD"),
            &signature,
            &signature,
            &enhanced_message,
            &tree,
            &parent_commit.iter().collect::<Vec<_>>(),
        )
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    Ok(commit_id.to_string())
}

/// Build commit message with Git trailers (standard Git practice)
pub fn build_commit_message(metadata: &CommitMetadata) -> String {
    let mut message = metadata.message.clone();

    // Add Git trailers (standard practice like Signed-off-by:)
    if let Some(ref user_id) = metadata.user_id {
        message.push_str(&format!("\n\nArxOS-User-ID: {}", user_id));
    }

    if let Some(ref device_id) = metadata.device_id {
        message.push_str(&format!("\nArxOS-Device-ID: {}", device_id));
    }

    if let Some(ref ar_scan_id) = metadata.ar_scan_id {
        message.push_str(&format!("\nArxOS-Scan-ID: {}", ar_scan_id));
    }

    message
}
