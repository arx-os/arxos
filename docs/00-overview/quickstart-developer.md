# Developer Quick Start Guide

## From Zero to RF Mesh Intelligence in 30 Minutes

This guide gets you up and running with Arxos development. You'll build a working RF mesh node that operates completely air-gapped, with semantic compression and SSH terminal access.

## Prerequisites

```bash
# Required tools
- Rust 1.75+ (rustup.rs)
- SQLite 3.40+ (for spatial database)
- ESP32 toolchain (for mesh nodes)

# For iOS development
- Xcode 15+ with iOS 17 SDK
- Swift 5.9+

# Optional but recommended
- Visual Studio Code with rust-analyzer
- TablePlus or DB Browser for SQLite
- Terminal emulator with SSH support
```

## 1. Environment Setup (5 minutes)

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Install Rust if needed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Add embedded targets for mesh nodes
rustup target add thumbv7em-none-eabihf    # ARM Cortex-M4
rustup target add riscv32imc-unknown-none-elf  # ESP32-C3

# Install ESP32 tools
cargo install espflash cargo-espflash

# Build all components
cargo build --all
```

### Project Structure

```
arxos/
├── src/
│   ├── core/              # Core library (13-byte protocol)
│   ├── terminal/          # SSH terminal client
│   └── embedded/          # ESP32 mesh node firmware
├── firmware/
│   └── esp32/            # LoRa mesh node
├── ios/
│   └── ArxosTerminal/    # iOS SSH + Camera app
├── migrations/           # SQLite database schema
└── hardware/            # PCB designs for mesh nodes
```

## 2. Build Your First Mesh Node (10 minutes)

### Core Library

```bash
# Build the core library
cd src/core
cargo build --release

# Run tests
cargo test

# Verify 13-byte ArxObject constraint
cargo test size_constraint_test -- --nocapture
```

### Example: Create an ArxObject

```rust
use arxos_core::{ArxObject, object_types};

fn main() {
    // Create an electrical outlet at position (1000, 2000, 1500)mm
    let outlet = ArxObject::new(
        0x4A7B,                    // Building ID
        object_types::OUTLET,      // Type
        1000, 2000, 1500          // Position in mm
    );
    
    // Serialize to 13 bytes for RF transmission
    let bytes = outlet.to_bytes();
    println!("ArxObject: {:?} ({} bytes)", bytes, bytes.len());
    
    // Query spatially
    if outlet.is_within_room(1000, 2000, 3000, 3000) {
        println!("Outlet found in room!");
    }
}
```

## 3. Deploy Mesh Node Firmware (5 minutes)

### Build for ESP32

```bash
cd firmware/esp32

# Configure for your region
# US: 915MHz, EU: 868MHz, AS: 923MHz
export LORA_FREQ=915

# Build firmware
cargo build --release --target riscv32imc-unknown-none-elf

# Flash to ESP32 (connect via USB)
espflash /dev/ttyUSB0 target/riscv32imc-unknown-none-elf/release/arxos-node
```

### Test Mesh Network

```bash
# Terminal 1: Start gateway node
./arxos-node --node-id 0x0001 --mode gateway

# Terminal 2: Start relay node
./arxos-node --node-id 0x0002 --mode relay

# Terminal 3: Connect via SSH
ssh arxos@localhost
arxos@mesh:~$ status
Building: Connected
Nodes: 2 online
RF Signal: -72 dBm
```

## 4. Database Setup (5 minutes)

### Initialize SQLite Database

```bash
# Create database with spatial schema
sqlite3 arxos.db < migrations/001_initial_schema.sql
sqlite3 arxos.db < migrations/002_spatial_functions.sql

# Test spatial queries
sqlite3 arxos.db "
SELECT COUNT(*) FROM arxobjects 
WHERE object_type = 1 
  AND x BETWEEN 1000 AND 2000
  AND y BETWEEN 1000 AND 2000;
"
```

## 5. Terminal Interface (5 minutes)

### Build and Run Terminal

```bash
# Build terminal client
cargo build --release --bin arxos

# Run in simulation mode
./target/release/arxos --simulate

# ASCII visualization appears
┌─────────────────────────────────────┐
│ FLOOR 2 - ARXOS MESH NODE 0x4A7B   │
├─────────────────────────────────────┤
│ [O]  [L]  [L]  [O]      [V]        │
│                                     │
│       ROOM 127 - CLASSROOM          │
│                                     │
│ [O]  [L]  [L]  [O]      [V]        │
└─────────────────────────────────────┘
O=Outlet  L=Light  V=Vent
```

### Query Building Intelligence

```bash
# Connect to mesh node
ssh arxos@mesh-node.local

# Query objects
arxos query "all outlets in room 127"
> Found 4 outlets at positions:
> - (1000, 1000, 300)
> - (1000, 3000, 300)
> - (3000, 1000, 300)
> - (3000, 3000, 300)

# Control systems (via RF)
arxos control lights --room=127 --state=off
> Command sent via RF mesh
> Acknowledged by node 0x0002
```

## 6. iOS App Integration (10 minutes)

### Simple Terminal + Camera App

```swift
// ArxosTerminalApp.swift
import SwiftUI
import NMSSH  // SSH library

struct ContentView: View {
    @State private var sshSession: NMSSHSession?
    @State private var showCamera = false
    
    var body: some View {
        VStack {
            // Terminal view
            TerminalView(session: sshSession)
            
            // Camera trigger button
            Button("Scan Room") {
                showCamera = true
            }
            .sheet(isPresented: $showCamera) {
                CameraView(onCapture: processLiDAR)
            }
        }
    }
    
    func processLiDAR(pointCloud: ARPointCloud) {
        // Compress on mesh node (not phone)
        let command = "arxos process-lidar"
        sshSession?.channel.write(pointCloud.data)
    }
}
```

### Build iOS App

```bash
cd ios/ArxosTerminal
xcodebuild -scheme ArxosTerminal -sdk iphoneos
```

## 7. Testing Your Setup (5 minutes)

### Integration Test

```bash
# Run all tests
cargo test --all

# Test mesh networking
cargo test --test mesh_integration

# Test SSH server
cargo test --test ssh_integration

# Verify RF-only (no internet)
cargo test --test airgap_verification
```

### Performance Metrics

```bash
# Compression test
./arxos test-compression sample-pointcloud.ply
> Input: 47.3 MB (1,234,567 points)
> Output: 4.7 KB (387 ArxObjects)
> Compression: 10,234:1
> Time: 127ms

# RF transmission test
./arxos test-rf-transmission
> Packet size: 13 bytes
> Transmission time: 12ms
> Range achieved: 2.7km
> Packet loss: 0.3%
```

## Common Development Tasks

### Add New Object Type

```rust
// In src/core/arxobject.rs
pub mod object_types {
    pub const FIRE_ALARM: u8 = 0x22;
}

// Usage
let alarm = ArxObject::new(
    building_id,
    object_types::FIRE_ALARM,
    x, y, z
);
```

### Create Database Migration

```sql
-- migrations/003_add_fire_alarms.sql
ALTER TABLE arxobjects 
ADD COLUMN last_tested DATE;

CREATE INDEX idx_fire_alarms 
ON arxobjects(object_type) 
WHERE object_type = 34;  -- 0x22 in decimal
```

### Deploy Firmware Update via RF

```bash
# Build update
cargo build --release --target riscv32imc-unknown-none-elf

# Sign with private key
arxos-sign target/release/arxos-node --key private.key

# Broadcast via RF (no internet!)
arxos-broadcast --file arxos-node.signed --priority high
> Broadcasting update via RF mesh
> Nodes acknowledging: 47/50
> Update will auto-install in 10 minutes
```

## Troubleshooting

### LoRa Not Working
```bash
# Check frequency for your region
# Wrong frequency = no communication
echo $LORA_FREQ  # Should be 915 (US) or 868 (EU)

# Verify antenna connected
# No antenna = no signal
```

### SSH Connection Failed
```bash
# Mesh nodes are on local network only
# No internet routing
ping mesh-node.local
nmap -p 22 mesh-node.local
```

### Database Issues
```bash
# Reset database
rm arxos.db
sqlite3 arxos.db < migrations/001_initial_schema.sql
```

## Next Steps

1. **Hardware**: Build physical mesh nodes with ESP32 + LoRa
2. **Deployment**: Install in real building for testing
3. **Gamification**: Implement BILT token rewards
4. **Scanning**: Integrate iPhone LiDAR capture

## Resources

- [RF Mesh Protocol Spec](../15-rf-updates/)
- [13-byte ArxObject Format](../02-arxobject/)
- [SSH Terminal Commands](../07-ios-integration/)
- [Hardware Designs](../../hardware/)

---

*Building the future of building intelligence - 100% air-gapped, 100% private*