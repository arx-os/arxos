# Nanometer Precision Coordinate System

## Overview

Arxos now uses **int64 nanometer precision** for all spatial coordinates, enabling seamless zooming from campus scale (kilometers) down to circuit board traces (nanometers). This is essential for the platform's vision of integrating with open source hardware, IoT devices, and manufacturing-level detail.

## Why Nanometer Precision?

### The Vision
- **Campus to Circuit**: Navigate from a building exterior down to individual PCB traces
- **Open Hardware Integration**: Import KiCad designs, manage network ports, configure IoT at the chip level
- **Universal Platform**: Single coordinate system for everything from cities to semiconductors

### Scale Range
With int64 nanometers, we support:
- **Range**: ±9,223,372 kilometers (can map entire continents)
- **Precision**: 1 nanometer (smaller than modern transistors)
- **Use Cases**:
  - Campus/building navigation (km to m scale)
  - Room and equipment placement (m to cm scale)
  - IoT device configuration (cm to mm scale)
  - PCB layout and traces (mm to μm scale)
  - Chip-level details (μm to nm scale)

## Technical Implementation

### Go Backend

```go
// Unit constants (core/arxobject/arxobject.go)
const (
    Nanometer  int64 = 1
    Micrometer int64 = 1000           // 1 μm = 1000 nm
    Millimeter int64 = 1000000        // 1 mm = 1,000,000 nm
    Meter      int64 = 1000000000     // 1 m = 1,000,000,000 nm
    Kilometer  int64 = 1000000000000  // 1 km = 10^12 nm
)

// ArxObject structure
type ArxObject struct {
    X, Y, Z       int64  // Position in nanometers
    Length, Width int64  // Dimensions in nanometers
    Height        int64
    ScaleLevel    uint8  // 0=circuit, 1=component, 2=room, 3=building, 4=campus
}
```

### Conversion Helpers

```go
// Convert for display
func (a *ArxObject) GetPositionMeters() (x, y, z float64) {
    return float64(a.X) / float64(Meter),
           float64(a.Y) / float64(Meter),
           float64(a.Z) / float64(Meter)
}

// Set from common units
func (a *ArxObject) SetPositionMillimeters(x, y, z float64) {
    a.X = int64(x * float64(Millimeter))
    a.Y = int64(y * float64(Millimeter))
    a.Z = int64(z * float64(Millimeter))
}
```

### JavaScript Frontend

```javascript
// Coordinate system with BigInt for precision
const Units = {
    Nanometer: 1n,
    Micrometer: 1000n,
    Millimeter: 1000000n,
    Meter: 1000000000n,
    Kilometer: 1000000000000n
};

// Handle large coordinates without precision loss
class ArxObjectNano {
    constructor(data) {
        this.x = BigInt(data.x || 0);
        this.y = BigInt(data.y || 0);
        this.z = BigInt(data.z || 0);
    }
}
```

### Database Schema

```sql
-- PostgreSQL with BIGINT columns
ALTER TABLE arx_objects 
    ADD COLUMN x_nano BIGINT,      -- ±9.2 million km range
    ADD COLUMN y_nano BIGINT,      -- 1 nm precision
    ADD COLUMN z_nano BIGINT,
    ADD COLUMN length_nano BIGINT,
    ADD COLUMN width_nano BIGINT,
    ADD COLUMN height_nano BIGINT;

-- Conversion functions
CREATE FUNCTION nano_to_meters(nano BIGINT) 
RETURNS DOUBLE PRECISION AS $$
    SELECT nano::DOUBLE PRECISION / 1000000000.0;
$$ LANGUAGE SQL IMMUTABLE;
```

## Scale Levels

The system uses scale levels to optimize rendering and data fetching:

| Level | Name      | Typical Range        | Objects                           |
|-------|-----------|---------------------|-----------------------------------|
| 4     | CAMPUS    | 100m - 10km         | Buildings, roads, infrastructure |
| 3     | BUILDING  | 1m - 100m           | Walls, floors, structural        |
| 2     | ROOM      | 10cm - 10m          | Furniture, equipment, fixtures    |
| 1     | COMPONENT | 1mm - 1m            | Devices, sensors, outlets, ports  |
| 0     | CIRCUIT   | 1nm - 10mm          | PCB traces, chips, transistors    |

## Migration Path

### From Millimeter (int32) to Nanometer (int64)

1. **Backward Compatibility**: New functions accept meters/millimeters for easy migration
2. **Database Migration**: Script converts existing millimeter data to nanometers
3. **API Compatibility**: Endpoints accept both coordinate systems during transition

### Example Migration

```go
// Old code (millimeters)
obj.X = int32(x * 1000)  // meters to mm

// New code (nanometers) 
obj.X = int64(x * float32(Meter))  // meters to nm

// Or use helpers
obj.SetPositionMeters(x, y, z)
```

## Use Cases

### Network Management
```go
// Create a network port at specific position on switch
port := &ArxObject{
    Type: NetworkPort,
    X: switchX + int64(portIndex * 25400000), // 1 inch spacing
    Y: switchY,
    Z: switchZ,
    Width: 15*Millimeter,  // RJ45 width
    Height: 12*Millimeter, // RJ45 height
}
```

### PCB Integration
```go
// Import PCB trace with 0.2mm width
trace := &ArxObject{
    Type: Trace,
    X: boardX + 50*Millimeter,
    Y: boardY + 25*Millimeter, 
    Width: 200*Micrometer,  // 0.2mm trace
    ScaleLevel: 0,  // Circuit level
}
```

### IoT Sensor Placement
```go
// Place temperature sensor in room
sensor := &ArxObject{
    Type: Sensor,
    X: roomCenterX,
    Y: roomCenterY,
    Z: 2500*Millimeter,  // 2.5m height
    ScaleLevel: 1,  // Component level
}
```

## Performance Considerations

- **Storage**: 24 bytes for position (3 × int64) vs 12 bytes (3 × int32)
- **Computation**: Modern CPUs handle int64 efficiently
- **Network**: Coordinates compress well due to locality
- **Caching**: Scale-based caching reduces data transfer

## Future Extensions

### Planned Features
- **Time dimension**: int64 nanoseconds for 4D building history
- **Rotation precision**: Milliarcseconds for astronomical alignment
- **Material properties**: Nanometer-scale surface roughness
- **Quantum scale**: Sub-nanometer for semiconductor physics

### CLI Integration
The nanometer precision enables powerful CLI operations:
```bash
# Query objects at PCB scale
arxos query --scale=circuit --center=0,0,0 --radius=100mm

# Navigate to specific chip pin
arxos goto --object=U1 --pin=24 --zoom=micrometer

# Measure trace width
arxos measure --from=pad1 --to=pad2 --unit=mil
```

## Best Practices

1. **Always use constants**: Never hardcode unit conversions
2. **Choose appropriate scale**: Set ScaleLevel for rendering optimization  
3. **Use helpers**: Leverage conversion functions for clarity
4. **Think in meters**: Default to meters for human-scale objects
5. **Document units**: Always specify units in comments and APIs

## Conclusion

The int64 nanometer coordinate system future-proofs Arxos for integration with:
- Open source hardware projects
- Manufacturing and fabrication systems
- IoT and embedded devices
- Building automation systems
- Network infrastructure management

This positions Arxos as the universal spatial platform for all physical infrastructure, from continental power grids down to individual transistors.