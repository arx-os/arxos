//! Consciousness Field Persistence
//! 
//! Stores consciousness fields with integrated information theory metrics

use crate::holographic::consciousness::{ConsciousnessField, QualiaSpace};
use crate::holographic::quantum::ArxObjectId;
use crate::holographic::error::{Result, HolographicError};
use super::connection_pool::ConnectionPool;
use rusqlite::params;

/// Store for consciousness field persistence
pub struct ConsciousnessStore {
    pool: ConnectionPool,
}

impl ConsciousnessStore {
    /// Create a new consciousness store
    pub fn new(pool: ConnectionPool) -> Self {
        Self { pool }
    }
    
    /// Save a consciousness field
    pub fn save_field(&self, arxobject_id: ArxObjectId, field: &ConsciousnessField) -> Result<i64> {
        let conn = self.pool.get()?;
        
        let mut stmt = conn.prepare(
            "INSERT OR REPLACE INTO consciousness_fields 
             (arxobject_id, phi, strength, coherence, causal_power, resonance_frequency,
              qualia_color_r, qualia_color_g, qualia_color_b,
              qualia_intensity, qualia_texture, qualia_harmony, qualia_novelty) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)"
        )?;
        
        stmt.execute(params![
            arxobject_id as i64,
            field.phi,
            field.strength,
            field.coherence,
            field.causal_power,
            field.resonance_frequency,
            field.qualia.color.0,
            field.qualia.color.1,
            field.qualia.color.2,
            field.qualia.intensity,
            field.qualia.texture,
            field.qualia.harmony,
            field.qualia.novelty,
        ])?;
        
        Ok(conn.last_insert_rowid())
    }
    
    /// Load consciousness field for an ArxObject
    pub fn load_field(&self, arxobject_id: ArxObjectId) -> Result<Option<ConsciousnessField>> {
        let conn = self.pool.get()?;
        
        let mut stmt = conn.prepare(
            "SELECT phi, strength, coherence, causal_power, resonance_frequency,
                    qualia_color_r, qualia_color_g, qualia_color_b,
                    qualia_intensity, qualia_texture, qualia_harmony, qualia_novelty
             FROM consciousness_fields 
             WHERE arxobject_id = ?1 
             ORDER BY updated_at DESC 
             LIMIT 1"
        )?;
        
        let result = stmt.query_row(params![arxobject_id as i64], |row| {
            Ok(ConsciousnessField {
                phi: row.get(0)?,
                strength: row.get(1)?,
                coherence: row.get(2)?,
                causal_power: row.get(3)?,
                resonance_frequency: row.get(4)?,
                qualia: QualiaSpace {
                    color: (
                        row.get::<_, f32>(5)?,
                        row.get::<_, f32>(6)?,
                        row.get::<_, f32>(7)?,
                    ),
                    intensity: row.get(8)?,
                    texture: row.get(9)?,
                    harmony: row.get(10)?,
                    novelty: row.get(11)?,
                    dimensions: Vec::new(), // Would need separate table for custom dimensions
                },
            })
        });
        
        match result {
            Ok(field) => Ok(Some(field)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(HolographicError::InvalidInput(format!("Query error: {}", e))),
        }
    }
    
    /// Find consciousness clusters above a phi threshold
    pub fn find_clusters(&self, min_phi: f32, radius: f32) -> Result<Vec<ClusterInfo>> {
        let conn = self.pool.get()?;
        
        // First, find all high-phi objects
        let mut stmt = conn.prepare(
            "SELECT cf.arxobject_id, cf.phi, a.x, a.y, a.z 
             FROM consciousness_fields cf
             JOIN arxobjects a ON cf.arxobject_id = a.id
             WHERE cf.phi >= ?1"
        )?;
        
        let high_phi_objects: Vec<(ArxObjectId, f32, f32, f32, f32)> = 
            stmt.query_map(params![min_phi], |row| {
                Ok((
                    row.get::<_, i64>(0)? as ArxObjectId,
                    row.get(1)?,
                    row.get::<_, i64>(2)? as f32,
                    row.get::<_, i64>(3)? as f32,
                    row.get::<_, i64>(4)? as f32,
                ))
            })?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| HolographicError::InvalidInput(format!("Query error: {}", e)))?;
        
        // Cluster using simple distance-based algorithm
        let mut clusters = Vec::new();
        let mut visited = std::collections::HashSet::new();
        
        for &(id, phi, x, y, z) in &high_phi_objects {
            if visited.contains(&id) {
                continue;
            }
            
            let mut cluster_members = Vec::new();
            let mut cluster_phi_sum = 0.0;
            let mut center = (0.0, 0.0, 0.0);
            
            // Find all objects within radius
            for &(other_id, other_phi, ox, oy, oz) in &high_phi_objects {
                let dist = ((x - ox).powi(2) + (y - oy).powi(2) + (z - oz).powi(2)).sqrt();
                if dist <= radius {
                    cluster_members.push(other_id);
                    cluster_phi_sum += other_phi;
                    center.0 += ox;
                    center.1 += oy;
                    center.2 += oz;
                    visited.insert(other_id);
                }
            }
            
            if !cluster_members.is_empty() {
                let count = cluster_members.len() as f32;
                clusters.push(ClusterInfo {
                    cluster_phi: cluster_phi_sum / count,
                    center: (center.0 / count, center.1 / count, center.2 / count),
                    radius,
                    member_count: cluster_members.len(),
                    member_ids: cluster_members,
                });
            }
        }
        
        // Save clusters to database
        for cluster in &clusters {
            self.save_cluster(&conn, cluster)?;
        }
        
        Ok(clusters)
    }
    
    /// Save a consciousness cluster
    fn save_cluster(&self, conn: &super::connection_pool::PooledConnection, cluster: &ClusterInfo) -> Result<i64> {
        // Insert cluster
        let mut stmt = conn.prepare(
            "INSERT INTO consciousness_clusters 
             (cluster_phi, center_x, center_y, center_z, radius, member_count) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)"
        )?;
        
        stmt.execute(params![
            cluster.cluster_phi,
            cluster.center.0,
            cluster.center.1,
            cluster.center.2,
            cluster.radius,
            cluster.member_count,
        ])?;
        
        let cluster_id = conn.last_insert_rowid();
        
        // Insert cluster members
        let mut member_stmt = conn.prepare(
            "INSERT INTO cluster_members (cluster_id, arxobject_id, contribution) 
             VALUES (?1, ?2, ?3)"
        )?;
        
        for &member_id in &cluster.member_ids {
            member_stmt.execute(params![
                cluster_id,
                member_id as i64,
                1.0 / cluster.member_count as f32, // Equal contribution for now
            ])?;
        }
        
        Ok(cluster_id)
    }
    
    /// Get fields with phi above threshold
    pub fn get_high_phi_fields(&self, min_phi: f32) -> Result<Vec<(ArxObjectId, ConsciousnessField)>> {
        let conn = self.pool.get()?;
        
        let mut stmt = conn.prepare(
            "SELECT arxobject_id, phi, strength, coherence, causal_power, resonance_frequency,
                    qualia_color_r, qualia_color_g, qualia_color_b,
                    qualia_intensity, qualia_texture, qualia_harmony, qualia_novelty
             FROM consciousness_fields 
             WHERE phi >= ?1 
             ORDER BY phi DESC"
        )?;
        
        let fields = stmt.query_map(params![min_phi], |row| {
            let id = row.get::<_, i64>(0)? as ArxObjectId;
            let field = ConsciousnessField {
                phi: row.get(1)?,
                strength: row.get(2)?,
                coherence: row.get(3)?,
                causal_power: row.get(4)?,
                resonance_frequency: row.get(5)?,
                qualia: QualiaSpace {
                    color: (
                        row.get::<_, f32>(6)?,
                        row.get::<_, f32>(7)?,
                        row.get::<_, f32>(8)?,
                    ),
                    intensity: row.get(9)?,
                    texture: row.get(10)?,
                    harmony: row.get(11)?,
                    novelty: row.get(12)?,
                    dimensions: Vec::new(),
                },
            };
            Ok((id, field))
        })?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| HolographicError::InvalidInput(format!("Query error: {}", e)))?;
        
        Ok(fields)
    }
}

/// Information about a consciousness cluster
#[derive(Debug, Clone)]
pub struct ClusterInfo {
    pub cluster_phi: f32,
    pub center: (f32, f32, f32),
    pub radius: f32,
    pub member_count: usize,
    pub member_ids: Vec<ArxObjectId>,
}