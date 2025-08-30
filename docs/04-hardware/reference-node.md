# Reference Node Design

## Complete Open Hardware Schematic

### Schematic

```
                 ESP32-S3 DevKit
                ┌─────────────────┐
                │                 │
    3.3V ───────┤ 3V3         GND ├─────── GND
                │                 │
    Relay ──────┤ GPIO32     GPIO5 ├────── LoRa SCK
                │                 │
    Sensor ─────┤ GPIO34    GPIO19 ├────── LoRa MISO
                │                 │
    LED ────────┤ GPIO2     GPIO27 ├────── LoRa MOSI
                │                 │
    Button ─────┤ GPIO0     GPIO18 ├────── LoRa CS
                │                 │
                │            GPIO14 ├────── LoRa RST
                │                 │
                │            GPIO26 ├────── LoRa IRQ
                │                 │
                └─────────────────┘
                
                 SX1262 LoRa Module
                ┌─────────────────┐
                │                 │
    3.3V ───────┤ VCC         GND ├─────── GND
                │                 │
    ─────────┤ SCK        BUSY ├────── GPIO33
                │                 │
    ─────────┤ MISO        DIO1 ├────── GPIO26
                │                 │
    ─────────┤ MOSI         CS ├──────
                │                 │
    ─────────┤ RST         ANT ├────── Antenna
                │                 │
                └─────────────────┘
```

### Bill of Materials

| Part | Quantity | Cost | Source |
|------|----------|------|--------|
| ESP32-S3 | 1 | $4.50 | Espressif |
| SX1262 | 1 | $8.00 | Semtech |
| Antenna | 1 | $3.00 | Generic |
| Relay | 1 | $2.00 | Songle |
| LED | 3 | $0.30 | Generic |
| Resistor | 5 | $0.10 | Generic |
| Capacitor | 3 | $0.20 | Generic |
| Connector | 4 | $2.00 | JST |
| PCB | 1 | $2.00 | JLCPCB |
| **Total** | | **$22.10** | |

### PCB Layout

```
┌──────────────────────────────┐
│  ANT                         │
│   ○                          │
│        ┌──────┐   ┌──────┐  │
│        │LoRa  │   │ESP32 │  │
│        │      │   │      │  │
│        └──────┘   └──────┘  │
│                              │
│  PWR ○  ○ GND   ○ ○ ○ GPIO  │
└──────────────────────────────┘
       Size: 50mm x 30mm
```

### Firmware

Available at: github.com/arxos/reference-node

---

→ Next: [Node Types](node-types.md)