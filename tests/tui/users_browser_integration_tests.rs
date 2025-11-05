//! Integration tests for user browser TUI
//!
//! Tests the interactive user browser interface including:
//! - User list rendering
//! - Search/filter functionality
//! - User detail display
//! - Organization grouping
//! - Activity timeline
//! - Git commit attribution
//! - End-to-end user browser workflow

use arxos::identity::{UserRegistry, User};
use arxos::git::manager::{BuildingGitManager, GitConfig, CommitMetadata};
use arxos::commands::git_ops::extract_user_id_from_commit;
use std::collections::HashMap;
use tempfile::TempDir;
use serial_test::serial;

/// Test that UserRegistry can be created and loaded
#[test]
fn test_user_registry_creation() {
    let temp_dir = TempDir::new().unwrap();
    let registry = UserRegistry::load(temp_dir.path()).unwrap();
    assert_eq!(registry.all_users().len(), 0);
}

/// Test that users can be added to registry
#[test]
fn test_user_registry_add_users() {
    let temp_dir = TempDir::new().unwrap();
    let mut registry = UserRegistry::load(temp_dir.path()).unwrap();
    
    let user1 = User::new(
        "alice@example.com".to_string(),
        "Alice Smith".to_string(),
        Some("Acme Corp".to_string()),
        None,
        None,
    );
    
    let user2 = User::new(
        "bob@example.com".to_string(),
        "Bob Jones".to_string(),
        Some("Beta Inc".to_string()),
        None,
        None,
    );
    
    registry.add_user(user1).unwrap();
    registry.add_user(user2).unwrap();
    
    assert_eq!(registry.all_users().len(), 2);
    assert!(registry.find_by_email("alice@example.com").is_some());
    assert!(registry.find_by_email("bob@example.com").is_some());
}

/// Test case-insensitive email lookup
#[test]
fn test_registry_case_insensitive_email_lookup() {
    let temp_dir = TempDir::new().unwrap();
    let mut registry = UserRegistry::load(temp_dir.path()).unwrap();
    
    let user = User::new(
        "Test@Example.COM".to_string(),
        "Test User".to_string(),
        None,
        None,
        None,
    );
    
    registry.add_user(user).unwrap();
    
    // Should find with any case variation
    assert!(registry.find_by_email("test@example.com").is_some());
    assert!(registry.find_by_email("TEST@EXAMPLE.COM").is_some());
    assert!(registry.find_by_email("Test@Example.COM").is_some());
    assert!(registry.find_by_email("unknown@example.com").is_none());
}

/// Test filtering users by query (simulating filter_users functionality)
#[test]
fn test_user_filtering_by_query() {
    let temp_dir = TempDir::new().unwrap();
    let mut registry = UserRegistry::load(temp_dir.path()).unwrap();
    
    // Create users with different names and organizations
    let users = vec![
        ("alice@example.com", "Alice Smith", "Acme Corp"),
        ("bob@example.com", "Bob Jones", "Beta Inc"),
        ("charlie@example.com", "Charlie Brown", "Acme Corp"),
    ];
    
    for (email, name, org) in users {
        let user = User::new(
            email.to_string(),
            name.to_string(),
            Some(org.to_string()),
            None,
            None,
        );
        registry.add_user(user).unwrap();
    }
    
    // Test finding users by organization (simulating filter)
    let all_users = registry.all_users();
    let acme_users: Vec<_> = all_users
        .iter()
        .filter(|u| u.organization.as_ref().map(|o| o == "Acme Corp").unwrap_or(false))
        .collect();
    
    assert_eq!(acme_users.len(), 2);
    assert!(acme_users.iter().any(|u| u.email == "alice@example.com"));
    assert!(acme_users.iter().any(|u| u.email == "charlie@example.com"));
    
    // Test finding by name
    let alice_users: Vec<_> = all_users
        .iter()
        .filter(|u| u.name.to_lowercase().contains("alice"))
        .collect();
    
    assert_eq!(alice_users.len(), 1);
    assert_eq!(alice_users[0].email, "alice@example.com");
}

/// Test organization grouping logic
#[test]
fn test_organization_grouping() {
    let temp_dir = TempDir::new().unwrap();
    let mut registry = UserRegistry::load(temp_dir.path()).unwrap();
    
    let users: Vec<(&str, &str, Option<&str>)> = vec![
        ("alice@example.com", "Alice Smith", Some("Acme Corp")),
        ("bob@example.com", "Bob Jones", Some("Beta Inc")),
        ("charlie@example.com", "Charlie Brown", Some("Acme Corp")),
        ("dave@example.com", "Dave Wilson", None),
    ];
    
    for (email, name, org) in users {
        let user = User::new(
            email.to_string(),
            name.to_string(),
            org.map(|s| s.to_string()),
            None,
            None,
        );
        registry.add_user(user).unwrap();
    }
    
    // Group users by organization
    let mut org_groups: HashMap<String, Vec<String>> = HashMap::new();
    let all_users = registry.all_users();
    
    for (idx, user) in all_users.iter().enumerate() {
        let org_name = user.organization.as_deref().unwrap_or("No Organization");
        org_groups.entry(org_name.to_string()).or_default().push(format!("{}", idx));
    }
    
    assert_eq!(org_groups.get("Acme Corp").map(|v| v.len()).unwrap_or(0), 2);
    assert_eq!(org_groups.get("Beta Inc").map(|v| v.len()).unwrap_or(0), 1);
    assert_eq!(org_groups.get("No Organization").map(|v| v.len()).unwrap_or(0), 1);
}

/// Test user activity loading with Git commits
#[serial]
#[test]
fn test_user_activity_with_git_commits() -> Result<(), Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let original_dir = std::env::current_dir()?;
    
    // Setup: Create Git repository
    let _repo = git2::Repository::init(temp_dir.path())?;
    std::env::set_current_dir(temp_dir.path())?;
    
    // Create user registry
    let mut registry = UserRegistry::load(temp_dir.path())?;
    let user = User::new(
        "test@example.com".to_string(),
        "Test User".to_string(),
        None,
        None,
        None,
    );
    registry.add_user(user)?;
    registry.save()?;
    
    let saved_user = registry.find_by_email("test@example.com").unwrap();
    let user_id = saved_user.id.clone();
    
    // Create Git commits with user attribution
    let config = GitConfig {
        author_name: "Test Author".to_string(),
        author_email: "test@example.com".to_string(),
        branch: "main".to_string(),
        remote_url: None,
    };
    
    let mut git_manager = BuildingGitManager::new(
        &temp_dir.path().to_string_lossy(),
        "Test Building",
        config
    )?;
    
    // Create a commit with user attribution
    let metadata = CommitMetadata {
        message: "Test commit with user attribution".to_string(),
        user_id: Some(user_id.clone()),
        device_id: None,
        ar_scan_id: None,
        signature: None,
    };
    
    // Stage and commit a test file
    let test_file = temp_dir.path().join("test.txt");
    std::fs::write(&test_file, "test content")?;
    
    git_manager.stage_file("test.txt")?;
    git_manager.commit_staged_with_user(&metadata)?;
    
    // Load commits and verify user attribution
    let commits = git_manager.list_commits(10)?;
    assert!(!commits.is_empty());
    
    let attributed_commit = commits.iter()
        .find(|c| extract_user_id_from_commit(&c.message).is_some())
        .expect("Should find commit with user attribution");
    
    let extracted_user_id = extract_user_id_from_commit(&attributed_commit.message)
        .expect("Should extract user ID");
    
    assert_eq!(extracted_user_id, user_id);
    
    // Verify user can be found by ID
    let user_from_id = registry.find_by_id(&extracted_user_id);
    assert!(user_from_id.is_some());
    assert_eq!(user_from_id.unwrap().email, "test@example.com");
    
    std::env::set_current_dir(original_dir)?;
    Ok(())
}

/// Test user activity filtering by user_id
#[serial]
#[test]
fn test_user_activity_filtering() -> Result<(), Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let original_dir = std::env::current_dir()?;
    
    let _repo = git2::Repository::init(temp_dir.path())?;
    std::env::set_current_dir(temp_dir.path())?;
    
    // Create two users
    let mut registry = UserRegistry::load(temp_dir.path())?;
    
    let user1 = User::new(
        "user1@example.com".to_string(),
        "User One".to_string(),
        None,
        None,
        None,
    );
    let user2 = User::new(
        "user2@example.com".to_string(),
        "User Two".to_string(),
        None,
        None,
        None,
    );
    
    registry.add_user(user1)?;
    registry.add_user(user2)?;
    registry.save()?;
    
    let saved_user1 = registry.find_by_email("user1@example.com").unwrap();
    let saved_user2 = registry.find_by_email("user2@example.com").unwrap();
    let user1_id = saved_user1.id.clone();
    let user2_id = saved_user2.id.clone();
    
    // Create commits for both users
    let config = GitConfig {
        author_name: "Test Author".to_string(),
        author_email: "test@example.com".to_string(),
        branch: "main".to_string(),
        remote_url: None,
    };
    
    let mut git_manager = BuildingGitManager::new(
        &temp_dir.path().to_string_lossy(),
        "Test Building",
        config
    )?;
    
    // Commit 1: User 1
    let test_file1 = temp_dir.path().join("test1.txt");
    std::fs::write(&test_file1, "content 1")?;
    git_manager.stage_file("test1.txt")?;
    
    let metadata1 = CommitMetadata {
        message: "User 1 commit".to_string(),
        user_id: Some(user1_id.clone()),
        device_id: None,
        ar_scan_id: None,
        signature: None,
    };
    git_manager.commit_staged_with_user(&metadata1)?;
    
    // Commit 2: User 2
    let test_file2 = temp_dir.path().join("test2.txt");
    std::fs::write(&test_file2, "content 2")?;
    git_manager.stage_file("test2.txt")?;
    
    let metadata2 = CommitMetadata {
        message: "User 2 commit".to_string(),
        user_id: Some(user2_id.clone()),
        device_id: None,
        ar_scan_id: None,
        signature: None,
    };
    git_manager.commit_staged_with_user(&metadata2)?;
    
    // Verify filtering works
    let commits = git_manager.list_commits(10)?;
    
    let user1_commits: Vec<_> = commits.iter()
        .filter(|c| {
            extract_user_id_from_commit(&c.message)
                .map(|uid| uid == user1_id)
                .unwrap_or(false)
        })
        .collect();
    
    let user2_commits: Vec<_> = commits.iter()
        .filter(|c| {
            extract_user_id_from_commit(&c.message)
                .map(|uid| uid == user2_id)
                .unwrap_or(false)
        })
        .collect();
    
    assert_eq!(user1_commits.len(), 1);
    assert_eq!(user2_commits.len(), 1);
    assert!(user1_commits[0].message.contains("User 1"));
    assert!(user2_commits[0].message.contains("User 2"));
    
    std::env::set_current_dir(original_dir)?;
    Ok(())
}

/// Test user browser workflow: registry → filtering → activity loading
#[test]
fn test_user_browser_workflow() {
    let temp_dir = TempDir::new().unwrap();
    let mut registry = UserRegistry::load(temp_dir.path()).unwrap();
    
    // Create multiple users
    let users_data = vec![
        ("alice@example.com", "Alice Smith", "Acme Corp"),
        ("bob@example.com", "Bob Jones", "Beta Inc"),
        ("charlie@example.com", "Charlie Brown", "Acme Corp"),
    ];
    
    for (email, name, org) in users_data {
        let user = User::new(
            email.to_string(),
            name.to_string(),
            Some(org.to_string()),
            None,
            None,
        );
        registry.add_user(user).unwrap();
    }
    
    // Test workflow: Load → Filter → Select
    let all_users = registry.all_users();
    assert_eq!(all_users.len(), 3);
    
    // Filter by organization
    let acme_users: Vec<_> = all_users
        .iter()
        .filter(|u| u.organization.as_ref().map(|o| o == "Acme Corp").unwrap_or(false))
        .collect();
    
    assert_eq!(acme_users.len(), 2);
    
    // Filter by name
    let alice: Vec<_> = all_users
        .iter()
        .filter(|u| u.name.contains("Alice"))
        .collect();
    
    assert_eq!(alice.len(), 1);
    assert_eq!(alice[0].email, "alice@example.com");
    
    // Verify user lookup works
    assert!(registry.find_by_email("alice@example.com").is_some());
    assert!(registry.find_by_email("bob@example.com").is_some());
    assert!(registry.find_by_email("charlie@example.com").is_some());
}

/// Test user search functionality (name, email, organization)
#[test]
fn test_user_search_functionality() {
    let temp_dir = TempDir::new().unwrap();
    let mut registry = UserRegistry::load(temp_dir.path()).unwrap();
    
    // Create diverse users
    let users_data = vec![
        ("john.doe@acme.com", "John Doe", "Acme Corporation"),
        ("jane.smith@beta.io", "Jane Smith", "Beta Industries"),
        ("bob.jones@acme.com", "Bob Jones", "Acme Corporation"),
        ("alice.williams@gamma.net", "Alice Williams", "Gamma Services"),
    ];
    
    for (email, name, org) in users_data {
        let user = User::new(
            email.to_string(),
            name.to_string(),
            Some(org.to_string()),
            None,
            None,
        );
        registry.add_user(user).unwrap();
    }
    
    let all_users = registry.all_users();
    
    // Test search by email domain
    let acme_email_users: Vec<_> = all_users
        .iter()
        .filter(|u| u.email.contains("@acme.com"))
        .collect();
    assert_eq!(acme_email_users.len(), 2);
    
    // Test search by name substring
    let name_contains_j: Vec<_> = all_users
        .iter()
        .filter(|u| u.name.to_lowercase().contains("j"))
        .collect();
    assert_eq!(name_contains_j.len(), 3); // John, Jane, Bob (Jones)
    
    // Test search by organization
    let acme_org_users: Vec<_> = all_users
        .iter()
        .filter(|u| {
            u.organization.as_ref()
                .map(|o| o.contains("Acme"))
                .unwrap_or(false)
        })
        .collect();
    assert_eq!(acme_org_users.len(), 2);
}

/// Test user verification status display logic
#[test]
fn test_user_verification_status() {
    let temp_dir = TempDir::new().unwrap();
    let mut registry = UserRegistry::load(temp_dir.path()).unwrap();
    
    // First user gets admin and auto-verified
    let admin = User::new(
        "admin@example.com".to_string(),
        "Admin User".to_string(),
        None,
        None,
        None,
    );
    registry.add_user(admin).unwrap();
    
    // Regular user - not verified
    let regular = User::new(
        "user@example.com".to_string(),
        "Regular User".to_string(),
        None,
        None,
        None,
    );
    registry.add_user(regular).unwrap();
    
    let all_users = registry.all_users();
    
    let admin_user = all_users.iter().find(|u| u.email == "admin@example.com").unwrap();
    assert!(admin_user.verified);
    assert!(admin_user.has_permission("verify_users"));
    
    let regular_user = all_users.iter().find(|u| u.email == "user@example.com").unwrap();
    assert!(!regular_user.verified);
    assert!(!regular_user.has_permission("verify_users"));
}
