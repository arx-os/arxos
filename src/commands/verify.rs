//! GPG signature verification commands for ArxOS

use crate::commands::git_ops::find_git_repository;
use crate::identity::is_gpg_available;
use std::process::Command;
use std::path::Path;

/// Handle verify command
pub fn handle_verify(commit: Option<String>, all: bool, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔐 Verifying GPG Signatures");
    println!("{}", "=".repeat(50));
    
    // Check if GPG is available
    if !is_gpg_available() {
        println!("❌ GPG is not available on this system");
        println!("💡 Install GPG to enable commit signature verification");
        println!("   Windows: Download from https://www.gpg4win.org/");
        println!("   macOS:   brew install gnupg");
        println!("   Linux:   sudo apt-get install gnupg");
        return Ok(());
    }
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. Verification requires a Git repository.")?;
    let repo_path = Path::new(&repo_path_str);
    
    if all {
        verify_all_commits(repo_path, verbose)
    } else {
        let commit_hash = commit.unwrap_or_else(|| "HEAD".to_string());
        verify_commit(repo_path, &commit_hash, verbose)
    }
}

/// Verify a specific commit
fn verify_commit(repo_path: &Path, commit_hash: &str, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Verifying commit: {}", commit_hash);
    println!("{}", "-".repeat(30));
    
    // Run git verify-commit
    let output = Command::new("git")
        .arg("-C")
        .arg(repo_path)
        .arg("verify-commit")
        .arg(commit_hash)
        .output()?;
    
    if output.status.success() {
        println!("✅ Commit signature is valid");
        
        if verbose {
            // Get commit details
            let commit_output = Command::new("git")
                .arg("-C")
                .arg(repo_path)
                .arg("show")
                .arg("--no-patch")
                .arg("--format=format:%H%n%an <%ae>%n%ad%n%s")
                .arg(commit_hash)
                .output()?;
            
            if commit_output.status.success() {
                let details = String::from_utf8_lossy(&commit_output.stdout);
                let lines: Vec<&str> = details.lines().collect();
                if lines.len() >= 4 {
                    println!("\n📝 Commit Details:");
                    println!("   Hash:    {}", lines[0]);
                    println!("   Author:  {}", lines[1]);
                    println!("   Date:    {}", lines[2]);
                    println!("   Message: {}", lines[3]);
                }
            }
            
            // Get GPG signature details
            let gpg_output = Command::new("git")
                .arg("-C")
                .arg(repo_path)
                .arg("log")
                .arg("--format=format:%G?%n%GK%n%GS")
                .arg("-1")
                .arg(commit_hash)
                .output()?;
            
            if gpg_output.status.success() {
                let gpg_info = String::from_utf8_lossy(&gpg_output.stdout);
                let lines: Vec<&str> = gpg_info.lines().collect();
                if lines.len() >= 3 {
                    let status = match lines[0] {
                        "G" => "✅ Good signature",
                        "B" => "⚠️  Bad signature",
                        "U" => "❓ Unknown signature",
                        "X" => "❌ Expired signature",
                        "Y" => "⏰ Expired key",
                        "R" => "🚫 Revoked key",
                        "E" => "❌ Error verifying",
                        _ => "❓ Unknown status",
                    };
                    
                    println!("\n🔐 GPG Signature:");
                    println!("   Status:     {}", status);
                    if !lines[1].is_empty() {
                        println!("   Key ID:     {}", lines[1]);
                    }
                    if !lines[2].is_empty() {
                        println!("   Signer:     {}", lines[2]);
                    }
                }
            }
        }
    } else {
        let error = String::from_utf8_lossy(&output.stderr);
        println!("❌ Commit signature verification failed");
        if verbose {
            println!("   Error: {}", error);
        } else {
            println!("   Run with --verbose to see details");
        }
    }
    
    Ok(())
}

/// Verify all commits in the current branch
fn verify_all_commits(repo_path: &Path, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Verifying all commits in current branch");
    println!("{}", "-".repeat(30));
    
    // Get current branch
    let branch_output = Command::new("git")
        .arg("-C")
        .arg(repo_path)
        .arg("rev-parse")
        .arg("--abbrev-ref")
        .arg("HEAD")
        .output()?;
    
    let branch = if branch_output.status.success() {
        String::from_utf8_lossy(&branch_output.stdout).trim().to_string()
    } else {
        "HEAD".to_string()
    };
    
    println!("📍 Branch: {}\n", branch);
    
    // Get all commit hashes
    let commits_output = Command::new("git")
        .arg("-C")
        .arg(repo_path)
        .arg("rev-list")
        .arg(&branch)
        .output()?;
    
    if !commits_output.status.success() {
        return Err("Failed to get commit list".into());
    }
    
    let commits = String::from_utf8_lossy(&commits_output.stdout);
    let commit_hashes: Vec<&str> = commits.lines().collect();
    
    println!("Found {} commits to verify\n", commit_hashes.len());
    
    let mut verified = 0;
    let mut failed = 0;
    let mut unsigned = 0;
    
    for (idx, hash) in commit_hashes.iter().enumerate() {
        let short_hash = &hash[..8.min(hash.len())];
        
        if verbose {
            print!("[{}/{}] Verifying {}... ", idx + 1, commit_hashes.len(), short_hash);
        }
        
        let output = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("verify-commit")
            .arg(hash)
            .output()?;
        
        if output.status.success() {
            verified += 1;
            if verbose {
                println!("✅");
            }
        } else {
            // Check if it's unsigned or actually failed
            let error = String::from_utf8_lossy(&output.stderr);
            if error.contains("no signature") || error.contains("not signed") {
                unsigned += 1;
                if verbose {
                    println!("⚠️  (unsigned)");
                }
            } else {
                failed += 1;
                if verbose {
                    println!("❌");
                }
            }
        }
    }
    
    println!("\n{}", "=".repeat(50));
    println!("📊 Verification Summary:");
    println!("   ✅ Verified:    {}", verified);
    println!("   ⚠️  Unsigned:    {}", unsigned);
    println!("   ❌ Failed:      {}", failed);
    println!("   📝 Total:       {}", commit_hashes.len());
    
    if verified == commit_hashes.len() {
        println!("\n🎉 All commits are verified!");
    } else if unsigned > 0 {
        println!("\n💡 Some commits are unsigned. Configure GPG signing:");
        println!("   git config user.signingkey <KEY_ID>");
        println!("   git config commit.gpgsign true");
    }
    
    Ok(())
}

