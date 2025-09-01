//! Slow-bleed mesh node implementation

use heapless::FnvIndexMap;
use crate::{
    ArxObject, 
    MeshPacket, 
    DetailStore, 
    BroadcastScheduler,
    ChunkType,
    DetailChunk,
    ProgressiveRenderer,
};

/// A node in the slow-bleed mesh network
pub struct SlowBleedNode {
    /// Node identity
    pub node_id: u16,
    pub building_id: u16,
    
    /// Live data (always current)
    pub live_objects: FnvIndexMap<u16, ArxObject, 256>,
    
    /// Progressive detail accumulation
    pub detail_store: DetailStore,
    
    /// Broadcasting machinery
    pub broadcast_scheduler: BroadcastScheduler,
    
    /// Statistics
    pub stats: NodeStats,
    
    /// Current timestamp (for embedded, use a counter)
    pub timestamp: u32,
}

/// Node statistics for monitoring
#[derive(Default, Debug)]
pub struct NodeStats {
    pub packets_sent: u64,
    pub packets_received: u64,
    pub live_updates: u64,
    pub detail_chunks: u64,
    pub cache_hits: u64,
    pub bandwidth_used: u64,
    pub bilt_earned: u32,
}

/// Node operating state
#[derive(Debug, PartialEq)]
pub enum NodeState {
    /// Learning about the mesh
    Discovering,
    /// Catching up on critical data
    Synchronizing,
    /// Actively participating
    Contributing,
    /// Reorganizing for efficiency
    Optimizing,
}

impl SlowBleedNode {
    /// Create a new node
    pub fn new(node_id: u16, building_id: u16) -> Self {
        Self {
            node_id,
            building_id,
            live_objects: FnvIndexMap::new(),
            detail_store: DetailStore::new(),
            broadcast_scheduler: BroadcastScheduler::new(),
            stats: NodeStats::default(),
            timestamp: 0,
        }
    }
    
    /// Process an incoming packet
    pub fn process_packet(&mut self, packet: MeshPacket) {
        self.stats.packets_received += 1;
        
        if packet.is_live() {
            self.process_live_packet(packet);
        } else {
            self.process_detail_packet(packet);
        }
    }
    
    /// Process a live update packet
    fn process_live_packet(&mut self, packet: MeshPacket) {
        self.stats.live_updates += 1;
        
        // Extract ArxObject from packet
        let object_id = packet.object_id();
        let object = ArxObject {
            building_id: object_id,
            object_type: packet.packet_type,
            x: u16::from_le_bytes([packet.payload[2], packet.payload[3]]),
            y: u16::from_le_bytes([packet.payload[4], packet.payload[5]]),
            z: u16::from_le_bytes([packet.payload[6], packet.payload[7]]),
            properties: packet.payload[8..12].try_into().unwrap(),
        };
        
        // Update live object store
        let _ = self.live_objects.insert(object_id, object);
        
        // Mark as having basic detail
        let mut level = self.detail_store.get_completeness(object_id);
        level.basic = true;
    }
    
    /// Process a detail chunk packet
    fn process_detail_packet(&mut self, packet: MeshPacket) {
        self.stats.detail_chunks += 1;
        
        if let Some(chunk) = DetailChunk::from_packet(&packet, self.timestamp) {
            // Store the chunk
            if self.detail_store.add_chunk(chunk.clone()).is_ok() {
                // Check if object is now complete enough for CAD rendering
                let completeness = self.detail_store.get_completeness(chunk.object_id);
                if completeness.has_cad_detail() {
                    self.on_object_complete(chunk.object_id);
                }
                
                // Award BILT for contributing to knowledge
                self.stats.bilt_earned += 1;
            }
        }
    }
    
    /// Called when an object reaches CAD-level detail
    fn on_object_complete(&mut self, _object_id: u16) {
        // Award bonus BILT for completing an object
        self.stats.bilt_earned += 100;
        
        // Could trigger special rendering or notifications here
    }
    
    /// Get the next packet to broadcast
    pub fn next_broadcast(&mut self) -> Option<MeshPacket> {
        // 20% chance to send live update, 80% detail
        let send_live = (self.timestamp % 5) == 0;
        
        if send_live {
            self.next_live_broadcast()
        } else {
            self.next_detail_broadcast()
        }
    }
    
    /// Get next live update to broadcast
    fn next_live_broadcast(&mut self) -> Option<MeshPacket> {
        // Round-robin through live objects
        let objects: heapless::Vec<_, 256> = self.live_objects.values().cloned().collect();
        
        if objects.is_empty() {
            return None;
        }
        
        let index = (self.timestamp as usize) % objects.len();
        let object = &objects[index];
        
        self.stats.packets_sent += 1;
        self.stats.bandwidth_used += 13;
        
        Some(MeshPacket::live_update(object))
    }
    
    /// Get next detail chunk to broadcast
    fn next_detail_broadcast(&mut self) -> Option<MeshPacket> {
        if let Some(priority) = self.broadcast_scheduler.next_chunk() {
            // Create detail packet
            // In real implementation, would fetch actual chunk data
            let dummy_data = [0u8; 8];
            
            let packet = MeshPacket::detail_chunk(
                priority.object_id,
                priority.chunk_id,
                priority.chunk_type,
                &dummy_data,
            );
            
            self.stats.packets_sent += 1;
            self.stats.detail_chunks += 1;
            self.stats.bandwidth_used += 13;
            
            Some(packet)
        } else {
            None
        }
    }
    
    /// Advance time (called periodically)
    pub fn tick(&mut self) {
        self.timestamp = self.timestamp.wrapping_add(1);
        
        // Periodic maintenance
        if self.timestamp % 3600 == 0 {  // Every "hour"
            self.perform_maintenance();
        }
    }
    
    /// Perform periodic maintenance
    fn perform_maintenance(&mut self) {
        // Clear old chunks to save memory
        self.detail_store.clear_old_chunks(86400, self.timestamp);  // 24 "hours"
        
        // Re-prioritize nearly complete objects
        let nearly_complete = self.detail_store.get_nearly_complete(0.8);
        for object_id in nearly_complete {
            // Queue missing chunks with high priority
            // In real implementation, would determine what's missing
            self.broadcast_scheduler.queue_chunk(
                object_id,
                0,  // Dummy chunk ID
                ChunkType::MaterialDensity,
            );
        }
    }
    
    /// Get current node state
    pub fn state(&self) -> NodeState {
        match self.stats.packets_received {
            0..=100 => NodeState::Discovering,
            101..=1000 => NodeState::Synchronizing,
            _ => NodeState::Contributing,
        }
    }
    
    /// Get a report of node status
    pub fn status_report(&self) -> String {
        use core::fmt::Write;
        let mut output = heapless::String::<512>::new();
        
        let _ = write!(
            output,
            "Node {:04X} | Building {:04X}\n",
            self.node_id, self.building_id
        );
        let _ = write!(
            output,
            "State: {:?}\n",
            self.state()
        );
        let _ = write!(
            output,
            "Objects: {} live, {} chunks stored\n",
            self.live_objects.len(),
            self.detail_store.storage_used() / 32  // Rough estimate
        );
        let _ = write!(
            output,
            "Traffic: {} sent, {} received\n",
            self.stats.packets_sent,
            self.stats.packets_received
        );
        let _ = write!(
            output,
            "BILT earned: {}\n",
            self.stats.bilt_earned
        );
        
        // Convert heapless String to std String for compatibility
        #[cfg(feature = "std")]
        return output.as_str().to_string();
        
        #[cfg(not(feature = "std"))]
        output
    }
    
    /// Render an object with its current detail level
    pub fn render_object(&self, object_id: u16) -> Option<heapless::String<1024>> {
        let object = self.live_objects.get(&object_id)?;
        let detail_level = self.detail_store.get_completeness(object_id);
        let renderer = ProgressiveRenderer::new();
        
        Some(renderer.render_object(object, &detail_level))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_node_creation() {
        let node = SlowBleedNode::new(0x0001, 0xA001);
        assert_eq!(node.node_id, 0x0001);
        assert_eq!(node.building_id, 0xA001);
        assert_eq!(node.state(), NodeState::Discovering);
    }
    
    #[test]
    fn test_packet_processing() {
        let mut node = SlowBleedNode::new(0x0001, 0xA001);
        
        // Create and process a live packet
        let object = ArxObject::new(0x1234, 0x10, 100, 200, 300);
        let packet = MeshPacket::live_update(&object);
        
        node.process_packet(packet);
        
        assert_eq!(node.stats.packets_received, 1);
        assert_eq!(node.stats.live_updates, 1);
        assert!(node.live_objects.contains_key(&0x1234));
    }
}