//! Webhook system for push notifications

use anyhow::Result;
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;
use chrono::{DateTime, Utc};

pub mod delivery;
pub mod manager;
pub mod types;

pub use delivery::WebhookDelivery;
pub use manager::WebhookManager;
pub use types::{Webhook, WebhookConfig, WebhookDeliveryLog};

/// Webhook system for managing and delivering webhooks
pub struct WebhookSystem {
    pool: PgPool,
    manager: Arc<WebhookManager>,
    delivery_queue: Arc<RwLock<Vec<WebhookDelivery>>>,
}

impl WebhookSystem {
    /// Create a new webhook system
    pub async fn new(db_url: &str) -> Result<Self> {
        let pool = PgPool::connect(db_url).await?;
        let manager = Arc::new(WebhookManager::new(pool.clone()));
        
        Ok(Self {
            pool,
            manager,
            delivery_queue: Arc::new(RwLock::new(Vec::new())),
        })
    }
    
    /// Register a new webhook
    pub async fn register_webhook(&self, config: WebhookConfig) -> Result<Webhook> {
        self.manager.create_webhook(config).await
    }
    
    /// Update an existing webhook
    pub async fn update_webhook(&self, id: Uuid, config: WebhookConfig) -> Result<Webhook> {
        self.manager.update_webhook(id, config).await
    }
    
    /// Delete a webhook
    pub async fn delete_webhook(&self, id: Uuid) -> Result<()> {
        self.manager.delete_webhook(id).await
    }
    
    /// List all webhooks
    pub async fn list_webhooks(&self, active_only: bool) -> Result<Vec<Webhook>> {
        self.manager.list_webhooks(active_only).await
    }
    
    /// Get a specific webhook
    pub async fn get_webhook(&self, id: Uuid) -> Result<Option<Webhook>> {
        self.manager.get_webhook(id).await
    }
    
    /// Process an event and queue webhooks for delivery
    pub async fn process_event(&self, event: &crate::events::BuildingEvent) -> Result<()> {
        // Get matching webhooks
        let webhooks = self.manager.get_matching_webhooks(event).await?;
        
        // Queue deliveries
        let mut queue = self.delivery_queue.write().await;
        for webhook in webhooks {
            let delivery = WebhookDelivery::new(webhook, event.clone());
            queue.push(delivery);
        }
        
        Ok(())
    }
    
    /// Start the delivery worker
    pub async fn start_delivery_worker(self: Arc<Self>) {
        let pool = self.pool.clone();
        let queue = self.delivery_queue.clone();
        
        tokio::spawn(async move {
            loop {
                // Process pending deliveries
                let deliveries = {
                    let mut queue = queue.write().await;
                    std::mem::take(&mut *queue)
                };
                
                for delivery in deliveries {
                    if let Err(e) = delivery.execute(&pool).await {
                        log::error!("Webhook delivery failed: {}", e);
                    }
                }
                
                // Check for retry deliveries
                if let Err(e) = WebhookDelivery::retry_failed(&pool).await {
                    log::error!("Failed to retry webhooks: {}", e);
                }
                
                // Sleep before next iteration
                tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
            }
        });
    }
    
    /// Get delivery logs for a webhook
    pub async fn get_delivery_logs(
        &self,
        webhook_id: Uuid,
        limit: Option<i32>,
    ) -> Result<Vec<WebhookDeliveryLog>> {
        self.manager.get_delivery_logs(webhook_id, limit).await
    }
}