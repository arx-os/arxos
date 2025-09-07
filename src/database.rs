//! Database layer for ArxOS

use crate::models::{Building, BuildingObject, Location, Connection, ObjectState};
use anyhow::Result;
use sqlx::{PgPool, postgres::PgPoolOptions, Row, Column};
use uuid::Uuid;
use std::collections::HashMap;

#[derive(Clone)]
pub struct Database {
    pool: PgPool,
}

impl Database {
    pub async fn connect(url: &str) -> Result<Self> {
        let pool = PgPoolOptions::new()
            .max_connections(5)
            .connect(url)
            .await?;
        
        Ok(Self { pool })
    }
    
    pub async fn list_buildings(&self) -> Result<Vec<BuildingInfo>> {
        let rows = sqlx::query("SELECT id::text as id, name FROM buildings ORDER BY name")
            .fetch_all(&self.pool)
            .await?;
        
        let mut buildings = Vec::new();
        for row in rows {
            buildings.push(BuildingInfo {
                id: row.get("id"),
                name: row.get("name"),
            });
        }
        
        Ok(buildings)
    }
    
    pub async fn load_building(&self, building_id: &str) -> Result<Building> {
        // Load building info
        let building_row = sqlx::query("SELECT name FROM buildings WHERE id = $1")
            .bind(Uuid::parse_str(building_id)?)
            .fetch_one(&self.pool)
            .await?;
        
        let building_name: String = building_row.get("name");
        
        // Load all objects for this building
        let rows = sqlx::query(
            r#"
            SELECT 
                id,
                path,
                object_type,
                location,
                parent_id,
                children,
                connections,
                properties,
                state,
                created_at,
                updated_at
            FROM building_objects
            WHERE building_id = $1
            "#
        )
        .bind(Uuid::parse_str(building_id)?)
        .fetch_all(&self.pool)
        .await?;
        
        let mut object_map = HashMap::new();
        
        for row in rows {
            let location_json: serde_json::Value = row.get("location");
            let location = Location {
                space: location_json.get("space")
                    .and_then(|v| v.as_str())
                    .unwrap_or("/")
                    .to_string(),
                x: location_json.get("x")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.0) as f32,
                y: location_json.get("y")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.0) as f32,
                z: location_json.get("z")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.0) as f32,
                mounting: location_json.get("mounting")
                    .and_then(|v| v.as_str())
                    .unwrap_or("floor")
                    .to_string(),
            };
            
            let state_json: serde_json::Value = row.get("state");
            let state = ObjectState {
                status: state_json.get("status")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown")
                    .to_string(),
                health: state_json.get("health")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown")
                    .to_string(),
                needs_repair: state_json.get("needs_repair")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false),
                metrics: state_json.get("metrics")
                    .and_then(|v| v.as_object())
                    .map(|m| {
                        m.iter()
                            .filter_map(|(k, v)| v.as_f64().map(|n| (k.clone(), n)))
                            .collect()
                    })
                    .unwrap_or_default(),
            };
            
            let children_json: Option<serde_json::Value> = row.get("children");
            let children = if let Some(json) = children_json {
                if let Some(arr) = json.as_array() {
                    arr.iter()
                        .filter_map(|v| v.as_str())
                        .filter_map(|s| Uuid::parse_str(s).ok())
                        .collect()
                } else {
                    Vec::new()
                }
            } else {
                Vec::new()
            };
            
            let connections_json: Option<serde_json::Value> = row.get("connections");
            let connections = if let Some(json) = connections_json {
                if let Some(arr) = json.as_array() {
                    arr.iter()
                        .filter_map(|v| {
                            let to_id = v.get("to_id")?.as_str()?;
                            let connection_type = v.get("connection_type")?.as_str()?;
                            let metadata = v.get("metadata")
                                .and_then(|m| m.as_object())
                                .map(|m| {
                                    m.iter()
                                        .map(|(k, v)| (k.clone(), v.clone()))
                                        .collect()
                                })
                                .unwrap_or_default();
                            
                            Some(Connection {
                                to_id: Uuid::parse_str(to_id).ok()?,
                                connection_type: connection_type.to_string(),
                                metadata,
                            })
                        })
                        .collect()
                } else {
                    Vec::new()
                }
            } else {
                Vec::new()
            };
            
            let properties_json: Option<serde_json::Value> = row.get("properties");
            let properties = if let Some(json) = properties_json {
                if let Some(obj) = json.as_object() {
                    obj.iter()
                        .map(|(k, v)| (k.clone(), v.clone()))
                        .collect()
                } else {
                    HashMap::new()
                }
            } else {
                HashMap::new()
            };
            
            let obj = BuildingObject {
                id: row.get("id"),
                path: row.get("path"),
                object_type: row.get("object_type"),
                location,
                parent_id: row.get("parent_id"),
                children,
                connections,
                properties,
                state,
                created_at: row.get("created_at"),
                updated_at: row.get("updated_at"),
            };
            
            object_map.insert(obj.id, obj);
        }
        
        Ok(Building {
            id: building_id.to_string(),
            name: building_name,
            objects: object_map,
        })
    }
    
    // API support methods
    pub async fn raw_query(&self, sql: &str) -> Result<Vec<serde_json::Value>> {
        let rows = sqlx::query(sql)
            .fetch_all(&self.pool)
            .await?;
        
        let mut results = Vec::new();
        for row in rows {
            let mut obj = serde_json::Map::new();
            for (i, column) in row.columns().iter().enumerate() {
                let key = column.name().to_string();
                let value: serde_json::Value = if let Ok(v) = row.try_get::<String, _>(i) {
                    serde_json::Value::String(v)
                } else if let Ok(v) = row.try_get::<i32, _>(i) {
                    serde_json::Value::Number(v.into())
                } else if let Ok(v) = row.try_get::<bool, _>(i) {
                    serde_json::Value::Bool(v)
                } else {
                    serde_json::Value::Null
                };
                obj.insert(key, value);
            }
            results.push(serde_json::Value::Object(obj));
        }
        
        Ok(results)
    }
    
    pub async fn get_object(&self, id: Uuid) -> Result<Option<serde_json::Value>> {
        let row = sqlx::query(
            "SELECT id, path, name, object_type, location_x, location_y, location_z, 
             status, health, needs_repair, properties, metrics 
             FROM building_objects WHERE id = $1"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;
        
        if let Some(row) = row {
            let obj = serde_json::json!({
                "id": row.get::<Uuid, _>("id").to_string(),
                "path": row.get::<String, _>("path"),
                "name": row.get::<String, _>("name"),
                "object_type": row.get::<String, _>("object_type"),
                "location": {
                    "x": row.get::<Option<f64>, _>("location_x"),
                    "y": row.get::<Option<f64>, _>("location_y"),
                    "z": row.get::<Option<f64>, _>("location_z"),
                },
                "status": row.get::<String, _>("status"),
                "health": row.get::<i32, _>("health"),
                "needs_repair": row.get::<bool, _>("needs_repair"),
                "properties": row.get::<serde_json::Value, _>("properties"),
                "metrics": row.get::<serde_json::Value, _>("metrics"),
            });
            Ok(Some(obj))
        } else {
            Ok(None)
        }
    }
    
    pub async fn create_object(
        &self,
        id: Uuid,
        path: String,
        object_type: String,
        location_x: f32,
        location_y: f32,
        location_z: f32,
        properties: serde_json::Value,
        status: String,
    ) -> Result<serde_json::Value> {
        let name = path.split('/').last().unwrap_or("unknown").to_string();
        
        sqlx::query(
            "INSERT INTO building_objects 
             (id, building_id, path, name, object_type, location_x, location_y, location_z, properties, status)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)"
        )
        .bind(id)
        .bind(Uuid::parse_str("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")?) // Default building for now
        .bind(&path)
        .bind(&name)
        .bind(&object_type)
        .bind(location_x as f64)
        .bind(location_y as f64)
        .bind(location_z as f64)
        .bind(&properties)
        .bind(&status)
        .execute(&self.pool)
        .await?;
        
        Ok(serde_json::json!({
            "id": id,
            "path": path,
        }))
    }
    
    pub async fn update_object(
        &self,
        id: Uuid,
        updates: crate::api::handlers::UpdateObjectRequest,
    ) -> Result<serde_json::Value> {
        let mut query = String::from("UPDATE building_objects SET updated_at = CURRENT_TIMESTAMP");
        
        if let Some(path) = &updates.path {
            query.push_str(&format!(", path = '{}'", path));
            query.push_str(&format!(", name = '{}'", path.split('/').last().unwrap_or("unknown")));
        }
        if let Some(status) = &updates.status {
            query.push_str(&format!(", status = '{}'", status));
        }
        if let Some(needs_repair) = updates.needs_repair {
            query.push_str(&format!(", needs_repair = {}", needs_repair));
        }
        if let Some(health) = updates.health {
            query.push_str(&format!(", health = {}", health));
        }
        
        query.push_str(&format!(" WHERE id = '{}'", id));
        
        sqlx::query(&query)
            .execute(&self.pool)
            .await?;
        
        Ok(serde_json::json!({
            "id": id,
        }))
    }
    
    pub async fn delete_object(&self, id: Uuid) -> Result<()> {
        sqlx::query("DELETE FROM building_objects WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await?;
        
        Ok(())
    }
}

#[derive(Debug)]
pub struct BuildingInfo {
    pub id: String,
    pub name: String,
}