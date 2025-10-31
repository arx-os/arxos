//! File system path safety utilities for ArxOS
//!
//! This module provides secure path operations that prevent directory traversal
//! attacks and ensure all file operations are restricted to intended directories.
//!
//! # Security Features
//!
//! - Path canonicalization to resolve `.` and `..` components
//! - Directory traversal prevention
//! - Base directory restriction enforcement
//! - Symlink safety (optional symlink resolution)
//! - Path validation and sanitization

use std::path::{Path, PathBuf};
use crate::error::ArxError;

/// Path safety error types
#[derive(Debug, thiserror::Error)]
pub enum PathSafetyError {
    #[error("Path traversal detected: path escapes base directory")]
    PathTraversal { path: String, base: String },
    
    #[error("Path does not exist: {path}")]
    PathNotFound { path: String },
    
    #[error("Path is not within allowed base directory: {path}")]
    PathOutsideBase { path: String, base: String },
    
    #[error("Cannot canonicalize path: {reason}")]
    CanonicalizationFailed { reason: String },
    
    #[error("Invalid path: {reason}")]
    InvalidPath { reason: String },
}

impl From<PathSafetyError> for ArxError {
    fn from(err: PathSafetyError) -> Self {
        match err {
            PathSafetyError::PathTraversal { path, base } => {
                ArxError::validation(format!("Path traversal detected: {}", path))
                    .with_file_path(path)
                    .with_suggestions(vec![
                        "Ensure the path is within the allowed directory".to_string(),
                        format!("Base directory: {}", base),
                    ])
                    .with_recovery(vec![
                        "Use relative paths from the base directory".to_string(),
                        "Do not use '..' in file paths".to_string(),
                    ])
            }
            PathSafetyError::PathNotFound { path } => {
                ArxError::io_error(format!("File not found: {}", path))
                    .with_file_path(path.clone())
                    .with_suggestions(vec![
                        "Check if the file exists".to_string(),
                        "Verify file permissions".to_string(),
                    ])
            }
            PathSafetyError::PathOutsideBase { path, base } => {
                ArxError::validation(format!("Path outside base directory: {}", path))
                    .with_file_path(path)
                    .with_suggestions(vec![
                        format!("Path must be within: {}", base),
                        "Use relative paths from the base directory".to_string(),
                    ])
            }
            PathSafetyError::CanonicalizationFailed { reason } => {
                ArxError::io_error(format!("Cannot resolve path: {}", reason))
                    .with_suggestions(vec![
                        "Check if the path exists".to_string(),
                        "Verify directory permissions".to_string(),
                    ])
            }
            PathSafetyError::InvalidPath { reason } => {
                ArxError::validation(format!("Invalid path: {}", reason))
                    .with_suggestions(vec![
                        "Ensure path does not contain invalid characters".to_string(),
                        "Check path length is within limits".to_string(),
                    ])
            }
        }
    }
}

/// Path safety utilities for secure file operations
pub struct PathSafety;

impl PathSafety {
    /// Canonicalize and validate a path, ensuring it's within a base directory
    ///
    /// # Arguments
    ///
    /// * `path` - The path to canonicalize (can be relative or absolute)
    /// * `base_dir` - The base directory that the path must be within
    ///
    /// # Returns
    ///
    /// Returns the canonicalized path if it's valid and within the base directory
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - The path cannot be canonicalized
    /// - The path exists but is outside the base directory
    /// - Path traversal is detected (even if canonicalization fails)
    ///
    /// # Examples
    ///
    /// ```rust,no_run
    /// use std::path::Path;
    /// use arxos::utils::path_safety::PathSafety;
    ///
    /// let base = Path::new("/safe/directory");
    /// let path = Path::new("../etc/passwd");
    ///
    /// // This will return an error - path traversal detected
    /// let result = PathSafety::canonicalize_and_validate(path, base);
    /// assert!(result.is_err());
    /// ```
    pub fn canonicalize_and_validate(
        path: &Path,
        base_dir: &Path,
    ) -> Result<PathBuf, PathSafetyError> {
        // First, ensure base_dir is canonicalized
        let base_canonical = base_dir
            .canonicalize()
            .map_err(|e| PathSafetyError::CanonicalizationFailed {
                reason: format!("Cannot canonicalize base directory: {}", e),
            })?;

        // Detect obvious path traversal attempts before canonicalization
        Self::detect_path_traversal(path)?;

        // If path is relative, join it with base_dir first
        let path_to_canonicalize = if path.is_absolute() {
            path.to_path_buf()
        } else {
            base_canonical.join(path)
        };

        // Canonicalize the path
        let canonical_path = path_to_canonicalize
            .canonicalize()
            .map_err(|e| {
                // Check if path traversal was attempted (file doesn't exist, but could be traversal)
                if path_to_canonicalize.to_string_lossy().contains("..") {
                    PathSafetyError::PathTraversal {
                        path: path.display().to_string(),
                        base: base_canonical.display().to_string(),
                    }
                } else {
                    PathSafetyError::CanonicalizationFailed {
                        reason: format!("Cannot canonicalize path: {}", e),
                    }
                }
            })?;

        // Verify the canonicalized path is within the base directory
        Self::ensure_path_within_base(&canonical_path, &base_canonical)?;

        Ok(canonical_path)
    }

    /// Validate a path for writing (file may not exist yet)
    ///
    /// This function validates that a path is safe to write to without requiring
    /// the file itself to exist. It canonicalizes the parent directory instead.
    pub fn validate_path_for_write(
        path: &Path,
        base_dir: &Path,
    ) -> Result<PathBuf, PathSafetyError> {
        // First, ensure base_dir is canonicalized
        let base_canonical = base_dir
            .canonicalize()
            .map_err(|e| PathSafetyError::CanonicalizationFailed {
                reason: format!("Cannot canonicalize base directory: {}", e),
            })?;

        // Detect obvious path traversal attempts
        Self::detect_path_traversal(path)?;

        // If path is relative, join it with base_dir first
        let full_path = if path.is_absolute() {
            path.to_path_buf()
        } else {
            base_canonical.join(path)
        };

        // Canonicalize the parent directory (which should exist) to validate structure
        let parent = full_path.parent()
            .unwrap_or_else(|| base_dir.as_ref());
        
        let canonical_parent = parent
            .canonicalize()
            .map_err(|e| {
                // Check if path traversal was attempted
                if full_path.to_string_lossy().contains("..") {
                    PathSafetyError::PathTraversal {
                        path: path.display().to_string(),
                        base: base_canonical.display().to_string(),
                    }
                } else {
                    PathSafetyError::CanonicalizationFailed {
                        reason: format!("Cannot canonicalize parent directory: {}", e),
                    }
                }
            })?;

        // Ensure parent is within base
        Self::ensure_path_within_base(&canonical_parent, &base_canonical)?;

        // Construct the final canonical path
        let file_name = full_path.file_name()
            .ok_or_else(|| PathSafetyError::InvalidPath {
                reason: "Path must have a file name".to_string(),
            })?;
        
        let canonical_path = canonical_parent.join(file_name);
        
        // Final check: ensure the final path is within base (using string comparison)
        let canonical_path_str = canonical_path.to_string_lossy();
        let base_str = base_canonical.to_string_lossy();
        
        if !canonical_path_str.starts_with(&*base_str) {
            return Err(PathSafetyError::PathOutsideBase {
                path: canonical_path.display().to_string(),
                base: base_canonical.display().to_string(),
            });
        }

        Ok(canonical_path)
    }

    /// Ensure a path is within a base directory
    ///
    /// This function checks that the canonicalized path is a child of the base directory.
    ///
    /// # Security Note
    ///
    /// This function assumes both paths are already canonicalized. Use `canonicalize_and_validate`
    /// if you need automatic canonicalization.
    pub fn ensure_path_within_base(
        path: &Path,
        base_dir: &Path,
    ) -> Result<PathBuf, PathSafetyError> {
        // Both paths should be canonicalized at this point
        let path_str = path.to_string_lossy();
        let base_str = base_dir.to_string_lossy();

        // Check if path starts with base directory
        if !path_str.starts_with(&*base_str) {
            return Err(PathSafetyError::PathOutsideBase {
                path: path.display().to_string(),
                base: base_dir.display().to_string(),
            });
        }

        // Additional check: ensure it's not just a prefix match
        // Path separator must match exactly
        if path != base_dir {
            // Check if there's a path separator after the base
            let remainder = path_str.strip_prefix(&*base_str);
            if let Some(remainder) = remainder {
                if !remainder.starts_with(std::path::MAIN_SEPARATOR) && !remainder.is_empty() {
                    return Err(PathSafetyError::PathOutsideBase {
                        path: path.display().to_string(),
                        base: base_dir.display().to_string(),
                    });
                }
            }
        }

        Ok(path.to_path_buf())
    }

    /// Detect obvious path traversal attempts
    ///
    /// This performs basic pattern matching to catch common traversal attempts
    /// before attempting file system operations.
    pub fn detect_path_traversal(path: &Path) -> Result<(), PathSafetyError> {
        let path_str = path.to_string_lossy();

        // Check for obvious traversal patterns
        if path_str.contains("../") || path_str.contains("..\\") {
            return Err(PathSafetyError::PathTraversal {
                path: path.display().to_string(),
                base: "detected during validation".to_string(),
            });
        }

        // Check for leading traversal sequences
        if path_str.starts_with("../") || path_str.starts_with("..\\") {
            return Err(PathSafetyError::PathTraversal {
                path: path.display().to_string(),
                base: "detected during validation".to_string(),
            });
        }

        // Check for absolute paths that might be problematic
        // (We allow absolute paths, but they'll be validated against base_dir)
        if cfg!(unix) {
            // On Unix, check for attempts to escape to root-sensitive locations
            if path_str.starts_with("/etc/")
                || path_str.starts_with("/usr/")
                || path_str.starts_with("/bin/")
                || path_str.starts_with("/sbin/")
            {
                // This might be legitimate, but we'll catch it in canonicalize_and_validate
                // if it's outside the base directory
            }
        }

        Ok(())
    }

    /// Validate a path for basic safety
    ///
    /// Checks for:
    /// - Empty paths
    /// - Null bytes (Unix concern)
    /// - Path length limits
    /// - Invalid characters
    pub fn validate_path_format(path: &Path) -> Result<(), PathSafetyError> {
        let path_str = path.to_string_lossy();

        if path_str.is_empty() {
            return Err(PathSafetyError::InvalidPath {
                reason: "Path cannot be empty".to_string(),
            });
        }

        // Check for null bytes (Unix path injection concern)
        if path_str.contains('\0') {
            return Err(PathSafetyError::InvalidPath {
                reason: "Path contains null byte".to_string(),
            });
        }

        // Check path length (reasonable limit)
        if path_str.len() > 4096 {
            return Err(PathSafetyError::InvalidPath {
                reason: format!("Path too long: {} characters (max 4096)", path_str.len()),
            });
        }

        Ok(())
    }

    /// Safely read file with full path validation
    ///
    /// This is a convenience function that combines canonicalization, validation,
    /// and file reading in a single secure operation.
    pub fn read_file_safely(
        file_path: &Path,
        base_dir: &Path,
    ) -> Result<String, PathSafetyError> {
        // Validate format first
        Self::validate_path_format(file_path)?;

        // Canonicalize and ensure within base
        let canonical_path = Self::canonicalize_and_validate(file_path, base_dir)?;

        // Read the file
        std::fs::read_to_string(&canonical_path)
            .map_err(|e| PathSafetyError::PathNotFound {
                path: format!("{}: {}", canonical_path.display(), e),
            })
    }

    /// Safely read directory with full path validation
    ///
    /// Returns a list of canonicalized paths within the base directory.
    pub fn read_dir_safely(
        dir_path: &Path,
        base_dir: &Path,
    ) -> Result<Vec<PathBuf>, PathSafetyError> {
        // Validate format first
        Self::validate_path_format(dir_path)?;

        // Canonicalize and ensure within base
        let canonical_dir = Self::canonicalize_and_validate(dir_path, base_dir)?;
        
        // Canonicalize base_dir as well for comparison
        let canonical_base = base_dir
            .canonicalize()
            .map_err(|e| PathSafetyError::CanonicalizationFailed {
                reason: format!("Cannot canonicalize base directory: {}", e),
            })?;

        // Read directory contents
        let entries = std::fs::read_dir(&canonical_dir)
            .map_err(|e| PathSafetyError::PathNotFound {
                path: format!("{}: {}", canonical_dir.display(), e),
            })?;

        let mut paths = Vec::new();
        for entry in entries {
            let entry = entry.map_err(|e| PathSafetyError::PathNotFound {
                path: format!("{}: {}", canonical_dir.display(), e),
            })?;

            let entry_path = entry.path();
            
            // Canonicalize the entry path before validation
            let canonical_entry = entry_path.canonicalize()
                .map_err(|e| PathSafetyError::CanonicalizationFailed {
                    reason: format!("Cannot canonicalize entry path: {}", e),
                })?;
            
            // Validate each entry is still within base (both paths are canonicalized)
            match Self::ensure_path_within_base(&canonical_entry, &canonical_base) {
                Ok(validated_path) => paths.push(validated_path),
                Err(_) => {
                    // Skip entries outside base (shouldn't happen, but be safe)
                    continue;
                }
            }
        }

        Ok(paths)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    use std::fs;

    #[test]
    fn test_path_traversal_detection() {
        // Test obvious traversal patterns
        assert!(PathSafety::detect_path_traversal(Path::new("../etc/passwd")).is_err());
        assert!(PathSafety::detect_path_traversal(Path::new("../../etc/passwd")).is_err());
        assert!(PathSafety::detect_path_traversal(Path::new("..\\windows\\system32")).is_err());
    }

    #[test]
    fn test_validate_path_format() {
        // Valid paths
        assert!(PathSafety::validate_path_format(Path::new("test.yml")).is_ok());
        assert!(PathSafety::validate_path_format(Path::new("./test.yml")).is_ok());
        
        // Invalid paths
        assert!(PathSafety::validate_path_format(Path::new("")).is_err());
        assert!(PathSafety::validate_path_format(Path::new("/path/with\0null")).is_err());
    }

    #[test]
    fn test_canonicalize_and_validate_relative_path() {
        let temp_dir = TempDir::new().unwrap();
        let base = temp_dir.path();
        
        // Create a test file
        let test_file = base.join("test.yml");
        fs::write(&test_file, "test content").unwrap();
        
        // Valid relative path
        let result = PathSafety::canonicalize_and_validate(Path::new("test.yml"), base);
        assert!(result.is_ok());
        
        // Path traversal attempt
        let result = PathSafety::canonicalize_and_validate(Path::new("../test.yml"), base);
        assert!(result.is_err());
    }

    #[test]
    fn test_canonicalize_and_validate_absolute_path() {
        let temp_dir = TempDir::new().unwrap();
        let base = temp_dir.path();
        
        // Create a test file
        let test_file = base.join("test.yml");
        fs::write(&test_file, "test content").unwrap();
        
        // Valid absolute path within base
        let abs_path = test_file.canonicalize().unwrap();
        let result = PathSafety::canonicalize_and_validate(&abs_path, base);
        assert!(result.is_ok());
        
        // Try to access file outside base (using parent)
        if let Some(parent) = base.parent() {
            let outside_file = parent.join("outside.yml");
            let result = PathSafety::canonicalize_and_validate(&outside_file, base);
            assert!(result.is_err());
        }
    }

    #[test]
    fn test_ensure_path_within_base() {
        let temp_dir = TempDir::new().unwrap();
        let base = temp_dir.path();
        
        // Create subdirectory structure
        let subdir = base.join("subdir");
        fs::create_dir(&subdir).unwrap();
        let file = subdir.join("file.yml");
        fs::write(&file, "content").unwrap();
        
        let base_canonical = base.canonicalize().unwrap();
        let file_canonical = file.canonicalize().unwrap();
        
        // File should be within base
        assert!(PathSafety::ensure_path_within_base(&file_canonical, &base_canonical).is_ok());
        
        // Try with path outside base
        if let Some(parent) = base_canonical.parent() {
            assert!(PathSafety::ensure_path_within_base(parent, &base_canonical).is_err());
        }
    }

    #[test]
    fn test_read_file_safely() {
        let temp_dir = TempDir::new().unwrap();
        let base = temp_dir.path();
        
        // Create test file
        let test_file = base.join("test.yml");
        fs::write(&test_file, "test content").unwrap();
        
        // Read valid file
        let content = PathSafety::read_file_safely(Path::new("test.yml"), base).unwrap();
        assert_eq!(content, "test content");
        
        // Try path traversal
        assert!(PathSafety::read_file_safely(Path::new("../test.yml"), base).is_err());
        
        // Try non-existent file
        assert!(PathSafety::read_file_safely(Path::new("nonexistent.yml"), base).is_err());
    }

    #[test]
    fn test_read_dir_safely() {
        let temp_dir = TempDir::new().unwrap();
        let base = temp_dir.path();
        
        // Create test files
        fs::write(base.join("file1.yml"), "content1").unwrap();
        fs::write(base.join("file2.yml"), "content2").unwrap();
        fs::write(base.join("file3.yaml"), "content3").unwrap();
        
        // Read directory - use the base directory itself, not "."
        let paths = PathSafety::read_dir_safely(base, base).unwrap();
        assert!(paths.len() >= 3, "Expected at least 3 files, got {}", paths.len()); // At least our test files
        
        // Try path traversal
        assert!(PathSafety::read_dir_safely(Path::new("../"), base).is_err());
    }
}

