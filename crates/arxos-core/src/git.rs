//! Git operations for building data version control

use crate::Result;
use std::path::Path;
use std::process::Command;
use tracing::{info, warn, error};

/// Initialize Git repository in the specified directory
pub fn init_repository(repo_path: &Path) -> Result<()> {
    info!("Initializing Git repository at: {}", repo_path.display());
    
    // Check if already a git repository
    if repo_path.join(".git").exists() {
        info!("Git repository already exists at: {}", repo_path.display());
        return Ok(());
    }
    
    // Initialize git repository
    let output = Command::new("git")
        .arg("init")
        .arg("--initial-branch=main")
        .current_dir(repo_path)
        .output()?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        error!("Failed to initialize Git repository: {}", error_msg);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git init failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git init failed: {}", error_msg)));
    }
    
    // Create initial .gitignore
    let gitignore_content = r#"# ArxOS Building Data
*.tmp
*.log
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Build artifacts
target/
*.o
*.so
*.dylib
*.dll

# Test data
test_data/temp/
"#;
    
    std::fs::write(repo_path.join(".gitignore"), gitignore_content)?;
    
    // Initial commit
    add_all_files(repo_path)?;
    commit_changes(repo_path, "Initial commit: ArxOS building data repository")?;
    
    info!("Git repository initialized successfully");
    Ok(())
}

/// Add all files to Git staging area
pub fn add_all_files(repo_path: &Path) -> Result<()> {
    let output = Command::new("git")
        .arg("add")
        .arg(".")
        .current_dir(repo_path)
        .output()?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        error!("Failed to add files to Git: {}", error_msg);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git add failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git add failed: {}", error_msg)));
    }
    
    Ok(())
}

/// Commit changes with a message
pub fn commit_changes(repo_path: &Path, message: &str) -> Result<()> {
    info!("Committing changes: {}", message);
    
    // Check if there are changes to commit
    let status_output = Command::new("git")
        .arg("status")
        .arg("--porcelain")
        .current_dir(repo_path)
        .output()?;
    
    if !status_output.status.success() {
        let error_msg = String::from_utf8_lossy(&status_output.stderr);
        error!("Failed to check Git status: {}", error_msg);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git status failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git status failed: {}", error_msg)));
    }
    
    let status = String::from_utf8_lossy(&status_output.stdout);
    if status.trim().is_empty() {
        info!("No changes to commit");
        return Ok(());
    }
    
    // Add all changes
    add_all_files(repo_path)?;
    
    // Commit changes
    let output = Command::new("git")
        .arg("commit")
        .arg("-m")
        .arg(message)
        .current_dir(repo_path)
        .output()?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        error!("Failed to commit changes: {}", error_msg);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git commit failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git commit failed: {}", error_msg)));
    }
    
    info!("Changes committed successfully");
    Ok(())
}

/// Sync with remote repository
pub fn sync_repository(repo_path: &Path, remote_url: Option<&str>) -> Result<()> {
    info!("Syncing repository at: {}", repo_path.display());
    
    // Check if remote is configured
    let remote_output = Command::new("git")
        .arg("remote")
        .arg("-v")
        .current_dir(repo_path)
        .output()?;
    
    if !remote_output.status.success() {
        let error_msg = String::from_utf8_lossy(&remote_output.stderr);
        error!("Failed to check Git remotes: {}", error_msg);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git remote check failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git remote check failed: {}", error_msg)));
    }
    
    let remotes = String::from_utf8_lossy(&remote_output.stdout);
    
    if remotes.trim().is_empty() {
        if let Some(url) = remote_url {
            // Add remote origin
            let add_remote_output = Command::new("git")
                .arg("remote")
                .arg("add")
                .arg("origin")
                .arg(url)
                .current_dir(repo_path)
                .output()?;
            
            if !add_remote_output.status.success() {
                let error_msg = String::from_utf8_lossy(&add_remote_output.stderr);
                error!("Failed to add remote origin: {}", error_msg);
                #[cfg(feature = "git")]
                return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git remote add failed: {}", error_msg))));
                #[cfg(not(feature = "git"))]
                return Err(crate::ArxError::Git(format!("Git remote add failed: {}", error_msg)));
            }
            
            info!("Added remote origin: {}", url);
        } else {
            warn!("No remote configured and no URL provided");
            return Ok(());
        }
    }
    
    // Fetch latest changes
    let fetch_output = Command::new("git")
        .arg("fetch")
        .arg("origin")
        .current_dir(repo_path)
        .output()?;
    
    if !fetch_output.status.success() {
        let error_msg = String::from_utf8_lossy(&fetch_output.stderr);
        warn!("Failed to fetch from remote: {}", error_msg);
        // Don't fail sync if fetch fails - might be offline
    } else {
        info!("Fetched latest changes from remote");
    }
    
    // Check if we're behind and can fast-forward
    let status_output = Command::new("git")
        .arg("status")
        .arg("-uno")
        .current_dir(repo_path)
        .output()?;
    
    if !status_output.status.success() {
        let error_msg = String::from_utf8_lossy(&status_output.stderr);
        error!("Failed to check Git status: {}", error_msg);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git status failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git status failed: {}", error_msg)));
    }
    
    let status = String::from_utf8_lossy(&status_output.stdout);
    
    if status.contains("Your branch is behind") {
        // Try to pull changes
        let pull_output = Command::new("git")
            .arg("pull")
            .arg("origin")
            .arg("main")
            .current_dir(repo_path)
            .output()?;
        
        if !pull_output.status.success() {
            let error_msg = String::from_utf8_lossy(&pull_output.stderr);
            warn!("Failed to pull changes: {}", error_msg);
            // Don't fail sync if pull fails - might have conflicts
        } else {
            info!("Pulled latest changes from remote");
        }
    }
    
    // Push local changes if any
    let push_output = Command::new("git")
        .arg("push")
        .arg("origin")
        .arg("main")
        .current_dir(repo_path)
        .output()?;
    
    if !push_output.status.success() {
        let error_msg = String::from_utf8_lossy(&push_output.stderr);
        warn!("Failed to push changes: {}", error_msg);
        // Don't fail sync if push fails - might be offline
    } else {
        info!("Pushed local changes to remote");
    }
    
    info!("Repository sync completed");
    Ok(())
}

/// Get Git status information
pub fn get_status(repo_path: &Path) -> Result<GitStatus> {
    // Get current branch
    let branch_output = Command::new("git")
        .arg("branch")
        .arg("--show-current")
        .current_dir(repo_path)
        .output()?;
    
    let branch = if branch_output.status.success() {
        String::from_utf8_lossy(&branch_output.stdout).trim().to_string()
    } else {
        "unknown".to_string()
    };
    
    // Get commit count
    let count_output = Command::new("git")
        .arg("rev-list")
        .arg("--count")
        .arg("HEAD")
        .current_dir(repo_path)
        .output()?;
    
    let commit_count = if count_output.status.success() {
        String::from_utf8_lossy(&count_output.stdout).trim().parse().unwrap_or(0)
    } else {
        0
    };
    
    // Get last commit message
    let last_commit_output = Command::new("git")
        .arg("log")
        .arg("-1")
        .arg("--pretty=format:%s")
        .current_dir(repo_path)
        .output()?;
    
    let last_commit = if last_commit_output.status.success() {
        String::from_utf8_lossy(&last_commit_output.stdout).trim().to_string()
    } else {
        "No commits".to_string()
    };
    
    // Check for uncommitted changes
    let status_output = Command::new("git")
        .arg("status")
        .arg("--porcelain")
        .current_dir(repo_path)
        .output()?;
    
    let has_changes = if status_output.status.success() {
        !String::from_utf8_lossy(&status_output.stdout).trim().is_empty()
    } else {
        false
    };
    
    // Check sync status
    let sync_status = if has_changes {
        "Local changes pending"
    } else {
        "Up to date"
    };
    
    Ok(GitStatus {
        branch,
        commit_count,
        last_commit,
        has_changes,
        sync_status: sync_status.to_string(),
    })
}

/// Get Git diff
pub fn get_diff(repo_path: &Path) -> Result<String> {
    let output = Command::new("git")
        .arg("diff")
        .current_dir(repo_path)
        .output()?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git diff failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git diff failed: {}", error_msg)));
    }
    
    let diff = String::from_utf8_lossy(&output.stdout);
    Ok(diff.to_string())
}

/// Get Git history
pub fn get_history(repo_path: &Path, limit: usize) -> Result<Vec<String>> {
    let output = Command::new("git")
        .arg("log")
        .arg(format!("-{}", limit))
        .arg("--pretty=format:%h - %s (%cr)")
        .current_dir(repo_path)
        .output()?;
    
    if !output.status.success() {
        let error_msg = String::from_utf8_lossy(&output.stderr);
        #[cfg(feature = "git")]
        return Err(crate::ArxError::Git(git2::Error::from_str(&format!("Git log failed: {}", error_msg))));
        #[cfg(not(feature = "git"))]
        return Err(crate::ArxError::Git(format!("Git log failed: {}", error_msg)));
    }
    
    let log = String::from_utf8_lossy(&output.stdout);
    let commits: Vec<String> = log.lines().map(|s| s.to_string()).collect();
    Ok(commits)
}

/// Git status information
#[derive(Debug, Clone)]
pub struct GitStatus {
    pub branch: String,
    pub commit_count: usize,
    pub last_commit: String,
    pub has_changes: bool,
    pub sync_status: String,
}
