//! Event system for real-time notifications

use anyhow::Result;
use serde::{Deserialize, Serialize};
use sqlx::postgres::{PgListener, PgNotification};
use std::sync::Arc;
use tokio::sync::{broadcast, RwLock};
use uuid::Uuid;
use chrono::{DateTime, Utc};

pub mod listener;
pub mod types;

pub use listener::EventListener;
pub use types::{BuildingEvent, EventType, EventMetadata, EventFilter};

/// Event system for managing real-time notifications
pub struct EventSystem {
    db_url: String,
    sender: broadcast::Sender<BuildingEvent>,
    listeners: Arc<RwLock<Vec<String>>>,
}

impl EventSystem {
    /// Create a new event system
    pub fn new(db_url: String) -> Self {
        let (sender, _) = broadcast::channel(1000);
        
        Self {
            db_url,
            sender,
            listeners: Arc::new(RwLock::new(Vec::new())),
        }
    }
    
    /// Subscribe to events
    pub fn subscribe(&self) -> broadcast::Receiver<BuildingEvent> {
        self.sender.subscribe()
    }
    
    /// Send an event directly
    pub fn send_event(&self, event: BuildingEvent) -> Result<()> {
        let _ = self.sender.send(event);
        Ok(())
    }
    
    /// Start listening to database notifications
    pub async fn start_listening(&self) -> Result<()> {
        let mut listener = PgListener::connect(&self.db_url).await?;
        
        // Listen to main channel
        listener.listen("arxos_events").await?;
        
        // Add any additional channels from listeners
        let channels = self.listeners.read().await;
        for channel in channels.iter() {
            listener.listen(channel).await?;
        }
        
        log::info!("Event listener started on arxos_events channel");
        
        // Process notifications
        loop {
            while let Some(notification) = listener.try_recv().await? {
                self.process_notification(notification).await?;
            }
            
            // Small delay to prevent busy loop
            tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
        }
    }
    
    /// Listen to a specific channel
    pub async fn listen_to_channel(&self, channel: String) -> Result<()> {
        let mut listeners = self.listeners.write().await;
        if !listeners.contains(&channel) {
            listeners.push(channel.clone());
            log::info!("Added listener for channel: {}", channel);
        }
        Ok(())
    }
    
    /// Process a database notification
    async fn process_notification(&self, notification: PgNotification) -> Result<()> {
        let channel = notification.channel();
        let payload = notification.payload();
        
        log::debug!("Received notification on channel {}: {}", channel, payload);
        
        // Parse the event
        match serde_json::from_str::<EventMetadata>(payload) {
            Ok(metadata) => {
                let event = BuildingEvent {
                    id: Uuid::new_v4(),
                    event_type: metadata.operation.clone().into(),
                    object_id: metadata.object_id,
                    object_path: metadata.path.clone(),
                    metadata,
                    timestamp: Utc::now(),
                };
                
                // Broadcast to all subscribers
                let _ = self.sender.send(event.clone());
                
                log::info!("Broadcasted event: {:?}", event.event_type);
            }
            Err(e) => {
                log::error!("Failed to parse event payload: {}", e);
            }
        }
        
        Ok(())
    }
    
    /// Get recent events from the database
    pub async fn get_recent_events(
        &self,
        since: Option<DateTime<Utc>>,
        limit: Option<i32>,
    ) -> Result<Vec<BuildingEvent>> {
        let pool = sqlx::PgPool::connect(&self.db_url).await?;
        
        let since = since.unwrap_or_else(|| Utc::now() - chrono::Duration::hours(1));
        let limit = limit.unwrap_or(100) as i64;
        
        let rows = sqlx::query_as::<_, (Uuid, String, Option<Uuid>, Option<String>, Option<serde_json::Value>, chrono::NaiveDateTime)>(
            "SELECT id, event_type, object_id, object_path, metadata, created_at
             FROM building_events
             WHERE created_at >= $1
             ORDER BY created_at DESC
             LIMIT $2"
        )
        .bind(since.naive_utc())
        .bind(limit)
        .fetch_all(&pool)
        .await?;
        
        let events = rows
            .into_iter()
            .map(|(id, event_type, object_id, object_path, metadata, created_at)| {
                BuildingEvent {
                    id,
                    event_type: event_type.into(),
                    object_id,
                    object_path,
                    metadata: metadata
                        .and_then(|m| serde_json::from_value(m).ok())
                        .unwrap_or_default(),
                    timestamp: DateTime::from_naive_utc_and_offset(created_at, Utc),
                }
            })
            .collect();
        
        Ok(events)
    }
}