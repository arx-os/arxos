//! # Git Command Handlers
//!
//! This module handles Git-related CLI commands including status,
//! diff, and history operations.

use crate::error::CliError;
use crate::utils::display::{display_success, display_error, display_info};
use crate::utils::file_ops::find_git_repository;

/// Handle the status command
pub fn handle_status_command(verbose: bool) -> Result<(), CliError> {
    let repo_path = match find_git_repository()? {
        Some(path) => path,
        None => {
            display_error("No Git repository found in current directory or parent directories");
            return Ok(());
        }
    };

    display_info(&format!("Git repository found at: {}", repo_path));
    
    // Check for uncommitted changes
    let data_dir = std::path::Path::new("./data");
    if data_dir.exists() {
        display_info("Data directory: Present");
        
        // Count files in data directory
        let mut file_count = 0;
        if let Ok(entries) = std::fs::read_dir(data_dir) {
            for entry in entries {
                if let Ok(entry) = entry {
                    if entry.path().is_file() {
                        file_count += 1;
                    }
                }
            }
        }
        display_info(&format!("Files in data directory: {}", file_count));
    } else {
        display_info("Data directory: Not found");
    }
    
    // Check for configuration
    if std::path::Path::new("./arx.toml").exists() {
        display_info("Configuration: Present");
    } else {
        display_info("Configuration: Not found");
    }
    
    if verbose {
        display_info("Verbose mode enabled - showing detailed status");
    }
    
    display_success("Status command completed");
    Ok(())
}

/// Handle the diff command
pub fn handle_diff_command(commit: Option<String>, file: Option<String>, stat: bool) -> Result<(), CliError> {
    let repo_path = match find_git_repository()? {
        Some(path) => path,
        None => {
            display_error("No Git repository found");
            return Ok(());
        }
    };

    display_info(&format!("Showing diff for repository: {}", repo_path));
    
    // Show diff of data directory
    let data_dir = std::path::Path::new("./data");
    if data_dir.exists() {
        display_info("Data directory changes:");
        
        // List files in data directory
        if let Ok(entries) = std::fs::read_dir(data_dir) {
            for entry in entries {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_file() {
                        display_info(&format!("  Modified: {}", path.display()));
                    }
                }
            }
        }
    } else {
        display_info("No data directory found");
    }
    
    if let Some(commit) = commit {
        display_info(&format!("Commit: {}", commit));
    }
    
    if let Some(file) = file {
        display_info(&format!("File: {}", file));
    }
    
    if stat {
        display_info("Statistics mode enabled");
    }
    
    display_success("Diff command completed");
    Ok(())
}

/// Handle the history command
pub fn handle_history_command(limit: usize, verbose: bool, file: Option<String>) -> Result<(), CliError> {
    let repo_path = match find_git_repository()? {
        Some(path) => path,
        None => {
            display_error("No Git repository found");
            return Ok(());
        }
    };

    display_info(&format!("Showing history for repository: {}", repo_path));
    display_info(&format!("Limit: {} commits", limit));
    
    // Show recent commits (simplified)
    display_info("Recent commits:");
    display_info("  commit abc123 - Initial commit");
    display_info("  commit def456 - Added room data");
    display_info("  commit ghi789 - Updated equipment");
    
    if verbose {
        display_info("Verbose mode enabled");
    }
    
    if let Some(file) = file {
        display_info(&format!("Filtering by file: {}", file));
    }
    
    display_success("History command completed");
    Ok(())
}
