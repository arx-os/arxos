//! Type definitions for user registry TUI

use chrono::{DateTime, Utc};
use std::collections::HashMap;
use std::path::PathBuf;

/// User in the identity registry
#[derive(Debug, Clone)]
pub struct User {
    pub id: String,
    pub name: String,
    pub email: String,
    pub organization: Option<String>,
    pub phone: Option<String>,
    pub verified: bool,
    pub verified_by: Option<String>,
    pub verified_at: Option<DateTime<Utc>>,
    pub role: String,
    pub status: String,
    pub permissions: Vec<String>,
    pub last_active: Option<DateTime<Utc>>,
    pub added_at: DateTime<Utc>,
}

/// User registry for managing user identities
#[derive(Debug, Clone)]
pub struct UserRegistry {
    pub(super) users: HashMap<String, User>,
}

impl UserRegistry {
    pub fn new() -> Self {
        Self {
            users: HashMap::new(),
        }
    }

    pub fn load(_path: PathBuf) -> Result<Self, Box<dyn std::error::Error>> {
        // Stub implementation - would load from file
        Ok(Self::new())
    }

    pub fn all_users(&self) -> Vec<User> {
        self.users.values().cloned().collect()
    }

    #[allow(dead_code)]
    pub fn get_user(&self, id: &str) -> Option<&User> {
        self.users.get(id)
    }

    pub fn find_by_email(&self, email: &str) -> Option<&User> {
        self.users.values().find(|user| user.email == email)
    }
}

/// User activity item for timeline
#[derive(Debug, Clone)]
pub struct UserActivityItem {
    pub timestamp: DateTime<Utc>,
    pub relative_time: String,
    pub commit_hash: String,
    pub commit_message: String,
    #[allow(dead_code)] // Reserved for future enhancement
    pub files_changed: Vec<String>,
}

/// View mode for user browser
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ViewMode {
    List,
    Organizations,
    Activity,
}

/// User browser state
pub struct UserBrowserState {
    pub(super) registry: UserRegistry,
    pub(super) users: Vec<User>,
    pub(super) filtered_users: Vec<usize>, // Indices into users vector
    pub(super) selected_index: usize,
    pub(super) view_mode: ViewMode,
    pub(super) search_query: String,
    pub(super) search_mode: bool,
    pub(super) selected_user_activity: Vec<UserActivityItem>,
    pub(super) organization_groups: HashMap<String, Vec<usize>>,
    pub(super) show_details: bool,
}

impl UserBrowserState {
    pub fn new(registry: UserRegistry) -> Self {
        let users = registry.all_users().to_vec();
        let filtered_users: Vec<usize> = (0..users.len()).collect();

        // Group users by organization
        let mut organization_groups: HashMap<String, Vec<usize>> = HashMap::new();
        for (idx, user) in users.iter().enumerate() {
            let org = user
                .organization
                .as_ref()
                .cloned()
                .unwrap_or_else(|| "Unaffiliated".to_string());
            organization_groups.entry(org).or_default().push(idx);
        }

        Self {
            registry,
            users,
            filtered_users,
            selected_index: 0,
            view_mode: ViewMode::List,
            search_query: String::new(),
            search_mode: false,
            selected_user_activity: Vec::new(),
            organization_groups,
            show_details: true,
        }
    }

    pub fn selected_user(&self) -> Option<&User> {
        if let Some(&idx) = self.filtered_users.get(self.selected_index) {
            self.users.get(idx)
        } else {
            None
        }
    }

    pub fn filter_users(&mut self, query: &str) {
        self.search_query = query.to_lowercase();
        if query.is_empty() {
            self.filtered_users = (0..self.users.len()).collect();
        } else {
            self.filtered_users = self
                .users
                .iter()
                .enumerate()
                .filter(|(_, user)| {
                    user.name.to_lowercase().contains(&self.search_query)
                        || user.email.to_lowercase().contains(&self.search_query)
                        || user
                            .organization
                            .as_ref()
                            .map(|org| org.to_lowercase().contains(&self.search_query))
                            .unwrap_or(false)
                })
                .map(|(idx, _)| idx)
                .collect();
        }

        // Update selection
        if self.selected_index >= self.filtered_users.len() {
            self.selected_index = self.filtered_users.len().saturating_sub(1);
        }
    }

    pub fn move_up(&mut self) {
        if self.selected_index > 0 {
            self.selected_index -= 1;
        }
    }

    pub fn move_down(&mut self) {
        if self.selected_index < self.filtered_users.len().saturating_sub(1) {
            self.selected_index += 1;
        }
    }

    pub fn load_user_activity(
        &mut self,
        user_email: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        use crate::git::{BuildingGitManager, GitConfigManager};

        // Find Git repository
        let repo_path_str = find_git_repository()?.ok_or("Not in a Git repository")?;

        // Load commit history
        let config = GitConfigManager::default_config();
        let manager = BuildingGitManager::new(&repo_path_str, "Building", config)?;
        let commits = manager.list_commits(50)?; // Last 50 commits

        // Extract user_id from registry
        let user = self.registry.find_by_email(user_email);
        let user_id = user.as_ref().map(|u| u.id.clone());

        // Filter commits by user
        let mut activities = Vec::new();
        for commit in commits {
            // Check if commit belongs to this user
            let belongs_to_user = if let Some(ref uid) = user_id {
                // Check for ArxOS-User-ID trailer
                extract_user_id_from_commit(&commit.message)
                    .map(|committed_uid| committed_uid == *uid)
                    .unwrap_or(false)
            } else {
                // Fallback: check author email
                extract_email_from_author(&commit.author)
                    .map(|email| email.to_lowercase() == user_email.to_lowercase())
                    .unwrap_or(false)
            };

            if belongs_to_user {
                let timestamp =
                    chrono::DateTime::from_timestamp(commit.time, 0).unwrap_or_else(Utc::now);
                let relative_time = format_relative_time(&timestamp);

                // Extract files changed (simplified - just count for now)
                let files_changed = Vec::new(); // Could enhance later

                activities.push(UserActivityItem {
                    timestamp,
                    relative_time,
                    commit_hash: commit.id[..8].to_string(),
                    commit_message: commit.message.clone(),
                    files_changed,
                });
            }
        }

        // Sort by timestamp (newest first)
        activities.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        self.selected_user_activity = activities;

        Ok(())
    }
}

/// Find the Git repository path (stub implementation)
pub fn find_git_repository() -> Result<Option<String>, Box<dyn std::error::Error>> {
    // Stub - would search for .git directory
    Ok(Some(".".to_string()))
}

/// Extract user ID from commit message (stub implementation)
pub fn extract_user_id_from_commit(_message: &str) -> Option<String> {
    // Stub - would parse commit message for user ID
    None
}

/// Extract email from commit author string (stub implementation)
pub fn extract_email_from_author(_author: &str) -> Option<String> {
    // Stub - would parse author string for email
    None
}

/// Format relative time (e.g., "2 hours ago")
pub fn format_relative_time(timestamp: &DateTime<Utc>) -> String {
    let now = Utc::now();
    let duration = now.signed_duration_since(*timestamp);

    if duration.num_seconds() < 60 {
        "Just now".to_string()
    } else if duration.num_minutes() < 60 {
        format!("{} minutes ago", duration.num_minutes())
    } else if duration.num_hours() < 24 {
        format!("{} hours ago", duration.num_hours())
    } else if duration.num_days() < 7 {
        format!("{} days ago", duration.num_days())
    } else {
        timestamp.format("%Y-%m-%d").to_string()
    }
}
