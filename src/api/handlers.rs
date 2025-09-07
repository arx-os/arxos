//! API request handlers

use crate::api::{ApiError, ApiResult};
use crate::api::extractors::{ApiKey, ObjectFilter};
use crate::database::Database;
use crate::models::BuildingObject;
use axum::{
    extract::{Path, State},
    Json,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::sync::Arc;
use uuid::Uuid;

/// List building objects with optional filtering
pub async fn list_objects(
    _auth: ApiKey,
    filter: axum::extract::Query<ObjectFilter>,
    State(db): State<Arc<Database>>,
) -> ApiResult<Json<Value>> {
    let mut query = String::from("SELECT * FROM building_objects WHERE 1=1");
    
    if let Some(path) = &filter.path {
        if path.ends_with('*') {
            let prefix = path.trim_end_matches('*');
            query.push_str(&format!(" AND path LIKE '{}%'", prefix));
        } else {
            query.push_str(&format!(" AND path = '{}'", path));
        }
    }
    
    if let Some(object_type) = &filter.object_type {
        query.push_str(&format!(" AND object_type = '{}'", object_type));
    }
    
    if let Some(status) = &filter.status {
        query.push_str(&format!(" AND status = '{}'", status));
    }
    
    if let Some(needs_repair) = filter.needs_repair {
        query.push_str(&format!(" AND needs_repair = {}", needs_repair));
    }
    
    query.push_str(&format!(
        " LIMIT {} OFFSET {}",
        filter.limit.unwrap_or(100),
        filter.offset.unwrap_or(0)
    ));
    
    // This is a simplified version - in production, use parameterized queries
    let objects = db.raw_query(&query).await?;
    
    Ok(Json(json!({
        "objects": objects,
        "count": objects.len(),
    })))
}

/// Get a specific object by ID
pub async fn get_object(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    State(db): State<Arc<Database>>,
) -> ApiResult<Json<Value>> {
    let object = db.get_object(id).await?
        .ok_or_else(|| ApiError::NotFound(format!("Object {} not found", id)))?;
    
    Ok(Json(json!(object)))
}

#[derive(Deserialize)]
pub struct CreateObjectRequest {
    pub path: String,
    pub object_type: String,
    pub location_x: Option<f32>,
    pub location_y: Option<f32>,
    pub location_z: Option<f32>,
    pub properties: Option<Value>,
    pub status: Option<String>,
}

/// Create a new object
pub async fn create_object(
    _auth: ApiKey,
    State(db): State<Arc<Database>>,
    Json(req): Json<CreateObjectRequest>,
) -> ApiResult<Json<Value>> {
    let id = Uuid::new_v4();
    
    db.create_object(
        id,
        req.path.clone(),
        req.object_type,
        req.location_x.unwrap_or(0.0),
        req.location_y.unwrap_or(0.0),
        req.location_z.unwrap_or(0.0),
        req.properties.unwrap_or(json!({})),
        req.status.unwrap_or_else(|| "active".to_string()),
    ).await?;
    
    Ok(Json(json!({
        "id": id.to_string(),
        "path": req.path,
        "message": "Object created successfully"
    })))
}

#[derive(Deserialize)]
pub struct UpdateObjectRequest {
    pub path: Option<String>,
    pub status: Option<String>,
    pub needs_repair: Option<bool>,
    pub health: Option<i32>,
    pub properties: Option<Value>,
    pub metrics: Option<Value>,
}

/// Update an existing object
pub async fn update_object(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    State(db): State<Arc<Database>>,
    Json(req): Json<UpdateObjectRequest>,
) -> ApiResult<Json<Value>> {
    // Check object exists
    let _existing = db.get_object(id).await?
        .ok_or_else(|| ApiError::NotFound(format!("Object {} not found", id)))?;
    
    db.update_object(id, req).await?;
    
    Ok(Json(json!({
        "id": id.to_string(),
        "message": "Object updated successfully"
    })))
}

/// Delete an object
pub async fn delete_object(
    _auth: ApiKey,
    Path(id): Path<Uuid>,
    State(db): State<Arc<Database>>,
) -> ApiResult<Json<Value>> {
    db.delete_object(id).await?;
    
    Ok(Json(json!({
        "message": "Object deleted successfully"
    })))
}

#[derive(Deserialize)]
pub struct QueryRequest {
    pub sql: String,
}

/// Execute a raw SQL query (with restrictions)
pub async fn execute_query(
    _auth: ApiKey,
    State(db): State<Arc<Database>>,
    Json(req): Json<QueryRequest>,
) -> ApiResult<Json<Value>> {
    // Validate query is SELECT only (no mutations)
    let query_upper = req.sql.to_uppercase();
    if !query_upper.trim().starts_with("SELECT") {
        return Err(ApiError::BadRequest("Only SELECT queries are allowed".to_string()));
    }
    
    if query_upper.contains("DELETE") || 
       query_upper.contains("UPDATE") || 
       query_upper.contains("INSERT") || 
       query_upper.contains("DROP") {
        return Err(ApiError::BadRequest("Mutation queries not allowed".to_string()));
    }
    
    let results = db.raw_query(&req.sql).await?;
    
    Ok(Json(json!({
        "results": results,
        "count": results.len(),
    })))
}

/// Health check endpoint
pub async fn health_check() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "service": "arxos-api",
        "version": env!("CARGO_PKG_VERSION"),
    }))
}