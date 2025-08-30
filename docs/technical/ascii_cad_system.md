# ASCII CAD System Technical Documentation

## Overview

The Arxos ASCII CAD system provides professional-grade Computer-Aided Design capabilities entirely within the terminal, using pure ASCII characters for rendering. This aligns with the Arxos philosophy of constraint-driven innovation - working within terminal limitations to create accessible, powerful building intelligence tools.

## Architecture

### Core Components

```
src/cad/
├── data_model.rs      # Geometric entities and layers
├── algorithms.rs      # Rasterization algorithms
├── renderer.rs        # ASCII rendering pipeline
├── commands.rs        # Command parsing and execution
├── viewport.rs        # Pan, zoom, and coordinate systems
└── mod.rs            # Module exports
```

### Design Principles

1. **Pure ASCII Output**: All rendering uses standard ASCII/Unicode box-drawing characters
2. **No External Dependencies**: Core algorithms implemented from scratch in Rust
3. **Mesh Integration**: Can reference and display ArxObjects from the packet radio mesh
4. **Progressive Detail**: Integrates with slow-bleed protocol for detail accumulation
5. **Professional Features**: Layers, snapping, dimensions - real CAD functionality

## Data Model

### Geometric Entities

```rust
enum Entity {
    Line(Line),           // Lines with styles (solid, dashed, etc.)
    Circle(Circle),       // Full circles
    Arc(Arc),            // Arc segments
    Rectangle(Rectangle), // Rectangles
    Polyline(Polyline),  // Connected line segments
    Text(Text),          // Annotations
    ArxObject(ArxObjectRef), // Mesh network objects
    Dimension(Dimension), // Measurements
    Hatch(Hatch),        // Filled areas
}
```

### Layer System

Layers are organized by building system for clarity:

```rust
enum LayerColor {
    Default,
    Electrical,  // Orange - electrical systems
    HVAC,        // Blue - heating/cooling
    Plumbing,    // Green - water systems
    Structural,  // Gray - walls, beams
    Furniture,   // Brown - equipment
    Annotation,  // Yellow - dimensions, labels
}
```

### ArxObject Integration

The CAD system can display objects from the mesh network:

```rust
struct ArxObjectRef {
    object_id: u16,        // ID from mesh network
    position: Point2D,     // CAD coordinates
    symbol_type: ArxSymbol,// How to display
}
```

## Rendering Pipeline

### 1. Rasterization Algorithms

#### Bresenham's Line Algorithm
Efficiently converts vector lines to grid points:

```rust
fn bresenham_line(start: Point2D, end: Point2D) -> Vec<GridPoint>
```

Used for:
- Drawing lines
- Rectangle edges
- Polyline segments

#### Midpoint Circle Algorithm
Draws circles using only integer arithmetic:

```rust
fn midpoint_circle(center: Point2D, radius: f64) -> Vec<GridPoint>
```

Generates 8-way symmetric points for efficiency.

#### Wu's Antialiasing Algorithm
Provides smooth lines with intensity gradients:

```rust
fn wu_line(start: Point2D, end: Point2D) -> Vec<AntialiasedPoint>
```

Each point includes intensity (0.0-1.0) for gradient characters.

### 2. Character Selection

The renderer supports multiple character sets:

#### Simple ASCII
```
Horizontal: -
Vertical: |
Corners: +
Cross: +
Diagonal: / \
```

#### Extended Unicode
```
Horizontal: ─
Vertical: │
Corners: ┌ ┐ └ ┘
Junctions: ├ ┤ ┬ ┴ ┼
```

#### Technical CAD
```
Horizontal: ═
Vertical: ║
Corners: ╔ ╗ ╚ ╝
Junctions: ╠ ╣ ╦ ╩ ╬
```

### 3. Z-Buffering

Multiple layers are handled with depth buffering:

```rust
struct Cell {
    char: char,
    depth: u8,     // Layer index (lower = higher priority)
    layer: usize,  // Source layer
}
```

### 4. Junction Detection

The renderer automatically detects line intersections and replaces characters with appropriate junctions:

```
Two lines crossing: ┼
T-junction: ├ ┤ ┬ ┴
Corner: ┌ ┐ └ ┘
```

## Command System

### Command Modes

```rust
enum CommandMode {
    Command,    // Typing commands
    Draw,       // Drawing mode
    Edit,       // Editing mode
    View,       // View manipulation
    Select,     // Selecting entities
}
```

### Multi-Step Commands

Drawing commands use multi-step input for precision:

```
> line
Line: First point (x,y): 10,10
Line: Second point (x,y): 50,30
[Line created]
```

### Command Shortcuts

Professional CAD-style shortcuts:
- `l` - Line
- `c` - Circle
- `r` - Rectangle
- `m` - Move
- `z` - Zoom
- `u` - Undo

## Viewport Management

### Coordinate Systems

```rust
World Coordinates → Screen Coordinates
     (CAD units)        (characters)
```

### Aspect Ratio Correction

Terminal characters are ~2x taller than wide:

```rust
pub struct Viewport {
    aspect_ratio: f64,  // Typically 2.0
}
```

### Snap Modes

```rust
enum SnapMode {
    Grid(f64),      // Snap to grid spacing
    Endpoint,       // Snap to line ends
    Midpoint,       // Snap to midpoints
    Center,         // Snap to circle centers
    Intersection,   // Snap to intersections
}
```

## Integration with Slow-Bleed Protocol

### Progressive Detail Rendering

As detail accumulates from the mesh network:

1. **Basic** (< 20% complete): Simple point markers
2. **Intermediate** (20-50%): Basic ASCII symbols
3. **Detailed** (50-80%): System connections shown
4. **CAD-Level** (> 80%): Full technical drawings

### Example: Electrical Outlet Evolution

```
Time: 0 hours (13-byte packet received)
[o] 1234 @ (1,2,1)

Time: 6 hours (material properties received)
 ___
|o o|
|___|
 1234

Time: 24 hours (electrical connections received)
 ___
|o o| 120V
|___| Circuit 12
 1234

Time: 1 week (full CAD detail)
╔════════╗
║  ┌──┐  ┌──┐  ║
║  │  │  │  │  ║ 120V
║  └──┘  └──┘  ║ 15A
╚════════╝
ID: 1234 | Circuit 12
⚡ Load: Normal
🔧 Next maintenance: 180 days
```

## Performance Optimizations

### Efficient Algorithms
- Bresenham: O(n) line drawing with integer-only math
- Midpoint circle: 8-way symmetry reduces calculations by 8x
- Spatial indexing for entity queries

### Memory Management
- No heap allocations in core algorithms
- Fixed-size buffers for embedded compatibility
- Lazy evaluation of complex renders

## Usage Example

```rust
use arxos_cad::{Drawing, Entity, Line, Point2D, AsciiRenderer};

fn main() {
    // Create drawing
    let mut drawing = Drawing::new();
    
    // Add a line
    let line = Line {
        start: Point2D::new(0.0, 0.0),
        end: Point2D::new(100.0, 50.0),
        style: LineStyle::Solid,
    };
    drawing.add_entity(Entity::Line(line));
    
    // Render to ASCII
    let mut renderer = AsciiRenderer::new(80, 24);
    renderer.render(&drawing);
    
    // Display
    println!("{}", renderer.to_string());
}
```

## Output Example

```
╔═══════════════════════════════════════╗
║     ELECTRICAL PANEL - FLOOR 2        ║
╠═══════════════════════════════════════╣
║  ╔═══════════════╗                    ║
║  ║ ┌─┬─┬─┬─┬─┬─┐ ║     Legend:        ║
║  ║ │1│2│3│4│5│6│ ║     ═ Circuit      ║
║  ║ ├─┼─┼─┼─┼─┼─┤ ║     ⊡ Outlet       ║
║  ║ │7│8│9│A│B│C│ ║     ⊟ Switch       ║
║  ║ ├─┼─┼─┼─┼─┼─┤ ║     ⊞ Thermostat   ║
║  ║ │D│E│F│M│▓│▓│ ║                    ║
║  ║ └─┴─┴─┴─┴─┴─┘ ║                    ║
║  ╚═══════════════╝                    ║
║                                        ║
║  ═══⊡═══⊡═══⊡═══⊡  Circuit 1 (15A)   ║
║                                        ║
║  ═══⊟═══⊟═══⊟      Circuit 2 (15A)   ║
║                                        ║
║  ═══⊞              Circuit 3 (20A)    ║
╚═══════════════════════════════════════╝
```

## Future Enhancements

1. **3D Wireframe**: Isometric projection for 3D views
2. **DXF Import/Export**: Industry-standard file format
3. **Parametric Constraints**: Dimensional relationships
4. **Block Libraries**: Reusable component symbols
5. **Mesh Queries**: Real-time data overlay from packet radio

## Conclusion

The ASCII CAD system demonstrates that professional-grade technical drawing is possible within terminal constraints. By combining classic computer graphics algorithms with modern Rust performance, we've created a CAD system that:

- Runs on any terminal
- Requires no GPU or graphics libraries
- Integrates seamlessly with the mesh network
- Progressively enhances with slow-bleed data
- Maintains professional CAD workflows

This is core to the Arxos vision: making building intelligence accessible through elegant constraint-based design.