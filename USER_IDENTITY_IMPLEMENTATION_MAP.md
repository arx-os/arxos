# User Identity & Attribution - Implementation Map

**Version:** 1.0  
**Date:** January 2025  
**Status:** Technical Architecture Document

---

## Overview

This document maps out exactly where to implement the User Identity & Attribution system in the ArxOS codebase. It follows the Git-native architecture and integrates with existing commit flows.

---

## Directory Structure

```
src/
├── identity/                    # NEW: Identity module (Phase 1)
│   ├── mod.rs                  # Module exports and public API
│   ├── user.rs                 # User data structures
│   ├── registry.rs             # UserRegistry implementation
│   ├── pending.rs              # Pending user requests (Phase 2)
│   └── gpg.rs                  # GPG signatures (Phase 3)
│
├── git/
│   └── manager.rs              # MODIFY: Add user_id to commits
│
├── persistence/
│   └── mod.rs                  # MODIFY: Pass user context to commits
│
├── mobile_ffi/
│   ├── ffi.rs                  # MODIFY: Add user_email parameter
│   └── jni.rs                  # MODIFY: Add user_email parameter
│
├── commands/
│   ├── users.rs                # NEW: User management commands
│   ├── git_ops.rs              # MODIFY: Display user info from registry
│   └── watch.rs                # MODIFY: Show user attribution
│
└── ui/
    └── users.rs                # NEW: User UI components (Phase 4)
```

---

## Implementation Locations

### 1. Core Identity Module (`src/identity/`)

**Purpose:** Central identity management system

#### 1.1 User Data Structure (`src/identity/user.rs`)

```rust
// src/identity/user.rs
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,  // UUID: "usr_550e8400-e29b-41d4-a716-446655440000"
    pub email: String,  // Primary lookup key
    pub name: String,
    pub organization: Option<String>,
    pub role: Option<String>,
    pub phone: Option<String>,  // Optional for privacy
    pub verified: bool,
    pub verified_by: Option<String>,  // Email of admin who verified
    pub verified_at: Option<DateTime<Utc>>,
    pub public_key_fingerprint: Option<String>,  // GPG key (Phase 3)
    pub status: UserStatus,
    pub added_at: DateTime<Utc>,
    pub last_active: Option<DateTime<Utc>>,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UserStatus {
    #[serde(rename = "active")]
    Active,
    #[serde(rename = "inactive")]
    Inactive,
    #[serde(rename = "revoked")]
    Revoked,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserRegistryData {
    pub version: String,
    pub users: Vec<User>,
}
```

**Integration Point:**
- Exported via `src/identity/mod.rs`
- Used by `UserRegistry` and command handlers

---

#### 1.2 User Registry (`src/identity/registry.rs`)

```rust
// src/identity/registry.rs
use std::path::{Path, PathBuf};
use crate::identity::user::{User, UserRegistryData, UserStatus};

pub struct UserRegistry {
    users: Vec<User>,
    file_path: PathBuf,
    repo_path: PathBuf,
}

impl UserRegistry {
    /// Load registry from building repository
    pub fn load(repo_path: &Path) -> Result<Self, RegistryError> {
        // Load from users.yaml in repo root
        // Path: repo_path / "users.yaml"
    }
    
    /// Find user by email (primary lookup)
    pub fn find_by_email(&self, email: &str) -> Option<&User> {
        // Case-insensitive email lookup
    }
    
    /// Find user by ID
    pub fn find_by_id(&self, id: &str) -> Option<&User> {
        // UUID-based lookup
    }
    
    /// Add new user (admin only)
    pub fn add_user(&mut self, user: User) -> Result<(), RegistryError> {
        // Validate email uniqueness
        // Check admin permissions (if implemented)
    }
    
    /// Save registry to Git
    pub fn save(&self) -> Result<(), RegistryError> {
        // Write to users.yaml
        // Stage to Git (but don't commit - let caller decide)
    }
}
```

**Integration Points:**
- Called by `src/commands/users.rs` (add/list/verify commands)
- Called by `src/git/manager.rs` (lookup user for commit attribution)
- Called by `src/commands/git_ops.rs` (display user info in history)

**File Location:**
- Registry file: `{repo_root}/users.yaml` (version controlled in Git)

---

### 2. Git Integration (`src/git/manager.rs`)

**Current State:**
```rust
// Line 286-289: Creates signature from git_config
let signature = Signature::now(
    &self.git_config.author_name,
    &self.git_config.author_email,
)?;
```

**Modification Required:**

#### 2.1 Enhanced Commit Metadata

```rust
// src/git/manager.rs

// Add new struct for commit metadata
#[derive(Debug, Clone)]
pub struct CommitMetadata {
    pub message: String,
    pub user_id: Option<String>,  // From registry
    pub device_id: Option<String>,  // From mobile (Phase 3)
}

impl BuildingGitManager {
    // MODIFY: commit_changes() to accept user context
    fn commit_changes_with_user(
        &self,
        metadata: &CommitMetadata,
        file_paths: &[String],
    ) -> Result<String, GitError> {
        // ... existing staging logic ...
        
        // Create signature (existing)
        let signature = Signature::now(
            &self.git_config.author_name,
            &self.git_config.author_email,
        )?;
        
        // Build enhanced commit message with trailers
        let enhanced_message = self.build_commit_message(&metadata)?;
        
        // Create commit
        let commit_id = self.repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            &enhanced_message,  // Use enhanced message
            &tree,
            &parent_commit.iter().collect::<Vec<_>>(),
        )?;
        
        Ok(commit_id.to_string())
    }
    
    // NEW: Build commit message with Git trailers
    fn build_commit_message(&self, metadata: &CommitMetadata) -> Result<String, GitError> {
        let mut message = metadata.message.clone();
        
        // Add Git trailers for user_id
        if let Some(ref user_id) = metadata.user_id {
            message.push_str(&format!("\n\nArxOS-User-ID: {}", user_id));
        }
        
        if let Some(ref device_id) = metadata.device_id {
            message.push_str(&format!("\nArxOS-Device-ID: {}", device_id));
        }
        
        Ok(message)
    }
    
    // MODIFY: commit_staged() to use user context
    pub fn commit_staged_with_user(
        &mut self,
        metadata: &CommitMetadata,
    ) -> Result<String, GitError> {
        // Similar to commit_changes_with_user but for staged changes
    }
}
```

**Integration Points:**
- Called by `src/persistence/mod.rs::save_and_commit()`
- Called by `src/mobile_ffi/ffi.rs` (via persistence layer)
- Called by `src/commands/git_ops.rs::handle_commit()`

---

### 3. Persistence Layer (`src/persistence/mod.rs`)

**Current State:**
```rust
// Line 140: save_and_commit() creates Git commit
pub fn save_and_commit(&self, data: &BuildingData, message: Option<&str>) -> PersistenceResult<String> {
    // ... saves to YAML ...
    
    // Creates Git commit
    let result = git_manager.export_building(data, message)?;
    Ok(result.commit_id)
}
```

**Modification Required:**

```rust
// src/persistence/mod.rs

use crate::identity::registry::UserRegistry;
use crate::git::CommitMetadata;

impl PersistenceManager {
    // NEW: Enhanced save_and_commit with user context
    pub fn save_and_commit_with_user(
        &self,
        data: &BuildingData,
        message: Option<&str>,
        user_email: Option<&str>,  // User email from config or FFI
    ) -> PersistenceResult<String> {
        // First save to YAML file
        self.save_building_data(data)?;
        
        // Commit to Git if repository exists
        if let Some(ref repo_path) = self.git_repo {
            // Load user registry
            let registry = UserRegistry::load(repo_path)?;
            
            // Look up user by email
            let user_id = user_email.and_then(|email| {
                registry.find_by_email(email).map(|u| u.id.clone())
            });
            
            // Build commit metadata
            let commit_message = message.unwrap_or("Update building data");
            let metadata = CommitMetadata {
                message: commit_message.to_string(),
                user_id,
                device_id: None,  // Phase 3
            };
            
            // Load Git config
            let config = GitConfigManager::load_from_arx_config_or_env();
            let mut git_manager = BuildingGitManager::new(
                &repo_path.to_string_lossy(),
                &self.building_name,
                config
            )?;
            
            // Commit with user metadata
            let commit_id = git_manager.commit_staged_with_user(&metadata)?;
            Ok(commit_id)
        } else {
            Ok("no-git-repo".to_string())
        }
    }
    
    // KEEP: Existing save_and_commit for backward compatibility
    pub fn save_and_commit(&self, data: &BuildingData, message: Option<&str>) -> PersistenceResult<String> {
        // Get user email from config
        let user_email = crate::config::get_config_or_default().user.email.clone();
        let user_email = if user_email.is_empty() { None } else { Some(user_email.as_str()) };
        
        self.save_and_commit_with_user(data, message, user_email)
    }
}
```

**Integration Points:**
- Called by `src/mobile_ffi/ffi.rs` (AR scan saves)
- Called by `src/commands/equipment_handlers.rs` (equipment updates)
- Called by `src/commands/room_handlers.rs` (room updates)
- Called by `src/ui/spreadsheet/data_source.rs` (spreadsheet saves)

---

### 4. Mobile FFI Integration (`src/mobile_ffi/`)

**Current State:**
```rust
// src/mobile_ffi/ffi.rs:1016
pub unsafe extern "C" fn arxos_save_ar_scan(
    json_data: *const c_char,
    building_name: *const c_char,
    confidence_threshold: f64,
) -> *mut c_char
```

**Modification Required:**

```rust
// src/mobile_ffi/ffi.rs

// MODIFY: Add user_email parameter
#[no_mangle]
pub unsafe extern "C" fn arxos_save_ar_scan(
    json_data: *const c_char,
    building_name: *const c_char,
    user_email: *const c_char,  // NEW: User email from mobile app
    confidence_threshold: f64,
) -> *mut c_char {
    // ... existing validation ...
    
    // Parse user_email (can be null for backward compatibility)
    let user_email_str = if user_email.is_null() {
        // Fallback to config
        crate::config::get_config_or_default().user.email.clone()
    } else {
        match CStr::from_ptr(user_email).to_str() {
            Ok(s) => s.to_string(),
            Err(_) => crate::config::get_config_or_default().user.email.clone(),
        }
    };
    
    // ... existing AR scan processing ...
    
    // MODIFY: Use save_and_commit_with_user instead of save_and_commit
    let persistence_manager = PersistenceManager::new(building_str)?;
    let commit_message = format!("Add equipment via AR scan: {}", equipment_name);
    
    let commit_id = persistence_manager.save_and_commit_with_user(
        &building_data,
        Some(&commit_message),
        Some(&user_email_str),  // Pass user email
    )?;
    
    // ... rest of function ...
}

// Apply same pattern to:
// - arxos_confirm_pending_equipment()
// - Any other FFI functions that create commits
```

**JNI Wrapper (`src/mobile_ffi/jni.rs`):**

```rust
// src/mobile_ffi/jni.rs

// MODIFY: Add user_email parameter
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeSaveARScan(
    mut env: JNIEnv,
    _class: JClass,
    json_data: JString,
    building_name: JString,
    user_email: JString,  // NEW
    confidence_threshold: f64
) -> jstring {
    // Extract user_email
    let user_email_str = java_string_to_rust(&env, user_email);
    
    // Call C FFI function
    let json_str = java_string_to_rust(&env, json_data);
    let building_str = java_string_to_rust(&env, building_name);
    
    let json_cstr = CString::new(json_str).unwrap();
    let building_cstr = CString::new(building_str).unwrap();
    let email_cstr = CString::new(user_email_str).unwrap();
    
    let result = arxos_save_ar_scan(
        json_cstr.as_ptr(),
        building_cstr.as_ptr(),
        email_cstr.as_ptr(),  // NEW
        confidence_threshold
    );
    
    // ... rest of function ...
}
```

**Mobile App Updates:**
- **iOS**: `ios/ArxOSMobile/ArxOSMobile/Services/ArxOSCoreFFI.swift`
  - Add `userEmail` parameter to `saveARScan()` method
  - Get email from UserDefaults or app settings
  
- **Android**: `android/app/src/main/java/com/arxos/mobile/service/ArxOSCoreService.kt`
  - Add `userEmail` parameter to JNI wrapper
  - Get email from SharedPreferences or app settings

---

### 5. Command Handlers (`src/commands/`)

#### 5.1 User Management Commands (`src/commands/users.rs`) - NEW

```rust
// src/commands/users.rs

use crate::identity::{UserRegistry, User};
use crate::git::find_git_repository;

/// Handle users add command
pub fn handle_users_add(
    name: String,
    email: String,
    organization: Option<String>,
    phone: Option<String>,
    verify: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let repo_path = find_git_repository()?
        .ok_or("Not in a Git repository")?;
    
    let mut registry = UserRegistry::load(&repo_path)?;
    
    // Create new user
    let user = User {
        id: generate_user_id(),  // UUID
        email,
        name,
        organization,
        phone,
        verified: verify,
        verified_by: if verify { Some(get_current_user_email()) } else { None },
        verified_at: if verify { Some(Utc::now()) } else { None },
        public_key_fingerprint: None,
        status: UserStatus::Active,
        added_at: Utc::now(),
        last_active: None,
        metadata: HashMap::new(),
    };
    
    registry.add_user(user)?;
    registry.save()?;
    
    // Stage users.yaml to Git
    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut git_manager = BuildingGitManager::new(&repo_path, "Building", config)?;
    git_manager.stage_file("users.yaml")?;
    
    println!("✅ User added to registry");
    Ok(())
}

/// Handle users list command
pub fn handle_users_list() -> Result<(), Box<dyn std::error::Error>> {
    let repo_path = find_git_repository()?
        .ok_or("Not in a Git repository")?;
    
    let registry = UserRegistry::load(&repo_path)?;
    
    println!("📋 Registered Users:");
    for user in &registry.users {
        println!("  • {} <{}>", user.name, user.email);
        if let Some(ref org) = user.organization {
            println!("    Organization: {}", org);
        }
        println!("    Status: {:?}", user.status);
        println!("    Verified: {}", if user.verified { "✅" } else { "❌" });
    }
    
    Ok(())
}

/// Handle users verify command
pub fn handle_users_verify(email: String) -> Result<(), Box<dyn std::error::Error>> {
    let repo_path = find_git_repository()?
        .ok_or("Not in a Git repository")?;
    
    let mut registry = UserRegistry::load(&repo_path)?;
    registry.verify_user_by_email(&email, &get_current_user_email())?;
    registry.save()?;
    
    println!("✅ User verified");
    Ok(())
}
```

**CLI Integration (`src/cli/mod.rs`):**

```rust
// src/cli/mod.rs

#[derive(Subcommand)]
pub enum Commands {
    // ... existing commands ...
    
    /// User management commands
    Users {
        #[command(subcommand)]
        subcommand: UsersCommands,
    },
}

#[derive(Subcommand)]
pub enum UsersCommands {
    /// Add user to registry
    Add {
        #[arg(long)]
        name: String,
        #[arg(long)]
        email: String,
        #[arg(long)]
        organization: Option<String>,
        #[arg(long)]
        phone: Option<String>,
        #[arg(long)]
        verify: bool,
    },
    /// List registered users
    List,
    /// Verify a user
    Verify {
        #[arg(long)]
        email: String,
    },
    /// Show user details
    Show {
        #[arg(long)]
        email: String,
    },
}
```

**Command Router (`src/commands/mod.rs`):**

```rust
// src/commands/mod.rs

pub mod users;  // NEW

match command {
    // ... existing commands ...
    Commands::Users { subcommand } => {
        users::handle_users_command(subcommand)
    },
}
```

---

#### 5.2 Git History Display (`src/commands/git_ops.rs`)

**Current State:**
```rust
// Line 111: display_commit_history() shows commits
display_commit_history(&commits, verbose)?;
```

**Modification Required:**

```rust
// src/commands/git_ops.rs

use crate::identity::UserRegistry;

/// Display commit history with user info
fn display_commit_history_with_users(
    commits: &[CommitInfo],
    verbose: bool,
    registry: Option<&UserRegistry>,
) -> Result<(), Box<dyn std::error::Error>> {
    for commit in commits {
        println!("📝 {}", commit.message);
        println!("   Author: {}", commit.author);
        
        // Extract user_id from commit message (Git trailers)
        if let Some(user_id) = extract_user_id_from_commit(&commit.message) {
            if let Some(registry) = registry {
                if let Some(user) = registry.find_by_id(&user_id) {
                    println!("   👤 User: {} ({})", user.name, user.email);
                    if let Some(ref org) = user.organization {
                        println!("   🏢 Organization: {}", org);
                    }
                    if user.verified {
                        println!("   ✅ Verified");
                    }
                }
            }
        }
        
        println!("   ⏰ {}", format_timestamp(commit.time));
        println!();
    }
    Ok(())
}

fn extract_user_id_from_commit(message: &str) -> Option<String> {
    // Parse Git trailers: "ArxOS-User-ID: usr_..."
    for line in message.lines() {
        if line.starts_with("ArxOS-User-ID:") {
            return Some(line[15..].trim().to_string());
        }
    }
    None
}

/// Handle history command - MODIFY
pub fn handle_history(limit: usize, verbose: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    // ... existing code ...
    
    // Load user registry
    let registry = UserRegistry::load(&repo_path).ok();
    
    // Display with user info
    display_commit_history_with_users(&commits, verbose, registry.as_ref())?;
    
    Ok(())
}
```

---

### 6. TUI Display (`src/ui/` and `src/commands/watch.rs`)

**Modification Required:**

```rust
// src/commands/watch.rs

use crate::identity::UserRegistry;

/// Enhance watch dashboard to show user attribution
pub fn render_user_info_in_watch(registry: &UserRegistry, commit_author: &str) -> String {
    // Extract email from Git author string: "Name <email@example.com>"
    if let Some(email) = extract_email_from_author(commit_author) {
        if let Some(user) = registry.find_by_email(&email) {
            format!(
                "👤 {} ({})\n   🏢 {}\n   {}",
                user.name,
                user.email,
                user.organization.as_ref().unwrap_or(&"Unknown".to_string()),
                if user.verified { "✅ Verified" } else { "⚠️ Unverified" }
            )
        }
    }
    
    format!("👤 Unknown User: {}", commit_author)
}
```

---

## File Locations Summary

### New Files to Create

1. **`src/identity/mod.rs`** - Module exports
2. **`src/identity/user.rs`** - User data structures
3. **`src/identity/registry.rs`** - UserRegistry implementation
4. **`src/commands/users.rs`** - User management CLI commands
5. **`src/ui/users.rs`** - User UI components (Phase 4)

### Files to Modify

1. **`src/git/manager.rs`** - Add `CommitMetadata` and enhanced commit methods
2. **`src/persistence/mod.rs`** - Add `save_and_commit_with_user()`
3. **`src/mobile_ffi/ffi.rs`** - Add `user_email` parameter to commit-making functions
4. **`src/mobile_ffi/jni.rs`** - Add `user_email` parameter to JNI wrappers
5. **`src/commands/git_ops.rs`** - Display user info in history
6. **`src/commands/watch.rs`** - Show user attribution in watch dashboard
7. **`src/cli/mod.rs`** - Add `Users` subcommand
8. **`src/commands/mod.rs`** - Route `Users` commands
9. **`src/lib.rs`** - Export identity module

### Repository Files (Version Controlled in Git)

1. **`users.yaml`** - User registry (in building repository root)
2. **`pending-users.yaml`** - Pending user requests (Phase 2)

---

## Integration Flow

### Commit Flow (Mobile AR Scan Example)

```
1. Mobile App (iOS/Android)
   ↓ (user_email parameter)
2. FFI: arxos_save_ar_scan(user_email, ...)
   ↓
3. PersistenceManager::save_and_commit_with_user(user_email, ...)
   ↓
4. UserRegistry::load() → find_by_email(user_email)
   ↓
5. BuildingGitManager::commit_staged_with_user(CommitMetadata { user_id, ... })
   ↓
6. Git commit with "ArxOS-User-ID: usr_..." trailer
   ↓
7. Commit synced to repository
```

### Display Flow (History Command Example)

```
1. CLI: arx history
   ↓
2. BuildingGitManager::list_commits()
   ↓
3. UserRegistry::load() → parse commits
   ↓
4. Extract "ArxOS-User-ID" from commit message
   ↓
5. UserRegistry::find_by_id(user_id)
   ↓
6. Display: "By: John Smith (ABC Contractors) ✅ Verified"
```

---

## Testing Strategy

### Unit Tests

- **`tests/identity/`** - New test directory
  - `user_tests.rs` - User data structure tests
  - `registry_tests.rs` - UserRegistry load/save/find tests

### Integration Tests

- **`tests/identity/identity_integration_tests.rs`**
  - Full cycle: Add user → Commit with user_id → Display user info
  - Mobile FFI → Registry lookup → Commit attribution

### Command Tests

- **`tests/commands/users_tests.rs`**
  - Test `arx users add`, `list`, `verify` commands

---

## Migration Path

### Phase 0: Backward Compatibility

- Keep existing `save_and_commit()` method
- Add `save_and_commit_with_user()` as new method
- Existing code continues to work (uses config email)

### Phase 1: New Code Uses Registry

- Mobile FFI updated to pass `user_email`
- New commits include `user_id` in trailers
- History display enhanced to show user info

### Phase 2: Retroactive Tagging

- Add `arx users tag-commit <hash> <user-id>` command
- Admins can retroactively tag historical commits
- Bulk tagging by email pattern: `arx users tag-by-email <email> <user-id>`

---

## Next Steps

1. **Review this implementation map**
2. **Create `src/identity/` module structure**
3. **Implement Phase 1 (User Registry)**
4. **Update Git commit methods**
5. **Update Mobile FFI**
6. **Add CLI commands**
7. **Test integration**

---

## Notes

- All identity data stored in Git (Git-native philosophy)
- No database dependencies
- Backward compatible with existing commits
- User registry is per-building (stored in building repo)
- Email is primary lookup key (with UUID for uniqueness)

