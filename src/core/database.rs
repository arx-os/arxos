//! Database abstraction layer for ArxOS
//! Supports both SQLite (embedded) and PostgreSQL (server deployment)

use rusqlite::{Connection, Result as SqliteResult, params};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::path::Path;

/// Database connection wrapper
pub struct ArxDatabase {
    conn: Connection,
}

/// Type alias for compatibility with other modules
pub type Database = ArxDatabase;

impl ArxDatabase {
    /// Create a new database connection
    pub fn new(path: &Path) -> SqliteResult<Self> {
        let conn = Connection::open(path)?;
        
        // Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON", [])?;
        
        // Optimize for performance
        conn.execute("PRAGMA journal_mode = WAL", [])?;
        conn.execute("PRAGMA synchronous = NORMAL", [])?;
        
        Ok(Self { conn })
    }
    
    /// Initialize database with schema
    pub fn init_schema(&self) -> SqliteResult<()> {
        // Read and execute migration files
        let schema_001 = include_str!("../../migrations/001_initial_schema.sql");
        let schema_002 = include_str!("../../migrations/002_spatial_functions.sql");
        
        self.conn.execute_batch(schema_001)?;
        self.conn.execute_batch(schema_002)?;
        
        Ok(())
    }
    
    /// Insert a new building
    pub fn insert_building(&self, building: &Building) -> SqliteResult<Uuid> {
        let id = Uuid::new_v4();
        
        self.conn.execute(
            "INSERT INTO buildings (id, name, address, origin_lat, origin_lon, origin_elevation, 
             width_mm, depth_mm, height_mm) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                id.to_string(),
                building.name,
                building.address,
                building.origin_lat,
                building.origin_lon,
                building.origin_elevation,
                building.width_mm,
                building.depth_mm,
                building.height_mm,
            ],
        )?;
        
        Ok(id)
    }
    
    /// Insert an ArxObject
    pub fn insert_arxobject(&self, obj: &ArxObjectDB) -> SqliteResult<()> {
        self.conn.execute(
            "INSERT INTO arxobjects (id, object_type, x, y, z, properties, building_id, 
             floor_number, room_id, source_points, compressed_size, compression_ratio, 
             semantic_confidence, created_by) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)",
            params![
                obj.id,
                obj.object_type,
                obj.x,
                obj.y,
                obj.z,
                obj.properties,
                obj.building_id.to_string(),
                obj.floor_number,
                obj.room_id.map(|id| id.to_string()),
                obj.source_points,
                obj.compressed_size,
                obj.compression_ratio,
                obj.semantic_confidence,
                obj.created_by,
            ],
        )?;
        
        Ok(())
    }
    
    /// Query objects within a bounding box
    pub fn query_bbox(&self, 
        building_id: Uuid,
        min_x: u16, min_y: u16, min_z: u16,
        max_x: u16, max_y: u16, max_z: u16
    ) -> SqliteResult<Vec<ArxObjectDB>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, object_type, x, y, z, properties, building_id, floor_number, room_id,
             source_points, compressed_size, compression_ratio, semantic_confidence,
             validation_status, validation_confidence, created_by, created_at
             FROM arxobjects 
             WHERE building_id = ?1 
             AND x >= ?2 AND x <= ?3 
             AND y >= ?4 AND y <= ?5 
             AND z >= ?6 AND z <= ?7"
        )?;
        
        let objects = stmt.query_map(
            params![
                building_id.to_string(),
                min_x, max_x,
                min_y, max_y,
                min_z, max_z
            ],
            |row| {
                Ok(ArxObjectDB {
                    id: row.get(0)?,
                    object_type: row.get(1)?,
                    x: row.get(2)?,
                    y: row.get(3)?,
                    z: row.get(4)?,
                    properties: row.get(5)?,
                    building_id: Uuid::parse_str(&row.get::<_, String>(6)?).unwrap(),
                    floor_number: row.get(7)?,
                    room_id: row.get::<_, Option<String>>(8)?
                        .and_then(|s| Uuid::parse_str(&s).ok()),
                    source_points: row.get(9)?,
                    compressed_size: row.get(10)?,
                    compression_ratio: row.get(11)?,
                    semantic_confidence: row.get(12)?,
                    validation_status: row.get(13)?,
                    validation_confidence: row.get(14)?,
                    created_by: row.get(15)?,
                    created_at: row.get(16)?,
                })
            }
        )?;
        
        objects.collect()
    }
    
    /// Find objects by type
    pub fn find_by_type(&self, building_id: Uuid, object_type: u8) -> SqliteResult<Vec<ArxObjectDB>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, object_type, x, y, z, properties, building_id, floor_number, room_id,
             source_points, compressed_size, compression_ratio, semantic_confidence,
             validation_status, validation_confidence, created_by, created_at
             FROM arxobjects 
             WHERE building_id = ?1 AND object_type = ?2"
        )?;
        
        let objects = stmt.query_map(
            params![building_id.to_string(), object_type],
            |row| {
                Ok(ArxObjectDB {
                    id: row.get(0)?,
                    object_type: row.get(1)?,
                    x: row.get(2)?,
                    y: row.get(3)?,
                    z: row.get(4)?,
                    properties: row.get(5)?,
                    building_id: Uuid::parse_str(&row.get::<_, String>(6)?).unwrap(),
                    floor_number: row.get(7)?,
                    room_id: row.get::<_, Option<String>>(8)?
                        .and_then(|s| Uuid::parse_str(&s).ok()),
                    source_points: row.get(9)?,
                    compressed_size: row.get(10)?,
                    compression_ratio: row.get(11)?,
                    semantic_confidence: row.get(12)?,
                    validation_status: row.get(13)?,
                    validation_confidence: row.get(14)?,
                    created_by: row.get(15)?,
                    created_at: row.get(16)?,
                })
            }
        )?;
        
        objects.collect()
    }
    
    /// Add detail chunk for progressive enhancement
    pub fn add_detail_chunk(&self, 
        arxobject_id: u16,
        chunk_type: u8,
        chunk_id: u16,
        chunk_data: &[u8; 8]
    ) -> SqliteResult<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO detail_chunks (arxobject_id, chunk_type, chunk_id, chunk_data)
             VALUES (?1, ?2, ?3, ?4)",
            params![arxobject_id, chunk_type, chunk_id, chunk_data.as_ref()],
        )?;
        
        Ok(())
    }
    
    /// Record BILT transaction
    pub fn record_bilt_transaction(&self, transaction: &BiltTransaction) -> SqliteResult<()> {
        self.conn.execute(
            "INSERT INTO bilt_transactions (user_id, action_type, arxobject_id, points_earned,
             first_mapper_bonus, professional_bonus, photo_bonus, verification_bonus, description)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                transaction.user_id,
                transaction.action_type,
                transaction.arxobject_id,
                transaction.points_earned,
                transaction.first_mapper_bonus,
                transaction.professional_bonus,
                transaction.photo_bonus,
                transaction.verification_bonus,
                transaction.description,
            ],
        )?;
        
        Ok(())
    }
    
    /// Get user's BILT balance
    pub fn get_bilt_balance(&self, user_id: &str) -> SqliteResult<BiltBalance> {
        self.conn.query_row(
            "SELECT total_earned, total_redeemed, current_balance, last_updated
             FROM bilt_balances WHERE user_id = ?1",
            params![user_id],
            |row| {
                Ok(BiltBalance {
                    user_id: user_id.to_string(),
                    total_earned: row.get(0)?,
                    total_redeemed: row.get(1)?,
                    current_balance: row.get(2)?,
                    last_updated: row.get(3)?,
                })
            }
        )
    }
    
    /// Update object validation status
    pub fn update_validation(&self, 
        object_id: u16,
        status: &str,
        confidence: f32,
        source: &str,
        validated_by: &str
    ) -> SqliteResult<()> {
        self.conn.execute(
            "UPDATE arxobjects 
             SET validation_status = ?2, 
                 validation_confidence = ?3,
                 validation_source = ?4,
                 validated_by = ?5,
                 last_verified = CURRENT_TIMESTAMP
             WHERE id = ?1",
            params![object_id, status, confidence, source, validated_by],
        )?;
        
        Ok(())
    }
    
    /// Get building completion statistics
    pub fn get_building_stats(&self, building_id: Uuid) -> SqliteResult<BuildingStats> {
        self.conn.query_row(
            "SELECT name, validation_status, total_rooms, mapped_rooms, total_objects,
             verified_objects, room_coverage_percentage, object_verification_percentage
             FROM building_completion WHERE id = ?1",
            params![building_id.to_string()],
            |row| {
                Ok(BuildingStats {
                    building_id,
                    name: row.get(0)?,
                    validation_status: row.get(1)?,
                    total_rooms: row.get(2)?,
                    mapped_rooms: row.get(3)?,
                    total_objects: row.get(4)?,
                    verified_objects: row.get(5)?,
                    room_coverage_percentage: row.get(6)?,
                    object_verification_percentage: row.get(7)?,
                })
            }
        )
    }
}

// Data structures

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Building {
    pub name: String,
    pub address: Option<String>,
    pub origin_lat: Option<f64>,
    pub origin_lon: Option<f64>,
    pub origin_elevation: f64,
    pub width_mm: u32,
    pub depth_mm: u32,
    pub height_mm: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArxObjectDB {
    pub id: u16,
    pub object_type: u8,
    pub x: u16,
    pub y: u16,
    pub z: u16,
    pub properties: Vec<u8>,
    pub building_id: Uuid,
    pub floor_number: Option<i32>,
    pub room_id: Option<Uuid>,
    pub source_points: Option<u32>,
    pub compressed_size: Option<u32>,
    pub compression_ratio: Option<f32>,
    pub semantic_confidence: f32,
    pub validation_status: Option<String>,
    pub validation_confidence: Option<f32>,
    pub created_by: Option<String>,
    pub created_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiltTransaction {
    pub user_id: String,
    pub action_type: String,
    pub arxobject_id: Option<u16>,
    pub points_earned: i32,
    pub first_mapper_bonus: f32,
    pub professional_bonus: f32,
    pub photo_bonus: f32,
    pub verification_bonus: f32,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiltBalance {
    pub user_id: String,
    pub total_earned: i32,
    pub total_redeemed: i32,
    pub current_balance: i32,
    pub last_updated: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingStats {
    pub building_id: Uuid,
    pub name: String,
    pub validation_status: String,
    pub total_rooms: i32,
    pub mapped_rooms: i32,
    pub total_objects: i32,
    pub verified_objects: i32,
    pub room_coverage_percentage: f32,
    pub object_verification_percentage: f32,
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    
    #[test]
    fn test_database_creation() {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        
        let db = ArxDatabase::new(&db_path).unwrap();
        db.init_schema().unwrap();
        
        // Test building insertion
        let building = Building {
            name: "Test Building".to_string(),
            address: Some("123 Test St".to_string()),
            origin_lat: Some(27.9506),
            origin_lon: Some(-82.4572),
            origin_elevation: 0.0,
            width_mm: 50000,
            depth_mm: 40000,
            height_mm: 12000,
        };
        
        let building_id = db.insert_building(&building).unwrap();
        assert!(!building_id.is_nil());
        
        // Test ArxObject insertion
        let obj = ArxObjectDB {
            id: 0x0001,
            object_type: 0x10, // Outlet
            x: 1500,
            y: 2000,
            z: 300,
            properties: vec![0, 0, 0, 0],
            building_id,
            floor_number: Some(1),
            room_id: None,
            source_points: Some(5000),
            compressed_size: Some(13),
            compression_ratio: Some(384.6),
            semantic_confidence: 0.95,
            validation_status: None,
            validation_confidence: None,
            created_by: Some("test_user".to_string()),
            created_at: None,
        };
        
        db.insert_arxobject(&obj).unwrap();
        
        // Test querying
        let objects = db.find_by_type(building_id, 0x10).unwrap();
        assert_eq!(objects.len(), 1);
        assert_eq!(objects[0].x, 1500);
    }
}