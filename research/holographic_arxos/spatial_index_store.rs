//! Spatial Index Store using R-tree
//! 
//! Provides efficient 3D spatial queries using SQLite's R-tree module

use crate::holographic::quantum::ArxObjectId;
use crate::holographic::error::{Result, HolographicError};
use super::connection_pool::ConnectionPool;
use rusqlite::params;

/// Store for spatial indexing
pub struct SpatialIndexStore {
    pool: ConnectionPool,
    rtree_available: bool,
}

impl SpatialIndexStore {
    /// Create a new spatial index store
    pub fn new(pool: ConnectionPool) -> Self {
        // Check if R-tree is available
        let rtree_available = Self::check_rtree_support(&pool);
        
        Self {
            pool,
            rtree_available,
        }
    }
    
    /// Check if SQLite has R-tree support
    fn check_rtree_support(pool: &ConnectionPool) -> bool {
        if let Ok(conn) = pool.get() {
            // Try to create a test R-tree table
            let result = conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS rtree_test USING rtree(id, minX, maxX)",
                [],
            );
            
            if result.is_ok() {
                // Clean up test table
                let _ = conn.execute("DROP TABLE IF EXISTS rtree_test", []);
                return true;
            }
        }
        false
    }
    
    /// Insert or update spatial index for an object
    pub fn index_object(&self, id: ArxObjectId, x: u16, y: u16, z: u16, radius: u16) -> Result<()> {
        let conn = self.pool.get()?;
        
        if self.rtree_available {
            // Use R-tree index
            conn.execute(
                "INSERT OR REPLACE INTO spatial_index 
                 (id, min_x, max_x, min_y, max_y, min_z, max_z) 
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                params![
                    id as i64,
                    x.saturating_sub(radius) as i64,
                    x.saturating_add(radius) as i64,
                    y.saturating_sub(radius) as i64,
                    y.saturating_add(radius) as i64,
                    z.saturating_sub(radius) as i64,
                    z.saturating_add(radius) as i64,
                ],
            )?;
        }
        // If no R-tree, we rely on regular indexes on arxobjects table
        
        Ok(())
    }
    
    /// Remove object from spatial index
    pub fn remove_object(&self, id: ArxObjectId) -> Result<()> {
        if self.rtree_available {
            let conn = self.pool.get()?;
            conn.execute(
                "DELETE FROM spatial_index WHERE id = ?1",
                params![id as i64],
            )?;
        }
        Ok(())
    }
    
    /// Query objects within a bounding box
    pub fn query_bbox(
        &self,
        min_x: u16, max_x: u16,
        min_y: u16, max_y: u16,
        min_z: u16, max_z: u16,
    ) -> Result<Vec<ArxObjectId>> {
        let conn = self.pool.get()?;
        
        let ids = if self.rtree_available {
            // Use R-tree for efficient query
            let mut stmt = conn.prepare(
                "SELECT id FROM spatial_index 
                 WHERE max_x >= ?1 AND min_x <= ?2 
                   AND max_y >= ?3 AND min_y <= ?4 
                   AND max_z >= ?5 AND min_z <= ?6"
            )?;
            
            stmt.query_map(
                params![
                    min_x as i64, max_x as i64,
                    min_y as i64, max_y as i64,
                    min_z as i64, max_z as i64,
                ],
                |row| row.get::<_, i64>(0),
            )?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| HolographicError::InvalidInput(format!("Query error: {}", e)))?
        } else {
            // Fall back to regular index query
            let mut stmt = conn.prepare(
                "SELECT id FROM arxobjects 
                 WHERE x BETWEEN ?1 AND ?2 
                   AND y BETWEEN ?3 AND ?4 
                   AND z BETWEEN ?5 AND ?6"
            )?;
            
            stmt.query_map(
                params![
                    min_x as i64, max_x as i64,
                    min_y as i64, max_y as i64,
                    min_z as i64, max_z as i64,
                ],
                |row| row.get::<_, i64>(0),
            )?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| HolographicError::InvalidInput(format!("Query error: {}", e)))?
        };
        
        Ok(ids.into_iter().map(|id| id as ArxObjectId).collect())
    }
    
    /// Find k nearest neighbors to a point
    pub fn find_k_nearest(&self, x: u16, y: u16, z: u16, k: usize) -> Result<Vec<(ArxObjectId, f32)>> {
        let conn = self.pool.get()?;
        
        // For k-NN, we need to calculate actual distances
        // Start with a reasonable search radius and expand if needed
        let mut search_radius = 1000u16;
        let mut results = Vec::new();
        
        while results.len() < k && search_radius < u16::MAX / 2 {
            let candidates = self.query_bbox(
                x.saturating_sub(search_radius),
                x.saturating_add(search_radius),
                y.saturating_sub(search_radius),
                y.saturating_add(search_radius),
                z.saturating_sub(search_radius),
                z.saturating_add(search_radius),
            )?;
            
            // Calculate distances for all candidates
            let mut stmt = conn.prepare(
                "SELECT id, x, y, z FROM arxobjects WHERE id IN (
                    SELECT value FROM json_each(?1)
                )"
            )?;
            
            let candidate_json = format!("[{}]", 
                candidates.iter()
                    .map(|id| id.to_string())
                    .collect::<Vec<_>>()
                    .join(",")
            );
            
            results = stmt.query_map(params![candidate_json], |row| {
                let id: i64 = row.get(0)?;
                let ox: i64 = row.get(1)?;
                let oy: i64 = row.get(2)?;
                let oz: i64 = row.get(3)?;
                
                let dx = (ox - x as i64) as f32;
                let dy = (oy - y as i64) as f32;
                let dz = (oz - z as i64) as f32;
                let distance = (dx * dx + dy * dy + dz * dz).sqrt();
                
                Ok((id as ArxObjectId, distance))
            })?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| HolographicError::InvalidInput(format!("Query error: {}", e)))?;
            
            // Sort by distance
            results.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
            
            // If we have enough results, truncate
            if results.len() >= k {
                results.truncate(k);
                break;
            }
            
            // Expand search radius
            search_radius = search_radius.saturating_mul(2);
        }
        
        Ok(results)
    }
    
    /// Rebuild the entire spatial index from arxobjects table
    pub fn rebuild_index(&self) -> Result<()> {
        if !self.rtree_available {
            return Ok(()); // Nothing to rebuild
        }
        
        let conn = self.pool.get()?;
        
        // Clear existing index
        conn.execute("DELETE FROM spatial_index", [])?;
        
        // Rebuild from arxobjects
        conn.execute(
            "INSERT INTO spatial_index (id, min_x, max_x, min_y, max_y, min_z, max_z)
             SELECT id, x, x, y, y, z, z FROM arxobjects",
            [],
        )?;
        
        Ok(())
    }
    
    /// Get statistics about the spatial index
    pub fn stats(&self) -> Result<SpatialIndexStats> {
        let conn = self.pool.get()?;
        
        let indexed_count = if self.rtree_available {
            conn.query_row(
                "SELECT COUNT(*) FROM spatial_index",
                [],
                |row| row.get::<_, i64>(0),
            )? as usize
        } else {
            0
        };
        
        let total_objects = conn.query_row(
            "SELECT COUNT(*) FROM arxobjects",
            [],
            |row| row.get::<_, i64>(0),
        )? as usize;
        
        Ok(SpatialIndexStats {
            rtree_available: self.rtree_available,
            indexed_objects: indexed_count,
            total_objects,
        })
    }
}

/// Spatial index statistics
#[derive(Debug, Clone)]
pub struct SpatialIndexStats {
    pub rtree_available: bool,
    pub indexed_objects: usize,
    pub total_objects: usize,
}