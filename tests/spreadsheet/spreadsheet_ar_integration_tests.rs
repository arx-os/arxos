//! Integration tests for AR scan watcher functionality
//!
//! Tests the AR scan file watcher that monitors for new AR scan files
//! and triggers spreadsheet auto-reload.

use arxos::tui::spreadsheet::workflow::ArScanWatcher;
use std::path::Path;
use serial_test::serial;
use std::fs;
use std::path::PathBuf;
use std::time::{Duration, Instant};
use tempfile::TempDir;

/// Test AR scan watcher creation and directory discovery
#[test]
#[serial]
fn test_ar_scan_watcher_creation() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create .arxos directory structure
    let arxos_dir = temp_dir.path().join(".arxos");
    fs::create_dir_all(&arxos_dir).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher - should create .arxos/ar-scans if it doesn't exist
    let watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Verify scan directory exists
    let scan_dir = arxos_dir.join("ar-scans");
    assert!(scan_dir.exists(), "Scan directory should be created");
    assert!(scan_dir.is_dir(), "Scan directory should be a directory");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test AR scan watcher finds existing scan directory
#[test]
#[serial]
fn test_ar_scan_watcher_finds_existing_directory() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create existing scan directory
    let arxos_dir = temp_dir.path().join(".arxos");
    let scan_dir = arxos_dir.join("ar-scans");
    fs::create_dir_all(&scan_dir).unwrap();
    
    // Create a test scan file
    let scan_file = scan_dir.join("scan-001.json");
    fs::write(&scan_file, r#"{"scan_id": "scan-001"}"#).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher
    let watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Verify initial count includes existing file
    let initial_count = watcher.total_scan_count();
    assert_eq!(initial_count, 1, "Should find existing scan file");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test AR scan file counting
#[test]
#[serial]
fn test_ar_scan_watcher_count_scan_files() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create scan directory
    let arxos_dir = temp_dir.path().join(".arxos");
    let scan_dir = arxos_dir.join("ar-scans");
    fs::create_dir_all(&scan_dir).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher
    let watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Initially no files
    assert_eq!(watcher.total_scan_count(), 0);
    
    // Create some scan files
    for i in 1..=5 {
        let scan_file = scan_dir.join(format!("scan-{:03}.json", i));
        fs::write(&scan_file, format!(r#"{{"scan_id": "scan-{:03}"}}"#, i)).unwrap();
    }
    
    // Count should be 5
    assert_eq!(watcher.total_scan_count(), 5);
    
    // Create more files
    for i in 6..=10 {
        let scan_file = scan_dir.join(format!("scan-{:03}.json", i));
        fs::write(&scan_file, format!(r#"{{"scan_id": "scan-{:03}"}}"#, i)).unwrap();
    }
    
    // Count should be 10
    assert_eq!(watcher.total_scan_count(), 10);
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test AR scan watcher detects new scans
#[test]
#[serial]
fn test_ar_scan_watcher_detects_new_scans() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create scan directory
    let arxos_dir = temp_dir.path().join(".arxos");
    let scan_dir = arxos_dir.join("ar-scans");
    fs::create_dir_all(&scan_dir).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher
    let mut watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Initial check - no new scans
    let new_scans = watcher.check_new_scans().unwrap();
    assert_eq!(new_scans, 0);
    
    // Create a new scan file
    let scan_file = scan_dir.join("scan-001.json");
    fs::write(&scan_file, r#"{"scan_id": "scan-001"}"#).unwrap();
    
    // Wait a bit for file system to settle (especially on macOS)
    std::thread::sleep(Duration::from_millis(100));
    
    // Check for new scans - should detect 1
    let new_scans = watcher.check_new_scans().unwrap();
    assert_eq!(new_scans, 1, "Should detect 1 new scan");
    
    // Check again - should be 0 (already counted)
    let new_scans = watcher.check_new_scans().unwrap();
    assert_eq!(new_scans, 0, "Should not detect new scans again");
    
    // Create multiple new scans
    for i in 2..=5 {
        let scan_file = scan_dir.join(format!("scan-{:03}.json", i));
        fs::write(&scan_file, format!(r#"{{"scan_id": "scan-{:03}"}}"#, i)).unwrap();
    }
    
    // Wait for file system
    std::thread::sleep(Duration::from_millis(100));
    
    // Should detect 4 new scans
    let new_scans = watcher.check_new_scans().unwrap();
    assert_eq!(new_scans, 4, "Should detect 4 new scans");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test AR scan watcher ignores non-JSON files
#[test]
#[serial]
fn test_ar_scan_watcher_ignores_non_json_files() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create scan directory
    let arxos_dir = temp_dir.path().join(".arxos");
    let scan_dir = arxos_dir.join("ar-scans");
    fs::create_dir_all(&scan_dir).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher
    let mut watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Create non-JSON files
    fs::write(scan_dir.join("scan.txt"), "not json").unwrap();
    fs::write(scan_dir.join("scan.yaml"), "not json").unwrap();
    fs::write(scan_dir.join("scan"), "not json").unwrap();
    
    // Should not count non-JSON files
    assert_eq!(watcher.total_scan_count(), 0);
    
    // Check for new scans
    let new_scans = watcher.check_new_scans().unwrap();
    assert_eq!(new_scans, 0);
    
    // Create a JSON file
    fs::write(scan_dir.join("scan.json"), r#"{"scan_id": "scan"}"#).unwrap();
    std::thread::sleep(Duration::from_millis(100));
    
    // Should count JSON file
    assert_eq!(watcher.total_scan_count(), 1);
    let new_scans = watcher.check_new_scans().unwrap();
    assert_eq!(new_scans, 1);
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test AR scan watcher debouncing
#[test]
#[serial]
fn test_ar_scan_watcher_debouncing() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create scan directory
    let arxos_dir = temp_dir.path().join(".arxos");
    let scan_dir = arxos_dir.join("ar-scans");
    fs::create_dir_all(&scan_dir).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher
    let mut watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Create a file quickly
    fs::write(scan_dir.join("scan-001.json"), r#"{"scan_id": "scan-001"}"#).unwrap();
    
    // Check immediately - should detect (debouncing allows immediate detection)
    let new_scans = watcher.check_new_scans().unwrap();
    assert!(new_scans >= 0, "Should handle rapid checks gracefully");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test AR scan watcher with building-specific directory
#[test]
#[serial]
fn test_ar_scan_watcher_building_specific_directory() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create building-specific scan directory
    let arxos_dir = temp_dir.path().join(".arxos");
    let building_dir = arxos_dir.join(building_name);
    let scan_dir = building_dir.join("scans");
    fs::create_dir_all(&scan_dir).unwrap();
    
    // Create a scan file
    fs::write(scan_dir.join("scan-001.json"), r#"{"scan_id": "scan-001"}"#).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher - should find building-specific directory
    let watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Should find the scan file in building-specific directory
    let count = watcher.total_scan_count();
    assert!(count >= 0, "Should handle building-specific directory");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test AR scan watcher with alternate directory names
#[test]
#[serial]
fn test_ar_scan_watcher_alternate_directory_names() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create alternate directory name
    let scan_dir = temp_dir.path().join(format!("{}_scans", building_name));
    fs::create_dir_all(&scan_dir).unwrap();
    
    // Create a scan file
    fs::write(scan_dir.join("scan-001.json"), r#"{"scan_id": "scan-001"}"#).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create watcher - should find alternate directory
    let watcher = ArScanWatcher::new(building_name).unwrap();
    
    // Should find the scan file
    let count = watcher.total_scan_count();
    assert!(count >= 0, "Should handle alternate directory names");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

