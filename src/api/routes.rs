//! API route configuration

use crate::api::handlers::*;
use crate::api::sse::{event_stream, get_recent_events};
use crate::api::webhooks;
use crate::api::bulk;
use crate::database::Database;
use crate::events::EventSystem;
use crate::webhooks::WebhookSystem;
use crate::bulk::BulkSystem;
use crate::rating::RatingService;
use crate::market::MarketService;
use crate::health::HealthService;
use crate::middleware;
use crate::docs;
use axum::{
    routing::{get, post, patch, delete},
    Router,
    middleware::from_fn,
};
use std::sync::Arc;
use tower_http::{
    compression::CompressionLayer,
};
use sqlx::PgPool;

/// Create the API router with all routes
pub fn create_router(
    database: Arc<Database>, 
    event_system: Arc<EventSystem>,
    webhook_system: Arc<WebhookSystem>,
    bulk_system: Arc<BulkSystem>,
    rating_service: Arc<RatingService>,
    market_service: Arc<MarketService>,
    health_service: Arc<HealthService>,
    db_pool: Arc<PgPool>,
) -> Router {
    // Database routes
    let db_routes = Router::new()
        // Object CRUD operations
        .route("/api/objects", get(list_objects).post(create_object))
        .route("/api/objects/:id", 
            get(get_object)
            .patch(update_object)
            .delete(delete_object)
        )
        // Query endpoint
        .route("/api/query", post(execute_query))
        .with_state(database);
    
    // Event routes
    let event_routes = Router::new()
        .route("/api/events", get(event_stream))
        .route("/api/events/recent", get(get_recent_events))
        .with_state(event_system);
    
    // Webhook routes
    let webhook_routes = Router::new()
        .route("/api/webhooks", 
            get(webhooks::list_webhooks)
            .post(webhooks::create_webhook)
        )
        .route("/api/webhooks/:id",
            get(webhooks::get_webhook)
            .patch(webhooks::update_webhook)
            .delete(webhooks::delete_webhook)
        )
        .route("/api/webhooks/:id/test", post(webhooks::test_webhook))
        .route("/api/webhooks/:id/logs", get(webhooks::get_webhook_logs))
        .with_state(webhook_system);
    
    // Bulk operations routes
    let bulk_routes = Router::new()
        .route("/api/bulk/update", post(bulk::bulk_update))
        .route("/api/bulk/delete", post(bulk::bulk_delete))
        .route("/api/bulk/update/preview", post(bulk::preview_bulk_update))
        .route("/api/bulk/operations", get(bulk::list_operations))
        .route("/api/bulk/operations/:id", get(bulk::get_operation_status))
        .route("/api/objects/:id/history", get(bulk::get_object_history))
        .route("/api/buildings/:id/history", get(bulk::get_building_history))
        .with_state(bulk_system);
    
    // BILT Rating routes
    let rating_routes = crate::rating::rating_routes(rating_service);
    
    // Market & Token Economics routes
    let market_routes = crate::market::market_routes(market_service);
    
    // Health and system routes
    let system_routes = crate::health::health_routes(db_pool, health_service);
    
    // Documentation routes
    let docs_routes = docs::docs_routes();
    
    Router::new()
        // Merge route groups
        .merge(system_routes)
        .merge(db_routes)
        .merge(event_routes)
        .merge(webhook_routes)
        .merge(bulk_routes)
        .merge(rating_routes)
        .merge(market_routes)
        .merge(docs_routes)
        
        // Add production middleware
        .layer(from_fn(middleware::security_headers_middleware))
        .layer(from_fn(middleware::api_versioning_middleware))
        .layer(from_fn(middleware::request_middleware))
        .layer(from_fn(middleware::rate_limiting_middleware))
        
        // Add other middleware
        .layer(middleware::cors::cors_layer())
        .layer(CompressionLayer::new())
}