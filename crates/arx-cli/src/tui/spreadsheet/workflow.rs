//! Workflow integration for spreadsheet
//!
//! Handles file locking, conflict detection, and workflow awareness

use log::{info, warn};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime};

/// File lock for preventing concurrent edits
pub struct FileLock {
    lock_file: PathBuf,
    process_id: u32,
}

impl FileLock {
    /// Acquire a file lock for the given building file
    ///
    /// Returns an error if another process has the lock.
    /// Removes stale locks (from processes that no longer exist).
    pub fn acquire(building_file: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let lock_file = building_file.with_extension("yaml.lock");

        // Check if lock exists
        if lock_file.exists() {
            // Read process ID from lock file
            let pid_str = fs::read_to_string(&lock_file)
                .map_err(|e| format!("Failed to read lock file: {}", e))?;
            let pid: u32 = pid_str
                .trim()
                .parse()
                .map_err(|e| format!("Invalid process ID in lock file: {}", e))?;

            // Check if process is still running
            if is_process_running(pid) {
                return Err(format!(
                    "Building data is being edited by another process (PID: {}). \
                     Close the other spreadsheet session first.",
                    pid
                )
                .into());
            } else {
                // Stale lock - remove it
                warn!("Removing stale lock file from process {}", pid);
                fs::remove_file(&lock_file)?;
            }
        }

        // Create lock file with current process ID
        let pid = std::process::id();
        fs::write(&lock_file, pid.to_string())
            .map_err(|e| format!("Failed to create lock file: {}", e))?;

        info!("Acquired file lock: {:?} (PID: {})", lock_file, pid);

        Ok(Self {
            lock_file,
            process_id: pid,
        })
    }

    /// Release the file lock
    pub fn release(self) -> Result<(), Box<dyn std::error::Error>> {
        if self.lock_file.exists() {
            fs::remove_file(&self.lock_file)
                .map_err(|e| format!("Failed to remove lock file: {}", e))?;
            info!(
                "Released file lock: {:?} (PID: {})",
                self.lock_file, self.process_id
            );
        }
        Ok(())
    }

    /// Get the lock file path
    pub fn lock_file(&self) -> &Path {
        &self.lock_file
    }

    /// Get the process ID
    pub fn process_id(&self) -> u32 {
        self.process_id
    }
}

impl Drop for FileLock {
    fn drop(&mut self) {
        // Try to clean up lock file on drop
        if self.lock_file.exists() {
            let _ = fs::remove_file(&self.lock_file);
        }
    }
}

/// Check if a process is still running
///
/// Platform-specific implementation needed.
fn is_process_running(pid: u32) -> bool {
    #[cfg(unix)]
    {
        // On Unix, check if process exists by sending signal 0
        use std::process::Command;
        // Try to kill with signal 0 (doesn't actually kill, just checks existence)
        let output = Command::new("kill").args(["-0", &pid.to_string()]).output();
        matches!(output, Ok(ref o) if o.status.success())
    }

    #[cfg(windows)]
    {
        // On Windows, check if process exists
        use std::process::Command;
        let output = Command::new("tasklist")
            .args(&["/FI", &format!("PID eq {}", pid)])
            .output();
        match output {
            Ok(o) => {
                let output_str = String::from_utf8_lossy(&o.stdout);
                output_str.contains(&pid.to_string())
            }
            Err(_) => false,
        }
    }
}

/// Conflict detector for external file changes
pub struct ConflictDetector {
    initial_mtime: SystemTime,
    file_path: PathBuf,
}

impl ConflictDetector {
    /// Create a new conflict detector for a file
    pub fn new(file_path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let metadata =
            fs::metadata(file_path).map_err(|e| format!("Failed to read file metadata: {}", e))?;
        let initial_mtime = metadata
            .modified()
            .map_err(|e| format!("Failed to get file modification time: {}", e))?;

        Ok(Self {
            initial_mtime,
            file_path: file_path.to_path_buf(),
        })
    }

    /// Check if the file has been modified externally
    pub fn check_conflict(&self) -> Result<bool, Box<dyn std::error::Error>> {
        if !self.file_path.exists() {
            return Ok(false);
        }

        let metadata = fs::metadata(&self.file_path)
            .map_err(|e| format!("Failed to read file metadata: {}", e))?;
        let current_mtime = metadata
            .modified()
            .map_err(|e| format!("Failed to get file modification time: {}", e))?;

        Ok(current_mtime > self.initial_mtime)
    }

    /// Update the initial modification time (after reloading)
    pub fn update(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let metadata = fs::metadata(&self.file_path)
            .map_err(|e| format!("Failed to read file metadata: {}", e))?;
        self.initial_mtime = metadata
            .modified()
            .map_err(|e| format!("Failed to get file modification time: {}", e))?;
        Ok(())
    }
}

/// Check if a file lock exists
pub fn file_lock_exists(building_file: &Path) -> bool {
    let lock_file = building_file.with_extension("yaml.lock");
    lock_file.exists()
}

/// Workflow status for active workflows
#[derive(Debug, Clone, Default)]
pub struct WorkflowStatus {
    pub watch_mode_active: bool,
    pub sync_active: bool,
    pub sensors_active: bool,
}

impl WorkflowStatus {
    /// Check for active workflows
    pub fn detect() -> Self {
        // Check for watch mode lock file
        let watch_lock = std::path::Path::new(".watch.lock");
        let watch_mode_active = watch_lock.exists();

        // Check for sync lock file
        let sync_lock = std::path::Path::new(".sync.lock");
        let sync_active = sync_lock.exists();

        // Check for sensor processing (look for sensor data directory or lock)
        let sensor_lock = std::path::Path::new(".sensors.lock");
        let sensors_active = sensor_lock.exists();

        Self {
            watch_mode_active,
            sync_active,
            sensors_active,
        }
    }

    /// Check if any workflows are active
    pub fn has_active_workflows(&self) -> bool {
        self.watch_mode_active || self.sync_active || self.sensors_active
    }

    /// Get warning messages for active workflows
    pub fn warnings(&self) -> Vec<String> {
        let mut warnings = Vec::new();

        if self.watch_mode_active {
            warnings.push("📊 Watch mode is active - saves will trigger IFC sync".to_string());
        }

        if self.sync_active {
            warnings.push("🔄 Sync mode is active - saves will trigger IFC sync".to_string());
        }

        if self.sensors_active {
            warnings
                .push("📡 Sensors are active - equipment status fields may be locked".to_string());
        }

        warnings
    }
}

/// AR scan file watcher
/// Polls for new AR scan JSON files and notifies when they're detected
pub struct ArScanWatcher {
    scan_dir: PathBuf,
    last_scan_count: usize,
    last_check: Instant,
    debounce_interval: Duration,
}

impl ArScanWatcher {
    /// Create a new AR scan watcher for the given building
    pub fn new(building_name: &str) -> Result<Self, Box<dyn std::error::Error>> {
        // Check multiple possible scan directory locations
        let scan_dirs = vec![
            PathBuf::from(".arxos/ar-scans"),
            PathBuf::from(format!("{}_scans", building_name)),
            PathBuf::from(format!(".arxos/{}/scans", building_name)),
        ];

        let mut scan_dir = None;
        for dir in scan_dirs {
            if dir.exists() {
                scan_dir = Some(dir);
                break;
            }
        }

        // Use first directory or create it if none exist
        let scan_dir = scan_dir.unwrap_or_else(|| {
            let dir = PathBuf::from(".arxos/ar-scans");
            let _ = fs::create_dir_all(&dir);
            dir
        });

        // Count initial scan files
        let last_scan_count = Self::count_scan_files(&scan_dir).unwrap_or(0);

        Ok(Self {
            scan_dir,
            last_scan_count,
            last_check: Instant::now(),
            debounce_interval: Duration::from_secs(1), // Debounce 1 second
        })
    }

    /// Count scan JSON files in directory
    fn count_scan_files(dir: &Path) -> Result<usize, Box<dyn std::error::Error>> {
        if !dir.exists() {
            return Ok(0);
        }

        let count = fs::read_dir(dir)?
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.path().extension().and_then(|e| e.to_str()) == Some("json"))
            .count();

        Ok(count)
    }

    /// Check for new scan files (debounced)
    pub fn check_new_scans(&mut self) -> Result<usize, Box<dyn std::error::Error>> {
        // Debounce checks
        if self.last_check.elapsed() < self.debounce_interval {
            return Ok(0);
        }

        let current_count = Self::count_scan_files(&self.scan_dir)?;
        let new_count = current_count.saturating_sub(self.last_scan_count);

        if new_count > 0 {
            self.last_scan_count = current_count;
        }

        self.last_check = Instant::now();
        Ok(new_count)
    }

    /// Get scan directory path
    pub fn scan_dir(&self) -> &Path {
        &self.scan_dir
    }

    /// Get total scan count
    pub fn total_scan_count(&self) -> usize {
        self.last_scan_count
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_file_lock_acquire_release() {
        let temp_dir = TempDir::new().unwrap();
        let test_file = temp_dir.path().join("test.yaml");
        fs::write(&test_file, "test").unwrap();

        // Acquire lock
        let lock = FileLock::acquire(&test_file).unwrap();
        let lock_file_path = lock.lock_file().to_path_buf();
        assert!(lock_file_path.exists());

        // Try to acquire again (should fail)
        let result = FileLock::acquire(&test_file);
        assert!(result.is_err());

        // Release lock
        lock.release().unwrap();
        assert!(!lock_file_path.exists());

        // Can acquire again after release
        let lock2 = FileLock::acquire(&test_file).unwrap();
        assert!(lock2.lock_file().exists());
        lock2.release().unwrap();
    }

    #[test]
    fn test_conflict_detector() {
        let temp_dir = TempDir::new().unwrap();
        let test_file = temp_dir.path().join("test.yaml");
        fs::write(&test_file, "initial").unwrap();

        let mut detector = ConflictDetector::new(&test_file).unwrap();

        // No conflict initially
        assert!(!detector.check_conflict().unwrap());

        // Modify file externally
        std::thread::sleep(std::time::Duration::from_millis(10));
        fs::write(&test_file, "modified").unwrap();

        // Should detect conflict
        assert!(detector.check_conflict().unwrap());

        // Update after reload
        detector.update().unwrap();
        assert!(!detector.check_conflict().unwrap());
    }

    #[test]
    fn test_workflow_status() {
        let status = WorkflowStatus::default();
        assert!(!status.has_active_workflows());

        let status = WorkflowStatus {
            watch_mode_active: true,
            ..WorkflowStatus::default()
        };
        assert!(status.has_active_workflows());
        assert_eq!(status.warnings().len(), 1);
    }
}
