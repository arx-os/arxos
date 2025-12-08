# Mobile Signup & Git Configuration Workflow _(Archived)_

> **Status (November 2025):** Native mobile onboarding is paused. The workflow described below applies only to the archived clients.

**Last Updated:** January 2025  
**Status:** Design Documentation  
**Target Users:** Low-tech-skill users (tradesworkers, construction, etc.)

---

## Overview

ArxOS mobile app requires zero terminal knowledge for users. The app automatically configures Git credentials from a simple one-time signup form, enabling complete tracking of who made which changes to building data.

---

## Problem Statement

**Challenge:**
- Target users are tradesworkers, construction workers, facility managers
- Typically low-tech-skill with no Git/terminal knowledge
- Need to track contributions (who added/modified equipment, rooms, etc.)
- Must be simple "one-time setup" then "just works"

**Solution:**
- Simple mobile signup form (name, email, company)
- Store credentials locally on device
- Automatically use them for all Git commits
- Zero terminal knowledge required

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile User Signup                        │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Onboarding View                                       │  │
│  │                                                         │  │
│  │  Name:  [John Smith                    ]               │  │
│  │  Email: [john@construction.com         ]               │  │
│  │  Company: [ABC Contractors             ]               │  │
│  │                                                         │  │
│  │            [ Continue ]                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│                           ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Store in UserDefaults                                │  │
│  │  - git.name = "John Smith"                            │  │
│  │  - git.email = "john@construction.com"                │  │
│  │  - git.company = "ABC Contractors"                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│                           ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  User scans room with AR                              │  │
│  │  → Detects equipment                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│                           ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Rust FFI creates Git commit                         │  │
│  │                                                         │  │
│  │  Author: John Smith <john@construction.com>           │  │
│  │  Message: "Add equipment via AR scan"                  │  │
│  │  Files: building.yaml                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│                           ↓                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Git history shows:                                   │  │
│  │                                                         │  │
│  │  $ git log                                             │  │
│  │  2024-01-15 14:30:23                                   │  │
│  │  Author: John Smith <john@construction.com>           │  │
│  │  "Add VAV-01-A to Room 101"                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## User Experience

### First Time Setup (One Time Only)

When the user first opens the mobile app:

1. **Shows onboarding screen:**
   - Welcome message
   - Simple form with 3 fields:
     - Name (required)
     - Email (required)
     - Company (optional)
   - "Continue" button

2. **User enters info and taps Continue**

3. **App:**
   - Stores data locally (UserDefaults)
   - Configures Git credentials automatically
   - Shows "Setup complete"

4. **User never sees this again**

### Daily Usage (After Setup)

User simply:
1. Opens app
2. Scans room with AR
3. Adds equipment
4. **That's it**

App handles Git commits automatically with their stored credentials.

---

## Implementation Details

### Swift/iOS Side

#### 1. User Profile Storage

```swift
// File: ios/ArxOSMobile/ArxOSMobile/Models/UserProfile.swift

import Foundation

struct UserProfile: Codable {
    var name: String
    var email: String
    var company: String?
    
    init(name: String, email: String, company: String? = nil) {
        self.name = name
        self.email = email
        self.company = company
    }
    
    /// Load profile from UserDefaults
    static func load() -> UserProfile? {
        guard let data = UserDefaults.standard.data(forKey: "arxos_user_profile"),
              let profile = try? JSONDecoder().decode(UserProfile.self, from: data) else {
            return nil
        }
        return profile
    }
    
    /// Save profile to UserDefaults
    func save() {
        if let data = try? JSONEncoder().encode(self) {
            UserDefaults.standard.set(data, forKey: "arxos_user_profile")
        }
    }
    
    /// Check if onboarding is needed
    static func needsOnboarding() -> Bool {
        return UserProfile.load() == nil
    }
}
```

#### 2. Onboarding View

```swift
// File: ios/ArxOSMobile/ArxOSMobile/Views/OnboardingView.swift

import SwiftUI

struct OnboardingView: View {
    @State private var name: String = ""
    @State private var email: String = ""
    @State private var company: String = ""
    @State private var showingValidationError = false
    @Environment(\.dismiss) var dismiss
    
    var isFormValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty &&
        !email.trimmingCharacters(in: .whitespaces).isEmpty &&
        email.contains("@") && email.contains(".")
    }
    
    var body: some View {
        VStack(spacing: 24) {
            // Header
            VStack(spacing: 8) {
                Image(systemName: "building.2")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)
                
                Text("Welcome to ArxOS")
                    .font(.title)
                    .bold()
                
                Text("Let's get you set up")
                    .foregroundColor(.secondary)
                    .font(.subheadline)
            }
            .padding(.top, 40)
            
            // Form
            VStack(spacing: 16) {
                TextField("Your Name", text: $name)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.words)
                
                TextField("Your Email", text: $email)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)
                
                TextField("Company (Optional)", text: $company)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.words)
            }
            .padding(.horizontal)
            
            if showingValidationError {
                Text("Please enter a valid name and email")
                    .foregroundColor(.red)
                    .font(.caption)
            }
            
            // Continue Button
            Button(action: handleSignup) {
                Text("Continue")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isFormValid ? Color.blue : Color.gray)
                    .cornerRadius(8)
            }
            .disabled(!isFormValid)
            .padding(.horizontal)
            
            Spacer()
        }
        .padding()
    }
    
    private func handleSignup() {
        guard isFormValid else {
            showingValidationError = true
            return
        }
        
        // Save profile
        let profile = UserProfile(
            name: name.trimmingCharacters(in: .whitespaces),
            email: email.trimmingCharacters(in: .whitespaces),
            company: company.isEmpty ? nil : company.trimmingCharacters(in: .whitespaces)
        )
        profile.save()
        
        // Configure Git via FFI
        configureGitCredentials(name: profile.name, email: profile.email)
        
        // Dismiss onboarding
        dismiss()
    }
    
    private func configureGitCredentials(name: String, email: String) {
        // TODO: Implement FFI call to Rust
        // arxos_set_git_credentials(name, email: email)
        
        // For now, log to console
        print("Configuring Git: \(name) <\(email)>")
    }
}
```

#### 3. Update App Entry Point

```swift
// In ContentView.swift or App struct

@main
struct ArxOSMobileApp: App {
    @StateObject private var userProfile = UserProfileManager.shared
    
    var body: some Scene {
        WindowGroup {
            if UserProfile.needsOnboarding() {
                OnboardingView()
            } else {
                MainTabView()
            }
        }
    }
}
```

### Rust/FFI Side

#### 1. Add FFI Function to Set Git Credentials

```rust
// Add to crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs

/// Configure Git user credentials for this app session
/// 
/// # Safety
/// Both name and email must be valid UTF-8 null-terminated strings
#[no_mangle]
pub unsafe extern "C" fn arxos_set_git_credentials(
    name: *const c_char,
    email: *const c_char
) -> i32 {
    if name.is_null() || email.is_null() {
        warn!("arxos_set_git_credentials: null pointer");
        return ArxOSErrorCode::InvalidData as i32;
    }
    
    let name_str = match CStr::from_ptr(name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_set_git_credentials: invalid UTF-8 in name");
            return ArxOSErrorCode::InvalidData as i32;
        }
    };
    
    let email_str = match CStr::from_ptr(email).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_set_git_credentials: invalid UTF-8 in email");
            return ArxOSErrorCode::InvalidData as i32;
        }
    };
    
    // Store in thread-local or global state
    // This will be used for subsequent Git operations
    let git_config = crate::git::GitConfig {
        author_name: name_str.to_string(),
        author_email: email_str.to_string(),
        branch: "main".to_string(),
        remote_url: None,
    };
    
    // TODO: Store in thread-local storage or app context
    // For now, log to info
    info!("Git credentials configured: {} <{}>", name_str, email_str);
    
    ArxOSErrorCode::Success as i32
}

/// Get the configured Git user name
#[no_mangle]
pub extern "C" fn arxos_get_git_user_name() -> *mut c_char {
    // TODO: Read from stored state or UserDefaults
    // For now, return empty
    CString::new("").unwrap().into_raw()
}

/// Get the configured Git user email
#[no_mangle]
pub extern "C" fn arxos_get_git_user_email() -> *mut c_char {
    // TODO: Read from stored state or UserDefaults
    // For now, return empty
    CString::new("").unwrap().into_raw()
}
```

#### 2. Update BuildingGitManager to Use Stored Config

```rust
// Modify src/git/manager.rs

pub struct BuildingGitManager {
    repo: Repository,
    serializer: BuildingYamlSerializer,
    path_generator: PathGenerator,
    git_config: GitConfig,  // ← Store the config
}

impl BuildingGitManager {
    pub fn new(repo_path: &str, building_name: &str, config: GitConfig) -> Result<Self, GitError> {
        // ... existing code ...
        
        Ok(Self {
            repo,
            serializer,
            path_generator,
            git_config: config,  // ← Store it
        })
    }
    
    // Modify commit functions to use stored config
    fn commit_changes(&self, message: &str, file_paths: &[String]) -> Result<String, GitError> {
        // ... existing code ...
        
        // Use stored config instead of hardcoded values
        let signature = Signature::now(
            &self.git_config.author_name,
            &self.git_config.author_email
        )?;
        
        // ... rest of commit logic ...
    }
    
    pub fn commit_staged(&mut self, message: &str) -> Result<String, GitError> {
        // ... existing code ...
        
        let signature = Signature::now(
            &self.git_config.author_name,
            &self.git_config.author_email
        )?;
        
        // ... rest of commit logic ...
    }
}
```

#### 3. Thread-Local Storage for Git Config

For a cleaner implementation, store Git config in thread-local or app context:

```rust
// Add to crates/arxos/crates/arxos/src/mobile_ffi/mod.rs

use std::sync::Mutex;
use crate::git::GitConfig;

lazy_static! {
    static ref MOBILE_GIT_CONFIG: Mutex<Option<GitConfig>> = Mutex::new(None);
}

pub fn set_mobile_git_config(config: GitConfig) {
    *MOBILE_GIT_CONFIG.lock().unwrap() = Some(config);
}

pub fn get_mobile_git_config() -> Option<GitConfig> {
    MOBILE_GIT_CONFIG.lock().unwrap().clone()
}

pub fn get_mobile_git_config_or_default() -> GitConfig {
    MOBILE_GIT_CONFIG.lock().unwrap().clone().unwrap_or_else(|| {
        GitConfig {
            author_name: "Mobile User".to_string(),
            author_email: "mobile@arxos.io".to_string(),
            branch: "main".to_string(),
            remote_url: None,
        }
    })
}
```

Then update FFI function:

```rust
#[no_mangle]
pub unsafe extern "C" fn arxos_set_git_credentials(
    name: *const c_char,
    email: *const c_char
) -> i32 {
    // ... validation code ...
    
    let git_config = crate::git::GitConfig {
        author_name: name_str.to_string(),
        author_email: email_str.to_string(),
        branch: "main".to_string(),
        remote_url: None,
    };
    
    // Store in global state
    crate::mobile_ffi::set_mobile_git_config(git_config);
    
    info!("Git credentials configured: {} <{}>", name_str, email_str);
    ArxOSErrorCode::Success as i32
}
```

---

## Workflow Examples

### Example 1: First Time User

```
1. User installs app
2. Opens app → Shows OnboardingView
3. Enters: "John Smith", "john@abc.com", "ABC Contractors"
4. Taps Continue
5. App saves to UserDefaults
6. App configures Git via FFI
7. Onboarding dismissed
8. User navigates to main app
```

### Example 2: AR Scan & Equipment Addition

```
1. User opens app (already configured)
2. Taps "Scan Room" button
3. Opens AR scanner
4. Detects: VAV-01-A equipment
5. Taps "Add to Building"
6. App calls Rust FFI: arxos_add_equipment()
7. Rust code:
   - Reads config from storage
   - Loads building data
   - Adds equipment
   - Creates Git commit with:
     Author: "John Smith <john@abc.com>"
     Message: "Add VAV-01-A via AR scan"
8. Data saved locally
9. User sees success message
```

### Example 3: Viewing Git History

Administrator or project manager can see who did what:

```bash
# On computer with building data
$ git log --format="%an <%ae> - %ad - %s" --date=short

John Smith <john@abc.com> - 2024-01-15 - Add VAV-01-A via AR scan
John Smith <john@abc.com> - 2024-01-15 - Update Room 101
Jane Doe <jane@xyz.com> - 2024-01-14 - Add lighting fixtures
John Smith <john@abc.com> - 2024-01-13 - Initial building import
```

---

## Security & Privacy

### What's Stored Locally

- Name, email, company (in UserDefaults/SQLite)
- Building data (in local Git repo)
- Git commit history

### Privacy Considerations

1. **No server required** - Everything local
2. **User control** - Can delete app data anytime
3. **Company control** - When pushing to shared repo, team sees attribution
4. **Audit trail** - Complete history for compliance

### Best Practices

1. **Validate email format** before saving
2. **Encrypt local storage** if needed (Keychain on iOS)
3. **User consent** - Show privacy policy during onboarding
4. **Allow editing** - Let users update their info later

---

## Implementation Checklist

### iOS/Swift
- [ ] Create `UserProfile` model with save/load
- [ ] Create `OnboardingView` UI
- [ ] Add onboarding check to app entry point
- [ ] Update app to show onboarding if needed
- [ ] Add validation (email format, required fields)
- [ ] Handle onboarding completion
- [ ] Add settings view to update profile

### Rust/FFI
- [ ] Add `arxos_set_git_credentials()` FFI function
- [ ] Add `arxos_get_git_user_name()` FFI function
- [ ] Add `arxos_get_git_user_email()` FFI function
- [ ] Implement thread-local storage for Git config
- [ ] Update `BuildingGitManager` to use stored config
- [ ] Replace hardcoded signatures with dynamic ones
- [ ] Add error handling for invalid credentials

### Testing
- [ ] Test first-time onboarding flow
- [ ] Test Git commit attribution (verify real name appears)
- [ ] Test offline mode (credentials still work)
- [ ] Test profile update flow
- [ ] Test multiple users on same device (if applicable)

### Documentation
- [ ] Add to user guide
- [ ] Add to developer guide
- [ ] Update architecture docs

---

## Future Enhancements

### Short-Term
1. **Profile editing** - Settings view to update name/email
2. **Avatar/photo** - Store user photo locally
3. **Multiple profiles** - Switch between user accounts

### Medium-Term
1. **Cloud sync** - Optional sync to ArxOS cloud
2. **Profile verification** - Email verification step
3. **Team assignments** - Assign users to projects

### Long-Term
1. **Biometric auth** - Use Face ID/Touch ID for access
2. **Role-based access** - Different permissions per user
3. **Analytics dashboard** - See all users' contributions

---

## Related Documentation

- [Mobile FFI Integration](./MOBILE_FFI_INTEGRATION.md) - FFI architecture
- [Architecture](./ARCHITECTURE.md) - System design
- [User Guide](./USER_GUIDE.md) - End-user documentation

---

**Next Steps:**
1. Implement basic onboarding in iOS app
2. Add FFI functions for Git configuration
3. Test end-to-end flow
4. Polish UI/UX
5. Add profile editing feature

