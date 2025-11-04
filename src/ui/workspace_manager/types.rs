//! Workspace Manager Types
//!
//! Defines core types for the workspace management system.

use std::path::PathBuf;

/// Workspace/Building information
#[derive(Debug, Clone)]
pub struct Workspace {
    /// Building name
    pub name: String,
    /// Path to building.yaml file
    pub path: PathBuf,
    /// Git repository path (if applicable)
    pub git_repo: Option<PathBuf>,
    /// Description (from building.yaml)
    pub description: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_workspace_structure() {
        let workspace = Workspace {
            name: "Test Building".to_string(),
            path: PathBuf::from("/test/building.yaml"),
            git_repo: Some(PathBuf::from("/test")),
            description: Some("Test description".to_string()),
        };
        
        assert_eq!(workspace.name, "Test Building");
        assert_eq!(workspace.path, PathBuf::from("/test/building.yaml"));
        assert_eq!(workspace.git_repo, Some(PathBuf::from("/test")));
        assert_eq!(workspace.description, Some("Test description".to_string()));
    }

    #[test]
    fn test_workspace_clone() {
        let workspace = Workspace {
            name: "Test Building".to_string(),
            path: PathBuf::from("/test/building.yaml"),
            git_repo: Some(PathBuf::from("/test")),
            description: Some("Test description".to_string()),
        };
        
        let cloned = workspace.clone();
        assert_eq!(workspace.name, cloned.name);
        assert_eq!(workspace.path, cloned.path);
        assert_eq!(workspace.git_repo, cloned.git_repo);
        assert_eq!(workspace.description, cloned.description);
    }
}

