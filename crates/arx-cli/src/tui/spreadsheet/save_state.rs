//! Save state management for spreadsheet
//!
//! Handles save status, auto-save debouncing, and save operations

use std::time::{Duration, Instant};

/// Save state
#[derive(Debug, Clone, PartialEq)]
pub enum SaveState {
    Clean,
    Modified,
    Saving,
    Saved,
    Error(String),
}

/// Auto-save manager with debouncing
pub struct AutoSaveManager {
    debounce_timer: Option<Instant>,
    debounce_duration: Duration,
    save_state: SaveState,
}

impl AutoSaveManager {
    /// Create a new auto-save manager
    pub fn new(debounce_ms: u64) -> Self {
        Self {
            debounce_timer: None,
            debounce_duration: Duration::from_millis(debounce_ms),
            save_state: SaveState::Clean,
        }
    }

    /// Trigger a save (starts debounce timer)
    pub fn trigger_save(&mut self) {
        self.save_state = SaveState::Modified;
        self.debounce_timer = Some(Instant::now());
    }

    /// Check if save should be performed (debounce elapsed)
    pub fn should_save(&self) -> bool {
        if let Some(timer) = self.debounce_timer {
            timer.elapsed() >= self.debounce_duration
        } else {
            false
        }
    }

    /// Mark as saving
    pub fn set_saving(&mut self) {
        self.save_state = SaveState::Saving;
        self.debounce_timer = None;
    }

    /// Mark as saved
    pub fn set_saved(&mut self) {
        self.save_state = SaveState::Saved;
        self.debounce_timer = None;
    }

    /// Mark as clean (no changes)
    pub fn set_clean(&mut self) {
        self.save_state = SaveState::Clean;
        self.debounce_timer = None;
    }

    /// Mark save error
    pub fn set_error(&mut self, error: String) {
        self.save_state = SaveState::Error(error);
        self.debounce_timer = None;
    }

    /// Get current save state
    pub fn state(&self) -> &SaveState {
        &self.save_state
    }

    /// Check if there are unsaved changes
    pub fn has_unsaved_changes(&self) -> bool {
        matches!(self.save_state, SaveState::Modified)
    }

    /// Get save status message for display
    pub fn status_message(&self) -> String {
        match &self.save_state {
            SaveState::Clean => "Clean".to_string(),
            SaveState::Modified => "Modified".to_string(),
            SaveState::Saving => "Saving...".to_string(),
            SaveState::Saved => "Saved".to_string(),
            SaveState::Error(msg) => format!("Error: {}", msg),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_auto_save_trigger() {
        let mut manager = AutoSaveManager::new(100);

        manager.trigger_save();

        assert_eq!(manager.state(), &SaveState::Modified);
        assert!(manager.debounce_timer.is_some());
    }

    #[test]
    fn test_auto_save_debounce() {
        let mut manager = AutoSaveManager::new(50);

        manager.trigger_save();

        // Should not save immediately
        assert!(!manager.should_save());

        // Wait for debounce
        thread::sleep(Duration::from_millis(60));

        // Should be ready to save
        assert!(manager.should_save());
    }

    #[test]
    fn test_auto_save_should_save() {
        let mut manager = AutoSaveManager::new(100);

        // Initially should not save
        assert!(!manager.should_save());

        manager.trigger_save();

        // Immediately should not save
        assert!(!manager.should_save());
    }

    #[test]
    fn test_auto_save_state_transitions() {
        let mut manager = AutoSaveManager::new(100);

        assert_eq!(manager.state(), &SaveState::Clean);

        manager.trigger_save();
        assert_eq!(manager.state(), &SaveState::Modified);

        manager.set_saving();
        assert_eq!(manager.state(), &SaveState::Saving);

        manager.set_saved();
        assert_eq!(manager.state(), &SaveState::Saved);

        manager.set_clean();
        assert_eq!(manager.state(), &SaveState::Clean);
    }

    #[test]
    fn test_auto_save_error_handling() {
        let mut manager = AutoSaveManager::new(100);

        manager.set_error("Test error".to_string());

        assert_eq!(manager.state(), &SaveState::Error("Test error".to_string()));
        assert!(!manager.has_unsaved_changes());
    }

    #[test]
    fn test_auto_save_has_unsaved_changes() {
        let mut manager = AutoSaveManager::new(100);

        assert!(!manager.has_unsaved_changes());

        manager.trigger_save();
        assert!(manager.has_unsaved_changes());

        manager.set_saved();
        assert!(!manager.has_unsaved_changes());
    }

    #[test]
    fn test_status_message() {
        let mut manager = AutoSaveManager::new(100);

        assert_eq!(manager.status_message(), "Clean");

        manager.trigger_save();
        assert_eq!(manager.status_message(), "Modified");

        manager.set_saving();
        assert_eq!(manager.status_message(), "Saving...");

        manager.set_saved();
        assert_eq!(manager.status_message(), "Saved");

        manager.set_error("Test".to_string());
        assert!(manager.status_message().contains("Error"));
    }
}
