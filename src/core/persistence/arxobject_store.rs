//! Lightweight ArxObject Storage
//! 
//! Simple SQLite storage for 13-byte ArxObjects.
//! No heavy processing - just store and retrieve.

use crate::arxobject::ArxObject;
use super::connection_pool::{ConnectionPool, PooledConnection};
use rusqlite::{params, Row};
use std::error::Error;

pub type ArxObjectId = u16;

/// Simple store for ArxObject persistence
pub struct ArxObjectStore {
    pool: ConnectionPool,
}

impl ArxObjectStore {
    /// Create a new ArxObject store
    pub fn new(pool: ConnectionPool) -> Self {
        Self { pool }
    }
    
    /// Store a single ArxObject
    pub fn store(&self, obj: &ArxObject) -> Result<ArxObjectId, Box<dyn Error>> {
        let conn = self.pool.get()?;
        
        // Copy fields from packed struct to avoid alignment issues
        let building_id = obj.building_id;
        let object_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        let properties = obj.properties;
        
        // Simple insert - ArxOS just stores, doesn't process
        conn.execute(
            "INSERT OR REPLACE INTO arxobjects 
             (building_id, object_type, x, y, z, properties) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                building_id,
                object_type,
                x,
                y,
                z,
                &properties[..],
            ],
        )?;
        
        Ok(conn.last_insert_rowid() as ArxObjectId)
    }
    
    /// Retrieve an ArxObject by ID
    pub fn get(&self, id: ArxObjectId) -> Result<Option<ArxObject>, Box<dyn Error>> {
        let conn = self.pool.get()?;
        
        let result = conn.query_row(
            "SELECT building_id, object_type, x, y, z, properties 
             FROM arxobjects WHERE id = ?1",
            params![id],
            |row| {
                let props_vec: Vec<u8> = row.get(5)?;
                let mut properties = [0u8; 4];
                properties.copy_from_slice(&props_vec[..4.min(props_vec.len())]);
                
                Ok(ArxObject {
                    building_id: row.get(0)?,
                    object_type: row.get(1)?,
                    x: row.get(2)?,
                    y: row.get(3)?,
                    z: row.get(4)?,
                    properties,
                })
            },
        );
        
        match result {
            Ok(obj) => Ok(Some(obj)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(Box::new(e)),
        }
    }
    
    /// Query ArxObjects by building
    pub fn query_by_building(&self, building_id: u16) -> Result<Vec<ArxObject>, Box<dyn Error>> {
        let conn = self.pool.get()?;
        
        let mut stmt = conn.prepare(
            "SELECT building_id, object_type, x, y, z, properties 
             FROM arxobjects WHERE building_id = ?1"
        )?;
        
        let objects = stmt.query_map(params![building_id], |row| {
            let props_vec: Vec<u8> = row.get(5)?;
            let mut properties = [0u8; 4];
            properties.copy_from_slice(&props_vec[..4.min(props_vec.len())]);
            
            Ok(ArxObject {
                building_id: row.get(0)?,
                object_type: row.get(1)?,
                x: row.get(2)?,
                y: row.get(3)?,
                z: row.get(4)?,
                properties,
            })
        })?
        .collect::<Result<Vec<_>, _>>()?;
        
        Ok(objects)
    }
    
    /// Delete old ArxObjects (cleanup)
    pub fn cleanup_old(&self, before_timestamp: i64) -> Result<usize, Box<dyn Error>> {
        let conn = self.pool.get()?;
        
        let deleted = conn.execute(
            "DELETE FROM arxobjects WHERE created_at < ?1",
            params![before_timestamp],
        )?;
        
        Ok(deleted)
    }
}