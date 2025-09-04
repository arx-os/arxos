---
title: Arxos Architecture: Building Intelligence Flow Orchestrator
summary: Design for routing 13-byte ArxObjects through an RF-only mesh using a terminal-first interface and ASCII bridges.
owner: Lead Architecture
last_updated: 2025-09-04
---
# Arxos Architecture: Building Intelligence Flow Orchestrator

> Canonical specs:
> - ArxObject 13-Byte format: [technical/arxobject_specification.md](../technical/arxobject_specification.md)
> - Mesh protocol details: [technical/mesh_architecture.md](../technical/mesh_architecture.md)
> - Slow-bleed progressive detail: [technical/slow_bleed_architecture.md](../technical/slow_bleed_architecture.md)

## Vision Statement

Arxos is the universal building protocol that unifies CAD, BAS, IoT, and field operations through a lightweight terminal+AR interface using 13-byte ArxObjects transmitted over packet radio mesh networks.

**Core Philosophy**: Arxos routes building intelligence, it doesn't process it.

## The Complete Stack

```
┌────────────────────────────────────────────────────────┐
│                    FIELD LAYER                         │
│   Maintenance Tech → iPhone AR → LiDAR → Perception    │
└────────────────────────┬───────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│                 INTERFACE LAYER                        │
│          Point Cloud → ASCII Art → Terminal            │
│     "ROOM_205: 20x15ft, 4_OUTLETS, 2_WINDOWS"         │
└────────────────────────┬───────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│               Arxos PROTOCOL LAYER                     │
│         ASCII ↔ ArxObject (13 bytes) ↔ Routing        │
│      Building Intelligence as Lightweight Seeds        │
└────────────────────────┬───────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│                 TRANSPORT LAYER                        │
│            LoRa Packet Radio Mesh (915MHz)            │
│                 13 bytes × 19 per packet               │
└────────────────────────┬───────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│               INTEGRATION LAYER                        │
│    Revit (CAD) | Honeywell (BAS) | IoT | Automation   │
│           All speaking ArxObject protocol              │
└────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. **Stay Light**
- 2-5MB binary size maximum
- No GPU dependencies
- No heavy processing in core
- 13-byte ArxObjects only

### 2. **Terminal-First**
- Everything is ASCII at the interface
- Human-readable commands
- Local serial/BLE as primary interaction
- AR as visual extension of terminal

### 3. **Universal Protocol**
- ArxObjects are the lingua franca
- Every system speaks through ASCII conversion
- Packet radio for resilient mesh networking
- No proprietary protocols

## Information Flow Patterns

### Field → Network (Capture)
```
1. Tech identifies issue via AR
2. iPhone captures spatial data
3. External processor → ASCII description
4. Arxos converts ASCII → ArxObject (13 bytes)
5. LoRa broadcasts to mesh
6. Systems receive and act
```

### Network → Field (Query)
```
1. System generates alert
2. Converts to ArxObject
3. Mesh routes to nearest tech
4. ArxOS converts ArxObject → ASCII
5. Terminal displays human-readable
6. AR overlays in physical space
```

## The ArxObject Protocol

### Structure (13 bytes)
```rust
pub struct ArxObject {
    building_id: u16,    // Which building (2 bytes)
    object_type: u8,     // What type (1 byte)
    x: u16,             // Position in mm (2 bytes)
    y: u16,             // Position in mm (2 bytes)
    z: u16,             // Position in mm (2 bytes)
    properties: [u8; 4], // Type-specific data (4 bytes)
}
```

### Compression Ratio
- Input: 1GB point cloud
- ASCII: 100KB feature description
- ArxObject: 13 bytes seed
- Ratio: 10,000,000:1

## ASCII Interface Specification

### Input Format
```
OBJECT_TYPE @ (X, Y, Z)
PROPERTY: VALUE
PROPERTY: VALUE
```

### Example Translations
```
"OUTLET @ (10.5, 2.3, 1.2)m" → ArxObject {
    building_id: current,
    object_type: 0x15,  // OUTLET
    x: 10500, y: 2300, z: 1200,
    properties: [0, 0, 0, 0]
}

"LEAK @ PIPE_J7 SEVERITY:HIGH" → ArxObject {
    building_id: current,
    object_type: 0x45,  // LEAK
    x: pipe_j7.x, y: pipe_j7.y, z: pipe_j7.z,
    properties: [7, 3, 0, 0]  // J7, HIGH
}
```

## Module Responsibilities

### Core Modules (Keep Light)

#### `/src/core/arxobject.rs`
- 13-byte structure definition
- Serialization/deserialization
- Basic validation

#### `/src/core/ascii_bridge.rs` (NEW)
- ASCII → ArxObject conversion
- ArxObject → ASCII rendering  
- Terminal command parsing

#### `/src/core/mesh_router.rs` (NEW)
- Routing table management
- Flow control
- Mesh topology

#### `/src/core/transport/`
- LoRa packet radio
- Mesh networking
- No heavy protocols

### External Processors (Move Out)

#### Point Cloud Processing
- Move to separate service
- Communicates via ASCII only
- Not part of ArxOS core

#### Graphics Rendering
- External AR renderer
- Receives ArxObjects
- Not in core

#### Neural Networks
- External AI service
- Sends results as ASCII
- Not in core

## Deployment Architecture

### School Building Setup
```
Maintenance Room:
├── Raspberry Pi ($35)
│   ├── ArxOS Core (2MB)
│   ├── LoRa Dongle ($25)
│   └── Local Terminal Service (Serial/BLE)
│
├── Existing Infrastructure:
│   ├── WiFi Network
│   ├── iPads/iPhones (AR)
│   └── Desktop Terminals
│
└── External Services (Optional, offline-prepared):
    ├── Point Cloud Processor
    ├── Revit API Bridge
    └── BAS Gateway
```

### District Mesh Topology
```
Elementary_A ←→ Elementary_B ←→ Middle_School
      ↓              ↓              ↓
   [LoRa]         [LoRa]         [LoRa]
      ↓              ↓              ↓
High_School ←→ District_Office ←→ Maintenance
```

## Performance Targets

### Latency
- ASCII → ArxObject: <1ms
- Mesh routing decision: <5ms  
- Packet transmission: <50ms
- End-to-end: <100ms

### Throughput
- 19 ArxObjects per LoRa packet
- 250kbps raw LoRa bandwidth
- ~1000 objects/second theoretical
- 100 objects/second practical

### Resource Usage
- RAM: <50MB active
- CPU: <5% on Raspberry Pi
- Storage: <10MB + cache
- Network: Optimized for narrow band

## Security Model

### Authentication
- Local pairing (BLE) or device allowlist (serial)
- Mesh uses rolling codes
- ArxObjects are signed

### Authorization  
- Building-based isolation
- Role-based access (Tech, Admin, View)
- Audit trail via ArxObject log

### Encryption
- BLE link-layer or serial over authenticated channel
- AES-128 for LoRa packets
- Optional quantum resistance

## Development Priorities

### Phase 1: Core Protocol (Current)
- [x] ArxObject 13-byte structure
- [x] Basic mesh routing
- [x] LoRa transport
- [ ] ASCII bridge completion
- [ ] Terminal interface

### Phase 2: Field Integration
- [ ] iPhone AR capture app
- [ ] ASCII art generator
- [ ] Terminal UI enhancement
- [ ] Mesh topology visualization

### Phase 3: System Bridges
- [ ] Revit API adapter
- [ ] BAS protocol converter
- [ ] IoT gateway
- [ ] Automation webhooks

### Phase 4: Scale
- [ ] Multi-building mesh
- [ ] District-wide routing
- [ ] Cloud processor integration
- [ ] Performance optimization

## Success Metrics

### Technical
- Binary size <5MB ✓
- Latency <100ms
- 10,000:1 compression ✓
- Runs on Raspberry Pi

### Deployment
- <$100 per building
- <1 hour setup
- No specialized training
- Works with existing devices

### Operational
- 90% issue capture via AR
- 50% reduction in dispatch time
- Unified building intelligence
- Real-time mesh updates

## Testing Strategy

### Unit Tests
- ArxObject serialization
- ASCII parsing
- Routing logic
- Mesh algorithms

### Integration Tests
- Terminal → ArxObject → LoRa
- AR → ASCII → ArxObject
- Full round-trip flows
- Multi-node mesh

### Field Tests
- Real building deployment
- Actual maintenance workflows
- Network reliability
- User acceptance

## Migration Path

### From Current Codebase
1. Remove heavy processing modules
2. Extract to external services
3. Enhance ASCII bridge
4. Simplify to routing only

### For Buildings
1. Deploy single Raspberry Pi
2. Connect LoRa dongle
3. Local terminal configuration (serial/BLE)
4. Join mesh network
5. Begin AR capture

## API Specification

### Terminal Commands
```bash
# Capture from AR
$ arxos capture
> Scanning...
> Found: OUTLET @ (10.5, 2.3, 1.2)m

# Query building
$ arxos query "outlets in room 205"
> OUTLET_1 @ (10.5, 2.3, 1.2)m
> OUTLET_2 @ (14.2, 2.3, 1.2)m

# Send to mesh
$ arxos broadcast "LEAK @ PIPE_J7"
> Converting to ArxObject[13B]
> Broadcasting via LoRa...
> Acknowledged by 3 nodes

# Monitor mesh
$ arxos mesh status
> Nodes: 12 active
> Throughput: 47 obj/sec
> Latency: 23ms avg
```

### ArxObject Protocol
```rust
trait ArxProtocol {
    fn from_ascii(text: &str) -> Result<ArxObject>;
    fn to_ascii(&self) -> String;
    fn to_bytes(&self) -> [u8; 13];
    fn from_bytes(bytes: &[u8; 13]) -> Self;
}
```

## Conclusion

ArxOS is not a building processor - it's a building intelligence router. By staying light and focusing on the flow of 13-byte seeds through mesh networks, we enable any building to join the network for <$100 with existing devices.

The magic is in the simplicity: **Terminal + AR + Radio + Seeds = Universal Building Intelligence**