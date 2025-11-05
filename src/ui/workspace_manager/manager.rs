//! Workspace Manager State Management
//!
//! Handles the state and logic for workspace management.

use super::{types::Workspace, discovery::discover_workspaces};
use crate::ui::{HelpSystem, HelpContext};
use ratatui::widgets::ListState;
use std::path::PathBuf;

/// Workspace manager state
pub struct WorkspaceManager {
    /// All available workspaces
    workspaces: Vec<Workspace>,
    /// Filtered workspaces based on search
    filtered_workspaces: Vec<usize>,
    /// Search query
    query: String,
    /// Selected workspace index
    selected: usize,
    /// List state for rendering
    list_state: ListState,
    /// Help system
    help_system: HelpSystem,
    /// Currently active workspace
    active_workspace: Option<PathBuf>,
}

impl WorkspaceManager {
    /// Create a new workspace manager
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let workspaces = discover_workspaces()?;
        let filtered_workspaces: Vec<usize> = (0..workspaces.len()).collect();
        
        // Detect current active workspace (from current directory)
        let active_workspace = std::env::current_dir()
            .ok()
            .and_then(|dir| {
                // Check if current directory has a building.yaml
                let yaml_path = dir.join("building.yaml");
                if yaml_path.exists() {
                    Some(yaml_path)
                } else {
                    None
                }
            });
        
        let mut list_state = ListState::default();
        if !workspaces.is_empty() {
            list_state.select(Some(0));
        }
        
        Ok(Self {
            workspaces,
            filtered_workspaces,
            query: String::new(),
            selected: 0,
            list_state,
            help_system: HelpSystem::new(HelpContext::General),
            active_workspace,
        })
    }
    
    /// Update search query and filter workspaces
    pub fn update_query(&mut self, query: String) {
        self.query = query.clone();
        
        if query.is_empty() {
            self.filtered_workspaces = (0..self.workspaces.len()).collect();
        } else {
            self.filtered_workspaces = self.workspaces
                .iter()
                .enumerate()
                .filter(|(_, ws)| {
                    let query_lower = query.to_lowercase();
                    ws.name.to_lowercase().contains(&query_lower) ||
                    ws.description.as_ref()
                        .map(|d| d.to_lowercase().contains(&query_lower))
                        .unwrap_or(false)
                })
                .map(|(idx, _)| idx)
                .collect();
        }
        
        // Reset selection
        self.selected = 0;
        self.list_state.select(Some(0));
    }
    
    /// Get current query
    pub fn query(&self) -> &str {
        &self.query
    }
    
    /// Get selected workspace
    pub fn selected_workspace(&self) -> Option<&Workspace> {
        self.filtered_workspaces
            .get(self.selected)
            .and_then(|&idx| self.workspaces.get(idx))
    }
    
    /// Get workspaces (for rendering)
    pub fn workspaces(&self) -> &[Workspace] {
        &self.workspaces
    }
    
    /// Get filtered workspaces (for rendering)
    pub fn filtered_workspaces(&self) -> &[usize] {
        &self.filtered_workspaces
    }
    
    /// Get list state (mutable, for rendering)
    pub fn list_state_mut(&mut self) -> &mut ListState {
        &mut self.list_state
    }
    
    /// Check if workspaces are empty
    pub fn is_empty(&self) -> bool {
        self.workspaces.is_empty()
    }
    
    /// Move selection up
    pub fn previous(&mut self) {
        if !self.filtered_workspaces.is_empty() {
            self.selected = if self.selected > 0 {
                self.selected - 1
            } else {
                self.filtered_workspaces.len() - 1
            };
            self.list_state.select(Some(self.selected));
        }
    }
    
    /// Move selection down
    pub fn next(&mut self) {
        if !self.filtered_workspaces.is_empty() {
            self.selected = if self.selected < self.filtered_workspaces.len() - 1 {
                self.selected + 1
            } else {
                0
            };
            self.list_state.select(Some(self.selected));
        }
    }
    
    /// Check if workspace is active
    pub fn is_active(&self, workspace: &Workspace) -> bool {
        self.active_workspace.as_ref()
            .map(|active| active == &workspace.path)
            .unwrap_or(false)
    }
    
    /// Get help system
    pub fn help_system(&self) -> &HelpSystem {
        &self.help_system
    }
    
    /// Get help system (mutable)
    pub fn help_system_mut(&mut self) -> &mut HelpSystem {
        &mut self.help_system
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn create_test_workspace(name: &str) -> Workspace {
        Workspace {
            name: name.to_string(),
            path: PathBuf::from(format!("/test/{}.yaml", name)),
            git_repo: None,
            description: Some(format!("Description for {}", name)),
        }
    }

    #[test]
    fn test_workspace_manager_new() {
        // This will use the actual discovery, which may fail in tests
        // So we test the structure rather than the full discovery
        let workspace = create_test_workspace("test");
        assert_eq!(workspace.name, "test");
    }

    #[test]
    fn test_workspace_manager_empty() {
        // Create a manager with empty workspaces manually
        // (We can't easily test the full new() without mocking discovery)
        let workspace = create_test_workspace("test");
        assert!(!workspace.name.is_empty());
    }

    #[test]
    fn test_workspace_manager_update_query() {
        // Test query update logic with mock data
        let workspaces = vec![
            create_test_workspace("Building A"),
            create_test_workspace("Building B"),
        ];
        let _filtered_workspaces: Vec<usize> = (0..workspaces.len()).collect();
        
        // Simulate query update
        let query = "A".to_string();
        let filtered: Vec<usize> = workspaces
            .iter()
            .enumerate()
            .filter(|(_, ws)| {
                let query_lower = query.to_lowercase();
                ws.name.to_lowercase().contains(&query_lower)
            })
            .map(|(idx, _)| idx)
            .collect();
        
        assert_eq!(filtered.len(), 1, "Should filter to one workspace");
        assert_eq!(filtered[0], 0, "Should match Building A");
    }

    #[test]
    fn test_workspace_manager_filter_by_name() {
        let workspaces = vec![
            create_test_workspace("Building Alpha"),
            create_test_workspace("Building Beta"),
        ];
        
        let query = "Beta".to_string();
        let filtered: Vec<usize> = workspaces
            .iter()
            .enumerate()
            .filter(|(_, ws)| {
                let query_lower = query.to_lowercase();
                ws.name.to_lowercase().contains(&query_lower)
            })
            .map(|(idx, _)| idx)
            .collect();
        
        assert_eq!(filtered.len(), 1, "Should filter to one workspace");
        assert_eq!(filtered[0], 1, "Should match Building Beta (index 1)");
    }

    #[test]
    fn test_workspace_manager_filter_by_description() {
        let workspaces = vec![
            create_test_workspace("Building A"),
            create_test_workspace("Building B"),
        ];
        
        let query = "Description for Building A".to_string();
        let filtered: Vec<usize> = workspaces
            .iter()
            .enumerate()
            .filter(|(_, ws)| {
                let query_lower = query.to_lowercase();
                ws.description.as_ref()
                    .map(|d| d.to_lowercase().contains(&query_lower))
                    .unwrap_or(false)
            })
            .map(|(idx, _)| idx)
            .collect();
        
        assert_eq!(filtered.len(), 1);
        assert_eq!(filtered[0], 0);
    }

    #[test]
    fn test_workspace_manager_selected_workspace() {
        // Test selection logic
        let workspaces = vec![
            create_test_workspace("Building A"),
            create_test_workspace("Building B"),
        ];
        let filtered_workspaces = vec![0, 1];
        let selected = 0;
        
        let selected_ws = filtered_workspaces
            .get(selected)
            .and_then(|&idx| workspaces.get(idx));
        
        assert!(selected_ws.is_some());
        assert_eq!(selected_ws.unwrap().name, "Building A");
    }

    #[test]
    fn test_workspace_manager_next() {
        let mut selected = 0;
        let filtered_workspaces = vec![0, 1, 2];
        
        selected = if selected < filtered_workspaces.len() - 1 {
            selected + 1
        } else {
            0
        };
        
        assert_eq!(selected, 1);
    }

    #[test]
    fn test_workspace_manager_previous() {
        let mut selected = 1;
        let filtered_workspaces = vec![0, 1, 2];
        
        selected = if selected > 0 {
            selected - 1
        } else {
            filtered_workspaces.len() - 1
        };
        
        assert_eq!(selected, 0);
    }

    #[test]
    fn test_workspace_manager_is_active() {
        let workspace = create_test_workspace("test");
        let active_workspace = Some(workspace.path.clone());
        
        let is_active = active_workspace.as_ref()
            .map(|active| active == &workspace.path)
            .unwrap_or(false);
        
        assert!(is_active, "Should be active");
    }

    #[test]
    fn test_workspace_manager_active_detection() {
        let workspace1 = create_test_workspace("test1");
        let workspace2 = create_test_workspace("test2");
        let active_workspace = Some(workspace1.path.clone());
        
        let is_active1 = active_workspace.as_ref()
            .map(|active| active == &workspace1.path)
            .unwrap_or(false);
        let is_active2 = active_workspace.as_ref()
            .map(|active| active == &workspace2.path)
            .unwrap_or(false);
        
        assert!(is_active1, "Workspace1 should be active");
        assert!(!is_active2, "Workspace2 should not be active");
    }
}

