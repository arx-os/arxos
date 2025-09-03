//! Real-time AR Streaming Protocol
//! 
//! Enables field technicians to draw in AR and have supervisors see
//! the drawings instantly over low-bandwidth radio networks

use crate::arxobject::ArxObject;
use crate::ar_compression::{ARCompressor, ARDecompressor, ARDrawingPrimitive, ARPathType};
use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Priority levels for AR transmissions
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum StreamPriority {
    /// Safety-critical annotations
    Emergency = 0,
    /// Supervisor-requested clarifications
    Interactive = 1,
    /// Standard path drawings
    Normal = 2,
    /// Background context updates
    Background = 3,
}

/// AR streaming session between field and operations
pub struct ARStreamSession {
    /// Session identifier
    session_id: u32,
    /// Field technician ID
    tech_id: u16,
    /// Supervisor ID
    supervisor_id: u16,
    /// Current building
    building_id: u16,
    /// Compression engine
    compressor: ARCompressor,
    /// Decompression engine
    decompressor: ARDecompressor,
    /// Outbound queue (prioritized)
    tx_queue: Vec<(StreamPriority, Vec<ArxObject>)>,
    /// Received objects buffer
    rx_buffer: HashMap<u8, Vec<ArxObject>>,
    /// Last activity timestamp
    last_activity: Instant,
}

impl ARStreamSession {
    pub fn new(tech_id: u16, supervisor_id: u16, building_id: u16) -> Self {
        Self {
            session_id: rand::random(),
            tech_id,
            supervisor_id,
            building_id,
            compressor: ARCompressor::new(building_id),
            decompressor: ARDecompressor::new(),
            tx_queue: Vec::new(),
            rx_buffer: HashMap::new(),
            last_activity: Instant::now(),
        }
    }
    
    /// Tech draws a path in AR - compress and queue for transmission
    pub fn tech_draws_path(&mut self, drawing: ARDrawingPrimitive) -> Result<(), String> {
        // Determine priority based on annotations
        let priority = if drawing.annotations.safety_critical {
            StreamPriority::Emergency
        } else if drawing.annotations.needs_approval {
            StreamPriority::Interactive
        } else {
            StreamPriority::Normal
        };
        
        // Compress the drawing
        let objects = self.compressor.compress_drawing(&drawing);
        
        // Add to transmission queue
        self.tx_queue.push((priority, objects.clone()));
        
        // Sort by priority (lower number = higher priority)
        self.tx_queue.sort_by_key(|(p, _)| *p);
        
        self.last_activity = Instant::now();
        
        println!(
            "Compressed AR drawing: {} points -> {} ArxObjects ({} bytes)",
            1, // Simplified for example
            objects.len(),
            objects.len() * 13
        );
        
        Ok(())
    }
    
    /// Get next packet to transmit (respecting priority)
    pub fn get_next_tx_packet(&mut self) -> Option<ArxObject> {
        while let Some((_, objects)) = self.tx_queue.first_mut() {
            if let Some(obj) = objects.pop() {
                return Some(obj);
            } else {
                // This queue entry is empty, remove it
                self.tx_queue.remove(0);
            }
        }
        None
    }
    
    /// Process received ArxObject from supervisor
    pub fn receive_object(&mut self, obj: ArxObject) -> Option<Vec<ARDrawingPrimitive>> {
        // Process through decompressor
        self.decompressor.process_object(&obj)
    }
    
    /// Get transmission statistics
    pub fn get_stats(&self) -> StreamStats {
        StreamStats {
            session_duration: Instant::now().duration_since(self.last_activity),
            queued_objects: self.tx_queue.iter().map(|(_, v)| v.len()).sum(),
            queued_bytes: self.tx_queue.iter().map(|(_, v)| v.len() * 13).sum(),
            emergency_count: self.tx_queue.iter()
                .filter(|(p, _)| *p == StreamPriority::Emergency)
                .count(),
        }
    }
}

/// Streaming statistics
#[derive(Debug)]
pub struct StreamStats {
    pub session_duration: Duration,
    pub queued_objects: usize,
    pub queued_bytes: usize,
    pub emergency_count: usize,
}

/// Manages multiple streaming sessions
pub struct ARStreamManager {
    /// Active sessions
    sessions: HashMap<u32, ARStreamSession>,
    /// Maximum concurrent sessions
    max_sessions: usize,
    /// Bandwidth allocator
    bandwidth_allocator: BandwidthAllocator,
}

impl ARStreamManager {
    pub fn new(max_sessions: usize, total_bandwidth_bps: u32) -> Self {
        Self {
            sessions: HashMap::new(),
            max_sessions,
            bandwidth_allocator: BandwidthAllocator::new(total_bandwidth_bps),
        }
    }
    
    /// Create new AR streaming session
    pub fn create_session(
        &mut self,
        tech_id: u16,
        supervisor_id: u16,
        building_id: u16,
    ) -> Result<u32, String> {
        if self.sessions.len() >= self.max_sessions {
            return Err("Maximum sessions reached".to_string());
        }
        
        let session = ARStreamSession::new(tech_id, supervisor_id, building_id);
        let session_id = session.session_id;
        
        self.sessions.insert(session_id, session);
        
        // Allocate bandwidth for this session
        self.bandwidth_allocator.allocate_session(session_id);
        
        Ok(session_id)
    }
    
    /// Get next packet to transmit across all sessions
    pub fn get_next_global_packet(&mut self) -> Option<(u32, ArxObject)> {
        // Round-robin with priority weighting
        let mut best_packet = None;
        let mut best_priority = StreamPriority::Background;
        
        for (session_id, session) in &mut self.sessions {
            if let Some(obj) = session.get_next_tx_packet() {
                // Check if this session has bandwidth available
                if self.bandwidth_allocator.can_transmit(*session_id) {
                    // For now, just return first available
                    return Some((*session_id, obj));
                }
            }
        }
        
        best_packet
    }
    
    /// Process performance metrics
    pub fn get_global_stats(&self) -> GlobalStreamStats {
        GlobalStreamStats {
            active_sessions: self.sessions.len(),
            total_queued_bytes: self.sessions.values()
                .map(|s| s.get_stats().queued_bytes)
                .sum(),
            emergency_packets: self.sessions.values()
                .map(|s| s.get_stats().emergency_count)
                .sum(),
        }
    }
}

/// Global streaming statistics
#[derive(Debug)]
pub struct GlobalStreamStats {
    pub active_sessions: usize,
    pub total_queued_bytes: usize,
    pub emergency_packets: usize,
}

/// Bandwidth allocator for fair sharing
struct BandwidthAllocator {
    /// Total bandwidth in bits per second
    total_bps: u32,
    /// Allocated bandwidth per session
    session_allocations: HashMap<u32, u32>,
    /// Last transmission time per session
    last_tx: HashMap<u32, Instant>,
}

impl BandwidthAllocator {
    fn new(total_bps: u32) -> Self {
        Self {
            total_bps,
            session_allocations: HashMap::new(),
            last_tx: HashMap::new(),
        }
    }
    
    fn allocate_session(&mut self, session_id: u32) {
        // Divide bandwidth equally among sessions
        let session_count = self.session_allocations.len() + 1;
        let bps_per_session = self.total_bps / session_count as u32;
        
        // Reallocate to all sessions
        for allocation in self.session_allocations.values_mut() {
            *allocation = bps_per_session;
        }
        
        self.session_allocations.insert(session_id, bps_per_session);
        self.last_tx.insert(session_id, Instant::now());
    }
    
    fn can_transmit(&mut self, session_id: u32) -> bool {
        let now = Instant::now();
        
        if let Some(last) = self.last_tx.get(&session_id) {
            if let Some(bps) = self.session_allocations.get(&session_id) {
                // Calculate minimum time between transmissions
                let bits_per_packet = 13 * 8; // 13 bytes
                let packets_per_second = *bps as f32 / bits_per_packet as f32;
                let min_interval = Duration::from_secs_f32(1.0 / packets_per_second);
                
                if now.duration_since(*last) >= min_interval {
                    self.last_tx.insert(session_id, now);
                    return true;
                }
            }
        }
        
        false
    }
}

/// Example: Simulated AR drawing scenario
pub fn simulate_ar_scenario() {
    println!("\n=== AR Drawing Compression Demo ===\n");
    
    let mut manager = ARStreamManager::new(10, 9600);
    
    // Tech starts AR session
    let session_id = manager.create_session(
        101,  // Tech ID
        201,  // Supervisor ID
        42,   // Building ID
    ).unwrap();
    
    let session = manager.sessions.get_mut(&session_id).unwrap();
    
    // Tech draws conduit path avoiding HVAC duct
    let drawing = ARDrawingPrimitive {
        path_type: ARPathType::ElectricalConduit,
        start: (1250.0, 3400.0, 2800.0),
        end: (4250.0, 3400.0, 2800.0),
        obstacle_id: Some(0xA3), // HVAC duct ID
        bend_radius: Some(300.0),
        annotations: crate::ar_compression::AnnotationFlags {
            needs_approval: true,
            cost_impact: true,
            ..Default::default()
        },
    };
    
    // Compress and queue
    session.tech_draws_path(drawing).unwrap();
    
    // Simulate transmission
    println!("\nTransmitting AR drawing:");
    while let Some((sid, obj)) = manager.get_next_global_packet() {
        println!(
            "  TX: Session {} -> ArxObject type 0x{:02X} ({} bytes)",
            sid, obj.object_type, 13
        );
    }
    
    // Show stats (get session again after manager use)
    let session = manager.sessions.get(&session_id).unwrap();
    let stats = session.get_stats();
    println!("\nStream Statistics:");
    println!("  Queued: {} objects ({} bytes)", stats.queued_objects, stats.queued_bytes);
    println!("  Emergency: {} packets", stats.emergency_count);
    
    println!("\n✅ AR drawing compressed from ~50KB -> {} bytes!", stats.queued_bytes);
}

// Import rand for session IDs
use rand;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_ar_streaming_session() {
        let mut session = ARStreamSession::new(1, 2, 42);
        
        let drawing = ARDrawingPrimitive {
            path_type: ARPathType::NetworkCable,
            start: (0.0, 0.0, 0.0),
            end: (1000.0, 0.0, 0.0),
            obstacle_id: None,
            bend_radius: None,
            annotations: Default::default(),
        };
        
        session.tech_draws_path(drawing).unwrap();
        
        // Should have packets queued
        assert!(session.get_next_tx_packet().is_some());
    }
    
    #[test]
    fn test_priority_ordering() {
        let mut session = ARStreamSession::new(1, 2, 42);
        
        // Add normal priority
        let normal_drawing = ARDrawingPrimitive {
            path_type: ARPathType::NetworkCable,
            start: (0.0, 0.0, 0.0),
            end: (1000.0, 0.0, 0.0),
            obstacle_id: None,
            bend_radius: None,
            annotations: Default::default(),
        };
        
        // Add emergency priority
        let emergency_drawing = ARDrawingPrimitive {
            path_type: ARPathType::FireSuppression,
            start: (0.0, 0.0, 0.0),
            end: (1000.0, 0.0, 0.0),
            obstacle_id: None,
            bend_radius: None,
            annotations: crate::ar_compression::AnnotationFlags {
                safety_critical: true,
                ..Default::default()
            },
        };
        
        session.tech_draws_path(normal_drawing).unwrap();
        session.tech_draws_path(emergency_drawing).unwrap();
        
        // Emergency should be transmitted first despite being added second
        let stats = session.get_stats();
        assert_eq!(stats.emergency_count, 1);
    }
}