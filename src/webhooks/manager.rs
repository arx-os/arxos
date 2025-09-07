//! Webhook management functions

use crate::webhooks::types::{Webhook, WebhookConfig, WebhookDeliveryLog};
use crate::events::BuildingEvent;
use anyhow::Result;
use sqlx::{PgPool, Row};
use uuid::Uuid;
use chrono::{DateTime, Utc, NaiveDateTime};

/// Webhook manager for CRUD operations
pub struct WebhookManager {
    pool: PgPool,
}

impl WebhookManager {
    /// Create a new webhook manager
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
    
    /// Create a new webhook
    pub async fn create_webhook(&self, config: WebhookConfig) -> Result<Webhook> {
        let id = Uuid::new_v4();
        let now = Utc::now();
        
        let row = sqlx::query(
            "INSERT INTO webhooks (
                id, name, url, secret, active,
                event_types, path_pattern, object_type, building_id,
                retry_count, timeout_seconds, custom_headers,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9,
                $10, $11, $12,
                $13, $13
            )
            RETURNING 
                id, name, url, secret, active,
                event_types, path_pattern, object_type, building_id,
                retry_count, timeout_seconds, custom_headers,
                created_at, updated_at, last_triggered_at,
                total_deliveries, successful_deliveries, failed_deliveries"
        )
        .bind(id)
        .bind(&config.name)
        .bind(&config.url)
        .bind(&config.secret)
        .bind(config.active)
        .bind(&config.event_types)
        .bind(&config.path_pattern)
        .bind(&config.object_type)
        .bind(config.building_id)
        .bind(config.retry_count)
        .bind(config.timeout_seconds)
        .bind(&config.custom_headers)
        .bind(now.naive_utc())
        .fetch_one(&self.pool)
        .await?;
        
        Ok(Self::row_to_webhook(&row))
    }
    
    /// Update an existing webhook
    pub async fn update_webhook(&self, id: Uuid, config: WebhookConfig) -> Result<Webhook> {
        let now = Utc::now();
        
        let row = sqlx::query(
            "UPDATE webhooks SET
                name = $2,
                url = $3,
                secret = $4,
                active = $5,
                event_types = $6,
                path_pattern = $7,
                object_type = $8,
                building_id = $9,
                retry_count = $10,
                timeout_seconds = $11,
                custom_headers = $12,
                updated_at = $13
            WHERE id = $1
            RETURNING 
                id, name, url, secret, active,
                event_types, path_pattern, object_type, building_id,
                retry_count, timeout_seconds, custom_headers,
                created_at, updated_at, last_triggered_at,
                total_deliveries, successful_deliveries, failed_deliveries"
        )
        .bind(id)
        .bind(&config.name)
        .bind(&config.url)
        .bind(&config.secret)
        .bind(config.active)
        .bind(&config.event_types)
        .bind(&config.path_pattern)
        .bind(&config.object_type)
        .bind(config.building_id)
        .bind(config.retry_count)
        .bind(config.timeout_seconds)
        .bind(&config.custom_headers)
        .bind(now.naive_utc())
        .fetch_one(&self.pool)
        .await?;
        
        Ok(Self::row_to_webhook(&row))
    }
    
    /// Delete a webhook
    pub async fn delete_webhook(&self, id: Uuid) -> Result<()> {
        sqlx::query("DELETE FROM webhooks WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await?;
        
        Ok(())
    }
    
    /// List webhooks
    pub async fn list_webhooks(&self, active_only: bool) -> Result<Vec<Webhook>> {
        let query = if active_only {
            "SELECT 
                id, name, url, secret, active,
                event_types, path_pattern, object_type, building_id,
                retry_count, timeout_seconds, custom_headers,
                created_at, updated_at, last_triggered_at,
                total_deliveries, successful_deliveries, failed_deliveries
            FROM webhooks
            WHERE active = true
            ORDER BY created_at DESC"
        } else {
            "SELECT 
                id, name, url, secret, active,
                event_types, path_pattern, object_type, building_id,
                retry_count, timeout_seconds, custom_headers,
                created_at, updated_at, last_triggered_at,
                total_deliveries, successful_deliveries, failed_deliveries
            FROM webhooks
            ORDER BY created_at DESC"
        };
        
        let rows = sqlx::query(query)
            .fetch_all(&self.pool)
            .await?;
        
        Ok(rows.iter().map(Self::row_to_webhook).collect())
    }
    
    /// Get a specific webhook
    pub async fn get_webhook(&self, id: Uuid) -> Result<Option<Webhook>> {
        let row = sqlx::query(
            "SELECT 
                id, name, url, secret, active,
                event_types, path_pattern, object_type, building_id,
                retry_count, timeout_seconds, custom_headers,
                created_at, updated_at, last_triggered_at,
                total_deliveries, successful_deliveries, failed_deliveries
            FROM webhooks
            WHERE id = $1"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;
        
        Ok(row.map(|r| Self::row_to_webhook(&r)))
    }
    
    /// Get webhooks that match an event
    pub async fn get_matching_webhooks(&self, event: &BuildingEvent) -> Result<Vec<Webhook>> {
        let webhooks = self.list_webhooks(true).await?;
        
        Ok(webhooks
            .into_iter()
            .filter(|w| w.matches_event(event))
            .collect())
    }
    
    /// Get delivery logs for a webhook
    pub async fn get_delivery_logs(
        &self,
        webhook_id: Uuid,
        limit: Option<i32>,
    ) -> Result<Vec<WebhookDeliveryLog>> {
        let limit = limit.unwrap_or(100) as i64;
        
        let rows = sqlx::query(
            "SELECT 
                id, webhook_id, event_id,
                url, method, headers, payload,
                status_code, response_body, response_headers,
                delivered, error_message, attempt_number,
                created_at, delivered_at, duration_ms
            FROM webhook_deliveries
            WHERE webhook_id = $1
            ORDER BY created_at DESC
            LIMIT $2"
        )
        .bind(webhook_id)
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;
        
        Ok(rows.iter().map(Self::row_to_delivery_log).collect())
    }
    
    /// Convert a database row to a Webhook
    fn row_to_webhook(row: &sqlx::postgres::PgRow) -> Webhook {
        Webhook {
            id: row.get("id"),
            name: row.get("name"),
            url: row.get("url"),
            secret: row.get("secret"),
            active: row.get("active"),
            event_types: row.get("event_types"),
            path_pattern: row.get("path_pattern"),
            object_type: row.get("object_type"),
            building_id: row.get("building_id"),
            retry_count: row.get("retry_count"),
            timeout_seconds: row.get("timeout_seconds"),
            custom_headers: row.get("custom_headers"),
            created_at: DateTime::from_naive_utc_and_offset(row.get::<NaiveDateTime, _>("created_at"), Utc),
            updated_at: DateTime::from_naive_utc_and_offset(row.get::<NaiveDateTime, _>("updated_at"), Utc),
            last_triggered_at: row.get::<Option<NaiveDateTime>, _>("last_triggered_at")
                .map(|dt| DateTime::from_naive_utc_and_offset(dt, Utc)),
            total_deliveries: row.get("total_deliveries"),
            successful_deliveries: row.get("successful_deliveries"),
            failed_deliveries: row.get("failed_deliveries"),
        }
    }
    
    /// Convert a database row to a WebhookDeliveryLog
    fn row_to_delivery_log(row: &sqlx::postgres::PgRow) -> WebhookDeliveryLog {
        WebhookDeliveryLog {
            id: row.get("id"),
            webhook_id: row.get("webhook_id"),
            event_id: row.get("event_id"),
            url: row.get("url"),
            method: row.get("method"),
            headers: row.get("headers"),
            payload: row.get("payload"),
            status_code: row.get("status_code"),
            response_body: row.get("response_body"),
            response_headers: row.get("response_headers"),
            delivered: row.get("delivered"),
            error_message: row.get("error_message"),
            attempt_number: row.get("attempt_number"),
            created_at: DateTime::from_naive_utc_and_offset(row.get::<NaiveDateTime, _>("created_at"), Utc),
            delivered_at: row.get::<Option<NaiveDateTime>, _>("delivered_at")
                .map(|dt| DateTime::from_naive_utc_and_offset(dt, Utc)),
            duration_ms: row.get("duration_ms"),
        }
    }
}