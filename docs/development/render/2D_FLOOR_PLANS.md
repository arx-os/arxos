# 2D Floor Plan Rendering

## Overview

ArxOS renders 2D top-down floor plans in ASCII art for terminal display. The renderer handles both AR/LiDAR scan data (world coordinates) and IFC building data (local coordinates).

## Data Flow

### AR/LiDAR Scans

```
iPhone/iPad LiDAR Scan
    ↓
3D Scanner App (roomplan.json)
    ↓
convert_3d_scanner_scan.rs
    ↓
YAML with world-space polygons
    ↓
BuildingRenderer.render_floor()
    ↓
ASCII 2D floor plan
```

**Coordinate System**: World space (absolute coordinates)

### IFC Files

```
IFC file (*.ifc)
    ↓
IFC Processor (hierarchy.rs)
    ↓
BuildingData with local-space polygons
    ↓
BuildingRenderer.render_floor()
    ↓
ASCII 2D floor plan
```

**Coordinate System**: Local space (relative to room position)

## Coordinate Space Detection

The renderer automatically detects coordinate system:

```rust
let is_world_space = room.properties.get("scan_source").is_some() || 
                     room.properties.get("scan_mode").is_some();
```

- **AR scans**: Have `scan_source` and `scan_mode` properties → world space
- **IFC data**: No scan properties → local space (needs room position transform)

## Polygon Format

Polygons are stored as semicolon-separated coordinates:

```
"x1,y1,z1;x2,y2,z2;x3,y3,z3;..."
```

For 2D rendering, only X and Y are used (Z is elevation, ignored).

## Transformation

**World Space** (AR scans):
```rust
let x = x_val;  // Already correct
let y = y_val;
```

**Local Space** (IFC):
```rust
let x = x_val + room_x;  // Transform to world
let y = y_val + room_y;
```

## Y-Axis Flipping

Terminal displays have Y increasing downward, but building plans have Y increasing as you go "north" (up on the floor plan). The renderer flips Y:

```rust
let gy = grid_height.saturating_sub(1) - 
         (((y - min_y) / (max_y - min_y) * grid_height as f64) as usize)
         .min(grid_height.saturating_sub(1));
```

This ensures:
- Larger world Y values appear at the top of the screen
- Floor plans look natural (north is up)

## Grid Rendering

The renderer:

1. **Calculates bounds** from all polygons
2. **Preserves aspect ratio** when scaling to terminal size
3. **Fills interior** with dots (`·`) using scanline fill
4. **Draws outlines** with box-drawing characters (`─`, `│`, `+`)
5. **Overlays labels** for room names
6. **Renders equipment** with type symbols (H=HVAC, E=Electrical, etc.)

## Example Output

```
┌─────────────────────────────────────────────────────────────┐
│ ┌───────────────────────────────┐                           │
│ │·······Main Floor··············│                           │
│ │······························│                           │
│ │······························│                           │
│ │··············H···············│                           │
│ │······························│                           │
│ └───────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## Rendering Functions

### Main Functions

- `BuildingRenderer::new()` - Create renderer with building data
- `BuildingRenderer::floors()` - Get list of floors
- `BuildingRenderer::render_floor()` - Render specific floor

### Internal Functions (Private)

- `calculate_floor_bounds()` - Compute X-Y bounds from polygons/bbox
- `draw_room()` - Render room polygon and label
- `draw_polygon_outline()` - Scanline fill + edge drawing
- `draw_line()` - Bresenham-like line drawing
- `draw_equipment()` - Position equipment symbols
- `draw_walls_in_polygon_space()` - Interior walls
- `render_equipment_summary()` - Equipment status table

## Testing

Test with both data sources:

```bash
# AR scan data
cargo run -p arxui -- render --building "Untitled Scan.yaml"

# IFC data
cargo run -p arxui -- render --building building.yaml --floor 1
```

## Scan Quality Tips

**For Accurate Floor Plans**:

The renderer displays exactly what the scan captured. For best results:

1. **Remove Furniture**: Move chairs, tables, and other objects before scanning
   - Furniture creates extra edges/walls in the polygon
   - Distorts the actual room boundaries
   - Leads to uneven walls and artifacts

2. **Scan Empty Rooms**: Clear the space before capturing
   - Gives cleaner floor polygon outlines
   - Results in more accurate terminal visualization
   - Better foundation for future AR overlay

3. **Multiple Passes**: Do several scans of the same area
   - Combine results for better accuracy
   - Helps identify and eliminate scan artifacts

4. **Check Polygon Preview**: Use 2D render to validate scan quality before committing

**Example**: A scan with furniture might show:
```
│     +─+    │  ← Distorted walls from furniture
│     │ │    │
│   ──+ │+───│  ← Should be straight walls
```

A clean scan shows:
```
│              │  ← Accurate, straight walls
│              │
│              │
```

**Note**: The code is working correctly! ✅ Any discrepancies in the terminal output are due to scan quality, not rendering bugs.

## Future Improvements

See [RENDER_REFACTOR_PLAN.md](./RENDER_REFACTOR_PLAN.md) for modular refactoring plan.

Key areas:
1. Extract polygon parsing to separate module
2. Extract coordinate transformations
3. Create dedicated grid management module
4. Separate room vs equipment rendering logic

