# Property Bit-Packing Strategies

## Making Every Bit Count in the Game

### The Challenge

With only 4 bytes (32 bits) for properties, we need clever encoding to represent complex building state. Think of it like inventory management in classic RPGs - limited slots, maximum utility.

### Bit-Packing Patterns

#### Pattern 1: Boolean Flags (Status Bytes)
```c
// 8 boolean values in 1 byte
uint8_t status = 0;
status |= (1 << 0);  // Bit 0: Power on
status |= (1 << 1);  // Bit 1: Fault detected
status |= (1 << 2);  // Bit 2: Maintenance needed
status |= (1 << 3);  // Bit 3: Override active
status |= (1 << 4);  // Bit 4: Alarm triggered
status |= (1 << 5);  // Bit 5: Network connected
status |= (1 << 6);  // Bit 6: Battery backup
status |= (1 << 7);  // Bit 7: Emergency mode

// Check individual flags
bool is_powered = status & (1 << 0);
bool has_fault = status & (1 << 1);
```

#### Pattern 2: Scaled Values
```c
// Temperature: -40°C to 215°C in 1 byte
uint8_t encode_temp(float celsius) {
    return (uint8_t)(celsius + 40);  // 0 = -40°C, 255 = 215°C
}
float decode_temp(uint8_t encoded) {
    return (float)encoded - 40.0;
}

// Percentage: 0-100% in 1 byte (with 0.4% precision)
uint8_t encode_percent(float percent) {
    return (uint8_t)(percent * 2.55);  // 0-255 scale
}
float decode_percent(uint8_t encoded) {
    return (float)encoded / 2.55;
}
```

#### Pattern 3: Packed Small Values
```c
// Pack two 4-bit values in 1 byte
uint8_t pack_nibbles(uint8_t high, uint8_t low) {
    return (high << 4) | (low & 0x0F);
}

// Example: Room zones and lighting scenes
properties[0] = pack_nibbles(zone_id, scene_id);
uint8_t zone = (properties[0] >> 4) & 0x0F;  // 0-15
uint8_t scene = properties[0] & 0x0F;         // 0-15
```

#### Pattern 4: 16-bit Values Across 2 Bytes
```c
// Store larger values like CO2 PPM (0-5000)
uint16_t co2_ppm = 1847;
properties[0] = (co2_ppm >> 8) & 0xFF;  // High byte
properties[1] = co2_ppm & 0xFF;         // Low byte

// Decode
uint16_t ppm = (properties[0] << 8) | properties[1];
```

### Real-World Examples

#### Electrical Outlet Encoding
```c
// Properties for outlet type 0x10
struct OutletProperties {
    uint8_t circuit_id;      // 0-255 circuits
    uint8_t max_amps;        // Direct value
    uint8_t status;          // 8 status bits
    uint8_t load_percent;    // 0-255 (maps to 0-100%)
};

// Status byte breakdown:
// Bit 0: Power (0=off, 1=on)
// Bit 1: Fault (0=normal, 1=fault)
// Bit 2: GFCI (0=normal, 1=tripped)
// Bit 3: Arc fault (0=normal, 1=detected)
// Bit 4: Grounded (0=no, 1=yes)
// Bit 5: USB ports (0=none, 1=has USB)
// Bit 6: Smart outlet (0=dumb, 1=smart)
// Bit 7: Locked (0=unlocked, 1=locked)
```

#### HVAC Zone Encoding
```c
// Properties for HVAC zone type 0x20
struct HVACProperties {
    uint8_t setpoint;        // Temperature + 40
    uint8_t current;         // Temperature + 40
    uint8_t mode_fan;        // Packed nibbles
    uint8_t humidity;        // 0-100% as 0-255
};

// mode_fan breakdown:
// Upper nibble (bits 4-7): Mode
//   0 = Off, 1 = Heat, 2 = Cool, 3 = Auto
//   4 = Emergency heat, 5 = Fan only
// Lower nibble (bits 0-3): Fan speed
//   0 = Auto, 1 = Low, 2 = Medium, 3 = High
```

#### Multi-Sensor Encoding
```c
// Properties for environmental sensor
struct SensorProperties {
    uint8_t temp_humidity;   // Packed values
    uint8_t co2_high;       // CO2 PPM high byte
    uint8_t co2_low;        // CO2 PPM low byte
    uint8_t light_motion;   // Packed sensors
};

// temp_humidity: 
//   Bits 0-4: Temperature (0-31 scale, maps to 50-95°F)
//   Bits 5-7: Humidity (0-7 scale, maps to 0-100%)

// light_motion:
//   Bits 0-3: Light level (0-15 scale)
//   Bits 4-6: Motion detected (0-7 people count)
//   Bit 7: Occupancy (0=empty, 1=occupied)
```

### Advanced Techniques

#### Delta Encoding
```c
// Instead of absolute values, send changes
struct DeltaUpdate {
    uint8_t field_mask;      // Which fields changed
    uint8_t delta_values[3]; // Only changed values
};

// field_mask bits indicate which properties changed
// Only transmit bytes for changed properties
```

#### Logarithmic Scaling
```c
// For wide ranges, use log scale
uint8_t encode_power_watts(uint32_t watts) {
    if (watts == 0) return 0;
    // Log scale: 0-255 represents 1W to 100kW
    return (uint8_t)(log10(watts) * 51);
}

uint32_t decode_power_watts(uint8_t encoded) {
    if (encoded == 0) return 0;
    return (uint32_t)pow(10, encoded / 51.0);
}
```

#### Time Encoding
```c
// Compact time representation
uint8_t encode_minutes(uint16_t minutes) {
    // 0-255 represents 0-24 hours in ~6 min increments
    return (uint8_t)(minutes / 6);
}

uint8_t encode_hour_min(uint8_t hour, uint8_t min) {
    // Pack time in 1 byte: 5 bits hour (0-23), 3 bits for 10-min blocks
    return (hour << 3) | (min / 10);
}
```

### Game Mechanics Encoding

#### Player Stats
```c
// Encode player information in building
struct PlayerProperties {
    uint8_t class_level;     // Upper: class, Lower: level/10
    uint8_t skills;          // Bit flags for skills
    uint8_t tokens_earned;   // BILT tokens / 10
    uint8_t achievements;    // Achievement flags
};

// class_level:
//   Bits 4-7: Class (0=Electrician, 1=HVAC, 2=Plumber...)
//   Bits 0-3: Level (0-15, multiply by 10 for 0-150)

// skills:
//   Each bit = different skill unlocked
//   Bit 0: Basic wiring
//   Bit 1: Panel work
//   Bit 2: Troubleshooting
//   etc.
```

#### Building Score
```c
// Encode building performance metrics
struct BuildingScore {
    uint8_t efficiency;      // Energy efficiency 0-100%
    uint8_t health;         // System health 0-100%
    uint8_t safety;         // Safety score 0-100%
    uint8_t comfort;        // Comfort index 0-100%
};

// All stored as 0-255, displayed as 0-100%
// Changes trigger BILT rewards for improvements
```

### Compression Strategies

#### Run-Length Encoding
```c
// For repetitive data (like identical outlets)
struct RLEPacket {
    uint8_t count;          // Number of identical objects
    uint8_t base_id_high;   // Starting ID high byte
    uint8_t base_id_low;    // Starting ID low byte
    uint8_t properties[4];  // Shared properties
};
```

#### Differential Updates
```c
// Only send what changed
struct DiffPacket {
    uint8_t object_id_offset; // Offset from last ID
    uint8_t prop_index;       // Which property (0-3)
    uint8_t new_value;        // New value
    uint8_t timestamp;        // Seconds since last update
};
```

### Best Practices

1. **Use every bit** - No wasted space
2. **Think in scales** - Map ranges to 0-255
3. **Pack related data** - Group bits logically
4. **Document encoding** - Critical for other players
5. **Version carefully** - Leave room for growth

### Common Encodings Reference

| Data Type | Range | Encoding | Bytes |
|-----------|-------|----------|-------|
| Temperature | -40 to 215°C | Add 40 | 1 |
| Percentage | 0-100% | Multiply by 2.55 | 1 |
| Power | 0-65kW | 16-bit direct | 2 |
| Time | 0-24 hours | Minutes/6 | 1 |
| Distance | 0-65m | Millimeters | 2 |
| Count | 0-255 | Direct | 1 |
| Flags | 8 booleans | Bit flags | 1 |

### Decoding in Terminal

```bash
# Show raw and decoded properties
$ arxos decode @outlet-4A7B
Object: 0x4A7B (Outlet)
Raw: [15, 20, 0x81, 127]
Decoded:
  Circuit: 15
  Max Amps: 20
  Status: ON | GROUNDED | SMART
  Load: 50%
```

---

→ Next: [Real-World Examples](examples.md)