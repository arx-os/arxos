//! BILT Rating Event Integration
//! 
//! Connects rating system with ArxOS event system for real-time
//! rating updates and immediate value reflection.

use anyhow::Result;
use serde_json::json;
use chrono::Utc;
use std::sync::Arc;
use tokio::sync::broadcast;

use crate::events::{BuildingEvent, EventSystem, EventType};
use super::models::{BiltRating, RatingChangeEvent};

/// BILT Rating Event Handler
pub struct RatingEventHandler {
    event_system: Arc<EventSystem>,
}

impl RatingEventHandler {
    /// Create new rating event handler
    pub fn new(event_system: Arc<EventSystem>) -> Self {
        Self { event_system }
    }
    
    /// Emit rating change event
    pub async fn emit_rating_change(
        &self,
        old_rating: Option<&BiltRating>,
        new_rating: &BiltRating,
        trigger_reason: &str,
    ) -> Result<()> {
        let old_grade = old_rating.map(|r| r.current_grade.clone()).unwrap_or_else(|| "none".to_string());
        let old_score = old_rating.map(|r| r.numeric_score).unwrap_or(0.0);
        
        let change_event = RatingChangeEvent {
            building_id: new_rating.building_id.clone(),
            old_grade: old_grade.clone(),
            new_grade: new_rating.current_grade.clone(),
            old_score,
            new_score: new_rating.numeric_score,
            trigger_reason: trigger_reason.to_string(),
            timestamp: Utc::now(),
        };
        
        // Create ArxOS building event
        let event = BuildingEvent {
            id: uuid::Uuid::new_v4(),
            event_type: EventType::RatingChanged,
            object_id: None, // Building-level event
            object_path: Some("/".to_string()), // Root level for building
            metadata: crate::events::types::EventMetadata {
                operation: "rating_change".to_string(),
                object_id: None,
                path: Some("/".to_string()),
                object_type: Some("building".to_string()),
                building_id: Some(uuid::Uuid::parse_str(&new_rating.building_id).ok().unwrap_or_default()),
                before: old_rating.map(|r| json!({"grade": r.current_grade, "score": r.numeric_score})),
                after: Some(json!({"grade": new_rating.current_grade, "score": new_rating.numeric_score})),
                changed_fields: Some(json!([trigger_reason])),
                state: Some(json!({
                    "rating_change": change_event,
                    "grade_improved": Self::is_grade_improvement(&old_grade, &new_rating.current_grade),
                    "score_delta": new_rating.numeric_score - old_score,
                    "components": new_rating.components,
                    "version": new_rating.version
                })),
            },
            timestamp: Utc::now(),
        };
        
        // Send through event system
        self.event_system.send_event(event)?;
        
        Ok(())
    }
    
    /// Emit rating calculation event (when rating is computed)
    pub async fn emit_rating_calculated(
        &self,
        rating: &BiltRating,
        calculation_duration_ms: u64,
    ) -> Result<()> {
        let event = BuildingEvent {
            id: uuid::Uuid::new_v4(),
            event_type: EventType::RatingCalculated,
            object_id: None,
            object_path: Some("/".to_string()),
            metadata: crate::events::types::EventMetadata {
                operation: "rating_calculated".to_string(),
                object_id: None,
                path: Some("/".to_string()),
                object_type: Some("building".to_string()),
                building_id: Some(uuid::Uuid::parse_str(&rating.building_id).ok().unwrap_or_default()),
                before: None,
                after: Some(json!({
                    "rating": {
                        "grade": rating.current_grade,
                        "score": rating.numeric_score,
                        "version": rating.version
                    },
                    "performance": {
                        "calculation_duration_ms": calculation_duration_ms,
                        "timestamp": rating.last_updated
                    },
                    "components": rating.components
                })),
                changed_fields: None,
                state: None,
            },
            timestamp: Utc::now(),
        };
        
        self.event_system.send_event(event)?;
        Ok(())
    }
    
    /// Check if grade change represents an improvement
    fn is_grade_improvement(old_grade: &str, new_grade: &str) -> bool {
        use super::models::BiltRating;
        BiltRating::grade_progression_value(new_grade) > BiltRating::grade_progression_value(old_grade)
    }
}

/// Rating trigger reasons for different types of contributions
pub struct RatingTriggers;

impl RatingTriggers {
    pub const OBJECT_CREATED: &'static str = "object_created";
    pub const OBJECT_UPDATED: &'static str = "object_updated";
    pub const OBJECT_DELETED: &'static str = "object_deleted";
    pub const PROPERTIES_ADDED: &'static str = "properties_added";
    pub const SENSOR_INSTALLED: &'static str = "sensor_installed";
    pub const MAINTENANCE_RECORDED: &'static str = "maintenance_recorded";
    pub const BULK_UPDATE: &'static str = "bulk_update";
    pub const SCHEDULED_RECALCULATION: &'static str = "scheduled_recalculation";
    pub const MANUAL_RECALCULATION: &'static str = "manual_recalculation";
    
    /// Get human-readable description of trigger
    pub fn description(trigger: &str) -> &'static str {
        match trigger {
            Self::OBJECT_CREATED => "New object added to building",
            Self::OBJECT_UPDATED => "Existing object updated",
            Self::OBJECT_DELETED => "Object removed from building",
            Self::PROPERTIES_ADDED => "Object properties added or updated",
            Self::SENSOR_INSTALLED => "IoT sensor connected",
            Self::MAINTENANCE_RECORDED => "Maintenance activity recorded",
            Self::BULK_UPDATE => "Bulk operation completed",
            Self::SCHEDULED_RECALCULATION => "Automatic rating recalculation",
            Self::MANUAL_RECALCULATION => "Manual rating refresh",
            _ => "Unknown trigger",
        }
    }
}

/// Helper for setting database session variables for trigger tracking
pub struct RatingContext;

impl RatingContext {
    /// Set trigger reason in database session for audit trail
    pub async fn set_trigger_reason(
        database: &crate::database::Database,
        reason: &str,
    ) -> Result<()> {
        let query = format!(
            "SELECT set_config('arxos.rating_trigger_reason', '{}', false)",
            reason.replace("'", "''") // Escape single quotes
        );
        database.raw_query(&query).await?;
        Ok(())
    }
    
    /// Clear trigger reason from database session
    pub async fn clear_trigger_reason(
        database: &crate::database::Database,
    ) -> Result<()> {
        database.raw_query("SELECT set_config('arxos.rating_trigger_reason', NULL, false)").await?;
        Ok(())
    }
}