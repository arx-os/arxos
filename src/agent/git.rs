use std::path::Path;

use anyhow::{anyhow, Context, Result};
use crate::git::{BuildingGitManager, CommitMetadata, DiffLineType, GitConfigManager};
use git2::{Repository, Status, StatusOptions};
use serde::Serialize;

#[derive(Serialize)]
pub struct GitStatusSummary {
    pub branch: String,
    pub last_commit: String,
    pub last_commit_message: String,
    pub last_commit_time: i64,
    pub staged_changes: usize,
    pub unstaged_changes: usize,
    pub untracked: usize,
    pub diff_summary: GitDiffStatsSummary,
}

#[derive(Serialize)]
pub struct GitDiffStatsSummary {
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
}

#[derive(Serialize)]
pub struct GitDiffPayload {
    pub commit_hash: String,
    pub compare_hash: String,
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
    pub files: Vec<GitFileDiff>,
}

#[derive(Serialize)]
pub struct GitFileDiff {
    pub file_path: String,
    pub line_number: usize,
    pub kind: String,
    pub content: String,
}

#[derive(Serialize)]
pub struct GitCommitResult {
    pub commit_id: String,
    pub staged_files: usize,
}

pub fn status(repo_root: &Path) -> Result<GitStatusSummary> {
    let config = GitConfigManager::load_from_arx_config_or_env();
    let repo_root_str = repo_root
        .to_str()
        .ok_or_else(|| anyhow!("Repository path is not valid UTF-8"))?;

    let manager = BuildingGitManager::new(repo_root_str, "Workspace", config.clone())
        .context("Failed to open Git repository")?;
    let status = manager.get_status().context("Failed to fetch Git status")?;
    let diff_stats = manager
        .get_diff_stats(None)
        .unwrap_or_else(|_| arx::git::DiffStats {
            files_changed: 0,
            insertions: 0,
            deletions: 0,
        });

    let repo = Repository::open(repo_root).context("Failed to open repository for status")?;
    let (staged_changes, unstaged_changes, untracked) = summarize_status_entries(&repo)?;

    Ok(GitStatusSummary {
        branch: status.current_branch,
        last_commit: status.last_commit,
        last_commit_message: status.last_commit_message,
        last_commit_time: status.last_commit_time,
        staged_changes,
        unstaged_changes,
        untracked,
        diff_summary: GitDiffStatsSummary {
            files_changed: diff_stats.files_changed,
            insertions: diff_stats.insertions,
            deletions: diff_stats.deletions,
        },
    })
}

pub fn diff(repo_root: &Path, commit: Option<&str>, file: Option<&str>) -> Result<GitDiffPayload> {
    let config = GitConfigManager::default_config();
    let repo_root_str = repo_root
        .to_str()
        .ok_or_else(|| anyhow!("Repository path is not valid UTF-8"))?;

    let manager = BuildingGitManager::new(repo_root_str, "Workspace", config)
        .context("Failed to open Git repository")?;
    let diff = manager
        .get_diff(commit, file)
        .context("Failed to generate diff")?;

    let files = diff
        .file_diffs
        .into_iter()
        .map(|line| GitFileDiff {
            file_path: line.file_path,
            line_number: line.line_number,
            kind: diff_line_type_to_str(line.line_type).to_string(),
            content: line.content,
        })
        .collect();

    Ok(GitDiffPayload {
        commit_hash: diff.commit_hash,
        compare_hash: diff.compare_hash,
        files_changed: diff.files_changed,
        insertions: diff.insertions,
        deletions: diff.deletions,
        files,
    })
}

pub fn commit(
    repo_root: &Path,
    message: &str,
    stage_all: bool,
    did_key: &str,
) -> Result<GitCommitResult> {
    if message.trim().is_empty() {
        return Err(anyhow!("Commit message cannot be empty"));
    }

    let repo_root_str = repo_root
        .to_str()
        .ok_or_else(|| anyhow!("Repository path is not valid UTF-8"))?;

    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut manager = BuildingGitManager::new(repo_root_str, "Workspace", config)
        .context("Failed to open Git repository")?;

    let staged_files = if stage_all {
        manager.stage_all().context("Failed to stage files")?
    } else {
        0
    };

    let metadata = CommitMetadata {
        message: message.to_string(),
        user_id: Some(did_key.to_string()),
        device_id: None,
        ar_scan_id: None,
        signature: None,
    };

    let commit_id = manager
        .commit_staged_with_user(&metadata)
        .context("Failed to create commit")?;

    Ok(GitCommitResult {
        commit_id,
        staged_files,
    })
}

fn summarize_status_entries(repo: &Repository) -> Result<(usize, usize, usize)> {
    let mut options = StatusOptions::new();
    options
        .include_untracked(true)
        .recurse_untracked_dirs(true)
        .renames_head_to_index(true)
        .renames_index_to_workdir(true)
        .include_unmodified(false);

    let statuses = repo
        .statuses(Some(&mut options))
        .context("Failed to collect status entries")?;

    let mut staged = 0;
    let mut unstaged = 0;
    let mut untracked = 0;

    for entry in statuses.iter() {
        let status = entry.status();

        if status.intersects(Status::INDEX_NEW | Status::INDEX_MODIFIED | Status::INDEX_DELETED) {
            staged += 1;
        }

        if status.intersects(Status::WT_MODIFIED | Status::WT_DELETED | Status::WT_TYPECHANGE) {
            unstaged += 1;
        }

        if status.contains(Status::WT_NEW) {
            untracked += 1;
        }
    }

    Ok((staged, unstaged, untracked))
}

fn diff_line_type_to_str(value: DiffLineType) -> &'static str {
    match value {
        DiffLineType::Addition => "addition",
        DiffLineType::Deletion => "deletion",
        DiffLineType::Context => "context",
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    const DID_KEY: &str = "did:key:ztest";

    struct EnvGuard;

    impl EnvGuard {
        fn new() -> Self {
            std::env::set_var("GIT_AUTHOR_NAME", "Test User");
            std::env::set_var("GIT_AUTHOR_EMAIL", "test@example.com");
            Self
        }
    }

    impl Drop for EnvGuard {
        fn drop(&mut self) {
            let _ = std::env::remove_var("GIT_AUTHOR_NAME");
            let _ = std::env::remove_var("GIT_AUTHOR_EMAIL");
        }
    }

    fn setup_repo() -> (TempDir, std::path::PathBuf, EnvGuard) {
        let guard = EnvGuard::new();
        let tmp = TempDir::new().unwrap();
        git2::Repository::init(tmp.path()).unwrap();
        let root = tmp.path().canonicalize().unwrap();
        (tmp, root, guard)
    }

    #[test]
    fn status_reports_changes() {
        let (_tmp, root, _guard) = setup_repo();
        let file = root.join("README.md");
        fs::write(&file, "hello world").unwrap();

        let result = status(&root).unwrap();
        assert_eq!(result.branch, "main");
        assert!(result.untracked >= 1);
    }

    #[test]
    fn commit_creates_revision() {
        let (_tmp, root, _guard) = setup_repo();
        let file = root.join("data.yaml");
        fs::write(&file, "name: sample").unwrap();

        let commit = commit(&root, "Initial commit", true, DID_KEY).unwrap();
        assert!(!commit.commit_id.is_empty());

        let status = status(&root).unwrap();
        assert_eq!(status.untracked, 0);
    }

    #[test]
    fn diff_returns_file_changes() {
        let (_tmp, root, _guard) = setup_repo();
        let file = root.join("example.txt");
        fs::write(&file, "first").unwrap();
        commit(&root, "Initial", true, DID_KEY).unwrap();

        fs::write(&file, "second").unwrap();
        commit(&root, "Update", true, DID_KEY).unwrap();

        let payload = diff(&root, None, None).unwrap();
        assert!(payload.files_changed >= 1);
    }
}
