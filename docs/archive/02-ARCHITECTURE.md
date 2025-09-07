# ArxOS Architecture: RF-Only Building Intelligence Routing

> **Core Principle: "ArxOS routes building intelligence, it doesn't process it."**

## Architectural Overview

ArxOS is designed as a pure routing architecture that moves 13-byte ArxObjects through RF mesh networks without requiring internet connectivity or centralized processing. Every component is optimized for routing efficiency, not computational complexity.

Compile-time features:
- `rf_only` (default): disables any net clients and enforces local-only operation.
- `internet_touchpoints` (off by default): compiles optional SMS/docs.
- `mobile_offline`: enables mobile BLE/USB bindings without network permissions.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER DEVICES                          │
├─────────────────────────────────────────────────────────┤
│  iPhone/Android │ Laptop │ Desktop │ Tablet             │
│       ↓            ↓        ↓         ↓                 │
│  Local Terminal Client (Serial/BLE)                      │
│       ↓            ↓        ↓         ↓                 │
│    [Camera]     [No Camera] [No Camera] [Camera]        │
└────────────────┬─────────────────────────────────────────┘
                 │ Serial/BLE Link (Local)
┌────────────────▼─────────────────────────────────────────┐
│                 MESH NODE LAYER                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │           ArxOS Core (Rust Binary)              │    │
│  │  • 13-byte ArxObject protocol                   │    │
│  │  • Semantic compression engine                  │    │
│  │  • Building intelligence routing                │    │
│  │  • File-based storage (no database)            │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │      Local Terminal Service (TTY/BLE)           │    │
│  │  • Terminal interface for all clients           │    │
│  │  • Camera data receiver for iOS/Android         │    │
│  │  • Command processing and routing               │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │         File-Based Storage System               │    │
│  │  • ArxObject files (13 bytes per object)        │    │
│  │  • Building intelligence files                  │    │
│  │  • Route tables and mesh topology              │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────┬─────────────────────────────────────────┘
                 │ LoRa Radio (NO INTERNET)
┌────────────────▼─────────────────────────────────────────┐
│              RF MESH NETWORK LAYER                       │
├─────────────────────────────────────────────────────────┤
│  Building A ←──LoRa──→ Building B ←──LoRa──→ Building C │
│      📡                    📡                    📡      │
│  • Meshtastic protocol for routing                       │
│  • 915MHz ISM band (US) / 868MHz (EU)                   │
│  • 2-10km range between nodes                           │
│  • Automatic mesh healing and routing                   │
└──────────────────────────────────────────────────────────┘
```

## Key Architectural Principles

- BAS/BMS Supervisory (concept): Local building Pis close hard loops; RF mesh carries supervisory commands and telemetry. See `docs/concepts/BAS_BMS_SUPERVISORY.md`.

### Sealed Frames and Anti‑Replay
- Application frames are sealed with a security header (8B: sender_id, key_version, nonce) and a 16B MAC.
- Anti‑replay enforced via per‑sender sliding window.
- With a 4B app header (frame index/total), 17 × 13B ArxObjects fit a 255‑byte MTU.
- See: `docs/technical/ARXOBJECT_WIRE_FORMAT.md` and `docs/LATENCY_ESTIMATES.md`.

### 1. File-Based Storage (No Database)

ArxOS uses a pure file-based storage system designed for extreme simplicity and mesh network efficiency:

```rust
// File-based storage structure
pub struct FileStorage {
    objects_dir: PathBuf,      // 13-byte ArxObject files
    routes_dir: PathBuf,       // Mesh routing tables
    building_dir: PathBuf,     // Building intelligence files
    cache_dir: PathBuf,        // Local cache files
}

// Each ArxObject stored as individual 13-byte file
// Filename: building_id.object_type.object_id
// Content: Exactly 13 bytes of ArxObject data
```

**Benefits of File-Based Storage:**
- **No database complexity**: No SQL engine, schemas, or query optimization
- **Mesh-friendly**: Files sync naturally across distributed nodes
- **Crash resistant**: Individual file corruption doesn't affect entire system
- **Debug simple**: Files can be inspected with standard tools
- **Bandwidth efficient**: Only changed files sync across mesh

### 2. RF Mesh Routing

ArxOS operates entirely over LoRa mesh networks using the proven Meshtastic protocol:

```rust
pub struct MeshRouter {
    radio: LoRaRadio,                    // SX126x LoRa radio
    routing_table: Vec<RouteEntry>,      // Known mesh paths
    building_topology: BuildingMap,       // Physical building layout
    packet_queue: PriorityQueue<Packet>, // Routing queue
}

// Routing decisions based on building intelligence
impl MeshRouter {
    fn route_packet(&self, packet: ArxPacket) -> Route {
        // 1. Check if destination is local building
        if self.is_local_building(packet.destination) {
            return Route::Local(self.find_local_node(packet.target));
        }
        
        // 2. Find best mesh path to target building
        let mesh_route = self.find_mesh_path(packet.destination);
        Route::Mesh(mesh_route)
    }
}
```

**RF Mesh Characteristics:**
- **Frequency**: 915MHz (US) / 868MHz (EU) ISM band
- **Protocol**: Meshtastic for proven mesh routing
- **Range**: 2-10km per hop depending on environment
- **Bandwidth**: Optimized for 13-byte ArxObject packets
- **Power**: Ultra-low power operation for battery nodes

### 3. Bandwidth-First Design Philosophy

ArxOS is architected around the fundamental constraint of RF bandwidth:

#### RF Reality Drives Architecture
```
LoRa Constraints:
├── Data rate: 0.3 - 50 kbps
├── Packet size: 51 - 222 bytes  
├── Airtime: ~1-2 seconds per packet
└── Duty cycle: 1-10% (regulations)

Architecture Response:
├── ArxObject compression (typically ~13 bytes)
├── Differential updates only
├── Priority-based routing
└── Progressive detail streaming
```

#### Rendering Modes Based on Bandwidth

**2D Terminal View** (Always Available):
- Data requirement: ~104 bytes per room
- Transmission: 3-30 seconds through mesh
- Guaranteed delivery even at minimum bandwidth

**3D ASCII "CAD" View** (When Bandwidth Permits):
- Data requirement: ~352 bytes per room
- Transmission: 6-60 seconds through mesh
- Progressive enhancement when bandwidth available

#### Smart Routing Priorities
```rust
enum PacketPriority {
    Emergency,     // < 1 second target
    Control,       // < 5 seconds target
    Update,        // < 30 seconds target
    Sync,          // Best effort
}
```

The entire system adapts to available bandwidth - from object size to rendering quality to update frequency.

### 4. ArxObject Protocol (Fractal Compression)

The ArxObject protocol is the universal language for building intelligence, using fractal compression to fit within bandwidth constraints:

```rust
#[repr(C, packed)]
pub struct ArxObject {
    pub building_id: u16,    // 2 bytes - Building identifier
    pub object_type: u8,     // 1 byte  - Object type (outlet, door, etc.)
    pub x: i16,             // 2 bytes - X position (mm)
    pub y: i16,             // 2 bytes - Y position (mm)  
    pub z: i16,             // 2 bytes - Z position (mm)
    pub properties: [u8; 4], // 4 bytes - Object properties
}
// Total: 13 bytes - Perfect for LoRa packets
```

**Object Type Examples:**
```rust
// Structural Elements
const WALL: u8 = 0x01;
const DOOR: u8 = 0x02;
const WINDOW: u8 = 0x03;

// Electrical Systems  
const OUTLET: u8 = 0x10;
const SWITCH: u8 = 0x11;
const PANEL: u8 = 0x12;

// HVAC Systems
const DUCT: u8 = 0x20;
const THERMOSTAT: u8 = 0x22;
const UNIT: u8 = 0x23;

// Safety Systems
const FIRE_ALARM: u8 = 0x50;
const EXIT_SIGN: u8 = 0x52;
```

**Compression Achievement:**
- Raw LiDAR scan: 50MB point cloud
- Semantic extraction: 5KB building features  
- ArxObject compression: 13 bytes per object
- **Total ratio: 10,000,000:1 compression**

### 5. School District Integration

ArxOS leverages school districts as backbone infrastructure through a carefully designed integration:

```rust
pub struct SchoolDistrictNode {
    // Local school building mesh
    local_mesh: BuildingMesh {
        frequency: 915.2, // MHz - dedicated school channel
        power: 100,       // mW - low power for classroom use
        encryption: true, // AES-256 for student privacy
    },
    
    // District backbone connection
    backbone_mesh: DistrictMesh {
        frequency: 915.4, // MHz - district coordination channel
        power: 1000,      // mW - higher power for inter-building
        routing_only: true, // Cannot decrypt building-specific traffic
    },
}
```

**Integration Benefits:**
- **Free infrastructure**: Schools provide buildings, power, IT support
- **Geographic coverage**: Even distribution across all population centers
- **Political protection**: Education mission provides regulatory cover
- **Network effects**: More schools create better mesh coverage

### 6. Terminal-First Interface

ArxOS uses terminal interfaces as the primary user interaction model:

```rust
pub struct TerminalInterface {
    command_parser: CommandParser,
    ascii_renderer: AsciiRenderer,
    mesh_client: MeshClient,
    local_cache: FileCache,
}

// ASCII building visualization
impl AsciiRenderer {
    fn render_building(&self, building: &Building) -> String {
        let mut output = String::new();
        
        // Multi-scale rendering based on zoom level
        match self.scale {
            Scale::Campus => self.render_building_outline(building),
            Scale::Building => self.render_floor_plan(building),
            Scale::Room => self.render_room_detail(building),
        }
    }
}
```

**Terminal Commands:**
```bash
# Building queries
arx query "outlets in room 205"
arx display building --floor=2 --system=electrical
arx scan room --target=205

# Mesh operations  
arx mesh status
arx mesh route building:0x1234
arx mesh sync --force

# Control operations
arx control hvac --zone=3 --temp=72
arx control lights --room=205 --state=on
```

**ASCII Visualization Example:**
```
ALAFIA ELEMENTARY - FLOOR 2 - ELECTRICAL SYSTEMS
═══════════════════════════════════════════════
┌─────────┬─────────┬─────────┬─────────┐
│ ∴ 201 ∴ │ ∴ 202 ∴ │ ∴ 203 ∴ │ ∴ 204 ∴ │
│ ∴∴○∴∴∴∴ │ ∴∴○∴∴∴∴ │ ∴∴○∴∴∴∴ │ ∴∴○∴∴∴∴ │
├─────────┼─────────┼─────────┼─────────┤
│ ○       │ ○       │ ○       │ ○       │
├═══════○═╪═══════○═╪═══════○═╪═══════○═┤
│         │         │   ▣     │         │
└─────────┴─────────┴─────────┴─────────┘
Legend: ○=Outlet ▣=Panel ═=Power ∴=Space
```

## Data Flow Architecture

### 1. ArxObject Routing Flow

```
User Query → Terminal Parser → Mesh Router → Target Building → Response
     ↓              ↓               ↓              ↓              ↓
  ASCII Text → ArxObject Query → LoRa Packet → Local Search → ArxObjects
     ↓              ↓               ↓              ↓              ↓
  Terminal Display ← ASCII Format ← Mesh Response ← File System ← Object Files
```

### 2. LiDAR Capture Flow

```
iPhone LiDAR → Point Cloud → Semantic Compression → ArxObjects → File Storage
     ↓              ↓              ↓                   ↓              ↓
  RoomPlan API → 50MB Data → Feature Extraction → 13 bytes × N → Local Files
     ↓              ↓              ↓                   ↓              ↓
  Building Model → Processing → ArxObject Creation → Mesh Broadcast → Network Sync
```

### 3. Mesh Synchronization Flow

```
Local Changes → File Watcher → Change Detection → Mesh Broadcast → Remote Nodes
     ↓              ↓              ↓                   ↓              ↓
  Object Updates → Inotify → Delta Calculation → LoRa Packets → File Updates
     ↓              ↓              ↓                   ↓              ↓
  Cache Invalid → Notification → Priority Queue → Network Routing → Sync Complete
```

## Performance Characteristics

### Mesh Network Performance
- **Latency**: <100ms for local building, <30s for cross-district
- **Bandwidth**: 13-byte ArxObjects = 19 objects per LoRa packet
- **Range**: 2km urban, 10km rural per hop
- **Reliability**: >99.9% delivery rate with mesh redundancy
- **Power**: Ultra-low power for battery operation

### File System Performance  
- **Object Storage**: 13 bytes per ArxObject file
- **Query Speed**: <10ms for local file system queries
- **Sync Efficiency**: Only changed files transferred
- **Storage Requirements**: ~50KB per typical building

### Terminal Interface Performance
- **ASCII Render**: <100ms for complex building visualization
- **Command Response**: <1s for cached data, <10s for mesh queries
- **Memory Usage**: <50MB for typical building data
- **Battery Impact**: Minimal due to efficient terminal interface

## Security Architecture

### Air-Gap Security Model
ArxOS achieves security through complete physical isolation:

```rust
pub struct SecurityModel {
    // NO internet connections (except 3 controlled touch points)
    internet_connections: None,
    
    // All communication via encrypted mesh
    mesh_encryption: AES256,
    
    // Local authentication only
    auth_method: LocalCertificate,
    
    // No centralized servers
    server_dependencies: None,
}
```

**Security Benefits:**
- **No attack surface**: Internet threats cannot reach mesh network
- **Data sovereignty**: Building data never leaves local control
- **Regulatory compliance**: Air-gap satisfies strictest privacy requirements
- **Disaster resilience**: Functions during internet outages

### Mesh Network Security
```rust
pub struct MeshSecurity {
    // Building-specific encryption keys
    building_keys: HashMap<BuildingId, AES256Key>,
    
    // Routing-only backbone nodes
    backbone_routing: ZeroKnowledgeRouting,
    
    // Packet integrity verification
    packet_signing: HMAC_SHA256,
    
    // Replay attack prevention
    timestamp_validation: AntiReplay,
}
```

## Deployment Architecture

### Single Building Deployment
```
Building Gateway Node:
├── Raspberry Pi 4 (4GB RAM, 64GB storage)
├── LoRa Radio (SX1262, 915MHz, 22dBm)
├── External Antenna (5.8dBi gain)
├── Power over Ethernet
└── Cost: ~$200 per building

Room-Level Nodes:
├── ESP32-S3 (dual core, 8MB RAM)
├── LoRa Radio (SX1262, 915MHz, 14dBm)
├── Internal Antenna
├── Battery + Solar Panel
└── Cost: ~$50 per room
```

### School District Deployment
```
District Backbone:
├── High-power LoRa gateway at district office
├── 1W transmission power for long-range coordination
├── Redundant internet connections (3 touch points only)
├── District-wide routing tables
└── Network operations center integration

School Buildings:
├── Standard building gateway per school
├── Room-level nodes for detailed building intelligence
├── Local mesh network within each building
├── Backbone connection to district network
└── Complete local autonomy if district connection fails
```

## Technology Stack

### Core Technologies
```yaml
Language: Rust (all components)
Storage: File system (no database)
Networking: LoRa mesh (Meshtastic protocol)  
Interface: Terminal + ASCII visualization
Hardware: Standard Raspberry Pi and ESP32
```

### Platform Support
```yaml
Mesh Nodes:
  - Raspberry Pi 4 (building gateways)
  - ESP32-S3 (room-level nodes)
  
User Devices:
  - iOS (Terminal + LiDAR scanning)
  - Android (Terminal + camera)
  - macOS/Linux/Windows (Terminal only)
  
Protocols:
  - LoRa (915MHz US, 868MHz EU)
  - Bluetooth Low Energy (device connections)
  - USB Serial (direct terminal access)
```

## Scalability Design

### Hierarchical Architecture
```
Global Scale:
├── 98,000+ school buildings (US backbone)
├── 1M+ commercial buildings (mesh participants)  
├── 10M+ ArxObjects (distributed storage)
├── Zero centralized processing
└── Linear scaling through mesh topology
```

### Compression Scaling
```
Building Level: 1,000 ArxObjects → 13KB storage
Campus Level: 10,000 ArxObjects → 130KB storage  
District Level: 100,000 ArxObjects → 1.3MB storage
Regional Level: 1M ArxObjects → 13MB storage
```

## Implementation Priorities

### Phase 1: Core Routing (Months 1-6)
- [x] 13-byte ArxObject protocol
- [x] File-based storage system
- [ ] LoRa mesh integration  
- [ ] Terminal interface
- [ ] ASCII visualization

### Phase 2: School Integration (Months 4-9)
- [ ] School district deployment tools
- [ ] Backbone routing protocols
- [ ] Building-to-building mesh
- [ ] District operations dashboard
- [ ] Emergency services integration

### Phase 3: Scale Optimization (Months 7-12)
- [ ] Multi-district mesh networks
- [ ] Performance optimization
- [ ] Advanced routing algorithms
- [ ] Network health monitoring
- [ ] Global routing coordination

## Success Metrics

### Technical Performance
- **Binary Size**: <5MB total system ✓
- **Routing Latency**: <100ms local, <30s remote
- **Storage Efficiency**: 13 bytes per building object ✓
- **Mesh Reliability**: >99.9% packet delivery
- **Power Efficiency**: >168 hours battery life

### Architectural Goals
- **No Database**: Pure file-based storage ✓
- **RF-Only**: No internet dependencies (except 3 touch points) ✓
- **Terminal-First**: ASCII interface primary ✓
- **13-Byte Protocol**: Universal building object format ✓
- **School Backbone**: Leverage education infrastructure ✓

---

*"The constraint is the innovation: 13 bytes forces elegance, RF-only forces simplicity, files force clarity."*