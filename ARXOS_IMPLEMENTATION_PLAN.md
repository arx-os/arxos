# Arxos Implementation Plan
## From Vision to Reality - Clean, Organized, Professional

---

## 🎯 Mission Statement
Build Arxos as the "Google Maps for Buildings" with a clean, understandable codebase that any engineer can jump into and immediately understand.

---

## 🧹 Phase 0: Codebase Cleanup (Week 1)
**Goal: Remove all dead code and organize what remains**

### Items to DELETE Immediately

#### 1. Remove Desktop Application Code
```bash
# ArxIDE was abandoned - remove it
rm -rf /arxide/                    # Entire desktop app
rm -rf /frontend/desktop/          # Desktop frontend
rm docker-compose.arxide.yml       # Desktop Docker config
```

#### 2. Remove Duplicate/Unused Services
```bash
rm -rf /services/ai/               # Unused AI service
rm -rf /services/cmms/             # CMMS not needed yet
rm -rf /services/construction/     # Future feature
rm -rf /services/data-vendor/      # Not implemented
rm -rf /services/partners/         # Future feature
rm -rf /services/planarx/          # Unknown service
rm -rf /services/mcp/              # Not implemented
```

#### 3. Remove Excessive Documentation
```bash
# Keep only essential docs
rm -rf /docs/DEVELOPMENT/          # 50+ planning docs
rm -rf /docs/architecture/ADR-*.md # Architecture decisions
rm -rf /reports/                   # Old analysis reports
rm -rf /tools/education/           # Educational materials

# Keep only:
# - README.md files
# - API documentation
# - Setup guides
```

#### 4. Clean Frontend Chaos
```bash
# Multiple frontend attempts - pick ONE
rm -rf /frontend/android/          # Future
rm -rf /frontend/ios/              # Future
rm -rf /frontend/fractal-demo/     # Demo code

# KEEP ONLY:
# /frontend/web/ - The main web interface
```

#### 5. Remove Test/Example Code
```bash
rm -rf /examples/                  # Example code
rm -rf /plugins/                   # Plugin examples
rm -rf /sdk/                       # SDK not ready
```

### Items to REORGANIZE

#### Current Messy Structure → Clean Structure
```
CURRENT (Messy):                   NEW (Clean):
/core/                             /arxos-core/
  /arxobject/                        /arxobject/     # THE ArxObject
  /backend/                          /engine/        # Core engine
  /constraints/                      /spatial/       # Spatial logic
  /optimization/                     
  /security/                       /arxos-api/
  /shared/                           /server/        # API server
  /spatial/                          /routes/        # API routes
  /streaming/                        /middleware/    # Auth, etc.

/svgx_engine/                      /arxos-ingestion/
  (100+ files)                       /pdf/           # PDF parser
                                     /photo/         # Photo parser
/frontend/web/                       /lidar/         # LiDAR capture
  (50+ HTML files)                   /symbols/       # Symbol library

/services/                         /arxos-web/
  /gus/                              /src/           # React/Vue app
  /iot/                              /public/        # Static files
  (many others)                      /api/           # API client
```

---

## 📁 Phase 1: New Folder Structure (Week 1)
**Goal: Organize code so it's immediately understandable**

```
arxos/
├── README.md                     # "Start Here" guide
├── ARCHITECTURE.md               # How it all fits together
├── docker-compose.yml            # One-command startup
│
├── arxos-core/                   # The Heart: ArxObject
│   ├── README.md                 # "This is the DNA of buildings"
│   ├── arxobject.go              # THE ArxObject definition
│   ├── repository.go             # Database operations
│   ├── engine.go                 # Core operations
│   └── tests/                    # Unit tests
│
├── arxos-ingestion/              # Getting Data In
│   ├── README.md                 # "How we eat building data"
│   ├── pdf/                      # PDF → ArxObject
│   │   ├── parser.go
│   │   └── extractor.go
│   ├── photo/                    # Photo → ArxObject
│   │   ├── perspective.go
│   │   └── ocr.go
│   ├── lidar/                    # LiDAR → ArxObject
│   │   └── capture.go
│   └── symbols/                  # Symbol Recognition
│       ├── library.go            # Symbol definitions
│       └── matcher.go            # Pattern matching
│
├── arxos-api/                    # REST API
│   ├── README.md                 # "API Reference"
│   ├── server.go                 # Main server
│   ├── routes/
│   │   ├── arxobject.go          # CRUD operations
│   │   ├── ingestion.go          # Upload endpoints
│   │   └── query.go              # Search/filter
│   └── middleware/
│       └── auth.go               # Authentication
│
├── arxos-web/                    # Web Interface
│   ├── README.md                 # "User Interface"
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx               # Main app
│   │   ├── components/
│   │   │   ├── Viewer/           # Fractal viewer
│   │   │   ├── Upload/           # File upload
│   │   │   └── SystemToggle/     # System layers
│   │   └── api/
│   │       └── client.ts         # API client
│   └── public/
│
├── arxos-storage/                # Database
│   ├── migrations/               # Schema versions
│   │   ├── 001_arxobjects.sql
│   │   ├── 002_symbols.sql
│   │   └── 003_contributions.sql
│   └── seed/                     # Test data
│
└── scripts/                      # Utility Scripts
    ├── setup.sh                  # First-time setup
    ├── cleanup.sh                # Remove old code
    └── test.sh                   # Run all tests
```

---

## 🏗️ Phase 2: Core ArxObject Implementation (Week 2)
**Goal: Build THE foundational data structure**

### Step 1: Create True ArxObject
```go
// arxos-core/arxobject.go
// THIS IS THE SINGLE SOURCE OF TRUTH

type ArxObject struct {
    // Identity (What am I?)
    ID          string    `json:"id"`          // "arx:building:floor:room:object"
    Type        string    `json:"type"`        // "outlet", "room", "building"
    Name        string    `json:"name"`        // Human readable
    System      string    `json:"system"`      // "electrical", "hvac", etc.
    
    // Hierarchy (Where do I belong?)
    ParentID    string    `json:"parent_id"`   // Fractal parent
    ChildIDs    []string  `json:"child_ids"`   // Fractal children
    
    // Space (Where am I?)
    Position    Position  `json:"position"`    // X, Y, Z coordinates
    Dimensions  Dims      `json:"dimensions"`  // Width, Height, Depth
    
    // Layers (How do I overlap?)
    SystemPlane Plane     `json:"plane"`       // Z-order, elevation
    Overlaps    []string  `json:"overlaps"`    // Other objects at same spot
    
    // Visibility (When do I appear?)
    ScaleMin    float64   `json:"scale_min"`   // Minimum zoom
    ScaleMax    float64   `json:"scale_max"`   // Maximum zoom
    
    // Recognition (How was I found?)
    SymbolID    string    `json:"symbol_id"`   // Symbol library reference
    Source      string    `json:"source"`      // "pdf", "photo", "lidar"
    Confidence  float64   `json:"confidence"`  // Recognition confidence
    
    // Contribution (Who added me?)
    CreatedBy   string    `json:"created_by"`  // User ID
    CreatedAt   time.Time `json:"created_at"`  // Timestamp
    BILTReward  float64   `json:"bilt_reward"` // Tokens earned
}
```

### Step 2: Create Repository Pattern
```go
// arxos-core/repository.go
type ArxObjectRepository interface {
    Create(obj *ArxObject) error
    Get(id string) (*ArxObject, error)
    Update(obj *ArxObject) error
    Delete(id string) error
    
    // Fractal queries
    GetChildren(parentID string) ([]*ArxObject, error)
    GetAtScale(scale float64, viewport Viewport) ([]*ArxObject, error)
    
    // System queries
    GetBySystem(system string) ([]*ArxObject, error)
    GetOverlapping(position Position) ([]*ArxObject, error)
}
```

---

## 🔍 Phase 3: Symbol Library & Recognition (Week 3)
**Goal: Teach Arxos to "read" building plans**

### Step 1: Define Symbol Structure
```go
// arxos-ingestion/symbols/symbol.go
type Symbol struct {
    ID          string
    System      string        // "electrical", "hvac", etc.
    Category    string        // "outlet", "switch", etc.
    Pattern     string        // SVG pattern to match
    TextClues   []string      // Text to look for nearby
    Properties  map[string]interface{}
    DefaultLayer int          // Z-order
}
```

### Step 2: Build Symbol Library
```go
// arxos-ingestion/symbols/library.go
var ElectricalSymbols = []Symbol{
    {
        ID:       "symbol:electrical:outlet:duplex",
        System:   "electrical",
        Category: "outlet",
        Pattern:  "M0,0 A5,5 0 1,1 0,0.1 M-3,0 L3,0",
        TextClues: []string{"120V", "DUPLEX", "GFCI"},
        DefaultLayer: 25,
    },
    // ... more symbols
}
```

---

## 📥 Phase 4: Three Ingestion Methods (Week 4)
**Goal: Get building data into Arxos**

### Method 1: PDF Ingestion
```go
// arxos-ingestion/pdf/ingest.go
func IngestPDF(file []byte) ([]*ArxObject, error) {
    elements := ExtractElements(file)
    symbols := LoadSymbolLibrary()
    
    objects := []*ArxObject{}
    for _, element := range elements {
        if match := symbols.Match(element); match != nil {
            obj := CreateArxObject(match, element)
            objects = append(objects, obj)
        }
    }
    return objects, nil
}
```

### Method 2: Photo of Paper Map
```go
// arxos-ingestion/photo/ingest.go
func IngestPhoto(image []byte) ([]*ArxObject, error) {
    corrected := PerspectiveCorrect(image)
    text := OCR(corrected)
    rooms := DetectRooms(corrected)
    
    // Create room ArxObjects
    objects := CreateRoomObjects(rooms, text)
    return objects, nil
}
```

### Method 3: LiDAR Capture
```go
// arxos-ingestion/lidar/capture.go
func CaptureLiDAR(session *LiDARSession) ([]*ArxObject, error) {
    walls := DetectWalls(session.PointCloud)
    objects := CreateWallObjects(walls)
    return objects, nil
}
```

---

## 🌐 Phase 5: API Layer (Week 5)
**Goal: Clean REST API**

### Core Endpoints
```go
// arxos-api/routes/arxobject.go

// Basic CRUD
POST   /api/arxobjects              // Create
GET    /api/arxobjects/:id          // Read
PUT    /api/arxobjects/:id          // Update
DELETE /api/arxobjects/:id          // Delete

// Ingestion
POST   /api/ingest/pdf              // Upload PDF
POST   /api/ingest/photo            // Upload photo
POST   /api/ingest/lidar            // Start LiDAR session

// Queries
GET    /api/arxobjects/scale/:zoom  // Get by zoom level
GET    /api/arxobjects/system/:type // Get by system
GET    /api/arxobjects/tile/:z/:x/:y // Tile-based loading
```

---

## 🖥️ Phase 6: Web Interface (Week 6)
**Goal: Clean, simple UI**

### Core Components
```typescript
// arxos-web/src/components/

1. FractalViewer    - Google Maps-style zoom
2. SystemToggle     - Turn systems on/off
3. FileUpload       - PDF/Photo ingestion
4. ArxObjectInfo    - Click to see details
5. ContributionForm - Add/edit objects
```

---

## 📚 Documentation Standards

### Every Folder Gets a README
```markdown
# Folder Name
## Purpose
One sentence explaining why this exists.

## Key Files
- `main.go` - Entry point
- `types.go` - Data structures

## How to Use
Simple example of using this module.
```

### Code Comments
```go
// ArxObject is the DNA of building infrastructure.
// It represents any physical object from a campus down to a screw.
type ArxObject struct {
    // ID uniquely identifies this object using hierarchical format:
    // "arx:building:floor:room:object"
    ID string
}
```

---

## 🚀 Implementation Timeline

### Week 1: Cleanup & Organize
- [ ] Delete dead code
- [ ] Create new folder structure
- [ ] Move existing useful code
- [ ] Update import paths

### Week 2: ArxObject Core
- [ ] Define ArxObject struct
- [ ] Build repository
- [ ] Create database schema
- [ ] Write tests

### Week 3: Symbol Library
- [ ] Define symbol structure
- [ ] Create symbol sets (electrical, HVAC, etc.)
- [ ] Build pattern matcher
- [ ] Test recognition

### Week 4: Ingestion
- [ ] PDF parser
- [ ] Photo processor
- [ ] LiDAR handler
- [ ] Test with real files

### Week 5: API
- [ ] Setup Go server
- [ ] Create routes
- [ ] Add authentication
- [ ] Write API docs

### Week 6: Web UI
- [ ] Setup React/Vue
- [ ] Build viewer
- [ ] Add upload
- [ ] Test end-to-end

---

## 🎯 Success Criteria

### Code Quality
- [ ] Any engineer can understand structure in 5 minutes
- [ ] No dead code
- [ ] Clear naming conventions
- [ ] Comprehensive README files

### Functionality
- [ ] Can ingest PDF and create ArxObjects
- [ ] Can take photo of paper map
- [ ] Can view fractal zoom
- [ ] Can toggle systems on/off

### Performance
- [ ] Loads 10,000 objects smoothly
- [ ] Zoom transitions < 200ms
- [ ] API responses < 100ms

---

## 🛑 What NOT to Build (Yet)

1. **Mobile Apps** - Web first
2. **Desktop App** - Cancelled
3. **Advanced Features** - Focus on core
4. **Multiple Databases** - PostgreSQL only
5. **Microservices** - Monolith first
6. **Complex Auth** - Basic auth for now

---

## 📝 Final Notes

### Principles
1. **Simple > Complex**
2. **Working > Perfect**
3. **Clear > Clever**
4. **Documented > Assumed**

### For New Engineers
When you join this project:
1. Read this document first
2. Run `docker-compose up`
3. Check README in each folder
4. Start with arxos-core

### Questions?
If something isn't clear, it needs better documentation.
**Fix it for the next person.**

---

**This is our North Star. Build it clean, build it right.**