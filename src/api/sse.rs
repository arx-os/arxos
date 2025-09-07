//! Server-Sent Events for real-time updates

use crate::api::extractors::ApiKey;
use crate::events::{EventSystem, EventFilter, EventType};
use axum::{
    response::sse::{Event, KeepAlive, Sse},
    extract::{Query, State},
};
use futures::stream::Stream;
use serde::Deserialize;
use std::{convert::Infallible, sync::Arc, time::Duration};
use tokio_stream::StreamExt as _;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct EventStreamQuery {
    /// Filter by event types (comma-separated)
    pub event_types: Option<String>,
    /// Filter by path pattern
    pub path_pattern: Option<String>,
    /// Filter by object type
    pub object_type: Option<String>,
    /// Filter by building ID
    pub building_id: Option<Uuid>,
}

/// SSE endpoint for streaming events
pub async fn event_stream(
    _auth: ApiKey,
    Query(query): Query<EventStreamQuery>,
    State(event_system): State<Arc<EventSystem>>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    // Parse event types filter
    let event_types = query.event_types.map(|types| {
        types
            .split(',')
            .map(|t| t.trim().to_string().into())
            .collect::<Vec<EventType>>()
    });
    
    // Create filter
    let filter = EventFilter {
        event_types,
        path_pattern: query.path_pattern,
        object_type: query.object_type,
        building_id: query.building_id,
    };
    
    // Subscribe to events
    let mut receiver = event_system.subscribe();
    
    // Create the event stream
    let stream = async_stream::stream! {
        // Send initial connection event
        yield Ok(Event::default()
            .event("connected")
            .data("Connected to ArxOS event stream"));
        
        // Listen for events
        loop {
            match receiver.recv().await {
                Ok(event) => {
                    // Check if event matches filter
                    if !event.matches_filter(&filter) {
                        continue;
                    }
                    
                    // Convert to SSE event
                    let sse_event = Event::default()
                        .event(match event.event_type {
                            EventType::ObjectCreated => "object.created",
                            EventType::ObjectUpdated => "object.updated",
                            EventType::ObjectDeleted => "object.deleted",
                            EventType::StateChanged => "state.changed",
                            EventType::MetricRecorded => "metric.recorded",
                            EventType::MaintenanceScheduled => "maintenance.scheduled",
                            EventType::AlertRaised => "alert.raised",
                            EventType::AlertResolved => "alert.resolved",
                            EventType::RatingChanged => "bilt.rating.changed",
                            EventType::RatingCalculated => "bilt.rating.calculated",
                        })
                        .json_data(event)
                        .unwrap_or_else(|_| Event::default().data("error"));
                    
                    yield Ok(sse_event);
                }
                Err(e) => {
                    log::error!("Error receiving event: {}", e);
                    break;
                }
            }
        }
    };
    
    Sse::new(stream).keep_alive(
        KeepAlive::new()
            .interval(Duration::from_secs(30))
            .text("keep-alive"),
    )
}

/// Get recent events endpoint
pub async fn get_recent_events(
    _auth: ApiKey,
    State(event_system): State<Arc<EventSystem>>,
) -> Result<axum::Json<serde_json::Value>, crate::api::ApiError> {
    let events = event_system
        .get_recent_events(None, Some(100))
        .await?;
    
    Ok(axum::Json(serde_json::json!({
        "events": events,
        "count": events.len(),
    })))
}