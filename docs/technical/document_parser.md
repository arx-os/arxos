# Document Parser

The Arxos Document Parser converts architectural drawings and BIM models into ASCII building representations and ArxObjects for mesh network distribution.

## Features

### Supported Formats
- **PDF**: Architectural floor plans, room schedules, equipment lists
- **IFC**: Industry Foundation Classes BIM models (IFC2X3, IFC4)

### Extraction Capabilities
- Room layouts and dimensions
- Equipment locations and types
- Building metadata (name, address, year built)
- Spatial relationships between rooms and floors
- MEP (Mechanical, Electrical, Plumbing) components

### Output Formats
- ASCII art floor plans for terminal display
- ArxObject binary format (13 bytes per object)
- JSON export for integration

## Terminal Commands

### Loading Documents
```bash
# Load a PDF floor plan
load-plan jefferson_elementary.pdf

# Load an IFC BIM model
load-plan building_model.ifc
```

### Viewing Floor Plans
```bash
# View specific floor
view-floor 1
view-floor --level=2

# List all floors
list-floors

# Show equipment on current floor
show-equipment

# Show equipment on specific floor
show-equipment 2
```

### Exporting Data
```bash
# Export as ArxObjects
export-arxobjects building.arxo

# Export to specific path
export-arxobjects /mesh/data/jefferson.arxo
```

## ASCII Rendering

The document parser converts floor plans to ASCII art for terminal viewing:

```
╔════════════════════════════════════════╗
║         FLOOR 1 - GROUND LEVEL         ║
╠════════════════════════════════════════╣
║ ┌──────────┐  ┌──────────┐            ║
║ │   127    │  │   128    │            ║
║ │ Lab [O]  │  │ Class    │            ║
║ │    [L]   │  │  [L][V]  │            ║
║ └────| |───┘  └────| |───┘            ║
║                                        ║
║ ┌──────────────────────┐              ║
║ │      129             │              ║
║ │   Computer Lab       │              ║
║ │  [O][O][O][O][D][D]  │              ║
║ └──────────| |─────────┘              ║
╚════════════════════════════════════════╝

ROOMS:
  127 - Science Lab (800 sq ft)
  128 - Classroom (600 sq ft)
  129 - Computer Lab (750 sq ft)

LEGEND:
  [O] Outlet    [L] Light     [V] Vent
  [F] Fire      [D] Data      | | Door
```

## Equipment Symbols

| Symbol | Equipment Type      | ArxObject Type |
|--------|-------------------|----------------|
| [O]    | Electrical Outlet | 0x0201         |
| [L]    | Light Fixture     | 0x0202         |
| [V]    | HVAC Vent        | 0x0301         |
| [F]    | Fire Alarm       | 0x0401         |
| [S]    | Smoke Detector   | 0x0402         |
| [E]    | Emergency Exit   | 0x0403         |
| [T]    | Thermostat       | 0x0302         |
| [/]    | Switch           | 0x0203         |
| [D]    | Data Port        | 0x0204         |
| [C]    | Security Camera  | 0x0501         |
| [*]    | Sprinkler        | 0x0404         |
| \| \|  | Door             | 0x0101         |
| [-]    | Window           | 0x0102         |

## PDF Parsing

The PDF parser extracts:
1. **Text Content**: Room schedules, equipment lists, building information
2. **Images**: Floor plan drawings for symbol detection
3. **Metadata**: Title, creation date, building details

### Room Schedule Format
The parser recognizes common room schedule patterns:
```
Room 127 - Science Lab - 800 sq ft
Room 128 - Classroom - 600 sq ft
```

### Equipment Schedule Format
```
EO-127-01  Electrical Outlet  Room 127  120V/20A
LF-128-01  Light Fixture      Room 128  LED 4000K
```

## IFC Parsing

The IFC parser extracts:
1. **Spatial Structure**: Site → Building → Storey → Space
2. **Building Elements**: Walls, doors, windows
3. **MEP Components**: Outlets, lights, HVAC terminals
4. **Properties**: Materials, dimensions, classifications

### Supported IFC Entities
- IfcBuilding, IfcBuildingStorey
- IfcSpace, IfcZone
- IfcWall, IfcDoor, IfcWindow
- IfcOutlet, IfcLightFixture
- IfcAirTerminal, IfcFireSuppressionTerminal
- IfcAlarm, IfcSensor

## ArxObject Conversion

Each equipment item is converted to a 13-byte ArxObject:

```rust
struct ArxObject {
    building_id: u16,    // Building identifier
    object_type: u16,    // Equipment type code
    x: i16,             // X position (mm)
    y: i16,             // Y position (mm)
    z: i16,             // Z position (mm)
    attributes: u8,      // Status/attributes
    checksum: u16,       // Data integrity
}
```

### Coordinate System
- Origin: Building entrance or grid reference
- Units: Millimeters (0.001m precision)
- Range: ±32.768 meters from origin

## Integration with Mesh Network

Parsed building data flows through the system:

```
PDF/IFC → Parser → ASCII/ArxObjects → Terminal → SSH → Mesh Node → RF Network
```

1. **Document Loading**: Terminal loads PDF/IFC file
2. **Parsing**: Extract rooms, equipment, structure
3. **Conversion**: Generate ArxObjects (13 bytes each)
4. **Transmission**: Send via SSH to mesh node
5. **Distribution**: Broadcast over RF network
6. **Persistence**: Store in node SQLite database

## Symbol Detection (Future)

Advanced features in development:
- Template matching for equipment symbols
- OCR for room numbers and labels
- Line detection for walls and boundaries
- Hough transform for door swings
- Connected component analysis for furniture

## Testing

Run document parser tests:
```bash
# Unit tests
cargo test document_parser::

# Integration tests
cargo test --test document_parser_integration

# Test script with sample files
./scripts/test_document_parser.sh
```

## Performance

Typical parsing performance:
- PDF (10 pages): ~500ms
- IFC (1000 entities): ~200ms
- ASCII generation: ~50ms
- ArxObject conversion: ~10ms per 100 objects

Memory usage:
- PDF parser: ~50MB for typical floor plan
- IFC parser: ~20MB per 1000 entities
- ASCII renderer: ~5MB for 5-floor building

## Limitations

Current limitations:
- PDF: Requires structured text, no OCR yet
- IFC: IFC2X3 and IFC4 only
- Images: Basic symbol detection only
- Coordinates: ±32m range from origin
- ASCII: 80x30 character display

## Future Enhancements

Planned improvements:
1. OCR integration for scanned drawings
2. Advanced symbol recognition with ML
3. 3D to 2D projection for BIM models
4. DXF/DWG support for AutoCAD files
5. Real-time updates from LiDAR scans
6. Automatic room boundary detection
7. Equipment inventory tracking
8. Energy usage estimation