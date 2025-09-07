//! CORS configuration for production

use tower_http::cors::{CorsLayer, Any};
use axum::http::{HeaderValue, Method};

/// Production CORS configuration
pub fn production_cors() -> CorsLayer {
    CorsLayer::new()
        .allow_origin([
            "https://app.arxos.io".parse::<HeaderValue>().unwrap(),
            "https://admin.arxos.io".parse::<HeaderValue>().unwrap(),
            "http://localhost:3000".parse::<HeaderValue>().unwrap(),
            "http://localhost:5173".parse::<HeaderValue>().unwrap(), // Vite dev
        ])
        .allow_methods([
            Method::GET,
            Method::POST,
            Method::PATCH,
            Method::DELETE,
            Method::OPTIONS,
        ])
        .allow_headers(Any)
        .allow_credentials(true)
        .max_age(std::time::Duration::from_secs(86400)) // 24 hours
}

/// Development CORS configuration (permissive)
pub fn development_cors() -> CorsLayer {
    CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any)
        .allow_credentials(true)
}

/// Get appropriate CORS layer based on environment
pub fn cors_layer() -> CorsLayer {
    if std::env::var("ARXOS_ENV").unwrap_or_else(|_| "development".to_string()) == "production" {
        production_cors()
    } else {
        development_cors()
    }
}