//! Enhanced logging and tracing

use axum::{
    extract::Request,
    response::Response,
};
use tower_http::trace::{TraceLayer, MakeSpan, OnRequest, OnResponse};
use tracing::{Span, Level};
use std::time::Duration;
use uuid::Uuid;

/// Request ID for correlation
#[derive(Debug, Clone)]
pub struct RequestId(pub String);

impl RequestId {
    pub fn new() -> Self {
        Self(Uuid::new_v4().to_string())
    }
    
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Custom trace layer for structured logging
pub struct LoggingLayer;

impl LoggingLayer {
    pub fn new() -> TraceLayer<
        tower_http::classify::SharedClassifier<tower_http::classify::ServerErrorsAsFailures>,
        impl MakeSpan<axum::body::Body> + Clone,
        impl OnRequest<axum::body::Body> + Clone,
        impl OnResponse<axum::body::Body> + Clone,
        (),
    > {
        TraceLayer::new_for_http()
            .make_span_with(|request: &Request| {
                let request_id = Uuid::new_v4().to_string();
                tracing::info_span!(
                    "http_request",
                    method = %request.method(),
                    uri = %request.uri(),
                    request_id = %request_id,
                    user_agent = ?request.headers().get("user-agent"),
                    content_length = ?request.headers().get("content-length"),
                )
            })
            .on_request(|request: &Request, _span: &Span| {
                tracing::info!(
                    method = %request.method(),
                    uri = %request.uri(),
                    "Started processing request"
                );
            })
            .on_response(|response: &Response, latency: Duration, _span: &Span| {
                tracing::info!(
                    status = %response.status(),
                    latency_ms = latency.as_millis(),
                    "Finished processing request"
                );
            })
    }
}

/// Initialize tracing for the application
pub fn init_tracing() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>> {
    use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};
    
    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| "arxos=info,tower_http=debug".into());
    
    // JSON formatting for production, pretty formatting for development
    let format_layer = if std::env::var("RUST_LOG_JSON").is_ok() {
        tracing_subscriber::fmt::layer()
            .json()
            .with_current_span(false)
            .with_span_list(true)
            .boxed()
    } else {
        tracing_subscriber::fmt::layer()
            .with_target(false)
            .compact()
            .boxed()
    };
    
    tracing_subscriber::registry()
        .with(env_filter)
        .with(format_layer)
        .init();
    
    Ok(())
}