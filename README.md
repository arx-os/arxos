# ArxOS - Buildings as Playable Worlds

> **"We're not maintaining buildings. We're playing them."**

## What is ArxOS?

ArxOS transforms every building on Earth into a **living, playable dungeon** - like Elden Ring meets infrastructure, Pokemon Go meets maintenance, all rendered in ASCII art and never touching the internet. Through 13-byte ArxObjects transmitted over packet radio, we compress reality itself into a game where every maintenance task is a quest, every room is a level, and every technician is a hero.

**Core Innovation**: Buildings become conscious, interactive game worlds. LiDAR scans and semantic input compress into ArxObjects that render as explorable ASCII dungeons in terminals, AR overlays for field techs, and CSI WiFi "vision" for security - all through RF mesh networks anchored by school districts.

## The Vision: Reality as a Game Engine

### Physical → Digital → Playable
1. **Capture**: LiDAR scans + semantic input → 10,000:1 compression
2. **Compress**: Reality → 13-byte ArxObjects (quantum seeds of infinite detail)
3. **Render**: ASCII dungeons, AR overlays, CSI WiFi vision
4. **Play**: Navigate buildings like roguelikes, complete quests, level up

### The Three Views
- **Terminal**: Buildings as ASCII art dungeons (think Dwarf Fortress)
- **AR**: Pokemon Go for maintenance techs
- **CSI WiFi**: See through walls using electromagnetic shadows

## Quick Start

```bash
# Clone and build
git clone https://github.com/arxos/arxos.git
cd arxos
cargo build --release

# Run ArxOS service
cargo run --bin arxos-service -- --config config.toml

# Connect to service via terminal
arxos connect --port /dev/ttyUSB0
```

## Core Features

### Reality Compression Engine
- **🗜️ 10,000:1 Compression**: 50MB point clouds → 5KB ArxObjects → Infinite procedural detail
- **🧬 Quantum Seeds**: Each 13-byte object contains infinite nested realities
- **📱 iPhone LiDAR**: 20-second scans capture entire buildings

### Gaming Infrastructure
- **🎮 Roguelike Buildings**: Every building is a playable dungeon
- **⚔️ Quest System**: Maintenance tasks become RPG quests with XP rewards
- **👁️ CSI WiFi Vision**: See through walls using electromagnetic patterns
- **🏆 Achievement System**: Level up, unlock abilities, compete globally

### Unhackable Mesh Network  
- **🔒 Air-Gapped**: No internet = no remote hacking possible
- **📡 RF Mesh**: LoRa packet radio creates planetary nervous system
- **🔐 Zero-Knowledge**: Districts route without reading data
- **🏫 School Backbone**: Public infrastructure as network nodes

## Documentation

### Vision Documents
- **[docs/01-vision/VISION.md](docs/01-vision/VISION.md)** - Core technical vision
- **[docs/01-vision/GAMING_VISION.md](docs/01-vision/GAMING_VISION.md)** - Buildings as playable worlds
- **[docs/01-vision/CSI_WIFI_VISION.md](docs/01-vision/CSI_WIFI_VISION.md)** - Electromagnetic vision system

### Architecture
- **[docs/03-architecture/NETWORK_ARCHITECTURE.md](docs/03-architecture/NETWORK_ARCHITECTURE.md)** - Zero-knowledge routing
- **[docs/03-architecture/FLOW_ORCHESTRATOR.md](docs/03-architecture/FLOW_ORCHESTRATOR.md)** - Core routing philosophy
- **[docs/README.md](docs/README.md)** - Complete documentation index

## Project Structure

```
arxos/
├── src/
│   ├── core/               # Core library (no_std compatible)
│   ├── terminal/           # Terminal client
│   ├── service/            # ArxOS service layer
│   └── ios/               # iOS LiDAR scanner
├── firmware_old/           # Legacy firmware (archived)
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

# Building as playable dungeon:
╔════════════════════════════════════════╗
║     FLOOR 1 - ACTIVE QUESTS: 3        ║
╠════════════════════════════════════════╣
║ ┌──────────┐  ┌──────────┐            ║
║ │Lab 127 ⚠ │  │Class 128 │            ║
║ │    @     │  │  ░░░░    │            ║
║ │  [O] [L] │  │ [L] [V]  │            ║
║ └────| |───┘  └────| |───┘            ║
║                                        ║
║ @ You  ⚠ Quest  ░ CSI Trail  O Outlet ║
╚════════════════════════════════════════╝
```

## Hardware Requirements

- **Standard Meshtastic Hardware** (ESP32 + LoRa radio)
- **ArxOS Service** runs on any compatible device
- **USB LoRa Dongle** for desktop connections
- **Bluetooth** for mobile device connections

## Contributing

This is an air-gapped system. Contributions must maintain the RF-only principle.

## License

MIT License - See LICENSE file

## The Philosophy

### Why Buildings as Games?
- **Engagement**: Maintenance becomes addictive, not tedious
- **Visualization**: Complex systems become intuitive dungeons
- **Motivation**: XP and achievements drive performance
- **Training**: New staff learn by playing
- **Community**: Technicians form guilds and share strategies

### Why No Internet?
- **Security**: Air-gapped = unhackable from outside
- **Sovereignty**: Your building data stays yours
- **Resilience**: Works during internet outages
- **Privacy**: No cloud surveillance possible
- **Innovation**: Constraints force elegant solutions

### The Cyberpunk Reality
We're building the cyberpunk future where:
- Hackers are maintenance techs with terminal access
- Buildings have consciousness rendered in ASCII
- Reality compresses into 13-byte seeds
- WiFi lets you see through walls
- Infrastructure is a massively multiplayer roguelike

---

*"We're not maintaining buildings. We're playing them."*