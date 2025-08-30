# Arxos Hardware Designs

## Open Hardware for Building Intelligence

This directory contains all hardware designs for Arxos nodes.

### Directory Structure

```
hardware/
├── pcb/                    # KiCad PCB designs
│   ├── reference-node/     # Basic ESP32 + LoRa node
│   ├── outlet-node/        # Outlet controller
│   └── sensor-node/        # Multi-sensor node
├── enclosures/            # 3D printable cases
│   ├── basic-box/         # Simple enclosure
│   └── din-rail/          # DIN rail mount
└── bom/                   # Bill of materials
```

### Reference Node BOM

| Part | Quantity | Unit Cost | Total | Source |
|------|----------|-----------|-------|--------|
| ESP32-S3-WROOM | 1 | $4.50 | $4.50 | Digikey |
| SX1262 LoRa Module | 1 | $8.00 | $8.00 | Digikey |
| 3.3V Regulator | 1 | $0.50 | $0.50 | Digikey |
| Antenna (915MHz) | 1 | $3.00 | $3.00 | Amazon |
| PCB | 1 | $2.00 | $2.00 | JLCPCB |
| Capacitors | 5 | $0.10 | $0.50 | Digikey |
| Resistors | 5 | $0.05 | $0.25 | Digikey |
| Headers | 2 | $0.50 | $1.00 | Digikey |
| Terminal Block | 1 | $1.00 | $1.00 | Digikey |
| **Total** | | | **$20.75** | |

### Design Principles

1. **Open Source** - All designs under MIT license
2. **Accessible** - Use common components
3. **Affordable** - Target <$25 total cost
4. **Modular** - Stackable/expandable designs
5. **Repairable** - Use standard footprints

### Contributing

1. Use KiCad for PCB designs
2. Use OpenSCAD or FreeCAD for enclosures
3. Include complete BOM with sources
4. Document assembly instructions
5. Test before submitting PR

### Certification

While these are DIY designs, consider:
- FCC Part 15 for US deployment
- CE marking for Europe
- Local electrical codes for mains-powered devices

### Safety

⚠️ **WARNING**: Some designs involve mains voltage (120/240V AC). Only qualified electricians should install mains-powered nodes.

---

*"Hardware so open, you can build it in your garage"* 🔧