# ArxObject Specification: Universal Building Intelligence Protocol

> **A fractal compression protocol that transforms building intelligence into RF-transmittable packets, optimized for mesh network bandwidth constraints.**

## Overview

The ArxObject is ArxOS's universal building intelligence format - a fractal, bandwidth-optimized representation of building elements. While the core atomic unit typically compresses to approximately 13 bytes, the actual size adapts to available RF bandwidth and required detail level. This specification defines the structure, encoding, and fractal nature of ArxObjects across the global ArxOS mesh network.

### Key Principle: Bandwidth-First Design

ArxObjects are NOT fixed at 13 bytes - they are compressed to fit within RF mesh constraints:
- **LoRa Reality**: 51-222 byte packets, 0.3-50 kbps
- **Compression Target**: Fit building intelligence through this "straw"
- **Result**: Core objects typically ~13 bytes, but can scale based on need

## Core Structure

### Binary Layout (Little-Endian, Signed Coordinates)
```rust
#[repr(C, packed)]
pub struct ArxObject {
    pub building_id: u16,    // 2 bytes - Building identifier (65,536 buildings)
    pub object_type: u8,     // 1 byte  - Object type (256 types)
    pub x: i16,              // 2 bytes - X position in millimeters (±32.7m)
    pub y: i16,              // 2 bytes - Y position in millimeters (±32.7m)  
    pub z: i16,              // 2 bytes - Z position in millimeters (±32.7m)
    pub properties: [u8; 4], // 4 bytes - Type-specific properties
}
// Total: 13 bytes (atomic unit)
```

Serialization MUST use explicit little-endian conversion (no `transmute`):
```rust
impl ArxObject {
    pub const SIZE: usize = 13;
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        let mut out = [0u8; Self::SIZE];
        let bid = self.building_id.to_le_bytes(); out[0]=bid[0]; out[1]=bid[1];
        out[2] = self.object_type;
        let xb = self.x.to_le_bytes(); out[3]=xb[0]; out[4]=xb[1];
        let yb = self.y.to_le_bytes(); out[5]=yb[0]; out[6]=yb[1];
        let zb = self.z.to_le_bytes(); out[7]=zb[0]; out[8]=zb[1];
        out[9..13].copy_from_slice(&self.properties);
        out
    }
    pub fn from_bytes(b: &[u8; Self::SIZE]) -> Self {
        Self {
            building_id: u16::from_le_bytes([b[0], b[1]]),
            object_type: b[2],
            x: i16::from_le_bytes([b[3], b[4]]),
            y: i16::from_le_bytes([b[5], b[6]]),
            z: i16::from_le_bytes([b[7], b[8]]),
            properties: [b[9], b[10], b[11], b[12]],
        }
    }
}
```

### Field Definitions

#### Building ID (2 bytes)
- **Range**: 0x0000 to 0xFFFF (65,536 unique buildings)
- **Scope**: Unique within a school district or mesh region
- **Encoding**: Little-endian 16-bit unsigned integer
- **Special Values**:
  - `0x0000`: Reserved for system messages
  - `0xFFFF`: Broadcast to all buildings

#### Object Type (1 byte)
- **Range**: 0x00 to 0xFF (256 object types)
- **Categories**: Organized by building system (see Object Type Registry)
- **Encoding**: Single unsigned byte
- **Extensibility**: Types 0xF0-0xFF reserved for custom/experimental use

#### Position (6 bytes)
- **Coordinate System**: Building-relative coordinates
- **Unit**: Millimeters for precise positioning
- **Range**: ±32,767mm (±32.7 meters) per axis
- **Origin**: Building corner or center point (defined per building)
- **Encoding**: Three signed 16-bit integers (x, y, z) in little-endian

#### Properties (4 bytes)
- **Structure**: Type-specific bit-packed data
- **Encoding**: Varies by object type (see Type-Specific Properties)
- **Optimization**: Maximum information density in 32 bits
- **Versioning**: First 2 bits can indicate property schema version

## Fractal Nature & Bandwidth Optimization

### The Fractal Reality Engine

ArxObjects are **fractal seeds** - each 13-byte structure contains the DNA for infinite procedural generation. Like fractals in nature, they reveal different levels of detail at different scales, all deterministically generated from the same compact seed.

```
Zoom Level 0: Molecular (generated from seed)
├── Material composition at atomic level
├── Wear patterns and degradation
└── Quantum properties

Zoom Level 1: Component (13 bytes + generation)
├── Individual screws, terminals, wires
├── Generated from parent object's fractal seed
└── Each sub-component has its own properties

Zoom Level 2: Object (core 13 bytes)
├── Single outlet, switch, or sensor
├── Position and basic properties
└── Can generate infinite sub-components

Zoom Level 3: System (aggregated objects)
├── All outlets on a circuit
├── Electrical panel relationships
├── Load calculations and dependencies

Zoom Level 4: Building (statistical compression)
├── Entire building as meta-object
├── "47 circuits, 3-phase, 2000A service"
└── Can drill down to any detail level
```

### Fractal Generation Engine

The 4-byte `properties` field acts as a **fractal seed** that deterministically generates:

```rust
// Generate infinite detail from 13 bytes
impl ArxObject {
    /// Generate contained objects when zooming IN
    pub fn generate_contained_object(&self, relative_pos: (i16, i16, i16), scale: f32) -> ArxObject {
        // Fractal seed determines sub-object types
        // E.g., outlet contains terminals, screws, housing
    }
    
    /// Generate parent systems when zooming OUT  
    pub fn generate_containing_system(&self, scale: f32) -> ArxObject {
        // Derive parent system from object type
        // E.g., outlet belongs to electrical panel
    }
    
    /// Generate implied properties on-demand
    pub fn implied_properties(&self) -> ImpliedProperties {
        // Power requirements, materials, maintenance
        // All derived from object type and seed
    }
}
```

This fractal approach enables:
- **Infinite zoom**: Explore from building-wide to molecular level
- **Deterministic generation**: Same seed always produces same details
- **Bandwidth efficiency**: Only transmit 13 bytes, generate rest locally
- **Gaming experience**: Terminal becomes explorable 3D ASCII world

### Bandwidth-Driven Sizing

ArxObject size emerges from RF constraints, not protocol requirements:

```rust
// Minimal 2D Terminal View
type Basic2D = (u16, ArxObject); // ~15 bytes

// Enhanced 3D View (bandwidth permitting)
struct Enhanced3D {
    room_id: u16,
    object: ArxObject,
    position_precise: [f32; 3],
    orientation: f32,
    visual_hints: u8,
}

// Full Room Sync (progressive)
struct RoomData { /* multiple frames */ }
```

## Real-World Transmission Notes

See `docs/LATENCY_ESTIMATES.md` for 17 objects per sealed frame (255 MTU − headers − MAC) and airtime ranges.

## Mesh Network Integration (updated)

### Sealed Frame Structure (application level)
- Security header (8 bytes): sender_id (LE u16), key_version (u8), reserved (u8), nonce (LE u32)
- Application header (typically 4 bytes): frame_index (LE u16), total_frames (LE u16)
- Payload: N × 13B ArxObjects
- MAC tag: 16 bytes

With a 255-byte MTU and a 4-byte app header, `17` objects fit per sealed frame.

### Routing Efficiency
- **17 ArxObjects per sealed frame** with security enabled
- **Binary compactness**: No text encodings on the wire
- **Progressive**: Partial frames still render useful state

## Encoding Examples

### Example 1: Classroom Outlet
```
Building: Lincoln Elementary (ID: 0x0234)
Location: Room 205, east wall
Position: (5.2m, 8.1m, 0.3m) from building origin
Properties: 120V, Circuit 15, 20 amp, GFCI, power on

ArxObject Encoding:
┌─────────────────────────────────────────────┐
│ Field       │ Bytes │ Value     │ Hex      │
├─────────────────────────────────────────────┤
│ building_id │   2   │ 564       │ 0x0234   │
│ object_type │   1   │ OUTLET    │ 0x10     │
│ x           │   2   │ 5200mm    │ 0x1450   │
│ y           │   2   │ 8100mm    │ 0x1FA4   │
│ z           │   2   │ 300mm     │ 0x012C   │
│ properties  │   4   │ See below │ See below│
└─────────────────────────────────────────────┘

Properties breakdown:
┌─────────┬─────────┬─────────┬─────────┐
│ Byte 0  │ Byte 1  │ Byte 2  │ Byte 3  │
│ 120V    │ Ckt 15  │ 20 Amp  │ Status  │
│ 0x78    │ 0x0F    │ 0x14    │ 0x0B    │
└─────────┴─────────┴─────────┴─────────┘

Complete 13-byte ArxObject (LE):
34 02 10 50 14 A4 1F 2C 01 78 0F 14 0B
```

### Example 2: Emergency Exit Sign
```
Building: Roosevelt High School (ID: 0x0456)
Location: Main hallway exit
Position: (12.0m, 2.5m, 2.8m)

Complete 13-byte ArxObject (LE):
56 04 52 E0 2E C4 09 F0 0A 12 FF 01 00
```

## Implementation Guidelines

### Endianness
- All multi-byte fields use little-endian encoding
- Consistent across all platforms and architectures

### Memory Alignment
- Packed structure with no padding bytes
- Total size exactly 13 bytes

### Safe Serialization
- Use explicit `to_le_bytes`/`from_le_bytes` (no `transmute`)
- Provide golden test vectors (see `docs/technical/ARXOBJECT_WIRE_FORMAT.md`)

---

*"Thirteen bytes contain the universe of building intelligence. Every bit counts, every byte matters."*