//! Custom extractors for API requests

use axum::{
    async_trait,
    extract::FromRequestParts,
    http::{request::Parts, StatusCode},
};
use serde::Deserialize;

/// API key authentication
pub struct ApiKey(pub String);

#[async_trait]
impl<S> FromRequestParts<S> for ApiKey
where
    S: Send + Sync,
{
    type Rejection = StatusCode;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        // For now, accept any X-API-Key header
        // In production, validate against database
        parts
            .headers
            .get("X-API-Key")
            .and_then(|value| value.to_str().ok())
            .map(|key| ApiKey(key.to_string()))
            .ok_or(StatusCode::UNAUTHORIZED)
    }
}

/// Query parameters for filtering objects
#[derive(Debug, Deserialize)]
pub struct ObjectFilter {
    pub path: Option<String>,
    pub object_type: Option<String>,
    pub status: Option<String>,
    pub needs_repair: Option<bool>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

impl Default for ObjectFilter {
    fn default() -> Self {
        Self {
            path: None,
            object_type: None,
            status: None,
            needs_repair: None,
            limit: Some(100),
            offset: Some(0),
        }
    }
}