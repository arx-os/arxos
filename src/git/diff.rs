//! Diff and history operations for Git repository

use super::GitError;
use git2::Repository;
use std::path::Path;

/// Git repository status
#[derive(Debug)]
pub struct GitStatus {
    pub current_branch: String,
    pub last_commit: String,
    pub last_commit_message: String,
    pub last_commit_time: i64,
    pub is_clean: bool,
    pub modified_files: Vec<String>,
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
#[derive(Debug, Clone)]
pub struct DiffResult {
    pub commit_hash: String,
    pub compare_hash: String,
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
    pub file_diffs: Vec<FileDiff>,
}

/// Individual file diff line
#[derive(Debug, Clone)]
pub struct FileDiff {
    pub file_path: String,
    pub line_number: usize,
    pub line_type: DiffLineType,
    pub content: String,
}

/// Type of diff line
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiffLineType {
    Addition,
    Deletion,
    Context,
}

/// Diff statistics
#[derive(Debug, Clone)]
pub struct DiffStats {
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
}

/// Get repository status
pub fn get_status(repo: &Repository, default_branch: &str) -> Result<GitStatus, GitError> {
    // Get working directory status
    let mut modified_files = Vec::new();
    let statuses = repo.statuses(None).map_err(|e| GitError::GitError(e.message().to_string()))?;
    
    for entry in statuses.iter() {
        let status = entry.status();
        if status.is_wt_new() || status.is_wt_modified() || status.is_index_new() || status.is_index_modified() {
            if let Some(path) = entry.path() {
                modified_files.push(path.to_string());
            }
        }
    }
    
    let is_clean = modified_files.is_empty();

    match repo.head() {
        Ok(head) => {
            let commit = head
                .peel_to_commit()
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            Ok(GitStatus {
                current_branch: head.shorthand().unwrap_or("HEAD").to_string(),
                last_commit: commit.id().to_string(),
                last_commit_message: commit.message().unwrap_or("").to_string(),
                last_commit_time: commit.time().seconds(),
                is_clean,
                modified_files,
            })
        }
        Err(_) => {
            // Unborn repository - no commits yet
            Ok(GitStatus {
                current_branch: default_branch.to_string(),
                last_commit: "".to_string(),
                last_commit_message: "No commits yet".to_string(),
                last_commit_time: 0,
                is_clean,
                modified_files,
            })
        }
    }
}

/// List commits in the repository
pub fn list_commits(repo: &Repository, limit: usize) -> Result<Vec<CommitInfo>, GitError> {
    let mut revwalk = repo
        .revwalk()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    revwalk
        .push_head()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    let mut commits = Vec::new();
    for (i, oid) in revwalk.enumerate() {
        if i >= limit {
            break;
        }

        let oid = oid.map_err(|e| GitError::GitError(e.message().to_string()))?;
        let commit = repo
            .find_commit(oid)
            .map_err(|e| GitError::GitError(e.message().to_string()))?;

        commits.push(CommitInfo {
            id: oid.to_string(),
            message: commit.message().unwrap_or("").to_string(),
            author: commit.author().name().unwrap_or("").to_string(),
            time: commit.time().seconds(),
        });
    }

    Ok(commits)
}

/// Get commit history for a specific file
pub fn get_file_history(repo: &Repository, file_path: &str) -> Result<Vec<CommitInfo>, GitError> {
    let mut revwalk = repo
        .revwalk()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    revwalk
        .push_head()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    let mut commits = Vec::new();
    for oid in revwalk {
        let oid = oid.map_err(|e| GitError::GitError(e.message().to_string()))?;
        let commit = repo
            .find_commit(oid)
            .map_err(|e| GitError::GitError(e.message().to_string()))?;

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
pub fn get_diff(
    repo: &Repository,
    commit_hash: Option<&str>,
    file_path: Option<&str>,
) -> Result<DiffResult, GitError> {
    // Get HEAD commit
    let head_ref = repo.head().map_err(|e| GitError::OperationFailed {
        operation: "get HEAD reference".to_string(),
        reason: format!("No HEAD reference found: {}", e),
    })?;

    let head_commit = head_ref
        .peel_to_commit()
        .map_err(|e| GitError::OperationFailed {
            operation: "peel HEAD to commit".to_string(),
            reason: format!("Cannot resolve HEAD to commit: {}", e),
        })?;

    let compare_commit = if let Some(hash) = commit_hash {
        let oid = git2::Oid::from_str(hash).map_err(|e| GitError::OperationFailed {
            operation: "parse commit hash".to_string(),
            reason: format!("Invalid commit hash '{}': {}", hash, e),
        })?;

        repo.find_commit(oid)
            .map_err(|e| GitError::GitError(e.message().to_string()))?
    } else {
        // Compare with previous commit
        let mut revwalk = repo.revwalk().map_err(|e| GitError::OperationFailed {
            operation: "create revwalk".to_string(),
            reason: format!("Cannot create revwalk: {}", e),
        })?;

        revwalk.push_head().map_err(|e| GitError::OperationFailed {
            operation: "push HEAD to revwalk".to_string(),
            reason: format!("Cannot push HEAD: {}", e),
        })?;

        // Get the second commit (previous to HEAD)
        let mut commits = revwalk.take(2);
        match commits.next() {
            Some(Ok(_)) => match commits.next() {
                Some(Ok(oid)) => repo
                    .find_commit(oid)
                    .map_err(|e| GitError::GitError(e.message().to_string()))?,
                Some(Err(e)) => {
                    return Err(GitError::OperationFailed {
                        operation: "get previous commit".to_string(),
                        reason: format!("Error walking commits: {}", e),
                    });
                }
                None => head_commit.clone(),
            },
            Some(Err(e)) => {
                return Err(GitError::OperationFailed {
                    operation: "walk commits".to_string(),
                    reason: format!("Error walking commits: {}", e),
                });
            }
            None => head_commit.clone(),
        }
    };

    let head_tree = head_commit
        .tree()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;
    let compare_tree = compare_commit
        .tree()
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    // Generate diff
    let diff = repo
        .diff_tree_to_tree(Some(&compare_tree), Some(&head_tree), None)
        .map_err(|e| GitError::GitError(e.message().to_string()))?;

    let mut diff_result = DiffResult {
        commit_hash: head_commit.id().to_string(),
        compare_hash: compare_commit.id().to_string(),
        files_changed: 0,
        insertions: 0,
        deletions: 0,
        file_diffs: Vec::new(),
    };

    // Track file paths and collect diff data
    let mut file_paths = std::collections::HashSet::new();
    let mut line_data = Vec::new();
    let file_path_filter = file_path.map(|s| s.to_string());

    // Process diff using foreach with proper callbacks (4 arguments: file, binary, hunk, line)
    diff.foreach(
        &mut |delta, _similarity| {
            // File callback - called once per file
            if let Some(ref filter) = file_path_filter {
                if let Some(path) = delta.new_file().path() {
                    let path_str = path.to_string_lossy();
                    if path_str != filter.as_str() {
                        return true; // Skip this file
                    }
                    file_paths.insert(path_str.to_string());
                } else {
                    return true; // Skip if no path
                }
            } else if let Some(path) = delta.new_file().path() {
                file_paths.insert(path.to_string_lossy().to_string());
            }
            true
        },
        None, // Binary callback - not needed
        None, // Hunk callback - not needed, we process lines directly
        Some(&mut |delta, _hunk, line| {
            // Line callback - called for each line
            let delta_path = delta
                .new_file()
                .path()
                .map(|p| p.to_string_lossy().to_string());

            // Check if this file should be included
            if let Some(ref filter) = file_path_filter {
                if let Some(ref path) = delta_path {
                    if path != filter {
                        return true; // Skip if filtered
                    }
                } else {
                    return true; // Skip if no path
                }
            }

            let line_type = match line.origin() {
                '+' => DiffLineType::Addition,
                '-' => DiffLineType::Deletion,
                _ => DiffLineType::Context,
            };

            // Extract line data immediately (can't store references)
            if let Some(path) = delta_path {
                let line_number = line.new_lineno().unwrap_or(0) as usize;
                let content = String::from_utf8_lossy(line.content())
                    .trim_end()
                    .to_string();
                line_data.push((path, line_type, line_number, content));
            }

            true
        }),
    )
    .map_err(|e| GitError::GitError(e.to_string()))?;

    // Process collected data
    diff_result.files_changed = file_paths.len();
    for (path, line_type, line_number, content) in line_data {
        if line_type == DiffLineType::Addition {
            diff_result.insertions += 1;
        } else if line_type == DiffLineType::Deletion {
            diff_result.deletions += 1;
        }

        diff_result.file_diffs.push(FileDiff {
            file_path: path,
            line_number,
            line_type,
            content,
        });
    }

    Ok(diff_result)
}

/// Get diff statistics between commits
pub fn get_diff_stats(repo: &Repository, commit_hash: Option<&str>) -> Result<DiffStats, GitError> {
    let diff_result = get_diff(repo, commit_hash, None)?;

    Ok(DiffStats {
        files_changed: diff_result.files_changed,
        insertions: diff_result.insertions,
        deletions: diff_result.deletions,
    })
}
