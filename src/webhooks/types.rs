//! Webhook type definitions

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Webhook configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebhookConfig {
    pub name: String,
    pub url: String,
    pub secret: Option<String>,
    pub active: bool,
    pub event_types: Option<Vec<String>>,
    pub path_pattern: Option<String>,
    pub object_type: Option<String>,
    pub building_id: Option<Uuid>,
    pub retry_count: i32,
    pub timeout_seconds: i32,
    pub custom_headers: serde_json::Value,
}

/// Webhook record from database
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Webhook {
    pub id: Uuid,
    pub name: String,
    pub url: String,
    pub secret: Option<String>,
    pub active: bool,
    pub event_types: Option<Vec<String>>,
    pub path_pattern: Option<String>,
    pub object_type: Option<String>,
    pub building_id: Option<Uuid>,
    pub retry_count: i32,
    pub timeout_seconds: i32,
    pub custom_headers: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub last_triggered_at: Option<DateTime<Utc>>,
    pub total_deliveries: i32,
    pub successful_deliveries: i32,
    pub failed_deliveries: i32,
}

/// Webhook delivery log entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebhookDeliveryLog {
    pub id: Uuid,
    pub webhook_id: Uuid,
    pub event_id: Uuid,
    pub url: String,
    pub method: String,
    pub headers: serde_json::Value,
    pub payload: serde_json::Value,
    pub status_code: Option<i32>,
    pub response_body: Option<String>,
    pub response_headers: Option<serde_json::Value>,
    pub delivered: bool,
    pub error_message: Option<String>,
    pub attempt_number: i32,
    pub created_at: DateTime<Utc>,
    pub delivered_at: Option<DateTime<Utc>>,
    pub duration_ms: Option<i32>,
}

impl Webhook {
    /// Check if this webhook matches an event
    pub fn matches_event(&self, event: &crate::events::BuildingEvent) -> bool {
        // Check if webhook is active
        if !self.active {
            return false;
        }
        
        // Check event type filter
        if let Some(ref types) = self.event_types {
            let event_type_str = format!("{:?}", event.event_type).to_lowercase();
            if !types.iter().any(|t| t.to_lowercase() == event_type_str) {
                return false;
            }
        }
        
        // Check path filter
        if let Some(ref pattern) = self.path_pattern {
            if let Some(ref path) = event.object_path {
                if !path.starts_with(pattern) {
                    return false;
                }
            } else {
                return false;
            }
        }
        
        // Check object type filter
        if let Some(ref obj_type) = self.object_type {
            if let Some(ref meta_type) = event.metadata.object_type {
                if meta_type != obj_type {
                    return false;
                }
            } else {
                return false;
            }
        }
        
        // Check building filter
        if let Some(ref building_id) = self.building_id {
            if let Some(ref event_building) = event.metadata.building_id {
                if event_building != building_id {
                    return false;
                }
            } else {
                return false;
            }
        }
        
        true
    }
}