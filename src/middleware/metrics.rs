//! Metrics collection and exposition

use axum::{
    extract::Request,
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::get,
    Router,
};
use metrics_exporter_prometheus::PrometheusBuilder;
use std::time::Instant;

/// Metrics layer for collecting application metrics
pub struct MetricsLayer;

impl MetricsLayer {
    /// Initialize metrics collection
    pub fn init() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>> {
        let builder = PrometheusBuilder::new();
        builder.install()?;
        
        // Register custom metrics
        metrics::describe_counter!(
            "arxos_requests_total",
            "Total number of HTTP requests received"
        );
        
        metrics::describe_histogram!(
            "arxos_request_duration_ms",
            "HTTP request duration in milliseconds"
        );
        
        metrics::describe_counter!(
            "arxos_errors_total",
            "Total number of HTTP errors"
        );
        
        metrics::describe_gauge!(
            "arxos_active_connections",
            "Number of active connections"
        );
        
        metrics::describe_gauge!(
            "arxos_database_connections",
            "Number of active database connections"
        );
        
        metrics::describe_counter!(
            "arxos_webhook_deliveries_total",
            "Total webhook deliveries attempted"
        );
        
        metrics::describe_counter!(
            "arxos_bulk_operations_total",
            "Total bulk operations executed"
        );
        
        metrics::describe_histogram!(
            "arxos_bulk_operation_duration_ms",
            "Bulk operation duration in milliseconds"
        );
        
        metrics::describe_gauge!(
            "arxos_objects_total",
            "Total number of building objects"
        );
        
        Ok(())
    }
    
    /// Create metrics endpoint router
    pub fn routes() -> Router {
        Router::new().route("/metrics", get(metrics_handler))
    }
}

/// Prometheus metrics endpoint
async fn metrics_handler() -> Response {
    match metrics_exporter_prometheus::render() {
        Ok(metrics) => (StatusCode::OK, [("content-type", "text/plain")], metrics).into_response(),
        Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to render metrics").into_response(),
    }
}

/// Record a request metric
pub fn record_request(method: &str, status: u16, duration_ms: u64) {
    metrics::counter!(
        "arxos_requests_total",
        "method" => method.to_string(),
        "status" => status.to_string()
    ).increment(1);
    
    metrics::histogram!(
        "arxos_request_duration_ms",
        "method" => method.to_string()
    ).record(duration_ms as f64);
}

/// Record an error metric
pub fn record_error(status: u16) {
    metrics::counter!(
        "arxos_errors_total",
        "status" => status.to_string()
    ).increment(1);
}

/// Record webhook delivery
pub fn record_webhook_delivery(success: bool) {
    metrics::counter!(
        "arxos_webhook_deliveries_total",
        "success" => success.to_string()
    ).increment(1);
}

/// Record bulk operation
pub fn record_bulk_operation(operation_type: &str, duration_ms: u64, affected_count: u32) {
    metrics::counter!(
        "arxos_bulk_operations_total",
        "type" => operation_type.to_string()
    ).increment(1);
    
    metrics::histogram!(
        "arxos_bulk_operation_duration_ms",
        "type" => operation_type.to_string()
    ).record(duration_ms as f64);
    
    metrics::gauge!("arxos_objects_total").set(affected_count as f64);
}

/// Update database connection gauge
pub fn update_database_connections(count: usize) {
    metrics::gauge!("arxos_database_connections").set(count as f64);
}