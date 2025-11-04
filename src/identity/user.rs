//! User data structures for identity registry

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;

/// User in the registry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    /// Unique UUID identifier (format: "usr_550e8400-e29b-41d4-a716-446655440000")
    pub id: String,
    
    /// Email address (primary lookup key, case-insensitive)
    pub email: String,
    
    /// Full name
    pub name: String,
    
    /// Organization (optional)
    pub organization: Option<String>,
    
    /// Role (optional)
    pub role: Option<String>,
    
    /// Phone number (optional for privacy - can be omitted from Git)
    pub phone: Option<String>,
    
    /// Whether user is verified by an admin
    pub verified: bool,
    
    /// Email of admin who verified this user
    pub verified_by: Option<String>,
    
    /// When user was verified
    pub verified_at: Option<DateTime<Utc>>,
    
    /// Permissions granted to this user (e.g., ["verify_users", "revoke_users"])
    #[serde(default)]
    pub permissions: Vec<String>,
    
    /// GPG key fingerprint (optional, Phase 3)
    pub public_key_fingerprint: Option<String>,
    
    /// Current status
    pub status: UserStatus,
    
    /// When user was added to registry
    pub added_at: DateTime<Utc>,
    
    /// Last active timestamp (updated on commits)
    pub last_active: Option<DateTime<Utc>>,
    
    /// Extensible metadata
    #[serde(default)]
    pub metadata: HashMap<String, String>,
}

/// User status in the registry
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum UserStatus {
    /// User is active
    Active,
    /// User is inactive
    Inactive,
    /// User access has been revoked
    Revoked,
}

/// User registry data structure (YAML format)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserRegistryData {
    /// Registry version
    pub version: String,
    
    /// List of users
    pub users: Vec<User>,
}

impl User {
    /// Create a new user with UUID
    pub fn new(
        email: String,
        name: String,
        organization: Option<String>,
        role: Option<String>,
        phone: Option<String>,
    ) -> Self {
        let id = format!("usr_{}", uuid::Uuid::new_v4());
        
        Self {
            id,
            email: email.to_lowercase(), // Normalize email
            name,
            organization,
            role,
            phone,
            verified: false,
            verified_by: None,
            verified_at: None,
            permissions: Vec::new(),
            public_key_fingerprint: None,
            status: UserStatus::Active,
            added_at: Utc::now(),
            last_active: None,
            metadata: HashMap::new(),
        }
    }
    
    /// Check if user has a specific permission
    pub fn has_permission(&self, permission: &str) -> bool {
        self.permissions.contains(&permission.to_string())
    }
    
    /// Grant a permission to user
    pub fn grant_permission(&mut self, permission: String) {
        if !self.permissions.contains(&permission) {
            self.permissions.push(permission);
        }
    }
    
    /// Revoke a permission from user
    pub fn revoke_permission(&mut self, permission: &str) {
        self.permissions.retain(|p| p != permission);
    }
    
    /// Update last active timestamp
    pub fn update_last_active(&mut self) {
        self.last_active = Some(Utc::now());
    }
}

impl Default for UserRegistryData {
    fn default() -> Self {
        Self {
            version: "1.0".to_string(),
            users: Vec::new(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_user_new() {
        let user = User::new(
            "test@example.com".to_string(),
            "Test User".to_string(),
            Some("Acme Corp".to_string()),
            Some("Engineer".to_string()),
            Some("555-1234".to_string()),
        );
        
        assert!(user.id.starts_with("usr_"));
        assert_eq!(user.email, "test@example.com");
        assert_eq!(user.name, "Test User");
        assert_eq!(user.organization, Some("Acme Corp".to_string()));
        assert_eq!(user.role, Some("Engineer".to_string()));
        assert_eq!(user.phone, Some("555-1234".to_string()));
        assert!(!user.verified);
        assert_eq!(user.status, UserStatus::Active);
        assert!(user.permissions.is_empty());
    }
    
    #[test]
    fn test_user_email_normalization() {
        let user = User::new(
            "Test@Example.COM".to_string(),
            "Test User".to_string(),
            None,
            None,
            None,
        );
        
        assert_eq!(user.email, "test@example.com");
    }
    
    #[test]
    fn test_user_has_permission() {
        let mut user = User::new(
            "test@example.com".to_string(),
            "Test User".to_string(),
            None,
            None,
            None,
        );
        
        assert!(!user.has_permission("verify_users"));
        
        user.grant_permission("verify_users".to_string());
        assert!(user.has_permission("verify_users"));
        
        user.grant_permission("revoke_users".to_string());
        assert!(user.has_permission("verify_users"));
        assert!(user.has_permission("revoke_users"));
    }
    
    #[test]
    fn test_user_grant_permission() {
        let mut user = User::new(
            "test@example.com".to_string(),
            "Test User".to_string(),
            None,
            None,
            None,
        );
        
        assert_eq!(user.permissions.len(), 0);
        
        user.grant_permission("verify_users".to_string());
        assert_eq!(user.permissions.len(), 1);
        assert!(user.permissions.contains(&"verify_users".to_string()));
        
        // Granting same permission twice should not duplicate
        user.grant_permission("verify_users".to_string());
        assert_eq!(user.permissions.len(), 1);
    }
    
    #[test]
    fn test_user_revoke_permission() {
        let mut user = User::new(
            "test@example.com".to_string(),
            "Test User".to_string(),
            None,
            None,
            None,
        );
        
        user.grant_permission("verify_users".to_string());
        user.grant_permission("revoke_users".to_string());
        assert_eq!(user.permissions.len(), 2);
        
        user.revoke_permission("verify_users");
        assert_eq!(user.permissions.len(), 1);
        assert!(!user.has_permission("verify_users"));
        assert!(user.has_permission("revoke_users"));
    }
    
    #[test]
    fn test_user_update_last_active() {
        let mut user = User::new(
            "test@example.com".to_string(),
            "Test User".to_string(),
            None,
            None,
            None,
        );
        
        assert!(user.last_active.is_none());
        
        user.update_last_active();
        assert!(user.last_active.is_some());
        
        let first_time = user.last_active.unwrap();
        std::thread::sleep(std::time::Duration::from_millis(10));
        user.update_last_active();
        
        assert!(user.last_active.unwrap() > first_time);
    }
    
    #[test]
    fn test_user_status_variants() {
        assert_eq!(UserStatus::Active, UserStatus::Active);
        assert_eq!(UserStatus::Inactive, UserStatus::Inactive);
        assert_eq!(UserStatus::Revoked, UserStatus::Revoked);
        assert_ne!(UserStatus::Active, UserStatus::Revoked);
    }
    
    #[test]
    fn test_user_registry_data_default() {
        let data = UserRegistryData::default();
        
        assert_eq!(data.version, "1.0");
        assert!(data.users.is_empty());
    }
    
    #[test]
    fn test_user_serialization() {
        let user = User::new(
            "test@example.com".to_string(),
            "Test User".to_string(),
            Some("Acme Corp".to_string()),
            None,
            None,
        );
        
        // Test serialization
        let json = serde_json::to_string(&user).unwrap();
        assert!(json.contains("test@example.com"));
        assert!(json.contains("Test User"));
        
        // Test deserialization
        let deserialized: User = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized.email, user.email);
        assert_eq!(deserialized.name, user.name);
    }
    
    #[test]
    fn test_user_status_serialization() {
        let status = UserStatus::Active;
        let json = serde_json::to_string(&status).unwrap();
        assert_eq!(json, "\"active\"");
        
        let deserialized: UserStatus = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized, UserStatus::Active);
    }
}

