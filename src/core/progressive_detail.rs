//! Progressive Detail Architecture for ArxObjects
//! 
//! This module implements the fractal expansion system where ArxObjects
//! start as 13-byte seeds and progressively accumulate detail based on
//! user input and system inference, like puzzle pieces with expandable tabs.

use crate::arxobject::ArxObject;
use crate::error::{Result, ArxError};
use std::collections::HashMap;
use serde::{Serialize, Deserialize};

/// The levels of detail that can be progressively added to an ArxObject
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub enum DetailLevel {
    /// Level 0: Just the 13-byte core seed
    Core,
    /// Level 1: Basic identity (make/model, specifications)
    Identity,
    /// Level 2: Direct connections (circuits, switches, controllers)
    Connections,
    /// Level 3: System topology (panels, zones, networks)
    Topology,
    /// Level 4: Full building context (complete graph relationships)
    Context,
}

/// Compressed identity information (Level 1)
/// Stores make/model and basic specifications
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressedIdentity {
    /// Manufacturer hash (4 bytes)
    pub manufacturer: u32,
    /// Model number hash (4 bytes)
    pub model: u32,
    /// Basic specifications based on object type
    pub specs: Vec<u8>, // Variable size, typically 8-16 bytes
}

/// Compressed connection information (Level 2)
/// Stores direct electrical/mechanical/data connections
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressedConnections {
    /// Circuit/network ID this object connects to
    pub primary_connection: u16,
    /// Secondary connections (switches, controllers, peers)
    pub secondary_connections: Vec<u16>, // Variable, typically 2-8 connections
    /// Connection metadata (wire gauge, protocol, etc.)
    pub metadata: Vec<u8>, // Variable, typically 4-8 bytes
}

/// Compressed topology information (Level 3)
/// Stores system-level relationships
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressedTopology {
    /// Panel/distribution point ID
    pub panel_id: u16,
    /// Zone/area ID for HVAC, lighting zones, etc.
    pub zone_id: u16,
    /// Network segment for data connections
    pub network_segment: u16,
    /// System flags (emergency circuit, critical load, etc.)
    pub system_flags: u16,
    /// Topology metadata
    pub metadata: Vec<u8>, // Variable, typically 8-16 bytes
}

/// Compressed context information (Level 4)
/// Full building graph relationships
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompressedContext {
    /// Building system dependencies
    pub dependencies: Vec<u16>,
    /// Objects that depend on this one
    pub dependents: Vec<u16>,
    /// Maintenance relationships
    pub maintenance_group: u16,
    /// Operational schedule ID
    pub schedule_id: u16,
    /// Full context metadata
    pub metadata: Vec<u8>, // Variable, can be large
}

/// Progressive Detail Tree - stores expanding information for an ArxObject
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetailTree {
    /// The core 13-byte ArxObject (always present)
    pub core: ArxObject,
    
    /// Level 1: Basic properties (make/model)
    pub identity: Option<CompressedIdentity>,
    
    /// Level 2: Direct connections
    pub connections: Option<CompressedConnections>,
    
    /// Level 3: System topology
    pub topology: Option<CompressedTopology>,
    
    /// Level 4: Full context
    pub context: Option<CompressedContext>,
    
    /// Timestamp of last update (for sync)
    pub last_updated: u64,
    
    /// Version number for conflict resolution
    pub version: u32,
}

impl DetailTree {
    /// Create a new detail tree from a core ArxObject
    pub fn new(core: ArxObject) -> Self {
        Self {
            core,
            identity: None,
            connections: None,
            topology: None,
            context: None,
            last_updated: 0, // Will be set by system
            version: 1,
        }
    }
    
    /// Add identity information (Level 1)
    pub fn add_identity(&mut self, manufacturer: &str, model: &str, specs: Vec<u8>) {
        self.identity = Some(CompressedIdentity {
            manufacturer: hash_string(manufacturer),
            model: hash_string(model),
            specs,
        });
        self.version += 1;
    }
    
    /// Add connection information (Level 2)
    pub fn add_connections(&mut self, primary: u16, secondary: Vec<u16>, metadata: Vec<u8>) {
        self.connections = Some(CompressedConnections {
            primary_connection: primary,
            secondary_connections: secondary,
            metadata,
        });
        self.version += 1;
    }
    
    /// Add topology information (Level 3)
    pub fn add_topology(&mut self, panel: u16, zone: u16, network: u16, flags: u16) {
        self.topology = Some(CompressedTopology {
            panel_id: panel,
            zone_id: zone,
            network_segment: network,
            system_flags: flags,
            metadata: Vec::new(),
        });
        self.version += 1;
    }
    
    /// Add context information (Level 4)
    pub fn add_context(&mut self, deps: Vec<u16>, dependents: Vec<u16>, maint: u16, schedule: u16) {
        self.context = Some(CompressedContext {
            dependencies: deps,
            dependents,
            maintenance_group: maint,
            schedule_id: schedule,
            metadata: Vec::new(),
        });
        self.version += 1;
    }
    
    /// Get the current detail level
    pub fn detail_level(&self) -> DetailLevel {
        if self.context.is_some() {
            DetailLevel::Context
        } else if self.topology.is_some() {
            DetailLevel::Topology
        } else if self.connections.is_some() {
            DetailLevel::Connections
        } else if self.identity.is_some() {
            DetailLevel::Identity
        } else {
            DetailLevel::Core
        }
    }
    
    /// Calculate total size in bytes
    pub fn total_size(&self) -> usize {
        let mut size = ArxObject::SIZE; // 13 bytes core
        
        if let Some(ref id) = self.identity {
            size += 8 + id.specs.len(); // 8 bytes fixed + variable specs
        }
        
        if let Some(ref conn) = self.connections {
            size += 2 + (conn.secondary_connections.len() * 2) + conn.metadata.len();
        }
        
        if let Some(ref topo) = self.topology {
            size += 8 + topo.metadata.len();
        }
        
        if let Some(ref ctx) = self.context {
            size += 4 + (ctx.dependencies.len() * 2) + (ctx.dependents.len() * 2) + ctx.metadata.len();
        }
        
        size
    }
    
    /// Get compression ratio compared to traditional BIM data
    pub fn compression_ratio(&self) -> f32 {
        // Traditional BIM object: ~2MB average
        // Our progressive detail: typically 13-200 bytes
        let traditional_size = 2_000_000.0; // 2MB
        let our_size = self.total_size() as f32;
        traditional_size / our_size
    }
}

/// Progressive Detail Store - manages all detail trees in a building
pub struct ProgressiveDetailStore {
    /// Map from ArxObject ID to its detail tree
    trees: HashMap<u64, DetailTree>,
    
    /// Index by detail level for efficient queries
    by_level: HashMap<DetailLevel, Vec<u64>>,
    
    /// Cache for frequently accessed details
    cache: lru::LruCache<u64, DetailTree>,
}

impl ProgressiveDetailStore {
    /// Create a new progressive detail store
    pub fn new(cache_size: usize) -> Self {
        Self {
            trees: HashMap::new(),
            by_level: HashMap::new(),
            cache: lru::LruCache::new(cache_size.try_into().unwrap()),
        }
    }
    
    /// Store a detail tree
    pub fn store(&mut self, tree: DetailTree) -> u64 {
        let id = tree.core.to_id();
        let level = tree.detail_level();
        
        // Update indices
        self.trees.insert(id, tree.clone());
        self.by_level.entry(level).or_insert_with(Vec::new).push(id);
        
        // Update cache
        self.cache.put(id, tree);
        
        id
    }
    
    /// Retrieve a detail tree (with caching)
    pub fn get(&mut self, id: u64) -> Option<DetailTree> {
        // Check cache first
        if let Some(tree) = self.cache.get(&id) {
            return Some(tree.clone());
        }
        
        // Load from store and cache
        if let Some(tree) = self.trees.get(&id) {
            self.cache.put(id, tree.clone());
            Some(tree.clone())
        } else {
            None
        }
    }
    
    /// Get only the core ArxObjects (13 bytes each) for transmission
    pub fn get_cores_only(&self) -> Vec<ArxObject> {
        self.trees.values().map(|tree| tree.core).collect()
    }
    
    /// Get objects at a specific detail level
    pub fn get_by_level(&self, level: DetailLevel) -> Vec<&DetailTree> {
        if let Some(ids) = self.by_level.get(&level) {
            ids.iter()
                .filter_map(|id| self.trees.get(id))
                .collect()
        } else {
            Vec::new()
        }
    }
    
    /// Lazy load details for an ArxObject
    pub fn lazy_load(&mut self, id: u64, requested_level: DetailLevel) -> Result<DetailTree> {
        if let Some(mut tree) = self.get(id) {
            // Check if we need to load more detail
            if tree.detail_level() < requested_level {
                // In real implementation, this would fetch from database or network
                self.fetch_details(&mut tree, requested_level)?;
                self.store(tree.clone());
            }
            Ok(tree)
        } else {
            Err(ArxError::NotFound(format!("ArxObject {} not found", id)))
        }
    }
    
    /// Fetch additional details (simulated - would connect to database)
    fn fetch_details(&self, tree: &mut DetailTree, target_level: DetailLevel) -> Result<()> {
        // This is where we'd fetch from database or infer from context
        // For now, we'll simulate the inference engine
        
        match target_level {
            DetailLevel::Identity => {
                // Infer identity from object type
                match tree.core.object_type {
                    0x10 => { // Light
                        tree.add_identity("Philips", "BR30-Hue", vec![47, 0, 120, 0]); // 47W, 120V
                    }
                    0x11 => { // Outlet
                        tree.add_identity("Leviton", "5-20R", vec![20, 0, 120, 0]); // 20A, 120V
                    }
                    _ => {
                        tree.add_identity("Generic", "Unknown", vec![]);
                    }
                }
            }
            DetailLevel::Connections => {
                // Infer connections from position and type
                let circuit_id = (tree.core.x / 1000) as u16; // Simple spatial hashing
                tree.add_connections(circuit_id, vec![], vec![]);
            }
            DetailLevel::Topology => {
                // Infer topology from connections
                if let Some(conn) = &tree.connections {
                    let panel_id = conn.primary_connection / 42; // Circuit to panel mapping
                    let zone_id = tree.core.z / 3000; // Floor-based zoning
                    tree.add_topology(panel_id, zone_id, 1, 0);
                }
            }
            DetailLevel::Context => {
                // Infer full context
                tree.add_context(vec![], vec![], 1, 1);
            }
            _ => {}
        }
        
        Ok(())
    }
    
    /// Calculate total bandwidth for different transmission strategies
    pub fn bandwidth_analysis(&self) -> BandwidthAnalysis {
        let cores_only = self.get_cores_only();
        let total_objects = cores_only.len();
        let core_bytes = total_objects * ArxObject::SIZE;
        
        let mut total_detail_bytes = 0;
        for tree in self.trees.values() {
            total_detail_bytes += tree.total_size();
        }
        
        BandwidthAnalysis {
            objects_count: total_objects,
            core_only_bytes: core_bytes,
            total_with_details: total_detail_bytes,
            compression_ratio: total_detail_bytes as f32 / core_bytes as f32,
            transmission_strategy: if total_objects > 1000 {
                "Transmit cores only, fetch details on demand".to_string()
            } else {
                "Transmit full details for small buildings".to_string()
            },
        }
    }
}

/// Bandwidth analysis results
#[derive(Debug)]
pub struct BandwidthAnalysis {
    pub objects_count: usize,
    pub core_only_bytes: usize,
    pub total_with_details: usize,
    pub compression_ratio: f32,
    pub transmission_strategy: String,
}

/// Simple string hashing function for consistent IDs
fn hash_string(s: &str) -> u32 {
    let mut hash: u32 = 5381;
    for byte in s.bytes() {
        hash = ((hash << 5).wrapping_add(hash)).wrapping_add(byte as u32);
    }
    hash
}

/// Extension trait for ArxObject to work with progressive details
impl ArxObject {
    /// Convert to unique ID for storage
    pub fn to_id(&self) -> u64 {
        let mut id = (self.building_id as u64) << 48;
        id |= (self.object_type as u64) << 40;
        id |= (self.x as u64) << 24;
        id |= (self.y as u64) << 8;
        id |= (self.z as u64 >> 8) as u64;
        id
    }
    
    /// Create a detail tree from this ArxObject
    pub fn to_detail_tree(self) -> DetailTree {
        DetailTree::new(self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_progressive_expansion() {
        // Start with 13-byte core
        let light = ArxObject::new(1, 0x10, 5000, 3000, 1200);
        assert_eq!(std::mem::size_of_val(&light), 13);
        
        // Create detail tree
        let mut tree = light.to_detail_tree();
        assert_eq!(tree.total_size(), 13);
        assert_eq!(tree.detail_level(), DetailLevel::Core);
        
        // Add identity (Level 1)
        tree.add_identity("Philips", "BR30", vec![47, 0, 120, 0]);
        assert!(tree.total_size() > 13);
        assert_eq!(tree.detail_level(), DetailLevel::Identity);
        
        // Add connections (Level 2)
        tree.add_connections(15, vec![201, 202], vec![14, 2]); // Circuit 15, switches 201/202, 14AWG
        assert_eq!(tree.detail_level(), DetailLevel::Connections);
        
        // Verify compression ratio
        let ratio = tree.compression_ratio();
        assert!(ratio > 10000.0); // Should achieve massive compression
    }
    
    #[test]
    fn test_bandwidth_conscious_transmission() {
        let mut store = ProgressiveDetailStore::new(100);
        
        // Add 1000 objects with varying detail levels
        for i in 0..1000 {
            let obj = ArxObject::new(1, 0x10, i * 100, i * 50, 1200);
            let mut tree = obj.to_detail_tree();
            
            if i % 10 == 0 {
                tree.add_identity("Philips", "BR30", vec![47, 0]);
            }
            
            store.store(tree);
        }
        
        // Analyze bandwidth
        let analysis = store.bandwidth_analysis();
        assert_eq!(analysis.objects_count, 1000);
        assert_eq!(analysis.core_only_bytes, 13000); // 1000 * 13 bytes
        
        // Verify cores-only transmission
        let cores = store.get_cores_only();
        assert_eq!(cores.len(), 1000);
        assert_eq!(cores[0].building_id, 1);
    }
}