# ArxOS Architecture Diagrams

Visual documentation of ArxOS system architecture, data flows, and module relationships.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Flow Diagrams](#data-flow-diagrams)
3. [Module Dependencies](#module-dependencies)
4. [Workflow Diagrams](#workflow-diagrams)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ArxOS System                            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │    CLI     │  │  Mobile    │  │   Web UI   │            │
│  │ Interface  │  │    App     │  │  (Future)  │            │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘            │
│         │                │                │                   │
│         └────────────────┴────────────────┘                   │
│                         │                                     │
│              ┌──────────▼──────────┐                         │
│              │   Commands Layer    │                         │
│              │  (Command Handlers) │                         │
│              └──────────┬──────────┘                         │
│                         │                                     │
│              ┌──────────▼──────────┐                         │
│              │  Operations Layer   │                         │
│              │  (Business Logic)   │                         │
│              └──────────┬──────────┘                         │
│                         │                                     │
│         ┌───────────────┼───────────────┐                   │
│         │               │               │                   │
│    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐              │
│    │  Core   │    │  YAML   │    │   Git   │              │
│    │  Types  │    │ Persist │    │ Manager │              │
│    └────┬────┘    └────┬────┘    └────┬────┘              │
│         │               │               │                   │
│         └───────────────┴───────────────┘                   │
│                         │                                     │
│              ┌──────────▼──────────┐                         │
│              │   File System       │                         │
│              │   (YAML + .git/)    │                         │
│              └─────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Presentation Layer:**
- CLI commands, TUI interfaces, mobile apps
- User input validation
- Display formatting

**Command Layer:**
- Command routing and parsing
- High-level workflow orchestration
- Error presentation

**Operations Layer:**
- Business logic
- Data validation
- Workflow implementation

**Data Layer:**
- YAML serialization
- Git operations
- File system access

---

## Data Flow Diagrams

### 1. Import Building Workflow

```
┌─────────┐         ┌────────────┐         ┌──────────┐
│   IFC   │────────▶│    IFC     │────────▶│  Parse   │
│  File   │         │  Parser    │         │  Result  │
└─────────┘         └────────────┘         └────┬─────┘
                                                 │
                                                 │
                                           ┌─────▼─────┐
                                           │  Convert  │
                                           │    to     │
                                           │ Building  │
                                           │   Data    │
                                           └─────┬─────┘
                                                 │
                                                 │
                    ┌────────────────────────────┤
                    │                            │
              ┌─────▼─────┐              ┌──────▼──────┐
              │   YAML    │              │     Git     │
              │ Serialize │              │   Commit    │
              └─────┬─────┘              └──────┬──────┘
                    │                            │
                    └────────────┬───────────────┘
                                 │
                          ┌──────▼──────┐
                          │    File     │
                          │   System    │
                          │  building.  │
                          │    yaml     │
                          └─────────────┘
```

### 2. Equipment Management Workflow

```
┌──────────┐      ┌────────────┐      ┌──────────┐      ┌─────────┐
│   User   │─────▶│  Command   │─────▶│Operations│─────▶│  Load   │
│  Input   │      │  Handler   │      │  Layer   │      │  YAML   │
└──────────┘      └────────────┘      └──────────┘      └────┬────┘
                                                              │
                                                              │
                                                     ┌────────▼────────┐
                                                     │  BuildingData   │
                                                     │   (in memory)   │
                                                     └────────┬────────┘
                                                              │
                                                     ┌────────▼────────┐
                                                     │     Modify      │
                                                     │   (add/edit/    │
                                                     │    delete)      │
                                                     └────────┬────────┘
                                                              │
                                           ┌──────────────────┴──────────────────┐
                                           │                                     │
                                      ┌────▼────┐                        ┌──────▼──────┐
                                      │  YAML   │                        │     Git     │
                                      │ Serialize│                       │    Commit   │
                                      │  & Save │                        │  (optional) │
                                      └────┬────┘                        └──────┬──────┘
                                           │                                     │
                                           └──────────────┬──────────────────────┘
                                                         │
                                                  ┌──────▼──────┐
                                                  │  File System│
                                                  │  (updated)  │
                                                  └─────────────┘
```

### 3. AR Integration Workflow

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│  Mobile  │──────▶│    AR    │──────▶│ Detected │
│   App    │       │   Scan   │       │Equipment │
│ (iOS/    │       │          │       │   JSON   │
│ Android) │       │          │       │          │
└──────────┘       └──────────┘       └────┬─────┘
                                            │
                                            │ Upload/Sync
                                            │
                                      ┌─────▼─────┐
                                      │  Process  │
                                      │  AR Scan  │
                                      └─────┬─────┘
                                            │
                                   ┌────────┴────────┐
                                   │                 │
                            ┌──────▼──────┐   ┌──────▼──────┐
                            │   Validate  │   │   Create    │
                            │  Confidence │   │   Pending   │
                            │  Threshold  │   │  Equipment  │
                            └──────┬──────┘   └──────┬──────┘
                                   │                 │
                                   └────────┬────────┘
                                            │
                                     ┌──────▼──────┐
                                     │   Pending   │
                                     │  Equipment  │
                                     │   Manager   │
                                     └──────┬──────┘
                                            │
                                   ┌────────┴────────┐
                                   │                 │
                            ┌──────▼──────┐   ┌──────▼──────┐
                            │Desktop Review│  │   Confirm/  │
                            │  (arx ar    │   │   Reject    │
                            │   pending)  │   │             │
                            └──────┬──────┘   └──────┬──────┘
                                   │                 │
                                   └────────┬────────┘
                                            │
                                     ┌──────▼──────┐
                                     │   Add to    │
                                     │  Building   │
                                     │    Data     │
                                     └──────┬──────┘
                                            │
                                     ┌──────▼──────┐
                                     │ Git Commit  │
                                     └─────────────┘
```

### 4. Export Workflow

```
┌──────────────┐       ┌─────────────┐       ┌──────────┐
│  Building    │──────▶│   Select    │──────▶│  Format  │
│    Data      │       │   Export    │       │ Exporter │
│ (YAML/Git)   │       │   Format    │       │          │
└──────────────┘       └─────────────┘       └────┬─────┘
                                                   │
                                  ┌────────────────┼────────────────┐
                                  │                │                │
                           ┌──────▼──────┐  ┌──────▼──────┐  ┌────▼─────┐
                           │     IFC     │  │     AR      │  │   Docs   │
                           │  Exporter   │  │  (glTF/USDZ)│  │  (HTML)  │
                           └──────┬──────┘  └──────┬──────┘  └────┬─────┘
                                  │                │                │
                           ┌──────▼──────┐  ┌──────▼──────┐  ┌────▼─────┐
                           │Delta Tracking│ │   Mesh      │  │ Template │
                           │Sync State   │  │ Generation  │  │  Engine  │
                           └──────┬──────┘  └──────┬──────┘  └────┬─────┘
                                  │                │                │
                                  └────────────────┼────────────────┘
                                                   │
                                            ┌──────▼──────┐
                                            │   Output    │
                                            │    File     │
                                            │   (.ifc,    │
                                            │  .gltf,     │
                                            │  .usdz,     │
                                            │   .html)    │
                                            └─────────────┘
```

---

## Module Dependencies

### Core Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                        main.rs / lib.rs                      │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
    │   CLI   │     │Commands │    │   UI    │
    │         │     │         │    │  (TUI)  │
    └────┬────┘     └────┬────┘    └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                    ┌────▼────┐
                    │  Core   │
                    │Operations│
                    └────┬────┘
                         │
         ┌───────────────┼───────────────────────────┐
         │               │               │           │
    ┌────▼────┐     ┌────▼────┐    ┌────▼────┐ ┌───▼───┐
    │  Core   │     │  YAML   │    │   Git   │ │Spatial│
    │  Types  │     │         │    │ Manager │ │       │
    └────┬────┘     └────┬────┘    └────┬────┘ └───────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
                   ┌─────▼─────┐
                   │Persistence│
                   │ Manager   │
                   └─────┬─────┘
                         │
                   ┌─────▼─────┐
                   │   File    │
                   │  System   │
                   └───────────┘
```

### Module Interaction Matrix

| Module | Depends On | Used By |
|--------|-----------|---------|
| **core/types** | spatial, serde | core/operations, commands, UI |
| **core/operations** | persistence, core/types | commands |
| **persistence** | yaml, git, filesystem | operations, commands |
| **yaml** | core/types, serde | persistence, export |
| **git** | git2, persistence | persistence |
| **commands** | operations, core | CLI, UI |
| **ui** | commands, core/types | main |
| **export** | core/types, yaml | commands |
| **ar_integration** | core/types, persistence | commands, mobile_ffi |
| **mobile_ffi** | ar_integration, core | iOS/Android apps |

---

## Data Flow Diagrams

### Building Data Lifecycle

```
┌───────────────────────────────────────────────────────────────┐
│                    BUILDING DATA LIFECYCLE                     │
└───────────────────────────────────────────────────────────────┘

CREATION:
  Import IFC  ──┐
  Manual Init ──┼──▶ BuildingData ──▶ YAML Serialize ──▶ File System
  AR Scan     ──┘                                            │
                                                             │
                                                          Git Init
                                                             │
                                                             ▼
                                                      .git/repository

MODIFICATION:
  User Edit   ──┐
  AR Confirm  ──┼──▶ Load YAML ──▶ Modify ──▶ Save YAML ──▶ Git Commit
  Spreadsheet ──┘         │                        │
                          │                        │
                    (BuildingData)           (Updated File)

QUERY/VIEW:
  List        ──┐
  Search      ──┼──▶ Load YAML ──▶ Query/Filter ──▶ Display
  Render      ──┤         │
  Dashboard   ──┘   (Read-Only)
  Export      ──────────┘

EXPORT:
  IFC         ──┐
  glTF/USDZ   ──┼──▶ Load YAML ──▶ Transform ──▶ Write Output
  HTML Docs   ──┘
```

### Git Integration Flow

```
┌────────────┐         ┌─────────────┐         ┌──────────┐
│   User     │────────▶│  Operation  │────────▶│   Load   │
│   Action   │         │   Handler   │         │   YAML   │
└────────────┘         └─────────────┘         └────┬─────┘
                                                     │
                                              ┌──────▼──────┐
                                              │ BuildingData│
                                              │ (modified)  │
                                              └──────┬──────┘
                                                     │
                          ┌──────────────────────────┼──────────────────────────┐
                          │                          │                          │
                    ┌─────▼─────┐           ┌────────▼────────┐        ┌───────▼───────┐
                    │   Commit  │           │   Serialize     │        │   Update      │
                    │  Flag?    │           │   to YAML       │        │   Metadata    │
                    └─────┬─────┘           └────────┬────────┘        └───────┬───────┘
                          │                          │                          │
                      Yes │                          │                          │
                          │                          ▼                          │
                    ┌─────▼─────┐           ┌────────────────┐                 │
                    │    Git    │◀──────────│  Write File    │◀────────────────┘
                    │   Stage   │           │  (building.    │
                    └─────┬─────┘           │     yaml)      │
                          │                 └────────────────┘
                    ┌─────▼─────┐
                    │    Git    │
                    │   Commit  │
                    │ (message) │
                    └───────────┘
```

### AR Scan Processing Flow

```
Mobile Device                    Server/Desktop                   Storage
─────────────                   ──────────────                   ────────

┌──────────┐
│  Camera  │
│   Scan   │
└────┬─────┘
     │
     │ ARKit/ARCore
     │ Detection
     ▼
┌──────────┐
│Detected  │
│Equipment │
│   JSON   │
└────┬─────┘
     │
     │ Upload/
     │ Transfer
     ▼
                               ┌──────────┐
                               │ Validate │
                               │AR Scan   │
                               │   Data   │
                               └────┬─────┘
                                    │
                                    │ Confidence
                                    │ Filtering
                                    ▼
                               ┌──────────┐
                               │  Create  │
                               │ Pending  │
                               │Equipment │
                               └────┬─────┘
                                    │
                                    │ Save
                                    ▼
                                                               ┌──────────┐
                                                               │ pending- │
                                                               │equipment │
                                                               │  .json   │
                                                               └────┬─────┘
                                                                    │
Desktop Review:                                                     │ Load
                               ┌──────────┐                         │
                               │Interactive│◀────────────────────────┘
                               │  Review  │
                               │   (TUI)  │
                               └────┬─────┘
                                    │
                          ┌─────────┴─────────┐
                          │                   │
                     ┌────▼────┐         ┌────▼────┐
                     │ Confirm │         │ Reject  │
                     └────┬────┘         └────┬────┘
                          │                   │
                          │                   │
                     ┌────▼────┐              │
                     │  Add to │              │
                     │Building │              │
                     │  Data   │              │
                     └────┬────┘              │
                          │                   │
                     ┌────▼────┐         ┌────▼────┐
                     │   Git   │         │ Remove  │
                     │  Commit │         │ Pending │
                     └─────────┘         └─────────┘
```

---

## Module Dependencies

### Dependency Layers (Bottom-Up)

**Layer 1: Foundation** (No dependencies)
- `spatial` - Point3D, BoundingBox3D, coordinate systems
- `error` - Error types and handling

**Layer 2: Data Structures**
- `core/types` - Position, Dimensions, BoundingBox, SpatialProperties
  - Depends on: spatial
- `domain` - ArxAddress, GUID generation
  - Depends on: spatial

**Layer 3: Core Business Objects**
- `core` - Building, Floor, Wing, Room, Equipment
  - Depends on: core/types, spatial, domain

**Layer 4: Serialization & Storage**
- `yaml` - YAML serialization
  - Depends on: core, spatial, serde
- `git` - Git operations
  - Depends on: git2
- `persistence` - File operations, caching
  - Depends on: yaml, git, filesystem

**Layer 5: Business Logic**
- `core/operations` - Business operations
  - Depends on: core, persistence
- `ifc` - IFC parsing
  - Depends on: core, spatial
- `export` - Export to various formats
  - Depends on: core, yaml

**Layer 6: Application Services**
- `ar_integration` - AR workflows
  - Depends on: core, persistence
- `hardware` - Sensor integration
  - Depends on: core
- `search` - Search engine
  - Depends on: core
- `query` - Address queries
  - Depends on: domain, core

**Layer 7: User Interface**
- `commands` - Command handlers
  - Depends on: operations, core, export, ar_integration
- `ui` - TUI components
  - Depends on: core, ratatui, crossterm

**Layer 8: Entry Points**
- `main.rs` - CLI application
  - Depends on: cli, commands, ui
- `mobile_ffi` - Mobile FFI
  - Depends on: ar_integration, core

### Coupling Strength

| Module Pair | Coupling | Type | Assessment |
|-------------|----------|------|------------|
| operations ↔ persistence | High | Necessary | ✅ Appropriate |
| commands ↔ operations | Medium | Logical | ✅ Good |
| ui ↔ commands | Medium | Logical | ✅ Good |
| core ↔ spatial | Low | Structural | ✅ Excellent |
| yaml ↔ core | Medium | Necessary | ✅ Appropriate |
| git ↔ persistence | High | Necessary | ✅ Appropriate |

---

## Workflow Diagrams

### Complete User Workflow: Import to Export

```
START
  │
  ▼
┌──────────────┐
│Import IFC    │  arx import building.ifc
│File          │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Parse & Load  │  IFC Parser extracts structure
│              │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Create YAML + │  building.yaml + .git/
│Git Repo      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│View/Edit     │  arx spreadsheet equipment
│              │  arx render --three-d
└──────┬───────┘
       │
       ▼
┌──────────────┐
│AR Field Scan │  Mobile app scans equipment
│(Optional)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Review Pending│  arx ar pending
│Equipment     │  Confirm/reject detections
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Validate Data │  arx doctor
│              │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Export        │  arx export ifc --output final.ifc
│              │  arx export ar --format gltf
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Share/Deliver │  Git push or file distribution
│              │
└──────────────┘
  │
  ▼
END
```

### Spreadsheet Edit Workflow

```
User Opens Spreadsheet
         │
         ▼
┌─────────────────┐
│  Load Building  │  Read YAML from file
│      Data       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Grid     │  Create spreadsheet rows/columns
│   Structure     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Interactive   │  User edits cells
│     Editing     │  ↑/↓/←/→, Enter, Esc
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validation     │  Check data types, constraints
│                 │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Valid?  │
    └────┬────┘
         │
    No   │   Yes
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────────────┐
│Show  │  │  Update      │
│Error │  │ BuildingData │
└──────┘  └──────┬───────┘
              │
              ▼
         ┌──────────────┐
         │Save YAML     │  Write to file
         └──────┬───────┘
                │
           ┌────▼────┐
           │Auto-    │
           │Commit?  │
           └────┬────┘
                │
           Yes  │  No
           ┌────┴────┐
           │         │
           ▼         ▼
      ┌────────┐  ┌──────┐
      │  Git   │  │ Done │
      │ Commit │  └──────┘
      └────┬───┘
           │
           ▼
      ┌──────┐
      │ Done │
      └──────┘
```

---

## Data Model Hierarchy

### Building Data Structure

```
BuildingData
│
├─ building: BuildingInfo
│  ├─ id: String
│  ├─ name: String
│  ├─ description: Option<String>
│  ├─ created_at: DateTime
│  ├─ updated_at: DateTime
│  └─ version: String
│
├─ metadata: BuildingMetadata
│  ├─ source_file: Option<String>
│  ├─ parser_version: String
│  ├─ total_entities: usize
│  ├─ spatial_entities: usize
│  ├─ coordinate_system: String
│  ├─ units: String
│  └─ tags: Vec<String>
│
├─ floors: Vec<Floor>
│  │
│  └─ Floor
│     ├─ id: String
│     ├─ name: String
│     ├─ level: i32
│     ├─ elevation: Option<f64>
│     ├─ bounding_box: Option<BoundingBox3D>
│     │
│     ├─ wings: Vec<Wing>
│     │  │
│     │  └─ Wing
│     │     ├─ id: String
│     │     ├─ name: String
│     │     │
│     │     ├─ rooms: Vec<Room>
│     │     │  │
│     │     │  └─ Room
│     │     │     ├─ id: String
│     │     │     ├─ name: String
│     │     │     ├─ room_type: RoomType
│     │     │     ├─ spatial_properties: SpatialProperties
│     │     │     ├─ equipment: Vec<Equipment>
│     │     │     └─ properties: HashMap
│     │     │
│     │     └─ equipment: Vec<Equipment>
│     │
│     ├─ equipment: Vec<Equipment> (floor-level)
│     │  │
│     │  └─ Equipment
│     │     ├─ id: String
│     │     ├─ name: String
│     │     ├─ path: String (Universal Path)
│     │     ├─ address: Option<ArxAddress>
│     │     ├─ equipment_type: EquipmentType
│     │     ├─ position: Position
│     │     ├─ status: EquipmentStatus
│     │     ├─ health_status: Option<EquipmentHealthStatus>
│     │     ├─ room_id: Option<String>
│     │     ├─ sensor_mappings: Option<Vec<SensorMapping>>
│     │     └─ properties: HashMap
│     │
│     └─ properties: HashMap
│
└─ coordinate_systems: Vec<CoordinateSystemInfo>
```

---

## Component Interaction Diagrams

### Persistence Layer Interaction

```
┌─────────────────────────────────────────────────────────┐
│               Persistence Architecture                   │
└─────────────────────────────────────────────────────────┘

Operations Layer:
  create_room(), add_equipment(), etc.
         │
         ▼
┌──────────────────┐
│ PersistenceManager│
│                   │
│ • load_building_data()
│ • save_building_data()
│ • save_and_commit()
│ • Caching (LRU)
│                   │
└─────────┬─────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌────────┐  ┌──────────┐
│  YAML  │  │   Git    │
│Serializer│ │ Manager  │
└────┬───┘  └────┬─────┘
     │           │
     └─────┬─────┘
           │
      ┌────▼────┐
      │  File   │
      │ System  │
      │         │
      │building.│
      │  yaml   │
      │  .git/  │
      └─────────┘
```

### UI Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    UI Architecture                       │
└─────────────────────────────────────────────────────────┘

Terminal:
  ratatui + crossterm
         │
         ▼
┌──────────────────┐
│   UI Manager     │
│  (Router/State)  │
└─────────┬────────┘
          │
    ┌─────┴─────────────────────┐
    │                           │
    ▼                           ▼
┌──────────────┐        ┌──────────────┐
│  Dashboard   │        │  Spreadsheet │
│  Components  │        │   Editor     │
│              │        │              │
│• Status      │        │• Grid        │
│• Health      │        │• Editor      │
│• Watch       │        │• Filter/Sort │
└──────┬───────┘        │• Search      │
       │                └──────┬───────┘
       │                       │
    ┌──┴─────┐         ┌───────┴────┐
    │        │         │            │
    ▼        ▼         ▼            ▼
┌────────┐ ┌───────┐ ┌──────┐  ┌────────┐
│Widgets │ │Command│ │Data  │  │undo/   │
│        │ │Palette│ │Source│  │redo    │
│• Badge │ │       │ │      │  │        │
│• Card  │ │       │ │      │  │        │
└────────┘ └───────┘ └──────┘  └────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Commands   │
                   │   Layer     │
                   └─────────────┘
```

---

## Concurrency & Safety

### File Locking Strategy

```
Multiple Editors (Spreadsheet):

Editor 1                    File System                 Editor 2
────────                   ─────────────                ────────

Open File
    │
    ▼
Acquire Lock ───────────▶ .lock file created
    │                            │
    │                            │ (locked)
    │                            │
    │                            ◀──── Attempt Open
    │                                      │
Edit Data                              Blocked
    │                                  (shows error)
    │                                      │
Save & Release Lock ──────▶ .lock file deleted
                                          │
                                          ▼
                                     Retry Open
                                          │
                                   Acquire Lock
                                          │
                                      Edit Data
```

### Git Conflict Resolution

```
User A Changes              Git Repository           User B Changes
──────────────             ────────────────         ──────────────

Edit building.yaml                 │                Edit building.yaml
      │                            │                       │
      ▼                            │                       │
Commit (A1) ─────────────────────▶│                       │
                                   │◀─────────────── Commit (B1)
                                   │                       │
                             Conflict!                     │
                                   │                       │
                                   │──────▶ Conflict Detection
                                   │       (via Git)
                                   │                       │
Pull & Merge ◀───────────────────│                       │
      │                            │                       │
Resolve Conflicts                  │                       │
      │                            │                       │
Commit (A2) ─────────────────────▶│                       │
                                   │──────────────────▶ Pull (gets A2)
                                   │
                                 Synced
```

---

## Extension Points

### How to Extend ArxOS

**Adding New Equipment Types:**
1. Add variant to `EquipmentType` enum (src/core/equipment.rs)
2. Add mapping to IFC type (crates/arxos/crates/arxos/src/export/ifc/mapper.rs)
3. Add color for 3D rendering (src/render3d/mod.rs)
4. Update documentation

**Adding New Commands:**
1. Add handler to crates/arxui/crates/arxui/src/commands/
2. Add CLI definition to src/cli.rs
3. Add to command palette (src/ui/command_palette/commands.rs)
4. Add tests
5. Update CLI_REFERENCE.md

**Adding New Export Formats:**
1. Create exporter in crates/arxos/crates/arxos/src/export/<format>/
2. Implement traits if needed
3. Add CLI command
4. Add tests
5. Document in CLI_REFERENCE.md

---

## Performance Considerations

### Data Loading

```
┌─────────────┐
│  Load YAML  │  ~5-50ms for typical building
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Cache?    │  LRU cache holds recent buildings
└──────┬──────┘
       │
  Hit  │  Miss
  ┌────┴────┐
  │         │
  ▼         ▼
┌────┐  ┌──────┐
│Fast│  │Parse │
│<1ms│  │YAML  │
└────┘  └───┬──┘
            │
            ▼
       ┌────────┐
       │Deserial│
       │  ize   │
       └───┬────┘
           │
           ▼
    ┌──────────┐
    │ Building │
    │   Data   │
    └──────────┘
```

**Performance Characteristics:**
- **Small buildings** (< 100 items): < 10ms
- **Medium buildings** (100-1000 items): 10-50ms
- **Large buildings** (> 1000 items): 50-200ms
- **Cache hit**: < 1ms

---

## Error Handling Flow

```
User Action
    │
    ▼
┌─────────────┐
│  Command    │
│  Handler    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Operations  │
│   Layer     │
└──────┬──────┘
       │
    Error?
    ┌──┴──┐
    │     │
   Yes    No
    │     │
    ▼     ▼
┌───────┐ ┌──────┐
│ Error │ │Success│
│Context│ │      │
└───┬───┘ └──────┘
    │
    ▼
┌──────────────┐
│Error Analytics│  Track error frequency
│  Recording    │
└──────┬───────┘
    │
    ▼
┌──────────────┐
│Format Error  │  User-friendly message
│  Message     │  + suggestions
└──────┬───────┘
    │
    ▼
┌──────────────┐
│  Display to  │  Terminal output or
│     User     │  UI error modal
└──────────────┘
```

---

## Security Architecture

### Data Access Control

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
└─────────────────────────────────────────────────────────────┘

User Input
    │
    ▼
┌──────────────┐
│  Validation  │  • Sanitize building names
│    Layer     │  • Validate paths
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Path Safety   │  • Prevent ../.. attacks
│   Module     │  • Canonicalize paths
│              │  • Ensure within workspace
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Permissions  │  • Check file permissions
│    Check     │  • Verify write access
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  File I/O    │  Safe file operations
└──────────────┘
```

---

## Conclusion

ArxOS follows a **layered architecture** with:
- ✅ Clear separation of concerns
- ✅ Logical module dependencies
- ✅ Appropriate coupling levels
- ✅ Good extensibility
- ✅ Strong error handling

**Architecture Score: 9/10** - Well-designed and maintainable.

For more details, see:
- [Operations Module Review](development/OPERATIONS_MODULE_REVIEW.md)
- [API Reference](API_REFERENCE.md)
- [User Guide](core/USER_GUIDE.md)

