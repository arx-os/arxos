# Arxos CLI Commands Reference

This document provides a comprehensive reference for all **Arxos CLI commands**, organized by category and including usage examples, options, and detailed explanations for the revolutionary building infrastructure platform.

---

## 🎯 **Overview**

The Arxos CLI is the **terminal-first interface** for the revolutionary Arxos platform. It transforms buildings into navigable filesystems with infinite fractal zoom capabilities, from campus level down to submicron precision. Every building component becomes an ArxObject with a path, properties, and real-time intelligence.

### **Revolutionary Features**
- **Building as Filesystem** - Navigate buildings like Unix filesystems
- **Infinite Zoom Architecture** - Seamless navigation from campus to nanoscopic levels
- **ASCII as Universal Language** - Buildings represented in ASCII art for universal access
- **SVG-Based BIM Foundation** - Precise coordinate system for 1:1 accurate rendering
- **ArxObject Intelligence** - Hierarchical system providing real-time data and control

---

## 🚀 **Initialization Commands**

### `arx init`

Initialize a new building workspace with the revolutionary ArxObject hierarchy and ASCII-BIM engine.

**Usage:**
```bash
arx init [flags] <building-id>
```

**Flags:**
- `--type <type>`: Building type (office, residential, industrial, retail, healthcare, educational)
- `--floors <n>`: Number of floors (default: 1)
- `--area <area>`: Building area (e.g., "5000m²", "10,000 sqft")
- `--location <location>`: Building location/address
- `--from-pdf <file>`: Initialize from PDF floor plan
- `--from-ifc <file>`: Initialize from IFC file
- `--from-svg <file>`: Initialize from SVG BIM file
- `--template <template>`: Use predefined building template
- `--config <file>`: Path to custom configuration file
- `--force`: Overwrite existing building workspace
- `--ascii-render`: Enable ASCII art rendering (default: true)
- `--svg-bim`: Enable SVG-based BIM (default: true)
- `--ar-overlay`: Enable AR ArxObject overlay (default: true)

**Examples:**
```bash
# Basic initialization
arx init building:office-001

# With specific configuration
arx init building:warehouse-001 --type industrial --floors 2 --area "25000m²"

# From PDF floor plan
arx init building:hospital-001 --type healthcare --floors 4 --from-pdf floor-plan.pdf

# From SVG BIM file
arx init building:complex-001 --type mixed-use --floors 6 --from-svg building-model.svg

# Using template
arx init building:school-001 --template educational --floors 3 --area "15000m²"
```

**What it creates:**
```
building-workspace/
├── .arxos/
│   ├── config/
│   │   ├── arxos.yml              # Building configuration
│   │   ├── environments/           # Environment-specific configs
│   │   └── templates/              # Building templates
│   ├── objects/                    # ArxObject database
│   │   ├── index.db               # Spatial and property indexes
│   │   ├── objects.db             # ArxObject storage
│   │   └── relationships.db        # Object relationship graph
│   ├── ascii-bim/                 # ASCII-BIM engine data
│   │   ├── zoom-levels/           # Infinite zoom configurations
│   │   ├── character-sets/        # Multi-resolution character sets
│   │   └── render-cache/          # Rendering cache
│   ├── svg-bim/                   # SVG-based BIM data
│   │   ├── models/                # SVG building models
│   │   ├── coordinates/           # Coordinate transformations
│   │   └── three-js/              # Three.js integration data
│   ├── ar-overlay/                # AR ArxObject overlay data
│   │   ├── spatial-anchors/       # Spatial anchoring data
│   │   ├── lidar-scans/           # LiDAR scanning data
│   │   └── field-validation/      # Field validation data
│   ├── vcs/                       # Version control data
│   │   ├── snapshots/             # Building state snapshots
│   │   ├── branches/              # Version branches
│   │   └── metadata/              # VCS metadata
│   ├── cache/                     # Performance cache
│   │   ├── ascii/                 # ASCII rendering cache
│   │   ├── spatial/               # Spatial query cache
│   │   └── validation/            # Validation result cache
│   └── logs/                      # Building operation logs
├── floors/                        # Floor directories
├── systems/                       # Building systems
├── zones/                         # Functional zones
├── assets/                        # Building assets
└── config/                        # Additional configuration
```

---

## 🗂️ **Navigation Commands**

### `arx pwd` - Print Working Directory

Displays the current virtual working directory within the building structure.

**Usage:**
```bash
arx pwd
```

**Output:**
```
building:building-001/floor-1/systems/electrical/panel-a
```

**Description:**
- Shows the current working directory in the virtual building filesystem
- Format: `building:<building-id><virtual-path>`
- Automatically detects building workspace and loads ArxObject session state

---

### `arx cd` - Change Directory

Changes the current working directory within the virtual building structure.

**Usage:**
```bash
arx cd <path>
arx cd ..                    # Go to parent directory
arx cd /                     # Go to building root
arx cd floor-1               # Go to specific floor
arx cd ../systems            # Relative path navigation
```

**Examples:**
```bash
# Navigate to a specific floor
arx cd floor-1

# Navigate to systems directory
arx cd /systems

# Navigate to electrical system
arx cd systems/electrical

# Navigate to specific panel
arx cd systems/electrical/panel-a

# Go back to parent directory
arx cd ..
```

**Features:**
- **Path Validation**: Ensures paths exist in the ArxObject hierarchy
- **Relative/Absolute**: Supports both relative and absolute path navigation
- **Session Persistence**: Automatically saves navigation state
- **History Tracking**: Maintains previous working directory
- **ArxObject Integration**: Works with live ArxObject data

**Output:**
```bash
✅ Changed directory to: /floor-1/systems/electrical/panel-a
Current location: building:building-001/floor-1/systems/electrical/panel-a
📊 ArxObject: panel-a (electrical_panel)
🔌 Properties: voltage=480V, amperage=400A, status=active
```

---

### `arx ls` - List Directory Contents

Lists the contents of the current or specified directory with ArxObject intelligence.

**Usage:**
```bash
arx ls [path] [options]
```

**Options:**
- `-l, --long`: Long format with detailed ArxObject information
- `-t, --types`: Group entries by ArxObject type
- `--tree`: Display as tree structure
- `-a, --all`: Show all entries including hidden
- `--ascii`: Show ASCII art render of current location
- `--svg`: Show SVG BIM view of current location
- `--properties`: Show ArxObject properties
- `--status`: Show operational status

**Examples:**
```bash
# List current directory
arx ls

# List specific directory
arx ls /systems

# Long format with ArxObject details
arx ls -l

# Group by ArxObject type
arx ls -t

# Tree view
arx ls --tree

# Show ASCII art render
arx ls --ascii

# Show SVG BIM view
arx ls --svg

# Show ArxObject properties
arx ls --properties
```

**Output Formats:**

**Standard List:**
```bash
📁 floor-1/          # Floor directory
📁 floor-2/          # Floor directory
📁 systems/          # Systems directory
📄 arxos.yml         # Configuration file
```

**Long Format (`-l`):**
```bash
drwxr-xr-x  floor-1          floor     /floor-1          ArxObject: floor-1
drwxr-xr-x  floor-2          floor     /floor-2          ArxObject: floor-2
drwxr-xr-x  systems          system    /systems          ArxObject: systems
-rw-r--r--  arxos.yml        file      /arxos.yml        Configuration
```

**Type Grouping (`-t`):**
```bash
📁 FLOORS:
  floor-1/          /floor-1          ArxObject: floor-1
  floor-2/          /floor-2          ArxObject: floor-2

📁 SYSTEMS:
  systems/           /systems          ArxObject: systems

📄 FILES:
  arxos.yml          /arxos.yml        Configuration
```

**ASCII Art Render (`--ascii`):**
```bash
🔬 Current Location: /floor-1/systems/electrical/panel-a

ASCII Render (Room Detail - 1 char = 0.01m):
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    ╔═══════════╗                       │
│                    ║  PANEL A  ║                       │
│                    ║  480V     ║                       │
│                    ║  400A     ║                       │
│                    ╚═══════════╝                       │
│                                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                  │
│  │ C1  │  │ C2  │  │ C3  │  │ C4  │                  │
│  │20A  │  │20A  │  │20A  │  │20A  │                  │
│  └─────┘  └─────┘  └─────┘  └─────┘                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### `arx tree` - Display Directory Tree

Displays the directory structure as a hierarchical tree with ArxObject information.

**Usage:**
```bash
arx tree [path] [options]
```

**Options:**
- `-d, --depth <n>`: Limit tree depth (default: 3)
- `-c, --compact`: Compact display mode
- `-a, --all`: Show all entries including hidden
- `--ascii`: Show ASCII art render at each level
- `--properties`: Show ArxObject properties in tree

**Examples:**
```bash
# Show current directory tree
arx tree

# Show specific directory tree
arx tree /systems

# Limit depth to 2 levels
arx tree -d 2

# Compact mode
arx tree -c

# Show ASCII art at each level
arx tree --ascii
```

**Output:**
```bash
📁 /
├── 📁 floor-1/ (ArxObject: floor-1)
│   ├── 📁 systems/ (ArxObject: systems)
│   │   ├── 📁 electrical/ (ArxObject: electrical_system)
│   │   │   ├── 📄 panel-a.yaml (ArxObject: panel-a)
│   │   │   └── 📄 panel-b.yaml (ArxObject: panel-b)
│   │   └── 📁 hvac/ (ArxObject: hvac_system)
│   │       ├── 📄 unit-1.yaml (ArxObject: hvac_unit_1)
│   │       └── 📄 ductwork.yaml (ArxObject: ductwork)
│   └── 📁 floor-plan.pdf
├── 📁 floor-2/ (ArxObject: floor-2)
└── 📄 arxos.yml
```

---

## 🔍 **Infinite Zoom Commands**

### `arx zoom`

Zoom to specific levels in the infinite zoom system, from campus to nanoscopic.

**Usage:**
```bash
arx zoom [level] [options]
```

**Available Levels:**
- `campus`: Campus overview (1 char = 100m)
- `site`: Site plan (1 char = 10m)
- `building`: Building outline (1 char = 1m)
- `floor`: Floor plan (1 char = 0.1m)
- `room`: Room detail (1 char = 0.01m)
- `furniture`: Furniture layout (1 char = 0.001m)
- `equipment`: Equipment detail (1 char = 0.0001m)
- `component`: Component detail (1 char = 0.00001m)
- `detail`: Micro detail (1 char = 0.000001m)
- `submicron`: Submicron detail (1 char = 0.0000001m)
- `nanoscopic`: Nanoscopic detail (1 char = 0.00000001m)

**Options:**
- `-s, --smooth`: Smooth transition (default: true)
- `--ascii`: Show ASCII art render at zoom level
- `--svg`: Show SVG BIM view at zoom level
- `--info`: Show zoom level information

**Examples:**
```bash
# Zoom to campus level
arx zoom campus

# Zoom to room detail
arx zoom room

# Zoom to submicron level
arx zoom submicron

# Smooth zoom to equipment detail
arx zoom equipment --smooth

# Show ASCII art at zoom level
arx zoom floor --ascii

# Show zoom information
arx zoom building --info
```

**Output:**
```bash
🔬 Zoomed to campus level
📏 Scale: 1 char = 100m
🎯 Precision: kilometer
📝 Description: Campus overview

ASCII Render (Campus View - 1 char = 100m):
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    ╔═══════════╗                       │
│                    ║ BUILDING  ║                       │
│                    ║    47     ║                       │
│                    ╚═══════════╝                       │
│                                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                  │
│  │  A  │  │  B  │  │  C  │  │  D  │                  │
│  │     │  │     │  │     │  │     │                  │
│  └─────┘  └─────┘  └─────┘  └─────┘                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔍 **Search and Query Commands**

### `arx find`

Search for building ArxObjects using text, filters, and advanced queries.

**Usage:**
```bash
arx find [query] [options]
```

**Options:**
- `-l, --limit <n>`: Maximum number of results (default: 50)
- `-f, --format <format>`: Output format (table, json, csv, ascii)
- `--type <type>`: Filter by ArxObject type
- `--status <status>`: Filter by operational status
- `--confidence <min>`: Minimum confidence threshold
- `--floor <n>`: Filter by floor number
- `--system <system>`: Filter by building system

**Query Syntax:**
```bash
Text Search:     "search term"              # Search in names and descriptions
Type Filter:     type:floor                 # Filter by ArxObject type
Status Filter:   status:active              # Filter by status
Path Filter:     path:/systems/*            # Filter by path pattern
Property Filter: voltage:480V               # Filter by property values
Confidence:      confidence:>0.8            # Filter by confidence
Wildcard:        *                          # Find all ArxObjects
```

**Examples:**
```bash
# Find all electrical ArxObjects
arx find "electrical"

# Find all floors
arx find type:floor

# Find active systems
arx find status:active

# Find objects in systems directory
arx find path:/systems/*

# Find high-confidence objects
arx find confidence:>0.8

# Combined search
arx find "hvac" type:system status:active

# Find all objects (limit results)
arx find * --limit 10

# JSON output
arx find type:floor --format json

# ASCII art output
arx find status:active --format ascii
```

**Output Formats:**

**Table Format (default):**
```bash
Name                                    Type           Path                         Metadata
---------------------------------------- --------------- ---------------------------- ------------------------------------------------
Electrical Panel A                      electrical_panel /systems/electrical/panel-a  status=active;voltage=480V;confidence=0.95
HVAC Unit 1                             hvac_unit      /systems/hvac/unit-1         status=active;capacity=5ton;confidence=0.92
Floor 1                                 floor          /floor-1                      level=1;area=10000sqft;confidence=0.98
```

**ASCII Art Format:**
```bash
🔍 Search Results for "electrical" (3 ArxObjects found)

ASCII Render (Room Detail - 1 char = 0.01m):
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                  │
│  │PANEL│  │PANEL│  │PANEL│  │PANEL│                  │
│  │  A  │  │  B  │  │  C  │  │  D  │                  │
│  │480V │  │480V │  │480V │  │480V │                  │
│  └─────┘  └─────┘  └─────┘  └─────┘                  │
│                                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                  │
│  │OUTLET│  │OUTLET│  │OUTLET│  │OUTLET│                  │
│  │  1   │  │  2   │  │  3   │  │  4   │                  │
│  │ 120V │  │ 120V │  │ 120V │  │ 120V │                  │
│  └─────┘  └─────┘  └─────┘  └─────┘                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🗂️ **ArxObject Management Commands**

### `arx arxobject`

Manage ArxObjects in the building with advanced capabilities.

**Command Structure:**
```bash
arx arxobject [command] [options]
```

**Available Commands:**
- `show`: Display detailed ArxObject information
- `validate`: Validate ArxObjects with evidence and confidence
- `relate`: Manage relationships between ArxObjects
- `lifecycle`: Manage ArxObject lifecycle status and phases
- `search`: Search ArxObjects with advanced filtering
- `stats`: Display comprehensive ArxObject statistics
- `export`: Export ArxObjects to various formats

#### `arx arxobject show [object-id]`

Display detailed information about an ArxObject.

**Features:**
- Complete ArxObject metadata display
- Properties and custom attributes
- Relationship information
- Validation history and confidence scores
- Location and spatial data
- Tags and flags

**Examples:**
```bash
arx arxobject show building:main
arx arxobject show building:main:floor:1
arx arxobject show building:main:system:electrical
arx arxobject show building:main:system:electrical:panel-a
```

**Output:**
```bash
🔍 ArxObject: building:main:system:electrical:panel-a

📊 Basic Information:
   Type: electrical_panel
   Name: Panel A
   Description: 480V 3-phase main electrical panel
   Status: active
   Confidence: 0.95

📍 Spatial Information:
   Position: (10.0m, 5.0m, 0.0m)
   Dimensions: (0.8m, 1.2m, 0.2m)
   Floor: 1
   Room: electrical-room-101

🔌 Electrical Properties:
   Voltage: 480V
   Amperage: 400A
   Phases: 3
   Manufacturer: Schneider Electric
   Model: Square-D
   Installation Date: 2024-01-15

📋 Properties:
   maintenance_cycle: annual
   last_inspection: 2024-01-15
   next_inspection: 2025-01-15
   load_percentage: 65.5
   temperature: 42.3°C
   humidity: 35.2%

🔗 Relationships:
   Contains: 24 circuits
   Connected to: main-transformer
   Located in: electrical-room-101
   Serves: floor-1-loads

📈 Validation History:
   2024-01-15: Field validation (confidence: 0.95)
   2024-01-10: Photo validation (confidence: 0.92)
   2024-01-05: LiDAR validation (confidence: 0.98)
```

#### `arx arxobject validate [object-id]`

Validate an ArxObject with evidence and confidence scoring.

**Features:**
- Multiple validation methods (photo, lidar, manual, etc.)
- Confidence scoring (0.0 to 1.0)
- Evidence tracking and file attachments
- Validation history and audit trail
- Automatic confidence updates

**Examples:**
```bash
arx arxobject validate building:main:floor:1 --method photo --confidence 0.9
arx arxobject validate building:main:system:hvac --method lidar --confidence 0.95 --by "field_engineer"
arx arxobject validate building:main:room:101 --method manual --confidence 0.8 --notes "Field inspection completed"
```

**Flags:**
- `--method`: Validation method (photo, lidar, manual, etc.)
- `--confidence`: Confidence level (0.0 to 1.0)
- `--by`: Who performed the validation
- `--notes`: Validation notes and comments
- `--evidence`: Evidence file path or URL

**Output:**
```bash
✅ ArxObject validated successfully!

🔍 Validation Details:
   Object: building:main:system:electrical:panel-a
   Method: Photo validation
   Confidence: 0.95
   Validated by: field_engineer_001
   Date: 2024-01-15 14:30:00
   Notes: Panel A verified in field with photo evidence

📊 Confidence Update:
   Previous confidence: 0.92
   New confidence: 0.95
   Improvement: +0.03

📈 Validation History:
   2024-01-15: Photo validation (confidence: 0.95) - field_engineer_001
   2024-01-10: Photo validation (confidence: 0.92) - field_engineer_002
   2024-01-05: LiDAR validation (confidence: 0.98) - lidar_system_001

🎯 Next Steps:
   - Panel A is now field-validated
   - Confidence threshold met (0.95 > 0.8)
   - Ready for operational use
```

---

## 🔍 **AQL Query Commands**

### `arx query`

Execute Arxos Query Language (AQL) queries for building data operations.

**Usage:**
```bash
arx query [command] [options]
```

**Available Commands:**
- `select`: Execute SELECT queries on ArxObjects
- `update`: Update ArxObject properties
- `validate`: Mark objects as field-validated
- `history`: View object version history
- `diff`: Compare object versions
- `ask`: Ask questions in natural language
- `shell`: Start interactive AQL shell
- `navigate`: Navigate through building hierarchy
- `templates`: Show and use AQL query templates

#### `arx query ask [question]`

Ask questions in natural language and get AQL-powered answers.

**Features:**
- Natural language to AQL conversion
- Context-aware query understanding
- Confidence scoring for generated queries
- Support for HVAC, electrical, maintenance, and energy queries

**Examples:**
```bash
arx query ask "show me all HVAC equipment on the 3rd floor"
arx query ask "find all equipment that needs maintenance this week"
arx query ask --explain "what's the energy consumption of building A last month?"
arx query ask --context="building:hq" "show me electrical panels"
```

**Flags:**
- `--context`: Additional context for better query understanding
- `--format`: Output format (table, json, csv, ascii-bim, summary)
- `--explain`: Show the generated AQL query
- `--interactive`: Enable interactive mode for query refinement

**Output:**
```bash
🤖 Natural Language Query: "show me all HVAC equipment on the 3rd floor"

🔍 Generated AQL Query:
   SELECT * FROM building:main:floor:3 WHERE type IN ('hvac_unit', 'air_handler', 'vav_box', 'chiller', 'boiler')

📊 Query Results (5 ArxObjects found):

1. HVAC Unit 1 (hvac_unit)
   - Location: /floor-3/room-301
   - Status: active
   - Capacity: 5 tons
   - Confidence: 0.92

2. Air Handler 1 (air_handler)
   - Location: /floor-3/mechanical-room
   - Status: active
   - Airflow: 20,000 CFM
   - Confidence: 0.95

3. VAV Box 1 (vav_box)
   - Location: /floor-3/room-302
   - Status: active
   - Airflow: 500-2000 CFM
   - Confidence: 0.88

4. VAV Box 2 (vav_box)
   - Location: /floor-3/room-303
   - Status: active
   - Airflow: 500-2000 CFM
   - Confidence: 0.88

5. Chiller 1 (chiller)
   - Location: /floor-3/mechanical-room
   - Status: active
   - Capacity: 200 tons
   - Confidence: 0.95

🎯 Summary:
   - Total HVAC equipment: 5 units
   - All equipment is active
   - Average confidence: 0.92
   - Equipment types: hvac_unit, air_handler, vav_box, chiller
```

---

## 📊 **Real-time Monitoring Commands**

### `arx monitor`

Monitor ArxObjects in real-time for updates and changes.

**Usage:**
```bash
arx monitor [path] [options]
```

**Options:**
- `--watch`: Watch for changes continuously
- `--interval <duration>`: Update interval (default: 1s)
- `--format <format>`: Output format (text, json, csv, ascii)
- `--alerts`: Enable alert system
- `--dashboard`: Start live dashboard mode
- `--refresh <duration>`: Refresh rate for dashboard mode

**Examples:**
```bash
# Monitor current location
arx monitor

# Monitor specific path
arx monitor /systems/electrical

# Watch for changes continuously
arx monitor --watch

# Set 5-second update interval
arx monitor --interval 5s

# Start dashboard mode
arx monitor --dashboard

# Show ASCII art updates
arx monitor --format ascii
```

**Output:**
```bash
🔍 Monitoring: /systems/electrical/panel-a

📊 Real-time Status:
   Time: 2024-01-15 14:35:00
   Status: active
   Load: 65.5%
   Temperature: 42.3°C
   Humidity: 35.2%
   Voltage A: 480.2V
   Voltage B: 479.8V
   Voltage C: 480.1V
   Current A: 260.5A
   Current B: 258.9A
   Current C: 259.7A

⚠️  Alerts:
   - Temperature approaching limit (42.3°C > 40°C threshold)
   - Load percentage high (65.5% > 60% threshold)

📈 Trends:
   - Temperature: ↗️ +2.1°C (last 5 minutes)
   - Load: ↗️ +1.2% (last 5 minutes)
   - Voltage: Stable (±0.2V)

🎯 Recommendations:
   - Monitor temperature trend
   - Consider load balancing
   - Schedule maintenance if trends continue
```

---

## 🔗 **Related Documentation**

- **Vision**: [Platform Vision](../../vision.md)
- **Architecture**: [Current Architecture](../current-architecture.md)
- **ASCII-BIM**: [ASCII-BIM Engine](../architecture/ascii-bim.md)
- **ArxObjects**: [ArxObject System](../architecture/arxobjects.md)
- **CLI Architecture**: [CLI Architecture](../architecture/cli-architecture.md)
- **Workflows**: [PDF to 3D Pipeline](../workflows/pdf-to-3d.md)

---

## 🆘 **Getting Help**

- **Architecture Questions**: Review [Current Architecture](../current-architecture.md)
- **C Development**: Check [Core C Engine](../core/c/README.md)
- **Go Development**: Review [Go Services](../core/README.md)
- **CLI Issues**: Test with [Enhanced Zoom Demo](../frontend/demo-enhanced-zoom.html)

**Happy building! 🏗️✨**
