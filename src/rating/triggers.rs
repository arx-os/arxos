//! BILT Rating Triggers
//! 
//! Automatic rating recalculation triggered by data contributions.
//! Every object creation, update, or property change triggers immediate
//! rating updates to reflect building value changes in real-time.

use anyhow::Result;
use std::sync::Arc;
use tokio::sync::broadcast;
use uuid::Uuid;

use crate::events::{BuildingEvent, EventType};
use super::{RatingService, RatingEventHandler, RatingTriggers, RatingContext};

/// Rating trigger system that responds to building data changes
pub struct RatingTriggerSystem {
    rating_service: Arc<RatingService>,
    rating_events: Arc<RatingEventHandler>,
}

impl RatingTriggerSystem {
    /// Create new rating trigger system
    pub fn new(
        rating_service: Arc<RatingService>,
        rating_events: Arc<RatingEventHandler>,
    ) -> Self {
        Self {
            rating_service,
            rating_events,
        }
    }
    
    /// Start listening for events that should trigger rating updates
    pub async fn start_trigger_listener(
        self: Arc<Self>,
        mut event_receiver: broadcast::Receiver<BuildingEvent>,
    ) {
        tokio::spawn(async move {
            loop {
                match event_receiver.recv().await {
                    Ok(event) => {
                        if let Err(e) = self.handle_event(&event).await {
                            log::error!("Failed to handle rating trigger for event {}: {}", event.id, e);
                        }
                    }
                    Err(e) => {
                        log::error!("Rating trigger receiver error: {}", e);
                        break;
                    }
                }
            }
        });
    }
    
    /// Handle individual events and determine if rating recalculation is needed
    async fn handle_event(&self, event: &BuildingEvent) -> Result<()> {
        // Only process events with building_id
        let building_id = match &event.metadata.building_id {
            Some(id) => id.to_string(),
            None => return Ok(()), // Skip events without building context
        };
        
        let trigger_reason = match &event.event_type {
            EventType::ObjectCreated => RatingTriggers::OBJECT_CREATED,
            EventType::ObjectUpdated => RatingTriggers::OBJECT_UPDATED, 
            EventType::ObjectDeleted => RatingTriggers::OBJECT_DELETED,
            EventType::StateChanged => RatingTriggers::PROPERTIES_ADDED,
            EventType::MetricRecorded => RatingTriggers::SENSOR_INSTALLED,
            EventType::MaintenanceScheduled => RatingTriggers::MAINTENANCE_RECORDED,
            EventType::RatingChanged | EventType::RatingCalculated => return Ok(()), // Skip rating events to avoid loops
            _ => return Ok(()), // Skip events that don't affect ratings
        };
        
        // Get current rating before recalculation
        let old_rating = self.rating_service.get_building_rating(&building_id).await?;
        
        // Recalculate rating
        let start_time = std::time::Instant::now();
        let new_rating = self.rating_service.update_building_rating(&building_id).await?;
        let calculation_duration = start_time.elapsed().as_millis() as u64;
        
        // Emit rating calculation event
        self.rating_events.emit_rating_calculated(&new_rating, calculation_duration).await?;
        
        // If rating changed, emit rating change event
        if let Some(old) = &old_rating {
            if old.current_grade != new_rating.current_grade || 
               (old.numeric_score - new_rating.numeric_score).abs() >= 0.1 {
                self.rating_events.emit_rating_change(
                    old_rating.as_ref(),
                    &new_rating,
                    trigger_reason,
                ).await?;
            }
        } else {
            // First rating calculation
            self.rating_events.emit_rating_change(
                None,
                &new_rating,
                "initial_rating_calculation",
            ).await?;
        }
        
        log::info!(
            "Rating updated for building {} from {} to {} (trigger: {})",
            building_id,
            old_rating.as_ref().map(|r| r.current_grade.as_str()).unwrap_or("none"),
            new_rating.current_grade,
            trigger_reason
        );
        
        Ok(())
    }
    
    /// Manually trigger rating recalculation for a building
    pub async fn manual_recalculate(&self, building_id: &str) -> Result<()> {
        let old_rating = self.rating_service.get_building_rating(building_id).await?;
        let new_rating = self.rating_service.update_building_rating(building_id).await?;
        
        self.rating_events.emit_rating_change(
            old_rating.as_ref(),
            &new_rating,
            RatingTriggers::MANUAL_RECALCULATION,
        ).await?;
        
        Ok(())
    }
    
    /// Batch recalculate ratings for multiple buildings
    pub async fn batch_recalculate(&self, building_ids: &[String]) -> Result<Vec<String>> {
        let mut updated_buildings = Vec::new();
        
        for building_id in building_ids {
            match self.manual_recalculate(building_id).await {
                Ok(_) => updated_buildings.push(building_id.clone()),
                Err(e) => log::error!("Failed to recalculate rating for building {}: {}", building_id, e),
            }
        }
        
        log::info!("Batch recalculated ratings for {} buildings", updated_buildings.len());
        Ok(updated_buildings)
    }
    
    /// Schedule periodic rating recalculation (for maintenance)
    pub async fn start_scheduled_recalculation(
        self: Arc<Self>,
        interval_hours: u64,
    ) {
        let mut interval = tokio::time::interval(std::time::Duration::from_secs(interval_hours * 3600));
        
        tokio::spawn(async move {
            loop {
                interval.tick().await;
                
                log::info!("Starting scheduled rating recalculation");
                
                // Get all buildings that need recalculation
                // (buildings with ratings older than 24 hours)
                match self.get_buildings_needing_recalculation().await {
                    Ok(building_ids) => {
                        if !building_ids.is_empty() {
                            match self.batch_recalculate(&building_ids).await {
                                Ok(updated) => log::info!("Scheduled recalculation completed: {} buildings updated", updated.len()),
                                Err(e) => log::error!("Scheduled recalculation failed: {}", e),
                            }
                        }
                    }
                    Err(e) => log::error!("Failed to get buildings for scheduled recalculation: {}", e),
                }
            }
        });
    }
    
    /// Get buildings that need rating recalculation
    async fn get_buildings_needing_recalculation(&self) -> Result<Vec<String>> {
        // This would query the database for buildings with stale ratings
        // For now, return empty list
        Ok(vec![])
    }
}