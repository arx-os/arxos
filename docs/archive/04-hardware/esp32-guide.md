# ESP32 Development Guide

## From Zero to Mesh Node

### Quick Start

```bash
# Install Arduino IDE
# Add ESP32 board support
# Install libraries:
- Meshtastic
- RadioLib
- ArxOS

# Flash firmware
# Join mesh
# Earn BILT!
```

### Recommended Boards

| Board | Price | Features | Best For |
|-------|-------|----------|----------|
| TTGO T-Beam | $35 | GPS, Battery | Mobile players |
| Heltec V3 | $25 | OLED display | Fixed nodes |
| LILYGO T3S3 | $20 | Smallest | Tight spaces |
| Custom PCB | $15 | Your design | Mass production |

### Pin Connections

```c
// LoRa SX1262 connections
#define LORA_SCK  5
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_CS   18
#define LORA_RST  14
#define LORA_IRQ  26

// Sensor/relay pins
#define RELAY_PIN 32
#define SENSOR_PIN 34
#define LED_PIN 2
```

### First Program

```rust
use arxos_esp::{ArxOS, ArxObject, ObjectType};
use esp_idf_hal::delay::FreeRtos;

#[no_mangle]
fn app_main() {
    let mut arxos = ArxOS::new();
    arxos.join_mesh("BuildingNet");
    
    loop {
        // Create outlet object
        let outlet = ArxObject {
            id: 0x0101,
            object_type: ObjectType::Outlet,
            x: 1000, y: 2000, z: 1200,
            properties: [15, 20, 1, 50],
        };
        
        // Send to mesh
        arxos.transmit(outlet);
        
        // Earn BILT!
        FreeRtos::delay_ms(10000);
    }
}
```

---

→ Next: [Reference Node](reference-node.md)