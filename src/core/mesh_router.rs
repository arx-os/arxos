//! Mesh Router - Lightweight Packet Routing for Building Networks
//! 
//! Routes 13-byte ArxObjects through LoRa mesh networks with minimal overhead.
//! Designed for low-power, low-bandwidth environments (250kbps LoRa).

use crate::arxobject::ArxObject;
use crate::packet::MeshPacket;
use std::collections::{HashMap, HashSet, VecDeque};
use std::time::{Duration, Instant};

/// Maximum number of hops a packet can take
const MAX_HOPS: u8 = 10;

/// TTL for routing table entries (5 minutes)
const ROUTE_TTL: Duration = Duration::from_secs(300);

/// Maximum packets in transit queue
const MAX_TRANSIT_QUEUE: usize = 1000;

/// Routing table entry
#[derive(Debug, Clone)]
struct Route {
    next_hop: u16,      // Node ID to forward to
    hop_count: u8,      // Number of hops to destination
    last_seen: Instant, // When this route was last updated
    metric: u16,        // Route quality metric (lower is better)
}

/// Packet in transit
#[derive(Debug, Clone)]
struct TransitPacket {
    packet: MeshPacket,
    destination: u16,
    received_at: Instant,
    retry_count: u8,
}

/// Mesh router for ArxObject flow orchestration
pub struct MeshRouter {
    node_id: u16,
    building_id: u16,
    
    // Routing table: destination -> route
    routes: HashMap<u16, Route>,
    
    // Neighbors directly reachable
    neighbors: HashSet<u16>,
    
    // Packets waiting to be forwarded
    transit_queue: VecDeque<TransitPacket>,
    
    // Recently seen packet IDs (prevent loops)
    seen_packets: HashMap<u64, Instant>,
    
    // Metrics
    packets_routed: usize,
    packets_dropped: usize,
    route_updates: usize,
}

impl MeshRouter {
    /// Create a new mesh router for a building node
    pub fn new(node_id: u16, building_id: u16) -> Self {
        Self {
            node_id,
            building_id,
            routes: HashMap::new(),
            neighbors: HashSet::new(),
            transit_queue: VecDeque::new(),
            seen_packets: HashMap::new(),
            packets_routed: 0,
            packets_dropped: 0,
            route_updates: 0,
        }
    }
    
    /// Process incoming ArxObject for routing
    pub fn route_arxobject(&mut self, obj: &ArxObject, destination: u16) -> Option<u16> {
        // Check if destination is a neighbor
        if self.neighbors.contains(&destination) {
            self.packets_routed += 1;
            return Some(destination);
        }
        
        // Look up route
        if let Some(route) = self.routes.get(&destination) {
            if route.last_seen.elapsed() < ROUTE_TTL {
                self.packets_routed += 1;
                return Some(route.next_hop);
            }
        }
        
        // No route found - flood to all neighbors
        self.broadcast_to_neighbors(obj)
    }
    
    /// Process incoming mesh packet
    pub fn process_packet(&mut self, packet: &MeshPacket, from_node: u16) -> RouterAction {
        // Update neighbor list
        self.neighbors.insert(from_node);
        
        // Check for duplicate
        let packet_id = self.packet_id(packet);
        if let Some(seen_time) = self.seen_packets.get(&packet_id) {
            if seen_time.elapsed() < Duration::from_secs(60) {
                return RouterAction::Drop; // Already processed
            }
        }
        self.seen_packets.insert(packet_id, Instant::now());
        
        // Extract destination from packet
        let destination = self.extract_destination(packet);
        
        // Is this packet for us?
        if destination == self.node_id {
            return RouterAction::Deliver;
        }
        
        // Should we forward?
        if packet.hop_count() >= MAX_HOPS {
            self.packets_dropped += 1;
            return RouterAction::Drop;
        }
        
        // Find next hop
        if let Some(next_hop) = self.find_next_hop(destination) {
            RouterAction::Forward(next_hop)
        } else {
            // Queue for later delivery
            if self.transit_queue.len() < MAX_TRANSIT_QUEUE {
                self.transit_queue.push_back(TransitPacket {
                    packet: packet.clone(),
                    destination,
                    received_at: Instant::now(),
                    retry_count: 0,
                });
                RouterAction::Queue
            } else {
                self.packets_dropped += 1;
                RouterAction::Drop
            }
        }
    }
    
    /// Update routing table from neighbor advertisement
    pub fn update_route(&mut self, destination: u16, next_hop: u16, hop_count: u8, metric: u16) {
        let should_update = if let Some(existing) = self.routes.get(&destination) {
            // Update if better metric or newer
            metric < existing.metric || 
            existing.last_seen.elapsed() > Duration::from_secs(30)
        } else {
            true
        };
        
        if should_update {
            self.routes.insert(destination, Route {
                next_hop,
                hop_count: hop_count + 1,
                last_seen: Instant::now(),
                metric: metric + 1,
            });
            self.route_updates += 1;
        }
    }
    
    /// Process queued packets
    pub fn process_queue(&mut self) -> Vec<(MeshPacket, u16)> {
        let mut to_send = Vec::new();
        let mut requeue = VecDeque::new();
        
        while let Some(mut transit) = self.transit_queue.pop_front() {
            if transit.received_at.elapsed() > Duration::from_secs(10) {
                self.packets_dropped += 1;
                continue; // Too old, drop it
            }
            
            if let Some(next_hop) = self.find_next_hop(transit.destination) {
                to_send.push((transit.packet, next_hop));
                self.packets_routed += 1;
            } else {
                transit.retry_count += 1;
                if transit.retry_count < 3 {
                    requeue.push_back(transit);
                } else {
                    self.packets_dropped += 1;
                }
            }
        }
        
        self.transit_queue = requeue;
        to_send
    }
    
    /// Clean up old routing entries and seen packets
    pub fn cleanup(&mut self) {
        let now = Instant::now();
        
        // Remove stale routes
        self.routes.retain(|_, route| {
            route.last_seen.elapsed() < ROUTE_TTL
        });
        
        // Remove old seen packets
        self.seen_packets.retain(|_, time| {
            now.duration_since(*time) < Duration::from_secs(300)
        });
    }
    
    /// Generate routing advertisement for neighbors
    pub fn generate_advertisement(&self) -> RoutingAdvertisement {
        let routes: Vec<RouteEntry> = self.routes
            .iter()
            .filter(|(_, route)| route.hop_count < MAX_HOPS - 1)
            .map(|(&dest, route)| RouteEntry {
                destination: dest,
                hop_count: route.hop_count,
                metric: route.metric,
            })
            .collect();
            
        RoutingAdvertisement {
            node_id: self.node_id,
            building_id: self.building_id,
            routes,
            timestamp: Instant::now(),
        }
    }
    
    /// Get router statistics
    pub fn stats(&self) -> RouterStats {
        RouterStats {
            node_id: self.node_id,
            routes_known: self.routes.len(),
            neighbors_count: self.neighbors.len(),
            queue_size: self.transit_queue.len(),
            packets_routed: self.packets_routed,
            packets_dropped: self.packets_dropped,
            route_updates: self.route_updates,
        }
    }
    
    // Helper methods
    
    fn broadcast_to_neighbors(&self, _obj: &ArxObject) -> Option<u16> {
        // Return special broadcast address
        Some(0xFFFF)
    }
    
    fn packet_id(&self, packet: &MeshPacket) -> u64 {
        // Generate unique ID from packet contents
        let mut id = 0u64;
        id |= (packet.header[0] as u64) << 56;
        id |= (packet.header[1] as u64) << 48;
        id |= (packet.payload[0] as u64) << 40;
        id |= (packet.payload[1] as u64) << 32;
        id |= (self.node_id as u64) << 16;
        id
    }
    
    fn extract_destination(&self, packet: &MeshPacket) -> u16 {
        // Destination in header bytes 2-3
        ((packet.header[2] as u16) << 8) | (packet.header[3] as u16)
    }
    
    fn find_next_hop(&self, destination: u16) -> Option<u16> {
        // Direct neighbor?
        if self.neighbors.contains(&destination) {
            return Some(destination);
        }
        
        // Routing table lookup
        self.routes
            .get(&destination)
            .filter(|route| route.last_seen.elapsed() < ROUTE_TTL)
            .map(|route| route.next_hop)
    }
}

/// Action to take for a packet
#[derive(Debug, PartialEq)]
pub enum RouterAction {
    Deliver,       // Packet is for this node
    Forward(u16),  // Forward to specified node
    Queue,         // Queued for later delivery
    Drop,          // Drop the packet
}

/// Routing advertisement message
#[derive(Debug, Clone)]
pub struct RoutingAdvertisement {
    pub node_id: u16,
    pub building_id: u16,
    pub routes: Vec<RouteEntry>,
    pub timestamp: Instant,
}

/// Single route entry in advertisement
#[derive(Debug, Clone)]
pub struct RouteEntry {
    pub destination: u16,
    pub hop_count: u8,
    pub metric: u16,
}

/// Router statistics
#[derive(Debug, Clone)]
pub struct RouterStats {
    pub node_id: u16,
    pub routes_known: usize,
    pub neighbors_count: usize,
    pub queue_size: usize,
    pub packets_routed: usize,
    pub packets_dropped: usize,
    pub route_updates: usize,
}

/// Mesh topology visualization for terminal
pub struct MeshTopology {
    nodes: HashMap<u16, NodeInfo>,
    links: Vec<Link>,
}

#[derive(Debug, Clone)]
struct NodeInfo {
    id: u16,
    building_id: u16,
    position: (f32, f32), // For visualization
    last_seen: Instant,
}

#[derive(Debug, Clone)]
struct Link {
    from: u16,
    to: u16,
    quality: f32, // 0.0 to 1.0
}

impl MeshTopology {
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            links: Vec::new(),
        }
    }
    
    /// Update topology from router advertisement
    pub fn update_from_advertisement(&mut self, ad: &RoutingAdvertisement) {
        // Add/update node
        self.nodes.insert(ad.node_id, NodeInfo {
            id: ad.node_id,
            building_id: ad.building_id,
            position: self.calculate_position(ad.node_id),
            last_seen: Instant::now(),
        });
        
        // Update links
        for route in &ad.routes {
            self.update_link(ad.node_id, route.destination, route.metric);
        }
    }
    
    /// Render topology as ASCII art
    pub fn render_ascii(&self) -> String {
        let mut output = String::new();
        output.push_str("=== MESH TOPOLOGY ===\n\n");
        
        // List nodes
        output.push_str("Nodes:\n");
        for (id, info) in &self.nodes {
            let age = info.last_seen.elapsed().as_secs();
            output.push_str(&format!("  [{:04X}] Building {} ({}s ago)\n", 
                id, info.building_id, age));
        }
        
        output.push_str("\nLinks:\n");
        for link in &self.links {
            let quality_bar = self.quality_bar(link.quality);
            output.push_str(&format!("  {:04X} <{}> {:04X}\n", 
                link.from, quality_bar, link.to));
        }
        
        output
    }
    
    fn calculate_position(&self, node_id: u16) -> (f32, f32) {
        // Simple positioning based on ID
        let angle = (node_id as f32) * 0.1;
        (angle.cos() * 10.0, angle.sin() * 10.0)
    }
    
    fn update_link(&mut self, from: u16, to: u16, metric: u16) {
        let quality = 1.0 / (1.0 + metric as f32 / 100.0);
        
        if let Some(link) = self.links.iter_mut().find(|l| l.from == from && l.to == to) {
            link.quality = quality;
        } else {
            self.links.push(Link { from, to, quality });
        }
    }
    
    fn quality_bar(&self, quality: f32) -> String {
        let bars = (quality * 5.0) as usize;
        let mut bar = String::new();
        for _ in 0..bars {
            bar.push('=');
        }
        for _ in bars..5 {
            bar.push('-');
        }
        bar
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_mesh_router_direct_neighbor() {
        let mut router = MeshRouter::new(1, 100);
        router.neighbors.insert(2);
        
        let obj = ArxObject::new(100, 0x15, 1000, 2000, 3000);
        let next_hop = router.route_arxobject(&obj, 2);
        
        assert_eq!(next_hop, Some(2));
        assert_eq!(router.packets_routed, 1);
    }
    
    #[test]
    fn test_mesh_router_indirect_route() {
        let mut router = MeshRouter::new(1, 100);
        router.neighbors.insert(2);
        router.update_route(3, 2, 1, 10);
        
        let obj = ArxObject::new(100, 0x15, 1000, 2000, 3000);
        let next_hop = router.route_arxobject(&obj, 3);
        
        assert_eq!(next_hop, Some(2));
        assert_eq!(router.packets_routed, 1);
    }
    
    #[test]
    fn test_packet_processing() {
        let mut router = MeshRouter::new(1, 100);
        router.neighbors.insert(2);
        
        let mut packet = MeshPacket::new();
        packet.header[2] = 0x00;
        packet.header[3] = 0x03; // Destination: 3
        
        let action = router.process_packet(&packet, 2);
        assert_eq!(action, RouterAction::Queue);
        
        // Now add route and process queue
        router.update_route(3, 2, 1, 10);
        let to_send = router.process_queue();
        
        assert_eq!(to_send.len(), 1);
        assert_eq!(to_send[0].1, 2);
    }
    
    #[test]
    fn test_routing_advertisement() {
        let mut router = MeshRouter::new(1, 100);
        router.update_route(2, 3, 1, 10);
        router.update_route(4, 3, 2, 20);
        
        let ad = router.generate_advertisement();
        
        assert_eq!(ad.node_id, 1);
        assert_eq!(ad.building_id, 100);
        assert_eq!(ad.routes.len(), 2);
    }
    
    #[test]
    fn test_topology_visualization() {
        let mut topology = MeshTopology::new();
        
        let ad = RoutingAdvertisement {
            node_id: 1,
            building_id: 100,
            routes: vec![
                RouteEntry { destination: 2, hop_count: 1, metric: 10 },
                RouteEntry { destination: 3, hop_count: 2, metric: 25 },
            ],
            timestamp: Instant::now(),
        };
        
        topology.update_from_advertisement(&ad);
        let ascii = topology.render_ascii();
        
        assert!(ascii.contains("MESH TOPOLOGY"));
        assert!(ascii.contains("[0001]"));
    }
}