//! Utility functions for hierarchy building
//!
//! Helper functions used across hierarchy construction modules.

use std::collections::HashSet;

/// Ensure a path is unique by appending a numeric suffix if needed
///
/// This function manages canonical path uniqueness by tracking used paths
/// and automatically appending a numeric suffix (-1, -2, etc.) if the
/// base path is already in use.
///
/// # Arguments
///
/// * `base` - The proposed path
/// * `used` - Set of already-used paths (will be updated)
///
/// # Returns
///
/// A unique path, either the original base or base-N where N is a number
///
/// # Examples
///
/// ```ignore
/// use std::collections::HashSet;
/// use crate::ifc::hierarchy::utils::ensure_unique_path;
///
/// let mut used = HashSet::new();
///
/// // First use returns the base path
/// let path1 = ensure_unique_path("/building/floor-1", &mut used);
/// assert_eq!(path1, "/building/floor-1");
///
/// // Second use of same base appends -1
/// let path2 = ensure_unique_path("/building/floor-1", &mut used);
/// assert_eq!(path2, "/building/floor-1-1");
///
/// // Third use appends -2
/// let path3 = ensure_unique_path("/building/floor-1", &mut used);
/// assert_eq!(path3, "/building/floor-1-2");
/// ```
pub fn ensure_unique_path(base: &str, used: &mut HashSet<String>) -> String {
    if used.insert(base.to_string()) {
        // Path is not in use, return as-is
        base.to_string()
    } else {
        // Path is already used, find next available suffix
        let mut index = 1;
        loop {
            let candidate = format!("{}-{}", base, index);
            if used.insert(candidate.clone()) {
                return candidate;
            }
            index += 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ensure_unique_path_first_use() {
        let mut used = HashSet::new();
        let path = ensure_unique_path("/building/floor-1", &mut used);
        assert_eq!(path, "/building/floor-1");
        assert!(used.contains("/building/floor-1"));
    }

    #[test]
    fn test_ensure_unique_path_duplicate() {
        let mut used = HashSet::new();

        let path1 = ensure_unique_path("/building/floor-1", &mut used);
        assert_eq!(path1, "/building/floor-1");

        let path2 = ensure_unique_path("/building/floor-1", &mut used);
        assert_eq!(path2, "/building/floor-1-1");

        let path3 = ensure_unique_path("/building/floor-1", &mut used);
        assert_eq!(path3, "/building/floor-1-2");
    }

    #[test]
    fn test_ensure_unique_path_multiple_bases() {
        let mut used = HashSet::new();

        let path1 = ensure_unique_path("/building/floor-1", &mut used);
        assert_eq!(path1, "/building/floor-1");

        let path2 = ensure_unique_path("/building/floor-2", &mut used);
        assert_eq!(path2, "/building/floor-2");

        // Duplicate of first base
        let path3 = ensure_unique_path("/building/floor-1", &mut used);
        assert_eq!(path3, "/building/floor-1-1");
    }

    #[test]
    fn test_ensure_unique_path_preserves_existing() {
        let mut used = HashSet::new();
        used.insert("/building/floor-1".to_string());
        used.insert("/building/floor-1-1".to_string());

        // Should skip to -2 since -1 is taken
        let path = ensure_unique_path("/building/floor-1", &mut used);
        assert_eq!(path, "/building/floor-1-2");
    }
}
