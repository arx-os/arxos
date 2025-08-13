# Arxos Quick Start for New Developers

## 🎯 What is Arxos?
**Google Maps for Buildings** - Infinite fractal zoom from campus to screw, with every outlet, pipe, and wire mapped.

## 🏗️ Core Concept: ArxObject
The DNA of building infrastructure:
```go
ID: "arx:building_1:floor_2:room_203:outlet_4"
```
- Hierarchical IDs create natural parent-child relationships
- Objects appear/disappear based on zoom level (like Google Maps)
- Standard SVG for rendering (no custom formats!)

## 🚀 Get Started in 5 Minutes

### 1. Clone and Setup
```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
cp .env.example .env.production
# Edit .env.production with your database credentials
```

### 2. Run with Docker
```bash
docker-compose -f docker-compose.production.yml up -d
```

### 3. Test the API
```bash
# Health check
curl http://localhost:8080/api/v1/health

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get buildings
curl http://localhost:8080/api/v1/arxobjects?type=building
```

### 4. Open Web Interface
Navigate to: http://localhost:3000

## 📁 Project Structure
```
arxos/
├── arxos-core/          # ArxObject implementation (Go)
├── arxos-api/           # REST API with JWT auth (Go)
├── arxos-ingestion/     # PDF, Photo, LiDAR ingestion (Go)
├── arxos-storage/       # Database schema (PostgreSQL)
├── web/                 # Web interface (Vanilla JS + SVG)
└── svgx_engine/         # Symbol recognition (Python)
    └── services/symbols/  # Symbol library
```

## 🔑 Key Features

### 1. Fractal Zoom Levels
- **100x**: Campus (buildings as dots)
- **10x**: Building (floors visible)
- **1x**: Floor (rooms visible)
- **0.1x**: Room (fixtures visible)
- **0.01x**: Wall (outlets visible)
- **0.001x**: Component (wires visible)

### 2. Three Ingestion Methods
- **PDF**: Upload building plans → Auto-recognize symbols
- **Photo**: Snap paper map → Perspective correction + OCR
- **LiDAR**: Walk the building → Real-time capture

### 3. System Layers
Toggle visibility of different building systems:
- Electrical (outlets, lights, panels)
- Mechanical (HVAC, ducts, vents)
- Plumbing (pipes, fixtures, valves)
- Fire Protection (sprinklers, alarms)
- Structural (walls, columns, beams)

## 💻 Development Workflow

### Making Changes
1. **ArxObject Logic**: Edit `arxos-core/arxobject.go`
2. **API Endpoints**: Edit `arxos-api/main.go`
3. **Symbol Recognition**: Edit `svgx_engine/services/symbols/symbol_recognition.py`
4. **Web Interface**: Edit `web/js/arxos-core.js`

### Running Tests
```bash
# All tests
python scripts/test_all.py

# Specific component
go test ./arxos-core/...
python -m pytest tests/unit/
```

### Adding a New Symbol
1. Add to `svgx_engine/services/symbols/symbol_recognition.py`:
```python
symbols['new_symbol'] = {
    'system': 'electrical',
    'display_name': 'New Symbol',
    'tags': ['tag1', 'tag2'],
    'svg': '<circle cx="0" cy="0" r="5"/>'
}
```

2. Restart the symbol service:
```bash
docker-compose restart svgx-engine
```

## 🎨 Frontend Development

### Rendering an ArxObject
```javascript
// Check if object is visible at current zoom
if (scale >= obj.scaleMin && scale <= obj.scaleMax) {
    // Render as standard SVG
    svg.innerHTML += `
        <g transform="translate(${obj.x}, ${obj.y})">
            ${obj.svgPath}
        </g>
    `;
}
```

### System Plane Layering
Objects are rendered in order:
1. Structural (bottom)
2. Architectural
3. Plumbing
4. Mechanical
5. Electrical
6. Fire Protection
7. Data (top)

## 🐛 Common Issues

### Symbol Recognition Not Working
```bash
# Check Python bridge
cd svgx_engine/services/symbols
python3 -c "from symbol_recognition import SymbolRecognitionEngine; print('OK')"
```

### Database Connection Failed
```bash
# Check PostgreSQL
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

### Authentication Issues
```bash
# Get new token
TOKEN=$(curl -X POST http://localhost:8080/api/v1/auth/login \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Use token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/v1/arxobjects
```

## 📚 Key Documentation
- `ARXOBJECT_COMPLETE_SPECIFICATION.md` - Full ArxObject spec
- `ENGINEERING_TODO.md` - What needs work
- `SESSION_SUMMARY_2024.md` - Recent development decisions
- `DEPLOYMENT_GUIDE.md` - Production deployment

## 🚀 Next Priority Items
1. **Mobile App** - For LiDAR field capture
2. **Real PDF Processing** - PyPDF2 integration
3. **Photo Enhancement** - OpenCV for perspective
4. **WebSocket** - Real-time collaboration
5. **BILT Rewards** - Token distribution system

## 💡 Remember
- **ArxObject is the innovation** (not rendering)
- **Standard SVG is perfect** (no SVGX needed!)
- **Fractal hierarchy enables everything**
- **Scale-based visibility is the magic**
- **Three ingestion methods are all critical**

---

Welcome to Arxos! You're building Google Maps for the physical world's infrastructure. 🏗️📍