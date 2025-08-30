//! Mesh network routing logic

use arxos_core::{ArxObject, MeshPacket};
use embassy_sync::{blocking_mutex::raw::CriticalSectionRawMutex, channel::Channel};
use embassy_time::{Duration, Timer};
use esp_println::println;
use heapless::{FnvIndexMap, Vec};

use crate::lora_driver::{LoRaDriver, LoRaError};

/// Maximum number of neighbors to track
const MAX_NEIGHBORS: usize = 32;
/// Maximum routing table entries
const MAX_ROUTES: usize = 64;
/// TX queue size
const TX_QUEUE_SIZE: usize = 16;

/// Mesh router handles packet routing and neighbor management
pub struct MeshRouter {
    node_id: u16,
    lora: LoRaDriver,
    neighbors: FnvIndexMap<u16, NeighborInfo, MAX_NEIGHBORS>,
    routing_table: FnvIndexMap<u16, Route, MAX_ROUTES>,
    tx_queue: Channel<CriticalSectionRawMutex, MeshPacket, TX_QUEUE_SIZE>,
    seen_packets: Vec<PacketId, 256>,  // Deduplication cache
    stats: RouterStats,
}

/// Information about a neighbor node
#[derive(Debug, Clone)]
struct NeighborInfo {
    node_id: u16,
    last_seen: u64,  // Timestamp in seconds
    rssi: i16,       // Signal strength in dBm
    packet_count: u32,
}

/// Routing table entry
#[derive(Debug, Clone)]
struct Route {
    destination: u16,
    next_hop: u16,
    hop_count: u8,
    last_updated: u64,
}

/// Packet ID for deduplication
#[derive(Debug, Clone, Copy, PartialEq)]
struct PacketId {
    source: u16,
    sequence: u16,
}

/// Router statistics
#[derive(Debug, Default)]
struct RouterStats {
    packets_received: u32,
    packets_transmitted: u32,
    packets_routed: u32,
    packets_dropped: u32,
}

impl MeshRouter {
    /// Create new mesh router
    pub fn new(node_id: u16, lora: LoRaDriver) -> Self {
        Self {
            node_id,
            lora,
            neighbors: FnvIndexMap::new(),
            routing_table: FnvIndexMap::new(),
            tx_queue: Channel::new(),
            seen_packets: Vec::new(),
            stats: RouterStats::default(),
        }
    }
    
    /// Receive packet from mesh
    pub async fn receive_packet(&mut self) -> Result<MeshPacket, LoRaError> {
        // Wait for packet with 1 second timeout
        let data = self.lora.receive(1000).await?;
        
        // Deserialize packet
        let packet: MeshPacket = postcard::from_bytes(&data)
            .map_err(|_| LoRaError::CrcError)?;
        
        self.stats.packets_received += 1;
        
        // Update neighbor info
        if let Ok(rssi) = self.lora.get_rssi().await {
            self.update_neighbor(packet.source_id, rssi);
        }
        
        Ok(packet)
    }
    
    /// Process received packet
    pub async fn process_packet(&mut self, packet: MeshPacket) {
        // Check for duplicate
        let packet_id = PacketId {
            source: packet.source_id,
            sequence: packet.sequence,
        };
        
        if self.seen_packets.contains(&packet_id) {
            println!("Duplicate packet dropped");
            self.stats.packets_dropped += 1;
            return;
        }
        
        // Add to seen packets (with size limit)
        if self.seen_packets.len() >= 250 {
            self.seen_packets.remove(0);  // Remove oldest
        }
        let _ = self.seen_packets.push(packet_id);
        
        // Check if packet is for us
        if packet.destination_id == self.node_id || packet.destination_id == 0xFFFF {
            self.handle_packet(packet).await;
        } else {
            // Route to destination
            self.route_packet(packet).await;
        }
    }
    
    /// Handle packet addressed to us
    async fn handle_packet(&mut self, packet: MeshPacket) {
        println!("Packet for us from 0x{:04X}", packet.source_id);
        
        match packet.packet_type {
            0x01 => {
                // ArxObject data
                if packet.payload.len() >= 13 {
                    let mut bytes = [0u8; 13];
                    bytes.copy_from_slice(&packet.payload[..13]);
                    let obj = ArxObject::from_bytes(&bytes);
                    println!("Received ArxObject type: 0x{:02X}", obj.object_type);
                }
            }
            0x02 => {
                // Neighbor discovery
                println!("Neighbor discovery from 0x{:04X}", packet.source_id);
                // Send discovery response
                let response = MeshPacket {
                    source_id: self.node_id,
                    destination_id: packet.source_id,
                    sequence: self.next_sequence(),
                    hop_count: 0,
                    packet_type: 0x03,  // Discovery response
                    payload: Vec::new(),
                };
                let _ = self.tx_queue.send(response).await;
            }
            0x03 => {
                // Discovery response
                println!("Discovery response from 0x{:04X}", packet.source_id);
            }
            _ => {
                println!("Unknown packet type: 0x{:02X}", packet.packet_type);
            }
        }
    }
    
    /// Route packet to next hop
    async fn route_packet(&mut self, mut packet: MeshPacket) {
        // Increment hop count
        packet.hop_count += 1;
        
        // Check hop limit
        if packet.hop_count > 15 {
            println!("Packet exceeded hop limit");
            self.stats.packets_dropped += 1;
            return;
        }
        
        // Find route
        if let Some(route) = self.routing_table.get(&packet.destination_id) {
            println!("Routing packet to 0x{:04X} via 0x{:04X}", 
                packet.destination_id, route.next_hop);
            
            // Queue for transmission
            let _ = self.tx_queue.send(packet).await;
            self.stats.packets_routed += 1;
        } else {
            // No route - broadcast (flooding)
            println!("No route to 0x{:04X}, broadcasting", packet.destination_id);
            packet.destination_id = 0xFFFF;  // Broadcast address
            let _ = self.tx_queue.send(packet).await;
        }
    }
    
    /// Transmit packet
    pub async fn transmit_packet(&mut self, packet: MeshPacket) -> Result<(), LoRaError> {
        // Serialize packet
        let data = postcard::to_vec::<_, 256>(&packet)
            .map_err(|_| LoRaError::BufferTooSmall)?;
        
        // Transmit via LoRa
        self.lora.transmit(&data).await?;
        self.stats.packets_transmitted += 1;
        
        Ok(())
    }
    
    /// Get next packet from TX queue
    pub async fn get_next_tx_packet(&mut self) -> Option<MeshPacket> {
        self.tx_queue.try_receive().ok()
    }
    
    /// Update neighbor information
    fn update_neighbor(&mut self, node_id: u16, rssi: i16) {
        let now = self.current_time();
        
        if let Some(neighbor) = self.neighbors.get_mut(&node_id) {
            neighbor.last_seen = now;
            neighbor.rssi = rssi;
            neighbor.packet_count += 1;
        } else {
            // Add new neighbor
            let neighbor = NeighborInfo {
                node_id,
                last_seen: now,
                rssi,
                packet_count: 1,
            };
            let _ = self.neighbors.insert(node_id, neighbor);
            println!("New neighbor discovered: 0x{:04X} (RSSI: {} dBm)", node_id, rssi);
        }
        
        // Update routing table
        self.update_route(node_id, node_id, 1);
    }
    
    /// Update routing table
    fn update_route(&mut self, destination: u16, next_hop: u16, hop_count: u8) {
        let now = self.current_time();
        
        if let Some(route) = self.routing_table.get_mut(&destination) {
            // Update if better route
            if hop_count < route.hop_count {
                route.next_hop = next_hop;
                route.hop_count = hop_count;
                route.last_updated = now;
            }
        } else {
            // Add new route
            let route = Route {
                destination,
                next_hop,
                hop_count,
                last_updated: now,
            };
            let _ = self.routing_table.insert(destination, route);
        }
    }
    
    /// Check if mesh is healthy
    pub async fn is_healthy(&self) -> bool {
        // Check if we have neighbors
        !self.neighbors.is_empty()
    }
    
    /// Get next sequence number
    fn next_sequence(&self) -> u16 {
        // TODO: Implement proper sequence tracking
        (self.stats.packets_transmitted & 0xFFFF) as u16
    }
    
    /// Get current time in seconds
    fn current_time(&self) -> u64 {
        // TODO: Implement proper time tracking
        0
    }
    
    /// Clone for sharing between tasks
    pub fn clone(&self) -> Self {
        // TODO: Implement proper sharing mechanism
        // This is a simplified version
        panic!("Clone not implemented - use Arc<Mutex<>> for sharing")
    }
}