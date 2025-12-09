# IFC Import/Export

Working with Industry Foundation Classes (IFC) files in ArxOS.

---

## Overview

ArxOS supports importing and exporting IFC files, the industry standard format for Building Information Modeling (BIM). IFC files contain 3D geometry, spatial hierarchies, and equipment metadata.

**Supported IFC Versions:**
- IFC2x3
- IFC4

---

## Import

### Basic Import

```bash
# Import IFC file to building.yaml
arx import building.ifc

# Preview import without changes
arx import building.ifc --dry-run

# Import from URL
arx import https://example.com/building.ifc
```

### What Gets Imported

The IFC parser extracts:

- **Building structure** – Floors, rooms, zones
- **Equipment** – HVAC, electrical, plumbing systems
- **Geometry** – 3D coordinates and bounding boxes
- **Properties** – Manufacturer, model, install date
- **Relationships** – Equipment-to-room assignments

### Import Process

```
IFC File
  ↓
Parse IFC entities (IFCBUILDING, IFCSPACE, IFCEQUIPMENT, etc.)
  ↓
Extract spatial hierarchy
  ↓
Build floor/room structure
  ↓
Extract equipment and properties
  ↓
Generate ArxAddress for each fixture
  ↓
Write building.yaml
  ↓
Git commit "Imported from building.ifc"
```

---

## Supported IFC Entities

### Spatial Entities

| IFC Entity | ArxOS Mapping |
|------------|---------------|
| `IFCBUILDING` | Building |
| `IFCBUILDINGSTOREY` | Floor |
| `IFCSPACE` | Room |
| `IFCZONE` | Wing (optional grouping) |

### Equipment Entities

| IFC Entity | Equipment Type |
|------------|----------------|
| `IFCAIRTERMINAL` | HVAC |
| `IFCBOILER` | HVAC |
| `IFCCHILLER` | HVAC |
| `IFCFAN` | HVAC |
| `IFCPUMP` | Plumbing |
| `IFCVALVE` | Plumbing |
| `IFCLAMP` | Lighting |
| `IFCLIGHTFIXTURE` | Lighting |
| `IFCOUTLET` | Electrical |
| `IFCSWITCHINGDEVICE` | Electrical |
| `IFCELECTRICMOTOR` | Electrical |
| `IFCFIREALARM` | Fire Safety |
| `IFCFIRESUPRESSION` | Fire Safety |
| `IFCSENSOR` | Sensor (type inferred) |

### Geometry Entities

| IFC Entity | Extracted Data |
|------------|----------------|
| `IFCEXTRUDEDAREASOLID` | 3D coordinates, bounding box |
| `IFCPOLYLINE` | Room boundaries |
| `IFCCARTESIANPOINT` | Point locations |
| `IFCAXIS2PLACEMENT3D` | Equipment placement |

---

## Property Extraction

IFC properties are mapped to ArxOS equipment properties:

**IFC Property Set:**
```
IFCEQUIPMENT
  → Pset_ManufacturerTypeInformation
    → Manufacturer: "Carrier"
    → ModelLabel: "AHU-5000"
    → ArticleNumber: "AHU-5K-001"
```

**ArxOS Equipment:**
```yaml
equipment:
  - name: "AHU-5000"
    equipment_type: "HVAC"
    properties:
      manufacturer: "Carrier"
      model: "AHU-5000"
      article_number: "AHU-5K-001"
```

---

## Export

### Export to IFC

```bash
# Export current building to IFC
arx export --format ifc --output building-v2.ifc

# Export only changes (delta mode)
arx export --format ifc --output changes.ifc --delta
```

### Export Formats

ArxOS supports multiple export formats:

#### IFC (`.ifc`)
```bash
arx export --format ifc --output building.ifc
```

Industry standard BIM format. Includes:
- Full spatial hierarchy
- Equipment with properties
- 3D geometry (if available)
- Relationships

#### glTF (`.gltf` / `.glb`)
```bash
arx export --format gltf --output model.gltf
```

3D graphics format for web visualization. Includes:
- Building geometry
- Room meshes
- Equipment locations
- Materials and textures

#### USDZ (`.usdz`)
```bash
arx export --format usdz --output model.usdz
```

Apple's AR Quick Look format. Includes:
- 3D geometry
- Optimized for mobile AR
- iOS-compatible packaging

---

## Configuration

### IFC Parser Configuration

Configure IFC import behavior in `.arxos/config.toml`:

```toml
[ifc]
# Skip invalid entities instead of failing
skip_invalid_entities = true

# Extract 3D geometry (slower but more accurate)
extract_geometry = true

# Generate equipment addresses automatically
auto_generate_addresses = true

# Coordinate system
coordinate_system = "World"

# Units
units = "meters"
```

---

## Troubleshooting

### Import Failures

**Error:** `IFC file not found`
```bash
# Check file path
ls -l building.ifc

# Use absolute path
arx import /full/path/to/building.ifc
```

**Error:** `Invalid IFC format`
```bash
# Verify IFC version
head -n 5 building.ifc

# Should show:
# ISO-10303-21;
# HEADER;
# FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
```

**Error:** `Failed to parse entity`
```bash
# Use dry-run to identify issues
arx import building.ifc --dry-run

# Enable detailed logging
RUST_LOG=debug arx import building.ifc
```

### Export Failures

**Error:** `Missing geometry data`

IFC export requires 3D coordinates. If missing:
```bash
# Check if building has geometry
arx validate --path building.yaml

# Import with geometry extraction
arx import source.ifc  # Geometry auto-extracted
```

**Error:** `Unsupported IFC version`

Export targets IFC4 by default. For IFC2x3:
```bash
arx export --format ifc --output building-2x3.ifc --ifc-version 2x3
```

---

## Geometry Handling

### Coordinate Systems

IFC files use various coordinate systems. ArxOS normalizes to:

- **Origin:** Building origin (0, 0, 0)
- **X-axis:** East
- **Y-axis:** North
- **Z-axis:** Up (elevation)

### Bounding Boxes

Each entity has a bounding box:

```yaml
equipment:
  - name: "HVAC-AHU-01"
    location:
      x: 10.5
      y: 5.2
      z: 2.8
    bounding_box:
      min: { x: 9.5, y: 4.2, z: 2.0 }
      max: { x: 11.5, y: 6.2, z: 3.6 }
```

Used for:
- Spatial queries
- Collision detection
- 3D visualization
- Room assignments

---

## Advanced Usage

### Batch Import

Import multiple IFC files:

```bash
for file in *.ifc; do
  arx import "$file"
done
```

### Merge IFC Files

Import multiple disciplines:

```bash
# Architecture
arx import Building-Architecture.ifc

# HVAC
arx import Building-HVAC.ifc

# Electrical
arx import Building-Electrical.ifc

# All merged into single building.yaml
```

### Selective Import

Import only specific floors:

```bash
# Manual: Edit IFC file, keep only desired IFCBUILDINGSTOREY
# Then import
arx import building-floor-2-only.ifc
```

### Custom Property Mapping

Define custom property mappings in config:

```toml
[ifc.property_mapping]
"Pset_Custom.CustomField" = "properties.custom_field"
"Pset_Warranty.WarrantyDate" = "properties.warranty_date"
```

---

## Performance

### Large IFC Files

For large IFC files (> 100 MB):

```bash
# Enable parallel processing
arx config --set performance.max_parallel_threads=16

# Increase memory limit
arx config --set performance.memory_limit_mb=4096

# Disable geometry extraction for speed
arx config --set ifc.extract_geometry=false
```

### Import Progress

Monitor import progress:

```bash
# Enable verbose output
arx import large-building.ifc --verbose

# Shows:
# ✓ Parsed 1000 entities
# ✓ Parsed 2000 entities
# ...
# ✓ Import complete: 5432 entities processed
```

---

## Validation

### Validate Imported Data

After import, validate the result:

```bash
# Run validation
arx validate

# Check for issues:
# ✓ Building structure valid
# ✓ All rooms have valid types
# ✓ All equipment has addresses
# ✓ All coordinates within bounds
# ✓ No duplicate IDs
```

### Common Issues

**Missing rooms:**
- IFC file may not contain `IFCSPACE` entities
- Solution: Manually add rooms to building.yaml

**Incorrect equipment types:**
- IFC entity type may not map cleanly
- Solution: Update `equipment_type` manually

**Missing properties:**
- IFC file may lack property sets
- Solution: Add properties manually or from documentation

---

## IFC Standards

### IFC2x3 vs IFC4

| Feature | IFC2x3 | IFC4 |
|---------|--------|------|
| Spatial hierarchy | Full | Full |
| Equipment entities | Basic | Extended |
| Geometry | Basic solids | Advanced BREP |
| Property sets | Standard | Enhanced |
| Relationships | Basic | Advanced |

**Recommendation:** Use IFC4 when possible for better property support.

### Certification

IFC files should follow buildingSMART standards:

- **MVD** (Model View Definition): CoordinationView preferred
- **Validation:** Use IfcOpenShell or buildingSMART validators
- **Compliance:** Check with `arx validate`

---

## Examples

### Complete Import Workflow

```bash
# 1. Preview import
arx import building.ifc --dry-run

# 2. Import to Git repository
arx import building.ifc

# 3. Validate result
arx validate

# 4. View building structure
arx render --building "My Building"

# 5. Check Git history
arx history

# 6. Export to glTF for web viewer
arx export --format gltf --output model.gltf
```

### Round-Trip Test

```bash
# Import original IFC
arx import original.ifc

# Export to IFC
arx export --format ifc --output exported.ifc

# Compare
diff original.ifc exported.ifc
```

---

**See Also:**
- [Getting Started](./getting-started.md) – Basic workflows
- [Data Format](./data-format.md) – Understanding building.yaml structure
- [CLI Reference](./cli-reference.md) – Complete command documentation
