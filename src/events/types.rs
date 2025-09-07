//! Event type definitions

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Types of events that can occur in the system
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum EventType {
    ObjectCreated,
    ObjectUpdated,
    ObjectDeleted,
    StateChanged,
    MetricRecorded,
    MaintenanceScheduled,
    AlertRaised,
    AlertResolved,
    RatingChanged,
    RatingCalculated,
}

impl From<String> for EventType {
    fn from(s: String) -> Self {
        match s.as_str() {
            "object.created" | "INSERT" => EventType::ObjectCreated,
            "object.updated" | "UPDATE" => EventType::ObjectUpdated,
            "object.deleted" | "DELETE" => EventType::ObjectDeleted,
            "state.changed" => EventType::StateChanged,
            "metric.recorded" => EventType::MetricRecorded,
            "maintenance.scheduled" => EventType::MaintenanceScheduled,
            "alert.raised" => EventType::AlertRaised,
            "alert.resolved" => EventType::AlertResolved,
            "bilt.rating.changed" => EventType::RatingChanged,
            "bilt.rating.calculated" => EventType::RatingCalculated,
            _ => EventType::ObjectUpdated,
        }
    }
}

/// Metadata about an event from the database
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EventMetadata {
    pub operation: String,
    pub object_id: Option<Uuid>,
    pub path: Option<String>,
    pub object_type: Option<String>,
    pub building_id: Option<Uuid>,
    pub before: Option<serde_json::Value>,
    pub after: Option<serde_json::Value>,
    pub changed_fields: Option<serde_json::Value>,
    pub state: Option<serde_json::Value>,
}

/// A building event that occurred
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingEvent {
    pub id: Uuid,
    pub event_type: EventType,
    pub object_id: Option<Uuid>,
    pub object_path: Option<String>,
    pub metadata: EventMetadata,
    pub timestamp: DateTime<Utc>,
}

impl BuildingEvent {
    /// Check if this event matches a filter
    pub fn matches_filter(&self, filter: &EventFilter) -> bool {
        // Check event type filter
        if let Some(ref types) = filter.event_types {
            if !types.contains(&self.event_type) {
                return false;
            }
        }
        
        // Check path filter
        if let Some(ref path_pattern) = filter.path_pattern {
            if let Some(ref path) = self.object_path {
                if !path.starts_with(path_pattern) {
                    return false;
                }
            } else {
                return false;
            }
        }
        
        // Check object type filter
        if let Some(ref obj_type) = filter.object_type {
            if let Some(ref meta_type) = self.metadata.object_type {
                if meta_type != obj_type {
                    return false;
                }
            } else {
                return false;
            }
        }
        
        // Check building filter
        if let Some(ref building_id) = filter.building_id {
            if let Some(ref event_building) = self.metadata.building_id {
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

/// Filter for events
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EventFilter {
    pub event_types: Option<Vec<EventType>>,
    pub path_pattern: Option<String>,
    pub object_type: Option<String>,
    pub building_id: Option<Uuid>,
}