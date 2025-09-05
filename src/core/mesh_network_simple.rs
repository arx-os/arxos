//! Simple Mesh Network for ArxObject Distribution
//! 
//! Provides peer-to-peer networking for building-wide intelligence

use crate::arxobject_simple::ArxObject;
use crate::file_storage::MemoryDatabase;
use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use serde::{Serialize, Deserialize};
use std::net::SocketAddr;

/// Node ID in the mesh network
pub type NodeId = u16;

/// Mesh network node configuration
#[derive(Clone)]
pub struct MeshConfig {
    pub node_id: NodeId,
    pub building_id: u16,
    pub listen_port: u16,
    pub broadcast_interval: Duration,
    pub sync_interval: Duration,
    pub max_peers: usize,
    pub database_path: String,
}

impl Default for MeshConfig {
    fn default() -> Self {
        Self {
            node_id: rand::random(),
            building_id: 0x0001,
            listen_port: 8080,
            broadcast_interval: Duration::from_secs(30),
            sync_interval: Duration::from_secs(60),
            max_peers: 10,
            database_path: "mesh_node.db".to_string(),
        }
    }
}

/// Message types in the mesh network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MeshMessage {
    /// Announce node presence
    Hello {
        node_id: NodeId,
        building_id: u16,
        capabilities: NodeCapabilities,
    },
    
    /// Share ArxObjects
    ObjectBroadcast {
        objects: Vec<ArxObject>,
        timestamp: u64,
    },
    
    /// Request objects in area
    SpatialQuery {
        query_id: u64,
        center: (f32, f32, f32),
        radius: f32,
    },
    
    /// Response to spatial query
    QueryResponse {
        query_id: u64,
        objects: Vec<ArxObject>,
    },
    
    /// Sync request for updates since timestamp
    SyncRequest {
        since_timestamp: u64,
        building_id: u16,
    },
    
    /// Heartbeat/keepalive
    Ping {
        node_id: NodeId,
        load: f32,
    },
    
    /// Response to ping
    Pong {
        node_id: NodeId,
        object_count: usize,
    },
}

/// Node capabilities and resources
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeCapabilities {
    pub storage_mb: u32,
    pub object_capacity: u32,
    pub has_database: bool,
    pub supports_queries: bool,
    pub battery_powered: bool,
}

/// Peer node information
#[derive(Debug, Clone)]
pub struct PeerInfo {
    pub node_id: NodeId,
    pub address: SocketAddr,
    pub last_seen: Instant,
    pub capabilities: NodeCapabilities,
    pub latency_ms: Option<u32>,
    pub object_count: usize,
}

/// Mesh network node
pub struct MeshNode {
    config: MeshConfig,
    peers: Arc<Mutex<HashMap<NodeId, PeerInfo>>>,
    database: Arc<Mutex<MemoryDatabase>>,
    message_queue: Arc<Mutex<VecDeque<(NodeId, MeshMessage)>>>,
    seen_objects: Arc<Mutex<HashSet<u64>>>, // Hash of seen objects to avoid duplicates
    stats: Arc<Mutex<NodeStats>>,
}

/// Node statistics
#[derive(Debug, Default, Clone)]
pub struct NodeStats {
    pub messages_sent: u64,
    pub messages_received: u64,
    pub objects_shared: u64,
    pub objects_received: u64,
    pub queries_handled: u64,
    pub sync_operations: u64,
    pub active_peers: usize,
}

impl MeshNode {
    /// Create new mesh node
    pub fn new(config: MeshConfig) -> Result<Self, Box<dyn std::error::Error>> {
        let database = MemoryDatabase::new();
        
        Ok(Self {
            config,
            peers: Arc::new(Mutex::new(HashMap::new())),
            database: Arc::new(Mutex::new(database)),
            message_queue: Arc::new(Mutex::new(VecDeque::new())),
            seen_objects: Arc::new(Mutex::new(HashSet::new())),
            stats: Arc::new(Mutex::new(NodeStats::default())),
        })
    }
    
    /// Start the mesh node
    pub async fn start(&self) -> Result<(), Box<dyn std::error::Error>> {
        println!("Starting mesh node {} on port {}", self.config.node_id, self.config.listen_port);
        
        // Start network listener
        let listener_handle = self.start_listener();
        
        // Start broadcast timer
        let broadcast_handle = self.start_broadcaster();
        
        // Start peer discovery
        let discovery_handle = self.start_discovery();
        
        // Start message processor
        let processor_handle = self.start_processor();
        
        // Wait for all tasks
        let _ = tokio::join!(
            listener_handle,
            broadcast_handle,
            discovery_handle,
            processor_handle
        );
        
        Ok(())
    }
    
    /// Start network listener
    async fn start_listener(&self) -> tokio::task::JoinHandle<()> {
        let config = self.config.clone();
        let _peers = self.peers.clone();
        let _queue = self.message_queue.clone();
        let _stats = self.stats.clone();
        
        tokio::spawn(async move {
            // In production, this would use TCP or UDP sockets
            // For now, simulating network communication
            println!("Listener started on port {}", config.listen_port);
            
            loop {
                // Simulate receiving messages
                tokio::time::sleep(Duration::from_secs(1)).await;
                
                // Check for incoming messages (would be from network)
                // Process and add to queue
            }
        })
    }
    
    /// Start periodic broadcaster
    async fn start_broadcaster(&self) -> tokio::task::JoinHandle<()> {
        let config = self.config.clone();
        let database = self.database.clone();
        let peers = self.peers.clone();
        let stats = self.stats.clone();
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(config.broadcast_interval);
            
            loop {
                interval.tick().await;
                
                // Get recent objects from database
                let db = database.lock().unwrap();
                if let Ok(objects) = db.get_building_objects(config.building_id) {
                    // Take last 10 objects as sample
                    let sample: Vec<ArxObject> = objects.into_iter().take(10).collect();
                    
                    if !sample.is_empty() {
                        let _msg = MeshMessage::ObjectBroadcast {
                            objects: sample.clone(),
                            timestamp: std::time::SystemTime::now()
                                .duration_since(std::time::UNIX_EPOCH)
                                .unwrap()
                                .as_secs(),
                        };
                        
                        // Broadcast to all peers
                        let peers = peers.lock().unwrap();
                        for peer in peers.values() {
                            // In production: send via network
                            println!("Broadcasting {} objects to node {}", 
                                    sample.len(), peer.node_id);
                        }
                        
                        let mut stats = stats.lock().unwrap();
                        stats.objects_shared += sample.len() as u64;
                        stats.messages_sent += peers.len() as u64;
                    }
                }
            }
        })
    }
    
    /// Start peer discovery
    async fn start_discovery(&self) -> tokio::task::JoinHandle<()> {
        let config = self.config.clone();
        let peers = self.peers.clone();
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(10));
            
            loop {
                interval.tick().await;
                
                // Send hello to discover peers
                let _hello = MeshMessage::Hello {
                    node_id: config.node_id,
                    building_id: config.building_id,
                    capabilities: NodeCapabilities {
                        storage_mb: 100,
                        object_capacity: 10000,
                        has_database: true,
                        supports_queries: true,
                        battery_powered: false,
                    },
                };
                
                // In production: broadcast hello via UDP multicast
                println!("Discovering peers for node {}", config.node_id);
                
                // Clean up stale peers
                let mut peers = peers.lock().unwrap();
                let now = Instant::now();
                peers.retain(|_, peer| {
                    now.duration_since(peer.last_seen) < Duration::from_secs(120)
                });
            }
        })
    }
    
    /// Start message processor
    async fn start_processor(&self) -> tokio::task::JoinHandle<()> {
        let database = self.database.clone();
        let queue = self.message_queue.clone();
        let seen = self.seen_objects.clone();
        let stats = self.stats.clone();
        let config = self.config.clone();
        
        tokio::spawn(async move {
            loop {
                // Process message queue
                let message = {
                    let mut queue = queue.lock().unwrap();
                    queue.pop_front()
                };
                
                if let Some((sender_id, msg)) = message {
                    match msg {
                        MeshMessage::ObjectBroadcast { objects, timestamp: _ } => {
                            // Store new objects
                            let mut new_count = 0;
                            let mut db = database.lock().unwrap();
                            
                            for obj in objects {
                                // Create hash for deduplication
                                let hash = Self::hash_object(&obj);
                                
                                let mut seen = seen.lock().unwrap();
                                if !seen.contains(&hash) {
                                    seen.insert(hash);
                                    
                                    if db.insert(&obj).is_ok() {
                                        new_count += 1;
                                    }
                                }
                            }
                            
                            if new_count > 0 {
                                println!("Received {} new objects from node {}", 
                                        new_count, sender_id);
                                
                                let mut stats = stats.lock().unwrap();
                                stats.objects_received += new_count as u64;
                            }
                        }
                        
                        MeshMessage::SpatialQuery { query_id, center, radius } => {
                            // Handle spatial query
                            let db = database.lock().unwrap();
                            if let Ok(objects) = db.find_within_radius(
                                center.0, center.1, center.2, radius
                            ) {
                                let _response = MeshMessage::QueryResponse {
                                    query_id,
                                    objects,
                                };
                                
                                // In production: send response to sender
                                println!("Handled spatial query {} from node {}", 
                                        query_id, sender_id);
                                
                                let mut stats = stats.lock().unwrap();
                                stats.queries_handled += 1;
                            }
                        }
                        
                        MeshMessage::Ping { node_id, load: _ } => {
                            // Respond with pong
                            let db = database.lock().unwrap();
                            if let Ok(stats) = db.get_stats() {
                                let _pong = MeshMessage::Pong {
                                    node_id: config.node_id,
                                    object_count: stats.total_objects,
                                };
                                
                                // In production: send pong to sender
                                println!("Responding to ping from node {}", node_id);
                            }
                        }
                        
                        _ => {
                            // Handle other message types
                        }
                    }
                    
                    let mut stats = stats.lock().unwrap();
                    stats.messages_received += 1;
                }
                
                tokio::time::sleep(Duration::from_millis(100)).await;
            }
        })
    }
    
    /// Hash an ArxObject for deduplication
    fn hash_object(obj: &ArxObject) -> u64 {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        // Copy values to avoid packed field alignment issues
        let building_id = obj.building_id;
        let object_type = obj.object_type;
        let x = obj.x;
        let y = obj.y;
        let z = obj.z;
        
        building_id.hash(&mut hasher);
        object_type.hash(&mut hasher);
        x.hash(&mut hasher);
        y.hash(&mut hasher);
        z.hash(&mut hasher);
        hasher.finish()
    }
    
    /// Add a peer to the network
    pub fn add_peer(&self, node_id: NodeId, address: SocketAddr, capabilities: NodeCapabilities) {
        let mut peers = self.peers.lock().unwrap();
        
        if peers.len() < self.config.max_peers {
            peers.insert(node_id, PeerInfo {
                node_id,
                address,
                last_seen: Instant::now(),
                capabilities,
                latency_ms: None,
                object_count: 0,
            });
            
            println!("Added peer {} at {}", node_id, address);
            
            let mut stats = self.stats.lock().unwrap();
            stats.active_peers = peers.len();
        }
    }
    
    /// Query objects from the mesh
    pub async fn query_spatial(&self, center: (f32, f32, f32), radius: f32) 
        -> Result<Vec<ArxObject>, Box<dyn std::error::Error>> {
        // First check local database
        let db = self.database.lock().unwrap();
        let results = db.find_within_radius(center.0, center.1, center.2, radius)?;
        
        // Then query peers
        let query_id = rand::random::<u64>();
        let _query = MeshMessage::SpatialQuery {
            query_id,
            center,
            radius,
        };
        
        // In production: send to peers and collect responses
        println!("Querying mesh for objects within {}m of ({:.1}, {:.1}, {:.1})",
                radius, center.0, center.1, center.2);
        
        Ok(results)
    }
    
    /// Get node statistics
    pub fn get_stats(&self) -> NodeStats {
        (*self.stats.lock().unwrap()).clone()
    }
    
    /// Trigger manual sync with peers
    pub async fn sync_with_peers(&self) {
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs() - 3600; // Sync last hour
        
        let _sync_request = MeshMessage::SyncRequest {
            since_timestamp: timestamp,
            building_id: self.config.building_id,
        };
        
        let peers = self.peers.lock().unwrap();
        for peer in peers.values() {
            // In production: send sync request
            println!("Requesting sync from node {}", peer.node_id);
        }
        
        let mut stats = self.stats.lock().unwrap();
        stats.sync_operations += 1;
    }
}

/// Mesh network simulator for testing
pub struct MeshSimulator {
    nodes: Vec<Arc<MeshNode>>,
}

impl MeshSimulator {
    /// Create a simulated mesh network
    pub fn new(num_nodes: usize) -> Result<Self, Box<dyn std::error::Error>> {
        let mut nodes = Vec::new();
        
        for i in 0..num_nodes {
            let config = MeshConfig {
                node_id: i as u16,
                building_id: 0x0001,
                listen_port: 8080 + i as u16,
                database_path: format!(":memory:"), // In-memory for testing
                ..Default::default()
            };
            
            let node = Arc::new(MeshNode::new(config)?);
            nodes.push(node);
        }
        
        // Connect all nodes to each other (full mesh)
        for i in 0..num_nodes {
            for j in 0..num_nodes {
                if i != j {
                    let addr = format!("127.0.0.1:{}", 8080 + j).parse().unwrap();
                    nodes[i].add_peer(
                        j as u16,
                        addr,
                        NodeCapabilities {
                            storage_mb: 100,
                            object_capacity: 10000,
                            has_database: true,
                            supports_queries: true,
                            battery_powered: false,
                        }
                    );
                }
            }
        }
        
        Ok(Self { nodes })
    }
    
    /// Inject objects into a node
    pub fn inject_objects(&self, node_index: usize, objects: Vec<ArxObject>) 
        -> Result<(), Box<dyn std::error::Error>> {
        if node_index < self.nodes.len() {
            let node = &self.nodes[node_index];
            let mut db = node.database.lock().unwrap();
            db.insert_batch(&objects)?;
            
            println!("Injected {} objects into node {}", objects.len(), node_index);
        }
        
        Ok(())
    }
    
    /// Simulate network activity
    pub async fn simulate(&self, duration: Duration) {
        println!("Simulating mesh network for {:?}", duration);
        
        let start = Instant::now();
        while start.elapsed() < duration {
            // Simulate random queries
            for node in &self.nodes {
                if rand::random::<f32>() < 0.1 {
                    let center = (
                        rand::random::<f32>() * 10.0,
                        rand::random::<f32>() * 10.0,
                        rand::random::<f32>() * 3.0,
                    );
                    
                    let _ = node.query_spatial(center, 2.0).await;
                }
            }
            
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
        
        // Print statistics
        println!("\nMesh Network Statistics:");
        for (i, node) in self.nodes.iter().enumerate() {
            let stats = node.get_stats();
            println!("Node {}:", i);
            println!("  Messages: {} sent, {} received", 
                    stats.messages_sent, stats.messages_received);
            println!("  Objects: {} shared, {} received",
                    stats.objects_shared, stats.objects_received);
            println!("  Queries handled: {}", stats.queries_handled);
            println!("  Active peers: {}", stats.active_peers);
        }
    }
}