# ArxOS Architecture

## Design Philosophy

ArxOS follows a **PostGIS-centric professional BIM integration** architecture where PostGIS serves as the single source of truth for all spatial data, with seamless integration into existing professional BIM workflows through universal IFC compatibility.

### Core Principles

1. **PostGIS as Spatial Truth**: All spatial data flows into PostGIS database for authoritative storage and spatial operations
   - **PostGIS Database**: Millimeter-precision coordinates, spatial queries, single source of truth
   - **Derived Outputs**: .bim.txt, IFC exports, PDF reports generated from PostGIS data
   - **Professional Integration**: Direct compatibility with any IFC-exporting BIM tool

2. **Universal IFC Compatibility**: Professional BIM tools integrate via standard IFC files
   - **No Tool-Specific Code**: Works with Revit, AutoCAD, ArchiCAD, Tekla, etc.
   - **Standard Workflows**: Leverages existing professional IFC export practices
   - **Zero Disruption**: Professionals continue using preferred tools

3. **Professional Workflow Integration**: Daemon-based automatic synchronization
   - **IFC File Monitoring**: Automatic detection and processing of BIM tool exports
   - **Team Collaboration**: Real-time updates across all interfaces
   - **Version Control**: Automatic Git commits for building changes

4. **Multi-Level User Experience**: Different interfaces serve different precision needs
   - **Schematic level** (.bim.txt): Human-readable building operations and relationships
   - **Spatial level** (PostGIS): Precise coordinates for AR and field work
   - **Professional level** (IFC): Full BIM tool integration and compatibility

5. **One Tool, Complete System**: Single binary handles everything
6. **Transparent Infrastructure**: Background services managed automatically

### User Experience Hierarchy

**BIM Professional**: "I need my Revit changes to automatically update the team"
- Exports IFC from preferred BIM tool (Revit, AutoCAD, ArchiCAD, etc.)
- ArxOS daemon automatically processes IFC and updates PostGIS
- Team sees changes in real-time across all interfaces

**Building Manager**: "Is there an outlet in Conference Room A?"
- Uses terminal with `.bim.txt` schematic view (generated from PostGIS)
- Needs general location and system relationships
- Gets human-readable representation of precise spatial data

**Field Technician**: "Where exactly should I mount this device?"
- Uses mobile AR with direct PostGIS spatial queries
- Needs millimeter precision for physical installation
- Real-time updates from BIM professional changes

**Systems Engineer**: "What's the power path from panel to outlet?"
- Uses terminal detail mode with PostGIS spatial tracing
- Needs technical specifications and connection paths
- Queries precise spatial relationships and system connections

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Professional BIM Tools                       │
│  ┌──────────┬──────────┬──────────┬────────────────────┐  │
│  │  Revit   │ AutoCAD  │ArchiCAD  │    Any IFC Tool    │  │
│  │          │          │  Tekla   │   (Universal)      │  │
│  └──────────┴──────────┴──────────┴────────────────────┘  │
│                              │                             │
│                       Standard IFC Export                  │
│                              ▼                             │
├─────────────────────────────────────────────────────────────┤
│                       ArxOS Daemon                          │
│                   (IFC File Monitoring)                     │
│  ┌─────────────────┬─────────────────┬─────────────────┐  │
│  │ File Detection  │ IFC Processing  │ Auto Generation │  │
│  │ & Validation    │ & PostGIS Import│ (.bim.txt/Git)  │  │
│  └─────────────────┴─────────────────┴─────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      PostGIS Database                       │
│                   (Single Source of Truth)                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ├─ Millimeter precision 3D coordinates             │  │
│  │ ├─ Spatial indexing and operations                 │  │
│  │ ├─ Equipment positioning and relationships         │  │
│  │ ├─ Building geometry and spatial queries           │  │
│  │ ├─ AR spatial anchors and mobile integration       │  │
│  │ └─ LiDAR point clouds and reality capture          │  │
│  └─────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                         arx binary                          │
│                    Command Layer (Cobra)                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │ install  │  daemon  │  import  │  query   │  export  │ │
│  │   repo   │  trace   │   serve  │  search  │   watch  │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      User Interfaces                        │
│  ┌──────────┬──────────┬──────────┬────────────────────┐  │
│  │ Terminal │  Web 3D  │Mobile AR │   Packet Radio    │  │
│  │ (ASCII)  │ (Svelte) │ (React   │  (LoRaWAN/APRS)   │  │
│  │Schematic │3D Visual │Precise AR│  Compressed       │  │
│  └──────────┴──────────┴──────────┴────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Derived Outputs                        │
│  ┌─────────────┬─────────────┬─────────────┬───────────┐  │
│  │ .bim.txt    │ IFC Export  │ PDF Plans   │ CSV/JSON  │  │
│  │(Git/Human)  │(BIM Tools)  │(Reports)    │(Analysis) │  │
│  └─────────────┴─────────────┴─────────────┴───────────┘  │
│                              ▲                             │
│                    One-Way Generation                       │
│                   (PostGIS → Formats)                      │
└─────────────────────────────────────────────────────────────┘
```

## Runtime Modes

### 1. CLI Mode (Default)
- **Lifecycle**: Start → Execute → Exit
- **Use Case**: User commands, queries, updates
- **Example**: `arx query --status failed`

### 2. Daemon Mode (Professional Integration)
- **Lifecycle**: System service, long-running
- **Use Case**: IFC file monitoring, automatic PostGIS import, team collaboration
- **Management**: Handled by systemd/launchd
- **Professional Focus**: `arx install --professional --with-daemon`
- **Key Features**: 
  - Monitors IFC exports from any BIM tool
  - Automatic PostGIS database updates
  - Real-time .bim.txt generation for Git
  - Team notification and collaboration

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
├── import <file>             # Import to PostGIS from various formats
│   ├── --format              # Specify format (pdf/ifc/lidar)
│   ├── --building            # Target building ID
│   └── --confidence          # Set confidence level for import
│
├── export <building>         # Export from PostGIS to various formats
│   ├── --format              # Output format (ifc/bim/pdf/csv)
│   ├── --precision           # Precision level (full/schematic)
│   ├── --template            # Report template
│   └── --output              # Output file
│
├── query                     # PostGIS spatial database queries
│   ├── --building            # Filter by building
│   ├── --floor               # Filter by floor
│   ├── --type                # Filter by equipment type
│   ├── --status              # Filter by status
│   ├── --spatial             # Spatial queries (within/near/contains)
│   └── --sql                 # Raw PostGIS spatial SQL
│
├── daemon                    # Professional BIM integration
│   ├── install --professional # Install for BIM professionals
│   ├── watch --ifc <pattern> # Monitor IFC files
│   ├── status --integrations # Show active BIM tool integrations
│   ├── start                 # Start daemon service
│   └── stop                  # Stop daemon service
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

## PostGIS-Centric Data Architecture

### Single Source of Truth Design

ArxOS uses **PostGIS as the authoritative spatial database** with derived outputs for different user needs:

#### **PostGIS Database (Source of Truth)**
- **Purpose**: Authoritative storage for all spatial data and relationships
- **Format**: 3D coordinates with full precision `POINT Z (12.547 8.291 1.127)`
- **Reference**: Real-world coordinates with GPS building origin
- **Use Cases**: AR overlay, LiDAR integration, precise installation, spatial queries
- **Precision**: Millimeter level with spatial indexing
- **Operations**: ST_Distance, ST_Contains, ST_Intersects, ST_Buffer

#### **Grid Coordinates (.bim.txt) - Derived**
- **Purpose**: Human-readable schematic representation generated from PostGIS
- **Format**: Integer grid positions `LOCATION: (45, 30)` for ASCII visualization
- **Scale**: Configurable conversion from PostGIS coordinates
- **Use Cases**: Building operations, ASCII visualization, Git diffs, team collaboration
- **Precision**: Building/room level (~0.5-1 meter resolution)
- **Generation**: Automatic from PostGIS data using spatial clustering

#### **Professional Coordinates (IFC) - Derived**
- **Purpose**: Full-precision export for professional BIM tool integration
- **Format**: Standard IFC coordinate system with millimeter precision
- **Reference**: Direct PostGIS coordinate export with proper coordinate system transformation
- **Use Cases**: BIM tool integration, professional workflows, design coordination
- **Precision**: Full millimeter precision maintained from PostGIS

### Data Flow

#### **Professional BIM Integration Flow**
```
BIM Professional (Revit/AutoCAD/ArchiCAD/etc.)
       ↓
   Standard IFC Export
       ↓
   ArxOS Daemon Detection
       ↓
   IFC Parser → PostGIS Import
       ↓
   PostGIS Database (Source of Truth)
       ↓
   Automatic Derived Output Generation
   ├─ .bim.txt (Git/Human readable)
   ├─ Team Notifications
   └─ Mobile/Web Interface Updates
```

#### **Manual Import Flow**
```
PDF/IFC/LiDAR File
       ↓
   arx import command
       ↓
   Format-Specific Parser
       ↓
   Direct PostGIS Import
   (with confidence tracking)
       ↓
   Optional: Generate .bim.txt
```

#### **Bidirectional CLI Control Flow**
```
Terminal CLI Commands ←→ PostGIS Database ←→ Mobile AR
     ↓                       ↓                ↓
Professional Tools      .bim.txt         IFC Export
   (IFC Import)        (derived view)    (full precision)

Examples:
arx update OUTLET_02 --location "12.547,8.291,1.127" → PostGIS
arx move HVAC_01 --by "0.05,0,0" → PostGIS → Mobile AR sees change
arx add /3/A/301/E/OUTLET_03 --location "x,y,z" → PostGIS → .bim.txt regen
```

#### **Query Flow (PostGIS-Powered)**
```
Terminal/Web/Mobile Query
       ↓
   PostGIS Spatial Database
   (ST_Distance, ST_Contains, ST_Within, etc.)
       ↓
   Real-time Spatial Results
   (millimeter precision + relationships)

Examples:
arx query --near "12.5,8.3,1.1" --radius 2.0  → ST_DWithin query
arx query --floor 3 --contains "room_polygon"  → ST_Contains query
```

#### **Export Flow (Multi-Precision)**
```
PostGIS Database (Source of Truth)
       ↓
   Export Command
   ├─ IFC Export (full millimeter precision)
   ├─ .bim.txt (grid coordinates for humans)
   ├─ PDF (floor plans with equipment positions)
   └─ CSV/JSON (analysis data with coordinates)

Examples:
arx export --format ifc --precision full      → All PostGIS coordinates
arx export --format bim --for-git            → Grid representation
```

## Professional BIM Integration

### Target Professional Workflow

```
Day-to-Day BIM Professional Workflow:
1. Work in preferred BIM tool (Revit, AutoCAD, ArchiCAD, etc.)
2. Export IFC file (standard professional practice)
3. ArxOS daemon automatically detects and processes IFC
4. PostGIS database updated with precise spatial data
5. Team collaboration files (.bim.txt) automatically generated
6. Field teams receive real-time updates via mobile AR
7. Project managers see changes in terminal/web interface
```

### Professional Value Proposition

- **Zero Workflow Disruption**: Continue using preferred BIM tools
- **Universal Compatibility**: Works with any BIM tool that exports IFC
- **Automatic Team Sync**: No manual steps for collaboration
- **Precision Maintained**: Full coordinate accuracy preserved
- **Version Control**: Building changes automatically tracked in Git
- **Real-time Updates**: Changes propagate to all team interfaces within minutes

### Professional Installation

#### Standard Installation
```bash
arx install --professional --with-daemon
```

#### Configuration for BIM Professionals
```bash
# Set up IFC monitoring
arx daemon watch --ifc "C:\BIM_Projects\*.ifc"
arx daemon watch --ifc "C:\Revit_Exports\*.ifc"

# Configure automatic exports
arx daemon config --auto-export bim,pdf
arx daemon config --git-auto-commit true

# Start professional daemon
arx daemon start --professional
```

#### CLI Spatial Control Examples
```bash
# Terminal users have full PostGIS control
arx update /3/A/301/E/OUTLET_02 --location "12.547,8.291,1.127"
arx move /3/A/301/E/OUTLET_02 --by "0.05,0,0"  # Move 5cm east
arx add /3/A/301/E/OUTLET_03 --location "12.6,8.3,1.1" --type "outlet"

# Spatial queries with PostGIS precision
arx query --near "12.5,8.3,1.1" --radius 2.0        # Within 2 meters
arx query --floor 3 --contains "room_boundaries"     # Spatial containment
arx query --building ARXOS-001 --spatial "ST_Distance(geom, point) < 5"

# Changes immediately available to all interfaces:
# - Mobile AR: Shows new precise position
# - IFC Export: Contains updated coordinates  
# - Web Interface: Queries return new position
# - .bim.txt: May show change if grid-significant
```

## Installation Process

### Standard Installation: `arx install`

1. **Create Directory Structure**
   ```
   ~/.arxos/
   ├── config.yaml           # Configuration
   ├── arxos.db             # SQLite database (fallback)
   ├── postgis.conf          # PostGIS connection config
   ├── logs/                # Log files
   └── run/                 # PID files, sockets
   ```

2. **Initialize Databases**
   - Set up PostGIS spatial database (primary)
   - Create SQLite fallback database
   - Run spatial migrations and indexing
   - Initialize system tables

3. **Optional: Install Professional Daemon**
   - Create systemd/launchd service for IFC monitoring
   - Configure IFC file watching patterns
   - Set up automatic export generation
   - Start professional integration service

4. **Optional: Install API Server**
   - Create server service for web/mobile clients
   - Configure ports/authentication
   - Start if requested

## PostGIS Spatial System

### PostGIS as Single Source of Truth

All spatial operations center around PostGIS database with standard spatial functions:

```go
type PostGISSpatialDB struct {
    db *sql.DB
    buildingOrigin  GPSCoordinate
    coordinateSystem string // EPSG:4326, etc.
}

// Store equipment with precise spatial coordinates
func (p *PostGISSpatialDB) StoreEquipment(equipment Equipment, coords Point3D) error {
    query := `
        INSERT INTO equipment (id, name, type, geom, building_id)
        VALUES ($1, $2, $3, ST_GeomFromText('POINT Z(%f %f %f)', 4326), $4)
    `
    _, err := p.db.Exec(query, equipment.ID, equipment.Name, equipment.Type, 
                       coords.X, coords.Y, coords.Z, equipment.BuildingID)
    return err
}

// Spatial proximity query using PostGIS
func (p *PostGISSpatialDB) FindNearbyEquipment(center Point3D, radiusMeters float64) ([]Equipment, error) {
    query := `
        SELECT id, name, type, ST_X(geom), ST_Y(geom), ST_Z(geom)
        FROM equipment
        WHERE ST_DWithin(geom, ST_GeomFromText('POINT Z(%f %f %f)', 4326), %f)
        ORDER BY ST_Distance(geom, ST_GeomFromText('POINT Z(%f %f %f)', 4326))
    `
    // Execute spatial query with PostGIS functions
    return p.executeEquipmentQuery(query, center.X, center.Y, center.Z, radiusMeters)
}
```

### Simplified Display Coordinate Generation

Simple one-way conversion from PostGIS to grid coordinates for human display:

```go
// Generate grid coordinates for .bim.txt display from PostGIS data
func (p *PostGISSpatialDB) GenerateGridCoordinates(buildingID string, gridScale float64) ([]GridEquipment, error) {
    query := `
        SELECT id, name, type, 
               ROUND(ST_X(geom) / $1) as grid_x,
               ROUND(ST_Y(geom) / $1) as grid_y,
               FLOOR(ST_Z(geom) / 3.0) as floor_level
        FROM equipment 
        WHERE building_id = $2
        ORDER BY floor_level, grid_y, grid_x
    `
    return p.executeGridQuery(query, gridScale, buildingID)
}

// No complex bidirectional sync - just simple generation for display
func GenerateBIMFile(buildingID string) (*BIMFile, error) {
    // 1. Query PostGIS for all equipment
    equipment := postgis.GetAllEquipment(buildingID)
    
    // 2. Convert to grid coordinates for ASCII display
    gridEquipment := postgis.GenerateGridCoordinates(buildingID, 0.5)
    
    // 3. Generate human-readable .bim.txt
    return bim.GenerateFromSpatialData(equipment, gridEquipment)
}
```

### LiDAR Integration Pipeline

```go
// Simplified LiDAR processing - direct PostGIS import
func ProcessLiDARScan(pointCloud PointCloud, buildingID string) error {
    // 1. Align point cloud to building coordinate system
    alignedCloud := alignToBuilding(pointCloud, buildingID)
    
    // 2. Import point cloud directly to PostGIS
    err := postgis.ImportPointCloud(alignedCloud, buildingID)
    if err != nil {
        return err
    }
    
    // 3. Use PostGIS spatial functions for object detection
    detectedObjects := postgis.SpatialClusterAnalysis(buildingID)
    
    // 4. Match using PostGIS spatial proximity
    for _, obj := range detectedObjects {
        nearbyEquipment := postgis.FindNearbyEquipment(obj.Center, 2.0) // 2m radius
        
        if len(nearbyEquipment) == 1 {
            // Update position with high confidence
            postgis.UpdateEquipmentPosition(nearbyEquipment[0].ID, obj.Center, "HIGH", "lidar")
        }
    }
    
    // 5. Regenerate .bim.txt from updated PostGIS data
    return GenerateBIMFile(buildingID)
}
```

## Interface Layers

### 1. Terminal Interface (Current) - Building Operations
- **Target Users**: Building managers, systems engineers, facility operators
- **Technology**: Native Go with ASCII art rendering
- **Data Source**: PostGIS spatial database with .bim.txt derived views
- **Features**: 
  - Real-time PostGIS spatial queries
  - System tracing using spatial relationships
  - ASCII floor plans generated from PostGIS data
  - Git-like version control for .bim.txt files
  - Spatial queries (proximity, containment, distance)
- **Status**: Core functionality implemented with PostGIS integration

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
cmd/arx/                     # CLI entrypoints (thin UX layer)
├── main.go                  # Entry point, mode detection
├── cmd_install.go           # Installation command (with professional setup)
├── cmd_daemon.go           # Professional BIM integration daemon
├── cmd_import.go           # Import to PostGIS operations (delegates to services)
├── cmd_export.go           # Export from PostGIS operations (delegates to services)
├── cmd_query.go            # PostGIS spatial query operations (delegates to services)
├── cmd_simulate.go         # Simulation operations (delegates to services)
├── cmd_sync.go             # BIM synchronization (delegates to services)
├── cmd_repo.go             # Repository operations
├── cmd_serve.go            # Server mode
└── cmd_crud.go             # CRUD operations

internal/
├── database/               # Database implementations
│   ├── postgis.go         # PostGIS spatial database (primary)
│   ├── sqlite.go          # SQLite fallback database
│   ├── spatial.go         # Spatial operations interface
│   └── hybrid.go          # Hybrid PostGIS/SQLite support
│
├── daemon/                 # Professional BIM integration
│   ├── ifc_watcher.go     # IFC file monitoring
│   ├── professional.go    # Professional workflow automation
│   ├── auto_export.go     # Automatic format generation
│   └── service.go         # Daemon service management
│
├── converter/              # Import format converters
│   ├── ifc_improved.go    # IFC → PostGIS converter
│   ├── pdf_real.go        # PDF → PostGIS converter
│   └── converter.go       # Converter registry
│
├── exporter/               # Export format generators (NEW)
│   ├── ifc_exporter.go    # PostGIS → IFC export
│   ├── bim_generator.go   # PostGIS → .bim.txt generation
│   ├── pdf_renderer.go    # PostGIS → PDF floor plans
│   └── multi_format.go    # Batch export capabilities
│
├── storage/               # Version control and file operations
│   ├── git_integration.go # Git operations for buildings
│   ├── change_tracker.go  # PostGIS change detection
│   └── repository.go      # Repository management
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
│   ├── bim_sync.go       # BIM synchronization service
│   ├── export_command.go # Export operations service
│   ├── import_command.go # Import operations service
│   ├── query_service.go  # Database query service
│   └── validator.go      # BIM validation
├── simulation/           # Building simulation engine
│   ├── engine.go         # Core simulation logic
│   └── service.go        # Simulation service layer
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
  database: ~/.arxos/arxos.db      # SQLite fallback
  postgis_config: ~/.arxos/postgis.conf
  buildings: ./buildings          # Git repositories
  logs: ~/.arxos/logs

# PostGIS primary database
postgis:
  enabled: true
  host: localhost
  port: 5432
  database: arxos_spatial
  user: arxos
  password: ${POSTGIS_PASSWORD}
  sslmode: prefer
  spatial_reference: 4326         # WGS84

# Professional BIM integration
professional:
  enabled: false
  daemon:
    enabled: false
    ifc_patterns:
      - "*.ifc"
      - "*.ifcxml"
    watch_directories:
      - "C:/BIM_Projects"
      - "C:/Revit_Exports"
    auto_export: true
    auto_commit: true
    check_interval: 30s

# Database fallback
database:
  type: hybrid                    # PostGIS primary, SQLite fallback
  fallback: sqlite
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
  ifc:
    coordinate_precision: millimeter
    validate_geometry: true
  pdf:
    ocr: true
    dpi: 300
    coordinate_estimation: true
  validation:
    strict: true

export:
  ifc:
    version: "4.0"
    precision: full
  bim:
    grid_scale: 0.5
    coordinate_system: "grid"
  pdf:
    dpi: 300
    include_metadata: true
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

- **Installation**: < 10 seconds (including PostGIS setup)
- **IFC Import**: < 30 seconds for typical building models
- **PostGIS Queries**: < 50ms for 10K+ equipment spatial queries
- **File Monitoring**: < 5 second IFC detection and processing
- **Export Generation**: < 15 seconds for .bim.txt from large PostGIS datasets
- **API Response**: < 25ms for standard PostGIS spatial queries
- **Daemon Response**: < 30 seconds from IFC change to team updates
- **Database Size**: ~2MB per 1,000 equipment items (with spatial indexes)

## BuildingOps Layer - Physical Control & Automation

### Overview

BuildingOps extends ArxOS from a data management system to a complete building operating system with bidirectional physical control. Every path in the database can trigger real-world actions through three unified interfaces.

### Control Interface Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   User Control Interfaces                    │
├───────────────────┬──────────────────┬──────────────────────┤
│   CLI Commands    │ Natural Language │  Visual Workflows    │
│  arx set [path]   │  "Make it cooler" │   n8n Drag-Drop     │
└───────────────────┴──────────────────┴──────────────────────┘
                            │
                    ┌───────▼───────┐
                    │  Path Engine   │
                    │  /B1/3/HVAC/*  │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │    PostGIS     │
                    │   Database     │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  Go Gateway    │
                    │  Translation   │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │ TinyGo Devices │
                    │  ESP32/RP2040  │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │Physical Actions│
                    │ Servos, Relays │
                    └────────────────┘
```

### Three Control Modes

#### 1. CLI Path Control
Direct terminal commands that map to physical actions:
```bash
# Direct control
arx set /B1/3/HVAC/DAMPER-01 position:50
arx set /B1/3/LIGHTS/ZONE-A brightness:75
arx set /B1/3/DOORS/MAIN state:locked

# Batch operations
arx set /B1/*/LIGHTS/* state:off
arx scene /B1/3/CONF-301 presentation
```

#### 2. Natural Language Processing
AI-interpreted commands that resolve to paths:
```bash
arx do "turn off all lights on floor 3"
arx do "set conference room to presentation mode"
arx do "secure the building"
```

Natural language → Intent extraction → Path resolution → Physical action

#### 3. Visual Workflow Automation (n8n)
Drag-and-drop workflows that control physical systems:
- Temperature sensor triggers → HVAC damper adjusts
- Motion detected → Lights activate
- Schedule reached → Building enters eco mode

### Hardware Integration Architecture

#### Three-Tier Hardware Stack

```
Cloud (ArxOS Core)          - Full Go, PostgreSQL/PostGIS
    ↓
Gateway (Raspberry Pi)      - Full Go, Protocol translation
    ↓
Edge Devices (ESP32)        - TinyGo, Simple HTTP/MQTT
```

#### Pure Go Implementation
- **No C required**: 100% Go/TinyGo codebase
- **Edge simplicity**: Devices only speak HTTP/MQTT
- **Gateway complexity**: All protocol translation at gateway
- **Type safety**: Go's type system throughout

### Safety & Validation

#### Command Validation Pipeline
```go
func ValidateCommand(cmd PathCommand) error {
    // 1. Permission check
    if !user.CanControl(cmd.Path) {
        return ErrUnauthorized
    }

    // 2. Safety interlocks
    if isEmergencyActive() && !cmd.Override {
        return ErrSafetyInterlock
    }

    // 3. Range validation
    if cmd.Value < 0 || cmd.Value > 100 {
        return ErrOutOfRange
    }

    // 4. Rate limiting
    if isRateLimited(cmd.Path) {
        return ErrRateLimited
    }

    return nil
}
```

### Workflow Integration

#### n8n Integration via REST
- ArxOS provides REST endpoints
- n8n uses built-in HTTP Request nodes
- No custom JavaScript required
- Bidirectional communication supported

#### Workflow Types
1. **Reactive**: Equipment failure → Create work order
2. **Scheduled**: Time-based maintenance routines
3. **Predictive**: Pattern analysis → Preventive action
4. **Emergency**: Alarm triggered → Building-wide response

### Implementation Components

```
internal/
├── control/          # Physical control logic
│   ├── validator.go  # Safety validation
│   ├── executor.go   # Command execution
│   └── feedback.go   # Status monitoring
├── nlp/              # Natural language processing
│   ├── interpreter.go # Intent extraction
│   └── resolver.go   # Path resolution
├── workflow/         # n8n integration
│   ├── handlers.go   # REST endpoints
│   └── registry.go   # Workflow management
└── hardware/         # Device communication
    ├── gateway.go    # Protocol translation
    └── mqtt.go       # Device messaging
```

### Performance Requirements

- **Command latency**: < 100ms to gateway
- **Physical actuation**: < 2s total
- **Natural language**: < 500ms processing
- **Workflow execution**: < 5s end-to-end
- **Safety validation**: < 10ms

## Future Enhancements

### Phase 1 (Current - In Progress)
- ✅ Single binary architecture
- ✅ PostGIS spatial database integration
- ✅ SQL-based query system with spatial operations
- 🚧 Professional BIM integration daemon
- 🚧 IFC import/export pipeline
- 🚧 Universal BIM tool compatibility

### Phase 2 (Professional Features)
- ⬜ Advanced spatial analytics and reporting
- ⬜ Multi-building project management
- ⬜ Professional BIM tool plugins (optional)
- ⬜ Advanced IFC schema support (IFC 5.0+)
- ⬜ Cloud-based PostGIS deployment
- ⬜ Professional team collaboration features

### Phase 3 (Advanced Capabilities)
- ⬜ Machine learning for spatial pattern recognition
- ⬜ Advanced AR/VR with spatial computing
- ⬜ IoT device direct integration with PostGIS
- ⬜ Real-time digital twin simulation
- ⬜ Predictive maintenance using spatial analytics
- ⬜ Mobile AR application (React Native)
- ⬜ Web 3D visualization (Svelte + Three.js)

### Phase 4 (Enterprise & Scale)
- ⬜ Distributed PostGIS deployment
- ⬜ Enterprise authentication and authorization
- ⬜ Compliance and audit trail features
- ⬜ Performance optimization for massive buildings
- ⬜ GraphQL API for advanced integrations
- ⬜ Packet radio transport (LoRaWAN/APRS)

## Troubleshooting

### Common Issues

**PostGIS connection issues**:
```bash
arx status --check-postgis   # Check PostGIS connection
arx install --setup-postgis # Reinstall PostGIS configuration
```

**Daemon not processing IFC files**:
```bash
arx daemon status           # Check daemon status
arx daemon logs            # View daemon logs
arx daemon restart         # Restart daemon service
```

**IFC import failures**:
```bash
arx validate <file.ifc>     # Check IFC file format
arx import --verbose <file.ifc> # Detailed error output
arx import --dry-run <file.ifc> # Test import without changes
```

**Export precision issues**:
```bash
arx export --format ifc --precision full  # Full precision export
arx query --spatial --building ARXOS-001  # Verify PostGIS data
```

## Professional BIM Integration Examples

### Typical Professional Workflows

#### Revit Integration Example
```bash
# 1. Professional setup (one-time)
arx install --professional --with-daemon
arx daemon watch --ifc "C:\Revit_Projects\*.ifc"

# 2. Daily workflow (automatic)
# - Architect works in Revit
# - Exports IFC to C:\Revit_Projects\Building_A.ifc
# - ArxOS daemon detects file change
# - PostGIS updated automatically
# - .bim.txt regenerated for Git
# - Team notified of changes

# 3. Team collaboration (real-time)
arx query --building Building_A --floor 3  # See latest changes
arx export Building_A --format pdf         # Generate updated floor plans
```

#### Multi-Tool Project Example
```bash
# Project with multiple BIM tools
arx daemon watch --ifc "C:\Project_Alpha\Revit\*.ifc"     # Architect
arx daemon watch --ifc "C:\Project_Alpha\AutoCAD\*.ifc"   # Engineer  
arx daemon watch --ifc "C:\Project_Alpha\Tekla\*.ifc"     # Structural

# All tools feed into same PostGIS database
# Team sees unified, real-time building model
# No manual coordination required
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

Key points for contributors:
- **PostGIS-First Development**: All spatial features should use PostGIS as primary storage
- **Professional Focus**: Consider BIM professional workflows in all design decisions
- **Universal IFC Compatibility**: Test with multiple BIM tool outputs
- **Single Binary Architecture**: All functionality in single `arx` binary
- **Commands use Cobra Framework**: Consistent CLI patterns
- **Spatial Testing Required**: PostGIS integration tests for spatial features
- **Professional Documentation**: Include BIM tool integration examples

### Development Priorities
1. **PostGIS Integration**: Spatial database operations and performance
2. **IFC Processing**: Universal BIM tool compatibility
3. **Professional Workflows**: Zero-disruption BIM integration
4. **Export Quality**: Precision maintenance across all formats
5. **Daemon Reliability**: Professional-grade service stability