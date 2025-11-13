//! IFC Sync State Tracking
//!
//! Tracks the last export state to enable delta calculation and incremental exports.

use chrono::{DateTime, Utc};
use log::{info, warn};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

/// Sync state tracking last export information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IFCSyncState {
    /// Timestamp of last successful export
    pub last_export_timestamp: DateTime<Utc>,
    /// Universal Paths of equipment exported in last sync
    pub exported_equipment_paths: HashSet<String>,
    /// Universal Paths of rooms exported in last sync
    pub exported_rooms_paths: HashSet<String>,
    /// Path to the IFC file that was exported
    pub ifc_file_path: PathBuf,
}

impl IFCSyncState {
    /// Create a new empty sync state
    pub fn new(ifc_file_path: PathBuf) -> Self {
        Self {
            last_export_timestamp: DateTime::UNIX_EPOCH,
            exported_equipment_paths: HashSet::new(),
            exported_rooms_paths: HashSet::new(),
            ifc_file_path,
        }
    }

    /// Load sync state from file
    ///
    /// # Arguments
    /// * `path` - Path to sync state JSON file (typically `.arxos/ifc-sync-state.json`)
    ///
    /// # Returns
    /// * Option<IFCSyncState> - Returns None if file doesn't exist or can't be read
    pub fn load(path: &Path) -> Option<Self> {
        if !path.exists() {
            warn!("Sync state file not found: {}", path.display());
            return None;
        }

        match fs::read_to_string(path) {
            Ok(content) => match serde_json::from_str::<IFCSyncState>(&content) {
                Ok(state) => {
                    info!("Loaded sync state from: {}", path.display());
                    Some(state)
                }
                Err(e) => {
                    warn!("Failed to parse sync state file {}: {}", path.display(), e);
                    None
                }
            },
            Err(e) => {
                warn!("Failed to read sync state file {}: {}", path.display(), e);
                None
            }
        }
    }

    /// Save sync state to file
    ///
    /// # Arguments
    /// * `path` - Path to save sync state JSON file
    ///
    /// # Returns
    /// * Result indicating success or failure
    pub fn save(&self, path: &Path) -> Result<(), Box<dyn std::error::Error>> {
        // Create parent directory if it doesn't exist
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let json = serde_json::to_string_pretty(self)?;
        fs::write(path, json)?;

        info!("Saved sync state to: {}", path.display());
        Ok(())
    }

    /// Update sync state after successful export
    ///
    /// # Arguments
    /// * `equipment_paths` - Universal Paths of exported equipment
    /// * `rooms_paths` - Universal Paths of exported rooms
    pub fn update_after_export(
        &mut self,
        equipment_paths: HashSet<String>,
        rooms_paths: HashSet<String>,
    ) {
        self.last_export_timestamp = Utc::now();
        self.exported_equipment_paths = equipment_paths;
        self.exported_rooms_paths = rooms_paths;
        info!(
            "Updated sync state: {} equipment, {} rooms",
            self.exported_equipment_paths.len(),
            self.exported_rooms_paths.len()
        );
    }

    /// Get default sync state file path (`.arxos/ifc-sync-state.json`)
    pub fn default_path() -> PathBuf {
        PathBuf::from(".arxos").join("ifc-sync-state.json")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_sync_state_save_and_load() {
        let temp_dir = TempDir::new().unwrap();
        let state_path = temp_dir.path().join("test-sync-state.json");

        let mut state = IFCSyncState::new(PathBuf::from("test.ifc"));
        state
            .exported_equipment_paths
            .insert("building/floor-1/equipment-1".to_string());
        state
            .exported_rooms_paths
            .insert("building/floor-1/room-101".to_string());

        // Save
        state.save(&state_path).unwrap();
        assert!(state_path.exists());

        // Load
        let loaded = IFCSyncState::load(&state_path).unwrap();
        assert_eq!(loaded.exported_equipment_paths.len(), 1);
        assert_eq!(loaded.exported_rooms_paths.len(), 1);
        assert!(loaded
            .exported_equipment_paths
            .contains("building/floor-1/equipment-1"));
    }

    #[test]
    fn test_sync_state_update_after_export() {
        let mut state = IFCSyncState::new(PathBuf::from("test.ifc"));

        let equipment_paths: HashSet<String> = [
            "building/floor-1/equipment-1".to_string(),
            "building/floor-1/equipment-2".to_string(),
        ]
        .into_iter()
        .collect();

        let rooms_paths: HashSet<String> = ["building/floor-1/room-101".to_string()]
            .into_iter()
            .collect();

        state.update_after_export(equipment_paths.clone(), rooms_paths.clone());

        assert_eq!(state.exported_equipment_paths.len(), 2);
        assert_eq!(state.exported_rooms_paths.len(), 1);
    }

    #[test]
    fn test_sync_state_load_nonexistent_file() {
        let temp_dir = TempDir::new().unwrap();
        let nonexistent_path = temp_dir.path().join("nonexistent.json");

        let loaded = IFCSyncState::load(&nonexistent_path);
        assert!(loaded.is_none());
    }

    #[test]
    fn test_sync_state_load_invalid_json() {
        let temp_dir = TempDir::new().unwrap();
        let invalid_path = temp_dir.path().join("invalid.json");

        // Write invalid JSON
        fs::write(&invalid_path, "{ invalid json }").unwrap();

        let loaded = IFCSyncState::load(&invalid_path);
        assert!(loaded.is_none());
    }

    #[test]
    fn test_sync_state_timestamp_updates() {
        let temp_dir = TempDir::new().unwrap();
        let _state_path = temp_dir.path().join("test-sync-state.json");

        let mut state = IFCSyncState::new(PathBuf::from("test.ifc"));
        let initial_timestamp = state.last_export_timestamp;

        // Wait a tiny bit to ensure timestamp changes
        std::thread::sleep(std::time::Duration::from_millis(10));

        state.update_after_export(HashSet::new(), HashSet::new());
        assert!(state.last_export_timestamp > initial_timestamp);
    }

    #[test]
    fn test_sync_state_default_path() {
        let path = IFCSyncState::default_path();
        assert_eq!(path, PathBuf::from(".arxos").join("ifc-sync-state.json"));
    }

    #[test]
    fn test_sync_state_new_has_empty_sets() {
        let state = IFCSyncState::new(PathBuf::from("test.ifc"));
        assert_eq!(state.exported_equipment_paths.len(), 0);
        assert_eq!(state.exported_rooms_paths.len(), 0);
        assert_eq!(state.last_export_timestamp, chrono::DateTime::UNIX_EPOCH);
    }
}
