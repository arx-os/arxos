//! Health check and system status

use axum::{
    extract::State,
    response::Json,
    routing::get,
    Router,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use std::sync::Arc;
use chrono::{DateTime, Utc};
use std::time::{SystemTime, UNIX_EPOCH};

/// System health status
#[derive(Debug, Serialize, Deserialize)]
pub struct HealthStatus {
    pub status: String,
    pub version: String,
    pub uptime_seconds: u64,
    pub database: DatabaseHealth,
    pub timestamp: DateTime<Utc>,
    pub environment: String,
}

/// Database health information
#[derive(Debug, Serialize, Deserialize)]
pub struct DatabaseHealth {
    pub status: String,
    pub active_connections: usize,
    pub response_time_ms: Option<u64>,
}

/// Health check service
pub struct HealthService {
    start_time: SystemTime,
    version: String,
    environment: String,
}

impl HealthService {
    /// Create new health service
    pub fn new() -> Self {
        Self {
            start_time: SystemTime::now(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            environment: std::env::var("ARXOS_ENV").unwrap_or_else(|_| "development".to_string()),
        }
    }
    
    /// Get system health status
    pub async fn get_health(&self, pool: &PgPool) -> HealthStatus {
        let uptime = self.start_time
            .elapsed()
            .unwrap_or_default()
            .as_secs();
        
        let database = self.check_database_health(pool).await;
        
        let overall_status = if database.status == "healthy" {
            "healthy"
        } else {
            "unhealthy"
        };
        
        HealthStatus {
            status: overall_status.to_string(),
            version: self.version.clone(),
            uptime_seconds: uptime,
            database,
            timestamp: Utc::now(),
            environment: self.environment.clone(),
        }
    }
    
    /// Check database health
    async fn check_database_health(&self, pool: &PgPool) -> DatabaseHealth {
        let start = std::time::Instant::now();
        
        // Test database connectivity
        let status = match sqlx::query("SELECT 1 as test").fetch_one(pool).await {
            Ok(_) => "healthy",
            Err(_) => "unhealthy",
        };
        
        let response_time = if status == "healthy" {
            Some(start.elapsed().as_millis() as u64)
        } else {
            None
        };
        
        DatabaseHealth {
            status: status.to_string(),
            active_connections: pool.size() as usize,
            response_time_ms: response_time,
        }
    }
}

/// Combined state for health handlers
#[derive(Clone)]
pub struct HealthState {
    pub pool: Arc<PgPool>,
    pub service: Arc<HealthService>,
}

/// Health check handler
pub async fn health_check(
    State(state): State<HealthState>,
) -> Json<HealthStatus> {
    Json(state.service.get_health(&state.pool).await)
}

/// Readiness check handler
pub async fn readiness_check(
    State(state): State<HealthState>,
) -> Result<Json<serde_json::Value>, axum::http::StatusCode> {
    // Check critical dependencies
    match sqlx::query("SELECT 1").fetch_one(state.pool.as_ref()).await {
        Ok(_) => Ok(Json(serde_json::json!({
            "status": "ready",
            "timestamp": Utc::now()
        }))),
        Err(_) => Err(axum::http::StatusCode::SERVICE_UNAVAILABLE),
    }
}

/// Liveness check handler
pub async fn liveness_check() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "alive",
        "timestamp": Utc::now()
    }))
}

/// Create health check routes
pub fn health_routes(pool: Arc<PgPool>, health_service: Arc<HealthService>) -> Router {
    let state = HealthState {
        pool,
        service: health_service,
    };
    
    Router::new()
        .route("/api/health", get(health_check))
        .route("/api/health/ready", get(readiness_check))
        .route("/api/health/live", get(liveness_check))
        .with_state(state)
}