//! User management commands for identity registry

use crate::cli::UsersCommands;
use crate::identity::{User, UserRegistry, PendingUserRegistry};
use crate::git::{GitConfigManager, BuildingGitManager};
use crate::commands::git_ops::find_git_repository;
use crate::identity::{is_gpg_available, get_key_fingerprint_for_email};
use crate::ui::handle_user_browser;
use chrono::Utc;

/// Handle users command
pub fn handle_users_command(subcommand: UsersCommands) -> Result<(), Box<dyn std::error::Error>> {
    match subcommand {
        UsersCommands::Add { name, email, organization, role, phone, verify } => {
            handle_users_add(name, email, organization, role, phone, verify)
        }
        UsersCommands::List => handle_users_list(),
        UsersCommands::Browse => handle_users_browse(),
        UsersCommands::Show { email } => handle_users_show(email),
        UsersCommands::Verify { email } => handle_users_verify(email),
        UsersCommands::Revoke { email } => handle_users_revoke(email),
        UsersCommands::Approve { email } => handle_users_approve(email),
        UsersCommands::Deny { email, reason } => handle_users_deny(email, reason),
        UsersCommands::Pending => handle_users_pending(),
    }
}

/// Handle users add command
fn handle_users_add(
    name: String,
    email: String,
    organization: Option<String>,
    role: Option<String>,
    phone: Option<String>,
    verify: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("➕ Adding user to registry");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load or create registry
    let mut registry = UserRegistry::load(repo_path)?;
    
    // Create new user
    let mut user = User::new(email.clone(), name, organization, role, phone);
    
    // Phase 3: Try to detect and store GPG fingerprint if available
    if is_gpg_available() {
        match get_key_fingerprint_for_email(&email) {
            Ok(fingerprint) => {
                user.public_key_fingerprint = Some(fingerprint.clone());
                println!("🔐 GPG key detected: {}", fingerprint);
            }
            Err(_) => {
                // GPG key not found for this email - that's okay, it's optional
                println!("💡 No GPG key found for {}. User can configure GPG later.", email);
            }
        }
    }
    
    // If verify flag is set, verify the user (Phase 1: Enforce permission check)
    if verify {
        let current_user_email = crate::config::get_config_or_default().user.email.clone();
        
        // Check permissions before allowing verification
        if !registry.has_permission(&current_user_email, "verify_users") {
            return Err(format!(
                "❌ Permission denied: You do not have permission to verify users.\n\
                💡 Only users with 'verify_users' permission can verify users during add.\n\
                📧 Your email: {}\n\
                💡 Use 'arx users add' without --verify flag, then have an admin verify the user.\n\
                💡 Or contact an admin to grant you this permission.",
                current_user_email
            ).into());
        }
        
        user.verified = true;
        user.verified_by = Some(current_user_email.clone());
        user.verified_at = Some(Utc::now());
        println!("✅ User will be verified by admin");
    }
    
    // Add user to registry
    registry.add_user(user.clone())?;
    
    // Save registry
    registry.save()?;
    
    // Stage users.yaml to Git
    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut git_manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
    git_manager.stage_file("users.yaml")?;
    
    println!("✅ User added: {} <{}>", user.name, user.email);
    if user.verified {
        println!("   Status: ✅ Verified");
    } else {
        println!("   Status: ⚠️  Unverified");
    }
    println!("💡 Stage and commit 'users.yaml' to save changes");
    
    Ok(())
}

/// Handle users list command
fn handle_users_list() -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Registered Users");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load registry
    let registry = UserRegistry::load(repo_path)?;
    
    let users = registry.all_users();
    
    if users.is_empty() {
        println!("📭 No users registered yet");
        println!("💡 Use 'arx users add' to add the first user");
        return Ok(());
    }
    
    println!("Found {} user(s):\n", users.len());
    
    for user in users {
        // Show verification badge prominently
        let verification_badge = if user.verified {
            "✅ Verified"
        } else {
            "⚠️  Unverified"
        };
        
        println!("{} {} <{}>", verification_badge, user.name, user.email);
        
        if let Some(ref org) = user.organization {
            println!("   🏢 Organization: {}", org);
        }
        if let Some(ref role) = user.role {
            println!("   💼 Role: {}", role);
        }
        println!("   Status: {:?}", user.status);
        if user.verified {
            if let Some(ref verified_by) = user.verified_by {
                println!("   Verified by: {}", verified_by);
            }
            if let Some(ref verified_at) = user.verified_at {
                println!("   Verified at: {}", verified_at.format("%Y-%m-%d %H:%M:%S UTC"));
            }
        }
        if !user.permissions.is_empty() {
            println!("   🔑 Permissions: {}", user.permissions.join(", "));
        }
        if let Some(ref last_active) = user.last_active {
            println!("   Last active: {}", last_active.format("%Y-%m-%d %H:%M:%S UTC"));
        }
        println!();
    }
    
    Ok(())
}

/// Handle users browse command (interactive TUI)
fn handle_users_browse() -> Result<(), Box<dyn std::error::Error>> {
    handle_user_browser()
}

/// Handle users show command
fn handle_users_show(email: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("👤 User Details");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load registry
    let registry = UserRegistry::load(repo_path)?;
    
    // Find user
    let user = registry.find_by_email(&email)
        .ok_or_else(|| format!("User not found: {}", email))?;
    
    println!("Name: {}", user.name);
    println!("Email: {}", user.email);
    println!("ID: {}", user.id);
    if let Some(ref org) = user.organization {
        println!("Organization: {}", org);
    }
    if let Some(ref role) = user.role {
        println!("Role: {}", role);
    }
    if let Some(ref phone) = user.phone {
        println!("Phone: {}", phone);
    }
    println!("Status: {:?}", user.status);
    println!("Verified: {}", if user.verified { "✅ Yes" } else { "❌ No" });
    if let Some(ref verified_by) = user.verified_by {
        println!("Verified by: {}", verified_by);
    }
    if let Some(ref verified_at) = user.verified_at {
        println!("Verified at: {}", verified_at.format("%Y-%m-%d %H:%M:%S UTC"));
    }
    if !user.permissions.is_empty() {
        println!("Permissions: {}", user.permissions.join(", "));
    }
    println!("Added: {}", user.added_at.format("%Y-%m-%d %H:%M:%S UTC"));
    if let Some(ref last_active) = user.last_active {
        println!("Last active: {}", last_active.format("%Y-%m-%d %H:%M:%S UTC"));
    }
    
    Ok(())
}

/// Handle users verify command
fn handle_users_verify(email: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("✅ Verifying user");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load registry
    let mut registry = UserRegistry::load(repo_path)?;
    
    // Get current user email
    let current_user_email = crate::config::get_config_or_default().user.email.clone();
    
    // Check permissions (Phase 1: Enforce permission check)
    if !registry.has_permission(&current_user_email, "verify_users") {
        return Err(format!(
            "❌ Permission denied: You do not have permission to verify users.\n\
            💡 Only users with 'verify_users' permission can verify other users.\n\
            📧 Your email: {}\n\
            💡 Contact an admin to grant you this permission.",
            current_user_email
        ).into());
    }
    
    // Verify user
    registry.verify_user_by_email(&email, &current_user_email)?;
    
    // Save registry
    registry.save()?;
    
    // Stage users.yaml to Git
    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut git_manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
    git_manager.stage_file("users.yaml")?;
    
    println!("✅ User verified: {}", email);
    println!("💡 Stage and commit 'users.yaml' to save changes");
    
    Ok(())
}

/// Handle users revoke command
fn handle_users_revoke(email: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("🚫 Revoking user access");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load registry
    let mut registry = UserRegistry::load(repo_path)?;
    
    // Get current user email
    let current_user_email = crate::config::get_config_or_default().user.email.clone();
    
    // Check permissions (Phase 1: Enforce permission check)
    if !registry.has_permission(&current_user_email, "revoke_users") {
        return Err(format!(
            "❌ Permission denied: You do not have permission to revoke users.\n\
            💡 Only users with 'revoke_users' permission can revoke user access.\n\
            📧 Your email: {}\n\
            💡 Contact an admin to grant you this permission.",
            current_user_email
        ).into());
    }
    
    // Revoke user
    registry.revoke_user_by_email(&email)?;
    
    // Save registry
    registry.save()?;
    
    // Stage users.yaml to Git
    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut git_manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
    git_manager.stage_file("users.yaml")?;
    
    println!("🚫 User access revoked: {}", email);
    println!("💡 Stage and commit 'users.yaml' to save changes");
    
    Ok(())
}

/// Handle users approve command
fn handle_users_approve(email: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("✅ Approving pending user request");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load registries
    let mut user_registry = UserRegistry::load(repo_path)?;
    let mut pending_registry = PendingUserRegistry::load(repo_path)?;
    
    // Get current user email
    let current_user_email = crate::config::get_config_or_default().user.email.clone();
    
    // Check permissions (admin only)
    if !user_registry.has_permission(&current_user_email, "verify_users") {
        return Err(format!(
            "❌ Permission denied: You do not have permission to approve users.\n\
            💡 Only users with 'verify_users' permission can approve registration requests.\n\
            📧 Your email: {}\n\
            💡 Contact an admin to grant you this permission.",
            current_user_email
        ).into());
    }
    
    // Find pending request
    let _pending_request = pending_registry.find_pending_by_email(&email)
        .ok_or_else(|| format!("Pending request not found for email: {}", email))?;
    
    // Approve the request
    let approved_request = pending_registry.approve_request(&email, &current_user_email)?;
    
    // Create user from approved request
    let new_user = User::new(
        approved_request.email.clone(),
        approved_request.name.clone(),
        approved_request.organization.clone(),
        approved_request.role.clone(),
        approved_request.phone.clone(),
    );
    
    // Add user to registry (already verified since admin approved)
    let mut verified_user = new_user;
    verified_user.verified = true;
    verified_user.verified_by = Some(current_user_email.clone());
    verified_user.verified_at = Some(Utc::now());
    
    user_registry.add_user(verified_user.clone())?;
    
    // Save both registries
    user_registry.save()?;
    pending_registry.save()?;
    
    // Stage both files to Git
    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut git_manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
    git_manager.stage_file("users.yaml")?;
    git_manager.stage_file("pending-users.yaml")?;
    
    println!("✅ User approved and added to registry: {} <{}>", verified_user.name, verified_user.email);
    println!("💡 Stage and commit changes to save");
    
    Ok(())
}

/// Handle users deny command
fn handle_users_deny(email: String, reason: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("❌ Denying pending user request");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load registries
    let user_registry = UserRegistry::load(repo_path)?;
    let mut pending_registry = PendingUserRegistry::load(repo_path)?;
    
    // Get current user email
    let current_user_email = crate::config::get_config_or_default().user.email.clone();
    
    // Check permissions (admin only)
    if !user_registry.has_permission(&current_user_email, "verify_users") {
        return Err(format!(
            "❌ Permission denied: You do not have permission to deny users.\n\
            💡 Only users with 'verify_users' permission can deny registration requests.\n\
            📧 Your email: {}\n\
            💡 Contact an admin to grant you this permission.",
            current_user_email
        ).into());
    }
    
    // Find pending request
    let _pending_request = pending_registry.find_pending_by_email(&email)
        .ok_or_else(|| format!("Pending request not found for email: {}", email))?;
    
    // Deny the request
    pending_registry.deny_request(&email, &current_user_email, reason.clone())?;
    
    // Save pending registry
    pending_registry.save()?;
    
    // Stage file to Git
    let config = GitConfigManager::load_from_arx_config_or_env();
    let mut git_manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
    git_manager.stage_file("pending-users.yaml")?;
    
    println!("❌ User request denied: {}", email);
    if let Some(ref reason) = reason {
        println!("   Reason: {}", reason);
    }
    println!("💡 Stage and commit changes to save");
    
    Ok(())
}

/// Handle users pending command
fn handle_users_pending() -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Pending User Registration Requests");
    println!("{}", "=".repeat(50));
    
    // Find Git repository
    let repo_path_str = find_git_repository()?
        .ok_or("Not in a Git repository. User registry must be in a Git repository.")?;
    let repo_path = std::path::Path::new(&repo_path_str);
    
    // Load pending registry
    let pending_registry = PendingUserRegistry::load(repo_path)?;
    
    let pending_requests = pending_registry.pending_requests();
    
    if pending_requests.is_empty() {
        println!("📭 No pending requests");
        return Ok(());
    }
    
    println!("Found {} pending request(s):\n", pending_requests.len());
    
    for request in pending_requests {
        println!("⏳ {} <{}>", request.name, request.email);
        if let Some(ref org) = request.organization {
            println!("   🏢 Organization: {}", org);
        }
        if let Some(ref role) = request.role {
            println!("   💼 Role: {}", role);
        }
        if let Some(ref device) = request.device_info {
            println!("   📱 Device: {}", device);
        }
        if let Some(ref app_version) = request.app_version {
            println!("   📦 App Version: {}", app_version);
        }
        println!("   📅 Requested: {}", request.requested_at.format("%Y-%m-%d %H:%M:%S UTC"));
        println!("   💡 Use 'arx users approve {}' to approve", request.email);
        println!("   💡 Use 'arx users deny {}' to deny", request.email);
        println!();
    }
    
    Ok(())
}

