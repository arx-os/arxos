# Arxos - Google Maps for Buildings

A lightweight, performance-first building infrastructure platform that treats every element as an **ArxObject** - from entire campuses down to individual circuit traces.

## 🎯 Core Philosophy

**The magic is in the ArxObject design, not framework complexity.**

Arxos implements fractal scaling for buildings - just like Google Maps, but for infrastructure. Zoom from satellite view to circuit board level in one seamless experience.

## 🏗️ Architecture

### Four Core Components (Vanilla JS)

1. **DataManager** - Handles ArxObject data and API communication
2. **StateManager** - Manages application state with fractal navigation
3. **SvgRenderer** - Pure SVG rendering with scale-aware optimization
4. **InteractionManager** - Handles user input and navigation

### Backend (Go)

- **ArxObject Engine** - Optimized for speed with fixed-point math
- **Spatial Indexing** - Flat quadtree for cache-efficient queries
- **PostgreSQL + PostGIS** - Spatial data storage
- **Redis** - Caching and real-time updates

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Access the app
open http://localhost
```

## 🔍 Scale Levels

```
10,000,000  GLOBAL     - Continental view
1,000,000   REGIONAL   - State/province level
100,000     MUNICIPAL  - City level
10,000      CAMPUS     - Property level
1,000       BUILDING   - Building exterior
100         FLOOR      - Floor plans
10          ROOM       - Room details
1           COMPONENT  - Equipment level
0.001       CIRCUIT    - Circuit board level
0.0001      TRACE      - Individual traces
```

## 🎮 Controls

- **Scroll** - Zoom in/out through scale levels
- **Drag** - Pan around the view
- **Click** - Select ArxObject
- **1-4** - Toggle systems (Electrical, HVAC, Plumbing, Structural)
- **F** - Fit to view
- **ESC** - Clear selection

## 📦 ArxObject Structure

```go
type ArxObject struct {
    ID       uint64        // Fast numeric ID
    Type     ArxObjectType // Building system type
    X, Y, Z  int32        // Position in millimeters
    Width    int16        // Dimensions
    Height   int16
    System   string       // electrical, hvac, plumbing, structural
}
```

## 🏃 Performance

- **< 16ms** frame time (60fps)
- **< 2s** initial load
- **< 500ms** scale transitions
- **< 2GB** memory for complete navigation
- **1M+** ArxObjects per building

## 🛠️ Development

```bash
# Backend (Go)
cd core/backend
go run main.go

# Frontend (Vanilla JS)
cd frontend/web
# Just open index.html - no build needed!
```

## 📊 Three Ingestion Methods

1. **PDF/IFC** - Symbol recognition from digital plans
2. **Photo** - OCR + perspective correction for paper maps
3. **LiDAR** - Real-time field capture

## 🌟 Key Features

- **Fractal Hierarchy** - `arx:building:floor:room:outlet:terminal`
- **Scale-Based Visibility** - Objects appear/disappear based on zoom
- **System Planes** - Z-order layering for overlapping systems
- **Real-time Updates** - WebSocket synchronization
- **Community Reporting** - Infrastructure issue tracking

## 📝 License

MIT

---

**Remember:** Keep it simple. The innovation is ArxObject, not complexity.