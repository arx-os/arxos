---
title: Technical Architecture: RF-Only Mesh Intelligence
summary: System design overview for the RF-only, terminal-first ArxOS architecture with links to canonicals.
owner: Lead Architecture
last_updated: 2025-09-04
---
# Technical Architecture: RF-Only Mesh Intelligence

> Scope: System design, constraints (RF-only, air-gapped), component interfaces, and data flows. Audience: lead architects and core engineers.
>
> Owner: Lead Architecture.

> Canonicals: `../technical/arxobject_specification.md` (13-byte), `../technical/mesh_architecture.md` (deep dive), `../technical/TERMINAL_API.md` (commands), `../12-protocols/MESH_PROTOCOL.md` (protocol). This page is an overview index.

## Pure Air-Gapped Building Operations

Arxos achieves complete internet independence through a radically simplified architecture that operates entirely over RF mesh networks. No cloud, no web, no internet vulnerabilities.

### 📖 Section Contents

Core:
1. **[Network Architecture](NETWORK_ARCHITECTURE.md)**
2. **[Flow Orchestrator](FLOW_ORCHESTRATOR.md)**
3. **[Engineering Design (Clean)](ENGINEERING_DESIGN_CLEAN.md)**
4. **[Complete Data Flow](COMPLETE_DATA_FLOW.md)**
5. **[Service Architecture](SERVICE_ARCHITECTURE.md)**

Data & Models:
6. **[Data Architecture](DATA_ARCHITECTURE.md)**
7. **[Business Data Model](DATA_MODEL_BUSINESS.md)**

Networking Details:
8. **[Mesh VLAN Architecture](MESH_VLAN_ARCHITECTURE.md)**
9. **[Network Topology Spec](NETWORK_TOPOLOGY_SPECIFICATION.md)**

Repositories:
10. **[Building Repository](BUILDING_REPOSITORY.md)**
11. **[Traffic Flow Architecture](TRAFFIC_FLOW_ARCHITECTURE.md)**

Legacy/Notes:
12. **[Old Architecture Notes](OLD_ARCHITECTURE.md)**

Related:
13. **[RF-Only Software Updates](../15-rf-updates/README.md)**

## 🎯 The Architecture in One Page

### The Problem with Internet-Connected Systems
```
Traditional "Smart" Building:
- Cloud dependency = Single point of failure
- Internet requirement = Cyber attack surface
- Web interfaces = Complex, slow, vulnerable
- Monthly fees = Ongoing operational cost
- Data leaves building = Privacy nightmare
```

### The Arxos RF-Only Solution
```
Arxos Air-Gapped Architecture:
- RF mesh network = No internet needed
- Local processing = Data never leaves
- Terminal interface = Fast, secure, proven
- One-time cost = No subscriptions
- Perfect privacy = Air-gapped security
```

## 🏗️ System Architecture

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
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Arxos Core (Rust Binary)              │    │
│  │  • 13-byte ArxObject protocol                   │    │
│  │  • Semantic compression engine                  │    │
│  │  • Building intelligence logic                  │    │
│  │  • BILT token calculations                      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │      Local Terminal Service (TTY/BLE)           │    │
│  │  • Terminal interface for all clients           │    │
│  │  • Camera data receiver for iOS/Android         │    │
│  │  • Command processing                           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │         Local SQLite Database                   │    │
│  │  • ArxObject storage                            │    │
│  │  • Building intelligence                        │    │
│  │  • BILT transactions                            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└────────────────┬─────────────────────────────────────────┘
                 │ LoRa Radio (NO INTERNET)
┌────────────────▼─────────────────────────────────────────┐
│              RF MESH NETWORK LAYER                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Building A ←──LoRa──→ Building B ←──LoRa──→ Building C │
│      📡                    📡                    📡      │
│                                                          │
│  • Meshtastic protocol for routing                       │
│  • 915MHz ISM band (US) / 868MHz (EU)                   │
│  • 2-10km range between nodes                           │
│  • Automatic mesh healing and routing                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 💡 Key Architectural Decisions

### 1. Native Rust Everywhere (No WASM)
```rust
// Single Rust binary runs on mesh nodes
pub struct ArxosNode {
    core: ArxosCore,           // Building intelligence
    ssh_server: SSHServer,     // Terminal access
    lora_radio: LoRaMesh,      // RF networking
    database: SQLite,          // Local storage
}

// Compiles natively for each platform:
// - ARM for Raspberry Pi nodes
// - RISC-V for ESP32 nodes  
// - x86 for development
```

### 2. Local Terminal as Universal Interface
```bash
# Connect via serial or BLE
arx> connect serial://COM3
arx> connect ble://meshtastic-001

# Power users love terminal efficiency:
arx> query "outlets in room 127"
arx> control hvac --zone=3 --temp=72
arx> report --format=ascii

# Camera integration for iOS/Android:
arx> scan --room=127
> Opening camera for LiDAR scan...
```

### 3. RF-Only Communication
```rust
pub struct RFOnlyNetworking {
    // No IP stack needed:
    protocol: "Meshtastic over LoRa",
    frequency: "915MHz ISM band",
    bandwidth: "125-500kHz",
    data_rate: "0.3-27 kbps",
    
    // Perfect for 13-byte packets:
    packet_size: 13, // bytes
    transmission_time: 4, // milliseconds
    
    // No internet anywhere:
    internet_required: false,
    cloud_connection: None,
    web_interface: None,
}
```

## 🚀 Why This Architecture Wins

### Simplicity
- **One language**: Rust for everything
- **One protocol**: SSH for all clients  
- **One network**: RF mesh only
- **One database**: SQLite locally

### Security
- **Air-gapped**: No internet attack surface
- **Local terminal link**: Serial/BLE with authenticated pairing
- **Local-only**: Data never leaves building
- **Encrypted**: All RF traffic encrypted

### Reliability
- **No dependencies**: Works without internet
- **Self-healing**: Mesh routes around failures
- **Disaster-proof**: Operates during outages
- **Simple**: Fewer things to break

### Performance
| Component | Metric | Value |
|-----------|--------|-------|
| Node boot time | Cold start | <5 seconds |
| Terminal link | Latency | <100ms |
| Mesh routing | Hop time | <50ms |
| Database query | Response | <10ms |
| Camera scan | Processing | <2 seconds |

## 📊 Data Flow Examples

### Room Scanning Flow
```
1. User command: $ arxos scan --room=127
2. iPhone camera opens → Captures LiDAR data
3. Data sent via local link → Mesh node processes
4. Semantic compression → 50MB to 5KB
5. Store in SQLite → Local database
6. Broadcast via LoRa → Other nodes updated
7. Terminal shows result → ASCII floor plan
```

### HVAC Control Flow
```
1. User command: $ arxos control hvac --temp=72
2. Terminal service receives → Validates command
3. Create ArxObject → 13-byte packet
4. Broadcast via LoRa → Mesh network
5. HVAC node receives → Adjusts temperature
6. Confirmation packet → Returns via mesh
7. Terminal shows result → "Temperature set to 72°F"
```

## 🔧 Implementation Technologies

### Core Stack (Just 3 Technologies)
```yaml
Language:
  Rust: "All business logic"
  
Database:
  SQLite: "Local storage on each node"
  
Network:
  LoRa: "RF mesh networking"
  
# That's it. No web frameworks, no cloud services, no containers.
```

### Hardware Platforms
```yaml
Mesh Nodes:
  - ESP32 + LoRa: "$25 minimal node"
  - Raspberry Pi + LoRa: "$75 powerful node"
  
Client Devices:
  - iPhone/iPad: "Terminal client + camera (BLE)"
  - Android: "Terminal client + camera (BLE)"  
  - Laptop/Desktop: "Terminal client (serial)"
```

## 🎯 The Paradigm Shift

This isn't just removing internet connectivity. It's a fundamental rethinking:

1. **Terminal over GUI**: Power users prefer efficiency
2. **Mesh over Internet**: RF networks are more resilient
3. **Local over Cloud**: Privacy and security guaranteed
4. **Simple over Complex**: Three technologies beat fifty
5. **Air-gapped over Connected**: Security through isolation

## 📈 Scalability

```
Single Building:
- 10-50 nodes
- 1,000 ArxObjects
- 100GB storage

Campus:
- 500 nodes  
- 50,000 ArxObjects
- 5TB storage

City-wide:
- 10,000 nodes
- 1M ArxObjects  
- 100TB distributed

# All without internet. All air-gapped. All secure.
```

---

*"The constraint is the innovation. No internet forces elegance."*