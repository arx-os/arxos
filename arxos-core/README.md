# Arxos Core - The ArxObject Foundation

## Purpose
This is the heart of Arxos - the ArxObject data structure that represents any piece of building infrastructure from a campus down to a screw.

## What is an ArxObject?
An ArxObject is the "DNA capsule" of building infrastructure. It knows:
- **What it is** (identity)
- **Where it exists** (position in space)
- **When it's visible** (zoom level)
- **How it connects** to other objects
- **Its complete history**

## Key Files
- `arxobject.go` - The ArxObject data structure (single source of truth)
- `repository.go` - Database operations for ArxObjects
- `engine.go` - Core operations and spatial queries
- `hierarchy.go` - Fractal parent-child relationships
- `overlaps.go` - System plane and overlap resolution

## Quick Example
```go
// Create a new electrical outlet ArxObject
outlet := &ArxObject{
    ID:       "arx:plant-high:floor-1:room-201:outlet-1",
    Type:     "outlet",
    System:   "electrical",
    ParentID: "arx:plant-high:floor-1:room-201",
    Position: Position{X: 1234.567, Y: 5678.901, Z: 450},
    ScaleMin: 0.01,  // Visible at room zoom and closer
    ScaleMax: 0.001, // Visible down to component level
}
```

## Architecture Principles
1. **Single Source of Truth** - This is THE ArxObject definition
2. **Fractal Hierarchy** - Objects contain objects infinitely
3. **System Planes** - Handle 2D overlaps with Z-order layers
4. **Scale Awareness** - Objects appear/disappear based on zoom

## For New Engineers
Start here to understand Arxos. The ArxObject is the foundation everything else builds upon.