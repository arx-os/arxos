//! Utility functions for ArxOS
//!
//! Common helper functions used across multiple modules.

use std::collections::HashMap;

/// Progress tracking utilities
pub mod progress {
    /// Simple progress tracker
    pub struct ProgressTracker {
        current: usize,
        total: usize,
        description: String,
    }

    impl ProgressTracker {
        pub fn new(total: usize, description: String) -> Self {
            Self {
                current: 0,
                total,
                description,
            }
        }

        pub fn increment(&mut self) {
            self.current += 1;
            if self.current % 10 == 0 || self.current == self.total {
                println!("{}: {}/{}", self.description, self.current, self.total);
            }
        }

        pub fn finish(&self) {
            println!("{}: Complete ({}/{})", self.description, self.current, self.total);
        }
    }

    /// Progress context for tracking operations
    pub struct ProgressContext {
        current: usize,
        total: usize,
        description: String,
    }

    impl ProgressContext {
        pub fn new(total: usize, description: String) -> Self {
            Self {
                current: 0,
                total,
                description,
            }
        }

        pub fn update(&mut self, progress_percent: usize, message: &str) {
            self.current = (progress_percent * self.total) / 100;
            println!("{}: {}% - {}", self.description, progress_percent, message);
        }

        pub fn set_total(&mut self, total: usize) {
            self.total = total;
        }

        pub fn finish_error(&self, error_message: &str) {
            eprintln!("{}: ERROR - {}", self.description, error_message);
        }
    }
}

/// Path safety utilities
pub mod path_safety {
    use std::path::{Path, PathBuf};

    /// Validate that a path is safe to use
    pub fn validate_safe_path(path: &Path) -> Result<(), String> {
        let path_str = path.to_string_lossy();

        // Check for path traversal attacks
        if path_str.contains("..") {
            return Err("Path contains dangerous '..' pattern".to_string());
        }

        // Note: Absolute paths are allowed. They're not inherently unsafe.
        // The real security comes from:
        // 1. No path traversal (checked above)
        // 2. Proper file permissions (handled by OS)
        // 3. Input validation at boundaries (caller's responsibility)

        Ok(())
    }

    /// Sanitize a path for safe use
    pub fn sanitize_path(path: &str) -> String {
        path.replace("..", "")
            .replace("//", "/")
            .replace("\\\\", "\\")
    }

    /// Path safety validator
    pub struct PathSafety;

    impl PathSafety {
        pub fn validate_path(path: &Path) -> Result<(), String> {
            validate_safe_path(path)
        }

        pub fn sanitize_path_string(path: &str) -> String {
            sanitize_path(path)
        }

        /// Canonicalize and validate a path
        pub fn canonicalize_and_validate(path: &Path) -> Result<PathBuf, String> {
            // Validate the path first
            Self::validate_path(path)?;

            // Attempt to canonicalize
            path.canonicalize()
                .map_err(|e| format!("Failed to canonicalize path: {}", e))
        }

        /// Safely read a file's contents with path validation
        pub fn read_file_safely(file_path: &Path, _base_dir: &Path) -> Result<String, Box<dyn std::error::Error>> {
            // Validate the path is safe
            Self::validate_path(file_path).map_err(|e| Box::new(std::io::Error::new(std::io::ErrorKind::InvalidInput, e)) as Box<dyn std::error::Error>)?;

            // Read the file
            let content = std::fs::read_to_string(file_path)?;
            Ok(content)
        }

        /// Validate path for write operations
        pub fn validate_path_for_write(path: &Path) -> Result<(), String> {
            // Check basic path safety
            Self::validate_path(path)?;

            // Check if parent directory exists
            if let Some(parent) = path.parent() {
                if !parent.exists() {
                    return Err(format!("Parent directory does not exist: {}", parent.display()));
                }
            }

            // Check if path is writable (if it exists)
            if path.exists() {
                let metadata = std::fs::metadata(path)
                    .map_err(|e| format!("Cannot access path metadata: {}", e))?;
                if metadata.permissions().readonly() {
                    return Err("Path is read-only".to_string());
                }
            }

            Ok(())
        }

        /// Validate path format
        pub fn validate_path_format(path: &str) -> Result<(), String> {
            // Check for empty path
            if path.trim().is_empty() {
                return Err("Path cannot be empty".to_string());
            }

            // Check for null bytes
            if path.contains('\0') {
                return Err("Path contains null bytes".to_string());
            }

            // Check for invalid characters (platform-specific)
            #[cfg(windows)]
            {
                let invalid_chars = ['<', '>', ':', '"', '|', '?', '*'];
                if path.chars().any(|c| invalid_chars.contains(&c)) {
                    return Err("Path contains invalid characters".to_string());
                }
            }

            Ok(())
        }

        /// Detect path traversal attempts
        pub fn detect_path_traversal(path: &str) -> Result<(), String> {
            // Check for .. sequences
            if path.contains("..") {
                return Err("Path traversal detected: contains '..'".to_string());
            }

            // Check for absolute path attempts in relative contexts
            if path.starts_with('/') || path.starts_with('\\') {
                return Err("Absolute path detected in relative context".to_string());
            }

            // Check for drive letter on Windows
            #[cfg(windows)]
            {
                if path.len() >= 2 && path.chars().nth(1) == Some(':') {
                    return Err("Drive letter detected in path".to_string());
                }
            }

            Ok(())
        }
    }
}

/// String utilities
pub mod string {
    /// Truncate a string to a maximum length
    pub fn truncate(s: &str, max_len: usize) -> String {
        if s.len() <= max_len {
            s.to_string()
        } else {
            format!("{}...", &s[..max_len.saturating_sub(3)])
        }
    }

    /// Check if a string contains only ASCII characters
    pub fn is_ascii_only(s: &str) -> bool {
        s.is_ascii()
    }

    /// Clean whitespace from a string
    pub fn clean_whitespace(s: &str) -> String {
        s.split_whitespace().collect::<Vec<_>>().join(" ")
    }

    /// Normalize a label for consistent formatting
    pub fn normalize_label(label: &str) -> String {
        label.trim()
            .chars()
            .map(|c| if c.is_whitespace() { ' ' } else { c })
            .collect::<String>()
            .split_whitespace()
            .collect::<Vec<_>>()
            .join(" ")
    }

    /// Create a URL-friendly slug from a string
    pub fn slugify(s: &str) -> String {
        s.to_lowercase()
            .chars()
            .map(|c| {
                if c.is_alphanumeric() {
                    c
                } else {
                    '-'  // Normalize separators and special chars to dash
                }
            })
            .collect::<String>()
            .split('-')
            .filter(|part| !part.is_empty())
            .collect::<Vec<_>>()
            .join("-")
    }
}

/// Loading utilities module
pub mod loading {
    

    /// Simple loading indicator
    pub fn show_loading_message(message: &str) {
        println!("Loading: {}", message);
    }

    /// Find YAML files in the current directory and subdirectories
    pub fn find_yaml_files() -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let mut yaml_files = Vec::new();
        let current_dir = std::env::current_dir()?;

        // Look for building.yaml files in common locations
        let search_paths = vec![
            current_dir.join("building.yaml"),
            current_dir.join("data/building.yaml"),
            current_dir.join("buildings/building.yaml"),
        ];

        for path in search_paths {
            if path.exists() && path.is_file() {
                if let Some(path_str) = path.to_str() {
                    yaml_files.push(path_str.to_string());
                }
            }
        }

        Ok(yaml_files)
    }
}

/// Create a HashMap from key-value pairs
pub fn hashmap_from_pairs<K, V>(pairs: Vec<(K, V)>) -> HashMap<K, V>
where
    K: std::hash::Hash + Eq,
{
    pairs.into_iter().collect()
}

/// Sanitize a string for use in file names or identifiers
pub fn sanitize_name(name: &str) -> String {
    name.to_lowercase()
        .chars()
        .map(|c| if c.is_alphanumeric() || c == '-' || c == '_' { c } else { '-' })
        .collect::<String>()
        .trim_matches('-')
        .to_string()
}

/// Generate a unique identifier
pub fn generate_id(prefix: &str) -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_else(|_| {
            // System clock is before UNIX epoch - use a random fallback
            use std::collections::hash_map::RandomState;
            use std::hash::BuildHasher;
            
            
            std::time::Duration::from_millis(RandomState::new().hash_one(prefix))
        })
        .as_millis();
    format!("{}_{}", prefix, timestamp)
}

/// Check if a string is empty or whitespace only
pub fn is_empty_or_whitespace(s: &str) -> bool {
    s.trim().is_empty()
}