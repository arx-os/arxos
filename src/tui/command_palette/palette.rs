//! Command Palette State Management
//!
//! Handles the state and logic for the command palette.

use super::{commands::load_commands, types::CommandEntry};
use crate::tui::{HelpContext, HelpSystem};
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
            self.filtered_commands = self
                .commands
                .iter()
                .enumerate()
                .filter(|(_, cmd)| {
                    // Simple fuzzy matching
                    let query_lower = query.to_lowercase();
                    cmd.name.to_lowercase().contains(&query_lower)
                        || cmd.description.to_lowercase().contains(&query_lower)
                        || cmd.full_command.to_lowercase().contains(&query_lower)
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

impl Default for CommandPalette {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_palette_new() {
        let palette = CommandPalette::new();
        assert!(!palette.commands().is_empty(), "Should have commands");
        assert_eq!(palette.query(), "", "Initial query should be empty");
        assert_eq!(palette.selected, 0, "Initial selection should be 0");
    }

    #[test]
    fn test_palette_initial_state() {
        let palette = CommandPalette::new();
        assert!(palette.query().is_empty(), "Initial query should be empty");
        assert!(
            palette.selected_command().is_some(),
            "Should have selected command"
        );
        assert_eq!(
            palette.filtered_commands().len(),
            palette.commands().len(),
            "All commands should be shown initially"
        );
    }

    #[test]
    fn test_palette_update_query() {
        let mut palette = CommandPalette::new();
        palette.update_query("equipment".to_string());
        assert_eq!(palette.query(), "equipment", "Query should be updated");
        assert_eq!(palette.selected, 0, "Selection should reset to 0");
    }

    #[test]
    fn test_palette_filter_commands() {
        let mut palette = CommandPalette::new();
        let initial_count = palette.filtered_commands().len();

        palette.update_query("equipment".to_string());
        let filtered_count = palette.filtered_commands().len();

        assert!(
            filtered_count <= initial_count,
            "Filtered should be <= total"
        );
        assert!(
            filtered_count > 0,
            "Should have filtered results for 'equipment'"
        );
    }

    #[test]
    fn test_palette_filter_fuzzy_matching() {
        let mut palette = CommandPalette::new();
        palette.update_query("equ".to_string());
        let filtered = palette.filtered_commands();
        assert!(!filtered.is_empty(), "Should find 'equipment' with 'equ'");
    }

    #[test]
    fn test_palette_filter_by_name() {
        let mut palette = CommandPalette::new();
        palette.update_query("init".to_string());
        let filtered = palette.filtered_commands();
        assert!(!filtered.is_empty(), "Should find command by name");

        // Check that the filtered command contains "init"
        let commands = palette.commands();
        let found = filtered
            .iter()
            .any(|&idx| commands[idx].name.contains("init"));
        assert!(found, "Should find 'init' command");
    }

    #[test]
    fn test_palette_filter_by_description() {
        let mut palette = CommandPalette::new();
        palette.update_query("interactive".to_string());
        let filtered = palette.filtered_commands();
        // Should find commands that have "interactive" in description
        assert!(
            !filtered.is_empty()
                || palette
                    .commands()
                    .iter()
                    .any(|c| c.description.contains("interactive")),
            "Should find by description"
        );
    }

    #[test]
    fn test_palette_filter_by_full_command() {
        let mut palette = CommandPalette::new();
        palette.update_query("arxos".to_string());
        let filtered = palette.filtered_commands();
        assert!(!filtered.is_empty(), "Should find commands by full_command");
    }

    #[test]
    fn test_palette_empty_query_shows_all() {
        let mut palette = CommandPalette::new();
        let initial_count = palette.filtered_commands().len();

        palette.update_query("test".to_string());
        let filtered_count = palette.filtered_commands().len();

        palette.update_query("".to_string());
        let all_count = palette.filtered_commands().len();

        assert_eq!(all_count, initial_count, "Empty query should show all");
        assert!(all_count >= filtered_count, "All should be >= filtered");
    }

    #[test]
    fn test_palette_selected_command() {
        let palette = CommandPalette::new();
        let selected = palette.selected_command();
        assert!(selected.is_some(), "Should have a selected command");
        assert_eq!(
            selected.unwrap().name,
            palette.commands()[0].name,
            "First command should be selected"
        );
    }

    #[test]
    fn test_palette_next() {
        let mut palette = CommandPalette::new();
        let initial_selected = palette.selected;
        palette.next();
        assert_eq!(palette.selected, 1, "Should move to next command");
        assert_ne!(
            palette.selected, initial_selected,
            "Selection should change"
        );
    }

    #[test]
    fn test_palette_previous() {
        let mut palette = CommandPalette::new();
        palette.next(); // Move to index 1
        let current = palette.selected;
        palette.previous();
        assert_eq!(palette.selected, 0, "Should move to previous command");
        assert_ne!(palette.selected, current, "Selection should change");
    }

    #[test]
    fn test_palette_wraps_selection() {
        let mut palette = CommandPalette::new();
        let total = palette.filtered_commands().len();
        assert!(total > 0, "Should have commands");

        // Move to end (total - 1 moves from 0 to total-1)
        for _ in 0..(total - 1) {
            palette.next();
        }
        assert_eq!(palette.selected, total - 1, "Should be at end");

        // Should wrap to beginning
        palette.next();
        assert_eq!(palette.selected, 0, "Should wrap to beginning");

        // Move to beginning and go previous
        palette.previous();
        assert_eq!(palette.selected, total - 1, "Should wrap to end");
    }

    #[test]
    fn test_palette_reset_selection_on_filter() {
        let mut palette = CommandPalette::new();
        palette.next();
        palette.next();
        assert!(palette.selected > 0, "Should have moved selection");

        palette.update_query("test".to_string());
        assert_eq!(palette.selected, 0, "Selection should reset to 0 on filter");
    }
}
