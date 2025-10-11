# Unified Space Architecture - Future Design

**Status:** Design Document for Future Implementation
**Target:** Post-initial deployment
**Priority:** Medium (after Phase 7 complete)

---

## Vision

ArxOS should be a **universal spatial operating system** that works for any physical structure, not just buildings. This document outlines the path to a fully domain-agnostic architecture.

## Current State vs. Vision

### Current Architecture (Building-Focused)

```go
// Separate entity types
type Building struct { ... }
type Floor struct { ... }
type Room struct { ... }
type Equipment struct { ... }
```

**Works for:** Buildings
**Doesn't work for:** Ships (decks), warehouses (aisles), data centers (racks)

### Future Architecture (Domain-Agnostic)

```go
// Unified Space entity - recursive hierarchy
type Space struct {
    ID         types.ID
    ParentID   *types.ID      // Points to parent space (recursive)
    Type       string         // "building", "ship", "floor", "deck", "room", "fridge"
    Name       string
    Path       string         // /structure/level/sublevel

    // Optional geometry (from IFC, LiDAR, or manual)
    Geometry   *Geometry      // Precise 3D boundary
    Dimensions *Dimensions    // Simple width/length/height

    // Metadata
    Properties map[string]interface{}

    // Fidelity tracking
    GeometrySource string  // "ifc", "lidar", "text", "none"
    Confidence     int     // 0-3 quality level

    // Audit
    CreatedAt time.Time
    UpdatedAt time.Time
}

// Convenience types (building domain)
type Building struct {
    Space  // Embeds generic Space
    // Building-specific helper methods
}

type Floor struct {
    Space
    Level int  // Building-specific field
}
```

---

## Benefits of Unified Space

### 1. True Domain Agnosticism

**Supports any spatial structure:**
```bash
# Buildings
arx space create --type building --name "Office Tower"
arx space create --type floor --parent "Office Tower"
arx space create --type room --parent "Floor 1"

# Ships
arx space create --type ship --name "USS Enterprise"
arx space create --type deck --parent "USS Enterprise" --level 3
arx space create --type compartment --parent "Deck 3"

# Warehouses
arx space create --type warehouse --name "Distribution Center A"
arx space create --type aisle --parent "Warehouse A"
arx space create --type shelf --parent "Aisle B"

# Nested containers
arx space create --type fridge --parent "Room 101"
arx space create --type shelf --parent "Fridge"
```

### 2. Recursive Hierarchy

**Any depth:**
```
Space → Space → Space → Space → ... → Item

Examples:
Building → Floor → Room → Cabinet → Drawer → Item
Ship → Deck → Compartment → Locker → Item
Warehouse → Zone → Aisle → Rack → Shelf → Bin → Item
```

### 3. Unified Operations

**Same commands work everywhere:**
```bash
# Query works the same for any space type
arx query /office-tower/floor-3/room-301/*
arx query /uss-enterprise/deck-3/torpedo-bay/*
arx query /warehouse-a/aisle-b/rack-5/*

# Version control works the same
arx commit -m "Updated Floor 3 layout"
arx commit -m "Modified Deck 3 torpedo bay"
arx commit -m "Reorganized Warehouse A"
```

### 4. IFC Import Still Works

**IFC is domain-agnostic:**
```bash
# Import building IFC
arx import office-tower.ifc
# Creates Spaces with type="building", "floor", "room"

# Import ship IFC
arx import cargo-ship.ifc
# Creates Spaces with type="ship", "deck", "compartment"

# Import factory IFC
arx import factory.ifc
# Creates Spaces with type="facility", "line", "zone"
```

IFC doesn't care about domain - it's just 3D geometry with metadata.

---

## Implementation Strategy

### Phase 1: Current (Shipped)
- Keep Building/Floor/Room as primary entities
- Component system provides flexibility
- Document that it's "building-first, but works for any space"

### Phase 2: Add Space Entity (Parallel)
- Create `internal/domain/space/space.go`
- Implement SpaceRepository
- Add `arx space` commands
- Keep Building/Floor/Room working (backward compatible)

### Phase 3: Migrate Internals
- Building/Floor/Room become wrappers around Space
- Existing APIs still work
- Internally use Space

### Phase 4: Deprecate (Future)
- Building/Floor/Room marked as legacy
- Recommend Space for new projects
- Eventually remove (breaking change)

---

## Technical Design

### Space Entity

```go
package space

import (
    "time"
    "github.com/arx-os/arxos/internal/domain/types"
)

// Space represents any physical space in a hierarchy
// Domain-agnostic: buildings, ships, warehouses, vehicles, containers
type Space struct {
    ID       types.ID  `json:"id"`
    ParentID *types.ID `json:"parent_id,omitempty"` // Null = root space

    // Identity
    Type string `json:"type"` // "building", "ship", "floor", "deck", "room", "fridge"
    Name string `json:"name"`
    Path string `json:"path"` // Auto-generated: /parent/parent/name

    // Optional geometry (high fidelity)
    Geometry *Geometry `json:"geometry,omitempty"` // Polygon, solid, or nil

    // Optional dimensions (low fidelity fallback)
    Dimensions *Dimensions `json:"dimensions,omitempty"` // Width, length, height

    // Metadata
    Properties map[string]interface{} `json:"properties"`

    // Fidelity tracking
    GeometrySource string `json:"geometry_source"` // "ifc", "lidar", "text", "none"
    Confidence     int    `json:"confidence"`      // 0-3 quality level

    // Optional IFC mapping (if imported from IFC)
    IFCClass    *string `json:"ifc_class,omitempty"`    // "IfcBuilding", "IfcSpace"
    IFCGlobalID *string `json:"ifc_global_id,omitempty"` // IFC GUID

    // Audit
    CreatedAt time.Time  `json:"created_at"`
    UpdatedAt time.Time  `json:"updated_at"`
    CreatedBy *types.ID  `json:"created_by,omitempty"`
}

// Dimensions represents simple dimensional data
type Dimensions struct {
    Width  float64 `json:"width"`  // meters
    Length float64 `json:"length"` // meters
    Height float64 `json:"height"` // meters
    Area   float64 `json:"area"`   // computed: width * length
    Volume float64 `json:"volume"` // computed: area * height
}

// Geometry represents precise 3D geometry
type Geometry struct {
    Type       string      `json:"type"`        // "polygon", "solid", "multipolygon"
    Coordinates []Point3D  `json:"coordinates"` // Boundary points
    IFCData    *string     `json:"ifc_data,omitempty"` // Raw IFC geometry
}

// Point3D represents a 3D coordinate
type Point3D struct {
    X float64 `json:"x"`
    Y float64 `json:"y"`
    Z float64 `json:"z"`
}
```

### CLI Commands

```bash
# Generic space commands
arx space create --type <type> --name <name> [--parent <id>]
arx space get <id-or-path>
arx space list [--parent <id>] [--type <type>]
arx space update <id> [options]
arx space delete <id>

# Building convenience commands (aliases)
arx building create   →  arx space create --type building
arx floor create      →  arx space create --type floor
arx room create       →  arx space create --type room

# New domain commands
arx ship create       →  arx space create --type ship
arx deck create       →  arx space create --type deck
arx warehouse create  →  arx space create --type warehouse
```

### Database Schema

```sql
-- New spaces table (replaces buildings, floors, rooms)
CREATE TABLE spaces (
    id UUID PRIMARY KEY,
    parent_id UUID REFERENCES spaces(id) ON DELETE CASCADE,

    type VARCHAR(50) NOT NULL,  -- Free-form: "building", "ship", "floor", etc.
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL UNIQUE,  -- /parent/parent/name

    -- Geometry (optional)
    geometry GEOMETRY(POLYGONZ, 4326),  -- Precise 3D boundary

    -- Dimensions (optional, fallback)
    width REAL,
    length REAL,
    height REAL,
    area REAL,
    volume REAL,

    -- Metadata
    properties JSONB,

    -- Fidelity
    geometry_source VARCHAR(20) DEFAULT 'none',  -- "ifc", "lidar", "text", "none"
    confidence SMALLINT DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 3),

    -- IFC mapping (optional)
    ifc_class VARCHAR(100),
    ifc_global_id VARCHAR(50),

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Spatial index
CREATE INDEX idx_spaces_geometry ON spaces USING GIST(geometry);
CREATE INDEX idx_spaces_parent ON spaces(parent_id);
CREATE INDEX idx_spaces_type ON spaces(type);
CREATE INDEX idx_spaces_path ON spaces(path);
```

---

## Migration Path

### Backward Compatibility

**Keep existing tables:**
- `buildings`, `floors`, `rooms` remain
- Add views that map to `spaces` table
- Gradual migration without breaking changes

**Example:**
```sql
-- View: buildings table → spaces WHERE type='building'
CREATE VIEW buildings AS
SELECT
    id,
    name,
    (properties->>'address')::TEXT as address,
    geometry as location,
    created_at,
    updated_at
FROM spaces
WHERE type = 'building';

-- View: floors table → spaces WHERE type='floor'
CREATE VIEW floors AS
SELECT
    id,
    parent_id as building_id,
    name,
    (properties->>'level')::INTEGER as level,
    created_at,
    updated_at
FROM spaces
WHERE type = 'floor';
```

**Benefits:**
- Existing code continues to work
- New code uses `spaces` table
- Migrate gradually over time

---

## Examples: Real-World Use Cases

### Use Case 1: Office Building
```bash
arx space create --type building --name "Tech Campus HQ"
arx space create --type floor --parent "Tech Campus HQ" --level 1
arx space create --type room --parent "Floor 1" --name "Room 101" --width 5 --length 8

arx item create --type laptop --space "Room 101" --name "Laptop-A1"
arx item create --type dock --space "Room 101" --name "Dock-A1"
```

### Use Case 2: Cargo Ship
```bash
arx space create --type ship --name "MV Cargo Voyager"
arx space create --type deck --parent "MV Cargo Voyager" --level 2
arx space create --type hold --parent "Deck 2" --name "Cargo Hold A"

arx item create --type container --space "Cargo Hold A" --name "CSQU3054383"
arx item create --type cargo --space "CSQU3054383" --name "Electronics Shipment"
```

### Use Case 3: Warehouse
```bash
arx space create --type warehouse --name "Distribution Center North"
arx space create --type zone --parent "DC North" --name "Zone A"
arx space create --type aisle --parent "Zone A" --name "Aisle 1"
arx space create --type rack --parent "Aisle 1" --name "Rack 5"
arx space create --type shelf --parent "Rack 5" --level 3

arx item create --type pallet --space "Shelf 3" --name "Pallet-12345"
arx item create --type forklift --space "Aisle 1" --name "Forklift-7"
```

### Use Case 4: Kitchen Inventory (Your Example)
```bash
arx space create --type building --name "Office"
arx space create --type floor --parent "Office"
arx space create --type room --parent "Floor 1" --name "Kitchen"
arx space create --type fridge --parent "Kitchen" --name "Main Fridge"
arx space create --type shelf --parent "Main Fridge" --level 2

arx item create --type sandwich --space "Shelf 2" --name "PBJ-001" \
  --property "bread:wheat" \
  --property "pb:creamy" \
  --property "jelly:grape"

arx query /office/floor-1/kitchen/main-fridge/*
# Returns: PBJ-001, Leftover-Pizza, Milk-Carton
```

---

## Integration with IFC

### IFC Import (Type Mapping)

```bash
arx import building.ifc

# Maps IFC classes to Space types:
IfcBuilding       → Space{type: "building", ifc_class: "IfcBuilding"}
IfcBuildingStorey → Space{type: "floor", ifc_class: "IfcBuildingStorey"}
IfcSpace          → Space{type: "room", ifc_class: "IfcSpace"}
IfcWall           → Space{type: "wall", ifc_class: "IfcWall"} (structural)
IfcDoor           → Item{type: "door", ifc_class: "IfcDoor"}
```

### IFC Export (Reverse Mapping)

```bash
arx export output.ifc

# Only exports Spaces/Items with IFC mappings:
✅ Space{type: "building", ifc_class: "IfcBuilding"} → IfcBuilding
✅ Space{type: "room", ifc_class: "IfcSpace"} → IfcSpace
❌ Space{type: "fridge"} → SKIPPED (no IFC equivalent)
❌ Item{type: "sandwich"} → SKIPPED (no IFC equivalent)

Warning: 3 items skipped (no IFC mapping)
```

**Key:** IFC is optional and only works for standard building elements.

---

## TUI Rendering with Unified Space

### Adaptive Rendering

```go
func (tui *TUI) RenderSpace(spaceID types.ID) {
    space := arx.GetSpace(spaceID)

    // Render based on available data
    if space.Geometry != nil {
        // High fidelity: Precise IFC/LiDAR geometry
        tui.renderPreciseGeometry(space.Geometry)

    } else if space.Dimensions != nil {
        // Medium fidelity: Simple rectangle
        tui.renderRectangle(space.Dimensions)

    } else {
        // Low fidelity: List/tree view
        tui.renderTreeView(space)
    }

    // Get child spaces and items
    children := arx.GetChildSpaces(spaceID)
    items := arx.GetItemsInSpace(spaceID)

    // Render children recursively
    for _, child := range children {
        tui.renderChild(child)
    }

    // Render items as symbols
    for _, item := range items {
        if item.Location != nil {
            tui.renderItemSymbol(item)
        }
    }
}
```

### Example TUI Output

```
┌─ Structure: USS Enterprise - Level: Deck 3 ────────┐
│                                                     │
│  ┌──────────────┐    ┌──────────────┐             │
│  │ Torpedo Bay  │    │ Engineering  │             │
│  │   T  T  T    │    │   R  R       │             │
│  │   T  T       │    │              │             │
│  └──────────────┘    └──────────────┘             │
│                                                     │
│  ┌─────────────────────┐                          │
│  │ Crew Quarters       │                          │
│  │  B  B  B  B         │                          │
│  └─────────────────────┘                          │
│                                                     │
└─────────────────────────────────────────────────────┘

Item Legend:
  T = Torpedo    R = Reactor    B = Bunk
  (Custom types use first letter)

Structure: USS Enterprise - Level: Deck 3
Items: 9 torpedoes, 2 reactors, 4 bunks
```

---

## Implementation Checklist

### Phase 1: Design & Planning (1 week)
- [x] Create this architecture document
- [ ] Review with stakeholders
- [ ] Finalize Space entity design
- [ ] Plan database migration strategy

### Phase 2: Core Implementation (2-3 weeks)
- [ ] Create `internal/domain/space/space.go`
- [ ] Create SpaceRepository interface
- [ ] Implement PostGIS SpaceRepository
- [ ] Create SpaceUseCase
- [ ] Unit tests

### Phase 3: CLI Integration (1 week)
- [ ] Create `arx space` commands
- [ ] Test with multiple domains (building, ship, warehouse)
- [ ] Integration tests

### Phase 4: Backward Compatibility (1 week)
- [ ] Create database views (buildings → spaces WHERE type='building')
- [ ] Test existing Building/Floor/Room code still works
- [ ] Migration script for existing data

### Phase 5: Documentation (1 week)
- [ ] Update all docs to reference Space
- [ ] Create migration guide for users
- [ ] Update examples with multiple domains

**Total Effort:** 6-7 weeks

---

## Decision: When to Implement

**NOT NOW.** Ship with current architecture first.

**Implement after:**
1. Phase 7 complete (integration done)
2. First 5-10 users validated the building use case
3. Someone asks for non-building use case (ship, warehouse, etc.)

**This is a future enhancement, not a blocker.**

---

## Current Workaround

Until unified Space is implemented:

**Use Component system for non-building domains:**
```bash
# Ship example using current Component system
arx component create --name "Torpedo-Bay-3" \
  --type "space" \
  --path "/uss-enterprise/deck-3/torpedo-bay" \
  --property "space_type:compartment"

arx component create --name "Torpedo-1" \
  --type "torpedo" \
  --path "/uss-enterprise/deck-3/torpedo-bay/torpedo-1"
```

**This works today** - Components are already fully domain-agnostic.

---

## References

- Current Component Implementation: `internal/domain/component/component.go`
- Current Building Entities: `internal/domain/entities.go`
- Version Control Objects: `internal/domain/building/object.go`
- TUI Renderer: `internal/tui/services/floor_plan_renderer.go`

---

**Status:** Documented for future implementation
**Priority:** Medium (after initial deployment)
**Blocker:** No (Component system provides workaround)

