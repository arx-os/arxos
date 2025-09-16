# ArxOS Architecture

## Design Philosophy

ArxOS follows a **multi-level user experience** architecture where different interfaces serve different precision needs, unified by a single binary that provides all functionality through different runtime modes.

### Core Principles

1. **Multi-Level Precision**: Different interfaces serve different user needs
   - **Schematic level** (.bim.txt): Building operations and relationships
   - **Spatial level** (PostGIS): Precise coordinates for AR and field work
   - **System level** (Terminal detail): Technical specifications and tracing

2. **One Tool, Complete System**: Single binary handles everything
3. **Transparent Infrastructure**: Background services managed automatically  
4. **Text as Schematic Truth**: `.bim.txt` files are the authoritative schematic representation
5. **Git-like Workflow**: Familiar version control patterns for building data
6. **Progressive Enhancement**: Complexity only when needed

### User Experience Hierarchy

**Building Manager**: "Is there an outlet in Conference Room A?"
- Uses terminal with `.bim.txt` schematic view
- Needs general location and system relationships

**Field Technician**: "Where exactly should I mount this device?"
- Uses mobile AR with PostGIS precise coordinates  
- Needs millimeter precision for physical installation

**Systems Engineer**: "What's the power path from panel to outlet?"
- Uses terminal detail mode with system tracing
- Needs technical specifications and connection paths

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│  ┌──────────┬──────────┬──────────┬────────────────────┐  │
│  │ Terminal │  Web 3D  │Mobile AR │   Packet Radio    │  │
│  │ (ASCII)  │ (Svelte) │ (React   │  (LoRaWAN/APRS)   │  │
│  │Schematic │3D Visual │Precise AR│  Compressed      │  │
│  └──────────┴──────────┴──────────┴────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                         arx binary                          │
├─────────────────────────────────────────────────────────────┤
│                    Command Layer (Cobra)                     │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │ install  │   repo   │  import  │  query   │  serve   │ │
│  │  view    │  trace   │  export  │  search  │  watch   │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Core Services                          │
│  ┌────────────────┬────────────────┬────────────────────┐ │
│  │   Repository   │  Coordinate    │   File Watcher    │ │
│  │    Manager     │  Translation   │     Service       │ │
│  └────────────────┴────────────────┴────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Transport Layers                         │
│  ┌────────────────┬────────────────┬────────────────────┐ │
│  │   HTTP/REST    │   WebSocket    │   Packet Radio    │ │
│  │               │  (Real-time)    │  (Low-bandwidth)  │ │
│  └────────────────┴────────────────┴────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Runtime Modes                          │
│  ┌────────────────┬────────────────┬────────────────────┐ │
│  │   CLI Mode     │  Daemon Mode   │   Server Mode     │ │
│  │ (interactive) │ (background)    │    (HTTP API)     │ │
│  └────────────────┴────────────────┴────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Multi-Level Storage Layer                   │
│  ┌─────────────────────────┬─────────────────────────────┐  │
│  │   .bim.txt Files        │     PostGIS Database        │  │
│  │  (Schematic Truth)      │   (Spatial Precision)       │  │
│  │  ├─ Human readable      │  ├─ Millimeter precision    │  │
│  │  ├─ Git version control │  ├─ 3D coordinates          │  │
│  │  ├─ Grid coordinates    │  ├─ AR spatial anchors      │  │
│  │  └─ System relationships│  └─ LiDAR point clouds      │  │
│  └─────────────────────────┴─────────────────────────────┘  │
│                              ▲                              │
│                    Bidirectional Sync                       │
│                  (Coordinate Translation)                    │
└─────────────────────────────────────────────────────────────┘
```

## Runtime Modes

### 1. CLI Mode (Default)
- **Lifecycle**: Start → Execute → Exit
- **Use Case**: User commands, queries, updates
- **Example**: `arx query --status failed`

### 2. Daemon Mode
- **Lifecycle**: System service, long-running
- **Use Case**: File monitoring, auto-import
- **Management**: Handled by systemd/launchd
- **Example**: Started automatically by `arx install`

### 3. Server Mode
- **Lifecycle**: Long-running HTTP server
- **Use Case**: REST API for web/mobile clients
- **Example**: `arx serve --daemon`

## Command Structure

```
arx
├── install                    # System setup and initialization
│   ├── --with-server         # Include API server setup
│   ├── --watch <dir>         # Initial watch directories
│   └── --config <file>       # Custom configuration
│
├── repo                      # Repository management (Git-like)
│   ├── init <building>       # Initialize building repository
│   ├── status                # Show changes
│   ├── diff                  # Show detailed differences
│   ├── commit                # Commit changes
│   ├── log                   # View history
│   ├── branch                # Branch operations
│   └── merge                 # Merge branches
│
├── import <file>             # Import from various formats
│   ├── --format              # Specify format (pdf/ifc/dwg)
│   ├── --building            # Target building ID
│   └── --auto-commit         # Auto-commit after import
│
├── export <building>         # Export building data
│   ├── --format              # Output format
│   ├── --template            # Report template
│   └── --output              # Output file
│
├── query                     # Database queries
│   ├── --building            # Filter by building
│   ├── --floor               # Filter by floor
│   ├── --type                # Filter by equipment type
│   ├── --status              # Filter by status
│   └── --sql                 # Raw SQL query
│
├── watch                     # File monitoring control
│   ├── add <dir>            # Add watch directory
│   ├── remove <dir>         # Remove watch directory
│   ├── list                 # List watched directories
│   ├── pause                # Pause monitoring
│   └── resume               # Resume monitoring
│
├── serve                     # API server
│   ├── --port               # Server port (default: 8080)
│   ├── --daemon             # Run as background service
│   ├── --stop               # Stop background server
│   └── --status             # Check server status
│
└── [CRUD operations]
    ├── add <path>           # Add component
    ├── get <path>           # Get component details
    ├── update <path>        # Update component
    ├── remove <path>        # Remove component
    └── list                 # List components
```

## Multi-Level Data Architecture

### Coordinate System Design

ArxOS uses a **dual coordinate system** to serve different user needs:

#### **Grid Coordinates (.bim.txt)**
- **Purpose**: Human-readable schematic representation
- **Format**: Integer grid positions `LOCATION: (45, 30)`
- **Scale**: Configurable (e.g., 1 grid unit = 0.5 meters)
- **Use Cases**: Building operations, ASCII visualization, Git diffs
- **Precision**: Building/room level (~0.5-1 meter resolution)

#### **World Coordinates (PostGIS)**
- **Purpose**: Precise spatial positioning for AR and field work
- **Format**: Real-world 3D coordinates `(12.547, 8.291, 1.127)` meters
- **Reference**: Building origin with GPS coordinates
- **Use Cases**: AR overlay, LiDAR integration, precise installation
- **Precision**: Millimeter level

### Data Flow

#### **Import Flow**
```
PDF/IFC/DWG File
       ↓
   [Parser] ──────────────────────┐
       ↓                         │
   .bim.txt                      │
   (Grid coords)                 ▼
       ↓                    [Coordinate]
   [Validator]              [Translation]
       ↓                         │
   Git Repository                ▼
       ↓                    PostGIS DB
   [Sync Service]           (World coords)
       ↓                         │
   SQLite DB ◄──────────────────┘
   (Query cache)
```

#### **AR Edit Flow**
```
AR User Edit (3D coords)
       ↓
   PostGIS Update
       ↓
   [Coordinate Translation]
       ↓
   Significant Change? ──Yes──► .bim.txt Update
       │                        ↓
       No                   Git Commit
       ↓                        ↓
   Cache in SQLite         File Watcher Sync
```

#### **Query Flow**
```
Terminal User Query
       ↓
   Query Type?
   ├─ Overview ──► SQLite ──► .bim.txt data
   ├─ Detail ────► SQLite ──► System tracing
   └─ Spatial ───► PostGIS ─► Precise coords
```

#### **Sync Strategy**
```
.bim.txt Changes ──► File Watcher ──► PostGIS Update
                                     (Grid → World coords)

PostGIS Changes ──► Coordinate ──► .bim.txt Update
                   Translation    (if significant)
```

## Installation Process

When user runs `arx install`:

1. **Create Directory Structure**
   ```
   ~/.arxos/
   ├── config.yaml           # Configuration
   ├── arxos.db             # SQLite database
   ├── logs/                # Log files
   └── run/                 # PID files, sockets
   ```

2. **Initialize Database**
   - Create schema
   - Set up indexes
   - Initialize system tables

3. **Install File Watcher**
   - Create systemd/launchd service
   - Configure watch directories
   - Start service

4. **Optional: Install API Server**
   - Create server service
   - Configure ports/authentication
   - Start if requested

## Coordinate Translation System

### Core Translation Service

The coordinate translation service bridges between grid coordinates (.bim.txt) and world coordinates (PostGIS):

```go
type CoordinateTranslator struct {
    BuildingOrigin  GPSCoordinate    // Real-world building origin
    GridScale      float64          // Meters per grid unit
    GridOrigin     Point2D          // Grid coordinate (0,0) position
    FloorHeight    float64          // Meters between floors
    Orientation    float64          // Building rotation (degrees from north)
}

// Convert grid coordinates to real-world 3D coordinates
func (ct *CoordinateTranslator) GridToWorld(
    gridX, gridY int, 
    floor int, 
    room string,
) (worldX, worldY, worldZ float64) {
    // Apply grid scaling
    worldX = float64(gridX) * ct.GridScale
    worldY = float64(gridY) * ct.GridScale
    worldZ = float64(floor) * ct.FloorHeight
    
    // Apply building rotation and origin offset
    // ... rotation matrix math
    // ... GPS coordinate transformation
    
    return worldX, worldY, worldZ
}

// Determine if AR edit requires .bim.txt update
func (ct *CoordinateTranslator) IsSignificantChange(
    oldWorld, newWorld Point3D,
) bool {
    // Different room?
    if ct.GetRoom(oldWorld) != ct.GetRoom(newWorld) {
        return true
    }
    
    // Movement > 1 grid unit?
    gridDistance := ct.WorldDistanceToGridUnits(
        oldWorld.DistanceTo(newWorld)
    )
    return gridDistance >= 1.0
}
```

### AR Integration Architecture

```go
// AR edit handler
func HandleAREdit(equipmentID string, newWorldCoords Point3D) error {
    // 1. Update PostGIS with precise coordinates
    err := spatialDB.UpdateEquipmentPosition(equipmentID, newWorldCoords)
    if err != nil {
        return err
    }
    
    // 2. Check if .bim.txt update needed
    oldCoords := getOldCoordinates(equipmentID)
    if translator.IsSignificantChange(oldCoords, newWorldCoords) {
        // 3. Convert to grid coordinates
        gridCoords := translator.WorldToGrid(newWorldCoords)
        
        // 4. Update .bim.txt file
        err = updateBIMFile(equipmentID, gridCoords)
        if err != nil {
            return err
        }
        
        // 5. Commit change
        return gitCommit(fmt.Sprintf("AR edit: moved %s", equipmentID))
    }
    
    return nil
}
```

### LiDAR Integration Pipeline

```go
// LiDAR processing workflow
func ProcessLiDARScan(pointCloud PointCloud, buildingID string) error {
    // 1. Align point cloud to building coordinate system
    alignedCloud := alignToBuilding(pointCloud, buildingID)
    
    // 2. Extract equipment positions (semi-automated)
    detectedObjects := detectEquipment(alignedCloud)
    
    // 3. Match detected objects to existing equipment
    for _, obj := range detectedObjects {
        matches := findPotentialMatches(obj, buildingID)
        
        if len(matches) == 1 {
            // Automatic match - update position
            updateEquipmentFromLiDAR(matches[0], obj.Position)
        } else {
            // Ambiguous - require user input
            queueForManualReview(obj, matches)
        }
    }
    
    return nil
}
```

## Interface Layers

### 1. Terminal Interface (Current) - Building Operations
- **Target Users**: Building managers, systems engineers, facility operators
- **Technology**: Native Go with ASCII art rendering
- **Data Source**: Primarily .bim.txt with PostGIS for spatial queries
- **Features**: 
  - Multi-level viewing (overview, detail, spatial)
  - System tracing and connection mapping
  - ASCII floor plans and equipment visualization
  - Git-like version control operations
- **Status**: Core functionality implemented

### 2. Mobile AR Interface (Future) - Field Operations  
- **Target Users**: Field technicians, installers, maintenance staff
- **Technology**: React Native + ARKit/ARCore
- **Data Source**: PostGIS spatial database with millimeter precision
- **Architecture**: Offline-first with spatial anchor persistence
- **Features**:
  - Precise AR equipment overlay
  - LiDAR scanning integration
  - Spatial anchoring across sessions
  - Work order management with voice/photo notes
  - Offline sync for remote locations
- **Status**: Foundation established in `/mobile`

### 3. Web 3D Interface (Future) - System Analysis
- **Target Users**: Engineers, architects, system designers  
- **Technology**: Svelte + Three.js + D3.js
- **Data Source**: Combined .bim.txt and PostGIS for comprehensive visualization
- **Architecture**: SPA with WebSocket real-time updates
- **Features**:
  - Interactive 3D building models
  - Multi-level zoom (building → system → component)
  - Real-time equipment status visualization
  - Energy flow and system relationship mapping
  - Historical data timeline and analysis
- **Status**: Foundation established in `/web`

### 4. Packet Radio Transport (Experimental) - Emergency Operations
- **Target Users**: Emergency responders, remote facility operators
- **Technology**: LoRaWAN, APRS, custom protocols
- **Data Source**: Compressed building data optimized for bandwidth constraints
- **Architecture**: Compressed binary protocol with automatic retransmission
- **Features**:
  - 92% message compression for radio efficiency
  - Context-based data optimization
  - Battery-efficient operation modes
  - Automatic retry and error correction
- **Status**: Core protocol implemented in `/internal/transport/radio`

## Code Organization

```go
cmd/arx/
├── main.go                   # Entry point, mode detection
├── cmd_install.go            # Installation command
├── cmd_repo.go              # Repository operations
├── cmd_import.go            # Import operations
├── cmd_export.go            # Export operations
├── cmd_query.go             # Query operations
├── cmd_watch.go             # Watch control
├── cmd_serve.go             # Server mode
└── cmd_crud.go              # CRUD operations

internal/
├── core/                    # Core business logic
│   ├── building.go         # Building management
│   ├── equipment.go        # Equipment operations
│   ├── addressing.go       # Universal addressing system
│   └── validation.go       # Data validation
│
├── runtime/                # Runtime modes
│   ├── cli.go             # CLI mode execution
│   ├── daemon.go          # Daemon mode (file watcher)
│   └── server.go          # HTTP server mode
│
├── storage/               # Storage implementations
│   ├── filesystem.go      # .bim.txt file operations
│   ├── database.go        # SQLite operations
│   ├── repository.go      # Git operations
│   ├── git_integration.go # Git operations for buildings
│   └── sync.go           # Sync between storage types
│
├── transport/            # Transport layers
│   ├── http.go          # HTTP/REST transport
│   ├── websocket.go     # WebSocket for real-time
│   └── radio/           # Packet radio transport
│       ├── transport.go # Core radio protocol
│       ├── lorawan.go   # LoRaWAN implementation
│       └── compression.go # Message compression
│
├── rendering/           # Visualization engines
│   ├── ascii.go        # Terminal ASCII art
│   ├── layered_renderer.go # Layered rendering
│   └── svg_renderer.go # SVG output
│
├── services/             # Shared services
│   ├── watcher.go        # File system monitoring
│   ├── importer/         # Import from various formats
│   │   ├── pdf.go
│   │   ├── ifc.go
│   │   └── dwg.go
│   ├── exporter/         # Export to various formats
│   └── validator.go      # BIM validation
│
├── api/                  # REST API (server mode)
│   ├── server.go        # HTTP server setup
│   ├── routes.go        # Route definitions
│   ├── handlers/        # Request handlers
│   └── middleware/      # Auth, logging, etc.
│
└── common/              # Shared utilities
    ├── config.go        # Configuration management
    ├── logger.go        # Logging
    └── errors.go        # Error handling

web/                     # Web 3D interface (Svelte)
├── src/
│   ├── components/     # Svelte components
│   ├── lib/           # Client libraries
│   └── stores/        # State management
└── package.json

mobile/                  # Mobile AR app (React Native)
├── src/
│   ├── screens/       # App screens
│   ├── components/    # React components
│   └── services/      # API and AR services
├── ios/               # iOS-specific code
└── android/           # Android-specific code
```

## Process Management

### Background Services

ArxOS manages background processes through OS service managers:

**Linux (systemd)**:
```ini
[Unit]
Description=ArxOS File Watcher
After=network.target

[Service]
Type=simple
User=%USER%
ExecStart=/usr/local/bin/arx watch --daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**macOS (launchd)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.arxos.watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/arx</string>
        <string>watch</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

### Inter-Process Communication

Services communicate via:
- **Unix sockets**: For local IPC (`~/.arxos/run/arxos.sock`)
- **PID files**: For process management (`~/.arxos/run/watcher.pid`)
- **SQLite**: Shared state with proper locking
- **Filesystem events**: inotify/fsevents for file changes

## Configuration

System configuration in `~/.arxos/config.yaml`:

```yaml
# System paths
paths:
  database: ~/.arxos/arxos.db
  buildings: ./buildings
  logs: ~/.arxos/logs

# File watcher
watcher:
  enabled: true
  directories:
    - ./buildings
    - /shared/bim-files
  patterns:
    - "*.bim.txt"
    - "*.pdf"
  auto_import: true
  scan_interval: 5s

# Database
database:
  type: sqlite
  backup:
    enabled: true
    interval: 24h
    keep: 7

# API Server
server:
  enabled: false
  port: 8080
  host: localhost
  auth:
    enabled: false
    jwt_secret: ${JWT_SECRET}

# Logging
logging:
  level: info
  file: ~/.arxos/logs/arxos.log
  max_size: 100M
  max_age: 30d

# Import/Export
import:
  pdf:
    ocr: true
    dpi: 300
  validation:
    strict: true
```

## Security Considerations

### File System Security
- Config files: 600 permissions
- Database: 644 permissions
- Sockets: 600 permissions
- Logs: 644 permissions

### API Security (when enabled)
- JWT authentication
- Rate limiting
- CORS configuration
- TLS support

### Data Security
- No credentials in .bim.txt files
- Sensitive data in config only
- Audit logging for changes

## Performance Targets

- **Installation**: < 5 seconds
- **Import PDF**: < 10 seconds for 50-page document
- **Query response**: < 100ms for 10,000 equipment items
- **File watch latency**: < 1 second detection
- **API response**: < 50ms for standard queries
- **Database size**: ~1MB per 1,000 equipment items

## Future Enhancements

### Phase 1 (Current - Complete)
- ✅ Single binary architecture
- ✅ File watching and auto-sync
- ✅ Import/export (PDF, BIM formats)
- ✅ SQLite storage with Git versioning
- ✅ ASCII art rendering
- ✅ Repository management (Git-like workflow)

### Phase 2 (In Progress)
- 🚧 Web 3D visualization (Svelte + Three.js)
- 🚧 Mobile AR application (React Native)
- 🚧 Packet radio transport (LoRaWAN/APRS)
- ⬜ Plugin system for custom importers
- ⬜ GraphQL API option
- ⬜ Distributed synchronization

### Phase 3 (Future Vision)
- ⬜ Machine learning for predictive maintenance
- ⬜ Advanced AR/VR with spatial computing
- ⬜ Blockchain audit trail for compliance
- ⬜ IoT device direct integration
- ⬜ Voice control and AI assistant
- ⬜ Digital twin simulation engine

## Troubleshooting

### Common Issues

**Watcher not starting**:
```bash
arx watch list              # Check configuration
arx status                  # Check system status
systemctl status arxos      # Check service status
```

**Database locked**:
```bash
arx status --check-locks    # Check for locks
arx repair                  # Repair database
```

**Import failures**:
```bash
arx validate <file>         # Check file format
arx import --verbose <file> # Detailed error output
```

## Building Ingestion & Progressive Enhancement

### Overview

ArxOS supports multiple ingestion methods, each providing different types and precision levels of data. The system intelligently merges these inputs to create a progressively refined building model that combines semantic completeness with spatial accuracy.

### Ingestion Methods & Data Characteristics

#### 1. PDF/HEIC Floor Plans
**Input Characteristics:**
- 2D schematic layouts
- Room boundaries and labels
- Approximate equipment locations
- Scale information

**Data Population:**
```
.bim.txt:  ✅ Complete (rooms, zones, equipment, grid positions)
PostGIS:   ⚠️  Estimated (interpolated from scale, ±1-2 meter accuracy)
Confidence: LOW (requires field verification)
```

**Processing Pipeline:**
```go
func ProcessPDFImport(pdf PDFDocument) (*Building, error) {
    // 1. OCR and pattern recognition
    layout := extractFloorPlan(pdf)

    // 2. Scale detection
    scale := detectScale(layout) // e.g., 1:100

    // 3. Grid mapping
    gridMap := mapToGrid(layout, scale)

    // 4. Equipment detection
    equipment := detectEquipment(layout) // outlets, switches, etc.

    // 5. Create .bim.txt with grid coordinates
    bimFile := generateBIMFile(gridMap, equipment)

    // 6. Estimate world coordinates for PostGIS
    worldCoords := estimateWorldCoordinates(gridMap, scale)
    // Mark as "estimated" confidence

    return building, nil
}
```

#### 2. IFC (Industry Foundation Classes)
**Input Characteristics:**
- 3D BIM model with relative precision
- Complete equipment metadata
- System relationships and connections
- Material properties

**Data Population:**
```
.bim.txt:  ✅ Complete (full semantic model)
PostGIS:   🔶 Good (needs real-world alignment)
Confidence: MEDIUM (requires GPS/survey alignment)
```

**Processing Pipeline:**
```go
func ProcessIFCImport(ifc IFCModel) (*Building, error) {
    // 1. Parse IFC structure
    spaces := extractSpaces(ifc)
    equipment := extractEquipment(ifc)
    systems := extractSystems(ifc)

    // 2. Convert to ArxOS addressing
    addressing := mapToUniversalAddressing(spaces)

    // 3. Extract relative 3D coordinates
    relativeCoords := extractCoordinates(ifc)

    // 4. Generate complete .bim.txt
    bimFile := generateFromIFC(spaces, equipment, systems)

    // 5. Store in PostGIS with alignment pending
    // Requires GPS anchor or survey point for real-world positioning

    return building, nil
}
```

#### 3. LiDAR Point Cloud
**Input Characteristics:**
- Ultra-precise 3D spatial data
- No semantic labels
- Physical geometry only
- Millimeter accuracy

**Data Population:**
```
.bim.txt:  ❌ Minimal (only detected spaces/structures)
PostGIS:   ✅ Perfect (millimeter precision)
Confidence: HIGH (actual reality capture)
```

**Processing Pipeline:**
```go
func ProcessLiDARScan(pointCloud PointCloud) (*PartialBuilding, error) {
    // 1. Point cloud alignment
    aligned := alignToCoordinateSystem(pointCloud)

    // 2. Space detection (rooms, walls)
    spaces := detectSpaces(aligned)

    // 3. Object detection (equipment shapes)
    objects := detectObjects(aligned)
    // Note: These are unlabeled geometries

    // 4. Store precise coordinates in PostGIS
    storeSpatialData(objects, spaces)

    // 5. Generate minimal .bim.txt structure
    // Requires human labeling for semantics

    return partialBuilding, nil
}
```

### Progressive Enhancement Strategy

ArxOS handles partial scans and mixed-precision data through a progressive refinement workflow:

#### Coverage Tracking

```go
type CoverageMap struct {
    BuildingID   string
    TotalArea    float64
    ScannedAreas []ScannedRegion
}

type ScannedRegion struct {
    Area         Polygon
    ScanDate     time.Time
    ScanType     string // "lidar", "photogrammetry", "manual"
    Confidence   float64
    PointDensity float64 // points per square meter
}

func (c *CoverageMap) GetCoveragePercentage() float64 {
    scannedArea := c.calculateScannedArea()
    return (scannedArea / c.TotalArea) * 100
}

func (c *CoverageMap) GetRegionConfidence(location Point) ConfidenceLevel {
    region := c.findRegion(location)
    if region == nil {
        return CONFIDENCE_ESTIMATED // PDF only
    }

    switch {
    case region.ScanType == "lidar" && region.PointDensity > 1000:
        return CONFIDENCE_HIGH
    case region.ScanType == "lidar":
        return CONFIDENCE_MEDIUM
    default:
        return CONFIDENCE_LOW
    }
}
```

#### Partial Scan Integration

When a partial LiDAR scan is imported, the system performs intelligent matching with existing data:

```go
type PartialScanMerger struct {
    ExistingBuilding *Building
    NewScan         *PointCloud
    CoverageMap     *CoverageMap
}

func (m *PartialScanMerger) MergePartialScan() (*MergeResult, error) {
    // 1. Detect scan overlap with existing model
    overlap := m.detectOverlap()

    // 2. Align coordinate systems
    alignment := m.findBestAlignment(overlap)

    // 3. For each detected object in scan
    matches := []ObjectMatch{}
    for _, detectedObj := range m.NewScan.DetectedObjects {
        // Find potential matches in existing model
        candidates := m.findNearbyCandidates(detectedObj, alignment)

        match := ObjectMatch{
            DetectedObject: detectedObj,
            Candidates:     candidates,
            Confidence:     m.calculateMatchConfidence(detectedObj, candidates),
        }
        matches = append(matches, match)
    }

    // 4. Process matches based on confidence
    for _, match := range matches {
        switch match.Confidence {
        case HIGH_CONFIDENCE:
            // Automatically update position
            m.updateEquipmentPosition(match)

        case MEDIUM_CONFIDENCE:
            // Queue for user confirmation
            m.queueForReview(match)

        case LOW_CONFIDENCE:
            // Possible new equipment or significant change
            m.flagForInvestigation(match)
        }
    }

    // 5. Update coverage map
    m.CoverageMap.AddScannedRegion(overlap.Area, "lidar", time.Now())

    return &MergeResult{
        UpdatedEquipment: len(matches),
        CoverageIncrease: overlap.Area,
        RequiresReview:   m.getPendingReviews(),
    }, nil
}
```

### Smart Merge Algorithm

The core intelligence for reconciling different data sources:

```go
type SmartMerger struct {
    Building     *Building
    DataSources  []DataSource
    Strategies   map[string]MergeStrategy
}

type DataSource struct {
    Type       string    // "pdf", "ifc", "lidar", "ar_edit"
    Timestamp  time.Time
    Confidence float64
    Coverage   *Polygon  // spatial extent
}

func (sm *SmartMerger) Merge() error {
    // 1. Sort sources by confidence and timestamp
    sort.Slice(sm.DataSources, func(i, j int) bool {
        if sm.DataSources[i].Confidence != sm.DataSources[j].Confidence {
            return sm.DataSources[i].Confidence > sm.DataSources[j].Confidence
        }
        return sm.DataSources[i].Timestamp.After(sm.DataSources[j].Timestamp)
    })

    // 2. Build composite model
    for _, source := range sm.DataSources {
        strategy := sm.Strategies[source.Type]

        if err := strategy.Apply(sm.Building, source); err != nil {
            // Handle conflicts
            conflict := detectConflict(err)
            resolution := resolveConflict(conflict, source)

            if resolution.RequiresHuman {
                queueForHumanReview(conflict)
            } else {
                applyResolution(resolution)
            }
        }
    }

    // 3. Validate merged model
    return sm.validateConsistency()
}

// Conflict Resolution Strategy
type ConflictResolver struct {
    Rules []ResolutionRule
}

type ResolutionRule struct {
    Condition func(Conflict) bool
    Action    func(Conflict) Resolution
}

var defaultRules = []ResolutionRule{
    {
        // LiDAR always wins for position
        Condition: func(c Conflict) bool {
            return c.Type == "position" && c.NewSource.Type == "lidar"
        },
        Action: func(c Conflict) Resolution {
            return Resolution{
                UseNew: true,
                UpdateConfidence: CONFIDENCE_HIGH,
            }
        },
    },
    {
        // Newer AR edits override older PDF estimates
        Condition: func(c Conflict) bool {
            return c.OldSource.Type == "pdf" && c.NewSource.Type == "ar_edit"
        },
        Action: func(c Conflict) Resolution {
            return Resolution{
                UseNew: true,
                UpdateConfidence: CONFIDENCE_MEDIUM,
            }
        },
    },
    {
        // Semantic data from IFC preferred over detected objects
        Condition: func(c Conflict) bool {
            return c.Type == "semantic" && c.NewSource.Type == "ifc"
        },
        Action: func(c Conflict) Resolution {
            return Resolution{
                UseNew: true,
                PreserveSpatial: true,
            }
        },
    },
}
```

### Confidence Tracking

Every piece of data in ArxOS carries confidence metadata:

```go
type EquipmentRecord struct {
    ID       string
    Path     string
    Location Point3D

    // Confidence tracking
    PositionConfidence ConfidenceLevel
    PositionSource     string // "pdf", "ifc", "lidar", "ar_verified"
    PositionUpdated    time.Time

    SemanticConfidence ConfidenceLevel
    SemanticSource     string
    SemanticUpdated    time.Time

    LastFieldVerified  *time.Time
}

type ConfidenceLevel int

const (
    CONFIDENCE_ESTIMATED ConfidenceLevel = iota // PDF/IFC without verification
    CONFIDENCE_LOW                              // Automated detection
    CONFIDENCE_MEDIUM                           // Partial verification
    CONFIDENCE_HIGH                             // LiDAR or AR verified
)

// Query by confidence
func QueryWithConfidence(building string, minConfidence ConfidenceLevel) []Equipment {
    query := `
        SELECT * FROM equipment
        WHERE building_id = ?
        AND position_confidence >= ?
        ORDER BY position_confidence DESC
    `
    return db.Query(query, building, minConfidence)
}
```

### Progressive Enhancement Workflow

A typical progressive enhancement lifecycle:

```bash
# Stage 1: Initial PDF import (Day 1)
arx import floor_plans.pdf --building ARXOS-001
> Created: 500 equipment items (confidence: ESTIMATED)
> Coverage: 100% semantic, 0% verified

# Stage 2: IFC model import (Day 5)
arx import design.ifc --building ARXOS-001 --merge
> Updated: 500 equipment items with metadata
> Added: System relationships
> Coverage: 100% semantic, 0% verified

# Stage 3: Partial LiDAR scan - Lobby (Day 10)
arx scan import lobby_scan.ply --building ARXOS-001 --area "Floor:1/Zone:Lobby"
> Matched: 15 equipment items (confidence: HIGH)
> Unknown: 3 objects (pending review)
> Coverage: 100% semantic, 5% verified

# Stage 4: Technician AR verification (Day 15-30)
# Technicians verify equipment during routine work
> Progressive updates via AR app
> Coverage: 100% semantic, 35% verified

# Stage 5: Complete LiDAR scan - Critical areas (Day 60)
arx scan import mechanical_rooms.ply --building ARXOS-001
> Matched: 127 equipment items (confidence: HIGH)
> Coverage: 100% semantic, 52% verified

# Query coverage status
arx coverage --building ARXOS-001 --detail
> Floor 1:
>   Semantic: 100% (Source: PDF+IFC)
>   Verified: 45% (LiDAR: 30%, AR: 15%)
>   Last scan: 2024-03-15
> Floor 2:
>   Semantic: 100% (Source: PDF+IFC)
>   Verified: 12% (AR: 12%)
>   Last scan: Never
```

### Implementation Status

- ✅ PDF import with grid mapping
- ✅ IFC import with semantic extraction
- 🚧 LiDAR point cloud processing
- 🚧 Progressive merge algorithm
- ⬜ Confidence tracking system
- ⬜ Coverage visualization
- ⬜ Automated object matching ML
- ⬜ Conflict resolution UI

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

Key points for contributors:
- All functionality in single binary
- Commands use Cobra framework
- Services must support all three runtime modes
- Tests required for new commands
- Documentation updates required