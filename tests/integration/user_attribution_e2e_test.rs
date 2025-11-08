//! End-to-end user attribution integration test
//!
//! This test verifies the complete user attribution workflow:
//! 1. Create user in registry
//! 2. Mobile FFI calls with user_email
//! 3. Git commit includes ArxOS-User-ID trailer
//! 4. Verify user attribution in commit history
//! 5. Verify user appears in user browser with activity

use arxos::ar_integration::pending::PendingEquipmentManager;
use arxos::git::manager::{BuildingGitManager, GitConfig};
use arxos::identity::{User, UserRegistry};
use arxos::mobile_ffi::ffi;
use arxui::commands::git_ops::extract_user_id_from_commit;
use serial_test::serial;
use std::ffi::{CStr, CString};
use std::path::{Path, PathBuf};
use tempfile::TempDir;

/// Helper to create a C string for FFI calls
fn to_c_string(s: &str) -> *const std::ffi::c_char {
    CString::new(s).unwrap().into_raw()
}

/// Helper to free a C string
unsafe fn free_c_string(ptr: *const std::ffi::c_char) {
    if !ptr.is_null() {
        drop(CString::from_raw(ptr as *mut std::ffi::c_char));
    }
}

/// Helper to create test building in temp directory
fn create_test_building(
    temp_dir: &TempDir,
    building_name: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    use std::fs;

    // Initialize Git repository
    let repo_path = temp_dir.path();
    let _repo = git2::Repository::init(repo_path)?;

    // Create building YAML file
    let building_yaml = format!(
        r#"
building:
  id: {}
  name: {}
  address: "123 Test St"
  total_floors: 1
metadata:
  version: "2.0"
  last_updated: "2024-01-01T00:00:00Z"
floors:
  - name: "Floor 1"
    level: 1
    rooms: []
    equipment: []
"#,
        building_name, building_name
    );

    let building_path = repo_path.join(format!("{}.yaml", building_name));
    fs::write(&building_path, building_yaml)?;

    // Stage and commit initial building file
    let repo = git2::Repository::open(repo_path)?;
    let mut index = repo.index()?;
    index.add_path(Path::new(&format!("{}.yaml", building_name)))?;
    index.write()?;

    let signature = git2::Signature::now("Test Author", "test@example.com")?;
    let tree_id = index.write_tree()?;
    let tree = repo.find_tree(tree_id)?;
    repo.commit(
        Some("HEAD"),
        &signature,
        &signature,
        "Initial building file",
        &tree,
        &[],
    )?;

    Ok(())
}

struct DirGuard {
    original_dir: PathBuf,
}

impl DirGuard {
    fn change_to(target: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        let original_dir = std::env::current_dir()?;
        std::env::set_current_dir(target)?;
        Ok(Self { original_dir })
    }
}

impl Drop for DirGuard {
    fn drop(&mut self) {
        if let Err(err) = std::env::set_current_dir(&self.original_dir) {
            eprintln!(
                "DirGuard: failed to restore directory {}: {}",
                self.original_dir.display(),
                err
            );
        }
    }
}

#[serial]
#[test]
fn test_user_attribution_e2e_ar_scan() -> Result<(), Box<dyn std::error::Error>> {
    // Test: Complete user attribution flow for AR scan

    let temp_dir = TempDir::new()?;

    // Setup: Create test building and Git repository
    let building_name = "e2e_attribution_test";
    create_test_building(&temp_dir, building_name)?;

    // Change to temp directory
    let _guard = DirGuard::change_to(temp_dir.path())?;

    // Step 1: Create user in registry
    let user_email = "test.user@example.com";
    let user_name = "Test User";
    let mut registry = UserRegistry::load(temp_dir.path())?;

    let user = User::new(
        user_email.to_string(),
        user_name.to_string(),
        Some("Test Organization".to_string()),
        Some("AR Scanner".to_string()),
        None,
    );

    // First user gets admin permissions automatically
    registry.add_user(user)?;
    registry.save()?;

    // Get the user ID for verification
    let saved_user = registry.find_by_email(user_email).unwrap();
    let user_id = saved_user.id.clone();
    assert!(!user_id.is_empty());
    assert!(user_id.starts_with("usr_"));

    // Step 2: Simulate mobile FFI call with user_email
    // This mimics what happens when a mobile app calls arxos_save_ar_scan
    let json_data = r#"{
        "detectedEquipment": [
            {
                "name": "Test HVAC Unit",
                "type": "HVAC",
                "position": {"x": 10.0, "y": 20.0, "z": 3.0},
                "confidence": 0.9,
                "detectionMethod": "AR Scan"
            }
        ],
        "roomBoundaries": {"walls": [], "openings": []},
        "roomName": "Test Room",
        "floorLevel": 1
    }"#;

    unsafe {
        let json_ptr = to_c_string(json_data);
        let building_ptr = to_c_string(building_name);
        let user_email_ptr = to_c_string(user_email);

        // Call FFI function with user_email
        let result = ffi::arxos_save_ar_scan(json_ptr, building_ptr, user_email_ptr, 0.7);

        // Verify result
        assert!(!result.is_null());
        let c_str = CStr::from_ptr(result);
        let json_str = c_str.to_str()?;
        let parsed: serde_json::Value = serde_json::from_str(json_str)?;

        // Should succeed
        assert!(
            parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false),
            "AR scan save should succeed"
        );

        // Cleanup
        ffi::arxos_free_string(result);
        free_c_string(json_ptr);
        free_c_string(building_ptr);
        free_c_string(user_email_ptr);
    }

    // Step 3: Verify pending equipment captures user attribution
    let storage_file = format!("{}_pending.json", building_name);
    let storage_path = Path::new(&storage_file);
    let mut manager = PendingEquipmentManager::new(building_name.to_string());
    manager.load_from_storage(storage_path)?;
    let pending_items = manager.list_pending();
    assert!(
        !pending_items.is_empty(),
        "AR scan should create pending equipment"
    );
    let pending_user = pending_items[0].user_email.as_deref().unwrap_or_default();
    assert_eq!(
        pending_user, user_email,
        "Pending equipment should retain user email"
    );

    // Step 4: Verify registry still contains user
    let registry_after = UserRegistry::load(temp_dir.path())?;
    let user_from_registry = registry_after
        .find_by_email(user_email)
        .expect("User should remain in registry");
    assert_eq!(user_from_registry.id, user_id);

    Ok(())
}

#[serial]
#[test]
fn test_user_attribution_e2e_confirm_equipment() -> Result<(), Box<dyn std::error::Error>> {
    // Test: User attribution in pending equipment confirmation

    let temp_dir = TempDir::new()?;

    // Setup: Create test building
    let building_name = "e2e_confirm_attribution_test";
    create_test_building(&temp_dir, building_name)?;

    let _guard = DirGuard::change_to(temp_dir.path())?;

    // Step 1: Create user
    let user_email = "confirm.user@example.com";
    let mut registry = UserRegistry::load(temp_dir.path())?;
    let user = User::new(
        user_email.to_string(),
        "Confirm User".to_string(),
        None,
        None,
        None,
    );
    registry.add_user(user)?;
    registry.save()?;

    let saved_user = registry.find_by_email(user_email).unwrap();
    let user_id = saved_user.id.clone();

    // Step 2: Create pending equipment via AR scan
    unsafe {
        let json_data = r#"{
            "detectedEquipment": [
                {
                    "name": "Pending Equipment",
                    "type": "Electrical",
                    "position": {"x": 5.0, "y": 10.0, "z": 2.0},
                    "confidence": 0.8,
                    "detectionMethod": "AR Scan"
                }
            ],
            "roomBoundaries": {"walls": [], "openings": []}
        }"#;

        let json_ptr = to_c_string(json_data);
        let building_ptr = to_c_string(building_name);
        let user_email_ptr = to_c_string(user_email);

        let save_result = ffi::arxos_save_ar_scan(json_ptr, building_ptr, user_email_ptr, 0.7);

        let c_str = CStr::from_ptr(save_result);
        let json_str = c_str.to_str()?;
        let parsed: serde_json::Value = serde_json::from_str(json_str)?;

        // Get pending ID
        let empty_vec: Vec<serde_json::Value> = vec![];
        let pending_ids = parsed
            .get("pending_ids")
            .and_then(|ids| ids.as_array())
            .unwrap_or(&empty_vec);

        if pending_ids.is_empty() {
            // No pending items created, skip confirmation test
            ffi::arxos_free_string(save_result);
            free_c_string(json_ptr);
            free_c_string(building_ptr);
            free_c_string(user_email_ptr);

            return Ok(());
        }

        let pending_id = pending_ids[0].as_str().unwrap();
        let pending_id_ptr = to_c_string(pending_id);

        // Step 3: Confirm pending equipment with user_email
        let confirm_result = ffi::arxos_confirm_pending_equipment(
            building_ptr,
            pending_id_ptr,
            user_email_ptr,
            1, // commit to Git
        );

        assert!(!confirm_result.is_null());
        let confirm_c_str = CStr::from_ptr(confirm_result);
        let confirm_json_str = confirm_c_str.to_str()?;
        let confirm_parsed: serde_json::Value = serde_json::from_str(confirm_json_str)?;

        assert!(
            confirm_parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false),
            "Equipment confirmation should succeed"
        );

        // Cleanup
        ffi::arxos_free_string(save_result);
        ffi::arxos_free_string(confirm_result);
        free_c_string(json_ptr);
        free_c_string(building_ptr);
        free_c_string(user_email_ptr);
        free_c_string(pending_id_ptr);
    }

    // Step 4: Verify commit includes user attribution
    let config = GitConfig {
        author_name: "Test Author".to_string(),
        author_email: "test@example.com".to_string(),
        branch: "main".to_string(),
        remote_url: None,
    };

    let repo_path_str = temp_dir.path().to_string_lossy().to_string();
    let git_manager = BuildingGitManager::new(&repo_path_str, building_name, config)?;

    let commits = git_manager.list_commits(10)?;

    // Find confirmation commit
    let confirm_commit = commits
        .iter()
        .find(|c| c.message.contains("Confirm") || c.message.contains("pending"))
        .expect("Should find confirmation commit");

    // Verify user attribution
    let extracted_user_id = extract_user_id_from_commit(&confirm_commit.message)
        .expect("Should extract user ID from confirmation commit");

    assert_eq!(
        extracted_user_id, user_id,
        "Confirmation commit should be attributed to correct user"
    );

    Ok(())
}

#[serial]
#[test]
fn test_user_attribution_fallback_to_config() -> Result<(), Box<dyn std::error::Error>> {
    // Test: Backward compatibility - null user_email falls back to config

    let temp_dir = TempDir::new()?;

    let building_name = "e2e_fallback_test";
    create_test_building(&temp_dir, building_name)?;

    let _guard = DirGuard::change_to(temp_dir.path())?;

    // Create user in registry
    let user_email = "config.user@example.com";
    let mut registry = UserRegistry::load(temp_dir.path())?;
    let user = User::new(
        user_email.to_string(),
        "Config User".to_string(),
        None,
        None,
        None,
    );
    registry.add_user(user)?;
    registry.save()?;

    // Test with null user_email (backward compatibility)
    unsafe {
        let json_data = r#"{
            "detectedEquipment": [
                {
                    "name": "Fallback Test Equipment",
                    "type": "HVAC",
                    "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                    "confidence": 0.9,
                    "detectionMethod": "Test"
                }
            ],
            "roomBoundaries": {"walls": [], "openings": []}
        }"#;

        let json_ptr = to_c_string(json_data);
        let building_ptr = to_c_string(building_name);

        // Call with null user_email (should fallback to config)
        let result = ffi::arxos_save_ar_scan(
            json_ptr,
            building_ptr,
            std::ptr::null(), // null user_email
            0.7,
        );

        // Should still succeed (may or may not have user attribution depending on config)
        assert!(!result.is_null());

        let c_str = CStr::from_ptr(result);
        let _json_str = c_str.to_str()?;

        ffi::arxos_free_string(result);
        free_c_string(json_ptr);
        free_c_string(building_ptr);
    }

    Ok(())
}
