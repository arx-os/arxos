# 2D Renderer Refactoring Plan

## Current State

The 2D renderer (`src/render/mod.rs`) is a single 574-line file that handles everything:
- Floor plan bounds calculation
- Polygon parsing and coordinate transformation
- ASCII grid creation and management
- Room polygon drawing (scanline fill, outlines)
- Equipment rendering
- Wall rendering
- Text/label rendering
- Equipment status summaries

## Goal

Split into focused modules following the 3D renderer pattern for better maintainability.

## Proposed Module Structure

```
src/render/
├── mod.rs              # Main BuildingRenderer + orchestration (50-100 lines)
├── bounds.rs           # Floor bounds calculation (50 lines)
├── polygon.rs          # Polygon parsing, transformation, drawing (150 lines)
├── grid.rs             # ASCII grid operations and drawing primitives (100 lines)
├── room.rs             # Room rendering (polygon + labels) (100 lines)
├── equipment.rs        # Equipment rendering + symbols (75 lines)
└── walls.rs            # Interior walls rendering (75 lines)
```

## Migration Strategy

**Phase 1: Create new modules** (non-breaking)
- Add new `.rs` files in `src/render/`
- Export via `mod.rs` but don't use yet
- Keep existing code working

**Phase 2: Move code incrementally**
- Move polygon parsing logic to `polygon.rs`
- Move grid operations to `grid.rs`
- Move rendering logic to specialized modules
- Each move followed by test verification

**Phase 3: Update main renderer**
- Update `BuildingRenderer` to use new modules
- Remove old inline implementations
- Final testing

## Key Functions to Extract

### bounds.rs
- `calculate_floor_bounds()` - Determine X-Y bounds for floor plan
- Handle coordinate space detection (world vs local)
- Add padding logic

### polygon.rs
- `parse_polygon_string()` - Parse "x,y,z;x,y,z" format
- `transform_polygon_coords()` - Apply coordinate space transformation
- `draw_polygon_outline()` - Scanline fill + edge drawing
- `draw_line()` - Bresenham-like line drawing

### grid.rs
- `create_grid()` - Initialize empty ASCII grid
- `world_to_grid()` - Coordinate transformation with Y-flip
- `draw_grid_to_terminal()` - Print formatted output
- Helper functions for character choice based on line direction

### room.rs
- `render_room()` - Main room rendering orchestration
- `draw_room_polygon()` - Call polygon module
- `draw_room_label()` - Name placement and truncation

### equipment.rs
- `draw_equipment()` - Equipment positioning
- `get_equipment_symbol()` - Type-to-character mapping
- Coordinate transformation for equipment

### walls.rs
- `draw_walls()` - Interior wall rendering
- `parse_walls_data()` - Wall segment parsing
- Coordinate validation and clipping

## Benefits

1. **Single Responsibility**: Each module has one clear job
2. **Testability**: Smaller modules easier to unit test
3. **Maintainability**: Easier to find and fix bugs
4. **Consistency**: Matches 3D renderer architecture pattern
5. **Clarity**: New developers can understand structure faster

## Testing Strategy

Keep existing renderer working throughout refactor:
1. Before each module move: `cargo test render`
2. After each module move: `cargo test render`
3. Smoke test with: `cargo run -p arxui -- render --building building.yaml`
4. Test both AR scan and IFC data formats

## Timeline Estimate

- **Phase 1**: 30 min (create modules, basic exports)
- **Phase 2**: 1-2 hours (incremental code moves)
- **Phase 3**: 30 min (update main renderer, cleanup)

**Total**: ~2-3 hours for full refactor with testing

## Questions Answered

1. ✅ Are there any external callers of internal render functions?
   - **Answer**: Only `BuildingRenderer::new()`, `.floors()`, and `.render_floor()` are public
   - Internal functions are all private, making refactoring safe
   
2. Should we create a `Coordinates` type for X-Y pairs instead of tuples?
   - **Recommendation**: Keep tuples for now, refactor later if complexity increases
   
3. Do we need a `Grid` struct or are we okay with `Vec<Vec<char>>`?
   - **Recommendation**: Keep `Vec<Vec<char>>` for now to avoid over-engineering
   
4. Should coordinate transformations be extracted to a common module?
   - **Recommendation**: Keep in `polygon.rs` since they're polygon-specific
     - IFC: local coordinates → world coordinates
     - AR: already world coordinates

## Current Public API (Preserve These)

```rust
pub struct BuildingRenderer {
    building_data: BuildingData,
}

impl BuildingRenderer {
    pub fn new(building_data: BuildingData) -> Self;
    pub fn floors(&self) -> &Vec<FloorData>;
    pub fn render_floor(&self, floor: i32) -> Result<(), Box<dyn std::error::Error>>;
}
```

All other methods are private and can be freely refactored.

