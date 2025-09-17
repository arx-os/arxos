# ArxOS - Building Operating System

[![CI/CD Pipeline](https://github.com/arx-os/arxos/actions/workflows/ci.yml/badge.svg)](https://github.com/arx-os/arxos/actions/workflows/ci.yml)
[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ArxOS treats buildings as code repositories, providing a universal addressing system for every component, system, and space. One tool manages everything - from field equipment to cloud analytics.

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

**Building-as-Code**: Human-readable `.bim.txt` files that work with Git, enabling version control, branching, and collaborative workflows impossible with traditional BIM formats.

## 🚀 Quick Start

### Installation

```bash
# Install from source
go install github.com/arx-os/arxos/cmd/arx@latest

# Or build locally
git clone https://github.com/arx-os/arxos.git
cd arxos
go build -o arx ./cmd/arx
sudo mv arx /usr/local/bin/

# Initialize ArxOS (one-time setup)
arx install

# Verify installation
arx status
```

### Your First Building

```bash
# Initialize a new building
arx repo init ARXOS-NA-US-CA-LAX-0001 --name "Los Angeles Office"

# Convert any building file to BIM format
arx convert floor_plan.pdf building.bim.txt

# Import to building repository
arx import building.bim.txt --building ARXOS-NA-US-CA-LAX-0001

# Add equipment manually
arx add /3/A/301/E/OUTLET_02 --type electrical.outlet --status operational

# Check what changed
arx repo status

# Commit changes
arx repo commit -m "Added third floor electrical outlets"

# Query equipment
arx query --floor 3 --type electrical
```

## 📖 Command Reference

### System Management

```bash
arx install                    # Set up ArxOS (creates database, starts file watcher)
arx install --with-server      # Also install API server as system service
arx status                     # Show system-wide status
arx config                     # View/edit configuration
arx uninstall                  # Remove ArxOS (preserves data)
```

### Repository Operations

```bash
arx repo init <building-id>    # Initialize building repository
arx repo status                # Show uncommitted changes
arx repo diff                  # Show detailed changes
arx repo commit -m "message"   # Commit changes to history
arx repo log                   # View commit history
arx repo branch <name>         # Create branch for experiments
arx repo merge <branch>        # Merge branch changes
```

### Data Operations

```bash
arx convert <file> [output]    # Convert any building file to BIM
arx convert list               # List all supported formats
arx import <file>              # Import from PDF/IFC/BIM/DWG
arx export <building-id>       # Export to various formats
arx validate <file>            # Validate BIM file format
arx sync                       # Sync between files and database
```

### Building Management

```bash
arx add <path> [options]       # Add component/equipment
arx update <path> [options]    # Update component properties
arx remove <path>              # Remove component
arx get <path>                 # Get component details
arx list [--type] [--status]   # List components
arx query [complex filters]    # Advanced queries
arx search <text>              # Full-text search
```

### Multi-Level Viewing

```bash
# Overview mode - room/floor level schematic
arx view CONFERENCE_A          # Shows general layout from .bim.txt
arx render --floor 3           # ASCII floor plan overview

# Detail mode - equipment specifications and connections  
arx view CONFERENCE_A/OUTLET_02 --detail    # Equipment specs, maintenance history
arx view OUTLET_02 --trace-power             # ASCII diagram of electrical path
arx view HVAC_SYSTEM --connections          # System interconnections

# Spatial mode - precise coordinates for field work
arx view OUTLET_02 --spatial   # PostGIS coordinates for AR applications
arx view --floor 3 --spatial   # Precise equipment positions
```

### File Monitoring

```bash
arx watch add <directory>      # Add directory to monitor
arx watch remove <directory>   # Stop monitoring directory
arx watch list                 # Show monitored directories
arx watch pause                # Temporarily pause monitoring
arx watch resume               # Resume monitoring
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

### **Data Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Level Data Storage                     │
├─────────────────────────────────────────────────────────────────┤
│  .bim.txt (Source of Truth)     │  PostGIS (Spatial Database)   │
│  ├─ Human-readable schematic    │  ├─ Precise 3D coordinates    │
│  ├─ Git version control         │  ├─ AR spatial anchors        │
│  ├─ Equipment relationships     │  ├─ LiDAR point clouds        │
│  └─ System connections          │  └─ Real-world positioning    │
├─────────────────────────────────────────────────────────────────┤
│                          Access Methods                         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐  │
│  │ Terminal    │  Web 3D     │ Mobile AR   │  Packet Radio   │  │
│  │ (ASCII)     │ (Svelte)    │ (React      │ (LoRaWAN/APRS) │  │
│  │             │             │  Native)    │                 │  │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### **Coordinate System Design**

- **.bim.txt**: Grid-based schematic coordinates for human readability
- **PostGIS**: Millimeter-precision real-world coordinates for AR/field work
- **Automatic sync**: AR edits update PostGIS; significant changes update .bim.txt
- **Zoom levels**: Terminal can show overview, detail, or system-trace views

## 📁 Project Structure

After installation, ArxOS creates:

```
~/.arxos/                      # ArxOS system directory
├── config.yaml                # System configuration
├── arxos.db                   # SQLite database
└── run/                       # Runtime files (PID, sockets)

./buildings/                   # Your building repositories (Git)
├── ARXOS-NA-US-CA-LAX-0001/
│   ├── .git/                  # Version history
│   ├── building.bim.txt       # Building definition
│   ├── floors/                # Floor plans
│   └── equipment/             # Equipment data
└── ARXOS-NA-US-NY-NYC-0002/
    └── ...
```

## 🔧 Configuration

ArxOS configuration lives in `~/.arxos/config.yaml`:

```yaml
# Database
database:
  path: ~/.arxos/arxos.db
  backup_interval: 24h

# File Monitoring
watcher:
  directories:
    - ./buildings
    - /shared/bim-files
  auto_import: true
  scan_interval: 5s

# API Server (optional)
server:
  enabled: false
  port: 8080
  auth: false

# Logging
log:
  level: info
  file: ~/.arxos/arxos.log
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

## 🔄 Universal File Converter

ArxOS can convert between any building file format and the universal BIM text format:

### Supported Formats
- **IFC** (.ifc, .ifcxml) - Industry Foundation Classes open BIM standard
- **PDF** (.pdf) - Floor plans, as-builts with OCR extraction
- **AutoCAD** (.dwg, .dxf) - 2D/3D CAD drawings
- **Revit** (.rvt, .rfa) - Autodesk BIM models
- **gbXML** (.gbxml) - Energy analysis models
- **COBie** (.xlsx, .csv) - Facility management spreadsheets
- **Point Clouds** (.las, .laz, .e57, .ply) - 3D laser scanning
- **Haystack/Brick** (.json, .zinc) - IoT sensor data
- **SketchUp** (.skp), **Navisworks** (.nwd), **ArchiCAD** (.pln), and more

### Conversion Examples
```bash
# Convert IFC to BIM
arx convert model.ifc building.bim.txt

# Auto-detect format and convert
arx convert floor_plan.pdf

# Merge IoT data into existing BIM
arx convert sensors.json building.bim.txt --merge

# List all supported formats
arx convert list
```

### Use Cases
- Import existing BIM models from any CAD/BIM software
- Extract floor plans and equipment from PDF documents
- Integrate IoT sensor networks with building models
- Convert facility management spreadsheets to BIM
- Merge as-built, as-designed, and as-operated data

## 🖥️ Interface Options

ArxOS provides multiple interfaces optimized for different user roles and precision needs:

### Terminal (Available Now) - Building Operations
**Target Users**: Building managers, systems engineers, facility operators
**Data Source**: `.bim.txt` files with PostGIS for detailed views
**Precision**: Schematic-level for overview, system-level for detailed tracing

```bash
# Overview: Quick reference and understanding
arx render --floor 3              # ASCII floor plan schematic
arx list --room CONFERENCE_A      # Equipment in room

# Detail: System tracing and specifications  
arx view OUTLET_02 --trace-power  # ASCII diagram of electrical path
arx view HVAC_SYSTEM --detail     # Technical specifications
arx monitor --live                # Live status display
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
**Data Source**: Combined .bim.txt and PostGIS for comprehensive visualization
**Precision**: Interactive 3D models with system relationships

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

ArxOS uses a simple, human-readable format designed for **schematic representation** and version control:

### **Design Philosophy**
- **Schematic, not CAD**: Focus on relationships and general positioning
- **Human-readable**: Engineers can read and edit with any text editor
- **Git-friendly**: Text diffs show meaningful changes
- **Grid-based coordinates**: Simple integer positions for ASCII visualization

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
- **Grid coordinates**: `LOCATION: (45, 30)` for ASCII visualization
- **Room references**: `ROOM: MECHANICAL_ROOM` for spatial context
- **Precise positioning**: Stored separately in PostGIS for AR/field applications
- **Automatic sync**: AR edits update PostGIS; significant moves update .bim.txt grid position

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

*ArxOS: Because buildings are infrastructure, and infrastructure should be code.*