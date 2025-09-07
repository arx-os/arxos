//! Core data models for ArxOS

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::HashMap;

/// A building object - the core unit of the system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingObject {
    pub id: Uuid,
    pub path: String,  // e.g., "/electrical/circuits/2/loads/outlet_2B"
    pub object_type: String,
    pub location: Location,
    pub parent_id: Option<Uuid>,
    pub children: Vec<Uuid>,
    pub connections: Vec<Connection>,
    pub properties: HashMap<String, serde_json::Value>,
    pub state: ObjectState,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl BuildingObject {
    pub fn name(&self) -> &str {
        self.path.split('/').last().unwrap_or("unknown")
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Location {
    pub space: String,  // e.g., "/spaces/floor_2/room_2B"
    pub x: f32,  // meters
    pub y: f32,
    pub z: f32,
    pub mounting: String,  // "wall", "ceiling", "floor"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Connection {
    pub to_id: Uuid,
    pub connection_type: String,  // "power", "data", "plumbing"
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectState {
    pub status: String,  // "normal", "degraded", "failed"
    pub health: String,  // "good", "fair", "poor"
    pub needs_repair: bool,
    pub metrics: HashMap<String, f64>,
}

/// A building containing many objects
#[derive(Debug, Clone)]
pub struct Building {
    pub id: String,
    pub name: String,
    pub objects: HashMap<Uuid, BuildingObject>,
}

impl Building {
    pub fn get_object(&self, id: &Uuid) -> Option<&BuildingObject> {
        self.objects.get(id)
    }
    
    pub fn find_by_path(&self, path: &str) -> Option<&BuildingObject> {
        self.objects.values().find(|o| o.path == path)
    }
    
    pub fn list_at_path(&self, path: &str) -> Vec<&BuildingObject> {
        let prefix = if path == "/" {
            "/".to_string()
        } else {
            format!("{}/", path)
        };
        
        self.objects.values()
            .filter(|o| o.path.starts_with(&prefix) && o.path != path)
            .collect()
    }
}