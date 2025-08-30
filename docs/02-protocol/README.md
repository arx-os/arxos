# The ArxObject Protocol

## 13 Bytes That Control Everything

### Core Concept

Every object in a building - from outlets to sensors to entire rooms - is represented by exactly 13 bytes:

```c
typedef struct {
    uint16_t object_id;      // 2 bytes - Unique identifier
    uint8_t  object_type;    // 1 byte  - What it is
    uint16_t x, y, z;        // 6 bytes - Where it is
    uint8_t  properties[4];  // 4 bytes - Current state
} ArxObject_Packet;          // Total: 13 bytes
```

### Why 13 Bytes?

At 1 kbps (typical LoRa bandwidth):
- **13 bytes** = 104 bits = 0.104 seconds transmission
- **Traditional BAS** = 400+ bytes = 3.2+ seconds
- **Improvement** = 30x faster, 30x more objects per second

### Protocol Layers

```
Application     Terminal commands, queries, control
    ↓
ArxObject       13-byte packet structure
    ↓  
Mesh Protocol   Meshtastic/custom routing
    ↓
LoRa Radio      915 MHz, spreading factor 7-12
```

### Packet Types

| Type ID | Object Type | Properties Usage |
|---------|------------|------------------|
| 0x10 | Electrical Outlet | Circuit, Amps, Status, Load% |
| 0x11 | Light Switch | Circuit, Status, Dimmer%, Mode |
| 0x12 | Temperature Sensor | Temp°C, Humidity%, CO2-high, CO2-low |
| 0x13 | Motion Sensor | Detected, Count, Timeout, Sensitivity |
| 0x14 | Door/Window | Status, Lock, Access, Alarm |
| 0x20 | HVAC Zone | Setpoint, Current, Mode, Fan |
| 0x30 | Room | Occupancy, Light%, Temp, CO2 |
| 0x40 | Floor | Zones, Occupancy%, Power%, Alert |
| 0x50 | Building | Floors, Occupancy%, Power%, Mode |

### Coordinate System

Location uses building-relative millimeters:
- **X**: East-West (0 = west edge)
- **Y**: North-South (0 = south edge)  
- **Z**: Vertical (0 = ground level)

Range: 0-65,535 mm = 65.5 meters per dimension

For larger buildings, use floor-relative coordinates with floor ID in upper nibble of object_type.

### Property Bit-Packing Examples

#### Outlet Properties (Type 0x10)
```c
properties[0] = circuit_id;        // 0-255 circuits
properties[1] = max_amps;          // 0-255 amps
properties[2] = status;            // Bit 0: On/Off, Bit 1: Fault
properties[3] = load_percent;      // 0-100%
```

#### Temperature Sensor (Type 0x12)
```c
properties[0] = temp_celsius + 40;  // -40 to 215°C range
properties[1] = humidity_percent;   // 0-100%
properties[2] = co2_high_byte;      // CO2 ppm high byte
properties[3] = co2_low_byte;       // CO2 ppm low byte
```

### Message Types

Beyond object state, the protocol supports:

| Message Type | Byte 0 | Purpose |
|--------------|--------|---------|
| Object State | 0x00-0x7F | Normal ArxObject packet |
| Query | 0x80 | Request object data |
| Command | 0x81 | Control object |
| Batch Start | 0x82 | Multiple objects follow |
| Batch End | 0x83 | End of batch |
| Delta Update | 0x84 | Differential update |
| Subscribe | 0x85 | Request updates |
| Unsubscribe | 0x86 | Stop updates |
| Error | 0xFF | Error response |

### Query Protocol

```c
// Query by ID
{0x80, 0x0F, 0x17, ...}  // Get object 0x0F17

// Query by location  
{0x80, 0xFF, 0xFF, x_hi, x_lo, y_hi, y_lo, z_hi, z_lo, radius}

// Query by type
{0x80, 0xFF, 0xFE, object_type, ...}
```

### Command Protocol

```c
// Turn outlet on
{0x81, 0x0F, 0x17, 0x10, 0x01, ...}  // Cmd, ID, Type, On

// Set temperature  
{0x81, 0x0A, 0x23, 0x20, 72, ...}    // Cmd, ID, Type, Temp
```

### Differential Updates

To save bandwidth, send only changes:

```c
// Full update (13 bytes)
{0x0F17, 0x10, 0x1472, 0x0866, 0x04B0, {15, 20, 0x01, 75}}

// Delta update (5 bytes) - only load changed
{0x84, 0x0F, 0x17, 0x03, 80}  // Delta, ID, Property index, New value
```

### Mesh Routing

Packets include mesh routing in separate header:
- Source node ID (2 bytes)
- Destination node ID (2 bytes)  
- Hop count (1 byte)
- Packet type (1 byte)
- ArxObject payload (13 bytes)

Total mesh packet: 19 bytes

### Security

- **AES-128 encryption** at LoRa layer
- **Rolling codes** for commands
- **Physical proximity** required (radio range)
- **No internet** = no remote attacks

### Bandwidth Budget

At 1 kbps sustained:
- **7 objects/second** with full updates
- **25 objects/second** with delta updates
- **100 objects** cached locally
- **95% queries** served from cache

### Protocol Evolution

Version field in object_type high bits:
- Bits 0-5: Object type (64 types)
- Bits 6-7: Protocol version (4 versions)

Current version: 0 (bits 6-7 = 00)

### Implementation Notes

1. **Byte order**: Little-endian for multi-byte fields
2. **Padding**: None - packed structure
3. **Alignment**: Not required for 8-bit MCUs
4. **Checksums**: Handled by LoRa layer
5. **Retransmission**: Automatic in mesh

### Next Steps

- [Packet Structure](packet-structure.md) - Detailed byte layout
- [Object Types](object-types.md) - All defined types
- [Properties](properties.md) - Bit-packing strategies
- [Examples](examples.md) - Real-world packets

---

*"Every byte justified, every bit meaningful"*