# Arxos - Google Maps for Buildings

> **The entire vision with just Go, vanilla JS, HTML/CSS, and PostgreSQL/PostGIS.**

A lightweight, performance-first building infrastructure platform that treats every element as an **ArxObject** - from entire campuses down to individual circuit traces.

## 🎯 Core Philosophy

**The magic is in the ArxObject design, not framework complexity.**

We can render the entire information map - from satellite view to circuit traces - with the simplest possible stack. No React. No Python. No TypeScript. Just the essentials.

## 🏗️ The Complete Stack

That's it. That's the entire stack:

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Go | ArxObject engine, API, WebSocket, tile generation |
| **Database** | PostgreSQL + PostGIS | Spatial queries, fractal indexing |
| **Frontend** | Vanilla JS | 4 clean components (400 lines total) |
| **Markup** | HTML + CSS | Simple, semantic, fast |
| **Updates** | HTMX (optional) | Partial updates without JS complexity |

## 🚀 Quick Start

```bash
# Start everything
docker-compose up -d

# Or run locally
go run core/backend/main.go  # Backend at :8080
open frontend/web/index.html # Frontend ready!

# That's it. No npm install. No build step. Just works.
```

## 🔍 Fractal Scale Levels

Just like Google Maps, but for buildings:

```
Scale    Level        View
──────────────────────────────────
10^7     GLOBAL      Continental power grids
10^6     REGIONAL    State infrastructure  
10^5     MUNICIPAL   City systems
10^4     CAMPUS      Property boundaries
10^3     BUILDING    Exterior walls
10^2     FLOOR       Floor plans
10^1     ROOM        Room layouts
10^0     COMPONENT   Equipment details
10^-3    CIRCUIT     Circuit boards
10^-4    TRACE       Copper paths
```

## 🎮 Controls

- **Scroll** - Zoom through scale levels
- **Drag** - Pan around
- **Click** - Select ArxObject
- **1-4** - Toggle systems (Electrical/HVAC/Plumbing/Structural)
- **F** - Fit to view
- **ESC** - Clear selection

## 📦 The ArxObject Magic

```go
type ArxObject struct {
    ID       uint64        // Fast numeric ID
    Type     ArxObjectType // Building system type
    X, Y, Z  int32        // Millimeter precision
    Width    int16        // Dimensions
    Height   int16
    System   string       // electrical, hvac, plumbing, structural
}
```

Every building element - from a campus to a screw - is an ArxObject. The hierarchy is fractal:

```
arx:campus:building:floor:room:wall:outlet:terminal:screw
```

## 🏃 Performance

With our minimal stack:

- **< 16ms** frame time (60fps)
- **< 1s** initial load
- **< 100KB** per tile transfer
- **< 50MB** client memory usage
- **1M+** ArxObjects per building (via tiles)

## 🗺️ How It Works (Like Google Maps)

### Tile-Based Loading
```go
// Go generates tiles based on zoom/pan
func GetTile(zoom, x, y int) []ArxObject {
    return db.Query(`
        SELECT * FROM arx_objects 
        WHERE geom && ST_MakeEnvelope($1,$2,$3,$4)
        AND scale_min <= $5 AND scale_max >= $5
    `, bounds, zoom)
}
```

### Scale-Aware Rendering
```javascript
// Only 400 lines of vanilla JS
class SvgRenderer {
    renderAtScale(scale) {
        // Fetch only objects visible at this scale
        const objects = await fetch(`/api/tiles/${scale}/${x}/${y}`);
        // Render as simple SVG
        objects.forEach(obj => this.drawArxObject(obj));
    }
}
```

### Real-Time Updates
```javascript
// WebSocket for live collaboration
const ws = new WebSocket('ws://localhost:8080/ws');
ws.onmessage = (e) => {
    const arxObject = JSON.parse(e.data);
    renderer.updateObject(arxObject);  // Instant updates!
};
```

## 📊 Three Ingestion Methods

All in pure Go:

1. **PDF/IFC** - Symbol recognition from digital plans
2. **Photo** - OCR + perspective correction for paper maps  
3. **LiDAR** - Real-time point cloud capture

## 🌟 Key Features

- **Fractal Hierarchy** - Infinite zoom levels
- **System Planes** - Z-order layering for overlapping systems
- **Community Reporting** - Photo → Issue → ArxObject
- **Real-time Sync** - WebSocket updates
- **Tile Caching** - Google Maps-like performance

## 🛠️ Development

```bash
# Backend development
cd core/backend
go run main.go

# Frontend development  
cd frontend/web
# Just edit index.html and arxos-core.js
# Refresh browser - no build needed!

# Database
psql arxos < infrastructure/database/001_create_arx_schema.sql
```

## 📈 Why This Stack?

### What We DON'T Need:
- ❌ **React/Vue/Angular** - Vanilla JS is faster
- ❌ **Python** - Go handles everything
- ❌ **GraphQL** - REST is simpler
- ❌ **Microservices** - Monolith is perfect
- ❌ **Webpack/Babel** - No build step!
- ❌ **Redux** - Simple state object works
- ❌ **Docker Swarm/K8s** - Single binary scales

### What We Have:
- ✅ **29K lines** of focused code (was 198K)
- ✅ **2 languages** instead of 4
- ✅ **1 binary** deployment
- ✅ **0 build steps**
- ✅ **60fps** performance
- ✅ **< 1 second** load time

## 🎯 The Vision

**"What if buildings were as queryable as Google Maps?"**

With Arxos, they are. Navigate from a satellite view of a campus down to the individual copper traces on a circuit board. Every element is spatially indexed, instantly queryable, and rendered at the appropriate scale.

All with just:
- Go (backend)
- PostgreSQL + PostGIS (spatial data)
- Vanilla JavaScript (frontend)
- HTML/CSS (markup)

**No frameworks. No complexity. Just speed and elegance.**

## 📝 License

MIT

---

**Remember:** The innovation is ArxObject and fractal scaling, not the tech stack. Keep it simple. Keep it fast.