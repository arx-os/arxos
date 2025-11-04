//! Pending user registration requests for mobile users
//!
//! This module manages user registration requests from mobile applications.
//! Requests are stored in `pending-users.yaml` and reviewed by admins.

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::path::{Path, PathBuf};
use std::collections::HashMap;
use log::{info, warn};
use thiserror::Error;

/// Status of a pending user request
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PendingRequestStatus {
    /// Request is pending admin review
    Pending,
    /// Request has been approved
    Approved,
    /// Request has been denied
    Denied,
}

/// A pending user registration request from a mobile application
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingUserRequest {
    /// Unique request ID (UUID format: "req_550e8400-e29b-41d4-a716-446655440000")
    pub id: String,
    
    /// User's email address (primary lookup key)
    pub email: String,
    
    /// User's full name
    pub name: String,
    
    /// Organization (optional)
    pub organization: Option<String>,
    
    /// Role (optional)
    pub role: Option<String>,
    
    /// Phone number (optional, for privacy)
    pub phone: Option<String>,
    
    /// Device information (optional, from mobile app)
    pub device_info: Option<String>,
    
    /// App version (optional, from mobile app)
    pub app_version: Option<String>,
    
    /// Current status of the request
    pub status: PendingRequestStatus,
    
    /// When the request was submitted
    pub requested_at: DateTime<Utc>,
    
    /// Admin who approved/denied (if applicable)
    pub reviewed_by: Option<String>,
    
    /// When the request was reviewed (if applicable)
    pub reviewed_at: Option<DateTime<Utc>>,
    
    /// Reason for denial (if denied)
    pub denial_reason: Option<String>,
    
    /// Extensible metadata
    #[serde(default)]
    pub metadata: HashMap<String, String>,
}

/// Pending user registry data structure (YAML format)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingUserRegistryData {
    /// Registry version
    pub version: String,
    
    /// List of pending requests
    pub requests: Vec<PendingUserRequest>,
}

/// Manages pending user registration requests
pub struct PendingUserRegistry {
    requests: Vec<PendingUserRequest>,
    file_path: PathBuf,
    repo_path: PathBuf,
}

/// Errors that can occur when working with pending user registry
#[derive(Error, Debug)]
pub enum PendingRegistryError {
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("YAML parsing error: {0}")]
    YamlError(#[from] serde_yaml::Error),
    
    #[error("Request not found: {0}")]
    RequestNotFound(String),
    
    #[error("Request already exists: {0}")]
    RequestExists(String),
    
    #[error("Invalid request ID format: {0}")]
    InvalidRequestId(String),
    
    #[error("Request already reviewed: {0}")]
    RequestAlreadyReviewed(String),
}

impl PendingUserRequest {
    /// Create a new pending user request
    pub fn new(
        email: String,
        name: String,
        organization: Option<String>,
        role: Option<String>,
        phone: Option<String>,
        device_info: Option<String>,
        app_version: Option<String>,
    ) -> Self {
        let id = format!("req_{}", uuid::Uuid::new_v4());
        
        Self {
            id,
            email: email.to_lowercase(), // Normalize email
            name,
            organization,
            role,
            phone,
            device_info,
            app_version,
            status: PendingRequestStatus::Pending,
            requested_at: Utc::now(),
            reviewed_by: None,
            reviewed_at: None,
            denial_reason: None,
            metadata: HashMap::new(),
        }
    }
}

impl Default for PendingUserRegistryData {
    fn default() -> Self {
        Self {
            version: "1.0".to_string(),
            requests: Vec::new(),
        }
    }
}

impl PendingUserRegistry {
    /// Load pending user registry from building repository
    ///
    /// Looks for `pending-users.yaml` in the repository root.
    /// If file doesn't exist, returns empty registry.
    pub fn load(repo_path: &Path) -> Result<Self, PendingRegistryError> {
        let repo_path_buf = repo_path.to_path_buf();
        let file_path = repo_path_buf.join("pending-users.yaml");
        
        if !file_path.exists() {
            info!("pending-users.yaml not found, creating empty registry");
            return Ok(Self {
                requests: Vec::new(),
                file_path,
                repo_path: repo_path_buf,
            });
        }
        
        let content = std::fs::read_to_string(&file_path)?;
        let data: PendingUserRegistryData = serde_yaml::from_str(&content)?;
        
        info!("Loaded {} pending requests from registry", data.requests.len());
        
        Ok(Self {
            requests: data.requests,
            file_path,
            repo_path: repo_path_buf,
        })
    }
    
    /// Add a new pending user request
    ///
    /// Returns an error if a request with the same email already exists and is pending.
    pub fn add_request(&mut self, request: PendingUserRequest) -> Result<(), PendingRegistryError> {
        // Check if a pending request with this email already exists
        if self.find_pending_by_email(&request.email).is_some() {
            return Err(PendingRegistryError::RequestExists(request.email));
        }
        
        // Validate request ID format
        if !request.id.starts_with("req_") {
            return Err(PendingRegistryError::InvalidRequestId(request.id));
        }
        
        self.requests.push(request);
        info!("Added pending user request: {}", self.requests.last().unwrap().email);
        
        Ok(())
    }
    
    /// Find pending request by email (case-insensitive)
    pub fn find_pending_by_email(&self, email: &str) -> Option<&PendingUserRequest> {
        let email_lower = email.to_lowercase();
        self.requests.iter()
            .find(|r| r.email.to_lowercase() == email_lower && r.status == PendingRequestStatus::Pending)
    }
    
    /// Find request by ID
    pub fn find_by_id(&self, id: &str) -> Option<&PendingUserRequest> {
        self.requests.iter().find(|r| r.id == id)
    }
    
    /// Find request by email (any status)
    pub fn find_by_email(&self, email: &str) -> Option<&PendingUserRequest> {
        let email_lower = email.to_lowercase();
        self.requests.iter()
            .find(|r| r.email.to_lowercase() == email_lower)
    }
    
    /// Get all pending requests
    pub fn pending_requests(&self) -> Vec<&PendingUserRequest> {
        self.requests.iter()
            .filter(|r| r.status == PendingRequestStatus::Pending)
            .collect()
    }
    
    /// Approve a pending request
    ///
    /// Marks the request as approved and records who approved it.
    pub fn approve_request(&mut self, email: &str, approved_by: &str) -> Result<PendingUserRequest, PendingRegistryError> {
        let request = self.requests.iter_mut()
            .find(|r| r.email.to_lowercase() == email.to_lowercase())
            .ok_or_else(|| PendingRegistryError::RequestNotFound(email.to_string()))?;
        
        if request.status != PendingRequestStatus::Pending {
            return Err(PendingRegistryError::RequestAlreadyReviewed(request.id.clone()));
        }
        
        request.status = PendingRequestStatus::Approved;
        request.reviewed_by = Some(approved_by.to_string());
        request.reviewed_at = Some(Utc::now());
        
        info!("Approved pending request: {} (by {})", email, approved_by);
        
        Ok(request.clone())
    }
    
    /// Deny a pending request
    ///
    /// Marks the request as denied and records who denied it and why.
    pub fn deny_request(&mut self, email: &str, denied_by: &str, reason: Option<String>) -> Result<(), PendingRegistryError> {
        let request = self.requests.iter_mut()
            .find(|r| r.email.to_lowercase() == email.to_lowercase())
            .ok_or_else(|| PendingRegistryError::RequestNotFound(email.to_string()))?;
        
        if request.status != PendingRequestStatus::Pending {
            return Err(PendingRegistryError::RequestAlreadyReviewed(request.id.clone()));
        }
        
        request.status = PendingRequestStatus::Denied;
        request.reviewed_by = Some(denied_by.to_string());
        request.reviewed_at = Some(Utc::now());
        request.denial_reason = reason;
        
        info!("Denied pending request: {} (by {})", email, denied_by);
        
        Ok(())
    }
    
    /// Save pending user registry to file
    ///
    /// Writes to `pending-users.yaml` but does not commit to Git.
    /// Caller should stage and commit the file separately.
    pub fn save(&self) -> Result<(), PendingRegistryError> {
        let data = PendingUserRegistryData {
            version: "1.0".to_string(),
            requests: self.requests.clone(),
        };
        
        let content = serde_yaml::to_string(&data)?;
        std::fs::write(&self.file_path, content)?;
        
        info!("Saved {} pending requests to registry", self.requests.len());
        Ok(())
    }
    
    /// Get the registry file path
    pub fn file_path(&self) -> &Path {
        &self.file_path
    }
    
    /// Get the repository path
    pub fn repo_path(&self) -> &Path {
        &self.repo_path
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    
    fn create_test_request(email: &str, name: &str) -> PendingUserRequest {
        PendingUserRequest::new(
            email.to_string(),
            name.to_string(),
            Some("Test Org".to_string()),
            Some("Engineer".to_string()),
            None,
            Some("iPhone 15 Pro".to_string()),
            Some("1.0.0".to_string()),
        )
    }
    
    #[test]
    fn test_pending_request_new() {
        let request = create_test_request("test@example.com", "Test User");
        
        assert!(request.id.starts_with("req_"));
        assert_eq!(request.email, "test@example.com");
        assert_eq!(request.name, "Test User");
        assert_eq!(request.status, PendingRequestStatus::Pending);
        assert!(request.requested_at <= Utc::now());
        assert!(request.reviewed_by.is_none());
        assert!(request.reviewed_at.is_none());
        assert!(request.denial_reason.is_none());
    }
    
    #[test]
    fn test_pending_request_email_normalization() {
        let request = PendingUserRequest::new(
            "Test@Example.COM".to_string(),
            "Test User".to_string(),
            None,
            None,
            None,
            None,
            None,
        );
        
        assert_eq!(request.email, "test@example.com");
    }
    
    #[test]
    fn test_pending_request_status_variants() {
        assert_eq!(PendingRequestStatus::Pending, PendingRequestStatus::Pending);
        assert_eq!(PendingRequestStatus::Approved, PendingRequestStatus::Approved);
        assert_eq!(PendingRequestStatus::Denied, PendingRequestStatus::Denied);
        assert_ne!(PendingRequestStatus::Pending, PendingRequestStatus::Approved);
    }
    
    #[test]
    fn test_pending_registry_load_empty() {
        let temp_dir = TempDir::new().unwrap();
        let registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        assert_eq!(registry.requests.len(), 0);
    }
    
    #[test]
    fn test_pending_registry_add_request() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        assert_eq!(registry.requests.len(), 1);
        assert_eq!(registry.requests[0].email, "test@example.com");
    }
    
    #[test]
    fn test_pending_registry_add_multiple_requests() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request1 = create_test_request("user1@example.com", "User One");
        let request2 = create_test_request("user2@example.com", "User Two");
        
        registry.add_request(request1).unwrap();
        registry.add_request(request2).unwrap();
        
        assert_eq!(registry.requests.len(), 2);
    }
    
    #[test]
    fn test_pending_registry_add_duplicate_email() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request1 = create_test_request("test@example.com", "Test User");
        registry.add_request(request1).unwrap();
        
        let request2 = create_test_request("test@example.com", "Another User");
        let result = registry.add_request(request2);
        
        assert!(result.is_err());
        if let Err(PendingRegistryError::RequestExists(email)) = result {
            assert_eq!(email, "test@example.com");
        } else {
            panic!("Expected RequestExists error");
        }
    }
    
    #[test]
    fn test_pending_registry_find_by_email() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        let found = registry.find_by_email("test@example.com");
        assert!(found.is_some());
        assert_eq!(found.unwrap().email, "test@example.com");
        
        // Case-insensitive search
        let found_upper = registry.find_by_email("TEST@EXAMPLE.COM");
        assert!(found_upper.is_some());
        
        // Not found
        let not_found = registry.find_by_email("notfound@example.com");
        assert!(not_found.is_none());
    }
    
    #[test]
    fn test_pending_registry_find_by_id() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        let request_id = request.id.clone();
        registry.add_request(request).unwrap();
        
        let found = registry.find_by_id(&request_id);
        assert!(found.is_some());
        assert_eq!(found.unwrap().id, request_id);
        
        // Not found
        let not_found = registry.find_by_id("req_invalid");
        assert!(not_found.is_none());
    }
    
    #[test]
    fn test_pending_registry_find_pending_by_email() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        // Should find pending request
        let found = registry.find_pending_by_email("test@example.com");
        assert!(found.is_some());
        assert_eq!(found.unwrap().status, PendingRequestStatus::Pending);
        
        // Approve the request
        registry.approve_request("test@example.com", "admin@example.com").unwrap();
        
        // Should not find it as pending anymore
        let found_after = registry.find_pending_by_email("test@example.com");
        assert!(found_after.is_none());
        
        // But should still find it by find_by_email
        let found_any = registry.find_by_email("test@example.com");
        assert!(found_any.is_some());
        assert_eq!(found_any.unwrap().status, PendingRequestStatus::Approved);
    }
    
    #[test]
    fn test_pending_registry_approve_request() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        let approved = registry.approve_request("test@example.com", "admin@example.com").unwrap();
        
        assert_eq!(approved.status, PendingRequestStatus::Approved);
        assert_eq!(approved.reviewed_by, Some("admin@example.com".to_string()));
        assert!(approved.reviewed_at.is_some());
        
        // Check registry state
        let found = registry.find_by_email("test@example.com").unwrap();
        assert_eq!(found.status, PendingRequestStatus::Approved);
        assert_eq!(found.reviewed_by, Some("admin@example.com".to_string()));
    }
    
    #[test]
    fn test_pending_registry_approve_nonexistent() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let result = registry.approve_request("notfound@example.com", "admin@example.com");
        
        assert!(result.is_err());
        if let Err(PendingRegistryError::RequestNotFound(email)) = result {
            assert_eq!(email, "notfound@example.com");
        } else {
            panic!("Expected RequestNotFound error");
        }
    }
    
    #[test]
    fn test_pending_registry_approve_already_approved() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        // Approve once
        registry.approve_request("test@example.com", "admin1@example.com").unwrap();
        
        // Try to approve again
        let result = registry.approve_request("test@example.com", "admin2@example.com");
        
        assert!(result.is_err());
        if let Err(PendingRegistryError::RequestAlreadyReviewed(id)) = result {
            assert!(id.starts_with("req_"));
        } else {
            panic!("Expected RequestAlreadyReviewed error");
        }
    }
    
    #[test]
    fn test_pending_registry_deny_request() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        let reason = Some("Incomplete information".to_string());
        registry.deny_request("test@example.com", "admin@example.com", reason.clone()).unwrap();
        
        // Check registry state
        let found = registry.find_by_email("test@example.com").unwrap();
        assert_eq!(found.status, PendingRequestStatus::Denied);
        assert_eq!(found.reviewed_by, Some("admin@example.com".to_string()));
        assert_eq!(found.denial_reason, reason);
    }
    
    #[test]
    fn test_pending_registry_deny_without_reason() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        registry.deny_request("test@example.com", "admin@example.com", None).unwrap();
        
        let found = registry.find_by_email("test@example.com").unwrap();
        assert_eq!(found.status, PendingRequestStatus::Denied);
        assert!(found.denial_reason.is_none());
    }
    
    #[test]
    fn test_pending_registry_deny_nonexistent() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let result = registry.deny_request("notfound@example.com", "admin@example.com", None);
        
        assert!(result.is_err());
        if let Err(PendingRegistryError::RequestNotFound(email)) = result {
            assert_eq!(email, "notfound@example.com");
        } else {
            panic!("Expected RequestNotFound error");
        }
    }
    
    #[test]
    fn test_pending_registry_deny_already_denied() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request = create_test_request("test@example.com", "Test User");
        registry.add_request(request).unwrap();
        
        // Deny once
        registry.deny_request("test@example.com", "admin1@example.com", None).unwrap();
        
        // Try to deny again
        let result = registry.deny_request("test@example.com", "admin2@example.com", None);
        
        assert!(result.is_err());
        if let Err(PendingRegistryError::RequestAlreadyReviewed(id)) = result {
            assert!(id.starts_with("req_"));
        } else {
            panic!("Expected RequestAlreadyReviewed error");
        }
    }
    
    #[test]
    fn test_pending_registry_pending_requests() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request1 = create_test_request("user1@example.com", "User One");
        let request2 = create_test_request("user2@example.com", "User Two");
        let request3 = create_test_request("user3@example.com", "User Three");
        
        registry.add_request(request1).unwrap();
        registry.add_request(request2).unwrap();
        registry.add_request(request3).unwrap();
        
        // All should be pending
        let pending = registry.pending_requests();
        assert_eq!(pending.len(), 3);
        
        // Approve one
        registry.approve_request("user1@example.com", "admin@example.com").unwrap();
        
        // Should only have 2 pending now
        let pending_after = registry.pending_requests();
        assert_eq!(pending_after.len(), 2);
        assert!(pending_after.iter().all(|r| r.status == PendingRequestStatus::Pending));
    }
    
    #[test]
    fn test_pending_registry_save_and_load() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request1 = create_test_request("user1@example.com", "User One");
        let request2 = create_test_request("user2@example.com", "User Two");
        
        registry.add_request(request1).unwrap();
        registry.add_request(request2).unwrap();
        
        // Save registry
        registry.save().unwrap();
        
        // Load again
        let loaded = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        assert_eq!(loaded.requests.len(), 2);
        assert!(loaded.find_by_email("user1@example.com").is_some());
        assert!(loaded.find_by_email("user2@example.com").is_some());
    }
    
    #[test]
    fn test_pending_registry_save_and_load_with_status() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        let request1 = create_test_request("user1@example.com", "User One");
        let request2 = create_test_request("user2@example.com", "User Two");
        let request3 = create_test_request("user3@example.com", "User Three");
        
        registry.add_request(request1).unwrap();
        registry.add_request(request2).unwrap();
        registry.add_request(request3).unwrap();
        
        // Approve one, deny one
        registry.approve_request("user1@example.com", "admin@example.com").unwrap();
        registry.deny_request("user2@example.com", "admin@example.com", Some("Rejected".to_string())).unwrap();
        
        // Save and load
        registry.save().unwrap();
        let loaded = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        assert_eq!(loaded.find_by_email("user1@example.com").unwrap().status, PendingRequestStatus::Approved);
        assert_eq!(loaded.find_by_email("user2@example.com").unwrap().status, PendingRequestStatus::Denied);
        assert_eq!(loaded.find_by_email("user3@example.com").unwrap().status, PendingRequestStatus::Pending);
    }
    
    #[test]
    fn test_pending_registry_invalid_request_id() {
        let temp_dir = TempDir::new().unwrap();
        let mut registry = PendingUserRegistry::load(temp_dir.path()).unwrap();
        
        // Create a request with invalid ID format
        let mut request = create_test_request("test@example.com", "Test User");
        request.id = "invalid_id".to_string();
        
        let result = registry.add_request(request);
        
        assert!(result.is_err());
        if let Err(PendingRegistryError::InvalidRequestId(id)) = result {
            assert_eq!(id, "invalid_id");
        } else {
            panic!("Expected InvalidRequestId error");
        }
    }
    
    #[test]
    fn test_pending_request_serialization() {
        let request = create_test_request("test@example.com", "Test User");
        
        // Test YAML serialization
        let yaml = serde_yaml::to_string(&request).unwrap();
        assert!(yaml.contains("test@example.com"));
        assert!(yaml.contains("Test User"));
        
        // Test deserialization
        let deserialized: PendingUserRequest = serde_yaml::from_str(&yaml).unwrap();
        assert_eq!(deserialized.email, request.email);
        assert_eq!(deserialized.name, request.name);
        assert_eq!(deserialized.status, request.status);
    }
}

