# ArxOS Architecture

## Vision
Buildings as queryable databases - navigate through building systems like a file system, query equipment with SQL.

## Core Concept
Every outlet, light, valve, and piece of equipment becomes part of a hierarchical data structure that can be:
- Navigated like a file system (`CD /electrical/circuits/15`)
- Queried like a database (`SELECT * FROM objects WHERE needs_repair = true`)
- Traced through connections (`TRACE outlet_2B UPSTREAM`)

## Current Implementation

### Project Structure
```
arxos/
├── src/
│   ├── main.rs        # Entry point and CLI
│   ├── models.rs      # Core data models
│   ├── database.rs    # PostgreSQL integration
│   ├── terminal.rs    # Terminal interface
│   └── query.rs       # Query engine
├── schema.sql         # Database schema
├── Cargo.toml         # Dependencies
└── README.md          # Documentation
```

### Core Components

#### 1. BuildingObject Model (`models.rs`)
- **Path**: Hierarchical filesystem-like paths (e.g., `/electrical/outlets/outlet_2B`)
- **Location**: 3D coordinates and mounting information
- **State**: Operational status, health, maintenance needs
- **Connections**: Relationships to other objects
- **Properties**: Flexible JSON for domain-specific data

#### 2. Terminal Interface (`terminal.rs`)
Primary user interface with commands:
- `CD` - Navigate the building hierarchy
- `LS` - List objects at current path
- `LOOK` - Describe current location
- `INSPECT` - Show detailed object information
- `TRACE` - Follow connections upstream/downstream
- `NEAR` - Find nearby objects
- `SELECT` - SQL-like queries

#### 3. Query Engine (`query.rs`)
Simple SQL-like query parser supporting:
- `WHERE` clauses with basic operators (`=`, `!=`, `LIKE`)
- Field filtering (type, status, health, properties)
- Boolean conditions (needs_repair = true)

#### 4. Database Layer (`database.rs`)
PostgreSQL integration:
- Building and object storage
- JSON fields for flexible properties
- Spatial data support (ready for PostGIS)

## Data Model

### Building Hierarchy
```
/building_42/
├── electrical/
│   ├── panels/
│   │   └── main/
│   ├── circuits/
│   │   └── 15/
│   └── outlets/
│       ├── outlet_2B_north
│       └── outlet_2B_south
├── spaces/
│   └── floor_2/
│       └── room_2B/
└── hvac/
    └── zones/
        └── zone_2/
```

### Object Structure
```rust
BuildingObject {
    id: UUID,
    path: String,              // "/electrical/outlets/outlet_2B"
    object_type: String,       // "outlet", "panel", "circuit"
    location: {
        space: String,         // "/spaces/floor_2/room_2B"
        x, y, z: float,       // Position in meters
        mounting: String       // "wall", "ceiling", "floor"
    },
    state: {
        status: String,        // "normal", "degraded", "failed"
        health: String,        // "good", "fair", "poor"
        needs_repair: bool,
        metrics: {}           // Key-value measurements
    },
    connections: [],          // Related objects
    properties: {}            // Domain-specific data
}
```

## Technology Stack

- **Language**: Rust
- **Database**: PostgreSQL
- **Terminal**: rustyline for CLI interaction
- **Serialization**: serde/serde_json
- **Async Runtime**: tokio
- **SQL**: sqlx

## Usage Flow

1. **Connect to Database**
   - Load building data from PostgreSQL
   
2. **Navigate Building**
   - Use `CD` to move through hierarchy
   - Use `LS` to explore contents
   
3. **Query Objects**
   - SQL-like queries to find equipment
   - Filter by type, status, location
   
4. **Inspect and Trace**
   - Detailed object information
   - Follow connections through systems

## Future Enhancements

- **Web Interface**: D3.js visualization (optional)
- **BILT Marketplace**: Trade building data access
- **IoT Integration**: Real-time sensor data
- **AR Support**: Augmented reality overlay
- **API Layer**: REST/WebSocket for external access

## Example Session

```
arxos:/> CD /spaces/floor_2/room_2B
arxos:/spaces/floor_2/room_2B> LS
  outlet_2B_north
  outlet_2B_south [NEEDS REPAIR]
  light_2B_ceiling

arxos:/spaces/floor_2/room_2B> INSPECT outlet_2B_south
Path:     /electrical/outlets/outlet_2B_south
Type:     outlet
Status:   degraded
Health:   fair
⚠ NEEDS REPAIR

arxos:/spaces/floor_2/room_2B> SELECT * FROM objects WHERE needs_repair = true
Found 1 objects:
  /electrical/outlets/outlet_2B_south - outlet (degraded)
```