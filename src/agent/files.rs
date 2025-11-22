use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use crate::utils::path_safety::PathSafety;
use serde::Serialize;

#[derive(Serialize)]
pub struct FileContent {
    pub path: String,
    pub content: String,
}

pub fn read_file(repo_root: &Path, relative_path: &str) -> Result<FileContent> {
    if relative_path.trim().is_empty() {
        anyhow::bail!("File path cannot be empty");
    }

    // Normalize the requested path
    let sanitized = PathBuf::from(relative_path);
    let content = PathSafety::read_file_safely(&sanitized, repo_root)
        .map_err(|e| anyhow::anyhow!("Failed to read file {}: {}", sanitized.display(), e))?;

    Ok(FileContent {
        path: sanitized.to_string_lossy().to_string(),
        content,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn reads_file_within_repo() {
        let tmp = TempDir::new().unwrap();
        git2::Repository::init(tmp.path()).unwrap();

        let file_path = tmp.path().join("nested").join("file.txt");
        std::fs::create_dir_all(file_path.parent().unwrap()).unwrap();
        std::fs::write(&file_path, "hello").unwrap();

        let content = read_file(tmp.path(), "nested/file.txt").unwrap();
        assert_eq!(content.content, "hello");
    }

    #[test]
    fn rejects_traversal() {
        let tmp = TempDir::new().unwrap();
        git2::Repository::init(tmp.path()).unwrap();

        let result = read_file(tmp.path(), "../outside.txt");
        assert!(result.is_err());
    }
}
