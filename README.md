# ArxOS - The Planetary Nervous System for Buildings

> **"ArxOS routes building intelligence, it doesn't process it."**

## What is ArxOS?

ArxOS is the TCP/IP of buildings - a universal protocol that enables every structure on Earth to share intelligence through 13-byte seeds flowing through packet radio mesh networks. 

**Core Innovation**: School districts become backbone nodes for a global building intelligence network, maintaining complete data sovereignty while enabling planetary-scale connectivity through zero-knowledge routing.

## The Vision

- **Stay Light**: <5MB binary, runs on Raspberry Pi ($35)
- **Terminal First**: ASCII is the interface
- **Universal Protocol**: 13 bytes for everything  
- **Route, Don't Process**: External services do heavy lifting
- **Secure by Default**: Zero-knowledge routing protects privacy

## Quick Start

```bash
# Clone and build
git clone https://github.com/arxos/arxos.git
cd arxos
cargo build --release

# Run terminal client
cargo run --bin arxos

# Connect to mesh node
ssh arxos@mesh-node.local -p 2222
```

## Core Features

- **🔒 Air-Gapped Security**: No internet connection ever required
- **📡 RF Mesh Network**: LoRa 915MHz (US) / 868MHz (EU) with 10km range
- **🗜️ 10,000:1 Compression**: 50MB point clouds → 5KB ArxObjects
- **🖥️ SSH Terminal Access**: Universal interface, no special software
- **📱 iPhone LiDAR**: 20-second scans with RoomPlan API
- **📄 Document Parsing**: PDF/IFC → ASCII floor plans
- **🔐 Ed25519 Signatures**: Cryptographic security for all updates

## Documentation

- **[docs/01-vision/VISION.md](docs/01-vision/VISION.md)** - Master vision document (START HERE)
- **[docs/03-architecture/NETWORK_ARCHITECTURE.md](docs/03-architecture/NETWORK_ARCHITECTURE.md)** - Zero-knowledge routing & security
- **[docs/03-architecture/FLOW_ORCHESTRATOR.md](docs/03-architecture/FLOW_ORCHESTRATOR.md)** - Core routing philosophy
- **[docs/README.md](docs/README.md)** - Complete documentation index
- **[CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)** - Recent architecture alignment

## Project Structure

```
arxos/
├── src/
│   ├── core/               # Core library (no_std compatible)
│   ├── terminal/           # SSH terminal client
│   └── ios/               # iOS LiDAR scanner
├── firmware/
│   └── esp32/             # ESP32 mesh node firmware
├── docs/                  # Documentation
├── hardware/              # PCB designs and schematics
└── tests/                 # Integration tests
```

## Example Usage

```bash
# Load building plan
arxos load-plan school.pdf

# View floor
arxos view-floor 1

# Query equipment
arxos query "room:127 type:outlet"

# ASCII floor plan output:
╔════════════════════════════════════════╗
║         FLOOR 1 - GROUND LEVEL         ║
╠════════════════════════════════════════╣
║ ┌──────────┐  ┌──────────┐            ║
║ │   127    │  │   128    │            ║
║ │ Lab [O]  │  │ Class    │            ║
║ │    [L]   │  │  [L][V]  │            ║
║ └────| |───┘  └────| |───┘            ║
╚════════════════════════════════════════╝
```

## Hardware Requirements

- **ESP32-S3** with 8MB PSRAM
- **SX1262 LoRa** radio module
- **16MB flash** + SD card
- Total cost: ~$25 per node

## Contributing

This is an air-gapped system. Contributions must maintain the RF-only principle.

## License

MIT License - See LICENSE file

---

*"The constraint is the innovation. No internet, pure RF, total privacy."*