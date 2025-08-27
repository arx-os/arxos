# ArxObject Naming Convention Specification

## Core Principles
1. **Filesystem-Compatible**: Names must work on all operating systems
2. **Hierarchical**: Reflect the physical building structure
3. **Navigable**: Support cd/ls/pwd navigation metaphors
4. **Queryable**: Enable efficient pattern matching and searches
5. **Human-Readable**: Intuitive for building operators

## Naming Format

### Primary Format: Slash-Delimited Paths
```
/building_id/floor_n/space_type/space_id/component_type/component_id
```

### Examples:
```
/hq/f1/room/101/wall/north
/hq/f2/room/201/door/main
/hq/f1/equipment/hvac/unit/1
/hq/systems/electrical/panel/main
/hq/f3/sensor/temp/zone/1
```

## Hierarchy Levels

### Level 1: Building
- Format: `/building_id`
- Example: `/hq`, `/factory1`, `/warehouse_west`
- Rules: Lowercase, alphanumeric + underscore, no spaces

### Level 2: Floor or System
- Floors: `/building/f{n}` where n is floor number
- Systems: `/building/systems`
- External: `/building/exterior`
- Roof: `/building/roof`
- Basement: `/building/b{n}` for basement levels

### Level 3: Space Type
- Common types: `room`, `corridor`, `lobby`, `stairwell`, `elevator`, `equipment`, `utility`
- Example: `/hq/f1/room`, `/hq/f2/corridor`

### Level 4: Space Identifier
- Rooms: Numeric (101, 102) or named (conference_a, lobby_main)
- Corridors: Named or directional (main, north_south, east_west)
- Equipment: System-based (hvac, electrical, plumbing)

### Level 5: Component Type
- Physical: `wall`, `door`, `window`, `ceiling`, `floor`
- Systems: `sensor`, `actuator`, `controller`, `unit`
- Fixtures: `light`, `outlet`, `switch`, `vent`

### Level 6: Component Identifier
- Directional: `north`, `south`, `east`, `west`, `ne`, `nw`, `se`, `sw`
- Functional: `main`, `emergency`, `service`
- Sequential: `1`, `2`, `3` or `a`, `b`, `c`

## Special Cases

### Multi-Building Complexes
```
/campus/building_id/...
/site_name/building_id/...
```

### Shared Walls/Components
Use the lower-numbered or alphabetically-first space:
```
/hq/f1/room/101/wall/east  (shared with room 102)
```

### Building Systems
Global systems that span the building:
```
/hq/systems/hvac/ahu/1
/hq/systems/electrical/panel/main
/hq/systems/fire/zone/3
/hq/systems/security/camera/entrance_main
```

### Virtual/Logical Objects
```
/hq/virtual/network/ap/1
/hq/virtual/occupancy/zone/lobby
/hq/virtual/energy/meter/floor_2
```

## File Storage

### Filesystem Mapping
ArxObject IDs map to filesystem paths with these transformations:
1. Replace `/` with OS path separator
2. Append `.json` for object files
3. Store in `.arxos/objects/` directory

Example:
- ArxObject ID: `/hq/f1/room/101/wall/north`
- File path: `.arxos/objects/hq/f1/room/101/wall/north.json`

### Alternative Flat Storage
For systems that can't handle deep directories:
- Use double underscore as delimiter: `hq__f1__room__101__wall__north.json`

## Query Patterns

### Wildcards
- `*` matches any single segment: `/hq/f1/room/*/door/*`
- `**` matches multiple segments: `/hq/**/sensor/*`

### Type Queries
- All rooms: `/*/f*/room/*`
- All doors: `/*/*/*/*/*/door/*`
- All sensors: `/**/*sensor*/*`

## Migration Path

### From Current Format
```
Current: building:hq:floor:1:room:101:wall:north
New:     /hq/f1/room/101/wall/north

Current: building:hq:system:hvac
New:     /hq/systems/hvac
```

### Compatibility Layer
- Accept both formats during transition
- Internally normalize to new format
- Provide migration tool

## Benefits

1. **Filesystem Navigation**: Can use actual OS filesystem for navigation
2. **URL-Compatible**: Can expose via REST API without encoding issues
3. **Glob Patterns**: Standard filesystem glob patterns work
4. **Hierarchy Clear**: Each level has specific meaning
5. **Extensible**: Can add new levels or types without breaking scheme

## Implementation Notes

### ID Generation Function
```go
func GenerateArxObjectID(building, floor, spaceType, spaceID, componentType, componentID string) string {
    parts := []string{building}
    
    if floor != "" {
        parts = append(parts, floor)
    }
    if spaceType != "" {
        parts = append(parts, spaceType)
    }
    if spaceID != "" {
        parts = append(parts, spaceID)
    }
    if componentType != "" {
        parts = append(parts, componentType)
    }
    if componentID != "" {
        parts = append(parts, componentID)
    }
    
    return "/" + strings.Join(parts, "/")
}
```

### Navigation Examples
```bash
# Navigate to room 101
cd /hq/f1/room/101

# List all walls in current room
ls wall/

# Show all doors on floor 2
ls /hq/f2/room/*/door/

# Go up to floor level
cd ../..
```

### Query Examples
```sql
-- All rooms on floor 1
SELECT * FROM /hq/f1/room/*

-- All temperature sensors
SELECT * FROM /hq/**/sensor/temp/*

-- All doors in building
SELECT * FROM /hq/**/door/*

-- Everything in room 101
SELECT * FROM /hq/f1/room/101/**
```