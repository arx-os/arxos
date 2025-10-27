// Git operations command handlers
// Handles status, diff, and history commands

use crate::git::manager::{BuildingGitManager, GitConfigManager, GitStatus, CommitInfo, DiffStats, DiffResult, DiffLineType};
use crate::utils::loading;

/// Find Git repository in current directory or parent directories
fn find_git_repository() -> Result<Option<String>, Box<dyn std::error::Error>> {
    let mut current_path = std::env::current_dir()?;
    
    loop {
        let git_path = current_path.join(".git");
        if git_path.exists() {
            return Ok(Some(current_path.to_string_lossy().to_string()));
        }
        
        if !current_path.pop() {
            break;
        }
    }
    
    Ok(None)
}

/// Display basic repository status
fn display_basic_status(status: &GitStatus) {
    println!("🌿 Branch: {}", status.current_branch);
    
    if !status.last_commit.is_empty() {
        println!("📝 Last commit: {}", &status.last_commit[..8]);
        println!("💬 Message: {}", status.last_commit_message);
        
        let commit_time = chrono::DateTime::from_timestamp(status.last_commit_time, 0)
            .unwrap_or_default();
        println!("⏰ Time: {}", commit_time.format("%Y-%m-%d %H:%M:%S"));
    } else {
        println!("📝 No commits yet");
    }
}

/// Display detailed repository status
fn display_detailed_status(manager: &BuildingGitManager) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n📋 Recent Commits:");
    println!("{}", "-".repeat(30));
    
    let commits = manager.list_commits(5)?;
    
    if commits.is_empty() {
        println!("No commits found");
    } else {
        for (i, commit) in commits.iter().enumerate() {
            let commit_time = chrono::DateTime::from_timestamp(commit.time, 0)
                .unwrap_or_default();
            
            println!("{}. {} - {}", 
                i + 1,
                &commit.id[..8],
                commit.message.lines().next().unwrap_or("No message")
            );
            println!("   Author: {} | Time: {}", 
                commit.author,
                commit_time.format("%Y-%m-%d %H:%M:%S")
            );
        }
    }
    
    Ok(())
}

/// Check working directory status for uncommitted changes
fn check_working_directory_status(_repo_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n📁 Working Directory Status:");
    println!("{}", "-".repeat(30));
    
    // Check for YAML files in current directory
    let yaml_files = loading::find_yaml_files()?;
    
    if yaml_files.is_empty() {
        println!("📄 No YAML files found in working directory");
        println!("💡 Run 'arx import <file.ifc>' to generate building data");
    } else {
        println!("📄 Found {} YAML file(s):", yaml_files.len());
        for file in yaml_files {
            println!("   • {}", file);
        }
    }
    
    // Check for IFC files
    let ifc_files = loading::find_ifc_files()?;
    
    if !ifc_files.is_empty() {
        println!("🏗️ Found {} IFC file(s):", ifc_files.len());
        for file in ifc_files {
            println!("   • {}", file);
        }
    }
    
    Ok(())
}

/// Display diff statistics
fn display_diff_stats(stats: &DiffStats) {
    println!("📊 Diff Statistics:");
    println!("{}", "-".repeat(30));
    println!("📁 Files changed: {}", stats.files_changed);
    println!("➕ Insertions: {}", stats.insertions);
    println!("➖ Deletions: {}", stats.deletions);
    
    if stats.insertions > 0 || stats.deletions > 0 {
        let net_change = stats.insertions as i32 - stats.deletions as i32;
        if net_change > 0 {
            println!("📈 Net change: +{}", net_change);
        } else if net_change < 0 {
            println!("📉 Net change: {}", net_change);
        } else {
            println!("⚖️ Net change: 0");
        }
    }
}

/// Display full diff result
fn display_diff_result(diff_result: &DiffResult, single_file: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📝 Commit: {} → {}", 
        &diff_result.compare_hash[..8], 
        &diff_result.commit_hash[..8]
    );
    
    if !single_file {
        println!("📊 {} files changed, {} insertions(+), {} deletions(-)", 
            diff_result.files_changed,
            diff_result.insertions,
            diff_result.deletions
        );
    }
    
    if diff_result.file_diffs.is_empty() {
        println!("✅ No changes found");
        return Ok(());
    }
    
    // Group diffs by file
    let mut current_file = String::new();
    for diff in &diff_result.file_diffs {
        if diff.file_path != current_file {
            current_file = diff.file_path.clone();
            println!("\n📄 {}", current_file);
            println!("{}", "-".repeat(50));
        }
        
        let prefix = match diff.line_type {
            DiffLineType::Addition => "+",
            DiffLineType::Deletion => "-",
            DiffLineType::Context => " ",
        };
        
        let color = match diff.line_type {
            DiffLineType::Addition => "🟢",
            DiffLineType::Deletion => "🔴",
            DiffLineType::Context => "⚪",
        };
        
        println!("{}{:4} {}{}", 
            color,
            diff.line_number,
            prefix,
            diff.content
        );
    }
    
    Ok(())
}

/// Display commit history
fn display_commit_history(commits: &[CommitInfo], verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    for (i, commit) in commits.iter().enumerate() {
        let short_hash = &commit.id[..8];
        let timestamp = chrono::DateTime::from_timestamp(commit.time, 0)
            .unwrap_or_default()
            .format("%Y-%m-%d %H:%M:%S")
            .to_string();
        
        if verbose {
            // Detailed format
            println!("{} 📝 Commit #{}", "=".repeat(20), i + 1);
            println!("🆔 Hash: {}", commit.id);
            println!("👤 Author: {}", commit.author);
            println!("⏰ Date: {}", timestamp);
            println!("💬 Message: {}", commit.message);
            println!();
        } else {
            // Compact format
            let message_preview = if commit.message.len() > 60 {
                format!("{}...", &commit.message[..57])
            } else {
                commit.message.clone()
            };
            
            println!("{} {} {} {} {}", 
                short_hash,
                timestamp,
                commit.author,
                "📝",
                message_preview
            );
        }
    }
    
    Ok(())
}

/// Handle status command - show repository status and changes
pub fn handle_status(verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📊 ArxOS Repository Status");
    println!("{}", "=".repeat(50));
    
    // Check if we're in a Git repository
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        // Initialize Git manager
        let config = GitConfigManager::default_config();
        let manager = BuildingGitManager::new(&repo_path, "Building", config)?;
        
        // Get repository status
        let status = manager.get_status()?;
        
        // Display basic status
        display_basic_status(&status);
        
        if verbose {
            // Display detailed information
            display_detailed_status(&manager)?;
        }
        
        // Check for uncommitted changes
        check_working_directory_status(&repo_path)?;
        
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Handle diff command - show differences between commits
pub fn handle_diff(commit: Option<String>, file: Option<String>, stat: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 ArxOS Diff");
    println!("{}", "=".repeat(50));
    
    // Check if we're in a Git repository
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        // Initialize Git manager
        let config = GitConfigManager::default_config();
        let manager = BuildingGitManager::new(&repo_path, "Building", config)?;
        
        if stat {
            // Show statistics only
            let stats = manager.get_diff_stats(commit.as_deref())?;
            display_diff_stats(&stats);
        } else {
            // Show full diff
            let diff_result = manager.get_diff(commit.as_deref(), file.as_deref())?;
            display_diff_result(&diff_result, file.is_some())?;
        }
        
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Handle stage command - stage changes for commit
pub fn handle_stage(_all: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("📦 Staging changes");
    println!("{}", "=".repeat(50));
    
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        let config = GitConfigManager::default_config();
        let mut manager = BuildingGitManager::new(&repo_path, "Building", config)?;
        
        if let Some(file_path) = file {
            println!("📄 Staging file: {}", file_path);
            manager.stage_file(&file_path)?;
            println!("✅ Staged: {}", file_path);
        } else {
            println!("📁 Staging all changes");
            let staged_files = manager.stage_all()?;
            println!("✅ Staged {} files", staged_files);
        }
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Handle commit command - commit staged changes
pub fn handle_commit(message: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("💾 Committing changes");
    println!("{}", "=".repeat(50));
    
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        let config = GitConfigManager::default_config();
        let mut manager = BuildingGitManager::new(&repo_path, "Building", config)?;
        
        println!("📝 Message: {}", message);
        let commit_id = manager.commit_staged(&message)?;
        println!("✅ Committed: {}", &commit_id[..8]);
        println!("💬 {}", message);
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Handle unstage command - unstage changes
pub fn handle_unstage(_all: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("📤 Unstaging changes");
    println!("{}", "=".repeat(50));
    
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        let config = GitConfigManager::default_config();
        let mut manager = BuildingGitManager::new(&repo_path, "Building", config)?;
        
        if let Some(file_path) = file {
            println!("📄 Unstaging file: {}", file_path);
            manager.unstage_file(&file_path)?;
            println!("✅ Unstaged: {}", file_path);
        } else {
            println!("📁 Unstaging all changes");
            let unstaged_files = manager.unstage_all()?;
            println!("✅ Unstaged {} files", unstaged_files);
        }
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Handle history command - show commit history
pub fn handle_history(limit: usize, verbose: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("📚 ArxOS History");
    println!("{}", "=".repeat(50));
    
    // Check if we're in a Git repository
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        // Initialize Git manager
        let config = GitConfigManager::default_config();
        let manager = BuildingGitManager::new(&repo_path, "Building", config)?;
        
        // Get commit history
        let commits = if let Some(file_path) = file {
            // Show history for specific file
            println!("📄 File History: {}", file_path);
            println!("{}", "-".repeat(30));
            manager.get_file_history(&file_path)?
        } else {
            // Show general commit history
            println!("📊 Recent Commits (showing {}):", limit);
            println!("{}", "-".repeat(30));
            manager.list_commits(limit)?
        };
        
        if commits.is_empty() {
            println!("📭 No commits found");
            return Ok(());
        }
        
        // Display commits
        display_commit_history(&commits, verbose)?;
        
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}
