//! Simple SQLite persistence for ArxObjects with spatial indexing
//! 
//! Provides efficient storage and spatial queries for building intelligence

use crate::arxobject_simple::{ArxObject, ObjectCategory};
use rusqlite::{Connection, Result, params, Row};
use std::path::Path;

/// Simple ArxObject database
pub struct ArxObjectDatabase {
    conn: Connection,
}

impl ArxObjectDatabase {
    /// Create new database (in-memory for testing)
    pub fn new_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        let mut db = Self { conn };
        db.init_schema()?;
        Ok(db)
    }
    
    /// Open database from file
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let mut db = Self { conn };
        db.init_schema()?;
        Ok(db)
    }
    
    /// Initialize database schema with spatial indexing
    fn init_schema(&mut self) -> Result<()> {
        // Main ArxObject table
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS arxobjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                object_type INTEGER NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                z INTEGER NOT NULL,
                properties BLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Spatial index columns (in meters for queries)
                x_m REAL GENERATED ALWAYS AS (CAST(x AS REAL) / 1000.0) STORED,
                y_m REAL GENERATED ALWAYS AS (CAST(y AS REAL) / 1000.0) STORED,
                z_m REAL GENERATED ALWAYS AS (CAST(z AS REAL) / 1000.0) STORED
            )",
            [],
        )?;
        
        // Create spatial indices
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spatial_x ON arxobjects(x_m)",
            [],
        )?;
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spatial_y ON arxobjects(y_m)",
            [],
        )?;
        
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spatial_z ON arxobjects(z_m)",
            [],
        )?;
        
        // Compound index for 3D spatial queries
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spatial_xyz ON arxobjects(x_m, y_m, z_m)",
            [],
        )?;
        
        // Index for building and type queries
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_building_type ON arxobjects(building_id, object_type)",
            [],
        )?;
        
        Ok(())
    }
    
    /// Insert single ArxObject
    pub fn insert(&mut self, obj: &ArxObject) -> Result<i64> {
        let properties_bytes = obj.properties.to_vec();
        // Copy values to avoid packed field alignment issues
        let building_id = obj.building_id;
        let object_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        
        self.conn.execute(
            "INSERT INTO arxobjects (building_id, object_type, x, y, z, properties)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                building_id,
                object_type,
                x,
                y,
                z,
                properties_bytes,
            ],
        )?;
        
        Ok(self.conn.last_insert_rowid())
    }
    
    /// Batch insert ArxObjects
    pub fn insert_batch(&mut self, objects: &[ArxObject]) -> Result<usize> {
        let tx = self.conn.transaction()?;
        
        {
            let mut stmt = tx.prepare(
                "INSERT INTO arxobjects (building_id, object_type, x, y, z, properties)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6)"
            )?;
            
            for obj in objects {
                // Copy values to avoid packed field alignment issues
                let building_id = obj.building_id;
                let object_type = obj.object_type;
                let x = obj.x;
                let y = obj.y;
                let z = obj.z;
                let properties = obj.properties.to_vec();
                
                stmt.execute(params![
                    building_id,
                    object_type,
                    x,
                    y,
                    z,
                    properties,
                ])?;
            }
        }
        
        tx.commit()?;
        Ok(objects.len())
    }
    
    /// Find objects within a radius (in meters)
    pub fn find_within_radius(&self, x_m: f32, y_m: f32, z_m: f32, radius_m: f32) -> Result<Vec<ArxObject>> {
        let mut stmt = self.conn.prepare(
            "SELECT building_id, object_type, x, y, z, properties
             FROM arxobjects
             WHERE (x_m - ?1) * (x_m - ?1) + 
                   (y_m - ?2) * (y_m - ?2) + 
                   (z_m - ?3) * (z_m - ?3) <= ?4 * ?4"
        )?;
        
        let objects = stmt.query_map(params![x_m, y_m, z_m, radius_m], |row| {
            row_to_arxobject(row)
        })?;
        
        objects.collect()
    }
    
    /// Find objects in a bounding box (coordinates in meters)
    pub fn find_in_box(&self, 
                       min_x: f32, min_y: f32, min_z: f32,
                       max_x: f32, max_y: f32, max_z: f32) -> Result<Vec<ArxObject>> {
        let mut stmt = self.conn.prepare(
            "SELECT building_id, object_type, x, y, z, properties
             FROM arxobjects
             WHERE x_m >= ?1 AND x_m <= ?2
               AND y_m >= ?3 AND y_m <= ?4
               AND z_m >= ?5 AND z_m <= ?6"
        )?;
        
        let objects = stmt.query_map(
            params![min_x, max_x, min_y, max_y, min_z, max_z],
            |row| row_to_arxobject(row)
        )?;
        
        objects.collect()
    }
    
    /// Find objects by type in a building
    pub fn find_by_type(&self, building_id: u16, object_type: u8) -> Result<Vec<ArxObject>> {
        let mut stmt = self.conn.prepare(
            "SELECT building_id, object_type, x, y, z, properties
             FROM arxobjects
             WHERE building_id = ?1 AND object_type = ?2"
        )?;
        
        let objects = stmt.query_map(params![building_id, object_type], |row| {
            row_to_arxobject(row)
        })?;
        
        objects.collect()
    }
    
    /// Find nearest N objects to a point
    pub fn find_nearest(&self, x_m: f32, y_m: f32, z_m: f32, limit: usize) -> Result<Vec<(ArxObject, f32)>> {
        let mut stmt = self.conn.prepare(
            "SELECT building_id, object_type, x, y, z, properties,
                    SQRT((x_m - ?1) * (x_m - ?1) + 
                         (y_m - ?2) * (y_m - ?2) + 
                         (z_m - ?3) * (z_m - ?3)) as distance
             FROM arxobjects
             ORDER BY distance
             LIMIT ?4"
        )?;
        
        let objects = stmt.query_map(params![x_m, y_m, z_m, limit], |row| {
            let obj = row_to_arxobject(row)?;
            let distance: f32 = row.get(6)?;
            Ok((obj, distance))
        })?;
        
        objects.collect()
    }
    
    /// Get statistics about stored objects
    pub fn get_stats(&self) -> Result<DatabaseStats> {
        let total_count: i64 = self.conn.query_row(
            "SELECT COUNT(*) FROM arxobjects",
            [],
            |row| row.get(0)
        )?;
        
        let building_count: i64 = self.conn.query_row(
            "SELECT COUNT(DISTINCT building_id) FROM arxobjects",
            [],
            |row| row.get(0)
        )?;
        
        // Get type distribution
        let mut stmt = self.conn.prepare(
            "SELECT object_type, COUNT(*) 
             FROM arxobjects 
             GROUP BY object_type"
        )?;
        
        let type_distribution = stmt.query_map([], |row| {
            Ok((row.get::<_, u8>(0)?, row.get::<_, i64>(1)?))
        })?
        .collect::<Result<Vec<_>>>()?;
        
        Ok(DatabaseStats {
            total_objects: total_count as usize,
            building_count: building_count as usize,
            type_distribution,
        })
    }
    
    /// Clear all data (useful for testing)
    pub fn clear(&mut self) -> Result<()> {
        self.conn.execute("DELETE FROM arxobjects", [])?;
        Ok(())
    }
    
    /// Find objects on a specific floor (z range in meters)
    pub fn find_on_floor(&self, building_id: u16, floor_height_m: f32, tolerance_m: f32) -> Result<Vec<ArxObject>> {
        let min_z = floor_height_m - tolerance_m;
        let max_z = floor_height_m + tolerance_m;
        
        let mut stmt = self.conn.prepare(
            "SELECT building_id, object_type, x, y, z, properties
             FROM arxobjects
             WHERE building_id = ?1 AND z_m >= ?2 AND z_m <= ?3"
        )?;
        
        let objects = stmt.query_map(params![building_id, min_z, max_z], |row| {
            row_to_arxobject(row)
        })?;
        
        objects.collect()
    }
    
    /// Get all objects for a building
    pub fn get_building_objects(&self, building_id: u16) -> Result<Vec<ArxObject>> {
        let mut stmt = self.conn.prepare(
            "SELECT building_id, object_type, x, y, z, properties
             FROM arxobjects
             WHERE building_id = ?1
             ORDER BY z, y, x"
        )?;
        
        let objects = stmt.query_map(params![building_id], |row| {
            row_to_arxobject(row)
        })?;
        
        objects.collect()
    }
}

/// Convert database row to ArxObject
fn row_to_arxobject(row: &Row) -> Result<ArxObject> {
    let building_id: u16 = row.get(0)?;
    let object_type: u8 = row.get(1)?;
    let x: u16 = row.get(2)?;
    let y: u16 = row.get(3)?;
    let z: u16 = row.get(4)?;
    let properties_vec: Vec<u8> = row.get(5)?;
    
    let mut properties = [0u8; 4];
    for (i, &byte) in properties_vec.iter().take(4).enumerate() {
        properties[i] = byte;
    }
    
    Ok(ArxObject::with_properties(
        building_id,
        object_type,
        x,
        y,
        z,
        properties,
    ))
}

/// Database statistics
#[derive(Debug)]
pub struct DatabaseStats {
    pub total_objects: usize,
    pub building_count: usize,
    pub type_distribution: Vec<(u8, i64)>,
}

impl DatabaseStats {
    /// Print formatted statistics
    pub fn print_summary(&self) {
        println!("Database Statistics:");
        println!("  Total objects: {}", self.total_objects);
        println!("  Buildings: {}", self.building_count);
        println!("  Type distribution:");
        
        for (obj_type, count) in &self.type_distribution {
            let category = ObjectCategory::from_type(*obj_type);
            println!("    {:?} (0x{:02X}): {}", category, obj_type, count);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_database_operations() {
        let mut db = ArxObjectDatabase::new_memory().unwrap();
        
        // Insert test object
        let obj = ArxObject::new(0x0001, object_types::OUTLET, 5000, 3000, 300);
        let id = db.insert(&obj).unwrap();
        assert!(id > 0);
        
        // Find by type
        let outlets = db.find_by_type(0x0001, object_types::OUTLET).unwrap();
        assert_eq!(outlets.len(), 1);
        
        // Spatial query - find within radius
        let nearby = db.find_within_radius(5.0, 3.0, 0.3, 1.0).unwrap();
        assert_eq!(nearby.len(), 1);
        
        // Find in bounding box
        let in_box = db.find_in_box(4.0, 2.0, 0.0, 6.0, 4.0, 1.0).unwrap();
        assert_eq!(in_box.len(), 1);
    }
    
    #[test]
    fn test_batch_insert() {
        let mut db = ArxObjectDatabase::new_memory().unwrap();
        
        let objects = vec![
            ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300),
            ArxObject::new(0x0001, object_types::LIGHT_SWITCH, 2000, 1000, 1200),
            ArxObject::new(0x0001, object_types::THERMOSTAT, 3000, 2000, 1500),
        ];
        
        let count = db.insert_batch(&objects).unwrap();
        assert_eq!(count, 3);
        
        let stats = db.get_stats().unwrap();
        assert_eq!(stats.total_objects, 3);
    }
    
    #[test]
    fn test_nearest_query() {
        let mut db = ArxObjectDatabase::new_memory().unwrap();
        
        // Insert objects at different distances
        db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300)).unwrap();
        db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 2000, 2000, 300)).unwrap();
        db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 5000, 5000, 300)).unwrap();
        
        // Find nearest to origin
        let nearest = db.find_nearest(0.0, 0.0, 0.3, 2).unwrap();
        assert_eq!(nearest.len(), 2);
        
        // Closest should be at (1,1)
        assert_eq!(nearest[0].0.x, 1000);
        assert_eq!(nearest[0].0.y, 1000);
    }
}