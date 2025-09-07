//! Bulk operation type definitions

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use serde_json::Value;

/// Bulk operation record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BulkOperation {
    pub id: Uuid,
    pub building_id: Uuid,
    pub operation_type: String,
    pub filter: Value,
    pub changes: Option<Value>,
    pub affected_count: i32,
    pub status: String,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
    pub affected_objects: Option<Vec<Uuid>>,
    pub source: Option<String>,
    pub created_at: DateTime<Utc>,
}

/// Filter criteria for bulk operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BulkFilter {
    /// Path pattern to match (e.g., "/electrical/circuits/%")
    pub path_pattern: Option<String>,
    
    /// Object type to filter by
    pub object_type: Option<String>,
    
    /// Parent object ID
    pub parent_id: Option<Uuid>,
    
    /// Property filters (key-value pairs)
    pub properties: Option<Value>,
    
    /// State filters
    pub state: Option<Value>,
    
    /// Created date range
    pub created_after: Option<DateTime<Utc>>,
    pub created_before: Option<DateTime<Utc>>,
    
    /// Updated date range
    pub updated_after: Option<DateTime<Utc>>,
    pub updated_before: Option<DateTime<Utc>>,
}

/// Changes to apply in bulk operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BulkChanges {
    /// Properties to update/merge
    pub properties: Option<Value>,
    
    /// State changes to apply
    pub state: Option<Value>,
    
    /// Metrics to update/merge
    pub metrics: Option<Value>,
    
    /// Whether to merge (true) or replace (false) JSON fields
    pub merge_json: Option<bool>,
}

/// Result of a bulk operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BulkResult {
    pub operation_id: Uuid,
    pub affected_count: i32,
    pub affected_objects: Vec<Uuid>,
    pub status: String,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
}

impl BulkFilter {
    /// Convert filter to SQL WHERE clause and parameters
    pub fn to_sql_where(&self) -> (String, Vec<String>) {
        let mut conditions = Vec::new();
        let mut params = Vec::new();
        let mut param_count = 0;
        
        if let Some(ref pattern) = self.path_pattern {
            param_count += 1;
            conditions.push(format!("path LIKE ${}", param_count));
            params.push(if pattern.contains('%') {
                pattern.clone()
            } else {
                format!("{}%", pattern)
            });
        }
        
        if let Some(ref obj_type) = self.object_type {
            param_count += 1;
            conditions.push(format!("object_type = ${}", param_count));
            params.push(obj_type.clone());
        }
        
        if let Some(parent_id) = self.parent_id {
            param_count += 1;
            conditions.push(format!("parent_id = ${}", param_count));
            params.push(parent_id.to_string());
        }
        
        if let Some(ref props) = self.properties {
            if let Value::Object(map) = props {
                for (key, value) in map {
                    param_count += 1;
                    conditions.push(format!("properties->>'{}' = ${}", key, param_count));
                    params.push(value.as_str().unwrap_or("").to_string());
                }
            }
        }
        
        if let Some(ref state_filter) = self.state {
            if let Value::Object(map) = state_filter {
                for (key, value) in map {
                    param_count += 1;
                    conditions.push(format!("state->>'{}' = ${}", key, param_count));
                    params.push(value.as_str().unwrap_or("").to_string());
                }
            }
        }
        
        if let Some(created_after) = self.created_after {
            param_count += 1;
            conditions.push(format!("created_at >= ${}", param_count));
            params.push(created_after.naive_utc().to_string());
        }
        
        if let Some(created_before) = self.created_before {
            param_count += 1;
            conditions.push(format!("created_at <= ${}", param_count));
            params.push(created_before.naive_utc().to_string());
        }
        
        if let Some(updated_after) = self.updated_after {
            param_count += 1;
            conditions.push(format!("updated_at >= ${}", param_count));
            params.push(updated_after.naive_utc().to_string());
        }
        
        if let Some(updated_before) = self.updated_before {
            param_count += 1;
            conditions.push(format!("updated_at <= ${}", param_count));
            params.push(updated_before.naive_utc().to_string());
        }
        
        let where_clause = if conditions.is_empty() {
            "1=1".to_string()
        } else {
            conditions.join(" AND ")
        };
        
        (where_clause, params)
    }
}