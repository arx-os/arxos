//! Git operations for building data version control
//!
//! This module provides comprehensive Git integration for ArxOS building data,
//! including repository management, commit operations, and branch handling.

use crate::Result;
use std::path::Path;
use std::process::Command;
use tracing::{info, warn, error};
use chrono::{DateTime, Utc};

#[cfg(feature = "git")]
use git2::{Repository, Signature, Oid, BranchType};

/// Git repository information
#[derive(Debug, Clone)]
pub struct GitRepository {
    pub path: String,
    pub branch: String,
    pub commit_count: usize,
    pub last_commit: String,
    pub has_changes: bool,
    pub remote_url: Option<String>,
}

/// Git commit information
#[derive(Debug, Clone)]
pub struct GitCommit {
    pub id: String,
    pub message: String,
    pub author: String,
    pub email: String,
    pub timestamp: DateTime<Utc>,
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
}

/// Git status information
#[derive(Debug, Clone)]
pub struct GitStatus {
    pub branch: String,
    pub commit_count: usize,
    pub last_commit: String,
    pub has_changes: bool,
    pub staged_files: Vec<String>,
    pub modified_files: Vec<String>,
    pub untracked_files: Vec<String>,
}

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
    let _sync_status = if has_changes {
        "Local changes pending"
    } else {
        "Up to date"
    };
    
        Ok(GitStatus {
            branch,
            commit_count,
            last_commit,
            has_changes,
            staged_files: vec![],
            modified_files: vec![],
            untracked_files: vec![],
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

/// Create a new commit with building data changes
pub fn create_commit(repo_path: &Path, message: &str, author_name: &str, author_email: &str) -> Result<String> {
    info!("Creating commit: {}", message);
    
    #[cfg(feature = "git")]
    {
        let repo = Repository::open(repo_path)?;
        
        // Add all changes
        let mut index = repo.index()?;
        index.add_all(["*"].iter(), git2::IndexAddOption::DEFAULT, None)?;
        index.write()?;
        
        // Create signature
        let signature = Signature::now(author_name, author_email)?;
        
        // Get tree
        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        
        // Create commit
        let commit_id = repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &[],
        )?;
        
        Ok(commit_id.to_string())
    }
    
    #[cfg(not(feature = "git"))]
    {
        // Fallback to command line git
        let output = Command::new("git")
            .arg("add")
            .arg(".")
            .current_dir(repo_path)
            .output()?;
        
        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            error!("Failed to stage changes: {}", error_msg);
            return Err(crate::ArxError::Git(format!("Git add failed: {}", error_msg)));
        }
        
        let output = Command::new("git")
            .arg("commit")
            .arg("-m")
            .arg(message)
            .arg("--author")
            .arg(format!("{} <{}>", author_name, author_email))
            .current_dir(repo_path)
            .output()?;
        
        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            error!("Failed to create commit: {}", error_msg);
            return Err(crate::ArxError::Git(format!("Git commit failed: {}", error_msg)));
        }
        
        // Get commit hash
        let output = Command::new("git")
            .arg("rev-parse")
            .arg("HEAD")
            .current_dir(repo_path)
            .output()?;
        
        if output.status.success() {
            Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
        } else {
            Ok("commit_created".to_string())
        }
    }
}

/// Get detailed commit information
pub fn get_commit_info(repo_path: &Path, commit_id: &str) -> Result<GitCommit> {
    #[cfg(feature = "git")]
    {
        let repo = Repository::open(repo_path)?;
        let oid = Oid::from_str(commit_id)?;
        let commit = repo.find_commit(oid)?;
        
        let author = commit.author();
        let timestamp = DateTime::from_timestamp(author.when().seconds(), 0)
            .unwrap_or_else(|| Utc::now());
        
        // Get diff stats
        let parent = commit.parent(0).ok();
        let tree = commit.tree()?;
        let parent_tree = parent.map(|p| p.tree()).transpose()?;
        
        let diff = repo.diff_tree_to_tree(
            parent_tree.as_ref(),
            Some(&tree),
            None,
        )?;
        
        let mut files_changed = 0;
        let mut insertions = 0;
        let mut deletions = 0;
        
        diff.foreach(
            &mut |_delta, _| {
                files_changed += 1;
                true
            },
            None,
            Some(&mut |_delta, hunk| {
                insertions += hunk.new_lines() as usize;
                deletions += hunk.old_lines() as usize;
                true
            }),
            None,
        )?;
        
        Ok(GitCommit {
            id: commit_id.to_string(),
            message: commit.message().unwrap_or("").to_string(),
            author: author.name().unwrap_or("").to_string(),
            email: author.email().unwrap_or("").to_string(),
            timestamp,
            files_changed,
            insertions,
            deletions,
        })
    }
    
    #[cfg(not(feature = "git"))]
    {
        // Fallback implementation
        Ok(GitCommit {
            id: commit_id.to_string(),
            message: "Commit message".to_string(),
            author: "Author".to_string(),
            email: "author@example.com".to_string(),
            timestamp: Utc::now(),
            files_changed: 0,
            insertions: 0,
            deletions: 0,
        })
    }
}

/// Create a new branch
pub fn create_branch(repo_path: &Path, branch_name: &str) -> Result<()> {
    info!("Creating branch: {}", branch_name);
    
    #[cfg(feature = "git")]
    {
        let repo = Repository::open(repo_path)?;
        let head = repo.head()?;
        let commit = head.peel_to_commit()?;
        
        repo.branch(branch_name, &commit, false)?;
        Ok(())
    }
    
    #[cfg(not(feature = "git"))]
    {
        let output = Command::new("git")
            .arg("checkout")
            .arg("-b")
            .arg(branch_name)
            .current_dir(repo_path)
            .output()?;
        
        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            error!("Failed to create branch: {}", error_msg);
            return Err(crate::ArxError::Git(format!("Git branch creation failed: {}", error_msg)));
        }
        
        Ok(())
    }
}

/// Switch to a branch
pub fn switch_branch(repo_path: &Path, branch_name: &str) -> Result<()> {
    info!("Switching to branch: {}", branch_name);
    
    #[cfg(feature = "git")]
    {
        let repo = Repository::open(repo_path)?;
        let reference = repo.find_reference(&format!("refs/heads/{}", branch_name))?;
        repo.set_head(reference.name().unwrap())?;
        repo.checkout_head(Some(git2::build::CheckoutBuilder::default().force()))?;
        Ok(())
    }
    
    #[cfg(not(feature = "git"))]
    {
        let output = Command::new("git")
            .arg("checkout")
            .arg(branch_name)
            .current_dir(repo_path)
            .output()?;
        
        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            error!("Failed to switch branch: {}", error_msg);
            return Err(crate::ArxError::Git(format!("Git checkout failed: {}", error_msg)));
        }
        
        Ok(())
    }
}

/// Get list of branches
pub fn list_branches(repo_path: &Path) -> Result<Vec<String>> {
    #[cfg(feature = "git")]
    {
        let repo = Repository::open(repo_path)?;
        let branches = repo.branches(Some(BranchType::Local))?;
        
        let mut branch_names = Vec::new();
        for branch in branches {
            let (branch, _) = branch?;
            if let Some(name) = branch.name()? {
                branch_names.push(name.to_string());
            }
        }
        
        Ok(branch_names)
    }
    
    #[cfg(not(feature = "git"))]
    {
        let output = Command::new("git")
            .arg("branch")
            .arg("--format=%(refname:short)")
            .current_dir(repo_path)
            .output()?;
        
        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            error!("Failed to list branches: {}", error_msg);
            return Err(crate::ArxError::Git(format!("Git branch listing failed: {}", error_msg)));
        }
        
        let branches: Vec<String> = String::from_utf8_lossy(&output.stdout)
            .lines()
            .map(|line| line.trim().to_string())
            .filter(|line| !line.is_empty())
            .collect();
        
        Ok(branches)
    }
}

/// Push changes to remote repository
pub fn push_to_remote(repo_path: &Path, remote_name: &str, branch_name: &str) -> Result<()> {
    info!("Pushing to remote: {}/{}", remote_name, branch_name);
    
    #[cfg(feature = "git")]
    {
        let repo = Repository::open(repo_path)?;
        let mut remote = repo.find_remote(remote_name)?;
        
        let refspec = format!("refs/heads/{}:refs/heads/{}", branch_name, branch_name);
        remote.push(&[&refspec], None)?;
        
        Ok(())
    }
    
    #[cfg(not(feature = "git"))]
    {
        let output = Command::new("git")
            .arg("push")
            .arg(remote_name)
            .arg(branch_name)
            .current_dir(repo_path)
            .output()?;
        
        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            error!("Failed to push to remote: {}", error_msg);
            return Err(crate::ArxError::Git(format!("Git push failed: {}", error_msg)));
        }
        
        Ok(())
    }
}

/// Pull changes from remote repository
pub fn pull_from_remote(repo_path: &Path, remote_name: &str, branch_name: &str) -> Result<()> {
    info!("Pulling from remote: {}/{}", remote_name, branch_name);
    
    #[cfg(feature = "git")]
    {
        let repo = Repository::open(repo_path)?;
        let mut remote = repo.find_remote(remote_name)?;
        
        remote.fetch(&[branch_name], None, None)?;
        
        let reference = repo.find_reference(&format!("refs/remotes/{}/{}", remote_name, branch_name))?;
        let commit = reference.peel_to_commit()?;
        
        repo.branch(branch_name, &commit, false)?;
        
        let reference = repo.find_reference(&format!("refs/heads/{}", branch_name))?;
        repo.set_head(reference.name().unwrap())?;
        repo.checkout_head(Some(git2::build::CheckoutBuilder::default().force()))?;
        
        Ok(())
    }
    
    #[cfg(not(feature = "git"))]
    {
        let output = Command::new("git")
            .arg("pull")
            .arg(remote_name)
            .arg(branch_name)
            .current_dir(repo_path)
            .output()?;
        
        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            error!("Failed to pull from remote: {}", error_msg);
            return Err(crate::ArxError::Git(format!("Git pull failed: {}", error_msg)));
        }
        
        Ok(())
    }
}
