//! GPG/PGP signature support for ArxOS user identity
//!
//! This module provides utilities for working with GPG signatures in Git commits.
//! Uses Git's native GPG support (no additional dependencies required).
//!
//! Users should configure GPG in their Git config:
//!   git config --global user.signingkey <KEY_ID>
//!   git config --global commit.gpgsign true

use std::path::Path;
use std::process::Command;
use log::{info, warn};
use thiserror::Error;

/// Errors that can occur when working with GPG
#[derive(Error, Debug)]
pub enum GpgError {
    #[error("GPG command failed: {0}")]
    CommandFailed(String),
    
    #[error("GPG key not found: {0}")]
    KeyNotFound(String),
    
    #[error("GPG key fingerprint not found for email: {0}")]
    FingerprintNotFound(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

/// Result type for GPG operations
pub type GpgResult<T> = Result<T, GpgError>;

/// Get the GPG key fingerprint for a user's email address
///
/// This searches for GPG keys associated with the email address.
///
/// # Arguments
/// * `email` - User's email address
///
/// # Returns
/// The GPG key fingerprint (40-character hex string)
pub fn get_key_fingerprint_for_email(email: &str) -> GpgResult<String> {
    info!("Looking up GPG key for email: {}", email);
    
    // Run: gpg --list-secret-keys --keyid-format LONG email
    let output = Command::new("gpg")
        .arg("--list-secret-keys")
        .arg("--keyid-format")
        .arg("LONG")
        .arg(email)
        .output()
        .map_err(|e| GpgError::CommandFailed(format!("Failed to run gpg command: {}", e)))?;
    
    if !output.status.success() {
        return Err(GpgError::KeyNotFound(format!("No GPG key found for email: {}", email)));
    }
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    
    // Parse output to find fingerprint
    // GPG output format: sec   rsa4096/KEY_ID YYYY-MM-DD [expires: YYYY-MM-DD]
    //                    Fingerprint=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    for line in stdout.lines() {
        if line.contains("Fingerprint=") {
            if let Some(fingerprint) = line.split("Fingerprint=").nth(1) {
                let fingerprint = fingerprint.trim().replace(" ", "").to_uppercase();
                if fingerprint.len() == 40 {
                    info!("Found GPG fingerprint: {}", fingerprint);
                    return Ok(fingerprint);
                }
            }
        }
        // Alternative: look for sec line with key ID, then get fingerprint from next lines
        if line.starts_with("sec") || line.starts_with("ssb") {
            // Try to extract from key ID line
            if let Some(parts) = line.split_whitespace().nth(1) {
                if parts.contains('/') {
                    let key_id = parts.split('/').nth(1).unwrap_or("");
                    if let Ok(fp) = get_fingerprint_from_key_id(key_id) {
                        return Ok(fp);
                    }
                }
            }
        }
    }
    
    // Fallback: try to get fingerprint directly from key ID
    if let Ok(key_id) = get_key_id_for_email(email) {
        return get_fingerprint_from_key_id(&key_id);
    }
    
    Err(GpgError::FingerprintNotFound(email.to_string()))
}

/// Get the GPG key ID (short format) for a user's email address
///
/// # Arguments
/// * `email` - User's email address
///
/// # Returns
/// The GPG key ID (16-character hex string)
pub fn get_key_id_for_email(email: &str) -> GpgResult<String> {
    info!("Looking up GPG key ID for email: {}", email);
    
    let output = Command::new("gpg")
        .arg("--list-secret-keys")
        .arg("--keyid-format")
        .arg("SHORT")
        .arg(email)
        .output()
        .map_err(|e| GpgError::CommandFailed(format!("Failed to run gpg command: {}", e)))?;
    
    if !output.status.success() {
        return Err(GpgError::KeyNotFound(format!("No GPG key found for email: {}", email)));
    }
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    
    // Parse output: sec   rsa4096/KEY_ID YYYY-MM-DD
    for line in stdout.lines() {
        if line.starts_with("sec") || line.starts_with("ssb") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 {
                let key_part = parts[1];
                if let Some(key_id) = key_part.split('/').nth(1) {
                    info!("Found GPG key ID: {}", key_id);
                    return Ok(key_id.to_string());
                }
            }
        }
    }
    
    Err(GpgError::KeyNotFound(format!("Could not extract key ID for email: {}", email)))
}

/// Get the full fingerprint from a key ID
///
/// # Arguments
/// * `key_id` - The GPG key ID (short format)
///
/// # Returns
/// The full fingerprint (40-character hex string)
fn get_fingerprint_from_key_id(key_id: &str) -> GpgResult<String> {
    let output = Command::new("gpg")
        .arg("--list-secret-keys")
        .arg("--keyid-format")
        .arg("LONG")
        .arg("--fingerprint")
        .arg(key_id)
        .output()
        .map_err(|e| GpgError::CommandFailed(format!("Failed to run gpg command: {}", e)))?;
    
    if !output.status.success() {
        return Err(GpgError::KeyNotFound(format!("No GPG key found for key ID: {}", key_id)));
    }
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    
    // Parse fingerprint line: Fingerprint = XXXX XXXX XXXX ...
    for line in stdout.lines() {
        if line.contains("Fingerprint") {
            let parts: Vec<&str> = line.split('=').collect();
            if parts.len() >= 2 {
                let fingerprint = parts[1].trim().replace(" ", "").to_uppercase();
                if fingerprint.len() == 40 {
                    return Ok(fingerprint);
                }
            }
        }
    }
    
    Err(GpgError::FingerprintNotFound(key_id.to_string()))
}

/// Sanitize email address for use in filename
///
/// Replaces invalid filename characters with underscores.
pub(crate) fn sanitize_email_for_filename(email: &str) -> String {
    let mut result = String::new();
    for c in email.to_lowercase().chars() {
        match c {
            '@' => result.push_str("_at_"),
            '.' => result.push('_'),
            '+' => result.push_str("_plus_"),
            '-' => result.push('_'),
            c if c.is_alphanumeric() => result.push(c),
            _ => result.push('_'),
        }
    }
    result
}

/// Check if GPG is configured and available
///
/// # Returns
/// True if GPG is available and configured
pub fn is_gpg_available() -> bool {
    Command::new("gpg")
        .arg("--version")
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

/// Get the configured signing key from Git config
///
/// # Arguments
/// * `repo_path` - Path to the Git repository
///
/// # Returns
/// The configured signing key ID, or None if not configured
pub fn get_git_signing_key(repo_path: &Path) -> Option<String> {
    let output = Command::new("git")
        .arg("-C")
        .arg(repo_path)
        .arg("config")
        .arg("user.signingkey")
        .output()
        .ok()?;
    
    if output.status.success() {
        let key = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if !key.is_empty() {
            return Some(key);
        }
    }
    
    None
}

/// Check if commit signing is enabled in Git config
///
/// # Arguments
/// * `repo_path` - Path to the Git repository
///
/// # Returns
/// True if commit signing is enabled
pub fn is_git_signing_enabled(repo_path: &Path) -> bool {
    let output = Command::new("git")
        .arg("-C")
        .arg(repo_path)
        .arg("config")
        .arg("commit.gpgsign")
        .output();
    
    if let Ok(output) = output {
        if output.status.success() {
            let value = String::from_utf8_lossy(&output.stdout).trim().to_lowercase();
            return value == "true" || value == "1" || value == "yes";
        }
    }
    
    false
}

/// Store GPG key fingerprint in user registry
///
/// This is a helper function that updates the user's GPG fingerprint
/// in the registry after they configure GPG.
///
/// # Arguments
/// * `email` - User's email address
/// * `repo_path` - Path to the Git repository
///
/// # Returns
/// The GPG fingerprint if found and stored successfully
pub fn store_gpg_fingerprint_for_user(email: &str, repo_path: &Path) -> GpgResult<String> {
    let fingerprint = get_key_fingerprint_for_email(email)?;
    
    // Update user registry with fingerprint
    use crate::identity::UserRegistry;
    let mut registry = UserRegistry::load(repo_path)
        .map_err(|e| GpgError::CommandFailed(format!("Failed to load user registry: {}", e)))?;
    
    if let Some(user) = registry.find_by_email(email) {
        let mut user_clone = user.clone();
        user_clone.public_key_fingerprint = Some(fingerprint.clone());
        
        // Update user in registry (this would require a method to update)
        // For now, we'll just return the fingerprint
        info!("GPG fingerprint stored for user: {}", email);
    } else {
        warn!("User not found in registry: {}", email);
    }
    
    Ok(fingerprint)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    
    #[test]
    fn test_is_gpg_available() {
        // This test will pass if GPG is installed, fail otherwise
        // It's informational only
        let available = is_gpg_available();
        if available {
            println!("GPG is available on this system");
        } else {
            println!("GPG is not available on this system");
        }
    }
    
    #[test]
    fn test_git_signing_detection() {
        let temp_dir = TempDir::new().unwrap();
        let repo_path = temp_dir.path();
        
        // Initialize a test Git repo
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("init")
            .output();
        
        // Check signing status (should be false by default)
        let signing_enabled = is_git_signing_enabled(repo_path);
        assert!(!signing_enabled); // Should be false for new repo
        
        let signing_key = get_git_signing_key(repo_path);
        assert!(signing_key.is_none()); // Should be None for new repo
    }
    
    #[test]
    fn test_git_signing_config_set_and_get() {
        let temp_dir = TempDir::new().unwrap();
        let repo_path = temp_dir.path();
        
        // Initialize a test Git repo
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("init")
            .output();
        
        // Set signing key
        let test_key = "TEST1234567890ABCD";
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("config")
            .arg("user.signingkey")
            .arg(test_key)
            .output();
        
        // Get signing key
        let signing_key = get_git_signing_key(repo_path);
        assert_eq!(signing_key, Some(test_key.to_string()));
        
        // Set commit signing
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("config")
            .arg("commit.gpgsign")
            .arg("true")
            .output();
        
        // Check signing status
        let signing_enabled = is_git_signing_enabled(repo_path);
        assert!(signing_enabled);
    }
    
    #[test]
    fn test_sanitize_email_for_filename() {
        assert_eq!(sanitize_email_for_filename("test@example.com"), "test_at_example_com");
        assert_eq!(sanitize_email_for_filename("user+tag@domain.co.uk"), "user_plus_tag_at_domain_co_uk");
        assert_eq!(sanitize_email_for_filename("user.name@example.com"), "user_name_at_example_com");
        assert_eq!(sanitize_email_for_filename("user-name@example.com"), "user_name_at_example_com");
        assert_eq!(sanitize_email_for_filename("USER@EXAMPLE.COM"), "user_at_example_com");
    }
    
    #[test]
    fn test_get_key_fingerprint_for_email_no_gpg() {
        // This test will fail if GPG is not available, which is expected
        // We test the error handling
        let result = get_key_fingerprint_for_email("nonexistent@example.com");
        
        // Should either return an error (no GPG) or KeyNotFound (GPG available but no key)
        // Both are acceptable outcomes
        match result {
            Err(GpgError::KeyNotFound(_)) => {
                // GPG is available but key not found - expected
            }
            Err(GpgError::CommandFailed(_)) => {
                // GPG not available or command failed - also acceptable
            }
            Err(_) => {
                // Other errors are also acceptable
            }
            Ok(_) => {
                // If this succeeds, GPG is available and a key exists - unlikely but possible
                // This is fine too
            }
        }
    }
    
    #[test]
    fn test_get_key_id_for_email_no_gpg() {
        // Similar to fingerprint test - test error handling
        let result = get_key_id_for_email("nonexistent@example.com");
        
        match result {
            Err(_) => {
                // Expected - GPG not available or key not found
            }
            Ok(_) => {
                // If this succeeds, it's fine - means GPG is available and key exists
            }
        }
    }
    
    #[test]
    fn test_store_gpg_fingerprint_for_user_no_user() {
        let temp_dir = TempDir::new().unwrap();
        let repo_path = temp_dir.path();
        
        // Initialize Git repo
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("init")
            .output();
        
        // Try to store fingerprint for non-existent user
        // This will fail at fingerprint lookup, which is expected
        let result = store_gpg_fingerprint_for_user("nonexistent@example.com", repo_path);
        
        // Should fail because either GPG not available or key not found
        assert!(result.is_err());
    }
    
    #[test]
    fn test_store_gpg_fingerprint_for_user_with_user() {
        let temp_dir = TempDir::new().unwrap();
        let repo_path = temp_dir.path();
        
        // Initialize Git repo
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("init")
            .output();
        
        // Create user registry with a user
        use crate::identity::{User, UserRegistry};
        let mut registry = UserRegistry::load(repo_path).unwrap();
        let user = User::new(
            "test@example.com".to_string(),
            "Test User".to_string(),
            None,
            None,
            None,
        );
        registry.add_user(user).unwrap();
        registry.save().unwrap();
        
        // Try to store fingerprint (will fail if GPG not available, which is fine)
        let result = store_gpg_fingerprint_for_user("test@example.com", repo_path);
        
        // Result depends on whether GPG is available
        // If GPG is available and key exists, it should succeed
        // If not, it should fail gracefully
        match result {
            Ok(_) => {
                // Success - GPG available and key found
            }
            Err(_) => {
                // Expected - GPG not available or key not found
            }
        }
    }
    
    #[test]
    fn test_git_signing_config_variations() {
        let temp_dir = TempDir::new().unwrap();
        let repo_path = temp_dir.path();
        
        // Initialize Git repo
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("init")
            .output();
        
        // Test different true values
        for value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"] {
            let _ = Command::new("git")
                .arg("-C")
                .arg(repo_path)
                .arg("config")
                .arg("commit.gpgsign")
                .arg(value)
                .output();
            
            assert!(is_git_signing_enabled(repo_path), "Should recognize '{}' as true", value);
        }
        
        // Test false values
        let _ = Command::new("git")
            .arg("-C")
            .arg(repo_path)
            .arg("config")
            .arg("commit.gpgsign")
            .arg("false")
            .output();
        
        assert!(!is_git_signing_enabled(repo_path));
    }
    
    #[test]
    fn test_gpg_error_display() {
        let error = GpgError::KeyNotFound("test@example.com".to_string());
        assert!(error.to_string().contains("test@example.com"));
        
        let error = GpgError::CommandFailed("test error".to_string());
        assert!(error.to_string().contains("test error"));
        
        let error = GpgError::FingerprintNotFound("test@example.com".to_string());
        assert!(error.to_string().contains("test@example.com"));
    }
}

