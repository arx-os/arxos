# ArxOS - Building Operating System

[![CI/CD Pipeline](https://github.com/arx-os/arxos/actions/workflows/ci.yml/badge.svg)](https://github.com/arx-os/arxos/actions/workflows/ci.yml)
[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ArxOS treats buildings as code repositories with PostGIS spatial precision, providing seamless integration with professional BIM tools and universal addressing for every component, system, and space. One tool manages everything - from professional BIM workflows to field equipment analytics.

## 🎯 Core Innovation

**Universal Addressing**: Every piece of equipment has a hierarchical path
```
ARXOS-NA-US-NY-NYC-0001/3/A/301/E/OUTLET_02
│                       │ │ │   │ └─ Equipment ID
│                       │ │ │   └─── Wall (East)
│                       │ │ └─────── Room 301
│                       │ └───────── Zone A
│                       └─────────── Floor 3
└───────────────────────────────────── Building UUID
```

**Building-as-Code**: Human-readable `.bim.txt` files generated from PostGIS spatial database, enabling Git version control, team collaboration, and professional BIM tool integration impossible with traditional formats.

**Professional BIM Integration**: Seamless integration with any BIM tool (Revit, AutoCAD, ArchiCAD, Tekla) via standard IFC files - no workflow changes required.

## 🚀 Quick Start

### Prerequisites

ArxOS requires PostGIS for spatial operations:

```bash
# Install PostGIS (Ubuntu/Debian)
sudo apt install postgresql postgis postgresql-contrib

# Or use Docker
docker run -d --name arxos-postgis \
  -e POSTGRES_DB=arxos_spatial \
  -e POSTGRES_USER=arxos \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# Verify PostGIS installation
psql -h localhost -U arxos -d arxos_spatial -c "SELECT PostGIS_Version();"
```

### Installation

```bash
# Install from source
go install github.com/arx-os/arxos/cmd/arx@latest

# Or build locally
git clone https://github.com/arx-os/arxos.git
cd arxos
go build -o arx ./cmd/arx

# Initialize ArxOS with PostGIS
arx install --setup-postgis

# For BIM professionals
arx install --professional --with-daemon

# Verify installation
arx query --help  # Should show spatial query options
```

### Your First Building

```bash
# Convert IFC file to PostGIS (imports spatial data)
arx import model.ifc --building ARXOS-NA-US-CA-LAX-0001

# Or convert PDF floor plan
arx convert floor_plan.pdf building.bim.txt
arx import building.bim.txt --building ARXOS-NA-US-CA-LAX-0001

# Add equipment with precise coordinates
arx add /3/A/301/E/OUTLET_02 --type electrical.outlet --location "12.547,8.291,1.127"

# Query with spatial operations (PostGIS-powered)
arx query --floor 3 --type electrical
arx query --near "12.5,8.3,1.1" --radius 5.0
arx query --building ARXOS-NA-US-CA-LAX-0001 --output json

# Update equipment position (millimeter precision)
arx update /3/A/301/E/OUTLET_02 --location "12.550,8.291,1.127"

# Export to various formats from PostGIS
arx export ARXOS-NA-US-CA-LAX-0001 --format ifc --precision full
arx export ARXOS-NA-US-CA-LAX-0001 --format bim --for-git
```

## 📖 Command Reference

### System Management

```bash
arx install                    # Set up ArxOS (creates PostGIS database)
arx install --professional     # Install with BIM professional daemon
arx install --setup-postgis    # Configure PostGIS spatial database
arx version                    # Show version information
```

### Professional BIM Integration

```bash
arx daemon watch --ifc "*.ifc"         # Monitor IFC files from BIM tools
arx daemon status                      # Show daemon and integration status
arx daemon start --professional        # Start professional workflow daemon
arx daemon stop                        # Stop daemon service
```

### Repository Operations (Planned)

```bash
arx repo init <building-id>    # Initialize building repository (planned)
arx repo status                # Show uncommitted changes (planned)
arx repo diff                  # Show detailed changes (planned)
arx repo commit -m "message"   # Commit changes to history (planned)
```

### Data Operations

```bash
arx convert <file> [output]    # Convert PDF/IFC to BIM format
arx convert list               # List supported formats (PDF, IFC)
arx import <file>              # Import to PostGIS from PDF/IFC
arx export <building-id>       # Export from PostGIS to various formats
arx validate <file>            # Validate file format
```

### Building Management (PostGIS-Powered)

```bash
arx add <path> --location "x,y,z"      # Add equipment with precise coordinates
arx update <path> --location "x,y,z"   # Update equipment position (millimeter precision)
arx update <path> --move-by "dx,dy,dz" # Move equipment relatively
arx remove <path>                      # Remove component
arx get <path>                         # Get component details (planned)
arx list [--type] [--status]           # List components (planned)
arx query [spatial filters]            # PostGIS spatial queries ✅
arx trace <path> --type <system>       # Trace system connections (planned)
```

### Spatial Queries (Available Now)

```bash
arx query --building <id>              # Filter by building
arx query --floor 3 --type electrical  # Floor and type filtering
arx query --status failed             # Status filtering
arx query --near "x,y,z" --radius 5.0 # Spatial proximity (PostGIS)
arx query --output json               # JSON output format
arx query --count                     # Count results only
arx query --limit 50 --offset 10      # Pagination
```

### Multi-Level Viewing (Planned)

```bash
# Overview mode - room/floor level schematic (from PostGIS)
arx visualize --floor 3                     # ASCII floor plan from PostGIS
arx query --floor 3 --visualize spatial     # Spatial layout visualization

# Detail mode - equipment specifications and connections (planned)
arx trace OUTLET_02 --type power --visualize path    # System tracing
arx query --equipment HVAC --visualize connections   # System interconnections

# Spatial mode - precise PostGIS coordinates
arx query --near "12.5,8.3,1.1" --radius 2.0       # Spatial proximity
arx query --floor 3 --output csv                    # Export coordinates
```

### Professional BIM Workflow

```bash
# One-time setup for BIM professionals
arx install --professional --with-daemon
arx daemon watch --ifc "C:\BIM_Projects\*.ifc"

# Daily workflow (automatic)
# 1. Work in Revit/AutoCAD/ArchiCAD as usual
# 2. Export IFC file (standard practice)
# 3. ArxOS daemon automatically processes IFC
# 4. PostGIS updated with precise coordinates
# 5. Team sees changes immediately

# View team updates
arx query --building ARXOS-001 --changed --since "1h"
arx export ARXOS-001 --format bim --for-git
```

### API Server

```bash
arx serve                      # Start API server (foreground)
arx serve --daemon             # Start as background service
arx serve --stop               # Stop background server
arx serve --status             # Check server status
```

## 🏗️ How It Works

ArxOS provides a **multi-level user experience** where different interfaces serve different precision needs:

### **Building Operations Hierarchy**

1. **Building Manager (Terminal)**: Overview and relationships
   - `.bim.txt` shows general equipment locations and connections
   - Perfect for: "Is there an outlet in Conference Room A?"
   - ASCII visualization for quick reference and understanding

2. **Field Technician (Mobile AR)**: Precise positioning and installation
   - AR overlay shows exact equipment locations in real-world space
   - Perfect for: "Where exactly should I mount this device?"
   - Millimeter precision for physical work

3. **Systems Engineer (Terminal Detail)**: Technical specifications and tracing
   - Detailed views show wiring paths, specifications, connections
   - Perfect for: "What's the power path from panel to outlet?"
   - System-level schematics and relationships

### **PostGIS-Centric Data Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                Professional BIM Tools                           │
│  ┌──────────┬──────────┬──────────┬────────────────────────┐  │
│  │  Revit   │ AutoCAD  │ArchiCAD  │    Any IFC Tool        │  │
│  └──────────┴──────────┴──────────┴────────────────────────┘  │
│                              │                               │
│                       Standard IFC Export                    │
│                              ▼                               │
├─────────────────────────────────────────────────────────────────┤
│                      ArxOS Daemon                               │
│                   (IFC File Monitoring)                         │
├─────────────────────────────────────────────────────────────────┤
│                   PostGIS Database                              │
│                 (Single Source of Truth)                        │
│  ├─ Millimeter-precision 3D coordinates                        │
│  ├─ Spatial indexes and operations                             │
│  ├─ Equipment positioning and relationships                     │
│  ├─ AR spatial anchors and mobile integration                  │
│  └─ LiDAR point clouds and reality capture                     │
├─────────────────────────────────────────────────────────────────┤
│                      User Interfaces                            │
│  ┌─────────────┬─────────────┬─────────────┬───────────────┐  │
│  │ Terminal    │  Web 3D     │ Mobile AR   │  Packet Radio │  │
│  │ (PostGIS)   │ (PostGIS)   │ (PostGIS)   │ (Compressed)  │  │
│  └─────────────┴─────────────┴─────────────┴───────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Derived Outputs                            │
│  ┌─────────────┬─────────────┬─────────────┬───────────────┐  │
│  │ .bim.txt    │ IFC Export  │ PDF Plans   │ CSV/JSON      │  │
│  │(Git/Human)  │(BIM Tools)  │(Reports)    │(Analysis)     │  │
│  └─────────────┴─────────────┴─────────────┴───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### **Coordinate System Design**

- **PostGIS Database**: Single source of truth with millimeter-precision 3D coordinates
- **.bim.txt**: Grid-based representation generated from PostGIS for human readability  
- **IFC Export**: Full-precision coordinates exported from PostGIS for BIM tools
- **CLI Control**: Terminal commands can query and modify PostGIS coordinates directly
- **Professional Integration**: BIM tool changes flow through IFC → PostGIS → team updates

## 📁 Project Structure

After installation, ArxOS creates:

```
~/.arxos/                      # ArxOS system directory
├── config.yaml                # System configuration
├── postgis.conf               # PostGIS connection config
├── arxos.db                   # SQLite database (fallback)
├── logs/                      # System logs
└── run/                       # Runtime files (PID, sockets)

./buildings/                   # Building repositories (Git)
├── ARXOS-NA-US-CA-LAX-0001/
│   ├── .git/                  # Version history
│   ├── building.bim.txt       # Generated from PostGIS
│   ├── exports/               # IFC exports for BIM tools
│   └── reports/               # Generated reports
└── ARXOS-NA-US-NY-NYC-0002/
    └── ...

PostGIS Database:              # Spatial data (primary storage)
├── equipment (with geom)      # Equipment with 3D coordinates
├── buildings                  # Building metadata
├── floors                     # Floor boundaries
└── spatial_indexes           # Performance optimization
```

## 🔧 Configuration

ArxOS configuration lives in `~/.arxos/config.yaml`:

```yaml
# PostGIS primary database
postgis:
  enabled: true
  host: localhost
  port: 5432
  database: arxos_spatial
  user: arxos
  password: ${POSTGIS_PASSWORD}
  spatial_reference: 4326

# Professional BIM integration
professional:
  enabled: false
  daemon:
    enabled: false
    ifc_patterns: ["*.ifc", "*.ifcxml"]
    watch_directories: ["C:/BIM_Projects", "C:/Revit_Exports"]
    auto_export: true
    auto_commit: true

# Database fallback
database:
  type: hybrid                # PostGIS primary, SQLite fallback
  fallback_path: ~/.arxos/arxos.db
  backup_interval: 24h

# API Server (optional)
server:
  enabled: false
  port: 8080
  auth: false

# Logging
log:
  level: info
  file: ~/.arxos/logs/arxos.log
```

## 🏢 Real-World Use Cases

### Construction Site
```bash
# Morning: Pull latest changes
arx sync

# During day: Track installations
arx update /3/A/301/E/OUTLET_02 --status installed --installer "John Smith"
arx update /3/A/301/N/HVAC_VAV_01 --status failed --notes "Actuator defective"

# End of day: Commit progress
arx repo commit -m "Day 47: Third floor electrical 85% complete"
```

### Facility Management
```bash
# Find all degraded equipment
arx query --status degraded

# Schedule maintenance
arx update /R/C/MECH/N/RTU_01 --next-maintenance 2024-03-15

# Generate monthly report
arx export ARXOS-NA-US-NY-NYC-0001 --format pdf --template maintenance-report
```

### Emergency Response
```bash
# Locate fire suppression systems
arx query --type "fire.*" --floor 3

# Find nearest exits
arx get /3/*/EXIT_*

# Check critical systems
arx query --critical --status operational
```

## 🔄 File Import & Export

ArxOS imports building data to PostGIS spatial database and exports to multiple formats:

### Currently Supported Formats
- **IFC** (.ifc, .ifcxml) - Industry Foundation Classes open BIM standard ✅
- **PDF** (.pdf) - Floor plans, as-builts with OCR extraction ✅

### Planned Format Support
- **Point Clouds** (.las, .laz, .e57, .ply) - 3D laser scanning
- **AutoCAD** (.dwg, .dxf) - 2D/3D CAD drawings  
- **gbXML** (.gbxml) - Energy analysis models
- **COBie** (.xlsx, .csv) - Facility management spreadsheets
- **Haystack/Brick** (.json, .zinc) - IoT sensor data

### Import/Export Examples
```bash
# Import IFC directly to PostGIS
arx import model.ifc --building ARXOS-001

# Convert PDF and import to PostGIS
arx convert floor_plan.pdf building.bim.txt
arx import building.bim.txt --building ARXOS-001

# Export from PostGIS to various formats
arx export ARXOS-001 --format ifc --precision full
arx export ARXOS-001 --format bim --for-git
arx export ARXOS-001 --format pdf --floor-plans

# List supported formats
arx convert list
```

### Use Cases
- **Professional BIM Integration**: Import IFC models from any BIM software
- **PDF Processing**: Extract floor plans and equipment from PDF documents  
- **Team Collaboration**: Generate .bim.txt files for Git version control
- **Spatial Analysis**: Query PostGIS database for equipment relationships
- **Multi-format Export**: Generate reports and exports for different stakeholders

## 🖥️ Interface Options

ArxOS provides multiple interfaces optimized for different user roles and precision needs:

### Terminal (Available Now) - PostGIS-Powered Operations
**Target Users**: Building managers, systems engineers, facility operators, BIM professionals
**Data Source**: PostGIS spatial database with .bim.txt derived views
**Precision**: Millimeter-level spatial queries with human-readable output

```bash
# Spatial queries: PostGIS-powered with real-time results
arx query --floor 3 --type electrical      # Filter by floor and type ✅
arx query --near "12.5,8.3,1.1" --radius 5.0  # Spatial proximity ✅
arx query --building ARXOS-001 --output json   # Multiple output formats ✅

# Spatial control: Direct PostGIS coordinate manipulation
arx update OUTLET_02 --location "12.547,8.291,1.127"  # Precise positioning
arx update OUTLET_02 --move-by "0.05,0,0"             # Relative movement

# Professional integration: Real-time BIM tool updates
arx daemon watch --ifc "C:\Projects\*.ifc"            # Monitor BIM exports
arx export ARXOS-001 --format ifc --precision full    # Export to BIM tools
```

### Mobile AR Application (Coming Soon) - Field Operations
**Target Users**: Field technicians, installers, maintenance staff
**Data Source**: PostGIS spatial database with millimeter precision
**Precision**: Real-world 3D coordinates for physical installation work

- **Technology**: React Native + ARKit/ARCore
- **Features**: 
  - Precise equipment positioning with AR overlay
  - LiDAR scanning integration
  - Spatial anchoring for persistent AR annotations
  - Offline sync for remote locations
- **Use Cases**: Equipment installation, maintenance, troubleshooting
- **Path**: `/mobile` - See [mobile/README.md](mobile/README.md)

### Web 3D Visualization (Coming Soon) - System Analysis
**Target Users**: Engineers, architects, system designers
**Data Source**: PostGIS spatial database for comprehensive 3D visualization
**Precision**: Interactive 3D models with real-time PostGIS spatial relationships

- **Technology**: Svelte + Three.js + D3.js
- **Features**: 
  - Interactive 3D building models
  - Real-time equipment status updates
  - Energy flow and system visualization
  - Multi-level zoom from building to component detail
- **Use Cases**: System design, analysis, presentations
- **Path**: `/web` - See [web/README.md](web/README.md)

### Packet Radio Transport (Experimental) - Emergency Operations
**Target Users**: Emergency responders, remote facility operators
**Data Source**: Compressed building data optimized for low bandwidth
**Precision**: Critical system information only

- **Protocols**: LoRaWAN, APRS, custom packet radio
- **Compression**: 92% size reduction for bandwidth constraints
- **Use Cases**: Off-grid buildings, disaster response, remote monitoring
- **Latency**: 1-30 seconds depending on radio technology
- **Path**: `/internal/transport/radio` - See [radio documentation](internal/transport/radio/README.md)

## 👔 Professional BIM Integration

### For BIM Professionals

ArxOS integrates seamlessly with existing professional BIM workflows through standard IFC files:

```bash
# One-time professional setup
arx install --professional --with-daemon

# Configure IFC monitoring for your BIM projects
arx daemon watch --ifc "C:\BIM_Projects\*.ifc"
arx daemon watch --ifc "C:\Revit_Exports\*.ifc"

# Continue working in your preferred BIM tool
# Export IFC as usual → ArxOS automatically processes → Team collaboration enabled
```

### Professional Workflow Benefits

- **Zero Workflow Changes**: Continue using Revit, AutoCAD, ArchiCAD, Tekla, etc.
- **Universal Compatibility**: Works with any BIM tool that exports IFC
- **Automatic Team Sync**: No manual coordination steps required
- **Precision Maintained**: Full millimeter accuracy preserved through PostGIS
- **Version Control**: Building changes automatically tracked in Git
- **Real-time Updates**: Changes propagate to field teams within minutes

### Professional Use Cases

#### Architecture Firm
```bash
# Architect exports Revit model to IFC
# ArxOS daemon detects change → PostGIS updated
# Engineering team sees updates immediately
arx query --building PROJECT_A --changed --since "1h"
arx export PROJECT_A --format pdf --floor-plans  # Updated drawings
```

#### Construction Project
```bash
# Multiple BIM tools feeding same project
arx daemon watch --ifc "C:\Project_Alpha\Revit\*.ifc"     # Architect
arx daemon watch --ifc "C:\Project_Alpha\AutoCAD\*.ifc"   # Engineer  
arx daemon watch --ifc "C:\Project_Alpha\Tekla\*.ifc"     # Structural

# Unified building model in PostGIS
# Field teams get coordinated, up-to-date information
arx query --building PROJECT_ALPHA --floor 3 --spatial
```

## 📊 API Reference

When you need programmatic access:

```bash
# Start API server
arx serve --daemon

# API is now available at http://localhost:8080
```

### Endpoints

```
GET    /api/v1/buildings              # List all buildings
GET    /api/v1/buildings/{id}         # Get building details
GET    /api/v1/equipment              # Query equipment
POST   /api/v1/equipment              # Add equipment
PATCH  /api/v1/equipment/{path}       # Update equipment
DELETE /api/v1/equipment/{path}       # Remove equipment
GET    /api/v1/search?q={query}       # Full-text search
WS     /api/v1/stream                 # Real-time updates
```

## 🧪 Development

```bash
# Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Run tests
go test ./...

# Build development version
go build -o arx ./cmd/arx

# Run with verbose logging
ARX_LOG_LEVEL=debug ./arx status
```

## 📝 BIM Text Format

ArxOS generates human-readable `.bim.txt` files from PostGIS spatial data for **team collaboration** and version control:

### **Design Philosophy**
- **Derived from PostGIS**: Generated automatically from spatial database, not manually edited
- **Schematic Representation**: Focus on relationships and general positioning for humans
- **Git-friendly**: Text diffs show meaningful building changes over time
- **Grid-based coordinates**: Simple integer positions converted from PostGIS for ASCII visualization
- **Team Collaboration**: Shareable, readable format for building managers and version control

### **Sample Format**
```
BUILDING: Example Office
UUID: ARXOS-NA-US-CA-LAX-0001
VERSION: 2.0
CREATED: 2024-01-15T10:00:00Z

# Coordinate system definition
COORDINATE_SYSTEM:
  ORIGIN: building_southwest_corner
  SCALE: 1_grid_unit = 0.5_meters
  ORIENTATION: north_up

FLOOR: 1 | Ground Floor
DIMENSIONS: 200 x 150 feet

EQUIPMENT:
  ID: HVAC_RTU_01
  PATH: /R/C/MECH/N
  TYPE: HVAC.RTU.Package
  LOCATION: (45, 30)           # Grid coordinates for ASCII display
  ROOM: MECHANICAL_ROOM
  STATUS: OPERATIONAL
  MODEL: Carrier 48TC
  SERIAL: CAR987654
  INSTALLED: 2023-06-01
  NOTES: Serving floors 1-3
```

### **Coordinate System**
- **Grid coordinates**: `LOCATION: (45, 30)` generated from PostGIS for ASCII visualization
- **Room references**: `ROOM: MECHANICAL_ROOM` for spatial context
- **Precise positioning**: Authoritative coordinates stored in PostGIS database
- **One-way generation**: PostGIS data automatically generates .bim.txt grid positions
- **CLI Control**: Terminal commands modify PostGIS directly, .bim.txt regenerated as needed

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

*ArxOS: Because buildings are infrastructure, and infrastructure should be code.*