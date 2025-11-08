//! Staging operations for Git repository

use super::GitError;
use git2::Repository;
use std::path::Path;

/// Stage a single file for commit
pub fn stage_file(repo: &mut Repository, file_path: &str) -> Result<(), GitError> {
    let mut index = repo
        .index()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    index
        .add_path(Path::new(file_path))
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    index
        .write()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    Ok(())
}

/// Stage all modified files
pub fn stage_all(repo: &mut Repository) -> Result<usize, GitError> {
    let mut index = repo
        .index()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    index
        .add_all(["*"], git2::IndexAddOption::DEFAULT, None)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    let count = index.len();
    index
        .write()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    Ok(count)
}

/// Unstage a single file
pub fn unstage_file(repo: &mut Repository, file_path: &str) -> Result<(), GitError> {
    let mut index = repo
        .index()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    index
        .remove_path(Path::new(file_path))
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    index
        .write()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    Ok(())
}

/// Unstage all files
pub fn unstage_all(repo: &mut Repository) -> Result<usize, GitError> {
    let mut index = repo.index()?;
    // Reset the index to HEAD
    let tree_id = match repo.head() {
        Ok(head) => {
            let commit = head
                .peel_to_commit()
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            commit.tree_id()
        }
        Err(_) => {
            // No HEAD, clear the index
            let count = index.len();
            index
                .clear()
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            index
                .write()
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            return Ok(count);
        }
    };

    let tree = repo
        .find_tree(tree_id)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    index
        .read_tree(&tree)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    let count = index.len();
    index
        .write()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    Ok(count)
}
