use std::path::{Path, PathBuf};
use std::sync::mpsc::{channel, Receiver, Sender};
use std::time::Duration;

use anyhow::Result;
use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};

/// File watcher for YAML building data files
pub struct FileWatcher {
    watcher: RecommendedWatcher,
    receiver: Receiver<Result<Event, notify::Error>>,
}

impl FileWatcher {
    /// Create a new file watcher for the given repository root
    pub fn new(repo_root: &Path) -> Result<Self> {
        let (tx, rx) = channel();
        
        let mut watcher = RecommendedWatcher::new(
            move |res| {
                let _ = tx.send(res);
            },
            Config::default()
                .with_poll_interval(Duration::from_millis(500)),
        )?;

        // Watch for YAML files in the repository root (non-recursive)
        watcher.watch(repo_root, RecursiveMode::NonRecursive)?;

        Ok(Self {
            watcher,
            receiver: rx,
        })
    }

    /// Check for YAML file changes (non-blocking)
    /// Returns Some(path) if a YAML file was modified, None otherwise
    pub fn check_for_changes(&self) -> Option<PathBuf> {
        // Drain all pending events and check if any are YAML modifications
        let mut yaml_changed = None;

        while let Ok(event_result) = self.receiver.try_recv() {
            if let Ok(event) = event_result {
                if self.is_yaml_modification(&event) {
                    // Get the first modified YAML path
                    if let Some(path) = event.paths.first() {
                        yaml_changed = Some(path.clone());
                    }
                }
            }
        }

        yaml_changed
    }

    /// Check if an event represents a YAML file modification
    fn is_yaml_modification(&self, event: &Event) -> bool {
        // Only care about modify/create events
        let is_relevant_event = matches!(
            event.kind,
            EventKind::Modify(_) | EventKind::Create(_)
        );

        if !is_relevant_event {
            return false;
        }

        // Check if any path is a YAML file
        event.paths.iter().any(|path| {
            path.extension()
                .and_then(|ext| ext.to_str())
                .map(|ext| ext.eq_ignore_ascii_case("yaml") || ext.eq_ignore_ascii_case("yml"))
                .unwrap_or(false)
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn detects_yaml_changes() {
        let temp = TempDir::new().unwrap();
        let repo_root = temp.path();
        
        let watcher = FileWatcher::new(repo_root).unwrap();

        // Create a YAML file
        let yaml_path = repo_root.join("building.yaml");
        fs::write(&yaml_path, "name: Test Building").unwrap();

        // Give the watcher time to detect the change
        std::thread::sleep(Duration::from_millis(600));

        // Check for changes
        let changed = watcher.check_for_changes();
        assert!(changed.is_some());
        assert_eq!(changed.unwrap(), yaml_path);
    }

    #[test]
    fn ignores_non_yaml_files() {
        let temp = TempDir::new().unwrap();
        let repo_root = temp.path();
        
        let watcher = FileWatcher::new(repo_root).unwrap();

        // Create a non-YAML file
        fs::write(repo_root.join("README.md"), "# Test").unwrap();

        // Give the watcher time
        std::thread::sleep(Duration::from_millis(600));

        // Should not detect changes
        let changed = watcher.check_for_changes();
        assert!(changed.is_none());
    }
}
