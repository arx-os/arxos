use std::env;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};

/// Detect the repository root for the agent to operate against.
///
/// Order of precedence:
/// 1. `ARXOS_REPO_ROOT` environment variable (can point anywhere inside a repository)
/// 2. Current working directory or its parents (via `git2::Repository::discover`)
pub fn detect_repo_root() -> Result<PathBuf> {
    if let Ok(explicit) = env::var("ARXOS_REPO_ROOT") {
        let candidate = PathBuf::from(explicit);
        return resolve_repo_root(&candidate).with_context(|| {
            format!(
                "Failed to resolve ARXOS_REPO_ROOT at {}",
                candidate.display()
            )
        });
    }

    let current_dir = env::current_dir().context("Failed to read current working directory")?;
    resolve_repo_root(&current_dir).with_context(|| {
        format!(
            "Failed to discover Git repository from {}",
            current_dir.display()
        )
    })
}

fn resolve_repo_root(path: &Path) -> Result<PathBuf> {
    let repository = git2::Repository::discover(path)
        .with_context(|| format!("{} is not inside a Git repository", path.display()))?;

    let workdir = repository
        .workdir()
        .context("Repository does not have a working directory")?
        .to_path_buf();

    Ok(workdir)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn detects_repo_root_from_env() {
        let tmp = TempDir::new().unwrap();
        git2::Repository::init(tmp.path()).unwrap();
        std::env::set_var("ARXOS_REPO_ROOT", tmp.path());

        let root = detect_repo_root().unwrap();
        assert_eq!(root, tmp.path().canonicalize().unwrap());

        std::env::remove_var("ARXOS_REPO_ROOT");
    }

    #[test]
    fn discovers_repo_from_current_dir() {
        let tmp = TempDir::new().unwrap();
        git2::Repository::init(tmp.path()).unwrap();
        let original = std::env::current_dir().unwrap();
        std::env::set_current_dir(tmp.path()).unwrap();

        let root = detect_repo_root().unwrap();
        assert_eq!(root, tmp.path().canonicalize().unwrap());

        std::env::set_current_dir(original).unwrap();
    }
}
