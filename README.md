# 📡 Arxos - Building Operating System via Packet Radio Mesh

## Minecraft for Buildings + Pokémon GO for Infrastructure

Arxos revolutionizes building automation by replacing $100,000+ proprietary systems with $25 open-source nodes that communicate via packet radio mesh networks - no internet required.

### 📁 Project Organization

```
arxos/
├── src/                    # Rust source code
│   ├── core/              # Core protocol library (no_std)
│   ├── terminal/          # Terminal client (like Minecraft)
│   └── embedded/          # Embedded systems library
├── firmware/              # Microcontroller firmware
│   ├── esp32/            # ESP32 Arduino/PlatformIO
│   └── arduino/          # Generic Arduino sketches
├── hardware/              # Open hardware designs
│   ├── pcb/              # KiCad PCB designs
│   ├── enclosures/       # 3D printable cases
│   └── bom/              # Bill of materials
├── mobile/                # Mobile apps
│   ├── ios/              # iPhone AR (Swift)
│   └── android/          # Android AR (Kotlin)
├── examples/              # Example projects
├── docs/                  # Documentation
│   ├── 01-vision/        # Why Arxos exists
│   ├── 02-protocol/      # 13-byte specification
│   ├── 03-mesh-network/  # LoRa/Meshtastic
│   └── ...               # Complete guides
└── Cargo.toml            # Rust workspace
```

### 🎮 The Gaming Revolution in Building Management

Imagine walking into a building with your phone, seeing every outlet, sensor, and system in augmented reality, and earning cryptocurrency-like tokens (BILT) for mapping and maintaining infrastructure. That's Arxos.

```
Traditional Building Automation:     Arxos Mesh Network:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$100,000+ investment                 $10,000 complete system
Proprietary vendor lock-in           Open source everything
Internet dependent                   Air-gapped packet radio
Complex professional install         Any electrician can deploy
400+ byte JSON objects              13-byte ArxObject packets
```

### 🚀 Quick Start

```bash
# Terminal shows your building like Minecraft
$ arxos view --building=main --floor=2

┌──────────────────────────────────────────────────┐
│ MAIN BUILDING - FLOOR 2 [LIVE]                  │
├──────────────────────────────────────────────────┤
│  ┌─────┬─────┬─────┐    ┌─────┬─────┬─────┐   │
│  │ 201 │ 202 │ 203 │    │ 204 │ 205 │ 206 │   │
│  │ ●   │ ○   │ ●   │    │ ○   │ ●   │ ○   │   │
│  └─────┴─────┴─────┘    └─────┴─────┴─────┘   │
├──────────────────────────────────────────────────┤
│ ● Light On  ○ Light Off  ▣ Panel  ═ Circuit    │
│ Players: 3  BILT Today: 847  Efficiency: 92%   │
└──────────────────────────────────────────────────┘
```

### 💡 Core Innovation: The 13-Byte Protocol

Every building object - outlets, sensors, rooms - is represented in exactly 13 bytes:

```c
typedef struct {
    uint16_t object_id;      // 2 bytes - Unique identifier
    uint8_t  object_type;    // 1 byte  - What it is
    uint16_t x, y, z;        // 6 bytes - Where it is
    uint8_t  properties[4];  // 4 bytes - Current state
} ArxObject_Packet;          // Total: 13 bytes

// 30x more efficient than JSON
// Works over 1 kbps mesh networks
// Fits in $4 microcontroller memory
```

### 🏗️ How It Works

1. **Hardware**: ESP32 + LoRa radio = $25 per node
2. **Network**: Meshtastic mesh protocol, no internet needed
3. **Interface**: ASCII terminal (works everywhere) + AR mobile app
4. **Gaming**: Players earn BILT tokens for mapping/maintaining
5. **Security**: Air-gapped, unhackable, physically secure

### 📚 Documentation

- **[Vision](docs/01-vision/)** - Why Arxos exists and the problem it solves
- **[Protocol](docs/02-protocol/)** - The 13-byte ArxObject specification
- **[Mesh Network](docs/03-mesh-network/)** - LoRa/Meshtastic architecture
- **[Hardware](docs/04-hardware/)** - Build your own nodes for $25
- **[Terminal](docs/05-terminal/)** - ASCII rendering and navigation
- **[Implementation](docs/06-implementation/)** - Rust development guide
- **[Deployment](docs/07-deployment/)** - Real-world installation
- **[AR Interface](docs/08-ar-interface/)** - iPhone ARKit integration
- **[Legacy](docs/09-legacy/)** - Lessons from the Go implementation

### 🎯 Use Cases

#### Schools (Finally Affordable)
- **Before**: Can't afford $100K+ systems, waste energy
- **After**: $5K system, students help map, 30% energy savings

#### Small Businesses
- **Before**: No automation, manual control only
- **After**: Professional-grade control for price of iPad

#### Developing Nations
- **Before**: Skip building intelligence entirely
- **After**: Leapfrog to mesh networks, no infrastructure needed

### 🛠️ Build Your First Node

```yaml
Shopping List:
- ESP32-S3: $4.50
- SX1262 LoRa: $8.00
- Antenna: $3.00
- Power Supply: $3.00
- Connectors: $2.00
Total: ~$25

Time: 30 minutes
Skill: Basic soldering
Reward: 100 BILT tokens
```

### 🌍 Join the Revolution

**Discord**: [discord.gg/arxos](https://discord.gg/arxos)  
**Hardware Designs**: [/docs/04-hardware/](docs/04-hardware/)  
**Protocol Spec**: [/docs/02-protocol/](docs/02-protocol/)

### 🏆 Why Arxos Wins

| Feature | Traditional BAS | Arxos |
|---------|----------------|-------|
| **Cost** | $100,000+ | $10,000 |
| **Install Time** | 3-6 months | 1 week |
| **Maintenance** | Vendor monopoly | Community |
| **Security** | Internet vulnerable | Air-gapped |
| **Data Size** | 400+ bytes/object | 13 bytes |
| **Gaming** | Boring | Earn while you work |

### 🔮 The Future

Imagine every building in the world:
- **Self-aware** of every outlet, sensor, and system
- **Interconnected** via secure mesh networks
- **Gamified** with rewards for maintenance
- **Accessible** to everyone, not just the wealthy
- **Unhackable** with no internet connection

This isn't just building automation. It's the democratization of building intelligence.

### 📡 Start Playing the Building Game

1. **Read** [The Vision](docs/01-vision/README.md)
2. **Build** a $25 node
3. **Deploy** in your building
4. **Earn** BILT tokens
5. **Join** the mesh network

---

*"The constraint is the innovation. 13 bytes forces elegance."*

**Building intelligence through packet radio and gaming mechanics.** 🏢📡🎮