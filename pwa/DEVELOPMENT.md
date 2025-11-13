# ArxOS PWA Development Guide

## Architecture Overview

The ArxOS PWA is built with a modular, feature-based architecture that separates concerns and enables clean code organization.

### Core Principles

1. **WASM-First**: All core logic lives in Rust, compiled to WebAssembly
2. **Type Safety**: Runtime validation of WASM responses using TypeScript type guards
3. **Modular Structure**: Feature modules are self-contained with components, state, types, and tests
4. **Command-Centric**: All user actions flow through the command palette/console
5. **Progressive Enhancement**: Works offline, enhanced when agent is available

## Module Structure

### Floor Module (`src/modules/floor/`)

The floor module provides interactive 2D floor plan visualization (M03).

```
src/modules/floor/
├── components/          # React components
│   ├── FloorViewer.tsx   # Main coordinator component
│   ├── FloorCanvas.tsx   # Canvas wrapper with event handling
│   ├── FloorControls.tsx # Zoom/pan controls
│   ├── FloorSelector.tsx # Building/floor selector
│   └── SelectionPanel.tsx # Details panel for selections
├── renderer/            # Canvas rendering engine
│   ├── Camera.ts         # Pan/zoom/viewport management
│   ├── SceneGraph.ts     # Layer management and hit testing
│   ├── Renderer.ts       # Main rendering coordinator
│   └── layers/           # Layer implementations
│       ├── GridLayer.ts      # Background grid with adaptive spacing
│       ├── RoomLayer.ts      # Room polygons and labels
│       └── EquipmentLayer.ts # Equipment symbols and labels
├── types/               # Shared types and utilities
│   └── index.ts          # Types, colors, coordinate transformations
└── index.ts             # Public exports

```

### Rendering Pipeline

```
User Interaction → FloorCanvas (events) → Renderer
                                              ↓
                                          Camera (viewport)
                                              ↓
                                        SceneGraph (layers)
                                              ↓
                            GridLayer → RoomLayer → EquipmentLayer
                                              ↓
                                         Canvas2D Context
```

### Data Flow

```
WASM (Rust)
    ↓ serde_json
JSON Response
    ↓ Type Guards
TypeScript Types
    ↓ React Props
Components
    ↓ Renderer
Canvas
```

## WASM Integration

### Geometry Module (`crates/arxos-wasm/src/geometry.rs`)

Provides building/floor data structures and mock data generators.

**DTOs:**
- `Coordinate` - 2D/3D point
- `BoundingBox` - Min/max coordinate pair
- `BuildingSummary` - Lightweight building metadata
- `Building` - Full building with floors
- `Floor` - Floor with rooms and equipment
- `Room` - Room with polygon and equipment
- `Equipment` - Equipment with position and properties

**Exports:**
- `get_buildings()` → `BuildingSummary[]`
- `get_building(path)` → `Building`
- `get_floor(buildingPath, floorId)` → `Floor`
- `get_floor_bounds(buildingPath, floorId)` → `BoundingBox`

### TypeScript Adapters (`src/lib/wasm/geometry.ts`)

Provides type-safe wrappers around WASM exports with runtime validation.

```typescript
// Runtime type validation
function isFloor(value: unknown): value is Floor {
  const floor = value as Floor;
  return (
    typeof floor?.id === "string" &&
    typeof floor?.name === "string" &&
    // ... more checks
  );
}

// Type-safe adapter
export async function getFloor(buildingPath: string, floorId: string): Promise<Floor> {
  const module = await initWasm();
  const result = await module.get_floor(buildingPath, floorId);

  if (!isFloor(result)) {
    throw new Error("WASM returned invalid floor format");
  }

  return result;
}
```

## Rendering Engine

### Camera System

The `Camera` class manages viewport state and transformations:

- **Pan**: Translate the view (middle-click or right-click drag)
- **Zoom**: Scale the view (scroll wheel)
- **Fit-to-View**: Auto-calculate zoom to fit floor bounds
- **Coordinate Conversion**: World ↔ Screen space transformations

**Key Methods:**
- `zoom(delta, centerX?, centerY?)` - Zoom toward a point
- `pan(deltaX, deltaY)` - Translate view
- `fitToView(width, height)` - Auto-fit to canvas
- `startDrag(x, y)` / `drag(x, y)` / `endDrag()` - Drag handling

### Scene Graph

The `SceneGraph` manages rendering layers and hit testing:

- **Layer Management**: Add, remove, toggle visibility
- **Render Order**: Grid → Rooms → Equipment
- **Hit Testing**: Point-in-polygon for rooms, distance-based for equipment

**Key Methods:**
- `addLayer(name, layer)` - Register a layer
- `render(context)` - Render all visible layers
- `findRoomAtPoint(rooms, x, y)` - Hit test rooms
- `findEquipmentAtPoint(equipment, x, y)` - Hit test equipment

### Layers

Each layer implements the `Layer` interface:

```typescript
interface Layer {
  type: LayerType;
  visible: boolean;
  render(context: RenderContext): void;
}
```

**GridLayer:**
- Adaptive grid spacing based on zoom
- Major/minor grid lines
- Axis labels and origin marker

**RoomLayer:**
- Polygon or bounding box rendering
- Color-coded by room type (mechanical, electrical, plumbing, office)
- Room name and type labels
- Selection and hover highlights

**EquipmentLayer:**
- Diamond symbols for equipment
- Color-coded by equipment type (HVAC, electrical, plumbing)
- Labels shown on hover/selection
- Distance-based hit testing

## State Management

### Local Component State

The `FloorViewer` component uses React's `useState` for:
- Current floor
- Selection state
- Layer visibility

This is sufficient for M03 since floor viewer is isolated. A Zustand store may be added in M04 when integrating with other features.

### Command Execution State

Global command execution state is managed by `useCommandExecutionStore` (Zustand):
- Execution logs
- Current command
- Execution state (idle/running/complete/error)

## Testing Strategy

### Unit Tests

- **Renderer Components**: Camera, SceneGraph, Layer rendering logic
- **WASM Adapters**: Type guard validation
- **React Components**: Component rendering and interactions

### Integration Tests

- **WASM → TypeScript**: End-to-end data flow
- **Component Composition**: FloorViewer integration

### E2E Tests (Playwright)

- **Floor Viewer Workflow**: Open viewer → Select building → Select floor → Navigate → Select elements
- **Keyboard Shortcuts**: Cmd/Ctrl+F to toggle
- **Mouse Interactions**: Pan, zoom, select

## M03 Exit Criteria

- [x] Canvas2D floor plan rendering
- [x] Pan and zoom controls
- [x] Layer system (grid, rooms, equipment)
- [x] Selection and hover states
- [x] Building/floor selector
- [x] WASM geometry exports
- [x] TypeScript adapters with validation
- [x] Mock data in Rust
- [x] Integration into App.tsx
- [x] All existing tests pass
- [x] Production build succeeds

## Future Enhancements (M04+)

- Real data loading via desktop agent
- Floor editing capabilities
- Measurement tools
- Export to formats (PNG, SVG, PDF)
- 3D view integration
- AR preview overlay
- Real-time collaboration
- Annotation system
