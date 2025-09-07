//! Bulk operation processing

use crate::bulk::types::{BulkOperation, BulkFilter, BulkChanges, BulkResult};
use anyhow::Result;
use sqlx::{PgPool, Row};
use uuid::Uuid;
use chrono::Utc;
use serde_json::Value;

/// Bulk operation processor
pub struct BulkProcessor {
    pool: PgPool,
}

impl BulkProcessor {
    /// Create new bulk processor
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
    
    /// Execute bulk update operation
    pub async fn execute_bulk_update(
        &self,
        building_id: Uuid,
        filter: BulkFilter,
        changes: BulkChanges,
        source: Option<String>,
    ) -> Result<BulkResult> {
        let operation_id = Uuid::new_v4();
        let started_at = Utc::now();
        let source = source.unwrap_or_else(|| "api".to_string());
        
        // Start transaction
        let mut tx = self.pool.begin().await?;
        
        // Record the bulk operation
        sqlx::query(
            "INSERT INTO bulk_operations (
                id, building_id, operation_type, filter, changes, 
                status, started_at, source
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"
        )
        .bind(operation_id)
        .bind(building_id)
        .bind("update")
        .bind(serde_json::to_value(&filter)?)
        .bind(serde_json::to_value(&changes)?)
        .bind("processing")
        .bind(started_at.naive_utc())
        .bind(&source)
        .execute(&mut *tx)
        .await?;
        
        // Set source for history tracking
        sqlx::query(&format!("SET SESSION arxos.source = '{}'", source))
            .execute(&mut *tx)
            .await?;
        
        let (where_clause, params) = filter.to_sql_where();
        
        // Find matching objects first
        let find_query = format!(
            "SELECT id FROM building_objects WHERE building_id = $1 AND {}",
            where_clause
        );
        
        let mut query = sqlx::query(&find_query).bind(building_id);
        for param in &params {
            query = query.bind(param);
        }
        
        let rows = query.fetch_all(&mut *tx).await?;
        let affected_objects: Vec<Uuid> = rows.iter().map(|r| r.get("id")).collect();
        let affected_count = affected_objects.len() as i32;
        
        if affected_count == 0 {
            // Complete operation with no changes
            sqlx::query(
                "UPDATE bulk_operations SET 
                    status = 'completed', 
                    completed_at = $2,
                    affected_count = 0
                WHERE id = $1"
            )
            .bind(operation_id)
            .bind(Utc::now().naive_utc())
            .execute(&mut *tx)
            .await?;
            
            tx.commit().await?;
            
            return Ok(BulkResult {
                operation_id,
                affected_count: 0,
                affected_objects: vec![],
                status: "completed".to_string(),
                started_at,
                completed_at: Some(Utc::now()),
                error_message: None,
            });
        }
        
        // Build update query
        let mut update_parts = Vec::new();
        let mut update_params = Vec::new();
        let mut param_count = 0;
        
        let merge_json = changes.merge_json.unwrap_or(true);
        
        if let Some(ref props) = changes.properties {
            param_count += 1;
            if merge_json {
                update_parts.push(format!("properties = properties || ${}", param_count));
            } else {
                update_parts.push(format!("properties = ${}", param_count));
            }
            update_params.push(props.clone());
        }
        
        if let Some(ref state_changes) = changes.state {
            param_count += 1;
            if merge_json {
                update_parts.push(format!("state = state || ${}", param_count));
            } else {
                update_parts.push(format!("state = ${}", param_count));
            }
            update_params.push(state_changes.clone());
        }
        
        if let Some(ref metrics) = changes.metrics {
            param_count += 1;
            if merge_json {
                update_parts.push(format!("metrics = metrics || ${}", param_count));
            } else {
                update_parts.push(format!("metrics = ${}", param_count));
            }
            update_params.push(metrics.clone());
        }
        
        // Always update the updated_at timestamp
        param_count += 1;
        update_parts.push(format!("updated_at = ${}", param_count));
        update_params.push(serde_json::json!(Utc::now().naive_utc()));
        
        if update_parts.is_empty() {
            return Err(anyhow::anyhow!("No changes specified for bulk update"));
        }
        
        // Execute the bulk update
        let update_query = format!(
            "UPDATE building_objects SET {} WHERE building_id = $1 AND {}",
            update_parts.join(", "),
            where_clause
        );
        
        let mut query = sqlx::query(&update_query).bind(building_id);
        for param in &params {
            query = query.bind(param);
        }
        for param in &update_params {
            query = query.bind(param);
        }
        
        let result = query.execute(&mut *tx).await?;
        let actual_affected = result.rows_affected() as i32;
        
        let completed_at = Utc::now();
        
        // Update the bulk operation record
        sqlx::query(
            "UPDATE bulk_operations SET 
                status = 'completed',
                completed_at = $2,
                affected_count = $3,
                affected_objects = $4
            WHERE id = $1"
        )
        .bind(operation_id)
        .bind(completed_at.naive_utc())
        .bind(actual_affected)
        .bind(&affected_objects)
        .execute(&mut *tx)
        .await?;
        
        tx.commit().await?;
        
        Ok(BulkResult {
            operation_id,
            affected_count: actual_affected,
            affected_objects,
            status: "completed".to_string(),
            started_at,
            completed_at: Some(completed_at),
            error_message: None,
        })
    }
    
    /// Execute bulk delete operation
    pub async fn execute_bulk_delete(
        &self,
        building_id: Uuid,
        filter: BulkFilter,
        source: Option<String>,
    ) -> Result<BulkResult> {
        let operation_id = Uuid::new_v4();
        let started_at = Utc::now();
        let source = source.unwrap_or_else(|| "api".to_string());
        
        // Start transaction
        let mut tx = self.pool.begin().await?;
        
        // Record the bulk operation
        sqlx::query(
            "INSERT INTO bulk_operations (
                id, building_id, operation_type, filter,
                status, started_at, source
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)"
        )
        .bind(operation_id)
        .bind(building_id)
        .bind("delete")
        .bind(serde_json::to_value(&filter)?)
        .bind("processing")
        .bind(started_at.naive_utc())
        .bind(&source)
        .execute(&mut *tx)
        .await?;
        
        // Set source for history tracking
        sqlx::query(&format!("SET SESSION arxos.source = '{}'", source))
            .execute(&mut *tx)
            .await?;
        
        let (where_clause, params) = filter.to_sql_where();
        
        // Find matching objects first
        let find_query = format!(
            "SELECT id FROM building_objects WHERE building_id = $1 AND {}",
            where_clause
        );
        
        let mut query = sqlx::query(&find_query).bind(building_id);
        for param in &params {
            query = query.bind(param);
        }
        
        let rows = query.fetch_all(&mut *tx).await?;
        let affected_objects: Vec<Uuid> = rows.iter().map(|r| r.get("id")).collect();
        let affected_count = affected_objects.len() as i32;
        
        if affected_count == 0 {
            // Complete operation with no changes
            sqlx::query(
                "UPDATE bulk_operations SET 
                    status = 'completed', 
                    completed_at = $2,
                    affected_count = 0
                WHERE id = $1"
            )
            .bind(operation_id)
            .bind(Utc::now().naive_utc())
            .execute(&mut *tx)
            .await?;
            
            tx.commit().await?;
            
            return Ok(BulkResult {
                operation_id,
                affected_count: 0,
                affected_objects: vec![],
                status: "completed".to_string(),
                started_at,
                completed_at: Some(Utc::now()),
                error_message: None,
            });
        }
        
        // Execute the bulk delete
        let delete_query = format!(
            "DELETE FROM building_objects WHERE building_id = $1 AND {}",
            where_clause
        );
        
        let mut query = sqlx::query(&delete_query).bind(building_id);
        for param in &params {
            query = query.bind(param);
        }
        
        let result = query.execute(&mut *tx).await?;
        let actual_affected = result.rows_affected() as i32;
        
        let completed_at = Utc::now();
        
        // Update the bulk operation record
        sqlx::query(
            "UPDATE bulk_operations SET 
                status = 'completed',
                completed_at = $2,
                affected_count = $3,
                affected_objects = $4
            WHERE id = $1"
        )
        .bind(operation_id)
        .bind(completed_at.naive_utc())
        .bind(actual_affected)
        .bind(&affected_objects)
        .execute(&mut *tx)
        .await?;
        
        tx.commit().await?;
        
        Ok(BulkResult {
            operation_id,
            affected_count: actual_affected,
            affected_objects,
            status: "completed".to_string(),
            started_at,
            completed_at: Some(completed_at),
            error_message: None,
        })
    }
    
    /// Get operation status
    pub async fn get_operation_status(&self, operation_id: Uuid) -> Result<Option<BulkOperation>> {
        let row = sqlx::query(
            "SELECT 
                id, building_id, operation_type, filter, changes,
                affected_count, status, started_at, completed_at,
                error_message, affected_objects, source, created_at
            FROM bulk_operations
            WHERE id = $1"
        )
        .bind(operation_id)
        .fetch_optional(&self.pool)
        .await?;
        
        Ok(row.map(|r| BulkOperation {
            id: r.get("id"),
            building_id: r.get("building_id"),
            operation_type: r.get("operation_type"),
            filter: r.get("filter"),
            changes: r.get("changes"),
            affected_count: r.get("affected_count"),
            status: r.get("status"),
            started_at: r.get::<Option<chrono::NaiveDateTime>, _>("started_at")
                .map(|dt| chrono::DateTime::from_naive_utc_and_offset(dt, Utc)),
            completed_at: r.get::<Option<chrono::NaiveDateTime>, _>("completed_at")
                .map(|dt| chrono::DateTime::from_naive_utc_and_offset(dt, Utc)),
            error_message: r.get("error_message"),
            affected_objects: r.get("affected_objects"),
            source: r.get("source"),
            created_at: chrono::DateTime::from_naive_utc_and_offset(
                r.get("created_at"), 
                Utc
            ),
        }))
    }
    
    /// List recent operations
    pub async fn list_operations(
        &self,
        building_id: Option<Uuid>,
        limit: Option<i32>,
    ) -> Result<Vec<BulkOperation>> {
        let limit = limit.unwrap_or(50) as i64;
        
        // Simplified version - just handle the building_id case
        let rows = if let Some(bid) = building_id {
            sqlx::query(
                "SELECT 
                    id, building_id, operation_type, filter, changes,
                    affected_count, status, started_at, completed_at,
                    error_message, affected_objects, source, created_at
                FROM bulk_operations
                WHERE building_id = $1
                ORDER BY created_at DESC
                LIMIT $2"
            )
            .bind(bid)
            .bind(limit)
            .fetch_all(&self.pool)
            .await?
        } else {
            sqlx::query(
                "SELECT 
                    id, building_id, operation_type, filter, changes,
                    affected_count, status, started_at, completed_at,
                    error_message, affected_objects, source, created_at
                FROM bulk_operations
                ORDER BY created_at DESC
                LIMIT $1"
            )
            .bind(limit)
            .fetch_all(&self.pool)
            .await?
        };
        
        Ok(rows.into_iter().map(|r| BulkOperation {
            id: r.get("id"),
            building_id: r.get("building_id"),
            operation_type: r.get("operation_type"),
            filter: r.get("filter"),
            changes: r.get("changes"),
            affected_count: r.get("affected_count"),
            status: r.get("status"),
            started_at: r.get::<Option<chrono::NaiveDateTime>, _>("started_at")
                .map(|dt| chrono::DateTime::from_naive_utc_and_offset(dt, Utc)),
            completed_at: r.get::<Option<chrono::NaiveDateTime>, _>("completed_at")
                .map(|dt| chrono::DateTime::from_naive_utc_and_offset(dt, Utc)),
            error_message: r.get("error_message"),
            affected_objects: r.get("affected_objects"),
            source: r.get("source"),
            created_at: chrono::DateTime::from_naive_utc_and_offset(
                r.get("created_at"), 
                Utc
            ),
        }).collect())
    }
}