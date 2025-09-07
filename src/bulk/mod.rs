//! Bulk operations for efficient batch processing

use anyhow::Result;
use serde::{Deserialize, Serialize};
use sqlx::{PgPool, Row};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use serde_json::Value;

pub mod operations;
pub mod types;

pub use operations::BulkProcessor;
pub use types::{BulkOperation, BulkFilter, BulkChanges, BulkResult};

/// Bulk operations system
pub struct BulkSystem {
    pool: PgPool,
    processor: BulkProcessor,
}

impl BulkSystem {
    /// Create new bulk system
    pub fn new(pool: PgPool) -> Self {
        let processor = BulkProcessor::new(pool.clone());
        Self { pool, processor }
    }
    
    /// Execute a bulk update operation
    pub async fn bulk_update(
        &self,
        building_id: Uuid,
        filter: BulkFilter,
        changes: BulkChanges,
        source: Option<String>,
    ) -> Result<BulkResult> {
        self.processor.execute_bulk_update(building_id, filter, changes, source).await
    }
    
    /// Execute a bulk delete operation
    pub async fn bulk_delete(
        &self,
        building_id: Uuid,
        filter: BulkFilter,
        source: Option<String>,
    ) -> Result<BulkResult> {
        self.processor.execute_bulk_delete(building_id, filter, source).await
    }
    
    /// Get bulk operation status
    pub async fn get_operation_status(&self, operation_id: Uuid) -> Result<Option<BulkOperation>> {
        self.processor.get_operation_status(operation_id).await
    }
    
    /// List recent bulk operations
    pub async fn list_operations(
        &self,
        building_id: Option<Uuid>,
        limit: Option<i32>,
    ) -> Result<Vec<BulkOperation>> {
        self.processor.list_operations(building_id, limit).await
    }
    
    /// Get object history
    pub async fn get_object_history(
        &self,
        object_id: Uuid,
        limit: Option<i32>,
    ) -> Result<Vec<ObjectHistoryEntry>> {
        let limit = limit.unwrap_or(50) as i64;
        
        let rows = sqlx::query(
            "SELECT 
                id, object_id, building_id, operation,
                path, name, object_type,
                old_properties, new_properties,
                old_state, new_state,
                old_metrics, new_metrics,
                changed_fields, change_summary,
                source, created_at
            FROM object_history
            WHERE object_id = $1
            ORDER BY created_at DESC
            LIMIT $2"
        )
        .bind(object_id)
        .bind(limit)
        .fetch_all(&self.pool)
        .await?;
        
        let entries = rows.into_iter().map(|row| {
            ObjectHistoryEntry {
                id: row.get("id"),
                object_id: row.get("object_id"),
                building_id: row.get("building_id"),
                operation: row.get("operation"),
                path: row.get("path"),
                name: row.get("name"),
                object_type: row.get("object_type"),
                old_properties: row.get("old_properties"),
                new_properties: row.get("new_properties"),
                old_state: row.get("old_state"),
                new_state: row.get("new_state"),
                old_metrics: row.get("old_metrics"),
                new_metrics: row.get("new_metrics"),
                changed_fields: row.get("changed_fields"),
                change_summary: row.get("change_summary"),
                source: row.get("source"),
                created_at: DateTime::from_naive_utc_and_offset(
                    row.get("created_at"), 
                    Utc
                ),
            }
        }).collect();
        
        Ok(entries)
    }
    
    /// Get building history
    pub async fn get_building_history(
        &self,
        building_id: Uuid,
        path_pattern: Option<String>,
        operation: Option<String>,
        limit: Option<i32>,
    ) -> Result<Vec<ObjectHistoryEntry>> {
        let limit = limit.unwrap_or(100) as i64;
        
        let mut query = "SELECT 
            id, object_id, building_id, operation,
            path, name, object_type,
            old_properties, new_properties,
            old_state, new_state,
            old_metrics, new_metrics,
            changed_fields, change_summary,
            source, created_at
        FROM object_history
        WHERE building_id = $1".to_string();
        
        let mut param_count = 1;
        let mut params: Vec<Box<dyn sqlx::Encode<'_, sqlx::Postgres> + Send + Sync>> = vec![
            Box::new(building_id)
        ];
        
        if let Some(pattern) = &path_pattern {
            param_count += 1;
            query.push_str(&format!(" AND path LIKE ${}", param_count));
            params.push(Box::new(format!("{}%", pattern)));
        }
        
        if let Some(op) = &operation {
            param_count += 1;
            query.push_str(&format!(" AND operation = ${}", param_count));
            params.push(Box::new(op.clone()));
        }
        
        query.push_str(" ORDER BY created_at DESC");
        
        param_count += 1;
        query.push_str(&format!(" LIMIT ${}", param_count));
        params.push(Box::new(limit));
        
        // Note: This is simplified - in practice we'd use a dynamic query builder
        let rows = sqlx::query(&query)
            .bind(building_id)
            .bind(limit)
            .fetch_all(&self.pool)
            .await?;
        
        let entries = rows.into_iter().map(|row| {
            ObjectHistoryEntry {
                id: row.get("id"),
                object_id: row.get("object_id"),
                building_id: row.get("building_id"),
                operation: row.get("operation"),
                path: row.get("path"),
                name: row.get("name"),
                object_type: row.get("object_type"),
                old_properties: row.get("old_properties"),
                new_properties: row.get("new_properties"),
                old_state: row.get("old_state"),
                new_state: row.get("new_state"),
                old_metrics: row.get("old_metrics"),
                new_metrics: row.get("new_metrics"),
                changed_fields: row.get("changed_fields"),
                change_summary: row.get("change_summary"),
                source: row.get("source"),
                created_at: DateTime::from_naive_utc_and_offset(
                    row.get("created_at"), 
                    Utc
                ),
            }
        }).collect();
        
        Ok(entries)
    }
}

/// Object history entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectHistoryEntry {
    pub id: Uuid,
    pub object_id: Uuid,
    pub building_id: Uuid,
    pub operation: String,
    pub path: String,
    pub name: String,
    pub object_type: String,
    pub old_properties: Option<Value>,
    pub new_properties: Option<Value>,
    pub old_state: Option<Value>,
    pub new_state: Option<Value>,
    pub old_metrics: Option<Value>,
    pub new_metrics: Option<Value>,
    pub changed_fields: Option<Vec<String>>,
    pub change_summary: Option<String>,
    pub source: Option<String>,
    pub created_at: DateTime<Utc>,
}