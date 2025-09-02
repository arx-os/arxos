# ArxOS Engineering Design & Architecture
**Project:** Building Intelligence Operating System  
**Version:** 2.0  
**Date:** December 2024

## Executive Summary

ArxOS transforms building data capture from expensive professional surveys to crowd-sourced intelligence using iPhone LiDAR and mesh networking. The system provides real-time building intelligence accessible via terminal interfaces while maintaining complete offline operation through RF mesh networks.

**Key Innovation:** ArxObjects semantic compression converts 50MB LiDAR point clouds into 13-byte queryable building data (10,000:1 compression ratio), enabling transmission over low-bandwidth packet radio while preserving building intelligence.

## Core Architecture

### Technology Stack
- **Rust:** Core processing engine (point cloud → ArxObjects → ASCII rendering)
- **SQLite:** Local data storage with R-Tree spatial indexing
- **LoRa Mesh:** Mesh networking (2km range, completely offline)
- **ESP32:** Pure Rust firmware for mesh nodes

### System Requirements
- **Mesh Node:** ESP32 + LoRa module + Solar power
- **Total Node Cost:** $25-85 per deployment
- **Power Usage:** 0.1-2W (solar compatible)
- **Software Footprint:** 1-5MB Rust binary + SQLite database
- **Storage per Building:** 15KB-100MB depending on detail level

## Data Flow Architecture

```
iPhone LiDAR Scan → ArxObjects → ASCII Terminal → SQLite Storage → LoRa Mesh
       ↓                ↓              ↓              ↓              ↓
   20-second      Semantic      Terminal        Spatial      Mesh Network
     capture     compression    interface      indexing     propagation
       ↓                ↓              ↓              ↓              ↓
  Room layout    13-byte building   Query/control   Local cache   Data sharing
```

### Bidirectional Intelligence Flow
```
LiDAR Scan → ArxObjects → Terminal Interface → SQL Storage → Mesh Network
     ↑                                                             ↓
iPhone Camera ←←← Terminal Queries ←←← Local Interfaces ←←← Data Consumers
```

## User Interface Strategy

### Terminal-First Access Design

**Problem Statement:** Different users need different interfaces - facilities managers want terminal power, contractors want visual simplicity, emergency responders need instant access.

**Solution:** Terminal-only interface with ASCII visualization for all users, maintaining complete air-gap security.

### Interface Types

#### 1. Desktop Terminal Interface
**Target Users:** Facilities managers, IT administrators, power users  
**Access Method:** USB LoRa dongle or Bluetooth connection to mesh network  
**Capabilities:**
- Complex building queries and automation
- System administration and configuration
- Bulk data operations and exports
- ASCII visualization of building systems

**Example Usage:**
```bash
arxos connect /dev/ttyUSB0  # Connect via USB LoRa dongle
arx> query "outlets circuit:B-7"
arx> query "equipment type:hvac floor:2"
arx> scan room:205
arx> status
```

#### 2. Mobile Terminal Interface
**Target Users:** Field workers, contractors, emergency responders  
**Access Method:** Bluetooth connection to nearby mesh node  
**Capabilities:**
- Terminal interface for building queries
- LiDAR scanning for building features
- Real-time mesh network status
- Command history and navigation

**Mobile Workflow:**
1. Open ArxOS mobile app
2. Connect to nearby mesh node via Bluetooth
3. Use terminal interface for building queries
4. Switch to LiDAR tab for 3D scanning
5. Scan data automatically sent to mesh network

#### 3. ASCII Visualization
**Target Users:** All users - visual representation of building data  
**Access Method:** Built into terminal interface  
**Capabilities:**
- ASCII art representation of building systems
- Real-time building data visualization
- Interactive system overlays
- Mobile-optimized display

## Hardware Architecture

### Mesh Node Configuration
Each ESP32 mesh node provides:
- **LoRa Radio:** Long-range mesh networking (2km urban, 10km rural)
- **Bluetooth:** Local device connections
- **Terminal Interface:** Command-line access for power users
- **Processing Power:** Local ArxObject queries and spatial indexing

### Connection Options

**Option 1: USB LoRa Dongle (Preferred)**
- Direct USB connection to user's computer
- No network configuration required
- Works with any computer with USB port
- Complete air-gap security

**Option 2: Bluetooth Connection**
- Wireless connection to nearby mesh node
- No network configuration required
- Works with mobile devices and laptops
- Range limited to ~10 meters

**Option 3: Direct Serial Connection**
- Direct serial connection to mesh node
- Used for debugging and configuration
- Requires physical access to node
- Complete air-gap security

## Security Architecture

### Air-Gapped Security Model
- **No Internet:** System never connects to the internet
- **Local Mesh Only:** All communication via LoRa/Bluetooth mesh networks
- **No SSH/TCP:** No traditional network protocols
- **Physical Isolation:** Complete separation from internet infrastructure

### Data Privacy
- **No Cloud:** No data sent to external servers
- **Local Storage:** All data stored locally on mesh nodes
- **User Control:** Users control all data sharing
- **Audit Trail:** Complete mesh communication logging

### Access Control
- **Node ID Authentication:** Mesh nodes use unique identifiers
- **Bluetooth Pairing:** Secure pairing for local connections
- **Encrypted Communication:** All mesh communication encrypted
- **Permission-Based:** Explicit user permissions required

## Deployment Architecture

### Building-Level Deployment
```
┌─────────────────────────────────────────────────────────────────┐
│                    BUILDING INTELLIGENCE NETWORK               │
├─────────────────────────────────────────────────────────────────┤
│  Gateway Node (ESP32) - Building coordinator                   │
│  ├── LoRa Mesh (915MHz) - Building-to-building communication   │
│  ├── Bluetooth - Local device connections                      │
│  ├── Database - Local building intelligence storage            │
│  └── Terminal Interface - Command-line access                  │
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

### District-Level Deployment
```
┌─────────────────────────────────────────────────────────────────┐
│                    SCHOOL DISTRICT NETWORK                     │
├─────────────────────────────────────────────────────────────────┤
│  District Gateway - Inter-building coordination                │
│  ├── High-power LoRa - District-wide communication             │
│  ├── Building Gateways - Individual building networks          │
│  └── District Database - Cross-building intelligence           │
├─────────────────────────────────────────────────────────────────┤
│  Building Networks - Individual building intelligence           │
│  ├── Building A - Complete building network                    │
│  ├── Building B - Complete building network                    │
│  └── Building C - Complete building network                    │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### LoRa Mesh Performance
- **Range:** 2km urban, 10km rural
- **Data Rate:** 0.3-50 kbps (perfect for 13-byte ArxObjects)
- **Latency:** 100ms-2s per packet
- **Power:** Ultra-low power consumption
- **Reliability:** Mesh redundancy provides high reliability

### System Performance
- **Query Response:** < 1 second for local queries
- **Mesh Propagation:** < 5 seconds for district-wide queries
- **LiDAR Processing:** Real-time on-device processing
- **Database Queries:** Sub-millisecond spatial queries
- **ASCII Rendering:** Real-time building visualization

## Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-4)
- [ ] Rust core library with ArxObject protocol
- [ ] ESP32 firmware with LoRa mesh networking
- [ ] Terminal interface implementation
- [ ] Basic database and spatial indexing

### Phase 2: Mobile Integration (Weeks 5-8)
- [ ] iOS mobile app with terminal interface
- [ ] LiDAR scanning integration
- [ ] Bluetooth mesh connection
- [ ] ArxObject generation from point clouds

### Phase 3: Mesh Network (Weeks 9-12)
- [ ] Multi-node mesh networking
- [ ] Packet routing and forwarding
- [ ] Network discovery and management
- [ ] Security and encryption

### Phase 4: Production Deployment (Weeks 13-16)
- [ ] Hardware integration testing
- [ ] Performance optimization
- [ ] Documentation and training
- [ ] Pilot deployment

## Critical Success Factors

### Technical Requirements
1. **Air-Gap Compliance:** No internet connectivity ever
2. **Terminal-Only Interface:** No web interfaces or SSH
3. **Pure Rust Implementation:** Consistent tech stack
4. **Mesh Network Reliability:** Robust packet routing
5. **LiDAR Integration:** Real-time point cloud processing

### User Experience Requirements
1. **Simple Connection:** USB dongle or Bluetooth pairing
2. **Familiar Interface:** Terminal commands for power users
3. **Visual Feedback:** ASCII art building visualization
4. **Mobile Support:** Terminal + LiDAR on mobile devices
5. **Offline Operation:** Full functionality without internet

## Risk Mitigation

### Technical Risks
- **Mesh Network Reliability:** Redundant nodes and routing
- **LiDAR Processing:** Optimized algorithms and hardware
- **Battery Life:** Low-power design and solar charging
- **Data Integrity:** Checksums and error correction

### User Adoption Risks
- **Learning Curve:** Terminal interface may require training
- **Hardware Requirements:** USB dongles or Bluetooth devices
- **Mobile Limitations:** LiDAR only available on newer iPhones
- **Network Coverage:** Mesh nodes must be properly distributed

## Conclusion

ArxOS represents a fundamental shift in building intelligence architecture. By creating a universal, air-gapped protocol for building intelligence, ArxOS enables every structure on Earth to share intelligence through mesh networks, creating a global building intelligence infrastructure that is secure, scalable, and future-proof.

The clean architecture ensures that ArxOS remains simple, maintainable, and aligned with the core philosophy of routing building intelligence rather than processing it. This approach enables rapid development, easy deployment, and long-term sustainability of the building intelligence network.
