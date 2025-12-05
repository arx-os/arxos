//! Sensor data storage layer
//! 
//! Provides Git-backed storage for sensor readings with optional audit logging.
//! Supports both real-time queries (no Git) and historical queries (from Git).

use anyhow::Result;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

/// Sensor snapshot stored in Git
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorSnapshot {
    pub timestamp: DateTime<Utc>,
    pub source: String,
    pub user: Option<String>,
    pub readings: HashMap<String, SensorValue>,
}

/// Individual sensor value
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorValue {
    pub value: f64,
    pub unit: String,
    pub quality: String,
}

/// Storage configuration
#[derive(Debug, Clone)]
pub struct StorageConfig {
    pub sensors_dir: PathBuf,
    pub retention_days: u32,
    pub auto_commit: bool,
}

impl Default for StorageConfig {
    fn default() -> Self {
        Self {
            sensors_dir: PathBuf::from("sensors"),
            retention_days: 30,
            auto_commit: false,
        }
    }
}

/// Sensor storage manager
pub struct SensorStorage {
    config: StorageConfig,
    repo_root: PathBuf,
}

impl SensorStorage {
    pub fn new(repo_root: PathBuf, config: StorageConfig) -> Self {
        Self { config, repo_root }
    }

    /// Write a sensor snapshot to disk (optionally commit to Git)
    pub fn write_snapshot(&self, snapshot: &SensorSnapshot, commit: bool) -> Result<PathBuf> {
        // Create sensors directory if it doesn't exist
        let sensors_path = self.repo_root.join(&self.config.sensors_dir);
        fs::create_dir_all(&sensors_path)?;

        // Generate filename: sensors/YYYY-MM-DD-HH-MM.yaml
        let filename = format!(
            "{}.yaml",
            snapshot.timestamp.format("%Y-%m-%d-%H-%M")
        );
        let file_path = sensors_path.join(&filename);

        // Serialize to YAML
        let yaml = serde_yaml::to_string(snapshot)?;
        fs::write(&file_path, yaml)?;

        // Optionally commit to Git
        if commit && self.config.auto_commit {
            self.commit_snapshot(&file_path, snapshot)?;
        }

        Ok(file_path)
    }

    /// Read sensor snapshots from a time range
    pub fn read_snapshots(
        &self,
        from: DateTime<Utc>,
        to: DateTime<Utc>,
    ) -> Result<Vec<SensorSnapshot>> {
        let sensors_path = self.repo_root.join(&self.config.sensors_dir);
        
        if !sensors_path.exists() {
            return Ok(Vec::new());
        }

        let mut snapshots = Vec::new();

        for entry in fs::read_dir(&sensors_path)? {
            let entry = entry?;
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("yaml") {
                let content = fs::read_to_string(&path)?;
                if let Ok(snapshot) = serde_yaml::from_str::<SensorSnapshot>(&content) {
                    if snapshot.timestamp >= from && snapshot.timestamp <= to {
                        snapshots.push(snapshot);
                    }
                }
            }
        }

        // Sort by timestamp
        snapshots.sort_by_key(|s| s.timestamp);

        Ok(snapshots)
    }

    /// Read the latest sensor snapshot
    pub fn read_latest(&self) -> Result<Option<SensorSnapshot>> {
        let sensors_path = self.repo_root.join(&self.config.sensors_dir);
        
        if !sensors_path.exists() {
            return Ok(None);
        }

        let mut latest: Option<(DateTime<Utc>, PathBuf)> = None;

        for entry in fs::read_dir(&sensors_path)? {
            let entry = entry?;
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("yaml") {
                let content = fs::read_to_string(&path)?;
                if let Ok(snapshot) = serde_yaml::from_str::<SensorSnapshot>(&content) {
                    if latest.is_none() || snapshot.timestamp > latest.as_ref().unwrap().0 {
                        latest = Some((snapshot.timestamp, path));
                    }
                }
            }
        }

        if let Some((_, path)) = latest {
            let content = fs::read_to_string(&path)?;
            let snapshot = serde_yaml::from_str(&content)?;
            Ok(Some(snapshot))
        } else {
            Ok(None)
        }
    }

    /// Clean up old sensor files beyond retention period
    pub fn cleanup_old_files(&self) -> Result<usize> {
        let sensors_path = self.repo_root.join(&self.config.sensors_dir);
        
        if !sensors_path.exists() {
            return Ok(0);
        }

        let cutoff = Utc::now() - chrono::Duration::days(self.config.retention_days as i64);
        let mut removed = 0;

        for entry in fs::read_dir(&sensors_path)? {
            let entry = entry?;
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("yaml") {
                let content = fs::read_to_string(&path)?;
                if let Ok(snapshot) = serde_yaml::from_str::<SensorSnapshot>(&content) {
                    if snapshot.timestamp < cutoff {
                        fs::remove_file(&path)?;
                        removed += 1;
                    }
                }
            }
        }

        Ok(removed)
    }

    /// Commit a sensor snapshot to Git
    fn commit_snapshot(&self, file_path: &Path, snapshot: &SensorSnapshot) -> Result<()> {
        use crate::git::manager::{BuildingGitManager, GitConfigManager};

        let config = GitConfigManager::load_from_arx_config_or_env();
        let repo_str = self.repo_root.to_str()
            .ok_or_else(|| anyhow::anyhow!("Invalid repo path"))?;
        
        let mut manager = BuildingGitManager::new(repo_str, "current", config)?;

        // Stage the file
        let relative_path = file_path.strip_prefix(&self.repo_root)?;
        manager.stage_file(relative_path.to_str().unwrap())?;

        // Commit with descriptive message
        let message = format!(
            "Sensor snapshot: {} ({})",
            snapshot.timestamp.format("%Y-%m-%d %H:%M:%S"),
            snapshot.source
        );
        
        if let Some(user) = &snapshot.user {
            manager.commit(&format!("{} by {}", message, user))?;
        } else {
            manager.commit(&message)?;
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_write_and_read_snapshot() {
        let temp = TempDir::new().unwrap();
        let storage = SensorStorage::new(
            temp.path().to_path_buf(),
            StorageConfig::default(),
        );

        let mut readings = HashMap::new();
        readings.insert(
            "floor:2:room:201:temp".to_string(),
            SensorValue {
                value: 72.5,
                unit: "°F".to_string(),
                quality: "good".to_string(),
            },
        );

        let snapshot = SensorSnapshot {
            timestamp: Utc::now(),
            source: "test".to_string(),
            user: Some("test_user".to_string()),
            readings,
        };

        // Write snapshot
        let path = storage.write_snapshot(&snapshot, false).unwrap();
        assert!(path.exists());

        // Read latest
        let latest = storage.read_latest().unwrap();
        assert!(latest.is_some());
        assert_eq!(latest.unwrap().source, "test");
    }

    #[test]
    fn test_cleanup_old_files() {
        let temp = TempDir::new().unwrap();
        let mut config = StorageConfig::default();
        config.retention_days = 0; // Immediate cleanup
        
        let storage = SensorStorage::new(temp.path().to_path_buf(), config);

        let snapshot = SensorSnapshot {
            timestamp: Utc::now() - chrono::Duration::days(1),
            source: "test".to_string(),
            user: None,
            readings: HashMap::new(),
        };

        storage.write_snapshot(&snapshot, false).unwrap();
        
        // Cleanup should remove the old file
        let removed = storage.cleanup_old_files().unwrap();
        assert_eq!(removed, 1);
    }
}
