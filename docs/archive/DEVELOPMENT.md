# Arxos Development Guide - RF-Only Architecture

## Building Air-Gapped Intelligence Systems

This guide helps you build and deploy Arxos mesh nodes that never touch the internet.

## 🚀 Prerequisites

### Required Tools
```bash
# 1. Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 2. Cross-compilation targets
rustup target add thumbv7em-none-eabihf  # For ARM Cortex-M4
rustup target add riscv32imc-unknown-none-elf  # For ESP32-C3
rustup target add aarch64-unknown-linux-gnu  # For Raspberry Pi

# 3. ESP32 tools (for firmware)
cargo install espflash cargo-espflash

# 4. Database tools
# Ubuntu/Debian:
sudo apt-get install sqlite3

# macOS:
brew install sqlite
```

## 🏗️ Project Structure

```
arxos/
├── src/
│   ├── core/              # Core library (13-byte protocol, mesh, SSH)
│   │   ├── arxobject.rs   # 13-byte object definition
│   │   ├── mesh_network.rs # RF mesh networking
│   │   ├── ssh_server.rs  # Terminal access
│   │   └── database.rs    # Local SQLite storage
│   ├── terminal/          # Terminal client
│   └── embedded/          # ESP32 firmware
├── firmware/
│   └── esp32/            # LoRa mesh node firmware
├── hardware/
│   ├── pcb/              # Open hardware designs
│   └── enclosures/       # 3D printable cases
├── ios/
│   └── ArxosTerminal/    # Simple SSH + Camera app
└── migrations/           # Database schema
```

## ⚡ Development Workflow

### 1. Build Core Library
```bash
# Build for development (native)
cargo build --package arxos-core

# Build for ESP32 embedded
cargo build --package arxos-core --target riscv32imc-unknown-none-elf --no-default-features

# Run tests
cargo test --workspace
```

### 2. Build Mesh Node Firmware
```bash
cd firmware/esp32

# Build for ESP32-C3 with LoRa
cargo build --release --target riscv32imc-unknown-none-elf

# Flash to device
espflash /dev/ttyUSB0 target/riscv32imc-unknown-none-elf/release/arxos-node
```

### 3. Set Up Database
```bash
# Create development database
sqlite3 dev.db < migrations/001_initial_schema.sql
sqlite3 dev.db < migrations/002_spatial_functions.sql

# Verify schema
sqlite3 dev.db ".tables"
```

### 4. Run Terminal Client
```bash
# Start terminal in simulation mode
cargo run --bin arxos-terminal -- --simulate

# Connect to real mesh node
cargo run --bin arxos-terminal -- --node-ip 192.168.1.100
```

## 📡 RF Mesh Network Setup

### Hardware Requirements
- ESP32 or ESP32-C3 board
- SX1262 LoRa module (915MHz US / 868MHz EU)
- Antenna (2dBi minimum)
- Power supply (USB or battery)

### Frequency Configuration
```rust
// In mesh_network.rs
pub const LORA_CONFIG: LoRaConfig = LoRaConfig {
    frequency: 915.0,  // US: 915MHz, EU: 868MHz
    bandwidth: 125,    // kHz
    spreading_factor: 9,
    tx_power: 20,      // dBm (check local regulations)
};
```

### Mesh Network Testing
```bash
# Deploy 3+ nodes for testing
# Node 1 (Gateway)
./arxos-node --node-id 0x0001 --mode gateway

# Node 2 (Relay)
./arxos-node --node-id 0x0002 --mode relay

# Node 3 (Endpoint)
./arxos-node --node-id 0x0003 --mode endpoint

# Monitor mesh status
arxos-cli mesh-status
> 3 nodes online
> Mesh topology: 0x0001 <-> 0x0002 <-> 0x0003
> Average RSSI: -72 dBm
```

## 🔒 SSH Server Configuration

### Start SSH Server on Mesh Node
```bash
# The mesh node runs an SSH server
# No configuration needed - it's built in

# Default credentials:
# Username: arxos
# Password: [building-specific]

# Connect from any SSH client:
ssh arxos@mesh-node.local
```

### Terminal Commands
```bash
# Building queries
arxos query "all outlets in room 127"
arxos query "emergency exits on floor 2"

# System control
arxos control hvac --zone=3 --temp=72
arxos control lights --room=127 --state=off

# Scanning (triggers camera on iOS)
arxos scan --room=127

# Status
arxos status
arxos mesh-status
arxos bilt-balance
```

## 🍎 iOS App Development

### Simple Terminal + Camera App
```swift
// Two components only:
// 1. SSH Terminal View
// 2. Camera View (LiDAR + AR)

// No complex logic - mesh node does everything
```

### Building iOS App
```bash
cd ios/ArxosTerminal
xcodebuild -scheme ArxosTerminal -sdk iphoneos
```

## 📊 Testing

### Unit Tests
```bash
# Run all tests
cargo test --all

# Test specific module
cargo test --package arxos-core mesh_network

# Test with output
cargo test -- --nocapture
```

### Integration Tests
```bash
# Test mesh networking
cargo test --test mesh_integration

# Test SSH server
cargo test --test ssh_integration

# Test database operations
cargo test --test database_integration
```

## 🚫 What NOT to Do

### Never Add These Dependencies
- ❌ Any HTTP/HTTPS libraries
- ❌ Cloud service SDKs
- ❌ Web frameworks
- ❌ REST API clients
- ❌ WebSocket libraries
- ❌ OAuth/JWT authentication
- ❌ Container orchestration

### Never Connect To
- ❌ Internet APIs
- ❌ Cloud databases
- ❌ Remote logging services
- ❌ Analytics platforms
- ❌ Update servers (use RF updates)

## 🔧 Troubleshooting

### LoRa Not Working
```bash
# Check frequency for your region
# US: 915MHz, EU: 868MHz, AS: 923MHz

# Verify antenna connection
# Poor antenna = no communication

# Check RSSI levels
arxos-cli check-rssi
> Node 0x0002: -65 dBm (Good)
> Node 0x0003: -89 dBm (Weak)
```

### SSH Connection Failed
```bash
# Ensure on same local network
# Mesh nodes don't use internet

# Check node is running SSH server
nmap -p 22 mesh-node.local

# Verify credentials
ssh -v arxos@mesh-node.local
```

### Database Issues
```bash
# Check database exists
ls -la *.db

# Verify schema
sqlite3 arxos.db ".schema"

# Reset database
rm arxos.db
sqlite3 arxos.db < migrations/001_initial_schema.sql
```

## 📡 RF Update Distribution

### Building Updates
```bash
# Create signed update
cargo build --release
arxos-sign target/release/arxos-node --key private.key

# Broadcast via RF (from HQ)
arxos-broadcast --file arxos-node.signed --priority normal
```

### Receiving Updates (Automatic)
```
Updates propagate through mesh network
No internet connection required
Cryptographically verified before installation
```

## 🎯 Development Philosophy

1. **No Internet, Ever**: If it needs internet, redesign it
2. **Terminal First**: Power users prefer efficiency
3. **Local Processing**: All intelligence on mesh nodes
4. **RF Only**: Updates, support, everything via RF
5. **Simple**: Complexity is the enemy of security

## 📚 Key Files to Study

- `src/core/arxobject.rs` - 13-byte protocol
- `src/core/mesh_network.rs` - RF mesh networking
- `src/core/ssh_server.rs` - Terminal interface
- `src/core/semantic_compression.rs` - 10,000:1 compression
- `migrations/*.sql` - Database schema

---

*"Building intelligence that works in bunkers, during blackouts, and after the apocalypse."*