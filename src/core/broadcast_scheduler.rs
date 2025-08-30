//! Intelligent broadcast scheduling for slow-bleed protocol

use heapless::{BinaryHeap, Vec};
use crate::packet::{ChunkType, MeshPacket, DetailChunk};

/// Manages what to broadcast next in the slow-bleed protocol
pub struct BroadcastScheduler {
    /// Priority queue of chunks to send
    priority_queue: BinaryHeap<ChunkPriority, 256>,
    
    /// Recent broadcasts to avoid repetition
    recent_broadcasts: Vec<(u16, u16), 64>,
    
    /// Track mesh requests for popular chunks
    request_counts: heapless::FnvIndexMap<(u16, u16), u32, 128>,
    
    /// Round-robin position for fairness
    round_robin_index: usize,
}

/// Priority for broadcasting a chunk
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ChunkPriority {
    pub priority: u32,
    pub object_id: u16,
    pub chunk_id: u16,
    pub chunk_type: ChunkType,
}

impl PartialOrd for ChunkPriority {
    fn partial_cmp(&self, other: &Self) -> Option<core::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for ChunkPriority {
    fn cmp(&self, other: &Self) -> core::cmp::Ordering {
        self.priority.cmp(&other.priority)
    }
}

impl BroadcastScheduler {
    pub fn new() -> Self {
        Self {
            priority_queue: BinaryHeap::new(),
            recent_broadcasts: Vec::new(),
            request_counts: heapless::FnvIndexMap::new(),
            round_robin_index: 0,
        }
    }
    
    /// Add a chunk to the broadcast queue
    pub fn queue_chunk(&mut self, object_id: u16, chunk_id: u16, chunk_type: ChunkType) {
        let priority = self.calculate_priority(object_id, chunk_id, &chunk_type);
        
        let chunk_priority = ChunkPriority {
            priority,
            object_id,
            chunk_id,
            chunk_type,
        };
        
        let _ = self.priority_queue.push(chunk_priority);
    }
    
    /// Get the next chunk to broadcast
    pub fn next_chunk(&mut self) -> Option<ChunkPriority> {
        // Try to find a non-recent chunk
        for _ in 0..10 {  // Try up to 10 times
            if let Some(chunk) = self.priority_queue.pop() {
                let key = (chunk.object_id, chunk.chunk_id);
                
                // Check if recently broadcast
                if !self.was_recently_broadcast(key) {
                    self.mark_as_broadcast(key);
                    return Some(chunk);
                }
                
                // Re-queue with lower priority
                let mut lower_priority = chunk;
                lower_priority.priority = lower_priority.priority.saturating_sub(10);
                let _ = self.priority_queue.push(lower_priority);
            } else {
                break;
            }
        }
        
        // Fallback: return any chunk
        self.priority_queue.pop()
    }
    
    /// Record that a chunk was requested by the mesh
    pub fn record_request(&mut self, object_id: u16, chunk_id: u16) {
        let key = (object_id, chunk_id);
        let count = self.request_counts.entry(key).or_insert(0);
        *count = count.saturating_add(1);
    }
    
    /// Calculate priority for a chunk
    fn calculate_priority(&self, object_id: u16, chunk_id: u16, chunk_type: &ChunkType) -> u32 {
        let mut priority = 100;  // Base priority
        
        // Factor 1: Object criticality (electrical/safety > aesthetic)
        priority += match chunk_type {
            ChunkType::ElectricalConnections |
            ChunkType::FailurePrediction => 50,
            
            ChunkType::HVACConnections |
            ChunkType::MaintenanceSchedule => 40,
            
            ChunkType::MaterialStructural |
            ChunkType::StructuralSupports => 30,
            
            ChunkType::MaterialVisual |
            ChunkType::SurfaceProperties => 10,
            
            _ => 20,
        };
        
        // Factor 2: Request frequency
        if let Some(&requests) = self.request_counts.get(&(object_id, chunk_id)) {
            priority += requests.min(50);  // Cap at 50
        }
        
        // Factor 3: Chunk type importance
        priority += match chunk_type {
            // Critical for safety
            ChunkType::FailurePrediction => 100,
            ChunkType::MaintenanceSchedule => 80,
            
            // Important for operations
            ChunkType::ElectricalConnections => 60,
            ChunkType::HVACConnections => 60,
            
            // Useful for analysis
            ChunkType::PerformanceHistory => 40,
            ChunkType::EnergyHistory => 40,
            
            // Nice to have
            ChunkType::MaterialVisual => 20,
            _ => 30,
        };
        
        priority
    }
    
    /// Check if a chunk was recently broadcast
    fn was_recently_broadcast(&self, key: (u16, u16)) -> bool {
        self.recent_broadcasts.iter().any(|&k| k == key)
    }
    
    /// Mark a chunk as broadcast
    fn mark_as_broadcast(&mut self, key: (u16, u16)) {
        if self.recent_broadcasts.is_full() {
            // Remove oldest (front)
            self.recent_broadcasts.swap_remove(0);
        }
        let _ = self.recent_broadcasts.push(key);
    }
    
    /// Get scheduler statistics
    pub fn stats(&self) -> SchedulerStats {
        SchedulerStats {
            queue_depth: self.priority_queue.len(),
            recent_broadcasts: self.recent_broadcasts.len(),
            total_requests: self.request_counts.values().sum(),
        }
    }
}

pub struct SchedulerStats {
    pub queue_depth: usize,
    pub recent_broadcasts: usize,
    pub total_requests: u32,
}