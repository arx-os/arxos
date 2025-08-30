# Slow-Bleed Progressive Enhancement Architecture

## BitTorrent for Building Intelligence

**Version:** 1.0  
**Date:** August 2024  
**Status:** Core Architecture Specification

---

## Executive Summary

The Slow-Bleed Architecture unifies the simplicity of 13-byte mesh packets with the richness of CAD-level building intelligence through a continuous, circular broadcasting pattern. Like BitTorrent, every node contributes pieces of detailed information, and over time, the entire mesh achieves complete building consciousness.

**Key Innovation:** Bandwidth constraints become a feature, not a bug. The slow accumulation of detail creates a living, breathing building intelligence that grows richer over time.

---

## 1. Architecture Overview

### 1.1 Dual-Layer Protocol

```
Layer 1: Critical Operations (Real-time)
├── 13-byte ArxObject packets
├── State changes and alerts
├── Control commands
└── 20% of bandwidth

Layer 2: Progressive Enhancement (Slow-bleed)
├── Detail chunks (13-byte packets)
├── Historical data
├── Simulation models
└── 80% of bandwidth
```

### 1.2 Data Flow Architecture

```
Building A                Building B                Building C
    │                         │                         │
    ├─[Live: 13B]────────────►├─[Live: 13B]────────────►│
    ├─[Detail: Chunk 001]────►├─[Detail: Chunk 001]────►│
    ├─[Detail: Chunk 002]────►├─[Detail: Chunk 002]────►│
    │                         │                         │
    │◄────────[Live: 13B]─────┤◄────────[Live: 13B]─────┤
    │◄──[Detail: Chunk 142]───┤◄──[Detail: Chunk 142]───┤
    │                         │                         │
    └─────────────────────────┴─────────────────────────┘
         Continuous Circular Broadcasting Pattern
```

---

## 2. Packet Specifications

### 2.1 Unified Packet Structure

All packets are exactly 13 bytes to maintain compatibility:

```rust
#[repr(C, packed)]
pub struct MeshPacket {
    pub packet_type: u8,    // 0x00-0x7F: Live, 0x80-0xFF: Detail
    pub payload: [u8; 12],  // Type-specific data
}
```

### 2.2 Live Packet (Critical Updates)

```rust
// Packet type: 0x00-0x7F
pub struct LivePacket {
    pub packet_type: u8,     // 0x00-0x7F (includes object type)
    pub object_id: u16,      // Which object
    pub x: u16,              // Current position
    pub y: u16,
    pub z: u16,
    pub properties: [u8; 4], // Current state
}
```

### 2.3 Detail Chunk Packet

```rust
// Packet type: 0x80-0xFF
pub struct DetailChunk {
    pub packet_type: u8,     // 0x80-0xFF (includes chunk type)
    pub object_id: u16,      // Which object
    pub chunk_id: u16,       // Which chunk (0-65535)
    pub chunk_data: [u8; 8], // Actual detail data
}
```

### 2.4 Chunk Type Definitions

```rust
pub enum ChunkType {
    // Material Properties (0x80-0x8F)
    MaterialDensity = 0x80,
    MaterialThermal = 0x81,
    MaterialAcoustic = 0x82,
    MaterialStructural = 0x83,
    
    // Historical Data (0x90-0x9F)
    MaintenanceHistory = 0x90,
    PerformanceHistory = 0x91,
    FailureHistory = 0x92,
    
    // Relationships (0xA0-0xAF)
    ElectricalConnections = 0xA0,
    HVACConnections = 0xA1,
    StructuralSupports = 0xA2,
    
    // Simulation Models (0xB0-0xBF)
    ThermalModel = 0xB0,
    AirflowModel = 0xB1,
    ElectricalModel = 0xB2,
    
    // Predictive Data (0xC0-0xCF)
    FailurePrediction = 0xC0,
    MaintenanceSchedule = 0xC1,
    OptimizationParams = 0xC2,
}
```

---

## 3. Progressive Enhancement Strategy

### 3.1 Detail Accumulation Levels

```rust
pub struct DetailLevel {
    pub basic: bool,         // 13-byte object (instant)
    pub material: f32,       // Material properties (0-1, hours)
    pub systems: f32,        // System connections (0-1, days)
    pub historical: f32,     // Historical data (0-1, weeks)
    pub simulation: f32,     // Simulation models (0-1, months)
    pub predictive: f32,     // Predictive analytics (0-1, months)
}

impl DetailLevel {
    pub fn completeness(&self) -> f32 {
        let weights = [
            (self.basic as u8 as f32) * 0.1,
            self.material * 0.2,
            self.systems * 0.2,
            self.historical * 0.2,
            self.simulation * 0.15,
            self.predictive * 0.15,
        ];
        weights.iter().sum()
    }
}
```

### 3.2 Broadcasting Priority Algorithm

```rust
pub struct BroadcastScheduler {
    priority_queue: BinaryHeap<ChunkPriority>,
    recent_broadcasts: CircularBuffer<(u16, u16)>,
    mesh_requests: HashMap<(u16, u16), u32>,
}

impl BroadcastScheduler {
    pub fn next_chunk(&mut self) -> DetailChunk {
        // Priority factors:
        // 1. Object criticality (electrical panels > walls)
        // 2. Request frequency (popular objects first)
        // 3. Completion gaps (missing pieces)
        // 4. Update freshness (recent changes)
        // 5. Round-robin fairness (all objects get time)
        
        loop {
            let candidate = self.priority_queue.pop().unwrap();
            
            // Avoid repeating recent broadcasts
            if !self.recent_broadcasts.contains(&candidate.chunk_id) {
                self.recent_broadcasts.push(candidate.chunk_id);
                return self.create_chunk(candidate);
            }
        }
    }
}
```

---

## 4. Bandwidth Economics

### 4.1 Bandwidth Allocation

```yaml
Total LoRa Bandwidth: 1000 bps (125 bytes/second)

Allocation:
  Critical Updates: 20% (25 bytes/second)
    - 1-2 live updates per second
    - Emergency overrides
    - Control commands
  
  Detail Streaming: 80% (100 bytes/second)
    - 7-8 detail chunks per second
    - 604,800 chunks per week
    - ~7.8 MB per week per node

Mesh Multiplication:
  10 nodes: 78 MB/week collective throughput
  100 nodes: 780 MB/week collective throughput
  1000 nodes: 7.8 GB/week collective throughput
```

### 4.2 Convergence Time Calculations

```python
def calculate_convergence_time(model_size_mb, num_nodes, efficiency=0.7):
    """Calculate time for full model propagation"""
    
    bandwidth_per_node = 100  # bytes/second for detail
    collective_bandwidth = bandwidth_per_node * num_nodes * efficiency
    
    model_size_bytes = model_size_mb * 1024 * 1024
    seconds = model_size_bytes / collective_bandwidth
    
    return {
        'seconds': seconds,
        'hours': seconds / 3600,
        'days': seconds / 86400,
        'weeks': seconds / 604800
    }

# Examples:
# 10 MB building, 10 nodes: ~1.7 days
# 100 MB campus, 100 nodes: ~1.7 days  
# 1 GB city, 1000 nodes: ~1.7 days
```

---

## 5. Implementation Architecture

### 5.1 Core Components

```rust
pub struct SlowBleedNode {
    // Identity
    pub node_id: u16,
    pub building_id: u16,
    
    // Live data (always current)
    pub live_objects: HashMap<u16, ArxObjectLive>,
    
    // Progressive detail accumulation
    pub detail_store: DetailStore,
    
    // Broadcasting machinery
    pub broadcast_scheduler: BroadcastScheduler,
    pub receive_buffer: ReceiveBuffer,
    
    // Mesh participation
    pub mesh_router: MeshRouter,
    pub peer_nodes: Vec<NodeInfo>,
    
    // Gaming mechanics
    pub bilt_tracker: BiltTracker,
    pub discovery_log: DiscoveryLog,
}

pub struct DetailStore {
    // Chunk storage by (object_id, chunk_id)
    chunks: HashMap<(u16, u16), DetailChunk>,
    
    // Track completeness per object
    completeness: HashMap<u16, DetailLevel>,
    
    // Indexes for fast lookup
    by_type: HashMap<ChunkType, Vec<(u16, u16)>>,
    by_freshness: BTreeMap<DateTime<Utc>, (u16, u16)>,
    
    // Verification hashes
    checksums: HashMap<u16, u32>,
}
```

### 5.2 State Machine

```rust
pub enum NodeState {
    // Discovery phase - learning about mesh
    Discovering { started: Instant, peers_found: u32 },
    
    // Synchronizing - catching up on critical data
    Synchronizing { progress: f32, target_peers: Vec<u16> },
    
    // Contributing - actively broadcasting
    Contributing { chunks_sent: u64, chunks_received: u64 },
    
    // Optimizing - reorganizing for efficiency
    Optimizing { defrag_progress: f32 },
}
```

---

## 6. Progressive Rendering

### 6.1 ASCII Rendering with Partial Data

```rust
impl ProgressiveRenderer {
    pub fn render_object(&self, object_id: u16) -> String {
        let completeness = self.detail_store.get_completeness(object_id);
        
        match completeness {
            0.0..=0.1 => self.render_basic(object_id),      // Just shape
            0.1..=0.3 => self.render_material(object_id),   // Add materials
            0.3..=0.5 => self.render_systems(object_id),    // Add connections
            0.5..=0.7 => self.render_historical(object_id), // Add history
            0.7..=0.9 => self.render_simulation(object_id), // Add dynamics
            0.9..=1.0 => self.render_full_cad(object_id),   // Full detail
            _ => "?".to_string(),
        }
    }
    
    fn render_with_confidence(&self, object_id: u16) -> String {
        let mut output = String::new();
        let detail = self.detail_store.get_detail_level(object_id);
        
        // Base representation
        output.push_str(&self.render_shape(object_id));
        
        // Progressive overlays
        if detail.material > 0.5 {
            output.push_str(&format!(" [{}]", self.get_material_indicator(object_id)));
        }
        
        if detail.systems > 0.5 {
            output.push_str(&format!(" →{}", self.get_connected_systems(object_id)));
        }
        
        if detail.historical > 0.5 {
            output.push_str(&format!(" ⟲{}", self.get_maintenance_indicator(object_id)));
        }
        
        output
    }
}
```

### 6.2 Confidence Visualization

```
Legend for Progressive Detail:
█ - Shape only (basic packet received)
▓ - Material properties loading (30% complete)
▒ - Systems connected (60% complete)
░ - Historical data available (80% complete)
□ - Simulation ready (90% complete)
⬚ - Full CAD detail (100% complete)

Special Indicators:
⟲ - Historical data available
→ - System connections mapped
◆ - Simulation model loaded
✓ - Fully synchronized
⚡ - Live data streaming
```

---

## 7. Gaming Mechanics

### 7.1 BILT Token Rewards

```rust
pub struct BiltRewards {
    // Discovery rewards
    pub first_chunk_discovery: u32,      // 10 BILT
    pub complete_object_discovery: u32,  // 100 BILT
    pub rare_chunk_discovery: u32,       // 50 BILT
    
    // Contribution rewards
    pub chunks_broadcasted: u32,         // 1 BILT per 100
    pub bandwidth_contributed: u32,      // 1 BILT per MB
    pub cache_hits_served: u32,          // 1 BILT per 1000
    
    // Verification rewards
    pub chunks_verified: u32,            // 5 BILT per verification
    pub inconsistencies_found: u32,      // 100 BILT per fix
}
```

### 7.2 Achievement System

```rust
pub enum Achievement {
    // Discovery achievements
    FirstContact,        // Discover first building
    Explorer,           // Discover 10 buildings
    Cartographer,       // Map entire mesh
    
    // Contribution achievements
    Broadcaster,        // Send 10,000 chunks
    CacheKing,         // Serve 100,000 requests
    BandwidthHero,     // Contribute 1 GB
    
    // Completeness achievements
    Perfectionist,     // 100% complete building
    Collector,         // 50% complete on 10 buildings
    Archivist,         // Store 1 GB of detail
}
```

---

## 8. Network Topology Examples

### 8.1 Small Campus (10 Buildings)

```
Convergence Timeline:
- Hour 1: All critical systems visible
- Day 1: Basic materials and connections
- Week 1: Full system mappings
- Month 1: Historical data complete
- Month 3: Full CAD parity achieved

Bandwidth Usage:
- Per node: 8.6 MB/day
- Total mesh: 86 MB/day
- Full model size: ~100 MB
- Convergence: ~1.2 days theoretical, 7 days practical
```

### 8.2 City District (100 Buildings)

```
Convergence Timeline:
- Hour 1: Emergency systems mapped
- Day 1: Critical infrastructure visible
- Week 1: Major systems documented
- Month 1: Standard detail level
- Month 6: Complete digital twin

Bandwidth Usage:
- Per node: 8.6 MB/day
- Total mesh: 860 MB/day
- Full model size: ~10 GB
- Convergence: ~12 days theoretical, 30 days practical
```

---

## 9. Implementation Roadmap

### Phase 1: Core Protocol (Month 1)
- Implement dual-layer packet structure
- Basic chunk storage and retrieval
- Simple round-robin broadcasting

### Phase 2: Progressive Enhancement (Month 2)
- Priority-based scheduling
- Completeness tracking
- Progressive rendering

### Phase 3: Mesh Intelligence (Month 3)
- Distributed caching
- Smart routing
- Peer discovery

### Phase 4: Gaming Layer (Month 4)
- BILT token tracking
- Achievement system
- Discovery rewards

---

## 10. Conclusion

The Slow-Bleed Architecture transforms bandwidth constraints into a feature, creating a living building intelligence that grows richer over time. Like a massive multiplayer game where the world slowly reveals itself, buildings share their consciousness through the mesh, achieving CAD-level detail through patience and collaboration rather than brute force bandwidth.

**This is building intelligence as an emergent property of collective participation.**