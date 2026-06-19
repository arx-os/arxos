//! Staging operations for Git repository

use super::GitError;
use git2::{ErrorCode, ObjectType, Repository};
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
    match repo.head() {
        Ok(head) => {
            let head_target = head
                .peel(ObjectType::Commit)
                .map_err(|e| GitError::GitError(e.message().to_string()))?;

            repo.reset_default(Some(&head_target), [file_path])
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            Ok(())
        }
        Err(_) => {
            let mut index = repo
                .index()
                .map_err(|e| GitError::GitError(e.message().to_string()))?;

            if let Err(err) = index.remove_path(Path::new(file_path)) {
                if err.code() != ErrorCode::NotFound {
                    return Err(GitError::GitError(err.message().to_string()));
                }
            }

            index
                .write()
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            Ok(())
        }
    }
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

#[cfg(test)]
mod tests {
    use super::{stage_file, unstage_file};
    use git2::{Repository, Signature, Status};
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn unstage_file_keeps_worktree_changes_but_clears_index_changes() {
        let temp_dir = TempDir::new().expect("create temp dir");
        let repo = Repository::init(temp_dir.path()).expect("init repo");

        let file_path = temp_dir.path().join("test.txt");
        fs::write(&file_path, "v1\n").expect("write initial file");

        let mut repo_for_commit = repo;
        stage_file(&mut repo_for_commit, "test.txt").expect("stage initial file");

        let mut index = repo_for_commit.index().expect("open index");
        let tree_id = index.write_tree().expect("write tree");
        let tree = repo_for_commit.find_tree(tree_id).expect("find tree");
        let signature = Signature::now("Test User", "test@example.com").expect("signature");
        repo_for_commit
            .commit(Some("HEAD"), &signature, &signature, "initial commit", &tree, &[])
            .expect("create initial commit");
        drop(tree);
        drop(index);

        fs::write(&file_path, "v2\n").expect("write modified file");
        stage_file(&mut repo_for_commit, "test.txt").expect("stage modified file");

        let staged_status = repo_for_commit
            .status_file(std::path::Path::new("test.txt"))
            .expect("status staged file");
        assert!(staged_status.contains(Status::INDEX_MODIFIED));

        unstage_file(&mut repo_for_commit, "test.txt").expect("unstage file");

        let unstaged_status = repo_for_commit
            .status_file(std::path::Path::new("test.txt"))
            .expect("status unstaged file");
        assert!(unstaged_status.contains(Status::WT_MODIFIED));
        assert!(!unstaged_status.intersects(
            Status::INDEX_NEW
                | Status::INDEX_MODIFIED
                | Status::INDEX_DELETED
                | Status::INDEX_RENAMED
                | Status::INDEX_TYPECHANGE,
        ));
    }
}
