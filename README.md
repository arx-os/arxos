# 🏰 ArxOS - Building Infrastructure as Epic Adventure

> **"Your building becomes Elden Ring"** - Real infrastructure gamified, transmitted via packet radio, rendered from ASCII to AR.

## What is ArxOS?

ArxOS revolutionizes building management by transforming Building Information Models (BIM) into engaging game worlds. We compress real infrastructure to 13-byte semantic objects that render as fantasy game elements while maintaining genuine building data. **10,000:1 compression** enables transmission over packet radio, making every outlet a power node, every breaker a dungeon gate, and every maintenance task an epic quest.

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

- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Complete system architecture and vision
- **[docs/ssh_terminal.md](docs/ssh_terminal.md)** - SSH terminal command reference
- **[docs/document_parser.md](docs/document_parser.md)** - PDF/IFC parsing capabilities
- **[docs/technical/](docs/technical/)** - Technical specifications

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