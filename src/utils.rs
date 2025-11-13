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
    }
}

/// Path safety utilities
pub mod path_safety {
    use std::path::Path;

    /// Validate that a path is safe to use
    pub fn validate_safe_path(path: &Path) -> Result<(), String> {
        let path_str = path.to_string_lossy();
        
        // Check for dangerous patterns
        if path_str.contains("..") {
            return Err("Path contains dangerous '..' pattern".to_string());
        }
        
        // Check for absolute paths in unsafe contexts
        if path.is_absolute() && path_str.starts_with('/') {
            return Err("Absolute path may be unsafe".to_string());
        }
        
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
            .map(|c| if c.is_alphanumeric() { c } else if c.is_whitespace() { '-' } else { '_' })
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
        .unwrap()
        .as_millis();
    format!("{}_{}", prefix, timestamp)
}

/// Check if a string is empty or whitespace only
pub fn is_empty_or_whitespace(s: &str) -> bool {
    s.trim().is_empty()
}