//! RF Mesh Networking Module
//! Pure LoRa mesh communication - no internet required

use crate::arxobject::ArxObject;
use crate::packet::MeshPacket;
use std::collections::{HashMap, HashSet, VecDeque};
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};

/// LoRa radio configuration
#[derive(Debug, Clone)]
pub struct LoRaConfig {
    /// Frequency in MHz (915 for US, 868 for EU)
    pub frequency: f32,
    /// Bandwidth in kHz (125, 250, or 500)
    pub bandwidth: u32,
    /// Spreading factor (7-12)
    pub spreading_factor: u8,
    /// Transmit power in dBm (0-20)
    pub tx_power: i8,
    /// Node ID for this device
    pub node_id: u16,
}

impl Default for LoRaConfig {
    fn default() -> Self {
        Self {
            frequency: 915.0,  // US ISM band
            bandwidth: 125,
            spreading_factor: 9,
            tx_power: 20,
            node_id: rand::random(),
        }
    }
}

/// RF Mesh Network Node
pub struct MeshNode {
    config: LoRaConfig,
    /// Routing table for mesh network
    routing_table: HashMap<u16, Route>,
    /// Message cache to prevent loops
    message_cache: MessageCache,
    /// Neighbor nodes discovered
    neighbors: HashSet<u16>,
    /// Pending outgoing packets
    tx_queue: VecDeque<MeshPacket>,
    /// Received packets buffer
    rx_buffer: VecDeque<MeshPacket>,
    /// Node statistics
    stats: NodeStats,
}

#[derive(Debug, Clone)]
struct Route {
    next_hop: u16,
    hop_count: u8,
    last_seen: Instant,
    signal_strength: i8,  // RSSI in dBm
}

struct MessageCache {
    seen_messages: HashMap<MessageId, Instant>,
    max_age: Duration,
}

#[derive(Hash, Eq, PartialEq, Clone, Copy)]
struct MessageId {
    source_node: u16,
    sequence: u16,
}

#[derive(Debug, Default)]
pub struct NodeStats {
    pub packets_sent: u64,
    pub packets_received: u64,
    pub packets_forwarded: u64,
    pub packets_dropped: u64,
    pub neighbor_count: usize,
}

impl MeshNode {
    /// Create new mesh node
    pub fn new(config: LoRaConfig) -> Self {
        Self {
            config,
            routing_table: HashMap::new(),
            message_cache: MessageCache::new(),
            neighbors: HashSet::new(),
            tx_queue: VecDeque::new(),
            rx_buffer: VecDeque::new(),
            stats: NodeStats::default(),
        }
    }
    
    /// Broadcast ArxObject to mesh network
    pub fn broadcast_object(&mut self, obj: &ArxObject) {
        let packet = MeshPacket {
            packet_type: 0x01,  // ArxObject type
            payload: obj.to_bytes()[..12].try_into().unwrap(),
        };
        
        self.broadcast_packet(packet);
    }
    
    /// Send packet to specific node
    pub fn send_to(&mut self, destination: u16, packet: MeshPacket) {
        // Find route to destination
        if let Some(route) = self.routing_table.get(&destination) {
            self.forward_packet(packet, route.next_hop);
        } else {
            // No route - broadcast for discovery
            self.broadcast_packet(packet);
        }
    }
    
    /// Broadcast packet to all neighbors
    pub fn broadcast_packet(&mut self, packet: MeshPacket) {
        self.tx_queue.push_back(packet);
        self.stats.packets_sent += 1;
        
        // In real implementation, this would trigger LoRa transmission
        self.transmit_rf();
    }
    
    /// Process received packet
    pub fn receive_packet(&mut self, packet: MeshPacket, rssi: i8, from_node: u16) {
        self.stats.packets_received += 1;
        
        // Update neighbor info
        self.neighbors.insert(from_node);
        self.update_route(from_node, from_node, 1, rssi);
        
        // Check if we've seen this packet before
        let msg_id = self.extract_message_id(&packet);
        if self.message_cache.has_seen(msg_id) {
            self.stats.packets_dropped += 1;
            return;
        }
        
        self.message_cache.mark_seen(msg_id);
        
        // Process or forward packet
        if self.is_for_us(&packet) {
            self.rx_buffer.push_back(packet);
        } else {
            self.forward_packet(packet, from_node);
            self.stats.packets_forwarded += 1;
        }
    }
    
    /// Forward packet to next hop
    fn forward_packet(&mut self, packet: MeshPacket, exclude_node: u16) {
        // Epidemic routing - send to all neighbors except source
        for &neighbor in &self.neighbors {
            if neighbor != exclude_node {
                self.tx_queue.push_back(packet);
            }
        }
    }
    
    /// Update routing table
    fn update_route(&mut self, destination: u16, next_hop: u16, hop_count: u8, rssi: i8) {
        let route = Route {
            next_hop,
            hop_count,
            last_seen: Instant::now(),
            signal_strength: rssi,
        };
        
        // Update if better route or fresher
        match self.routing_table.get(&destination) {
            Some(existing) if existing.hop_count <= hop_count => {
                if existing.last_seen.elapsed() > Duration::from_secs(60) {
                    self.routing_table.insert(destination, route);
                }
            }
            _ => {
                self.routing_table.insert(destination, route);
            }
        }
    }
    
    /// Check if packet is for this node
    fn is_for_us(&self, _packet: &MeshPacket) -> bool {
        // In real implementation, check destination field
        true  // For now, accept all packets
    }
    
    /// Extract message ID for deduplication
    fn extract_message_id(&self, _packet: &MeshPacket) -> MessageId {
        MessageId {
            source_node: rand::random(),  // Would extract from packet
            sequence: rand::random(),
        }
    }
    
    /// Simulate RF transmission
    fn transmit_rf(&self) {
        // In real implementation, this would:
        // 1. Configure LoRa radio with self.config
        // 2. Transmit packets from tx_queue
        // 3. Handle collision avoidance
    }
    
    /// Get next received packet
    pub fn get_received_packet(&mut self) -> Option<MeshPacket> {
        self.rx_buffer.pop_front()
    }
    
    /// Get network statistics
    pub fn get_stats(&self) -> &NodeStats {
        &self.stats
    }
}

impl MessageCache {
    fn new() -> Self {
        Self {
            seen_messages: HashMap::new(),
            max_age: Duration::from_secs(300),  // 5 minutes
        }
    }
    
    fn has_seen(&mut self, id: MessageId) -> bool {
        // Clean old entries
        self.clean_old_entries();
        
        self.seen_messages.contains_key(&id)
    }
    
    fn mark_seen(&mut self, id: MessageId) {
        self.seen_messages.insert(id, Instant::now());
    }
    
    fn clean_old_entries(&mut self) {
        let now = Instant::now();
        self.seen_messages.retain(|_, time| {
            now.duration_since(*time) < self.max_age
        });
    }
}

/// RF Update Distribution System
pub struct RFUpdateSystem {
    /// Current firmware version
    current_version: Version,
    /// Update chunks received
    update_chunks: HashMap<u16, Vec<u8>>,
    /// Total chunks expected
    total_chunks: Option<u16>,
    /// Update signature for verification
    update_signature: Option<[u8; 64]>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Version {
    pub major: u8,
    pub minor: u8,
    pub patch: u8,
}

impl RFUpdateSystem {
    pub fn new(current_version: Version) -> Self {
        Self {
            current_version,
            update_chunks: HashMap::new(),
            total_chunks: None,
            update_signature: None,
        }
    }
    
    /// Process update announcement
    pub fn process_announcement(&mut self, version: Version, total_chunks: u16, signature: [u8; 64]) {
        if version > self.current_version {
            self.total_chunks = Some(total_chunks);
            self.update_signature = Some(signature);
            self.update_chunks.clear();
        }
    }
    
    /// Receive update chunk
    pub fn receive_chunk(&mut self, chunk_index: u16, data: Vec<u8>) -> bool {
        self.update_chunks.insert(chunk_index, data);
        
        // Check if complete
        if let Some(total) = self.total_chunks {
            self.update_chunks.len() == total as usize
        } else {
            false
        }
    }
    
    /// Verify and install update
    pub fn install_update(&self) -> Result<(), &'static str> {
        // Verify signature
        if !self.verify_signature() {
            return Err("Invalid update signature");
        }
        
        // Reassemble firmware
        let _firmware = self.reassemble_firmware()?;
        
        // In real implementation:
        // 1. Write to backup partition
        // 2. Verify checksum
        // 3. Set boot flag
        // 4. Reboot
        
        Ok(())
    }
    
    fn verify_signature(&self) -> bool {
        // Ed25519 signature verification
        // Would use actual crypto library
        true  // Placeholder
    }
    
    fn reassemble_firmware(&self) -> Result<Vec<u8>, &'static str> {
        let total = self.total_chunks.ok_or("No update in progress")?;
        let mut firmware = Vec::new();
        
        for i in 0..total {
            let chunk = self.update_chunks.get(&i)
                .ok_or("Missing chunk")?;
            firmware.extend_from_slice(chunk);
        }
        
        Ok(firmware)
    }
}

impl PartialOrd for Version {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Version {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        match self.major.cmp(&other.major) {
            std::cmp::Ordering::Equal => {
                match self.minor.cmp(&other.minor) {
                    std::cmp::Ordering::Equal => self.patch.cmp(&other.patch),
                    other => other,
                }
            }
            other => other,
        }
    }
}

impl PartialEq for Version {
    fn eq(&self, other: &Self) -> bool {
        self.major == other.major && 
        self.minor == other.minor && 
        self.patch == other.patch
    }
}

impl Eq for Version {}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_mesh_routing() {
        let config = LoRaConfig::default();
        let mut node = MeshNode::new(config);
        
        // Simulate receiving packet from neighbor
        let packet = MeshPacket {
            packet_type: 0x01,
            payload: [0; 12],
        };
        
        node.receive_packet(packet, -70, 0x1234);
        
        assert_eq!(node.neighbors.len(), 1);
        assert!(node.neighbors.contains(&0x1234));
        assert_eq!(node.stats.packets_received, 1);
    }
    
    #[test]
    fn test_version_comparison() {
        let v1 = Version { major: 1, minor: 0, patch: 0 };
        let v2 = Version { major: 1, minor: 0, patch: 1 };
        let v3 = Version { major: 2, minor: 0, patch: 0 };
        
        assert!(v2 > v1);
        assert!(v3 > v2);
        assert!(v3 > v1);
    }
}