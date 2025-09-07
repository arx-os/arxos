//! Simplified production middleware

use axum::{
    extract::Request,
    http::{HeaderMap, StatusCode},
    middleware::Next,
    response::Response,
};
use std::time::Instant;

/// Simple request logging and metrics middleware
pub async fn request_middleware(
    request: Request,
    next: Next,
) -> Response {
    let start = Instant::now();
    let method = request.method().clone();
    let uri = request.uri().clone();
    
    // Generate request ID
    let request_id = uuid::Uuid::new_v4().to_string();
    
    // Log request
    tracing::info!(
        request_id = %request_id,
        method = %method,
        uri = %uri,
        "Request started"
    );
    
    let response = next.run(request).await;
    
    let elapsed = start.elapsed();
    let status = response.status();
    
    // Log response
    tracing::info!(
        request_id = %request_id,
        method = %method,
        uri = %uri,
        status = %status,
        duration_ms = elapsed.as_millis(),
        "Request completed"
    );
    
    response
}

/// API versioning middleware
pub async fn api_versioning_middleware(
    request: Request,
    next: Next,
) -> Response {
    // Check for API version header
    let version = request.headers()
        .get("X-API-Version")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("v1");
    
    if version != "v1" {
        return Response::builder()
            .status(StatusCode::BAD_REQUEST)
            .header("Content-Type", "application/json")
            .body(
                serde_json::json!({
                    "error": "Unsupported API version",
                    "supported_versions": ["v1"],
                    "requested_version": version
                })
                .to_string()
                .into()
            )
            .unwrap();
    }
    
    let mut response = next.run(request).await;
    response.headers_mut().insert("X-API-Version", "v1".parse().unwrap());
    response
}

/// Security headers middleware
pub async fn security_headers_middleware(
    request: Request,
    next: Next,
) -> Response {
    let mut response = next.run(request).await;
    
    let headers = response.headers_mut();
    headers.insert("X-Content-Type-Options", "nosniff".parse().unwrap());
    headers.insert("X-Frame-Options", "DENY".parse().unwrap());
    headers.insert("X-XSS-Protection", "1; mode=block".parse().unwrap());
    headers.insert("Referrer-Policy", "strict-origin-when-cross-origin".parse().unwrap());
    headers.insert("Content-Security-Policy", "default-src 'self'".parse().unwrap());
    
    response
}

/// Simple rate limiting placeholder
pub async fn rate_limiting_middleware(
    request: Request,
    next: Next,
) -> Response {
    // Placeholder for rate limiting - would implement proper rate limiting in production
    next.run(request).await
}