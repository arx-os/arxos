//! Webhook API handlers

use crate::api::{ApiError, ApiResult};
use crate::api::extractors::ApiKey;
use crate::webhooks::{WebhookSystem, WebhookConfig};
pub use crate::webhooks::WebhookConfig as WebhookConfigType;
use axum::{
    extract::{Path, State, Query},
    Json,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::sync::Arc;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct WebhookQuery {
    active_only: Option<bool>,
}

/// List all webhooks
pub async fn list_webhooks(
    _auth: ApiKey,
    Query(query): Query<WebhookQuery>,
    State(webhooks): State<Arc<WebhookSystem>>,
) -> ApiResult<Json<Value>> {
    let active_only = query.active_only.unwrap_or(false);
    let webhook_list = webhooks.list_webhooks(active_only).await?;
    
    Ok(Json(json!({
        "webhooks": webhook_list,
        "count": webhook_list.len(),
    })))
}

/// Get a specific webhook
pub async fn get_webhook(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    State(webhooks): State<Arc<WebhookSystem>>,
) -> ApiResult<Json<Value>> {
    match webhooks.get_webhook(id).await? {
        Some(webhook) => Ok(Json(json!(webhook))),
        None => Err(ApiError::NotFound(format!("Webhook {} not found", id))),
    }
}

/// Create a new webhook
pub async fn create_webhook(
    _auth: ApiKey,
    State(webhooks): State<Arc<WebhookSystem>>,
    Json(config): Json<WebhookConfig>,
) -> ApiResult<Json<Value>> {
    let webhook = webhooks.register_webhook(config).await?;
    
    Ok(Json(json!({
        "webhook": webhook,
        "message": "Webhook created successfully",
    })))
}

/// Update a webhook
pub async fn update_webhook(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    State(webhooks): State<Arc<WebhookSystem>>,
    Json(config): Json<WebhookConfig>,
) -> ApiResult<Json<Value>> {
    let webhook = webhooks.update_webhook(id, config).await?;
    
    Ok(Json(json!({
        "webhook": webhook,
        "message": "Webhook updated successfully",
    })))
}

/// Delete a webhook
pub async fn delete_webhook(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    State(webhooks): State<Arc<WebhookSystem>>,
) -> ApiResult<Json<Value>> {
    webhooks.delete_webhook(id).await?;
    
    Ok(Json(json!({
        "message": format!("Webhook {} deleted successfully", id),
    })))
}

/// Test a webhook by sending a sample event
pub async fn test_webhook(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    State(webhooks): State<Arc<WebhookSystem>>,
) -> ApiResult<Json<Value>> {
    // Get the webhook
    let webhook = match webhooks.get_webhook(id).await? {
        Some(w) => w,
        None => return Err(ApiError::NotFound(format!("Webhook {} not found", id))),
    };
    
    // Create a test event
    let test_event = crate::events::BuildingEvent {
        id: Uuid::new_v4(),
        event_type: crate::events::EventType::ObjectUpdated,
        object_id: Some(Uuid::new_v4()),
        object_path: Some("/test/webhook".to_string()),
        metadata: crate::events::EventMetadata {
            operation: "test".to_string(),
            object_type: Some("test".to_string()),
            ..Default::default()
        },
        timestamp: chrono::Utc::now(),
    };
    
    // Queue the test delivery
    webhooks.process_event(&test_event).await?;
    
    Ok(Json(json!({
        "message": format!("Test event sent to webhook {}", id),
        "event": test_event,
    })))
}

#[derive(Debug, Deserialize)]
pub struct DeliveryLogQuery {
    limit: Option<i32>,
}

/// Get delivery logs for a webhook
pub async fn get_webhook_logs(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    Query(query): Query<DeliveryLogQuery>,
    State(webhooks): State<Arc<WebhookSystem>>,
) -> ApiResult<Json<Value>> {
    let logs = webhooks.get_delivery_logs(id, query.limit).await?;
    
    Ok(Json(json!({
        "logs": logs,
        "count": logs.len(),
        "webhook_id": id,
    })))
}