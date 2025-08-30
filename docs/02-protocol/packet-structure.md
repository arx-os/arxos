# ArxObject Packet Structure

## Detailed 13-Byte Specification

### Memory Layout

```c
typedef struct __attribute__((packed)) {
    uint16_t object_id;      // Bytes 0-1: Unique identifier
    uint8_t  object_type;    // Byte 2: Type and version
    uint16_t x;              // Bytes 3-4: X coordinate (mm)
    uint16_t y;              // Bytes 5-6: Y coordinate (mm)
    uint16_t z;              // Bytes 7-8: Z coordinate (mm)
    uint8_t  properties[4];  // Bytes 9-12: Type-specific data
} ArxObject_Packet;
```

### Byte-by-Byte Breakdown

```
Offset  Size  Field         Description
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0-1     2     object_id     Unique ID (0x0001-0xFFFE)
                            0x0000 = Reserved
                            0xFFFF = Broadcast
2       1     object_type   Bits 0-5: Type (0-63)
                            Bits 6-7: Version (0-3)
3-4     2     x            X position in mm (0-65535)
5-6     2     y            Y position in mm (0-65535)
7-8     2     z            Z position in mm (0-65535)
9       1     properties[0] Type-specific byte 1
10      1     properties[1] Type-specific byte 2
11      1     properties[2] Type-specific byte 3
12      1     properties[3] Type-specific byte 4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 13 bytes (104 bits)
```

### Object ID Allocation

```
Range           Assignment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0x0000         Reserved (invalid)
0x0001-0x00FF  System objects (255)
0x0100-0x0FFF  Floor 1 objects (3,840)
0x1000-0x1FFF  Floor 2 objects (4,096)
0x2000-0x2FFF  Floor 3 objects (4,096)
0x3000-0x3FFF  Floor 4 objects (4,096)
0x4000-0x7FFF  Floors 5-8 (16,384)
0x8000-0xEFFF  Dynamic allocation (28,672)
0xF000-0xFFFE  Special/temporary (4,094)
0xFFFF         Broadcast address
```

### Object Type Field

```
Bit 7  6  5  4  3  2  1  0
    │  │  └──────────────┘
    │  │         │
    │  │    Object Type (0-63)
    └──┘
    Version (0-3)
```

#### Type Categories

```
Type Range  Category
━━━━━━━━━━━━━━━━━━━━━━━━━
0x00-0x0F  System/Meta
0x10-0x1F  Electrical
0x20-0x2F  HVAC
0x30-0x3F  Sensors
0x40-0x4F  Security
0x50-0x5F  Structural
0x60-0x6F  Plumbing
0x70-0x7F  Reserved
```

### Coordinate System Details

#### Coordinate Encoding
- **Unit**: Millimeters from origin
- **Range**: 0-65,535 mm (65.5 meters)
- **Origin**: Building southwest ground corner
- **Byte order**: Little-endian

#### Large Building Support
For buildings > 65 meters:
1. Use floor-relative coordinates
2. Encode floor in object_type bits
3. Or use building zones with local origins

### Properties Array Patterns

#### Pattern 1: Status + Measurements
```c
properties[0] = status_bits;     // 8 boolean flags
properties[1] = measurement_1;    // 0-255 scale
properties[2] = measurement_2;    // 0-255 scale
properties[3] = measurement_3;    // 0-255 scale
```

#### Pattern 2: High-Resolution Value
```c
properties[0] = value_high;       // MSB
properties[1] = value_low;        // LSB
properties[2] = status;           // Status/flags
properties[3] = reserved;         // Future use
```

#### Pattern 3: Multiple Small Values
```c
properties[0] = (val1 << 4) | val2;  // Two 4-bit values
properties[1] = (val3 << 4) | val4;  // Two 4-bit values
properties[2] = value5;              // 8-bit value
properties[3] = value6;              // 8-bit value
```

### Special Packet Formats

#### Null/Empty Object
```c
{0x0000, 0x00, 0x0000, 0x0000, 0x0000, {0, 0, 0, 0}}
```

#### Broadcast Packet
```c
{0xFFFF, type, 0x0000, 0x0000, 0x0000, {data}}
```

#### Error Response
```c
{object_id, 0xFF, error_code, 0x0000, 0x0000, {details}}
```

### Transmission Formats

#### Raw Binary (Preferred)
```
Direct 13-byte transmission over LoRa
No encoding overhead
```

#### Hex String (Debug)
```
"0F17101472086604B00F140150"
26 characters, 26 bytes
```

#### Base64 (Text Transport)
```
"DxcQFHIIZgSwDxQBUA=="
20 characters, 20 bytes
```

### Endianness

All multi-byte fields are **little-endian**:
```c
uint16_t id = 0x0F17;
// Transmitted as: 0x17, 0x0F

uint16_t x = 0x1472;  // 5234 decimal
// Transmitted as: 0x72, 0x14
```

### Packing/Unpacking Code

#### C Implementation
```c
void pack_arxobject(uint8_t* buffer, ArxObject_Packet* obj) {
    buffer[0] = obj->object_id & 0xFF;
    buffer[1] = (obj->object_id >> 8) & 0xFF;
    buffer[2] = obj->object_type;
    buffer[3] = obj->x & 0xFF;
    buffer[4] = (obj->x >> 8) & 0xFF;
    buffer[5] = obj->y & 0xFF;
    buffer[6] = (obj->y >> 8) & 0xFF;
    buffer[7] = obj->z & 0xFF;
    buffer[8] = (obj->z >> 8) & 0xFF;
    memcpy(&buffer[9], obj->properties, 4);
}

void unpack_arxobject(ArxObject_Packet* obj, uint8_t* buffer) {
    obj->object_id = buffer[0] | (buffer[1] << 8);
    obj->object_type = buffer[2];
    obj->x = buffer[3] | (buffer[4] << 8);
    obj->y = buffer[5] | (buffer[6] << 8);
    obj->z = buffer[7] | (buffer[8] << 8);
    memcpy(obj->properties, &buffer[9], 4);
}
```

#### Rust Implementation
```rust
#[repr(C, packed)]
#[derive(Copy, Clone, Debug)]
pub struct ArxObject {
    pub id: u16,
    pub object_type: u8,
    pub x: u16,
    pub y: u16,
    pub z: u16,
    pub properties: [u8; 4],
}

impl ArxObject {
    pub fn to_bytes(&self) -> [u8; 13] {
        unsafe { std::mem::transmute(*self) }
    }
    
    pub fn from_bytes(bytes: [u8; 13]) -> Self {
        unsafe { std::mem::transmute(bytes) }
    }
}
```

### Validation Rules

1. **ID Validation**: Must not be 0x0000 (except for null object)
2. **Type Validation**: Version bits must be 0 for v1
3. **Coordinate Validation**: Check against building bounds
4. **Property Validation**: Type-specific rules apply

### Performance Characteristics

| Operation | Time | CPU Cycles |
|-----------|------|------------|
| Pack | < 1 μs | ~50 |
| Unpack | < 1 μs | ~50 |
| Validate | < 2 μs | ~100 |
| Transmit (LoRa) | 104 ms | N/A |
| Cache lookup | < 10 μs | ~500 |

### Evolution Path

#### Version 0 (Current)
- 13 bytes fixed size
- 64 object types
- 65m coordinate range

#### Version 1 (Planned)
- Extended coordinate range option
- More object types
- Backward compatible

#### Version 2 (Future)
- Compressed format option
- Multi-object packets
- Stream mode

---

→ Next: [Object Types](object-types.md)