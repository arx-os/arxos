//! Persistent counter management for auto-generated fixture IDs
//!
//! Stores counters per room/type combination in .arxos/counters.toml
//! to ensure IDs survive restarts and work across concurrent users.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

/// Counter storage for fixture ID generation
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CounterStorage {
    /// Map of (room, type) -> next counter value
    #[serde(default)]
    pub counters: HashMap<String, u32>,
}

impl CounterStorage {
    /// Load counters from .arxos/counters.toml
    pub fn load() -> Result<Self> {
        let counters_path = Self::counters_path()?;

        if !counters_path.exists() {
            return Ok(Self::default());
        }

        let content = fs::read_to_string(&counters_path).with_context(|| {
            format!("Failed to read counters file: {}", counters_path.display())
        })?;

        let storage: CounterStorage = toml::from_str(&content).with_context(|| {
            format!("Failed to parse counters file: {}", counters_path.display())
        })?;

        Ok(storage)
    }

    /// Save counters to .arxos/counters.toml
    pub fn save(&self) -> Result<()> {
        let counters_path = Self::counters_path()?;

        // Ensure .arxos directory exists
        if let Some(parent) = counters_path.parent() {
            fs::create_dir_all(parent).with_context(|| {
                format!("Failed to create .arxos directory: {}", parent.display())
            })?;
        }

        let content =
            toml::to_string_pretty(self).context("Failed to serialize counters to TOML")?;

        fs::write(&counters_path, content).with_context(|| {
            format!("Failed to write counters file: {}", counters_path.display())
        })?;

        Ok(())
    }

    /// Get next ID for a room/type combination and increment
    pub fn next_id(&mut self, room: &str, typ: &str) -> Result<u32> {
        let key = format!("{}:{}", room, typ);
        let id = self.counters.entry(key).or_insert(0);
        *id += 1;
        Ok(*id)
    }

    /// Get next ID without incrementing (peek)
    pub fn peek_id(&self, room: &str, typ: &str) -> u32 {
        let key = format!("{}:{}", room, typ);
        self.counters.get(&key).copied().unwrap_or(0) + 1
    }

    /// Get path to counters file
    fn counters_path() -> Result<PathBuf> {
        let current_dir = std::env::current_dir().context("Failed to get current directory")?;
        Ok(current_dir.join(".arxos").join("counters.toml"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_counter_storage() {
        let temp_dir = TempDir::new().unwrap();
        std::env::set_current_dir(temp_dir.path()).unwrap();

        // Create .arxos directory
        fs::create_dir_all(".arxos").unwrap();

        let mut storage = CounterStorage::default();

        // Test incrementing
        assert_eq!(storage.next_id("mech", "boiler").unwrap(), 1);
        assert_eq!(storage.next_id("mech", "boiler").unwrap(), 2);
        assert_eq!(storage.next_id("kitchen", "fridge").unwrap(), 1);

        // Test peek
        assert_eq!(storage.peek_id("mech", "boiler"), 3);
        assert_eq!(storage.peek_id("kitchen", "fridge"), 2);

        // Save and reload
        storage.save().unwrap();
        let loaded = CounterStorage::load().unwrap();

        assert_eq!(loaded.peek_id("mech", "boiler"), 3);
        assert_eq!(loaded.peek_id("kitchen", "fridge"), 2);
    }
}
