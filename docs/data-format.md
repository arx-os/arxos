# Data Format

ArxOS building data format and Git storage structure.

---

## Overview

ArxOS stores all building data in **YAML files** under **Git version control**. This approach provides:

- **Human-readable** format (YAML)
- **Version control** (Git history)
- **Diff-friendly** structure (line-based changes)
- **Merge-capable** (Git merge tools)
- **Distributed** collaboration (Git workflows)

---

## Directory Structure

```
project/
├── building.yaml          # Main building data
├── .arxos/               # ArxOS metadata
│   ├── config.toml       # Local configuration
│   └── cache/            # Performance cache (optional)
└── .git/                 # Git repository
    ├── objects/
    ├── refs/
    └── ...
```

---

## building.yaml Schema

The main building file follows this hierarchical structure:

```yaml
id: "550e8400-e29b-41d4-a716-446655440000"
name: "Office Building"
path: "/usa/ny/manhattan/office-building"
created_at: "2025-01-15T10:30:00Z"
updated_at: "2025-01-15T14:45:00Z"

metadata:
  source_file: "building.ifc"
  parser_version: "2.0.0"
  total_entities: 1234
  spatial_entities: 456
  coordinate_system: "World"
  units: "meters"
  tags:
    - "commercial"
    - "hvac-enabled"

floors:
  - number: 1
    name: "Ground Floor"
    elevation: 0.0
    height: 4.2
    wings:
      - name: "North Wing"
        rooms:
          - name: "Lobby"
            room_type: "Lobby"
            area_sqm: 120.5
            equipment:
              - name: "HVAC-AHU-01"
                equipment_type: "HVAC"
                status: "operational"
                address: "/usa/ny/manhattan/office-building/floor-01/lobby/hvac-ahu-01"
                location:
                  x: 10.5
                  y: 5.2
                  z: 2.8
                properties:
                  manufacturer: "Carrier"
                  model: "AHU-5000"
                  install_date: "2020-03-15"
```

---

## Field Definitions

### Building Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String (UUID) | Yes | Unique building identifier |
| `name` | String | Yes | Human-readable building name |
| `path` | String | Yes | Universal path identifier |
| `created_at` | DateTime | Yes | Creation timestamp (ISO 8601) |
| `updated_at` | DateTime | Yes | Last modification timestamp |
| `metadata` | Object | No | Parser metadata and tags |
| `floors` | Array | Yes | List of floors |

### Floor Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | Integer | Yes | Floor number (can be negative for basements) |
| `name` | String | No | Human-readable floor name |
| `elevation` | Float | No | Height above ground (meters) |
| `height` | Float | No | Floor-to-ceiling height (meters) |
| `wings` | Array | Yes | List of wings/zones |

### Wing Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Wing/zone name |
| `rooms` | Array | Yes | List of rooms |

### Room Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Room name/identifier |
| `room_type` | String | Yes | Room type (Office, Lobby, Mechanical, etc.) |
| `area_sqm` | Float | No | Room area in square meters |
| `equipment` | Array | No | Equipment in the room |

### Equipment Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Equipment name/identifier |
| `equipment_type` | String | Yes | Type: HVAC, Electrical, Plumbing, etc. |
| `status` | String | No | Status: operational, maintenance, offline |
| `address` | String | No | ArxAddress path |
| `location` | Object | No | 3D coordinates (x, y, z) |
| `properties` | Object | No | Custom key-value properties |

---

## ArxAddress Format

Equipment uses **ArxAddress** for hierarchical addressing:

```
/country/state/city/building/floor/room/fixture
```

**Example:**
```
/usa/ny/manhattan/office-building/floor-01/lobby/hvac-ahu-01
```

This enables powerful query patterns:

```bash
# Find all boilers in mech rooms
arx query "/usa/ny/*/floor-*/mech/boiler-*"

# Find all equipment on floor 3
arx query "/usa/ny/manhattan/office-building/floor-03/*/*"
```

---

## Room Types

Supported room types:

- `Office` – Standard office space
- `Lobby` – Building entrance/reception
- `Mechanical` – Mechanical/equipment rooms
- `Electrical` – Electrical rooms
- `Storage` – Storage/warehouse
- `Restroom` – Bathrooms/facilities
- `Stairwell` – Stairs and emergency exits
- `Elevator` – Elevator shafts
- `Conference` – Meeting rooms
- `Kitchen` – Cafeteria/break rooms
- `Server` – Data center/server rooms
- `Parking` – Parking areas
- `Retail` – Retail/commercial spaces
- `Residential` – Living spaces
- `Other` – Miscellaneous/uncategorized

---

## Equipment Types

Supported equipment types:

- `HVAC` – Heating, ventilation, air conditioning
- `Electrical` – Electrical systems and panels
- `Plumbing` – Plumbing and water systems
- `Fire Safety` – Fire alarms, sprinklers, suppression
- `Security` – Access control, cameras, sensors
- `Lighting` – Lighting fixtures and controls
- `Elevator` – Elevator and escalator systems
- `Network` – Network and telecom equipment
- `AV` – Audio/visual equipment
- `Other` – Miscellaneous equipment

---

## Equipment Status

Standard status values:

- `operational` – Functioning normally
- `maintenance` – Under scheduled maintenance
- `degraded` – Functioning but with issues
- `offline` – Not functioning / powered off
- `alarm` – Active alarm state
- `unknown` – Status not available

---

## Metadata Fields

Optional metadata block:

```yaml
metadata:
  source_file: "original.ifc"           # Source IFC file
  parser_version: "2.0.0"               # ArxOS version used
  total_entities: 5432                  # Total IFC entities
  spatial_entities: 1234                # Spatial entities
  coordinate_system: "World"            # Coordinate system
  units: "meters"                       # Measurement units
  tags:                                 # Custom tags
    - "commercial"
    - "leed-certified"
```

---

## Git Storage

### Commits

Every change to `building.yaml` creates a Git commit:

```bash
# Automatic commit message examples:
"Updated equipment status for floor 3"
"Added new HVAC equipment to mechanical room"
"Imported from building-v2.ifc"
```

### Branches

Use Git branches for:
- **Feature development** – `feature/add-hvac-floor-5`
- **Versions** – `v1.0`, `v2.0`
- **Scenarios** – `scenario/renovation-2026`

### Tags

Tag significant milestones:

```bash
git tag v1.0 -m "Initial building model"
git tag construction-complete -m "As-built model"
```

---

## Minimal Example

Absolute minimum valid `building.yaml`:

```yaml
id: "550e8400-e29b-41d4-a716-446655440000"
name: "My Building"
path: "/usa/ca/sf/my-building"
created_at: "2025-01-15T10:00:00Z"
updated_at: "2025-01-15T10:00:00Z"
floors:
  - number: 1
    name: "Ground Floor"
    wings:
      - name: "Main"
        rooms:
          - name: "Room 101"
            room_type: "Office"
```

---

## Full Example

See example files:
- `examples/buildings/minimal-building.yaml` – Minimal valid building
- `examples/buildings/building.yaml` – Complete building with equipment
- `examples/buildings/multi-floor-building.yaml` – Multi-floor complex

---

## Configuration File

ArxOS configuration in `.arxos/config.toml`:

```toml
[user]
name = "John Doe"
email = "john@example.com"

[git]
auto_stage = true
auto_commit = false
commit_template = "Building update: {message}"

[performance]
cache_enabled = true
max_parallel_threads = 8

[sensors]
enable_mqtt = false
enable_http = true
http_port = 3000
```

---

## Validation

Validate building data:

```bash
# Validate current building
arx validate

# Validate specific file
arx validate --path building.yaml
```

Validation checks:
- ✅ Required fields present
- ✅ Valid UUID format for IDs
- ✅ Valid ISO 8601 timestamps
- ✅ Valid room types
- ✅ Valid equipment types
- ✅ ArxAddress format correctness
- ✅ Coordinate value ranges
- ✅ YAML syntax

---

## Best Practices

### Structure
- Keep room names descriptive and unique
- Use consistent naming conventions
- Include ArxAddress for all equipment
- Add metadata tags for categorization

### Git Workflow
- Commit frequently with clear messages
- Use branches for major changes
- Tag release versions
- Review diffs before committing

### Equipment
- Always include `equipment_type` and `status`
- Use `properties` for manufacturer details
- Include 3D `location` when available
- Update `updated_at` on changes

### Performance
- Enable caching for large buildings
- Use spatial indexing for 3D queries
- Limit search results with `--limit`
- Use `--dry-run` for import testing

---

**See Also:**
- [Getting Started](./getting-started.md) – Basic workflows
- [CLI Reference](./cli-reference.md) – Command documentation
- [IFC Import/Export](./ifc.md) – Working with IFC files
