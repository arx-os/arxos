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

