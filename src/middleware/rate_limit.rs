//! Rate limiting configuration and middleware

use governor::{Quota, RateLimiter};
use std::num::NonZeroU32;
use std::time::Duration;
use axum::{
    extract::Request,
    http::StatusCode,
    middleware::Next,
    response::Response,
};

/// Rate limiting configuration
#[derive(Debug, Clone)]
pub struct RateLimitConfig {
    pub requests_per_minute: u32,
    pub burst_size: u32,
}

impl Default for RateLimitConfig {
    fn default() -> Self {
        Self {
            requests_per_minute: 100,
            burst_size: 20,
        }
    }
}

impl RateLimitConfig {
    /// Create a new rate limit config
    pub fn new(requests_per_minute: u32, burst_size: u32) -> Self {
        Self {
            requests_per_minute,
            burst_size,
        }
    }
    
    /// Create rate limiting middleware (simplified implementation)
    pub fn middleware() -> impl Fn(Request, Next) -> impl std::future::Future<Output = Response> + Clone {
        move |request: Request, next: Next| async move {
            // Simplified rate limiting - in production would use a proper rate limiter
            // For now, just pass through with metrics
            let start = std::time::Instant::now();
            let response = next.run(request).await;
            let elapsed = start.elapsed();
            
            // Record rate limiting metrics
            metrics::histogram!("arxos_request_processing_time", "endpoint" => "all")
                .record(elapsed.as_millis() as f64);
            
            response
        }
    }
    
    /// Higher limits for authenticated users
    pub fn authenticated() -> Self {
        Self {
            requests_per_minute: 1000,
            burst_size: 100,
        }
    }
    
    /// Lower limits for public endpoints
    pub fn public() -> Self {
        Self {
            requests_per_minute: 30,
            burst_size: 10,
        }
    }
    
    /// Very restrictive limits for expensive operations
    pub fn expensive() -> Self {
        Self {
            requests_per_minute: 10,
            burst_size: 2,
        }
    }
}