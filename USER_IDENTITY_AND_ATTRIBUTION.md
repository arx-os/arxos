# User Identity & Attribution in Git-Native ArxOS

**Version:** 2.0  
**Date:** January 2025  
**Status:** Design Document (Updated with Recommendations)  
**Priority:** High - Critical for Production

---

## Executive Summary

ArxOS uses a **Git-native, database-free architecture** where all data changes are tracked via Git commits. This creates a challenge: **How do we know who is who?** When a mobile user scans equipment via AR, how does the facility manager in the TUI know who performed that scan?

**Current State:**
- User identity stored in local config files (`user.name`, `user.email`)
- Git commits include author name/email in commit metadata
- Mobile apps allow users to set their identity during onboarding
- TUI can view Git history showing author information

**The Problem:**
- No centralized user directory/verification
- No way to verify if "John Smith <john@example.com>" is actually John Smith
- Anyone can claim any name/email in their config
- Facility manager has no way to contact or verify users
- No authentication/authorization system

**Goal:**
Design identity and attribution solutions that maintain Git-native philosophy while providing:
1. User verification/authentication
2. Author attribution in commits
3. User discovery (who can see who else is working on the building)
4. Contact information for collaboration
5. No centralized database dependency

---

## Current Implementation

### User Identity Storage

```12:14:src/config/mod.rs
pub struct UserConfig {
    /// User's full name
    pub name: String,
    /// User's email address
    pub email: String,
```

Users configure their identity via:
1. **Config file** (`~/.arx/config.toml` or `arx.toml`)
2. **Environment variables** (`ARX_USER_NAME`, `ARX_USER_EMAIL`)
3. **Mobile app settings** (stored in UserDefaults, sent via FFI)

### Git Commit Attribution

```273:284:src/git/manager.rs
        // Create signature using configured Git author
        let signature = Signature::now(
            &self.git_config.author_name,
            &self.git_config.author_email,
        )?;

        // Create commit
        let commit_id = self.repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            message,
            &tree,
            &parent_commit.iter().collect::<Vec<_>>(),
        )?;
```

All commits use the configured user name/email as Git author information.

### Viewing Attribution in TUI

```359:404:src/commands/git_ops.rs
/// Handle history command - show commit history
pub fn handle_history(limit: usize, verbose: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("📚 ArxOS History");
    println!("{}", "=".repeat(50));
    
    // Check if we're in a Git repository
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        // Initialize Git manager
        let config = GitConfigManager::default_config();
        let manager = BuildingGitManager::new(&repo_path, "Building", config)?;
        
        // Get commit history
        let commits = if let Some(file_path) = file {
            // Show history for specific file
            println!("📄 File History: {}", file_path);
            println!("{}", "-".repeat(30));
            manager.get_file_history(&file_path)?
        } else {
            // Show general commit history
            println!("📊 Recent Commits (showing {}):", limit);
            println!("{}", "-".repeat(30));
            manager.list_commits(limit)?
        };
        
        if commits.is_empty() {
            println!("📭 No commits found");
            return Ok(());
        }
        
        // Display commits
        display_commit_history(&commits, verbose)?;
        
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}
```

The TUI shows author names/emails from Git commit history, but has no way to verify or get more information about those users.

---

## Problem Scenarios

### Scenario 1: Mobile User Scans Equipment

**What Happens:**
1. Mobile user "Jane Doe" opens AR scanner
2. App has configured: `name = "Jane Doe"`, `email = "jane@contractor.com"`
3. User scans equipment "HVAC-301"
4. App calls `arxos_save_ar_scan()` FFI
5. Rust creates Git commit: `"Add HVAC-301 via AR scan"` by `"Jane Doe <jane@contractor.com>"`
6. Commit synced to building repository

**Problem:**
- Facility manager sees commit by "Jane Doe" but:
  - Who is Jane Doe? Is she a contractor? Employee? Unauthorized user?
  - How to contact her?
  - Is she authorized to scan equipment?
  - Was that actually Jane, or someone using her phone?

### Scenario 2: Multiple Users Same Building

**What Happens:**
1. Building repo has commits from 5 different people
2. Facility manager runs `arx history` in TUI
3. Sees: "John Smith", "Jane Doe", "Mike Johnson", "Sarah Lee", "Bob Wilson"

**Problem:**
- No way to see:
  - Which users are active
  - Who works for which organization
  - Contact information
  - Role/permissions
  - Last active date

### Scenario 3: Unauthorized Access

**What Happens:**
1. Unauthorized person gets access to building repository
2. Configures `name = "Authorized Contractor"`, `email = "fake@example.com"`
3. Makes commits that look legitimate
4. Facility manager can't tell they're unauthorized

**Problem:**
- No verification system
- No way to revoke access
- No audit trail of who has access

---

## Proposed Solutions

### Solution 1: Git Commit Signatures (GPG) ⭐ **RECOMMENDED FOR ENTERPRISE**

**How It Works:**
- Users generate GPG key pairs
- Commits are cryptographically signed with GPG keys
- Public keys stored in Git repository
- Facility manager can verify commit authenticity

**Implementation:**
1. Add GPG key generation to mobile onboarding
2. Store public keys in `users/` directory in Git repo
3. Sign all commits with user's GPG key
4. TUI shows verification status next to commits
5. Add `arx verify-commits` command

**Pros:**
- Cryptographic proof of identity
- Works with Git-native architecture
- Industry standard (GitHub, GitLab use this)
- Can revoke keys
- No centralized database

**Cons:**
- More complex for non-technical users
- Requires key management
- Mobile GPG integration can be tricky

**Files to Create:**
- `src/identity/gpg.rs` - GPG signature handling
- `src/identity/keys.rs` - Key management
- `users/john-smith.pub` - Public keys in Git
- `src/commands/verify.rs` - Verification commands

---

### Solution 2: User Registry in Git (YAML) ⭐ **RECOMMENDED FOR MOST USERS**

**How It Works:**
- Create `users.yaml` file in building repository
- Admins add verified users to registry
- Commits reference user ID from registry
- TUI shows full user info from registry

**User Registry Format:**
```yaml
# users.yaml (version controlled in Git)
version: "1.0"
users:
  - id: "usr_550e8400-e29b-41d4-a716-446655440000"  # UUID for uniqueness
    email: "john.smith@abc-contractors.com"  # Primary lookup key
    name: "John Smith"
    organization: "ABC Contractors"
    role: "HVAC Technician"
    phone: null  # Optional for privacy (can be stored locally instead)
    verified: true
    verified_by: "facility_manager@building.com"  # Email of admin who verified
    verified_at: "2024-01-15T10:00:00Z"
    permissions:
      - "verify_users"  # Admin permissions
      - "revoke_users"
    public_key_fingerprint: null  # Optional GPG (Phase 3)
    status: "active"  # active, inactive, revoked
    added_at: "2024-01-10T08:00:00Z"
    last_active: "2024-01-20T14:30:00Z"
    
  - id: "usr_660f9511-f3ac-52e5-b827-557766551111"
    email: "jane.doe@xyz-services.com"
    name: "Jane Doe"
    organization: "XYZ Services"
    role: "AR Scanner"
    phone: null  # Optional
    verified: true
    verified_by: "facility_manager@building.com"
    verified_at: "2024-01-12T14:30:00Z"
    permissions: []  # No admin permissions
    status: "active"
    added_at: "2024-01-12T14:00:00Z"
    last_active: "2024-01-19T10:15:00Z"
```

**Key Design Decisions:**
- **UUID-based IDs**: `usr_550e8400-...` for global uniqueness (not `user_john_smith_001`)
- **Email as primary key**: Used for lookup (case-insensitive)
- **Phone optional**: Privacy consideration - can be stored locally or omitted from Git
- **Permissions system**: Explicit admin model from day one
- **Email can change**: User ID stays same, email updates

**Commit Enhancement:**
Use Git commit trailers (standard Git practice) instead of inline message:
```
feat: Add HVAC-301 via AR scan

ArxOS-User-ID: usr_660f9511-f3ac-52e5-b827-557766551111
ArxOS-Device-ID: device_abc123xyz789  # Phase 3
```

**Benefits of Git Trailers:**
- Standard Git practice (like `Signed-off-by:`, `Co-authored-by:`)
- Easy to parse programmatically
- Doesn't clutter commit message
- Can be extracted with `git interpret-trailers`

**TUI Display:**
```
┌─────────────────────────────────────────────────────────┐
│ Recent Changes                                           │
├─────────────────────────────────────────────────────────┤
│ 🔵 HVAC-301 added                                        │
│    By: Jane Doe (XYZ Services)                          │
│    📧 jane.doe@xyz-services.com                         │
│    📞 +1-555-0456                                        │
│    ⏰ 2 hours ago                                         │
│                                                          │
│ 🔵 VAV-205 status updated                                │
│    By: John Smith (ABC Contractors)                     │
│    📧 john.smith@abc-contractors.com                    │
│    ⏰ 5 hours ago                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
1. Create `src/identity/registry.rs` - User registry management
2. Create `src/commands/users.rs` - User management commands
3. Enhance commit to include user_id
4. TUI reads registry to display user info
5. Add `arx users add` / `arx users list` commands

**Pros:**
- Simple to understand
- Full contact information
- Can track organizations/roles
- Easy to revoke users (set status: revoked)
- No cryptography needed
- Works with existing Git workflow

**Cons:**
- Requires manual user registration
- Registry can get out of sync if users change emails
- No cryptographic proof (but can combine with GPG)

**Files to Create:**
- `src/identity/registry.rs` - Registry management
- `src/identity/user.rs` - User data structures
- `src/commands/users.rs` - User management CLI
- `users.yaml` - Registry file (in Git)

---

### Solution 3: Device-Based Identity

**How It Works:**
- Each device generates unique device ID (UUID)
- Device ID + user config creates compound identity
- Device registry in Git tracks devices
- Commits include device ID

**Identity Format:**
```
User: "Jane Doe <jane@example.com>"
Device: "device_abc123xyz789"
Identity: "jane@example.com:device_abc123xyz789"
```

**Implementation:**
1. Generate device ID on first app launch
2. Store device ID in mobile app UserDefaults
3. Include device ID in FFI calls
4. Create `devices.yaml` registry
5. Commits include both user and device info

**Pros:**
- Prevents identity spoofing (need access to device)
- Can track which device made which change
- Useful for security auditing

**Cons:**
- Doesn't solve "who is the person" problem
- Multiple users could use same device
- Device registry management overhead

**Best Used With:** Solution 2 (User Registry)

---

### Solution 4: Email Domain Verification

**How It Works:**
- Organization maintains `authorized-domains.yaml` in repo
- Only commits from verified email domains are trusted
- Admins can verify domains (e.g., "@abc-contractors.com")

**Authorized Domains:**
```yaml
# authorized-domains.yaml
domains:
  - domain: "abc-contractors.com"
    organization: "ABC Contractors"
    verified: true
    verified_by: "facility_manager@building.com"
    verified_at: "2024-01-10T08:00:00Z"
    
  - domain: "xyz-services.com"
    organization: "XYZ Services"
    verified: true
    verified_by: "facility_manager@building.com"
    verified_at: "2024-01-12T14:00:00Z"
```

**TUI Display:**
```
┌─────────────────────────────────────────────────────────┐
│ Commit by: john@abc-contractors.com                     │
│ ✅ Verified Organization: ABC Contractors                │
│ ⚠️  User not in registry (domain verified)              │
└─────────────────────────────────────────────────────────┘
```

**Pros:**
- Simple for organizations
- Automatic verification for known domains
- Good for contractor scenarios

**Cons:**
- Doesn't identify individual users
- Anyone with that email domain can commit
- Less granular than user registry

**Best Used With:** Solution 2 (User Registry) as fallback

---

## Recommended Hybrid Approach

**For Most Use Cases: Combine Solutions 1 + 2**

1. **User Registry (Solution 2)** for human-readable identity and contact info
2. **GPG Signatures (Solution 1)** for cryptographic verification (optional but recommended)
3. **Device IDs (Solution 3)** for security auditing
4. **Domain Verification (Solution 4)** as fallback for unregistered users

**Implementation Priority:**
1. **Phase 1**: User Registry (Solution 2) - Immediate need
2. **Phase 2**: GPG Signatures (Solution 1) - Enhanced security
3. **Phase 3**: Device IDs (Solution 3) - Audit trail
4. **Phase 4**: Domain Verification (Solution 4) - Convenience

---

## Implementation Plan

### Phase 0.5: Basic Registry (Week 1) - **SIMPLIFIED MVP**

**Goal:** Minimal viable user identity system (no verification yet)

**Tasks:**
1. Create `src/identity/registry.rs` with UserRegistry struct
2. Create `User` data structure (UUID ID, email primary key)
3. Create `users.yaml` schema
4. Add `arx users add` command (admin can add users)
5. Add `arx users list` command
6. Enhance Git commits to include `user_id` in trailers
7. Update TUI history to show user info from registry
8. Mobile FFI: Add `user_email` parameter to commit-making functions

**Key Simplifications:**
- No verification required initially (manual trust)
- No permissions check yet (all users can add users)
- Phone numbers optional (privacy consideration)
- Backward compatible (existing code continues to work)

**Files to Create:**
- `src/identity/mod.rs`
- `src/identity/registry.rs`
- `src/identity/user.rs`
- `src/commands/users.rs`
- `users.yaml` (in building repos)

**Files to Modify:**
- `src/git/manager.rs` - Add `CommitMetadata` and Git trailers support
- `src/persistence/mod.rs` - Add `save_and_commit_with_user()` method
- `src/mobile_ffi/ffi.rs` - Add `user_email` parameter
- `src/mobile_ffi/jni.rs` - Add `user_email` parameter
- `src/commands/git_ops.rs` - Display user info from registry
- `src/commands/watch.rs` - Show user attribution

### Phase 1: Verification & Permissions (Week 2)

**Goal:** Admin verification and permissions system

**Tasks:**
1. Add `permissions` field to User struct
2. Add `arx users verify` command (admin only)
3. Add `arx users revoke` command (admin only)
4. Check permissions before allowing user management
5. Bootstrap: First user in registry is self-verified admin
6. TUI shows verification badges

**Files to Modify:**
- `src/identity/user.rs` - Add permissions field
- `src/identity/registry.rs` - Add permission checking
- `src/commands/users.rs` - Add verify/revoke commands

---

### Phase 2: Mobile User Registration (Week 3)

**Goal:** Mobile users can register themselves (pending admin approval)

**Tasks:**
1. Add `arx users request` FFI function
2. Mobile app: "Request Access" flow
3. Creates `pending-users.yaml` with request
4. Admin reviews and approves via `arx users approve`
5. Mobile app checks registration status
6. Show registration status in mobile UI

**Files to Create:**
- `src/identity/pending.rs` - Pending user requests
- `pending-users.yaml` (in building repos)

**Files to Modify:**
- `src/mobile_ffi/ffi.rs` - Add registration request
- `ios/ArxOSMobile/...` - Add registration UI
- `android/app/src/main/java/...` - Add registration UI

---

### Phase 3: GPG Signatures (Week 4)

**Goal:** Cryptographic verification (optional but recommended)

**Tasks:**
1. Research GPG library for Rust (gpgme or sequoia)
2. Create `src/identity/gpg.rs` for key generation/signing
3. Mobile: Generate GPG key during onboarding
4. Store public keys in `users/` directory
5. Sign all commits with user's GPG key
6. Add `arx verify` command to check signatures
7. TUI shows verification badges

**Files to Create:**
- `src/identity/gpg.rs`
- `src/identity/keys.rs`
- `users/john-smith.pub` (public keys in Git)

**Files to Modify:**
- `src/git/manager.rs` - Sign commits
- `src/commands/git_ops.rs` - Verify signatures
- `src/mobile_ffi/ffi.rs` - Key generation

---

### Phase 4: Enhanced TUI Display (Week 5)

**Goal:** Beautiful user attribution in TUI

**Tasks:**
1. Enhance Ratatui watch dashboard to show user info
2. Add user lookup panel (`arx users show <email>`)
3. Add user activity timeline
4. Show organization grouping
5. Contact buttons (copy email/phone)

**Files to Modify:**
- `src/commands/watch.rs` - Enhanced user display
- `src/commands/users.rs` - TUI user browser
- `src/ui/users.rs` - User UI components (NEW)

---

## Technical Specifications

### User Registry Structure

```rust
// src/identity/user.rs
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,  // UUID: "usr_550e8400-e29b-41d4-a716-446655440000"
    pub email: String,  // Primary lookup key (case-insensitive)
    pub name: String,
    pub organization: Option<String>,
    pub role: Option<String>,
    pub phone: Option<String>,  // Optional for privacy (can be omitted from Git)
    pub verified: bool,
    pub verified_by: Option<String>,  // Email of admin who verified
    pub verified_at: Option<DateTime<Utc>>,
    pub permissions: Vec<String>,  // e.g., ["verify_users", "revoke_users"]
    pub public_key_fingerprint: Option<String>,  // GPG key fingerprint (Phase 3)
    pub status: UserStatus,
    pub added_at: DateTime<Utc>,
    pub last_active: Option<DateTime<Utc>>,
    pub metadata: HashMap<String, String>,  // Extensible
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
    pub version: String,  // "1.0"
    pub users: Vec<User>,
}
```

**Key Design Points:**
- **UUID-based IDs**: Globally unique, not dependent on name
- **Email as primary key**: Used for lookups (case-insensitive matching)
- **Phone optional**: Privacy consideration - can be stored locally or omitted
- **Permissions system**: Explicit admin model from Phase 1
- **Email can change**: User ID stays same, email can be updated

### Enhanced Commit Metadata

```rust
// src/git/manager.rs

#[derive(Debug, Clone)]
pub struct CommitMetadata {
    pub message: String,
    pub user_id: Option<String>,  // From registry (UUID)
    pub device_id: Option<String>,  // From mobile device (Phase 3)
    pub ar_scan_id: Option<String>,  // If from AR scan
    pub signature: Option<String>,  // GPG signature (Phase 3)
}

impl BuildingGitManager {
    /// Build commit message with Git trailers
    fn build_commit_message(&self, metadata: &CommitMetadata) -> Result<String, GitError> {
        let mut message = metadata.message.clone();
        
        // Add Git trailers (standard Git practice)
        if let Some(ref user_id) = metadata.user_id {
            message.push_str(&format!("\n\nArxOS-User-ID: {}", user_id));
        }
        
        if let Some(ref device_id) = metadata.device_id {
            message.push_str(&format!("\nArxOS-Device-ID: {}", device_id));
        }
        
        Ok(message)
    }
}
```

**Benefits:**
- Uses Git trailers (standard practice like `Signed-off-by:`)
- Easy to parse programmatically
- Doesn't clutter commit message
- Can be extracted with `git interpret-trailers`

### User Registry API

```rust
// src/identity/registry.rs
use std::path::{Path, PathBuf};

pub struct UserRegistry {
    users: Vec<User>,
    file_path: PathBuf,
    repo_path: PathBuf,
}

impl UserRegistry {
    /// Load registry from building repository
    pub fn load(repo_path: &Path) -> Result<Self, RegistryError>;
    
    /// Find user by email (primary lookup, case-insensitive)
    pub fn find_by_email(&self, email: &str) -> Option<&User>;
    
    /// Find user by ID (UUID)
    pub fn find_by_id(&self, id: &str) -> Option<&User>;
    
    /// Add new user (admin only in Phase 1)
    pub fn add_user(&mut self, user: User) -> Result<(), RegistryError>;
    
    /// Verify user (admin only)
    pub fn verify_user_by_email(&mut self, email: &str, verified_by: &str) -> Result<(), RegistryError>;
    
    /// Revoke user (admin only)
    pub fn revoke_user_by_email(&mut self, email: &str) -> Result<(), RegistryError>;
    
    /// Check if user has permission
    pub fn has_permission(&self, email: &str, permission: &str) -> bool;
    
    /// Save registry to file (stages to Git, doesn't commit)
    pub fn save(&self) -> Result<(), RegistryError>;
}
```

**Key Methods:**
- `find_by_email()`: Primary lookup method (case-insensitive)
- `has_permission()`: Check admin permissions (Phase 1)
- `save()`: Writes to `users.yaml`, stages to Git (caller decides when to commit)

---

## Migration Path

### For Existing Repositories

1. **Initial Setup (Bootstrap):**
   ```bash
   # First user creates initial registry (self-verified admin)
   arx users add --name "Facility Manager" \
                 --email "manager@building.com" \
                 --organization "Building Corp" \
                 --verify
   # First user is automatically granted admin permissions
   ```

2. **Existing Commits:**
   - Historical commits won't have `ArxOS-User-ID` trailer
   - TUI shows three-tier display:
     - **Verified users**: ✅ "John Smith (ABC Contractors) - Verified"
     - **Known users** (email in registry but not verified): ⚠️ "Jane Doe (XYZ Services) - Unverified"
     - **Unknown users**: ❓ "Unknown User: someone@example.com"
   - Admin can retroactively tag: `arx users tag-commit <commit-hash> <user-id>`
   - Bulk tagging: `arx users tag-by-email <email> <user-id>`

3. **Mobile Users:**
   - **Phase 0.5**: Mobile FFI accepts `user_email` parameter (can be null for backward compatibility)
   - **Phase 2**: Mobile app prompts for registration, user requests access
   - Admin approves via `arx users approve <email>`
   - Future commits include `user_id` in trailers

### Backward Compatibility

- **Existing code continues to work**: `save_and_commit()` still exists, uses config email
- **New code uses**: `save_and_commit_with_user()` with explicit user email
- **Mobile FFI**: `user_email` parameter is optional (null = fallback to config)
- **Three-tier user model**:
  1. **Verified**: User in registry with `verified: true` → Full info displayed
  2. **Known**: User in registry but not verified → Info displayed with warning
  3. **Unknown**: Email not in registry → Shows email only with "Unknown User" label

---

## Security Considerations

### Without Database

**Threats:**
1. **Identity Spoofing**: User claims to be someone else
2. **Unauthorized Access**: Unauthorized person makes commits
3. **User Registry Tampering**: Someone edits `users.yaml` maliciously

**Mitigations:**
1. **GPG Signatures**: Cryptographic proof (Solution 1)
2. **Git Commit History**: All registry changes tracked in Git
3. **Admin Verification**: Only verified admins can add users
4. **Revocation**: Can revoke users by updating registry
5. **Audit Trail**: All registry changes in Git history

### Access Control

**Phase 0.5**: No access control (anyone with repo access can commit)
- **Reason**: Simplified MVP for faster implementation
- **Mitigation**: Admin verification system in Phase 1

**Phase 1**: Basic permissions system
- Users have `permissions` array (e.g., `["verify_users", "revoke_users"]`)
- Only users with `verify_users` permission can verify other users
- Only users with `revoke_users` permission can revoke users
- First user in registry is automatically granted admin permissions

**Future Enhancement (Post-Phase 4):**
- Role-based access control (`permissions.yaml`)
- Commits check permissions before allowing operations
- Mobile app checks permissions before operations
- Fine-grained permissions (e.g., `edit_equipment`, `view_sensors`)

---

## Success Criteria

✅ **Phase 0.5 Complete (MVP):**
- Admin can add users to registry
- Commits include `ArxOS-User-ID` trailer
- TUI shows user info from registry (three-tier display)
- Mobile FFI accepts `user_email` parameter
- Backward compatible (existing code continues to work)

✅ **Phase 1 Complete:**
- Admin verification system works
- Permissions system implemented
- First user is bootstrap admin
- TUI shows verification badges
- Users can be verified/revoked

✅ **Phase 2 Complete:**
- Mobile users can request access
- Admin can approve/deny requests
- Mobile app shows registration status
- Pending users workflow functional

✅ **Phase 3 Complete:**
- GPG key generation works on mobile
- Commits are cryptographically signed
- Verification works in TUI
- Public keys stored in Git

✅ **Production Ready:**
- Facility manager can see who made each change
- Can contact users via registry (email required, phone optional)
- Unauthorized users can be identified and revoked
- Full audit trail in Git history
- Three-tier user display (verified/known/unknown)
- Retroactive commit tagging available

---

## Open Questions

1. **Should user registry be per-building or global?**
   - **Recommendation:** Per-building (stored in building repo)
   - Allows different users per building
   - Simpler for multi-building organizations

2. **How to handle user email changes?**
   - Update registry when user changes email?
   - Link old email to new email?
   - **Recommendation:** User ID stays same, email can update

3. **What about anonymous/guest users?**
   - **Three-tier model**:
     1. **Verified users**: `verified: true` → Full info, ✅ badge
     2. **Known users**: Email in registry but `verified: false` → Info with ⚠️ warning
     3. **Unknown users**: Email not in registry → Shows email only with ❓ "Unknown User"
   - **Recommendation**: 
     - Mobile: Require registration (can't use app without user_email)
     - CLI: Allow anonymous with warning (uses config email, shows as "Unknown User")
     - TUI: Shows appropriate badge based on verification status

4. **Multi-organization support?**
   - Users can belong to multiple organizations?
   - **Recommendation:** One organization per user (can change over time)

---

## Mobile FFI Integration

### Current State

Mobile FFI functions currently don't pass user identity explicitly:
- `arxos_save_ar_scan()` - No user_email parameter
- Commits use global config (ArxConfig user.email)

### Required Changes

**FFI Signature Update:**
```rust
// src/mobile_ffi/ffi.rs

// BEFORE:
pub unsafe extern "C" fn arxos_save_ar_scan(
    json_data: *const c_char,
    building_name: *const c_char,
    confidence_threshold: f64,
) -> *mut c_char

// AFTER:
pub unsafe extern "C" fn arxos_save_ar_scan(
    json_data: *const c_char,
    building_name: *const c_char,
    user_email: *const c_char,  // NEW: Can be null for backward compatibility
    confidence_threshold: f64,
) -> *mut c_char
```

**Mobile App Updates:**
- **iOS**: `ArxOSCoreFFI.swift` - Add `userEmail` parameter, get from UserDefaults
- **Android**: `ArxOSCoreService.kt` - Add `userEmail` parameter, get from SharedPreferences
- Mobile app stores user email during onboarding/settings
- Pass email to all FFI functions that create commits

**Flow:**
1. Mobile app → Gets user email from app settings
2. Mobile app → Calls FFI with `user_email` parameter
3. Rust → Looks up user in registry by email
4. Rust → Includes `user_id` in commit trailers
5. Commit → Synced to repository with attribution

---

## Privacy Considerations

### Phone Numbers

**Decision**: Phone numbers are **optional** in user registry

**Rationale:**
- Phone numbers in Git history are permanent (can't be removed)
- Privacy regulations (GDPR, etc.) may require data minimization
- Not all users want phone numbers public
- Email is sufficient for contact

**Implementation:**
- `phone: Option<String>` in User struct
- Can be omitted from `users.yaml`
- Can be stored locally in mobile app instead
- Admin can add phone if needed, but not required

### Email Addresses

**Decision**: Email is required (primary lookup key)

**Rationale:**
- Email is standard for Git commits anyway
- Needed for contact and verification
- Less sensitive than phone numbers
- Already in Git commit history

---

## Conclusion

The **User Registry in Git (Solution 2)** provides the best balance of simplicity and functionality for most ArxOS deployments. Combined with **GPG Signatures (Solution 1)** for enhanced security, this creates a robust identity system that maintains Git-native architecture while solving the "who is who" problem.

**Key Improvements in v2.0:**
- ✅ UUID-based user IDs (globally unique)
- ✅ Email as primary lookup key
- ✅ Git commit trailers (standard practice)
- ✅ Explicit permissions system (Phase 1)
- ✅ Privacy-conscious (phone optional)
- ✅ Simplified MVP (Phase 0.5)
- ✅ Three-tier user model (verified/known/unknown)
- ✅ Mobile FFI integration details
- ✅ Backward compatibility maintained

**Next Steps:**
1. ✅ Review and approve this design (v2.0)
2. Implement Phase 0.5 (Basic Registry - MVP)
3. Test with real mobile users
4. Gather feedback
5. Iterate on design
6. Proceed with Phase 1+ as needed

**See Also:**
- `USER_IDENTITY_IMPLEMENTATION_MAP.md` - Detailed technical implementation guide
