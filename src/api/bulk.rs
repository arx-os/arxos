//! Bulk operations API handlers

use crate::api::{ApiError, ApiResult};
use crate::api::extractors::ApiKey;
use crate::bulk::{BulkSystem, BulkFilter, BulkChanges};
use axum::{
    extract::{Path, State, Query},
    Json,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;
use uuid::Uuid;

#[derive(Debug, Deserialize)]
pub struct BulkUpdateRequest {
    pub building_id: Uuid,
    pub filter: BulkFilter,
    pub changes: BulkChanges,
}

#[derive(Debug, Deserialize)]
pub struct BulkDeleteRequest {
    pub building_id: Uuid,
    pub filter: BulkFilter,
}

#[derive(Debug, Deserialize)]
pub struct OperationQuery {
    pub building_id: Option<Uuid>,
    pub limit: Option<i32>,
}

#[derive(Debug, Deserialize)]
pub struct HistoryQuery {
    pub path_pattern: Option<String>,
    pub operation: Option<String>,
    pub limit: Option<i32>,
}

/// Execute bulk update operation
pub async fn bulk_update(
    _auth: ApiKey,
    State(bulk_system): State<Arc<BulkSystem>>,
    Json(request): Json<BulkUpdateRequest>,
) -> ApiResult<Json<Value>> {
    let result = bulk_system
        .bulk_update(
            request.building_id,
            request.filter,
            request.changes,
            Some("api".to_string()),
        )
        .await?;
    
    Ok(Json(json!({
        "result": result,
        "message": format!("Bulk update completed. {} objects affected.", result.affected_count)
    })))
}

/// Execute bulk delete operation
pub async fn bulk_delete(
    _auth: ApiKey,
    State(bulk_system): State<Arc<BulkSystem>>,
    Json(request): Json<BulkDeleteRequest>,
) -> ApiResult<Json<Value>> {
    let result = bulk_system
        .bulk_delete(
            request.building_id,
            request.filter,
            Some("api".to_string()),
        )
        .await?;
    
    Ok(Json(json!({
        "result": result,
        "message": format!("Bulk delete completed. {} objects affected.", result.affected_count)
    })))
}

/// Get bulk operation status
pub async fn get_operation_status(
    _auth: ApiKey,
    Path(operation_id): Path<Uuid>,
    State(bulk_system): State<Arc<BulkSystem>>,
) -> ApiResult<Json<Value>> {
    match bulk_system.get_operation_status(operation_id).await? {
        Some(operation) => Ok(Json(json!(operation))),
        None => Err(ApiError::NotFound(format!("Operation {} not found", operation_id))),
    }
}

/// List recent bulk operations
pub async fn list_operations(
    _auth: ApiKey,
    Query(query): Query<OperationQuery>,
    State(bulk_system): State<Arc<BulkSystem>>,
) -> ApiResult<Json<Value>> {
    let operations = bulk_system
        .list_operations(query.building_id, query.limit)
        .await?;
    
    Ok(Json(json!({
        "operations": operations,
        "count": operations.len(),
    })))
}

/// Get object history
pub async fn get_object_history(
    _auth: ApiKey,
    Path(object_id): Path<Uuid>,
    Query(query): Query<OperationQuery>,
    State(bulk_system): State<Arc<BulkSystem>>,
) -> ApiResult<Json<Value>> {
    let history = bulk_system
        .get_object_history(object_id, query.limit)
        .await?;
    
    Ok(Json(json!({
        "history": history,
        "count": history.len(),
        "object_id": object_id,
    })))
}

/// Get building history
pub async fn get_building_history(
    _auth: ApiKey,
    Path(building_id): Path<Uuid>,
    Query(query): Query<HistoryQuery>,
    State(bulk_system): State<Arc<BulkSystem>>,
) -> ApiResult<Json<Value>> {
    let history = bulk_system
        .get_building_history(
            building_id,
            query.path_pattern,
            query.operation,
            query.limit,
        )
        .await?;
    
    Ok(Json(json!({
        "history": history,
        "count": history.len(),
        "building_id": building_id,
    })))
}

/// Preview bulk operation (dry run)
pub async fn preview_bulk_update(
    _auth: ApiKey,
    State(bulk_system): State<Arc<BulkSystem>>,
    Json(request): Json<BulkUpdateRequest>,
) -> ApiResult<Json<Value>> {
    // This is a simplified preview - in a full implementation we'd execute the query
    // without actually modifying data to show what would be affected
    
    Ok(Json(json!({
        "message": "Preview functionality would show affected objects without making changes",
        "filter": request.filter,
        "changes": request.changes,
        "building_id": request.building_id,
        "note": "This is a placeholder - full implementation would run SELECT query to show affected objects"
    })))
}