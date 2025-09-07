//! Webhook delivery implementation

use crate::webhooks::types::Webhook;
use crate::events::BuildingEvent;
use anyhow::Result;
use sqlx::{PgPool, Row};
use uuid::Uuid;
use chrono::Utc;
use std::time::Duration;

/// Webhook delivery task
pub struct WebhookDelivery {
    webhook: Webhook,
    event: BuildingEvent,
    attempt: i32,
}

impl WebhookDelivery {
    /// Create a new webhook delivery
    pub fn new(webhook: Webhook, event: BuildingEvent) -> Self {
        Self {
            webhook,
            event,
            attempt: 1,
        }
    }
    
    /// Execute the webhook delivery
    pub async fn execute(&self, pool: &PgPool) -> Result<()> {
        let delivery_id = Uuid::new_v4();
        let start_time = std::time::Instant::now();
        
        // Prepare payload
        let payload = serde_json::json!({
            "event_id": self.event.id,
            "event_type": self.event.event_type,
            "object_id": self.event.object_id,
            "object_path": self.event.object_path,
            "metadata": self.event.metadata,
            "timestamp": self.event.timestamp,
        });
        
        // Prepare headers
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert(
            reqwest::header::CONTENT_TYPE,
            reqwest::header::HeaderValue::from_static("application/json"),
        );
        
        // Add custom headers
        if let Some(custom) = self.webhook.custom_headers.as_object() {
            for (key, value) in custom {
                if let Some(val_str) = value.as_str() {
                    if let Ok(header_name) = reqwest::header::HeaderName::from_bytes(key.as_bytes()) {
                        if let Ok(header_value) = reqwest::header::HeaderValue::from_str(val_str) {
                            headers.insert(header_name, header_value);
                        }
                    }
                }
            }
        }
        
        // Add HMAC signature if secret is configured
        if let Some(ref secret) = self.webhook.secret {
            use hmac::{Hmac, Mac};
            use sha2::Sha256;
            
            type HmacSha256 = Hmac<Sha256>;
            
            let payload_str = serde_json::to_string(&payload)?;
            let mut mac = HmacSha256::new_from_slice(secret.as_bytes())?;
            mac.update(payload_str.as_bytes());
            let signature = hex::encode(mac.finalize().into_bytes());
            
            headers.insert(
                reqwest::header::HeaderName::from_static("x-arxos-signature"),
                reqwest::header::HeaderValue::from_str(&format!("sha256={}", signature))?,
            );
        }
        
        // Convert headers to JSON for storage
        let headers_json = serde_json::json!({
            "content-type": "application/json",
            "x-arxos-signature": headers.get("x-arxos-signature")
                .and_then(|v| v.to_str().ok())
                .unwrap_or("")
        });
        
        // Record delivery attempt
        sqlx::query(
            "INSERT INTO webhook_deliveries (
                id, webhook_id, event_id,
                url, method, headers, payload,
                attempt_number, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)"
        )
        .bind(delivery_id)
        .bind(self.webhook.id)
        .bind(self.event.id)
        .bind(&self.webhook.url)
        .bind("POST")
        .bind(&headers_json)
        .bind(&payload)
        .bind(self.attempt)
        .bind(Utc::now().naive_utc())
        .execute(pool)
        .await?;
        
        // Send HTTP request
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(self.webhook.timeout_seconds as u64))
            .build()?;
        
        let result = client
            .post(&self.webhook.url)
            .headers(headers)
            .json(&payload)
            .send()
            .await;
        
        let duration_ms = start_time.elapsed().as_millis() as i32;
        
        match result {
            Ok(response) => {
                let status = response.status().as_u16() as i32;
                let response_headers = serde_json::to_value(
                    response.headers()
                        .iter()
                        .map(|(k, v)| (k.as_str(), v.to_str().unwrap_or("")))
                        .collect::<Vec<_>>()
                )?;
                let response_body = response.text().await.unwrap_or_default();
                
                let delivered = status >= 200 && status < 300;
                
                sqlx::query(
                    "UPDATE webhook_deliveries
                    SET status_code = $2,
                        response_body = $3,
                        response_headers = $4,
                        delivered = $5,
                        delivered_at = $6,
                        duration_ms = $7
                    WHERE id = $1"
                )
                .bind(delivery_id)
                .bind(status)
                .bind(&response_body)
                .bind(&response_headers)
                .bind(delivered)
                .bind(Utc::now().naive_utc())
                .bind(duration_ms)
                .execute(pool)
                .await?;
                
                if !delivered && self.attempt < self.webhook.retry_count {
                    // Schedule retry
                    self.schedule_retry(pool, delivery_id).await?;
                }
            }
            Err(e) => {
                sqlx::query(
                    "UPDATE webhook_deliveries
                    SET error_message = $2,
                        delivered = false,
                        duration_ms = $3
                    WHERE id = $1"
                )
                .bind(delivery_id)
                .bind(e.to_string())
                .bind(duration_ms)
                .execute(pool)
                .await?;
                
                if self.attempt < self.webhook.retry_count {
                    self.schedule_retry(pool, delivery_id).await?;
                }
            }
        }
        
        Ok(())
    }
    
    /// Schedule a retry for failed delivery
    async fn schedule_retry(&self, pool: &PgPool, delivery_id: Uuid) -> Result<()> {
        // Exponential backoff: 5s, 25s, 125s
        let delay_seconds = 5_i32.pow(self.attempt as u32);
        
        log::info!(
            "Scheduling webhook retry {} for {} in {}s",
            self.attempt + 1,
            self.webhook.id,
            delay_seconds
        );
        
        // Mark for retry (in a real system, this would use a job queue)
        sqlx::query(
            "UPDATE webhook_deliveries
            SET attempt_number = $2
            WHERE id = $1"
        )
        .bind(delivery_id)
        .bind(self.attempt + 1)
        .execute(pool)
        .await?;
        
        Ok(())
    }
    
    /// Retry failed webhook deliveries
    pub async fn retry_failed(pool: &PgPool) -> Result<()> {
        // Find deliveries that need retry using dynamic SQL
        let retry_interval = format!("INTERVAL '5 seconds' * POWER(5, attempt_number - 1)");
        let query = format!(
            "SELECT 
                d.id, d.webhook_id, d.event_id, d.attempt_number,
                w.url, w.secret, w.retry_count, w.timeout_seconds, w.custom_headers
            FROM webhook_deliveries d
            JOIN webhooks w ON w.id = d.webhook_id
            WHERE d.delivered = false
                AND d.attempt_number < w.retry_count
                AND d.created_at < NOW() - {}
            LIMIT 10",
            retry_interval
        );
        
        let rows = sqlx::query(&query)
            .fetch_all(pool)
            .await?;
        
        for row in rows {
            // Reconstruct webhook and event (simplified for retry)
            let webhook = Webhook {
                id: row.get("webhook_id"),
                name: String::new(),
                url: row.get("url"),
                secret: row.get("secret"),
                active: true,
                event_types: None,
                path_pattern: None,
                object_type: None,
                building_id: None,
                retry_count: row.get("retry_count"),
                timeout_seconds: row.get("timeout_seconds"),
                custom_headers: row.get::<Option<serde_json::Value>, _>("custom_headers")
                    .unwrap_or_else(|| serde_json::json!({})),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                last_triggered_at: None,
                total_deliveries: 0,
                successful_deliveries: 0,
                failed_deliveries: 0,
            };
            
            // Create minimal event for retry
            let event = BuildingEvent {
                id: row.get("event_id"),
                event_type: crate::events::EventType::ObjectUpdated,
                object_id: None,
                object_path: None,
                metadata: Default::default(),
                timestamp: Utc::now(),
            };
            
            let mut delivery = WebhookDelivery::new(webhook, event);
            delivery.attempt = row.get("attempt_number");
            
            if let Err(e) = delivery.execute(pool).await {
                log::error!("Webhook retry failed: {}", e);
            }
        }
        
        Ok(())
    }
}