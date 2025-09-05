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

### Binary Layout
```rust
#[repr(C, packed)]
pub struct ArxObject {
    pub building_id: u16,    // 2 bytes - Building identifier (65,536 buildings)
    pub object_type: u8,     // 1 byte  - Object type (256 types)
    pub x: i16,             // 2 bytes - X position in millimeters (±32.7m)
    pub y: i16,             // 2 bytes - Y position in millimeters (±32.7m)  
    pub z: i16,             // 2 bytes - Z position in millimeters (±32.7m)
    pub properties: [u8; 4], // 4 bytes - Type-specific properties
}
// Total: 13 bytes typical (atomic unit)
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

### The Fractal Principle

ArxObjects are **fractal** - they represent different levels of detail based on perspective and available bandwidth:

```
Zoom Level 1: Atomic (13 bytes)
├── Single outlet location
└── Basic properties

Zoom Level 2: Contextual (26-52 bytes)
├── Outlet + circuit relationship
├── Connected devices
└── Power consumption

Zoom Level 3: System (100+ bytes)
├── All outlets on circuit
├── Breaker panel connection
└── Load calculations

Zoom Level 4: Building (compressed back to ~13 bytes)
├── Statistical summary
└── "47 circuits, 3-phase power"
```

### Bandwidth-Driven Sizing

ArxObject size emerges from RF constraints, not protocol requirements:

```rust
// For 2D Terminal View (minimal bandwidth)
struct Basic2DUpdate {
    room_id: u16,          // 2 bytes
    object: ArxObject,     // ~13 bytes
    // Total: ~15 bytes (fits in single LoRa packet)
}

// For 3D ASCII "CAD" View (when bandwidth allows)
struct Enhanced3DUpdate {
    room_id: u16,          // 2 bytes
    object: ArxObject,     // ~13 bytes
    position_precise: [f32; 3], // 12 bytes
    orientation: f32,      // 4 bytes
    visual_hints: u8,      // 1 byte
    // Total: ~32 bytes (still fits in single packet)
}

// Full Room Sync (progressive download)
struct RoomData {
    geometry: Vec<Wall>,   // ~100 bytes
    objects: Vec<ArxObject>, // N × 13 bytes
    // Sent over multiple packets as bandwidth permits
}
```

### Real-World Transmission Times

Based on LoRa constraints (0.3-50 kbps):

| Data Type | Size | Time @ 50kbps | Time @ 0.3kbps | Mesh Hops (3x) |
|-----------|------|---------------|----------------|----------------|
| Single Outlet | 13 bytes | 0.002s | 0.35s | 1-3s |
| 2D Room Update | 104 bytes | 0.02s | 2.8s | 3-30s |
| 3D Room Render | 352 bytes | 0.06s | 9.4s | 6-60s |
| Building Sync | ~10KB | 1.6s | 267s | 5-15 min |

**Key Insight**: 30-60 second latency is completely acceptable for building information - buildings don't change that fast!

## Object Type Registry

### Structural Elements (0x01-0x0F)
```rust
const WALL:    u8 = 0x01;  // Wall segment
const DOOR:    u8 = 0x02;  // Door or opening
const WINDOW:  u8 = 0x03;  // Window
const FLOOR:   u8 = 0x04;  // Floor surface
const CEILING: u8 = 0x05;  // Ceiling surface
const COLUMN:  u8 = 0x06;  // Structural column
const BEAM:    u8 = 0x07;  // Structural beam
const STAIR:   u8 = 0x08;  // Staircase
```

### Electrical Systems (0x10-0x1F)
```rust
const OUTLET:       u8 = 0x10;  // Electrical outlet
const SWITCH:       u8 = 0x11;  // Light switch
const PANEL:        u8 = 0x12;  // Electrical panel
const CIRCUIT:      u8 = 0x13;  // Circuit breaker
const FIXTURE:      u8 = 0x14;  // Light fixture
const CONDUIT:      u8 = 0x15;  // Electrical conduit
const JUNCTION:     u8 = 0x16;  // Junction box
const METER:        u8 = 0x17;  // Electrical meter
```

### HVAC Systems (0x20-0x2F)
```rust
const DUCT:         u8 = 0x20;  // Air duct
const VENT:         u8 = 0x21;  // Air vent
const THERMOSTAT:   u8 = 0x22;  // Temperature control
const UNIT:         u8 = 0x23;  // HVAC unit
const DAMPER:       u8 = 0x24;  // Air damper
const COIL:         u8 = 0x25;  // Heating/cooling coil
const FAN:          u8 = 0x26;  // Ventilation fan
const FILTER:       u8 = 0x27;  // Air filter
```

### Plumbing Systems (0x30-0x3F)
```rust
const PIPE:         u8 = 0x30;  // Water pipe
const VALVE:        u8 = 0x31;  // Water valve
const FIXTURE_PLUMB:u8 = 0x32;  // Plumbing fixture
const DRAIN:        u8 = 0x33;  // Drain
const PUMP:         u8 = 0x34;  // Water pump
const TANK:         u8 = 0x35;  // Water tank
const METER_WATER:  u8 = 0x36;  // Water meter
const HEATER:       u8 = 0x37;  // Water heater
```

### Network Infrastructure (0x40-0x4F)
```rust
const CABLE:        u8 = 0x40;  // Network cable
const JACK:         u8 = 0x41;  // Network jack
const SWITCH_NET:   u8 = 0x42;  // Network switch
const ACCESS_POINT: u8 = 0x43;  // Wireless access point
const ROUTER:       u8 = 0x44;  // Network router
const PATCH_PANEL:  u8 = 0x45;  // Patch panel
const RACK:         u8 = 0x46;  // Equipment rack
const FIBER:        u8 = 0x47;  // Fiber optic cable
```

### Safety Systems (0x50-0x5F)
```rust
const FIRE_ALARM:   u8 = 0x50;  // Fire alarm device
const SPRINKLER:    u8 = 0x51;  // Sprinkler head
const EXIT_SIGN:    u8 = 0x52;  // Emergency exit sign
const EXTINGUISHER: u8 = 0x53;  // Fire extinguisher
const SMOKE_DETECT: u8 = 0x54;  // Smoke detector
const HEAT_DETECT:  u8 = 0x55;  // Heat detector
const PULL_STATION: u8 = 0x56;  // Manual fire alarm
const EMERGENCY_LIGHT: u8 = 0x57; // Emergency lighting
```

### IoT & Sensors (0x60-0x6F)
```rust
const SENSOR:       u8 = 0x60;  // Generic sensor
const ACTUATOR:     u8 = 0x61;  // Generic actuator
const CONTROLLER:   u8 = 0x62;  // Control device
const CAMERA:       u8 = 0x63;  // Security camera
const BADGE_READER: u8 = 0x64;  // Access card reader
const INTERCOM:     u8 = 0x65;  // Intercom system
const DISPLAY:      u8 = 0x66;  // Digital display
const BEACON:       u8 = 0x67;  // Bluetooth beacon
```

## Type-Specific Properties

### Electrical Outlet (0x10)
```rust
// Properties byte layout for outlets
struct OutletProperties {
    voltage: u8,        // Byte 0: 120V=0x78, 240V=0xF0, 480V=0xFF
    circuit: u8,        // Byte 1: Circuit number (1-255)
    amperage: u8,       // Byte 2: Amp rating (15=0x0F, 20=0x14, 30=0x1E)
    status: u8,         // Byte 3: Status bits
}

// Status byte bit allocation
const STATUS_POWER_ON:  u8 = 0b00000001;  // Has power
const STATUS_GFCI:      u8 = 0b00000010;  // GFCI protected
const STATUS_SWITCHED:  u8 = 0b00000100;  // Switch controlled
const STATUS_USB:       u8 = 0b00001000;  // Has USB ports
const STATUS_FAULT:     u8 = 0b10000000;  // Fault detected
```

### HVAC Thermostat (0x22)
```rust
struct ThermostatProperties {
    set_temp: u8,       // Byte 0: Temperature in Fahrenheit (32-100)
    current_temp: u8,   // Byte 1: Current reading in Fahrenheit
    mode: u8,          // Byte 2: Operating mode and fan settings
    zone: u8,          // Byte 3: HVAC zone number
}

// Mode byte bit allocation
const MODE_HEAT:        u8 = 0b00000001;
const MODE_COOL:        u8 = 0b00000010;
const MODE_AUTO:        u8 = 0b00000100;
const MODE_FAN_ON:      u8 = 0b00001000;
const MODE_SCHEDULE:    u8 = 0b00010000;
const MODE_OCCUPIED:    u8 = 0b00100000;
```

### Fire Alarm Device (0x50)
```rust
struct FireAlarmProperties {
    device_type: u8,    // Byte 0: Specific alarm type
    zone: u8,          // Byte 1: Fire alarm zone
    loop: u8,          // Byte 2: Detection loop
    status: u8,        // Byte 3: Status and test results
}

// Device type values
const ALARM_SMOKE:      u8 = 0x01;
const ALARM_HEAT:       u8 = 0x02;
const ALARM_PULL:       u8 = 0x03;
const ALARM_HORN:       u8 = 0x04;
const ALARM_STROBE:     u8 = 0x05;

// Status bits
const ALARM_NORMAL:     u8 = 0b00000000;
const ALARM_ACTIVE:     u8 = 0b00000001;
const ALARM_TROUBLE:    u8 = 0b00000010;
const ALARM_SUPERVISORY: u8 = 0b00000100;
const ALARM_TEST_MODE:  u8 = 0b10000000;
```

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

Status byte 0x0B = 0b00001011:
- Power on: YES
- GFCI: YES  
- Switched: NO
- USB: YES
- Fault: NO

Complete 13-byte ArxObject:
34 02 10 50 14 A4 1F 2C 01 78 0F 14 0B
```

### Example 2: Emergency Exit Sign
```
Building: Roosevelt High School (ID: 0x0456)
Location: Main hallway exit
Position: (12.0m, 2.5m, 2.8m)
Properties: LED, Battery backup, Normal operation

ArxObject Encoding:
┌─────────────────────────────────────────────┐
│ Field       │ Bytes │ Value     │ Hex      │
├─────────────────────────────────────────────┤
│ building_id │   2   │ 1110      │ 0x0456   │
│ object_type │   1   │ EXIT_SIGN │ 0x52     │
│ x           │   2   │ 12000mm   │ 0x2EE0   │
│ y           │   2   │ 2500mm    │ 0x09C4   │
│ z           │   2   │ 2800mm    │ 0x0AF0   │
│ properties  │   4   │ LED+Batt  │ 0x12FF01 │
└─────────────────────────────────────────────┘

Complete 13-byte ArxObject:
56 04 52 E0 2E C4 09 F0 0A 12 FF 01 00
```

## ASCII Representation

ArxObjects have human-readable ASCII representations for terminal interfaces:

### Parsing Format
```
OBJECT_TYPE @ (X, Y, Z) PROPERTY:VALUE PROPERTY:VALUE ...
```

### Examples
```
OUTLET @ (5.2, 8.1, 0.3)m VOLTAGE:120V CIRCUIT:15 AMP:20 GFCI:YES

THERMOSTAT @ (3.0, 4.5, 1.5)m TEMP:72F MODE:AUTO ZONE:3

EXIT_SIGN @ (12.0, 2.5, 2.8)m TYPE:LED BATTERY:OK STATUS:NORMAL

FIRE_ALARM @ (6.5, 10.2, 3.0)m TYPE:SMOKE ZONE:2 LOOP:A STATUS:NORMAL
```

### Terminal Commands
```bash
# Query by type
arx query "outlets in building"
arx query "fire_alarms status:trouble"

# Query by location
arx query "devices in room 205"
arx query "devices near (5.0, 8.0, 1.0)m"

# Query by properties
arx query "outlets circuit:15"
arx query "thermostats temp:>75"
```

## Mesh Network Integration

### Packet Structure
ArxObjects are packed into LoRa mesh packets with minimal overhead:

```rust
struct ArxMeshPacket {
    // Meshtastic header (handled by radio layer)
    mesh_header: [u8; 16],
    
    // ArxOS application header
    building_id: u16,        // Target building
    message_type: u8,        // Query, response, update
    object_count: u8,        // Objects in this packet
    
    // ArxObject payload (up to 19 objects)
    objects: [ArxObject; 19], // 19 × 13 = 247 bytes
    
    // Integrity check
    checksum: u16,
}
// Total: 16 + 4 + 247 + 2 = 269 bytes (under LoRa 270 byte limit)
```

### Routing Efficiency
- **19 ArxObjects per packet**: Maximum utilization of LoRa bandwidth
- **13-byte efficiency**: Minimal overhead compared to traditional protocols
- **Binary compactness**: No JSON/XML parsing overhead
- **Direct routing**: Building ID enables smart routing decisions

## Compression Analysis

### Traditional BIM vs ArxObject
```
Traditional Revit Element:
├── Geometry: 2KB (tessellated mesh)
├── Properties: 1KB (material, manufacturer, etc.)
├── Relationships: 500 bytes (connections, systems)
├── Metadata: 500 bytes (creation date, author, etc.)
└── Total: ~4KB per element

ArxObject:
├── Essential geometry: 6 bytes (position only)
├── Essential properties: 4 bytes (functional data)
├── Type identification: 1 byte
├── Building context: 2 bytes
└── Total: 13 bytes per element

Compression Ratio: 4,000 ÷ 13 = 307:1
```

### Real-World Building Example
```
Typical Elementary School:
├── Revit model: 50MB (detailed geometry)
├── IFC export: 25MB (standardized format)
├── Simplified BIM: 5MB (essential elements only)
├── ArxObjects: 13KB (1,000 elements × 13 bytes)
└── Compression: 50MB ÷ 13KB = 3,846:1 ratio
```

## Validation & Quality Assurance

### Byte-Level Validation
```rust
impl ArxObject {
    pub fn validate(&self) -> Result<(), ValidationError> {
        // Check building ID is not reserved
        if self.building_id == 0x0000 || self.building_id == 0xFFFF {
            return Err(ValidationError::ReservedBuildingId);
        }
        
        // Verify object type is defined
        if !is_valid_object_type(self.object_type) {
            return Err(ValidationError::UnknownObjectType);
        }
        
        // Check position is reasonable (within ±32m)
        if self.x.abs() > 32000 || self.y.abs() > 32000 || self.z.abs() > 32000 {
            return Err(ValidationError::PositionOutOfRange);
        }
        
        // Validate type-specific properties
        self.validate_properties()?;
        
        Ok(())
    }
}
```

### Network Integrity
```rust
pub fn verify_packet_integrity(packet: &[u8; 13]) -> bool {
    // Basic structure validation
    let object = unsafe { std::mem::transmute::<[u8; 13], ArxObject>(*packet) };
    
    // Validate all fields
    object.validate().is_ok()
}
```

## Extensions & Future Compatibility

### Version Handling
```rust
// Properties field can include version information
struct VersionedProperties {
    version: u8,        // Bits 7-6 of first property byte
    data: [u8; 4],     // Remaining 30 bits for actual properties
}

const VERSION_1_0: u8 = 0b00000000;  // Current version
const VERSION_1_1: u8 = 0b01000000;  // Future version
const VERSION_2_0: u8 = 0b10000000;  // Breaking changes
```

### Custom Object Types
```rust
// Reserved ranges for extensions
const CUSTOM_START:     u8 = 0xF0;
const CUSTOM_END:       u8 = 0xFF;

// Example custom types
const SOLAR_PANEL:      u8 = 0xF0;  // Solar panel
const EV_CHARGER:       u8 = 0xF1;  // Electric vehicle charger
const BATTERY_STORAGE:  u8 = 0xF2;  // Energy storage
const DRONE_PORT:       u8 = 0xF3;  // Drone landing pad
```

## Implementation Guidelines

### Endianness
- **All multi-byte fields use little-endian encoding**
- **Consistent across all platforms and architectures**
- **Validates correctly on ARM, x86, and RISC-V processors**

### Memory Alignment
- **Packed structure with no padding bytes**
- **Total size always exactly 13 bytes**
- **Safe for direct network transmission**

### Performance Considerations
```rust
// Efficient bulk operations
impl ArxObject {
    // Fast serialization (zero-copy)
    pub fn as_bytes(&self) -> &[u8; 13] {
        unsafe { std::mem::transmute(self) }
    }
    
    // Fast deserialization (zero-copy)
    pub fn from_bytes(bytes: &[u8; 13]) -> &Self {
        unsafe { std::mem::transmute(bytes) }
    }
}
```

## Success Metrics

### Protocol Efficiency
- **13 bytes exactly**: Never exceed the size limit ✓
- **19 objects per packet**: Maximize LoRa bandwidth utilization ✓  
- **Zero padding**: No wasted bytes in structure ✓
- **Direct binary**: No encoding/decoding overhead ✓

### Semantic Completeness
- **256 object types**: Cover all common building elements ✓
- **65,536 buildings**: Support large districts ✓
- **±32m range**: Handle large buildings ✓
- **4 billion property combinations**: Rich type-specific data ✓

### Implementation Success
- **Cross-platform**: Works on embedded and desktop systems ✓
- **Network efficient**: Optimal for LoRa mesh constraints ✓
- **Human readable**: ASCII representation for debugging ✓
- **Future proof**: Versioning and extension capabilities ✓

---

*"Thirteen bytes contain the universe of building intelligence. Every bit counts, every byte matters."*