# Open Hardware Platform

## $25 Nodes vs $500 Controllers

### The Revolution

Traditional building automation requires proprietary $500+ controllers. Arxos runs on $25 ESP32 boards that anyone can build, buy, or modify.

```
Traditional Controller:          Arxos Node:
━━━━━━━━━━━━━━━━━━━━━━━━━━━    ━━━━━━━━━━━━━━━━━━━━━━━━━━
Proprietary CPU                 ESP32-S3 (open)
Locked firmware                 Open source
$500-$5000                      $25-$75
Vendor only                     DIY friendly
Special tools                   Arduino IDE
Annual license                  Free forever
```

### Core Components

#### Minimum Viable Node ($25)
```yaml
ESP32-S3:        $4.50   # Dual-core 240 MHz
SX1262 LoRa:     $8.00   # 915 MHz radio
Antenna:         $3.00   # Simple wire/PCB
Power Supply:    $3.00   # 3.3V regulator
PCB:             $2.00   # Or breadboard
Connectors:      $2.50   # Headers/terminals
Enclosure:       $2.00   # 3D printed
━━━━━━━━━━━━━━━━━━━━━━━━━
Total:           $25.00
```

#### Professional Node ($75)
```yaml
ESP32 + LoRa:    $25.00  # Integrated module
Antenna:         $10.00  # High-gain external
Power:           $10.00  # Industrial supply
Enclosure:       $15.00  # Weatherproof
Connectors:      $10.00  # Industrial grade
Mounting:        $5.00   # DIN rail/wall
━━━━━━━━━━━━━━━━━━━━━━━━━
Total:           $75.00
```

### Node Types

#### Outlet Node
```
Controls and monitors electrical outlets
- Relay: 20A switching
- Current sensor: Power monitoring
- Status LED: Visual feedback
- BILT Reward: 25 tokens per outlet
```

#### Sensor Node
```
Environmental monitoring
- Temperature/Humidity
- CO2 sensor
- Motion detection
- Light level
- BILT Reward: 10-20 tokens
```

#### Panel Node
```
Electrical panel monitoring
- Current transformers
- Voltage sensing
- Breaker status
- BILT Reward: 100 tokens
```

#### Gateway Node
```
Building mesh coordinator
- External antenna
- Ethernet option
- SD card logging
- BILT Reward: 200 tokens
```

### Why ESP32-S3?

| Feature | Benefit |
|---------|---------|
| Dual-core 240 MHz | Real-time control |
| 512 KB SRAM | ArxObject cache |
| 8 MB Flash | Firmware + storage |
| WiFi/BLE | Optional connectivity |
| Deep sleep | Battery operation |
| $4.50 price | Accessible to all |
| Arduino/IDF | Easy programming |

### Power Options

#### USB Powered
```
- Simplest option
- 5V USB → 3.3V
- Phone charger works
- No battery needed
```

#### Battery Powered
```
- 18650 Li-ion cell
- 2-4 week runtime
- Solar charging option
- Mobile nodes
```

#### Mains Powered
```
- AC-DC converter
- Always on
- Most reliable
- Fixed installations
```

### Build vs Buy

#### DIY Build (Makers)
- Learn by building
- Customize everything
- Lowest cost
- Community support
- Earn Builder BILT

#### Pre-Built (Installers)
- Certified hardware
- Warranty included
- Plug and play
- Professional look
- Earn Installer BILT

#### Commercial (Enterprises)
- Bulk pricing
- Custom firmware
- Support contracts
- Training included
- Earn Enterprise BILT

### The Game Changer

```
Old Way:
- Request quote from vendor
- Wait 2-4 weeks
- Pay $50,000+
- Locked into proprietary system
- Pay annual licenses

Arxos Way:
- Order ESP32 on Amazon
- Arrives in 2 days
- Build for $25
- Join mesh network
- Start earning BILT
```

### Community Hardware

Players are creating amazing nodes:

```yaml
"ThermalVision Node":
  Creator: Player_Sarah
  Features: FLIR Lepton thermal camera
  Cost: $125
  BILT Earned: 5,847
  Downloads: 234

"PowerMeter Node":
  Creator: Player_Mike
  Features: 6-channel power monitoring
  Cost: $45
  BILT Earned: 3,291
  Downloads: 567

"Universal Sensor":
  Creator: Player_Alex
  Features: 12 sensor types
  Cost: $65
  BILT Earned: 8,923
  Downloads: 891
```

### Certification Levels

| Level | Requirements | BILT Multiplier |
|-------|--------------|-----------------|
| Hobbyist | Build 1 node | 1.0x |
| Maker | Build 10 nodes | 1.5x |
| Installer | Deploy 50 nodes | 2.0x |
| Integrator | Deploy 500 nodes | 3.0x |
| Master | Create new node type | 5.0x |

### Next Steps

- [ESP32 Setup Guide](esp32-guide.md) - Getting started
- [Reference Node Design](reference-node.md) - Complete schematic
- [Node Types](node-types.md) - All node varieties
- [Assembly Guide](assembly.md) - Step-by-step build

---

*"Every building deserves intelligence. Every person can build it."*