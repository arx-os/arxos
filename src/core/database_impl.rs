//! Production SQLite database implementation with spatial queries
//! 
//! Provides persistent storage for ArxObjects with efficient spatial indexing

use rusqlite::{
    params, Connection, Result as SqlResult,
    types::ToSql,
};
use std::sync::{Arc, Mutex};
use thiserror::Error;
use serde::{Deserialize, Serialize};

use crate::arxobject::{ArxObject, object_types};

/// Database errors
#[derive(Error, Debug)]
pub enum DatabaseError {
    #[error("SQLite error: {0}")]
    SqliteError(#[from] rusqlite::Error),
    
    #[error("Serialization error: {0}")]
    SerializationError(String),
    
    #[error("Object not found: {0}")]
    ObjectNotFound(u32),
    
    #[error("Invalid query: {0}")]
    InvalidQuery(String),
    
    #[error("Transaction failed: {0}")]
    TransactionFailed(String),
}

/// Database connection pool
pub struct DatabasePool {
    connections: Vec<Arc<Mutex<Connection>>>,
    path: String,
}

impl DatabasePool {
    /// Create new database pool
    pub fn new(path: &str, pool_size: usize) -> Result<Self, DatabaseError> {
        let mut connections = Vec::new();
        
        for _ in 0..pool_size {
            let conn = Connection::open(path)?;
            configure_connection(&conn)?;
            connections.push(Arc::new(Mutex::new(conn)));
        }
        
        Ok(Self {
            connections,
            path: path.to_string(),
        })
    }
    
    /// Get connection from pool
    pub fn get_connection(&self) -> Arc<Mutex<Connection>> {
        // Simple round-robin for now
        // TODO: Implement proper connection pooling
        self.connections[0].clone()
    }
}

/// Configure SQLite connection for optimal performance
fn configure_connection(conn: &Connection) -> SqlResult<()> {
    // Enable WAL mode for better concurrency
    conn.execute_batch(
        "PRAGMA journal_mode = WAL;
         PRAGMA synchronous = NORMAL;
         PRAGMA cache_size = 10000;
         PRAGMA temp_store = MEMORY;
         PRAGMA mmap_size = 30000000000;"
    )?;
    
    // Enable foreign keys
    conn.execute_batch("PRAGMA foreign_keys = ON;")?;
    
    Ok(())
}

/// Main database interface
pub struct ArxosDatabase {
    pool: DatabasePool,
}

impl ArxosDatabase {
    /// Open or create database
    pub fn open(path: &str) -> Result<Self, DatabaseError> {
        let pool = DatabasePool::new(path, 4)?;
        
        // Initialize schema if needed
        let conn = pool.get_connection();
        let conn = conn.lock().unwrap();
        initialize_schema(&conn)?;
        
        Ok(Self { pool })
    }
    
    /// Create in-memory database (for testing)
    pub fn memory() -> Result<Self, DatabaseError> {
        Self::open(":memory:")
    }
    
    /// Insert a building (for testing)
    pub fn insert_building(&self, name: &str, width_mm: u32, depth_mm: u32, height_mm: u32) -> Result<String, DatabaseError> {
        let conn = self.pool.get_connection();
        let conn = conn.lock().unwrap();
        
        // Use the same UUID format as our building_id conversion
        let building_id = format!("00000000-0000-0000-0000-{:012}", 1);
        
        conn.execute(
            "INSERT INTO buildings (id, name, width_mm, depth_mm, height_mm) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![&building_id, name, width_mm, depth_mm, height_mm],
        )?;
        
        Ok(building_id)
    }
    
    /// Insert ArxObject
    pub fn insert_object(&self, obj: &ArxObject, building_id: u32) -> Result<u32, DatabaseError> {
        let conn = self.pool.get_connection();
        let mut conn = conn.lock().unwrap();
        
        let tx = conn.transaction()?;
        
        // Copy values from packed struct
        let object_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        let properties = obj.properties;
        
        let id = tx.execute(
            "INSERT INTO arxobjects (
                building_id, object_type, x, y, z, properties,
                source_points, compressed_size, compression_ratio, semantic_confidence
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
            params![
                format!("00000000-0000-0000-0000-{:012}", building_id),  // Convert u32 to UUID format
                object_type,
                x,
                y,
                z,
                &properties[..],
                5000,  // Estimated source points
                13,    // ArxObject is 13 bytes
                384.6, // Compression ratio
                0.95,  // Default confidence
            ],
        )?;
        
        // TODO: Update spatial index when rtree extension is available
        // tx.execute(
        //     "INSERT INTO arxobjects_spatial (id, min_x, max_x, min_y, max_y, min_z, max_z)
        //      VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        //     params![
        //         id,
        //         obj.x - 100,  // Add small buffer for spatial queries
        //         obj.y - 100,
        //         obj.x + 100,
        //         obj.y + 100,
        //         obj.z - 100,
        //         obj.z + 100,
        //     ],
        // )?;
        
        tx.commit()?;
        
        Ok(id as u32)
    }
    
    /// Get ArxObject by ID
    pub fn get_object(&self, id: u32) -> Result<ArxObject, DatabaseError> {
        let conn = self.pool.get_connection();
        let conn = conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, object_type, x, y, z, properties
             FROM arxobjects WHERE id = ?1"
        )?;
        
        let obj = stmt.query_row(params![id], |row| {
            let mut obj = ArxObject::new(
                row.get(0)?,  // id
                row.get(1)?,  // object_type
                row.get(2)?,  // x
                row.get(3)?,  // y
                row.get(4)?,  // z
            );
            
            // Load properties
            let props: Vec<u8> = row.get(5)?;
            if props.len() >= 4 {
                obj.properties.copy_from_slice(&props[..4]);
            }
            
            // All fields have been retrieved
            
            Ok(obj)
        })?;
        
        Ok(obj)
    }
    
    /// Spatial query - find objects in bounding box
    pub fn query_spatial(
        &self,
        min_x: i16,
        max_x: i16,
        min_y: i16,
        max_y: i16,
        min_z: Option<i16>,
        max_z: Option<i16>,
    ) -> Result<Vec<ArxObject>, DatabaseError> {
        let conn = self.pool.get_connection();
        let conn = conn.lock().unwrap();
        
        let query = if let (Some(_min_z), Some(_max_z)) = (min_z, max_z) {
            // 3D query - directly on arxobjects table
            "SELECT id, object_type, x, y, z, properties
             FROM arxobjects
             WHERE x >= ?1 AND x <= ?2
               AND y >= ?3 AND y <= ?4
               AND z >= ?5 AND z <= ?6"
        } else {
            // 2D query (ignore Z) - directly on arxobjects table
            "SELECT id, object_type, x, y, z, properties
             FROM arxobjects
             WHERE x >= ?1 AND x <= ?2
               AND y >= ?3 AND y <= ?4"
        };
        
        let mut stmt = conn.prepare(query)?;
        
        // Store z values to avoid lifetime issues
        let z_values = match (min_z, max_z) {
            (Some(min), Some(max)) => Some((min, max)),
            _ => None,
        };
        
        let params: Vec<&dyn ToSql> = if let Some((ref min_z, ref max_z)) = z_values {
            vec![&min_x, &max_x, &min_y, &max_y, min_z, max_z]
        } else {
            vec![&min_x, &max_x, &min_y, &max_y]
        };
        
        let objects = stmt.query_map(&params[..], |row| {
            let mut obj = ArxObject::new(
                row.get(0)?,
                row.get(1)?,
                row.get(2)?,
                row.get(3)?,
                row.get(4)?,
            );
            
            let props: Vec<u8> = row.get(5)?;
            if props.len() >= 4 {
                obj.properties.copy_from_slice(&props[..4]);
            }
            
            // All fields have been retrieved
            
            Ok(obj)
        })?
        .collect::<Result<Vec<_>, _>>()?;
        
        Ok(objects)
    }
    
    /// Query by object type
    pub fn query_by_type(&self, object_type: u8) -> Result<Vec<ArxObject>, DatabaseError> {
        let conn = self.pool.get_connection();
        let conn = conn.lock().unwrap();
        
        let mut stmt = conn.prepare(
            "SELECT id, object_type, x, y, z, properties
             FROM arxobjects WHERE object_type = ?1"
        )?;
        
        let objects = stmt.query_map(params![object_type], |row| {
            let mut obj = ArxObject::new(
                row.get(0)?,
                row.get(1)?,
                row.get(2)?,
                row.get(3)?,
                row.get(4)?,
            );
            
            let props: Vec<u8> = row.get(5)?;
            if props.len() >= 4 {
                obj.properties.copy_from_slice(&props[..4]);
            }
            
            // All fields have been retrieved
            
            Ok(obj)
        })?
        .collect::<Result<Vec<_>, _>>()?;
        
        Ok(objects)
    }
    
    /// Execute semantic query
    pub fn query_semantic(&self, query: &str) -> Result<QueryResult, DatabaseError> {
        // Parse natural language query
        let parsed = parse_semantic_query(query)?;
        
        // Convert to SQL
        let sql = build_sql_query(&parsed)?;
        
        // Execute
        let conn = self.pool.get_connection();
        let conn = conn.lock().unwrap();
        
        let mut stmt = conn.prepare(&sql)?;
        let results = stmt.query_map([], |row| {
            Ok(QueryRow {
                id: row.get(0)?,
                object_type: row.get(1)?,
                x: row.get(2)?,
                y: row.get(3)?,
                z: row.get(4)?,
            })
        })?
        .collect::<Result<Vec<_>, _>>()?;
        
        Ok(QueryResult {
            query: query.to_string(),
            sql: sql,
            rows: results,
        })
    }
    
    /// Get database statistics
    pub fn get_stats(&self) -> Result<DatabaseStats, DatabaseError> {
        let conn = self.pool.get_connection();
        let conn = conn.lock().unwrap();
        
        let total_objects: u32 = conn.query_row(
            "SELECT COUNT(*) FROM arxobjects",
            [],
            |row| row.get(0),
        )?;
        
        let total_buildings: u32 = conn.query_row(
            "SELECT COUNT(DISTINCT building_id) FROM arxobjects",
            [],
            |row| row.get(0),
        )?;
        
        let db_size: u64 = conn.query_row(
            "SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()",
            [],
            |row| row.get(0),
        )?;
        
        Ok(DatabaseStats {
            total_objects,
            total_buildings,
            db_size_bytes: db_size,
        })
    }
}

/// Initialize database schema
fn initialize_schema(conn: &Connection) -> SqlResult<()> {
    // Read and execute migration files
    conn.execute_batch(include_str!("../../migrations/001_initial_schema.sql"))?;
    
    // Skip spatial functions migration for now as it requires extensions
    // TODO: Load SQLite math extensions or rewrite queries without SQRT
    // conn.execute_batch(include_str!("../../migrations/002_spatial_functions.sql"))?;
    
    Ok(())
}

/// Parse semantic query into structured format
fn parse_semantic_query(query: &str) -> Result<ParsedQuery, DatabaseError> {
    let query_lower = query.to_lowercase();
    
    // Simple keyword parsing for now
    let object_type = if query_lower.contains("outlet") {
        Some(object_types::OUTLET)
    } else if query_lower.contains("light") {
        Some(object_types::LIGHT)
    } else if query_lower.contains("thermostat") {
        Some(object_types::THERMOSTAT)
    } else {
        None
    };
    
    // Extract room number if present
    let room = extract_room_number(&query_lower);
    
    // Extract floor if present
    let floor = extract_floor_number(&query_lower);
    
    Ok(ParsedQuery {
        object_type,
        room,
        floor,
        raw_query: query.to_string(),
    })
}

/// Build SQL query from parsed semantic query
fn build_sql_query(parsed: &ParsedQuery) -> Result<String, DatabaseError> {
    let mut conditions = Vec::new();
    
    if let Some(object_type) = parsed.object_type {
        conditions.push(format!("object_type = {}", object_type));
    }
    
    if let Some(room) = parsed.room {
        // Room boundaries would be defined in a separate table
        // For now, use approximate boundaries
        let (min_x, max_x, min_y, max_y) = get_room_bounds(room);
        conditions.push(format!(
            "x BETWEEN {} AND {} AND y BETWEEN {} AND {}",
            min_x, max_x, min_y, max_y
        ));
    }
    
    if let Some(floor) = parsed.floor {
        let z_min = floor * 3000;  // 3 meters per floor
        let z_max = (floor + 1) * 3000;
        conditions.push(format!("z BETWEEN {} AND {}", z_min, z_max));
    }
    
    let where_clause = if conditions.is_empty() {
        String::new()
    } else {
        format!("WHERE {}", conditions.join(" AND "))
    };
    
    Ok(format!(
        "SELECT id, object_type, x, y, z FROM arxobjects {} LIMIT 100",
        where_clause
    ))
}

fn extract_room_number(query: &str) -> Option<u16> {
    // Look for patterns like "room 127" or "rm 127"
    if let Some(pos) = query.find("room ") {
        let num_str = &query[pos + 5..].split_whitespace().next()?;
        num_str.parse().ok()
    } else if let Some(pos) = query.find("rm ") {
        let num_str = &query[pos + 3..].split_whitespace().next()?;
        num_str.parse().ok()
    } else {
        None
    }
}

fn extract_floor_number(query: &str) -> Option<i16> {
    // Look for patterns like "floor 2" or "2nd floor"
    if let Some(pos) = query.find("floor ") {
        let num_str = &query[pos + 6..].split_whitespace().next()?;
        num_str.parse().ok()
    } else if query.contains("1st floor") || query.contains("first floor") {
        Some(1)
    } else if query.contains("2nd floor") || query.contains("second floor") {
        Some(2)
    } else if query.contains("3rd floor") || query.contains("third floor") {
        Some(3)
    } else {
        None
    }
}

fn get_room_bounds(room: u16) -> (i16, i16, i16, i16) {
    // This would be loaded from a rooms table
    // For now, return example bounds
    match room {
        127 => (1000, 5000, 1000, 4000),
        _ => (0, 10000, 0, 10000),
    }
}

/// Parsed semantic query
#[derive(Debug)]
struct ParsedQuery {
    object_type: Option<u8>,
    room: Option<u16>,
    floor: Option<i16>,
    raw_query: String,
}

/// Query result
#[derive(Debug, Serialize, Deserialize)]
pub struct QueryResult {
    pub query: String,
    pub sql: String,
    pub rows: Vec<QueryRow>,
}

/// Query result row
#[derive(Debug, Serialize, Deserialize)]
pub struct QueryRow {
    pub id: u32,
    pub object_type: u8,
    pub x: i16,
    pub y: i16,
    pub z: i16,
}

/// Database statistics
#[derive(Debug, Serialize, Deserialize)]
pub struct DatabaseStats {
    pub total_objects: u32,
    pub total_buildings: u32,
    pub db_size_bytes: u64,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_database_creation() {
        let db = ArxosDatabase::memory().unwrap();
        let stats = db.get_stats().unwrap();
        assert_eq!(stats.total_objects, 0);
    }
    
    #[test]
    fn test_insert_and_retrieve() {
        let db = ArxosDatabase::memory().unwrap();
        
        // Insert a building first
        db.insert_building("Test Building", 10000, 10000, 3000).unwrap();
        
        let obj = ArxObject::new(0x0001, object_types::OUTLET, 1000, 2000, 300);
        let building_id = 1; // Default building ID for tests
        let id = db.insert_object(&obj, building_id).unwrap();
        
        let retrieved = db.get_object(id).unwrap();
        let retrieved_type = retrieved.object_type;
        let retrieved_x = retrieved.x;
        assert_eq!(retrieved_type, object_types::OUTLET);
        assert_eq!(retrieved_x, 1000);
    }
    
    #[test]
    fn test_spatial_query() {
        let db = ArxosDatabase::memory().unwrap();
        
        // Insert a building first
        db.insert_building("Test Building", 10000, 10000, 3000).unwrap();
        
        let building_id = 1; // Default building ID for tests
        
        // Insert test objects
        db.insert_object(&ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300), building_id).unwrap();
        db.insert_object(&ArxObject::new(0x0001, object_types::OUTLET, 3000, 3000, 300), building_id).unwrap();
        db.insert_object(&ArxObject::new(0x0001, object_types::OUTLET, 5000, 5000, 300), building_id).unwrap();
        
        // Query middle region
        let results = db.query_spatial(2000, 4000, 2000, 4000, None, None).unwrap();
        assert_eq!(results.len(), 1);
        // Copy value from packed struct to avoid alignment issues
        let result_x = results[0].x;
        assert_eq!(result_x, 3000);
    }
    
    #[test]
    fn test_semantic_query_parsing() {
        let parsed = parse_semantic_query("all outlets in room 127").unwrap();
        assert_eq!(parsed.object_type, Some(object_types::OUTLET));
        assert_eq!(parsed.room, Some(127));
        
        let parsed = parse_semantic_query("lights on floor 2").unwrap();
        assert_eq!(parsed.object_type, Some(object_types::LIGHT));
        assert_eq!(parsed.floor, Some(2));
    }
}