//! REST API for ArxOS
//! 
//! Provides HTTP endpoints for external integrations (N8N, Zapier, etc.)

pub mod handlers;
pub mod routes;
pub mod error;
pub mod extractors;
pub mod sse;
pub mod webhooks;
pub mod bulk;
pub mod d3_endpoints;

pub use routes::create_router;
pub use error::{ApiError, ApiResult};