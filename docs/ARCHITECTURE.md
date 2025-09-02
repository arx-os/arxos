# ArxOS Final Architecture

## Overview

ArxOS is a building intelligence operating system that creates and utilizes digital twins through the "arxobject" - a universal 13-byte protocol that enables every structure on Earth to share intelligence through packet radio mesh networks.

## Core Philosophy

> **"ArxOS routes building intelligence, it doesn't process it."**

ArxOS provides the infrastructure for building intelligence, similar to how TCP/IP provides the infrastructure for internet communication. The system is designed to be completely air-gapped, operating entirely through local mesh networks without any internet connectivity.

## Architecture Principles

### 1. Air-Gapped Design
- **No Internet**: System never connects to the internet
- **Local Mesh Only**: All communication via LoRa/Bluetooth mesh networks
- **No SSH/TCP**: No traditional network protocols
- **Secure by Design**: Physical isolation provides security

### 2. Universal Protocol
- **13-byte ArxObjects**: Universal building intelligence format
- **Mesh Routing**: Automatic packet routing through building networks
- **Cross-Platform**: Works on any device with mesh connectivity
- **Future-Proof**: Protocol designed for global building networks

### 3. Terminal-First Interface
- **CLI Primary**: Terminal interface for power users
- **ASCII Visualization**: Building data rendered as ASCII art
- **Mobile Terminal**: Mobile app provides terminal + camera
- **No Web UI**: No web interfaces to maintain air-gap

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                             │
├─────────────────────────────────────────────────────────────────┤
│  Desktop Terminal (Rust)  │  Mobile Terminal (Swift)          │
│  - CLI Commands           │  - Terminal Interface             │
│  - ASCII Visualization    │  - LiDAR Scanning                 │
│  - Mesh Connection        │  - Bluetooth Mesh                 │
└─────────────────┬─────────────────┬─────────────────────────────┘
                  │                 │
                  ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ARXOS SERVICE (Rust)                        │
├─────────────────────────────────────────────────────────────────┤
│  - ArxObject Protocol     │  - Meshtastic Client               │
│  - Database Engine        │  - Building Intelligence Engine    │
│  - Query Engine           │  - Document Parser                 │
└─────────────────┬─────────────────┬─────────────────────────────┘
                  │                 │
                  ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MESHTASTIC HARDWARE                         │
├─────────────────────────────────────────────────────────────────┤
│  - Standard Meshtastic     │  - LoRa Mesh (915MHz)             │
│  - ESP32 + LoRa Radio      │  - Building-to-Building           │
│  - Unchanged Firmware      │  - Proven Mesh Protocol           │
└─────────────────┬─────────────────┬─────────────────────────────┘
                  │                 │
                  ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUILDING INTELLIGENCE                       │
├─────────────────────────────────────────────────────────────────┤
│  - Electrical Systems     │  - HVAC Systems                    │
│  - Security Systems       │  - Fire Safety                     │
│  - Structural Data        │  - Environmental Sensors           │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Core Technologies
- **Rust**: Backend, terminal, Meshtastic client, building intelligence
- **Swift**: iOS mobile app (terminal + LiDAR)
- **Meshtastic**: Standard mesh networking (unchanged)

#### Hardware Platforms
- **ESP32**: Standard Meshtastic hardware (unchanged firmware)
- **LoRa**: Long-range mesh communication (915MHz US, 868MHz EU)
- **Meshtastic**: Proven mesh networking platform
- **Bluetooth**: Local device communication
- **iPhone LiDAR**: 3D scanning for building features

#### Communication Protocols
- **LoRa Mesh**: Building-to-building communication
- **Bluetooth**: Device-to-node communication
- **ArxObject Protocol**: Universal 13-byte building intelligence format

## Component Architecture

### 1. ArxOS Core (Rust)

#### ArxObject Protocol
```rust
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

#### Mesh Network Manager
```rust
pub struct ArxOSMesh {
    radio: Sx126x,                    // LoRa radio
    database: Database,               // Local building database
    node_id: u16,                    // This node's ID
    neighbors: HashMap<u16, NeighborInfo>, // Known neighbors
}
```

### 2. Terminal Interface (Rust)

#### Command System
```rust
pub enum ArxOSCommand {
    Query { query: String },           // Query building data
    Scan { room: Option<String> },     // Scan room (mobile app)
    Connect { device: Option<String> }, // Connect to mesh
    Status,                            // Show network status
    Help,                              // Show help
    Exit,                              // Exit application
}
```

### 3. Mobile App (Swift)

#### Terminal Interface
```swift
struct TerminalView: View {
    @State private var commandInput = ""
    @State private var outputLines: [String] = []
    @EnvironmentObject var meshClient: MeshClient
    
    // Terminal command processing
    // Real-time mesh network status
    // Command history and navigation
}
```

#### LiDAR Scanning
```swift
struct CameraView: View {
    @State private var isScanning = false
    @State private var scanProgress: Double = 0.0
    
    // LiDAR point cloud capture
    // Real-time 3D processing
    // ArxObject generation
    // Automatic mesh transmission
}
```

### 4. Firmware (Pure Rust)

#### ESP32 Firmware
```rust
#![no_std]
#![no_main]

use esp_hal::{clock::ClockControl, gpio::IO, peripherals::Peripherals};
use sx126x::Sx126x;
use arxos_core::{ArxObject, Database, mesh_network::ArxOSMesh};

#[entry]
fn main() -> ! {
    // Initialize LoRa radio
    // Initialize ArxOS database
    // Start mesh network
    // Main loop: receive packets, process queries, send responses
}
```

## Data Flow

### 1. User Query Flow
```
User Terminal → ArxOS Core → Mesh Network → Building Nodes → Response
     ↓              ↓             ↓              ↓            ↓
  "query room:205" → Parse → LoRa Packet → ESP32 Node → ArxObjects
     ↓              ↓             ↓              ↓            ↓
  ASCII Display ← Format ← Mesh Response ← Database Query ← Local Data
```

### 2. LiDAR Scan Flow
```
iPhone LiDAR → Point Cloud → ArxObject Generation → Mesh Transmission
     ↓              ↓              ↓                    ↓
  3D Scan → ML Processing → 13-byte Objects → LoRa Broadcast
     ↓              ↓              ↓                    ↓
  Building Data → Spatial Index → Mesh Network → All Nodes
```

## Security Architecture

### Air-Gapped Security
- **Physical Isolation**: No internet connectivity
- **Mesh Encryption**: All mesh communication encrypted
- **Local Processing**: All data processing on-device
- **Permission-Based**: Explicit user permissions required

### Data Privacy
- **No Cloud**: No data sent to external servers
- **Local Storage**: All data stored locally on mesh nodes
- **User Control**: Users control all data sharing
- **Audit Trail**: Complete mesh communication logging

## Deployment Architecture

### Building-Level Deployment
```
┌─────────────────────────────────────────────────────────────────┐
│                    BUILDING INTELLIGENCE NETWORK               │
├─────────────────────────────────────────────────────────────────┤
│  Gateway Node (ESP32) - Building coordinator                   │
│  ├── LoRa Mesh (915MHz) - Building-to-building communication   │
│  ├── Bluetooth - Local device connections                      │
│  ├── Ethernet - Local network integration                      │
│  └── Database - Local building intelligence storage            │
├─────────────────────────────────────────────────────────────────┤
│  Room-Level Nodes (ESP32) - Local intelligence                 │
│  ├── Outlet Nodes - Electrical monitoring/control              │
│  ├── Sensor Nodes - Environmental monitoring                   │
│  ├── Door Nodes - Access control and monitoring                │
│  └── Panel Nodes - Electrical panel monitoring                 │
├─────────────────────────────────────────────────────────────────┤
│  User Devices - Field interaction                              │
│  ├── Desktop/Laptop - Terminal interface                       │
│  ├── Mobile Devices - Terminal + LiDAR scanning                │
│  └── LoRa Dongles - Direct mesh connection                     │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### LoRa Mesh Performance
- **Range**: 2km urban, 10km rural
- **Data Rate**: 0.3-50 kbps (perfect for 13-byte ArxObjects)
- **Latency**: 100ms-2s per packet
- **Power**: Ultra-low power consumption
- **Reliability**: Mesh redundancy provides high reliability

### System Performance
- **Query Response**: < 1 second for local queries
- **Mesh Propagation**: < 5 seconds for district-wide queries
- **LiDAR Processing**: Real-time on-device processing
- **Database Queries**: Sub-millisecond spatial queries
- **ASCII Rendering**: Real-time building visualization

## Conclusion

ArxOS represents a fundamental shift in building intelligence architecture. By creating a universal, air-gapped protocol for building intelligence, ArxOS enables every structure on Earth to share intelligence through mesh networks, creating a global building intelligence infrastructure that is secure, scalable, and future-proof.

The clean architecture ensures that ArxOS remains simple, maintainable, and aligned with the core philosophy of routing building intelligence rather than processing it. This approach enables rapid development, easy deployment, and long-term sustainability of the building intelligence network.
