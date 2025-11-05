# Building Data Examples

This directory contains example building data files demonstrating the ArxOS building data structure and format.

## 📁 Available Examples

### [`building.yaml`](./building.yaml) - Complete Office Building
**Best for:** Understanding full building structure with equipment

A complete example showing:
- ✅ Multiple floors (Ground Floor, First Floor)
- ✅ Multiple room types (Lobby, Conference, Office)
- ✅ Equipment examples (HVAC, Electrical, AV)
- ✅ Proper spatial data (positions, bounding boxes)
- ✅ Equipment-room relationships
- ✅ Universal paths
- ✅ Complete metadata

**Use this example when:**
- Learning the full building data structure
- Understanding equipment placement
- Seeing room-equipment relationships
- Testing equipment-related features

---

### [`minimal-building.yaml`](./minimal-building.yaml) - Minimal Valid Building
**Best for:** Quick reference, understanding required fields

A minimal example showing:
- ✅ Only required fields
- ✅ Valid empty structure
- ✅ Basic coordinate system
- ✅ Proper metadata structure

**Use this example when:**
- Understanding minimum required fields
- Creating a new building from scratch
- Testing validation logic
- Learning the basic structure

---

### [`multi-floor-building.yaml`](./multi-floor-building.yaml) - Multi-Floor Building
**Best for:** Understanding hierarchical structure across multiple floors

A comprehensive example showing:
- ✅ Multiple floors (Basement, Ground, First, Second)
- ✅ Different elevations
- ✅ Various room types (Mechanical, Lobby, Office, Conference)
- ✅ Floor-level organization
- ✅ Proper elevation tracking

**Use this example when:**
- Working with multi-story buildings
- Understanding floor hierarchies
- Testing elevation calculations
- Learning spatial organization

---

## 🚀 Quick Start

### Using Examples with ArxOS CLI

```bash
# Validate an example file
arx validate --path examples/buildings/building.yaml

# Import an example (if it were an IFC file)
arx import examples/buildings/building.yaml

# View building structure
arx browse --building "Example Office Building"

# Search for equipment
arx search "HVAC" --path examples/buildings/

# Render building visualization
arx render --building "Example Office Building" --three-d
```

### Using Examples Programmatically

```rust
use arxos::yaml::BuildingData;
use std::fs;

// Load example building data
let yaml_content = fs::read_to_string("examples/buildings/building.yaml")?;
let building_data: BuildingData = serde_yaml::from_str(&yaml_content)?;

// Access building information
println!("Building: {}", building_data.building.name);
println!("Floors: {}", building_data.floors.len());

// Iterate through floors
for floor in &building_data.floors {
    println!("Floor: {} (Level {})", floor.name, floor.level);
    println!("  Rooms: {}", floor.rooms.len());
    println!("  Equipment: {}", floor.equipment.len());
}
```

---

## 📊 Data Structure

All building files follow this structure:

```yaml
building:
  id: string                    # Unique identifier
  name: string                  # Human-readable name
  description: string?           # Optional description
  created_at: datetime          # ISO 8601 timestamp
  updated_at: datetime          # ISO 8601 timestamp
  version: string               # Version string
  global_bounding_box: BoundingBox?  # Optional global bounds

metadata:
  source_file: string?          # Source IFC file (if imported)
  parser_version: string        # ArxOS parser version
  total_entities: usize        # Total entity count
  spatial_entities: usize       # Spatial entity count
  coordinate_system: string     # Coordinate system name
  units: string                 # Units (meters, feet, etc.)
  tags: string[]                # Tags for categorization

floors:
  - id: string                  # Floor identifier
    name: string                # Floor name
    level: i32                   # Floor level (0 = ground, negative = basement)
    elevation: f64               # Elevation in meters
    rooms: RoomData[]            # Rooms on this floor
    equipment: EquipmentData[]   # Equipment on this floor
    bounding_box: BoundingBox?  # Floor bounding box

coordinate_systems:
  - name: string                # Coordinate system name
    origin: Point3D              # Origin point
    x_axis: Point3D              # X-axis direction
    y_axis: Point3D              # Y-axis direction
    z_axis: Point3D              # Z-axis direction
    description: string?        # Optional description
```

---

## 🔍 Key Concepts

### Coordinate Systems
All spatial data uses coordinate systems defined in `coordinate_systems`. The default "World" coordinate system uses meters as units with origin at (0, 0, 0).

### Universal Paths
Equipment has `universal_path` fields following the pattern:
```
/BUILDING/{building-name}/FLOOR-{level}/ROOM-{room-name}/EQUIPMENT/{equipment-name}
```

### Room-Equipment Relationships
- Equipment is listed in `floor.equipment[]`
- Rooms reference equipment via `room.equipment[]` (equipment IDs)
- Equipment `universal_path` includes room information

### Equipment Status
Equipment status values:
- `Healthy` - Operating normally
- `Warning` - Needs attention
- `Critical` - Requires immediate action
- `Unknown` - Status unknown

### Equipment Types
Supported equipment types:
- `HVAC` - Heating, ventilation, air conditioning
- `Electrical` - Electrical systems
- `AV` - Audio/visual equipment
- `Furniture` - Furniture items
- `Safety` - Safety equipment
- `Plumbing` - Plumbing systems
- `Network` - Network infrastructure

---

## 📝 Notes

### Data Quality
- ✅ All examples use clean, human-readable names
- ✅ Coordinates are normalized to meters
- ✅ Precision is reasonable (3 decimal places)
- ✅ Metadata is accurate and consistent
- ✅ Equipment examples demonstrate all types

### File Format
- All files use YAML format
- UTF-8 encoding
- Follow ArxOS BuildingData schema
- Validated against current schema

### Version Compatibility
- Examples are compatible with ArxOS v2.0+
- Schema matches current `BuildingData` structure
- Examples are updated when schema changes

---

## 🔗 Related Documentation

- **[User Guide](../../docs/core/USER_GUIDE.md)** - Complete usage guide
- **[API Reference](../../docs/core/API_REFERENCE.md)** - API documentation
- **[Architecture](../../docs/core/ARCHITECTURE.md)** - System architecture
- **[IFC Processing](../../docs/features/IFC_PROCESSING.md)** - IFC import guide

---

## 🛠️ Contributing

When adding new examples:

1. **Use human-readable names** - No obfuscated IDs
2. **Clean coordinates** - Round to 3 decimal places, normalize to meters
3. **Complete metadata** - Ensure `total_entities` and `spatial_entities` match content
4. **Validate structure** - Ensure file matches `BuildingData` schema
5. **Add documentation** - Update this README with new example description

---

## 📄 License

Examples are provided under the same license as ArxOS (MIT License).
