use anyhow::{Context, Result};
use russh_keys::key::PublicKey;
use serde::Deserialize;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct Role {
    pub permissions: Vec<String>,
}

#[derive(Debug, Deserialize, Default, Clone)]
pub struct PermissionsConfig {
    pub roles: HashMap<String, Role>,
    pub users: HashMap<String, UserConfig>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct UserConfig {
    pub role: String,
}

pub struct SshAuthenticator {
    // Map of public key (base64) to username
    authorized_keys: HashMap<String, String>,
    permissions: PermissionsConfig,
}

impl SshAuthenticator {
    pub fn new(repo_root: &Path) -> Result<Self> {
        let mut authenticator = Self {
            authorized_keys: HashMap::new(),
            permissions: PermissionsConfig::default(),
        };
        
        // Load authorized keys
        let auth_keys_path = repo_root.join(".arxos/authorized_keys");
        if auth_keys_path.exists() {
            authenticator.load_authorized_keys(&auth_keys_path)
                .context("Failed to load authorized_keys")?;
        }

        // Load permissions
        let perm_path = repo_root.join(".arxos/permissions.yaml");
        if perm_path.exists() {
            authenticator.load_permissions(&perm_path)
                .context("Failed to load permissions.yaml")?;
        }
        
        Ok(authenticator)
    }

    fn load_authorized_keys(&mut self, path: &Path) -> Result<()> {
        let content = std::fs::read_to_string(path)?;
        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            // Format: ssh-rsa AAAAB3... user@host
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 {
                // Key data is commonly the second part
                let key_data = parts[1];
                let username = if parts.len() > 2 { parts[2] } else { "unknown" };
                self.authorized_keys.insert(key_data.to_string(), username.to_string());
            }
        }
        Ok(())
    }

    fn load_permissions(&mut self, path: &Path) -> Result<()> {
        let content = std::fs::read_to_string(path)?;
        self.permissions = serde_yaml::from_str(&content)?;
        Ok(())
    }

    /// Verify a public key and return the associated username if valid
    /// Note: This compares base64 representation of the key.
    pub fn verify_key(&self, _public_key: &PublicKey) -> Option<String> {
        // TODO: Implement proper key comparison using russh_keys
        // For now, we would need to convert the incoming PublicKey to base64 
        // string to match what we have in the authorized_keys file.
        // This is a simplified placeholder.
        
        // Real implementation would look something like:
        // let key_openssh = public_key.to_openssh_string(); ...
        
        None 
    }

    /// Check if a user has a specific permission
    pub fn check_permission(&self, _username: &str, _permission: &str) -> bool {
        // 1. Find role usage for the user? 
        // The users map matches identifier (key string often) to role.
        // Ideally we map username -> role if username is stable.
        
        // In permissions.yaml:
        // users:
        //   "ssh-rsa AAA...": { role: "admin" }
        // The key is the full public key line or just the key part?
        // The implementation plan example showed "ssh-rsa AAA...manager@laptop" as key.
        
        // Assuming we look up by username for now if we extracted it from authorized_keys
        // Or we might need to look up by the key itself.
        
        // Let's assume we pass the username that was resolved from verify_key
        false // Placeholder
    }
    
    pub fn get_user_role(&self, user_id: &str) -> Option<&String> {
        self.permissions.users.get(user_id).map(|u| &u.role)
    }
    
    pub fn get_role_permissions(&self, role_name: &str) -> Option<&Vec<String>> {
        self.permissions.roles.get(role_name).map(|r| &r.permissions)
    }
}
