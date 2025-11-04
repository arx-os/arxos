//! Command Palette State Management
//!
//! Handles the state and logic for the command palette.

use super::{types::CommandEntry, commands::load_commands};
use crate::ui::{HelpSystem, HelpContext};
use ratatui::widgets::ListState;

/// Command palette state
pub struct CommandPalette {
    /// All available commands
    commands: Vec<CommandEntry>,
    /// Filtered commands based on search
    filtered_commands: Vec<usize>,
    /// Search query
    query: String,
    /// Selected command index
    selected: usize,
    /// List state for rendering
    list_state: ListState,
    /// Help system
    help_system: HelpSystem,
}

impl CommandPalette {
    /// Create a new command palette with all available commands
    pub fn new() -> Self {
        let commands = load_commands();
        let filtered_commands: Vec<usize> = (0..commands.len()).collect();
        
        let mut list_state = ListState::default();
        list_state.select(Some(0));
        
        Self {
            commands,
            filtered_commands,
            query: String::new(),
            selected: 0,
            list_state,
            help_system: HelpSystem::new(HelpContext::CommandPalette),
        }
    }
    
    /// Update search query and filter commands
    pub fn update_query(&mut self, query: String) {
        self.query = query.clone();
        
        if query.is_empty() {
            self.filtered_commands = (0..self.commands.len()).collect();
        } else {
            self.filtered_commands = self.commands
                .iter()
                .enumerate()
                .filter(|(_, cmd)| {
                    // Simple fuzzy matching
                    let query_lower = query.to_lowercase();
                    cmd.name.to_lowercase().contains(&query_lower) ||
                    cmd.description.to_lowercase().contains(&query_lower) ||
                    cmd.full_command.to_lowercase().contains(&query_lower)
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
    
    /// Get selected command
    pub fn selected_command(&self) -> Option<&CommandEntry> {
        self.filtered_commands
            .get(self.selected)
            .and_then(|&idx| self.commands.get(idx))
    }
    
    /// Get filtered commands (for rendering)
    pub fn filtered_commands(&self) -> &[usize] {
        &self.filtered_commands
    }
    
    /// Get all commands (for rendering)
    pub fn commands(&self) -> &[CommandEntry] {
        &self.commands
    }
    
    /// Get list state (mutable, for rendering)
    pub fn list_state_mut(&mut self) -> &mut ListState {
        &mut self.list_state
    }
    
    /// Move selection up
    pub fn previous(&mut self) {
        if !self.filtered_commands.is_empty() {
            self.selected = if self.selected > 0 {
                self.selected - 1
            } else {
                self.filtered_commands.len() - 1
            };
            self.list_state.select(Some(self.selected));
        }
    }
    
    /// Move selection down
    pub fn next(&mut self) {
        if !self.filtered_commands.is_empty() {
            self.selected = if self.selected < self.filtered_commands.len() - 1 {
                self.selected + 1
            } else {
                0
            };
            self.list_state.select(Some(self.selected));
        }
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

