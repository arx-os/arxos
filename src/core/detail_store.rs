//! Progressive detail accumulation for slow-bleed architecture

use heapless::{FnvIndexMap, Vec};
use crate::packet::{DetailChunk, ChunkType};

/// Stores progressively accumulated detail for objects
pub struct DetailStore {
    /// Chunk storage with limited capacity for embedded systems
    chunks: FnvIndexMap<(u16, u16), DetailChunk, 1024>,
    
    /// Track completeness per object
    completeness: FnvIndexMap<u16, DetailLevel, 256>,
}

/// Tracks how complete our knowledge of an object is
#[derive(Clone, Debug, Default)]
pub struct DetailLevel {
    pub basic: bool,         // Have 13-byte object
    pub material: f32,       // Material properties (0-1)
    pub systems: f32,        // System connections (0-1)
    pub historical: f32,     // Historical data (0-1)
    pub simulation: f32,     // Simulation models (0-1)
    pub predictive: f32,     // Predictive analytics (0-1)
}

impl DetailLevel {
    /// Calculate overall completeness (0.0 to 1.0)
    pub fn completeness(&self) -> f32 {
        let weights = [
            if self.basic { 0.1 } else { 0.0 },
            self.material * 0.2,
            self.systems * 0.2,
            self.historical * 0.2,
            self.simulation * 0.15,
            self.predictive * 0.15,
        ];
        
        weights.iter().sum::<f32>().min(1.0)
    }
    
    /// Check if we have enough detail for CAD rendering
    pub fn has_cad_detail(&self) -> bool {
        self.completeness() > 0.7
    }
    
    /// Check if we have enough for basic visualization
    pub fn has_basic_detail(&self) -> bool {
        self.basic && self.material > 0.3
    }
}

impl DetailStore {
    /// Create a new detail store
    pub fn new() -> Self {
        Self {
            chunks: FnvIndexMap::new(),
            completeness: FnvIndexMap::new(),
        }
    }
    
    /// Add a detail chunk
    pub fn add_chunk(&mut self, chunk: DetailChunk) -> Result<(), DetailChunk> {
        let key = (chunk.object_id, chunk.chunk_id);
        
        // Update completeness tracking
        self.update_completeness(chunk.object_id, &chunk.chunk_type);
        
        // Store the chunk
        self.chunks.insert(key, chunk).map_err(|e| e.1)?;
        
        Ok(())
    }
    
    /// Get a specific chunk
    pub fn get_chunk(&self, object_id: u16, chunk_id: u16) -> Option<&DetailChunk> {
        self.chunks.get(&(object_id, chunk_id))
    }
    
    /// Get all chunks for an object
    pub fn get_object_chunks(&self, object_id: u16) -> Vec<&DetailChunk, 64> {
        let mut chunks = Vec::new();
        
        for ((oid, _), chunk) in &self.chunks {
            if *oid == object_id {
                let _ = chunks.push(chunk);
            }
        }
        
        chunks
    }
    
    /// Get completeness level for an object
    pub fn get_completeness(&self, object_id: u16) -> DetailLevel {
        self.completeness
            .get(&object_id)
            .cloned()
            .unwrap_or_default()
    }
    
    /// Update completeness based on chunk type
    fn update_completeness(&mut self, object_id: u16, chunk_type: &ChunkType) {
        // Use get_mut or insert pattern for heapless
        let level = if let Some(level) = self.completeness.get_mut(&object_id) {
            level
        } else {
            self.completeness.insert(object_id, DetailLevel::default()).ok();
            self.completeness.get_mut(&object_id).unwrap()
        };
        
        match chunk_type {
            ChunkType::MaterialDensity |
            ChunkType::MaterialThermal |
            ChunkType::MaterialAcoustic |
            ChunkType::MaterialStructural => {
                level.material = (level.material + 0.25).min(1.0);
            }
            
            ChunkType::ElectricalConnections |
            ChunkType::HVACConnections |
            ChunkType::PlumbingConnections => {
                level.systems = (level.systems + 0.33).min(1.0);
            }
            
            ChunkType::MaintenanceHistory |
            ChunkType::PerformanceHistory |
            ChunkType::FailureHistory => {
                level.historical = (level.historical + 0.33).min(1.0);
            }
            
            ChunkType::ThermalModel |
            ChunkType::AirflowModel |
            ChunkType::ElectricalModel => {
                level.simulation = (level.simulation + 0.33).min(1.0);
            }
            
            ChunkType::FailurePrediction |
            ChunkType::MaintenanceSchedule |
            ChunkType::OptimizationParams => {
                level.predictive = (level.predictive + 0.33).min(1.0);
            }
            
            _ => {}
        }
    }
    
    /// Get objects that are nearly complete (for priority broadcasting)
    pub fn get_nearly_complete(&self, threshold: f32) -> Vec<u16, 32> {
        let mut objects = Vec::new();
        
        for (object_id, level) in &self.completeness {
            let completeness = level.completeness();
            if completeness >= threshold && completeness < 1.0 {
                let _ = objects.push(*object_id);
            }
        }
        
        objects
    }
    
    /// Calculate total storage used
    pub fn storage_used(&self) -> usize {
        self.chunks.len() * core::mem::size_of::<DetailChunk>()
    }
    
    /// Clear old chunks to free memory
    pub fn clear_old_chunks(&mut self, age_threshold: u32, current_time: u32) {
        // Manually filter chunks for heapless compatibility
        let mut to_remove = Vec::<(u16, u16), 64>::new();
        for (key, chunk) in self.chunks.iter() {
            if current_time.saturating_sub(chunk.timestamp) >= age_threshold {
                let _ = to_remove.push(*key);
            }
        }
        for key in to_remove {
            self.chunks.remove(&key);
        }
    }
}