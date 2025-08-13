# Arxos Architecture - Pure Simplicity

> **The entire Google Maps for Buildings vision with just Go, vanilla JS, HTML/CSS, and PostgreSQL/PostGIS.**

## Core Principle

We can render an infinite information map - from satellite view to circuit traces - with the absolute minimum stack. The innovation is the ArxObject and fractal scaling, not framework complexity.

## System Architecture

```
┌─────────────────┐
│   Browser       │
│  ┌───────────┐  │
│  │  HTML/CSS │  │  ← Static files (no build)
│  │  Vanilla  │  │  ← 400 lines of JS
│  │    JS     │  │  ← 4 clean components
│  └─────┬─────┘  │
│        │        │
│   WebSocket &   │
│   REST API      │
└────────┬────────┘
         │
┌────────┴────────┐
│   Go Backend    │
│  ┌───────────┐  │
│  │ ArxObject │  │  ← Core engine
│  │  Engine   │  │  ← Spatial indexing
│  │   Tiles   │  │  ← Map-like loading
│  └─────┬─────┘  │
└────────┬────────┘
         │
┌────────┴────────┐
│  PostgreSQL +   │
│    PostGIS      │  ← Spatial queries
└─────────────────┘
```

## The Four Frontend Components

### 1. DataManager (Data & API)
```javascript
class DataManager {
    arxObjects = new Map()      // Object cache
    scaleCache = new Map()      // Tile cache
    
    async fetchArxObjectsAtScale(scale, viewport) {
        // Fetch only visible objects at current scale
        // Cache for performance
    }
}
```

### 2. StateManager (Application State)
```javascript
class StateManager {
    state = {
        scaleLevel: 1.0,        // Current zoom
        viewport: {x,y,w,h},    // Visible area
        selectedObject: null,    // Selection
        visibleSystems: [...]    // Layer visibility
    }
    
    // Observer pattern for reactive updates
    updateState(changes) { /* notify observers */ }
}
```

### 3. SvgRenderer (Pure SVG Rendering)
```javascript
class SvgRenderer {
    renderAtScale(scale) {
        // Create SVG elements for ArxObjects
        // Scale-aware visibility
        // System-based styling
    }
}
```

### 4. InteractionManager (User Input)
```javascript
class InteractionManager {
    handleZoom(delta)    // Fractal navigation
    handlePan(dx, dy)    // Viewport movement
    handleClick(x, y)    // Object selection
    handleKeyboard(key)  // System toggles
}
```

## Backend Architecture (Go)

### Core ArxObject Engine
```go
// Optimized for speed with fixed-point math
type ArxObject struct {
    ID       uint64  // Fast numeric ID
    Type     uint8   // Building system type
    X, Y, Z  int32   // Position in millimeters
    Width    int16   // Dimensions
    Height   int16
    System   string  // electrical, hvac, plumbing, structural
}

// Cache-efficient spatial queries
type Engine struct {
    objects []ArxObject      // Flat array for cache locality
    spatial *SpatialIndex    // Quadtree indexing
    idIndex map[uint64]int   // O(1) lookups
}
```

### Tile Generation (Like Google Maps)
```go
type TileService struct {
    db *sql.DB
}

func (t *TileService) GetTile(zoom, x, y int) []ArxObject {
    // Calculate tile bounds
    bounds := TileToBounds(zoom, x, y)
    
    // Query PostGIS for objects in tile
    query := `
        SELECT id, type, ST_X(geom), ST_Y(geom), properties
        FROM arx_objects
        WHERE geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
        AND scale_min <= $5 AND scale_max >= $5
        ORDER BY z_order
    `
    
    return t.executeQuery(query, bounds, zoom)
}
```

### WebSocket for Real-time Updates
```go
type Hub struct {
    clients map[*Client]bool
    broadcast chan ArxObject
}

func (h *Hub) Run() {
    for {
        select {
        case obj := <-h.broadcast:
            // Send update to all connected clients
            for client := range h.clients {
                client.send <- obj
            }
        }
    }
}
```

## Database Schema (PostgreSQL + PostGIS)

### Spatial Tables
```sql
-- Core ArxObject table with spatial indexing
CREATE TABLE arx_objects (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    system VARCHAR(20) NOT NULL,
    geom GEOMETRY(POINTZ, 4326),
    scale_min INTEGER NOT NULL,
    scale_max INTEGER NOT NULL,
    z_order INTEGER DEFAULT 0,
    properties JSONB,
    
    -- Spatial index for viewport queries
    CONSTRAINT arx_objects_geom_idx 
        USING GIST (geom)
);

-- Fractal hierarchy
CREATE TABLE arx_hierarchy (
    parent_id BIGINT REFERENCES arx_objects(id),
    child_id BIGINT REFERENCES arx_objects(id),
    relationship VARCHAR(50),
    PRIMARY KEY (parent_id, child_id)
);
```

### Scale-Based Indexing
```sql
-- Index for efficient scale queries
CREATE INDEX idx_scale_range ON arx_objects(scale_min, scale_max);

-- System plane indexing
CREATE INDEX idx_system_zorder ON arx_objects(system, z_order);

-- Tile query optimization
CREATE INDEX idx_tile_query ON arx_objects 
    USING GIST (geom) 
    WHERE scale_min <= 1000 AND scale_max >= 100;
```

## Fractal Scale System

```
Scale Level   Database Storage         Visible Elements
─────────────────────────────────────────────────────
10,000,000    Campus boundaries        Buildings as dots
1,000,000     Building outlines        Floors as lines
100,000       Floor plans              Rooms as polygons
10,000        Room layouts             Walls, doors
1,000         Wall details             Outlets, switches
100           Component level          Wiring, conduits
10            Equipment internals      Circuit boards
1             Circuit details          Components
0.001         Microscopic              Traces, solder points
```

## Performance Optimizations

### 1. Tile-Based Loading
- Only load visible objects
- Cache tiles client-side
- Predictive pre-loading based on pan direction

### 2. Fixed-Point Math
```go
// Millimeter precision with int32 (±2,147km range)
X, Y, Z int32  // Instead of float64

// Fast distance calculations
func Distance(a, b *ArxObject) int32 {
    dx := a.X - b.X
    dy := a.Y - b.Y
    // Approximate distance without sqrt
    return abs(dx) + abs(dy)
}
```

### 3. Spatial Indexing
```go
// Flat quadtree for cache efficiency
type SpatialIndex struct {
    grid [][]uint64  // 2D grid of object IDs
    gridSize int     // Resolution
}

// O(1) grid lookup
func (s *SpatialIndex) GetCell(x, y int32) []uint64 {
    gridX := x / s.gridSize
    gridY := y / s.gridSize
    return s.grid[gridY][gridX]
}
```

## Ingestion Pipeline (All Go)

### PDF Processing
```go
func ProcessPDF(path string) []ArxObject {
    // 1. Extract pages as images
    // 2. Detect symbols using image processing
    // 3. OCR for text labels
    // 4. Convert to ArxObjects with spatial positions
}
```

### Photo Ingestion
```go
func ProcessPhoto(img image.Image) []ArxObject {
    // 1. Perspective correction
    // 2. Enhance contrast
    // 3. Symbol detection
    // 4. Create ArxObjects
}
```

### LiDAR Processing
```go
func ProcessPointCloud(points []Point3D) []ArxObject {
    // 1. Cluster points into surfaces
    // 2. Detect walls, floors, equipment
    // 3. Generate ArxObjects with 3D positions
}
```

## Deployment

### Development
```bash
# Single terminal
go run core/backend/main.go

# Browser
open frontend/web/index.html

# Done! Hot reload by refreshing browser
```

### Production
```bash
# Build single binary
go build -o arxos core/backend/main.go

# Run with systemd
[Unit]
Description=Arxos Server
After=postgresql.service

[Service]
Type=simple
ExecStart=/usr/local/bin/arxos
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker (Optional)
```yaml
version: '3.8'
services:
  arxos:
    build: .
    ports: ["8080:8080"]
  
  postgres:
    image: postgis/postgis:15-3.3
    volumes: ["./schema.sql:/docker-entrypoint-initdb.d/"]
  
  redis:
    image: redis:7-alpine
```

## Why This Architecture Works

### Simplicity
- **2 languages** (Go + JS) instead of 4+
- **0 build steps** - just run and refresh
- **1 binary** deployment
- **No npm**, no webpack, no transpiling

### Performance
- **60fps** rendering with vanilla JS
- **< 100KB** per tile transfer
- **< 50MB** client memory
- **Sub-second** scale transitions

### Scalability
- Single Go binary handles thousands of users
- PostgreSQL scales to billions of ArxObjects
- Tile caching reduces database load
- WebSocket for efficient real-time updates

## The Magic Formula

```
ArxObject (fractal data structure)
+ PostGIS (spatial indexing)
+ Tile Loading (Google Maps pattern)
+ Vanilla JS (no framework overhead)
= Google Maps for Buildings
```

That's it. That's the entire system. **The innovation is in the ArxObject design and fractal scaling, not in complex technology.**