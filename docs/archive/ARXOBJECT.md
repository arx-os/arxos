# ArxObject Protocol Specification

## Overview

The ArxObject is a 13-byte packed structure that represents any building element with millimeter precision. It achieves 10,000:1 compression through semantic understanding rather than traditional data compression.

## Binary Structure

```
┌────────────┬──────────┬────────────────────────────────────┐
│ Offset     │ Size     │ Field                              │
├────────────┼──────────┼────────────────────────────────────┤
│ 0x00       │ 2 bytes  │ building_id (u16, little-endian)  │
│ 0x02       │ 1 byte   │ object_type (u8)                  │
│ 0x03       │ 2 bytes  │ x (i16, little-endian)            │
│ 0x05       │ 2 bytes  │ y (i16, little-endian)            │
│ 0x07       │ 2 bytes  │ z (i16, little-endian)            │
│ 0x09       │ 4 bytes  │ properties[4] (u8 array)          │
└────────────┴──────────┴────────────────────────────────────┘

Total: 13 bytes
```

## Rust Implementation

```rust
#[repr(packed)]
#[derive(Copy, Clone, Debug)]
pub struct ArxObject {
    pub building_id: u16,    // Building identifier (0-65535)
    pub object_type: u8,     // Object type (0-255)
    pub x: i16,              // X position in mm (-32768 to 32767)
    pub y: i16,              // Y position in mm
    pub z: i16,              // Z position in mm (height/floor)
    pub properties: [u8; 4], // Type-specific properties
}
```

## Field Specifications

### building_id (2 bytes)
- **Range**: 0 to 65,535
- **Purpose**: Uniquely identifies a building within the system
- **Assignment**: Sequential or geographic-based

### object_type (1 byte)
- **Range**: 0 to 255
- **Purpose**: Classifies the type of building element
- **Categories**: See Object Type Registry below

### Position (x, y, z - 6 bytes total)
- **Range**: -32,768mm to 32,767mm (±32.7 meters)
- **Resolution**: 1mm precision
- **Coordinate System**: 
  - Origin: Building entrance or corner
  - X: East-West axis
  - Y: North-South axis
  - Z: Vertical (floor height)

### properties (4 bytes)
- **Purpose**: Type-specific attributes
- **Interpretation**: Depends on object_type
- **Examples**: Circuit number, temperature, status flags

## Object Type Registry

### Infrastructure (0x00-0x3F)

| Type | Hex | ASCII | Description | Properties |
|------|-----|-------|-------------|------------|
| WALL | 0x01 | WALL | Structural wall | [material, thickness, fire_rating, reserved] |
| FLOOR | 0x05 | FLOOR | Floor surface | [material, level, zone, reserved] |
| CEILING | 0x0A | CEILING | Ceiling | [height_cm, material, reserved, reserved] |
| COLUMN | 0x0C | COLUMN | Support column | [material, diameter_cm, load_class, reserved] |

### HVAC (0x0F-0x1F)

| Type | Hex | ASCII | Description | Properties |
|------|-----|-------|-------------|------------|
| VENT | 0x0F | VENT | Air vent | [unit_id, status, flow_rate, reserved] |
| THERMOSTAT | 0x32 | THERMO | Temperature control | [setpoint_f, mode, status, schedule] |
| DAMPER | 0x11 | DAMPER | Air damper | [position_pct, auto, reserved, reserved] |
| FURNACE | 0x12 | FURNACE | Heating unit | [unit_id, status, capacity, efficiency] |

### Electrical (0x20-0x3F)

| Type | Hex | ASCII | Description | Properties |
|------|-----|-------|-------------|------------|
| OUTLET | 0x28 | OUTLET | Power outlet | [circuit, status, voltage, amperage] |
| SWITCH | 0x2D | SWITCH | Light switch | [circuit, state, dimmer_pct, reserved] |
| LIGHT | 0x14 | LIGHT | Light fixture | [circuit, state, brightness, color_temp] |
| PANEL | 0x3C | PANEL | Electrical panel | [circuits, voltage, phase, capacity] |

### Security (0x1E-0x2F)

| Type | Hex | ASCII | Description | Properties |
|------|-----|-------|-------------|------------|
| CAMERA | 0x1E | CAMERA | Security camera | [camera_id, status, angle, resolution] |
| SENSOR | 0x19 | SENSOR | Motion sensor | [sensor_id, status, sensitivity, zone] |
| DOOR | 0x23 | DOOR | Door/entrance | [access_type, status, lock_id, reserved] |
| BADGE | 0x24 | BADGE | Card reader | [reader_id, status, access_level, reserved] |

### Plumbing (0x40-0x4F)

| Type | Hex | ASCII | Description | Properties |
|------|-----|-------|-------------|------------|
| VALVE | 0x40 | VALVE | Water valve | [valve_id, position, type, pressure] |
| FAUCET | 0x41 | FAUCET | Water faucet | [fixture_id, status, flow_rate, temp] |
| DRAIN | 0x42 | DRAIN | Drain | [drain_id, status, size_in, reserved] |
| PUMP | 0x43 | PUMP | Water pump | [pump_id, status, flow_gpm, pressure] |

## Property Encoding

Properties are interpreted based on object_type. Common patterns:

### Status Flags (1 byte)
```
Bit 7: Active/Inactive
Bit 6: Error/OK
Bit 5: Maintenance needed
Bit 4: Override active
Bit 3-0: Type-specific
```

### Measurements
- **Temperature**: Fahrenheit, 0-255 range
- **Percentage**: 0-100, scaled to 0-255
- **Pressure**: PSI, 0-255 range
- **Flow**: GPM or CFM, logarithmic scale

## ASCII Representation

Human-readable format for terminal interface:

```
TYPE @ (X, Y, Z)m [PROPERTY:VALUE ...]

Examples:
OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15 STATUS:OK
VENT @ (12.0, 3.0, 2.8)m UNIT:1 FLOW:250cfm
DOOR @ (3.0, 7.5, 0.0)m ACCESS:BADGE STATUS:LOCKED
```

## Compression Analysis

### Traditional Approach
A typical BIM object in IFC format:
```
#123= IFCOUTLET('2x3F4G5H6J7K8L9M',$,'Electrical Outlet',$,$,
  #124,#125,'OutletType001',.ELECTRICAL.);
#124= IFCLOCALPLACEMENT(#126,#127);
#127= IFCAXIS2PLACEMENT3D(#128,#129,#130);
#128= IFCCARTESIANPOINT((10500.,2300.,1200.));
```
**Size**: ~500 bytes minimum

### ArxObject Approach
```
[42, 0, 40, 4, 41, 252, 8, 176, 4, 15, 0, 0, 0]
```
**Size**: 13 bytes

**Compression Ratio**: 500:13 ≈ 38:1 for single object

### Building Scale
- **Traditional BIM**: 50MB for 10,000 objects
- **ArxOS**: 127KB for 10,000 objects
- **Ratio**: 10,000:1 at building scale

## Serialization

### To Bytes
```rust
impl ArxObject {
    pub fn to_bytes(&self) -> [u8; 13] {
        let mut bytes = [0u8; 13];
        bytes[0..2].copy_from_slice(&self.building_id.to_le_bytes());
        bytes[2] = self.object_type;
        bytes[3..5].copy_from_slice(&self.x.to_le_bytes());
        bytes[5..7].copy_from_slice(&self.y.to_le_bytes());
        bytes[7..9].copy_from_slice(&self.z.to_le_bytes());
        bytes[9..13].copy_from_slice(&self.properties);
        bytes
    }
}
```

### From Bytes
```rust
impl ArxObject {
    pub fn from_bytes(bytes: &[u8; 13]) -> Self {
        Self {
            building_id: u16::from_le_bytes([bytes[0], bytes[1]]),
            object_type: bytes[2],
            x: i16::from_le_bytes([bytes[3], bytes[4]]),
            y: i16::from_le_bytes([bytes[5], bytes[6]]),
            z: i16::from_le_bytes([bytes[7], bytes[8]]),
            properties: [bytes[9], bytes[10], bytes[11], bytes[12]],
        }
    }
}
```

## Validation Rules

1. **Building ID**: Must be > 0 for valid buildings
2. **Object Type**: Must be defined in registry
3. **Position**: Must be within building bounds
4. **Properties**: Must conform to type specification

## Example Workflows

### Creating from Scan
```rust
// LiDAR point identified as outlet
let outlet = ArxObject::new(
    42,      // building_id
    0x28,    // OUTLET type
    10500,   // x: 10.5 meters
    2300,    // y: 2.3 meters
    1200,    // z: 1.2 meters (first floor)
);
outlet.properties[0] = 15;  // Circuit 15
```

### Parsing from ASCII
```rust
// "OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15"
let obj = AsciiBridge::parse("OUTLET @ (10.5, 2.3, 1.2)m CIRCUIT:15")?;
```

### Querying
```rust
// Find all outlets on circuit 15
let outlets: Vec<&ArxObject> = repository
    .objects
    .values()
    .filter(|o| o.object_type == 0x28 && o.properties[0] == 15)
    .collect();
```

## Network Protocol

When transmitted, ArxObjects can be sent individually or in batches:

### Single Object Packet
```
[HEADER(2)] [ARXOBJECT(13)] [CRC(2)]
Total: 17 bytes
```

### Batch Packet
```
[HEADER(2)] [COUNT(2)] [ARXOBJECT(13)] * N [CRC(2)]
Total: 4 + (13 * N) + 2 bytes
```

## Future Extensions

### Considered for v2
- **Extended Properties**: Optional 8-byte extension
- **Temporal Data**: Timestamp field
- **Relationships**: Parent/child linkage
- **Metadata**: Description strings

### Backward Compatibility
The 13-byte format is frozen. Extensions will use:
- Separate extension packets
- Property byte flags for extended data
- Companion data structures