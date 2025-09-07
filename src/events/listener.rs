//! Event listener for handling real-time notifications

use crate::events::{BuildingEvent, EventFilter};
use tokio::sync::broadcast;

/// Event listener that can filter and process events
pub struct EventListener {
    receiver: broadcast::Receiver<BuildingEvent>,
    filter: Option<EventFilter>,
}

impl EventListener {
    /// Create a new event listener
    pub fn new(receiver: broadcast::Receiver<BuildingEvent>) -> Self {
        Self {
            receiver,
            filter: None,
        }
    }
    
    /// Set a filter for this listener
    pub fn with_filter(mut self, filter: EventFilter) -> Self {
        self.filter = Some(filter);
        self
    }
    
    /// Wait for the next event that matches the filter
    pub async fn next(&mut self) -> Option<BuildingEvent> {
        loop {
            match self.receiver.recv().await {
                Ok(event) => {
                    // Check if event matches filter
                    if let Some(ref filter) = self.filter {
                        if !event.matches_filter(filter) {
                            continue;
                        }
                    }
                    return Some(event);
                }
                Err(broadcast::error::RecvError::Lagged(n)) => {
                    log::warn!("Event listener lagged by {} messages", n);
                    continue;
                }
                Err(broadcast::error::RecvError::Closed) => {
                    log::warn!("Event channel closed");
                    return None;
                }
            }
        }
    }
    
    /// Try to receive an event without blocking
    pub fn try_next(&mut self) -> Option<BuildingEvent> {
        match self.receiver.try_recv() {
            Ok(event) => {
                // Check if event matches filter
                if let Some(ref filter) = self.filter {
                    if !event.matches_filter(filter) {
                        return None;
                    }
                }
                Some(event)
            }
            Err(_) => None,
        }
    }
}