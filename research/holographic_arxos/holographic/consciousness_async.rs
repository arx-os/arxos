//! Async/Concurrent Consciousness System
//! 
//! High-performance parallel implementation of consciousness calculations
//! using tokio for async operations and rayon for CPU-bound parallelism.

use std::sync::Arc;
use parking_lot::RwLock;
use rayon::prelude::*;
use tokio::sync::{mpsc, oneshot};
use futures::future::join_all;
use std::collections::HashMap;

use crate::holographic::{
    consciousness::{ConsciousnessField, QualiaSpace},
    quantum::ArxObjectId,
    spatial_index::{SpatialIndex, Point3D},
    error::{Result, HolographicError},
};
use crate::arxobject::ArxObject;

/// Message types for consciousness updates
pub enum ConsciousnessMessage {
    UpdateField(ArxObjectId, ConsciousnessField),
    CalculatePhi(Vec<ArxObjectId>, oneshot::Sender<Vec<f32>>),
    GetField(ArxObjectId, oneshot::Sender<Option<ConsciousnessField>>),
    BatchUpdate(Vec<(ArxObjectId, ConsciousnessField)>),
}

/// Async consciousness field manager with parallel processing
pub struct AsyncBuildingConsciousness {
    /// Thread-safe field storage
    object_fields: Arc<RwLock<HashMap<ArxObjectId, ConsciousnessField>>>,
    
    /// Spatial index for efficient neighbor queries
    spatial_index: Arc<RwLock<SpatialIndex>>,
    
    /// Message channel for async updates
    tx: mpsc::UnboundedSender<ConsciousnessMessage>,
    
    /// Worker handle
    worker_handle: Option<tokio::task::JoinHandle<()>>,
    
    /// Thread pool for CPU-intensive calculations
    thread_pool: Arc<rayon::ThreadPool>,
}

impl AsyncBuildingConsciousness {
    /// Create new async consciousness system
    pub fn new() -> Self {
        let (tx, mut rx) = mpsc::unbounded_channel();
        let object_fields = Arc::new(RwLock::new(HashMap::new()));
        let spatial_index = Arc::new(RwLock::new(SpatialIndex::new(
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(65535.0, 65535.0, 65535.0),
        )));
        
        // Create custom thread pool for parallel processing
        let thread_pool = Arc::new(
            rayon::ThreadPoolBuilder::new()
                .num_threads(num_cpus::get())
                .thread_name(|i| format!("consciousness-worker-{}", i))
                .build()
                .expect("Failed to create consciousness thread pool")
        );
        
        // Clone for worker thread
        let fields_clone = Arc::clone(&object_fields);
        let spatial_clone = Arc::clone(&spatial_index);
        let pool_clone = Arc::clone(&thread_pool);
        
        // Spawn async worker
        let worker_handle = tokio::spawn(async move {
            while let Some(msg) = rx.recv().await {
                match msg {
                    ConsciousnessMessage::UpdateField(id, field) => {
                        let mut fields = fields_clone.write();
                        fields.insert(id, field);
                    }
                    ConsciousnessMessage::CalculatePhi(ids, response) => {
                        let fields = fields_clone.read();
                        let spatial = spatial_clone.read();
                        
                        // Parallel phi calculation
                        let phis = pool_clone.install(|| {
                            ids.par_iter()
                                .map(|id| {
                                    if let Some(field) = fields.get(id) {
                                        Self::calculate_phi_parallel(field, &fields, &spatial, *id)
                                    } else {
                                        0.0
                                    }
                                })
                                .collect()
                        });
                        
                        let _ = response.send(phis);
                    }
                    ConsciousnessMessage::GetField(id, response) => {
                        let fields = fields_clone.read();
                        let _ = response.send(fields.get(&id).cloned());
                    }
                    ConsciousnessMessage::BatchUpdate(updates) => {
                        let mut fields = fields_clone.write();
                        for (id, field) in updates {
                            fields.insert(id, field);
                        }
                    }
                }
            }
        });
        
        Self {
            object_fields,
            spatial_index,
            tx,
            worker_handle: Some(worker_handle),
            thread_pool,
        }
    }
    
    /// Add an object with its consciousness field
    pub async fn add_object(&self, id: ArxObjectId, field: ConsciousnessField, position: Point3D) -> Result<()> {
        // Update spatial index
        {
            let mut spatial = self.spatial_index.write();
            spatial.insert(id, position)?;
        }
        
        // Send async update
        self.tx.send(ConsciousnessMessage::UpdateField(id, field))
            .map_err(|_| HolographicError::InvalidInput("Worker thread died".to_string()))?;
        
        Ok(())
    }
    
    /// Batch update multiple objects in parallel
    pub async fn batch_update(&self, objects: Vec<(ArxObject, ConsciousnessField)>) -> Result<()> {
        // Update spatial index in parallel
        let spatial_updates: Vec<_> = objects
            .iter()
            .map(|(obj, _)| {
                let id = obj.building_id;
                let pos = Point3D::new(obj.x as f32, obj.y as f32, obj.z as f32);
                (id, pos)
            })
            .collect();
        
        {
            let mut spatial = self.spatial_index.write();
            for (id, pos) in spatial_updates {
                spatial.insert(id, pos).ok();
            }
        }
        
        // Send batch update
        let updates: Vec<_> = objects
            .into_iter()
            .map(|(obj, field)| (obj.building_id, field))
            .collect();
        
        self.tx.send(ConsciousnessMessage::BatchUpdate(updates))
            .map_err(|_| HolographicError::InvalidInput("Worker thread died".to_string()))?;
        
        Ok(())
    }
    
    /// Calculate phi for multiple objects in parallel
    pub async fn calculate_phi_batch(&self, ids: Vec<ArxObjectId>) -> Result<Vec<f32>> {
        let (tx, rx) = oneshot::channel();
        
        self.tx.send(ConsciousnessMessage::CalculatePhi(ids, tx))
            .map_err(|_| HolographicError::InvalidInput("Worker thread died".to_string()))?;
        
        rx.await
            .map_err(|_| HolographicError::InvalidInput("Failed to receive response".to_string()))
    }
    
    /// Parallel phi calculation using rayon
    fn calculate_phi_parallel(
        field: &ConsciousnessField,
        all_fields: &HashMap<ArxObjectId, ConsciousnessField>,
        spatial_index: &SpatialIndex,
        id: ArxObjectId,
    ) -> f32 {
        // Find nearby objects using spatial index
        if let Some(&pos) = spatial_index.object_positions.get(&id) {
            let nearby = spatial_index.find_within_radius(&pos, 100.0);
            
            // Parallel calculation of information integration
            let integration_sum: f32 = nearby
                .par_iter()
                .filter_map(|&other_id| {
                    if other_id != id {
                        all_fields.get(&other_id).map(|other_field| {
                            Self::calculate_integration(field, other_field)
                        })
                    } else {
                        None
                    }
                })
                .sum();
            
            // Normalize by number of connections
            let phi = if nearby.len() > 1 {
                integration_sum / (nearby.len() - 1) as f32
            } else {
                field.phi
            };
            
            phi.min(1.0)
        } else {
            field.phi
        }
    }
    
    /// Calculate integration between two consciousness fields
    fn calculate_integration(field1: &ConsciousnessField, field2: &ConsciousnessField) -> f32 {
        let phi_diff = (field1.phi - field2.phi).abs();
        let strength_product = field1.strength * field2.strength;
        let coherence_factor = (field1.coherence + field2.coherence) / 2.0;
        
        strength_product * coherence_factor * (1.0 - phi_diff)
    }
    
    /// Get a single field
    pub async fn get_field(&self, id: ArxObjectId) -> Option<ConsciousnessField> {
        let (tx, rx) = oneshot::channel();
        
        self.tx.send(ConsciousnessMessage::GetField(id, tx)).ok()?;
        rx.await.ok()?
    }
    
    /// Process consciousness evolution in parallel
    pub async fn evolve_consciousness(&self, time_delta: f32) -> Result<()> {
        let fields = self.object_fields.read();
        let ids: Vec<_> = fields.keys().copied().collect();
        drop(fields); // Release lock
        
        // Calculate new phi values in parallel
        let new_phis = self.calculate_phi_batch(ids.clone()).await?;
        
        // Update fields with evolution
        let updates: Vec<_> = self.thread_pool.install(|| {
            ids.par_iter()
                .zip(new_phis.par_iter())
                .filter_map(|(id, new_phi)| {
                    let fields = self.object_fields.read();
                    fields.get(id).map(|field| {
                        let mut evolved = field.clone();
                        
                        // Smooth evolution
                        let phi_delta = (new_phi - evolved.phi) * time_delta;
                        evolved.phi = (evolved.phi + phi_delta).clamp(0.0, 1.0);
                        
                        // Update other properties
                        evolved.strength *= (1.0 - time_delta * 0.01); // Slight decay
                        evolved.coherence = (evolved.coherence + new_phi) / 2.0;
                        
                        (*id, evolved)
                    })
                })
                .collect()
        });
        
        // Send batch update
        self.tx.send(ConsciousnessMessage::BatchUpdate(updates))
            .map_err(|_| HolographicError::InvalidInput("Worker thread died".to_string()))?;
        
        Ok(())
    }
    
    /// Find consciousness clusters using parallel analysis
    pub async fn find_consciousness_clusters(&self, min_phi: f32) -> Vec<Vec<ArxObjectId>> {
        let fields = self.object_fields.read();
        let spatial = self.spatial_index.read();
        
        // Filter high-consciousness objects
        let high_phi_objects: Vec<_> = fields
            .iter()
            .filter(|(_, field)| field.phi >= min_phi)
            .map(|(id, _)| *id)
            .collect();
        
        // Parallel clustering using spatial proximity
        self.thread_pool.install(|| {
            let mut clusters = Vec::new();
            let mut visited = std::collections::HashSet::new();
            
            for &id in &high_phi_objects {
                if visited.contains(&id) {
                    continue;
                }
                
                let mut cluster = Vec::new();
                let mut to_visit = vec![id];
                
                while let Some(current) = to_visit.pop() {
                    if !visited.insert(current) {
                        continue;
                    }
                    
                    cluster.push(current);
                    
                    // Find nearby high-consciousness objects
                    if let Some(&pos) = spatial.object_positions.get(&current) {
                        let nearby = spatial.find_within_radius(&pos, 50.0);
                        for &nearby_id in &nearby {
                            if high_phi_objects.contains(&nearby_id) && !visited.contains(&nearby_id) {
                                to_visit.push(nearby_id);
                            }
                        }
                    }
                }
                
                if !cluster.is_empty() {
                    clusters.push(cluster);
                }
            }
            
            clusters
        })
    }
    
    /// Shutdown the worker thread gracefully
    pub async fn shutdown(mut self) {
        drop(self.tx);
        if let Some(handle) = self.worker_handle.take() {
            handle.await.ok();
        }
    }
}

/// Parallel consciousness field calculator
pub struct ParallelPhiCalculator {
    thread_pool: Arc<rayon::ThreadPool>,
}

impl ParallelPhiCalculator {
    pub fn new(num_threads: Option<usize>) -> Self {
        let thread_pool = Arc::new(
            rayon::ThreadPoolBuilder::new()
                .num_threads(num_threads.unwrap_or_else(num_cpus::get))
                .build()
                .expect("Failed to create ParallelPhiCalculator thread pool")
        );
        
        Self { thread_pool }
    }
    
    /// Calculate phi for all objects in parallel
    pub fn calculate_all(&self, objects: &[ArxObject]) -> Vec<f32> {
        self.thread_pool.install(|| {
            objects
                .par_iter()
                .map(|obj| self.calculate_single(obj))
                .collect()
        })
    }
    
    /// Calculate phi for a single object
    fn calculate_single(&self, object: &ArxObject) -> f32 {
        // Simplified phi calculation based on object properties
        let base_phi = (object.object_type as f32) / 255.0;
        let spatial_factor = ((object.x ^ object.y ^ object.z) as f32) / 65535.0;
        
        (base_phi + spatial_factor) / 2.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_async_consciousness() -> Result<()> {
        let consciousness = AsyncBuildingConsciousness::new();
        
        // Add some objects
        let field = ConsciousnessField {
            phi: 0.5,
            strength: 0.8,
            qualia: QualiaSpace::default(),
            causal_power: 0.6,
            resonance_frequency: 10.0,
            coherence: 0.7,
        };
        
        consciousness.add_object(1, field.clone(), Point3D::new(100.0, 100.0, 100.0)).await?;
        consciousness.add_object(2, field.clone(), Point3D::new(110.0, 100.0, 100.0)).await?;
        consciousness.add_object(3, field.clone(), Point3D::new(120.0, 100.0, 100.0)).await?;
        
        // Calculate phi in parallel
        let phis = consciousness.calculate_phi_batch(vec![1, 2, 3]).await?;
        assert_eq!(phis.len(), 3);
        
        // Evolve consciousness
        consciousness.evolve_consciousness(0.1).await?;
        
        // Find clusters
        let clusters = consciousness.find_consciousness_clusters(0.3).await;
        assert!(!clusters.is_empty());
        
        consciousness.shutdown().await;
        Ok(())
    }
    
    #[test]
    fn test_parallel_phi_calculator() {
        let calculator = ParallelPhiCalculator::new(Some(4));
        
        let objects: Vec<_> = (0..1000)
            .map(|i| ArxObject::new(i as u16, 1, 100, 100, 100))
            .collect();
        
        let phis = calculator.calculate_all(&objects);
        assert_eq!(phis.len(), 1000);
        
        // All phis should be in valid range
        for phi in phis {
            assert!(phi >= 0.0 && phi <= 1.0);
        }
    }
}