# ArxOS API Reference

**Version:** 2.0.0  
**Last Updated:** January 2025

This document provides a comprehensive reference for all ArxOS APIs, including CLI commands, configuration options, FFI functions, and core types.

---

## Table of Contents

1. [CLI Commands](#cli-commands)
2. [Configuration Options](#configuration-options)
3. [FFI Functions](#ffi-functions)
4. [Core API Types](#core-api-types)
5. [Error Codes](#error-codes)
6. [Request/Response Formats](#requestresponse-formats)

---

## CLI Commands

### Building Management

#### `arx init`

Initialize a new building from scratch.

**Usage:**
```bash
arx init --name <building-name> [OPTIONS]
```

**Arguments:**
- `--name <STRING>` (required) - Building name
- `--description <STRING>` (optional) - Building description
- `--location <STRING>` (optional) - Location/address
- `--git-init` - Initialize Git repository
- `--commit` - Commit initial building.yaml
- `--coordinate-system <STRING>` (default: "World") - Coordinate system
- `--units <STRING>` (default: "meters") - Units

**Examples:**
```bash
# Initialize a new building
arx init --name "PS-118" --description "Public School 118" --location "Brooklyn, NY"

# Initialize with Git
arx init --name "PS-118" --git-init --commit
```

---

#### `arx import`

Import IFC file to Git repository.

**Usage:**
```bash
arx import <ifc-file> [OPTIONS]
```

**Arguments:**
- `<ifc-file>` (required) - Path to IFC file
- `--repo <URL>` (optional) - Git repository URL
- `--dry-run` - Show what would be done without making changes

**Examples:**
```bash
# Import IFC file
arx import building.ifc

# Dry run to see what would happen
arx import building.ifc --dry-run
```

---

#### `arx export`

Export building data to Git repository or other formats.

**Usage:**
```bash
arx export [OPTIONS]
```

**Arguments:**
- `--format <FORMAT>` (default: "git") - Export format: git, ifc, gltf, usdz
- `--output <PATH>` (optional) - Output file path (required for non-git formats)
- `--repo <URL>` (optional) - Git repository URL (required for git format)
- `--delta` - Export only changes (delta mode)

**Examples:**
```bash
# Export to Git
arx export --format git --repo https://github.com/example/building.git

# Export to IFC
arx export --format ifc --output building.ifc

# Export to glTF for AR
arx export --format gltf --output building.gltf
```

---

#### `arx sync`

Sync building data to IFC file (continuous or one-time).

**Usage:**
```bash
arx sync [OPTIONS]
```

**Arguments:**
- `--ifc <PATH>` (optional) - Path to IFC file
- `--watch` - Enable watch mode (daemon) for continuous sync
- `--delta` - Export only changes (delta mode)

**Examples:**
```bash
# One-time sync
arx sync --ifc building.ifc

# Continuous sync (watch mode)
arx sync --ifc building.ifc --watch
```

---

### Equipment Management

#### `arx equipment add`

Add equipment to a room.

**Usage:**
```bash
arx equipment add --room <ROOM> --name <NAME> --equipment-type <TYPE> [OPTIONS]
```

**Arguments:**
- `--room <ROOM>` (required) - Room ID or name
- `--name <NAME>` (required) - Equipment name
- `--equipment-type <TYPE>` (required) - Equipment type
- `--position <x,y,z>` (optional) - Equipment position
- `--at <PATH>` (optional) - ArxOS Address path (e.g., `/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01`)
- `--property <key=value>` (optional) - Equipment properties (can be repeated)
- `--commit` - Commit changes to Git

**Examples:**
```bash
# Add equipment with auto-generated address
arx equipment add --room "Conference Room" --name "VAV-301" --equipment-type "HVAC"

# Add equipment with custom address
arx equipment add --room "Conference Room" --name "VAV-301" --equipment-type "HVAC" \
    --at "/usa/ny/brooklyn/ps-118/floor-02/mech/vav-301"

# Add equipment with properties
arx equipment add --room "Kitchen" --name "Refrigerator" --equipment-type "Custom" \
    --property "model=ABC123" --property "serial=XYZ789"
```

---

#### `arx equipment list`

List equipment.

**Usage:**
```bash
arx equipment list [OPTIONS]
```

**Arguments:**
- `--room <ROOM>` (optional) - Filter by room ID or name
- `--equipment-type <TYPE>` (optional) - Filter by equipment type
- `--verbose` - Show detailed information
- `--interactive` - Open interactive browser

**Examples:**
```bash
# List all equipment
arx equipment list

# List equipment in a specific room
arx equipment list --room "Conference Room"

# List HVAC equipment
arx equipment list --equipment-type "HVAC" --verbose
```

---

#### `arx equipment update`

Update equipment properties.

**Usage:**
```bash
arx equipment update <equipment> [OPTIONS]
```

**Arguments:**
- `<equipment>` (required) - Equipment ID or name
- `--property <key=value>` (optional) - Property to update (can be repeated)
- `--position <x,y,z>` (optional) - New position
- `--commit` - Commit changes to Git

**Examples:**
```bash
# Update equipment property
arx equipment update "VAV-301" --property "status=Active"

# Update equipment position
arx equipment update "VAV-301" --position "10.5,20.3,0.0" --commit
```

---

#### `arx equipment remove`

Remove equipment.

**Usage:**
```bash
arx equipment remove <equipment> [OPTIONS]
```

**Arguments:**
- `<equipment>` (required) - Equipment ID or name
- `--confirm` - Confirm deletion
- `--commit` - Commit changes to Git

**Examples:**
```bash
# Remove equipment
arx equipment remove "VAV-301" --confirm --commit
```

---

### Room Management

#### `arx room create`

Create a new room.

**Usage:**
```bash
arx room create --building <BUILDING> --floor <LEVEL> --wing <WING> --name <NAME> --room-type <TYPE> [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (required) - Building name
- `--floor <LEVEL>` (required) - Floor level
- `--wing <WING>` (required) - Wing name
- `--name <NAME>` (required) - Room name
- `--room-type <TYPE>` (required) - Room type
- `--dimensions <width x depth x height>` (optional) - Room dimensions
- `--position <x,y,z>` (optional) - Room position
- `--commit` - Commit changes to Git

**Examples:**
```bash
# Create a room
arx room create --building "PS-118" --floor 2 --wing "Main" --name "Conference Room" \
    --room-type "Conference" --dimensions "10 x 20 x 8" --position "0,0,0"
```

---

#### `arx room list`

List rooms.

**Usage:**
```bash
arx room list [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (optional) - Filter by building name
- `--floor <LEVEL>` (optional) - Filter by floor level
- `--wing <WING>` (optional) - Filter by wing name
- `--verbose` - Show detailed information
- `--interactive` - Open interactive explorer

---

#### `arx room show`

Show room details.

**Usage:**
```bash
arx room show <room> [OPTIONS]
```

**Arguments:**
- `<room>` (required) - Room ID or name
- `--equipment` - Show equipment in room

---

#### `arx room update`

Update room properties.

**Usage:**
```bash
arx room update <room> --property <key=value> [OPTIONS]
```

**Arguments:**
- `<room>` (required) - Room ID or name
- `--property <key=value>` (required) - Property to update (can be repeated)
- `--commit` - Commit changes to Git

---

#### `arx room delete`

Delete a room.

**Usage:**
```bash
arx room delete <room> [OPTIONS]
```

**Arguments:**
- `<room>` (required) - Room ID or name
- `--confirm` - Confirm deletion
- `--commit` - Commit changes to Git

---

### Git Operations

#### `arx status`

Show repository status and changes.

**Usage:**
```bash
arx status [OPTIONS]
```

**Arguments:**
- `--verbose` - Show detailed status information
- `--interactive` - Open interactive dashboard

---

#### `arx stage`

Stage changes in the working directory.

**Usage:**
```bash
arx stage [OPTIONS]
```

**Arguments:**
- `--all` - Stage all modified files (default behavior)
- `<file>` (optional) - Specific file to stage

**Examples:**
```bash
# Stage all changes
arx stage

# Stage specific file
arx stage building.yaml
```

---

#### `arx commit`

Commit staged changes.

**Usage:**
```bash
arx commit <message>
```

**Arguments:**
- `<message>` (required) - Commit message

**Examples:**
```bash
arx commit "Add new HVAC equipment"
```

---

#### `arx unstage`

Unstage changes.

**Usage:**
```bash
arx unstage [OPTIONS]
```

**Arguments:**
- `--all` - Unstage all files
- `<file>` (optional) - Specific file to unstage

---

#### `arx diff`

Show differences between commits.

**Usage:**
```bash
arx diff [OPTIONS]
```

**Arguments:**
- `--commit <HASH>` (optional) - Compare with specific commit hash
- `--file <PATH>` (optional) - Show diff for specific file
- `--stat` - Show statistics only
- `--interactive` - Open interactive diff viewer

---

#### `arx history`

Show commit history.

**Usage:**
```bash
arx history [OPTIONS]
```

**Arguments:**
- `--limit <N>` (optional) - Limit number of commits
- `--verbose` - Show detailed information
- `--file <PATH>` (optional) - Show history for specific file

---

### Search and Query

#### `arx search`

Search building data.

**Usage:**
```bash
arx search <query> [OPTIONS]
```

**Arguments:**
- `<query>` (required) - Search query
- `--equipment` - Search equipment only
- `--rooms` - Search rooms only
- `--buildings` - Search buildings only
- `--case-sensitive` - Case-sensitive search
- `--regex` - Use regex pattern matching
- `--limit <N>` (optional) - Maximum number of results
- `--verbose` - Show detailed results
- `--interactive` - Open interactive browser

**Examples:**
```bash
# Search for equipment
arx search "VAV" --equipment

# Search with regex
arx search "HVAC.*301" --regex --equipment
```

---

#### `arx query`

Query equipment by ArxAddress glob pattern.

**Usage:**
```bash
arx query <pattern> [OPTIONS]
```

**Arguments:**
- `<pattern>` (required) - Glob pattern (e.g., `/usa/ny/*/floor-*/mech/boiler-*`)
- `--format <FORMAT>` (default: "table") - Output format: table, json, yaml
- `--verbose` - Show detailed information

**Examples:**
```bash
# Query all equipment in NYC buildings
arx query "/usa/ny/*"

# Query all HVAC equipment on floor 2
arx query "/*/*/*/*/floor-02/mech/*"

# Query specific boiler
arx query "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01" --format json
```

---

#### `arx filter`

Filter building data.

**Usage:**
```bash
arx filter [OPTIONS]
```

**Arguments:**
- `--equipment-type <TYPE>` (optional) - Filter by equipment type
- `--status <STATUS>` (optional) - Filter by equipment status
- `--floor <LEVEL>` (optional) - Filter by floor level
- `--room <ROOM>` (optional) - Filter by room name
- `--building <BUILDING>` (optional) - Filter by building name
- `--critical-only` - Show only critical equipment
- `--healthy-only` - Show only healthy equipment
- `--alerts-only` - Show only equipment with alerts
- `--format <FORMAT>` (default: "table") - Output format: table, json, yaml
- `--limit <N>` (default: 100) - Maximum number of results
- `--verbose` - Show detailed results

---

### AR Integration

#### `arx ar-integrate`

Integrate AR scan data.

**Usage:**
```bash
arx ar-integrate <scan-file> [OPTIONS]
```

**Arguments:**
- `<scan-file>` (required) - Path to AR scan JSON file
- `--room <ROOM>` (optional) - Room name
- `--floor <LEVEL>` (optional) - Floor level
- `--building <BUILDING>` (optional) - Building name
- `--commit` - Commit changes to Git
- `--message <MSG>` (optional) - Custom commit message

---

### Sensor Data

#### `arx process-sensors`

Process sensor data and update equipment status.

**Usage:**
```bash
arx process-sensors <sensor-dir> --building <BUILDING> [OPTIONS]
```

**Arguments:**
- `<sensor-dir>` (required) - Directory containing sensor data files
- `--building <BUILDING>` (required) - Building name
- `--commit` - Commit changes to Git
- `--watch` - Watch directory for new sensor files

---

#### `arx sensors-http`

Start HTTP server for real-time sensor data ingestion.

**Usage:**
```bash
arx sensors-http --building <BUILDING> [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (required) - Building name
- `--host <HOST>` (default: "localhost") - Server host
- `--port <PORT>` (default: 8080) - Server port

---

#### `arx sensors-mqtt`

Start MQTT subscriber for real-time sensor data ingestion.

**Usage:**
```bash
arx sensors-mqtt --building <BUILDING> [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (required) - Building name
- `--broker <HOST>` (default: "localhost") - MQTT broker host
- `--port <PORT>` (default: 1883) - MQTT broker port
- `--username <USER>` (optional) - MQTT username
- `--password <PASS>` (optional) - MQTT password
- `--topics <TOPIC>` (optional) - MQTT topics to subscribe to (can be repeated)

---

### Visualization

#### `arx render`

Render building visualization.

**Usage:**
```bash
arx render --building <BUILDING> [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (required) - Building identifier
- `--floor <LEVEL>` (optional) - Floor number
- `--three-d` - Enable 3D multi-floor visualization
- `--show-status` - Show equipment status indicators
- `--show-rooms` - Show room boundaries
- `--format <FORMAT>` (default: "ascii") - Output format: ascii, advanced, json, yaml
- `--projection <TYPE>` (default: "isometric") - Projection type: isometric, orthographic, perspective
- `--view-angle <ANGLE>` (default: "isometric") - View angle: topdown, front, side, isometric
- `--scale <FLOAT>` (default: 1.0) - Scale factor for 3D rendering
- `--spatial-index` - Enable spatial index integration

---

#### `arx interactive`

Interactive 3D building visualization with real-time controls.

**Usage:**
```bash
arx interactive --building <BUILDING> [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (required) - Building identifier
- `--projection <TYPE>` (default: "isometric") - Projection type
- `--view-angle <ANGLE>` (default: "isometric") - View angle
- `--scale <FLOAT>` (default: 1.0) - Scale factor
- `--width <N>` (default: 120) - Canvas width in characters
- `--height <N>` (default: 40) - Canvas height in characters
- `--spatial-index` - Enable spatial index integration
- `--show-status` - Show equipment status indicators
- `--show-rooms` - Show room boundaries
- `--show-connections` - Show equipment connections
- `--fps <N>` (default: 30) - Target FPS for rendering (1-240)
- `--show-fps` - Show FPS counter
- `--show-help` - Show help overlay by default

---

### Spreadsheet Interface

#### `arx spreadsheet equipment`

Open equipment spreadsheet.

**Usage:**
```bash
arx spreadsheet equipment [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (optional) - Building name (default: current directory)
- `--filter <PATTERN>` (optional) - Pre-filter data (e.g., "status=Active" or glob pattern)
- `--commit` - Auto-commit on save (default: stage only)
- `--no-git` - Disable Git integration (read-only mode)

**Keyboard Shortcuts:**
- Arrow keys: Navigate cells
- Enter: Edit cell / Open address modal (on address column)
- Ctrl+F: Activate search
- Ctrl+A: Toggle address column visibility
- Esc: Close modal / Exit search / Quit
- Tab: Next cell
- Shift+Tab: Previous cell
- Ctrl+S: Save changes

---

#### `arx spreadsheet rooms`

Open room spreadsheet.

**Usage:**
```bash
arx spreadsheet rooms [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (optional) - Building name
- `--filter <PATTERN>` (optional) - Pre-filter data
- `--commit` - Auto-commit on save
- `--no-git` - Disable Git integration

---

#### `arx spreadsheet sensors`

Open sensor spreadsheet.

**Usage:**
```bash
arx spreadsheet sensors [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (optional) - Building name
- `--filter <PATTERN>` (optional) - Pre-filter data
- `--commit` - Auto-commit on save
- `--no-git` - Disable Git integration

---

### Configuration

#### `arx config`

Manage configuration.

**Usage:**
```bash
arx config [OPTIONS]
```

**Arguments:**
- `--show` - Show current configuration
- `--set <section.key=value>` (optional) - Set configuration value
- `--reset` - Reset to defaults
- `--edit` - Edit configuration file
- `--interactive` - Open interactive wizard

**Examples:**
```bash
# Show current configuration
arx config --show

# Set configuration value
arx config --set user.name="John Doe"
arx config --set building.auto_commit=false

# Edit configuration file
arx config --edit
```

---

### Utilities

#### `arx validate`

Validate building data.

**Usage:**
```bash
arx validate [OPTIONS]
```

**Arguments:**
- `--path <PATH>` (optional) - Path to building data (default: current directory)

---

#### `arx health`

Run system health diagnostics.

**Usage:**
```bash
arx health [OPTIONS]
```

**Arguments:**
- `<component>` (optional) - Specific component to check
- `--verbose` - Show detailed diagnostics
- `--interactive` - Open interactive dashboard

---

#### `arx doc`

Generate HTML documentation for a building.

**Usage:**
```bash
arx doc --building <BUILDING> [OPTIONS]
```

**Arguments:**
- `--building <BUILDING>` (required) - Building name to document
- `--output <PATH>` (optional) - Output file path (default: ./docs/{building}.html)

---

#### `arx migrate`

Migrate existing fixtures to ArxAddress format.

**Usage:**
```bash
arx migrate [OPTIONS]
```

**Arguments:**
- `--dry-run` - Show what would be migrated without making changes

**Examples:**
```bash
# Preview migration
arx migrate --dry-run

# Perform migration
arx migrate
```

---

## Configuration Options

### Configuration Precedence

Configuration is loaded with the following precedence (highest to lowest):

1. **Environment Variables** (highest priority)
2. **Project Config** (`.arxos/config.toml` in current directory)
3. **User Config** (`~/.arxos/config.toml` on Unix, `%APPDATA%\arxos\config.toml` on Windows)
4. **Global Config** (`/etc/arxos/config.toml` on Unix, `C:\ProgramData\arxos\config.toml` on Windows)
5. **Built-in Defaults** (lowest priority)

### Configuration Schema

#### User Configuration (`[user]`)

| Field | Type | Default | Environment Variable | Description |
|-------|------|---------|---------------------|-------------|
| `name` | String | "ArxOS User" | `ARX_USER_NAME` | User's full name for commits |
| `email` | String | "user@arxos.com" | `ARX_USER_EMAIL` | User's email address for commits |
| `organization` | String? | None | `ARX_USER_ORGANIZATION` | User's organization (optional) |
| `commit_template` | String | "feat: {operation} {building_name}" | - | Default commit message template |

**Example:**
```toml
[user]
name = "John Doe"
email = "john.doe@example.com"
organization = "Acme Corp"
commit_template = "feat: {operation} {building_name}"
```

---

#### Path Configuration (`[paths]`)

| Field | Type | Default | Environment Variable | Description |
|-------|------|---------|---------------------|-------------|
| `default_import_path` | Path | "./buildings" | `ARX_DEFAULT_IMPORT_PATH` | Default directory for importing IFC files |
| `backup_path` | Path | "./backups" | `ARX_BACKUP_PATH` | Directory for backup files |
| `template_path` | Path | "./templates" | - | Directory for template files |
| `temp_path` | Path | "./temp" | - | Directory for temporary files |

**Example:**
```toml
[paths]
default_import_path = "./buildings"
backup_path = "./backups"
template_path = "./templates"
temp_path = "./temp"
```

---

#### Building Configuration (`[building]`)

| Field | Type | Default | Environment Variable | Description |
|-------|------|---------|---------------------|-------------|
| `default_coordinate_system` | String | "WGS84" | - | Default coordinate system (WGS84, UTM, LOCAL) |
| `auto_commit` | Boolean | true | `ARX_AUTO_COMMIT` | Automatically commit changes to Git |
| `naming_pattern` | String | "{building_name}-{timestamp}" | - | Default building naming pattern (must include {building_name}) |
| `validate_on_import` | Boolean | true | - | Validate IFC files on import |

**Example:**
```toml
[building]
default_coordinate_system = "WGS84"
auto_commit = true
naming_pattern = "{building_name}-{timestamp}"
validate_on_import = true
```

---

#### Performance Configuration (`[performance]`)

| Field | Type | Default | Environment Variable | Description |
|-------|------|---------|---------------------|-------------|
| `max_parallel_threads` | Integer | CPU count | `ARX_MAX_THREADS` | Maximum number of parallel threads (1-64) |
| `memory_limit_mb` | Integer | 1024 | `ARX_MEMORY_LIMIT_MB` | Memory limit in MB (1-16384) |
| `cache_enabled` | Boolean | true | - | Enable caching |
| `cache_path` | Path | "./cache" | - | Cache directory path |
| `show_progress` | Boolean | true | - | Show progress bars |

**Example:**
```toml
[performance]
max_parallel_threads = 4
memory_limit_mb = 2048
cache_enabled = true
cache_path = "./cache"
show_progress = true
```

---

#### UI Configuration (`[ui]`)

| Field | Type | Default | Environment Variable | Description |
|-------|------|---------|---------------------|-------------|
| `use_emoji` | Boolean | true | - | Use emoji in output |
| `verbosity` | Enum | "Normal" | `ARX_VERBOSITY` | Output verbosity level (Silent, Normal, Verbose, Debug) |
| `color_scheme` | Enum | "Auto" | - | Color scheme preference (Auto, Always, Never) |
| `detailed_help` | Boolean | false | - | Show detailed help by default |

**Example:**
```toml
[ui]
use_emoji = true
verbosity = "Normal"
color_scheme = "Auto"
detailed_help = false
```

---

### Complete Configuration Example

```toml
[user]
name = "John Doe"
email = "john.doe@example.com"
organization = "Acme Corp"
commit_template = "feat: {operation} {building_name}"

[paths]
default_import_path = "./buildings"
backup_path = "./backups"
template_path = "./templates"
temp_path = "./temp"

[building]
default_coordinate_system = "WGS84"
auto_commit = true
naming_pattern = "{building_name}-{timestamp}"
validate_on_import = true

[performance]
max_parallel_threads = 4
memory_limit_mb = 2048
cache_enabled = true
cache_path = "./cache"
show_progress = true

[ui]
use_emoji = true
verbosity = "Normal"
color_scheme = "Auto"
detailed_help = false
```

---

## FFI Functions

### C FFI Functions (iOS/Android)

All FFI functions return JSON strings and use thread-local error storage.

#### Error Handling

**Functions:**
- `arxos_last_error() -> i32` - Get last error code
- `arxos_last_error_message() -> *mut c_char` - Get last error message
- `arxos_free_string(ptr: *mut c_char)` - Free string returned by FFI functions

**Error Codes:**
- `0` - Success
- `1` - NotFound
- `2` - InvalidData
- `3` - IoError
- `99` - Unknown

---

#### Room Operations

**`arxos_list_rooms(building_name: *const c_char) -> *mut c_char`**

List all rooms in a building.

**Parameters:**
- `building_name` - Building name (null-terminated C string)

**Returns:**
JSON array of room objects:
```json
[
  {
    "id": "room-001",
    "name": "Conference Room",
    "room_type": "Conference",
    "area": 200.0,
    "volume": 1600.0,
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "address_path": "/usa/ny/brooklyn/ps-118/floor-02/main/conference-room"
  }
]
```

---

**`arxos_get_room(building_name: *const c_char, room_id: *const c_char) -> *mut c_char`**

Get details for a specific room.

**Parameters:**
- `building_name` - Building name
- `room_id` - Room ID or name

**Returns:**
JSON object with room details:
```json
{
  "id": "room-001",
  "name": "Conference Room",
  "room_type": "Conference",
  "area": 200.0,
  "volume": 1600.0,
  "position": {"x": 0.0, "y": 0.0, "z": 0.0},
  "equipment": [
    {"id": "equip-001", "name": "VAV-301", "type": "HVAC"}
  ],
  "address_path": "/usa/ny/brooklyn/ps-118/floor-02/main/conference-room"
}
```

---

#### Equipment Operations

**`arxos_list_equipment(building_name: *const c_char) -> *mut c_char`**

List all equipment in a building.

**Parameters:**
- `building_name` - Building name

**Returns:**
JSON array of equipment objects:
```json
[
  {
    "id": "equip-001",
    "name": "VAV-301",
    "equipment_type": "HVAC",
    "status": "Active",
    "position": {"x": 10.0, "y": 20.0, "z": 0.0},
    "address_path": "/usa/ny/brooklyn/ps-118/floor-02/mech/vav-301"
  }
]
```

---

**`arxos_get_equipment(building_name: *const c_char, equipment_id: *const c_char) -> *mut c_char`**

Get details for specific equipment.

**Parameters:**
- `building_name` - Building name
- `equipment_id` - Equipment ID or name

**Returns:**
JSON object with equipment details:
```json
{
  "id": "equip-001",
  "name": "VAV-301",
  "equipment_type": "HVAC",
  "status": "Active",
  "position": {"x": 10.0, "y": 20.0, "z": 0.0},
  "properties": {"model": "ABC123", "serial": "XYZ789"},
  "address_path": "/usa/ny/brooklyn/ps-118/floor-02/mech/vav-301"
}
```

---

#### AR Operations

**`arxos_parse_ar_scan(json_data: *const c_char) -> *mut c_char`**

Parse AR scan data from JSON.

**Parameters:**
- `json_data` - JSON string containing AR scan data (see ARScanData structure)

**Returns:**
JSON object with parsed scan data:
```json
{
  "success": true,
  "detected_equipment": [
    {
      "name": "VAV-301",
      "equipment_type": "HVAC",
      "position": {"x": 10.0, "y": 20.0, "z": 0.0},
      "confidence": 0.95
    }
  ],
  "room_boundaries": {...},
  "scan_timestamp": "2025-01-03T14:30:00Z"
}
```

---

**`arxos_save_ar_scan(json_data: *const c_char, building_name: *const c_char, confidence_threshold: f64) -> *mut c_char`**

Save AR scan data and process to pending equipment.

**Parameters:**
- `json_data` - JSON string containing AR scan data
- `building_name` - Name of building for context
- `confidence_threshold` - Minimum confidence score (0.0-1.0) to create pending items

**Returns:**
JSON object with processing results:
```json
{
  "success": true,
  "building": "ps-118",
  "pending_count": 3,
  "pending_ids": ["pending-1", "pending-2", "pending-3"],
  "confidence_threshold": 0.7,
  "scan_timestamp": "2025-01-03T14:30:00Z",
  "message": "AR scan processed successfully"
}
```

---

**`arxos_list_pending_equipment(building_name: *const c_char) -> *mut c_char`**

List pending equipment items waiting for confirmation.

**Parameters:**
- `building_name` - Building name

**Returns:**
JSON array of pending equipment:
```json
[
  {
    "id": "pending-1",
    "name": "VAV-301",
    "equipment_type": "HVAC",
    "confidence": 0.95,
    "scan_id": "scan-001",
    "detected_at": "2025-01-03T14:30:00Z"
  }
]
```

---

**`arxos_confirm_pending_equipment(building_name: *const c_char, pending_id: *const c_char, room_id: *const c_char) -> *mut c_char`**

Confirm pending equipment and add to building.

**Parameters:**
- `building_name` - Building name
- `pending_id` - Pending equipment ID
- `room_id` - Room ID or name (optional, can be null)

**Returns:**
JSON object with confirmation result:
```json
{
  "success": true,
  "pending_id": "pending-1",
  "equipment_id": "equip-001",
  "message": "Equipment confirmed and added to building"
}
```

---

**`arxos_reject_pending_equipment(building_name: *const c_char, pending_id: *const c_char) -> *mut c_char`**

Reject pending equipment item.

**Parameters:**
- `building_name` - Building name
- `pending_id` - Pending equipment ID

**Returns:**
JSON object with rejection result:
```json
{
  "success": true,
  "pending_id": "pending-1",
  "message": "Pending equipment rejected"
}
```

---

**`arxos_load_ar_model(building_name: *const c_char, format: *const c_char, output_path: *const c_char) -> *mut c_char`**

Load AR model (glTF or USDZ) for a building.

**Parameters:**
- `building_name` - Building name
- `format` - Export format: "usdz" or "gltf" (case-insensitive)
- `output_path` - Optional path where model should be saved (null for temp file)

**Returns:**
JSON object with export result:
```json
{
  "success": true,
  "building": "ps-118",
  "format": "usdz",
  "file_path": "/path/to/model.usdz",
  "file_size": 12345,
  "message": "Model exported successfully"
}
```

---

#### Game System Operations

**`arxos_load_pr(pr_id: *const c_char, pr_dir: *const c_char, building_name: *const c_char) -> *mut c_char`**

Load a PR for review (game mode).

**Parameters:**
- `pr_id` - PR ID
- `pr_dir` - PR directory path (optional, can be null for default)
- `building_name` - Building name

**Returns:**
JSON object with PR summary:
```json
{
  "pr_id": "pr-001",
  "building": "ps-118",
  "total_items": 10,
  "valid_items": 8,
  "items_with_violations": 2,
  "total_violations": 3,
  "critical_violations": 1,
  "warnings": 2,
  "equipment": [...]
}
```

---

**`arxos_validate_constraints(equipment_json: *const c_char, constraints_json: *const c_char) -> *mut c_char`**

Validate equipment placement against constraints.

**Parameters:**
- `equipment_json` - JSON string with equipment data
- `constraints_json` - JSON string with constraints (optional, can be null)

**Returns:**
JSON object with validation results:
```json
{
  "is_valid": false,
  "violations": [
    {
      "type": "proximity",
      "message": "Equipment too close to wall",
      "severity": "critical"
    }
  ],
  "suggestions": ["Move equipment 2m away from wall"]
}
```

---

**`arxos_get_game_plan(session_id: *const c_char, building_name: *const c_char) -> *mut c_char`**

Get game plan for equipment placement.

**Parameters:**
- `session_id` - Game session ID
- `building_name` - Building name

**Returns:**
JSON object with game plan.

---

### JNI Functions (Android)

All JNI functions are Java-compatible wrappers around C FFI functions.

**Package:** `com.arxos.mobile`

**Functions:**
- `listRooms(buildingName: String): String` - List all rooms
- `getRoom(buildingName: String, roomId: String): String` - Get room details
- `listEquipment(buildingName: String): String` - List all equipment
- `getEquipment(buildingName: String, equipmentId: String): String` - Get equipment details
- `parseARScan(jsonData: String): String` - Parse AR scan data
- `saveARScan(jsonData: String, buildingName: String, confidenceThreshold: Double): String` - Save AR scan
- `listPendingEquipment(buildingName: String): String` - List pending equipment
- `confirmPendingEquipment(buildingName: String, pendingId: String, roomId: String?): String` - Confirm pending equipment
- `rejectPendingEquipment(buildingName: String, pendingId: String): String` - Reject pending equipment
- `loadARModel(buildingName: String, format: String, outputPath: String?): String` - Load AR model

See `src/mobile_ffi/jni.rs` for complete JNI function signatures.

---

## Core API Types

### Building Types

**`Building`**
- Root entity for building data
- Contains floors, metadata, and coordinate systems

**`Floor`**
- Represents a floor in a building
- Contains wings, rooms, and equipment

**`Wing`**
- Represents a wing on a floor
- Contains rooms and equipment

**`Room`**
- Represents a room in a building
- Contains equipment and spatial properties

**`Equipment`**
- Represents equipment in a building
- Contains position, type, status, and properties

### Spatial Types

**`Position`**
- 3D position with coordinate system
- Fields: `x`, `y`, `z`, `coordinate_system`

**`Dimensions`**
- 3D dimensions
- Fields: `width`, `height`, `depth`

**`BoundingBox`**
- 3D bounding box
- Fields: `min: Position`, `max: Position`

**`ArxAddress`**
- 7-part hierarchical address
- Format: `/country/state/city/building/floor/room/fixture`
- Path: `String` - Full path string
- Methods:
  - `new(country, state, city, building, floor, room, fixture) -> Result<ArxAddress>`
  - `from_path(path: &str) -> Result<ArxAddress>`
  - `validate() -> Result<()>`
  - `to_guid() -> String` - Generate SHA-256 GUID for IFC

### Equipment Types

**`EquipmentType`**
- Enum: `HVAC`, `Electrical`, `AV`, `Plumbing`, `Network`, `Other(String)`

**`EquipmentStatus`**
- Enum: `Active`, `Inactive`, `Maintenance`, `Retired`

### Room Types

**`RoomType`**
- Enum: `Office`, `Conference`, `Classroom`, `Lab`, `Storage`, `Bathroom`, `Kitchen`, `Other(String)`

---

## Error Codes

### ArxError Variants

All errors include a `Box<ErrorContext>` with suggestions, recovery steps, and debug information.

**`IfcProcessing`**
- IFC file processing errors
- Fields: `message`, `context`, `source`

**`Configuration`**
- Configuration errors
- Fields: `message`, `context`, `field`

**`GitOperation`**
- Git operation errors
- Fields: `message`, `context`, `operation`

**`Validation`**
- Validation errors
- Fields: `message`, `context`, `file_path`

**`IoError`**
- I/O errors
- Fields: `message`, `context`, `path`

**`YamlProcessing`**
- YAML processing errors
- Fields: `message`, `context`, `file_path`

**`SpatialData`**
- Spatial data errors
- Fields: `message`, `context`, `entity_type`

**`AddressValidation`**
- Address validation errors
- Fields: `message`, `context`, `path`, `source`

**`CounterOverflow`**
- Counter overflow errors
- Fields: `message`, `context`, `room`, `equipment_type`

**`PathInvalid`**
- Path validation errors
- Fields: `message`, `context`, `path`, `expected_format`

### FFI Error Codes

**`ArxOSErrorCode`**
- `0` - Success
- `1` - NotFound
- `2` - InvalidData
- `3` - IoError
- `99` - Unknown

---

## Request/Response Formats

### AR Scan Data Format

**Request:**
```json
{
  "detectedEquipment": [
    {
      "name": "VAV-301",
      "equipmentType": "HVAC",
      "position": {"x": 10.0, "y": 20.0, "z": 0.0},
      "boundingBox": {
        "min": {"x": 9.5, "y": 19.5, "z": -1.0},
        "max": {"x": 10.5, "y": 20.5, "z": 1.0}
      },
      "confidence": 0.95,
      "detectionMethod": "ARKit",
      "properties": {}
    }
  ],
  "roomBoundaries": {
    "points": [...],
    "center": {"x": 0.0, "y": 0.0, "z": 0.0}
  },
  "deviceType": "iOS",
  "appVersion": "1.0.0",
  "scanDurationMs": 5000,
  "pointCount": 10000,
  "accuracyEstimate": 0.05,
  "lightingConditions": "bright",
  "roomName": "Conference Room",
  "floorLevel": 2
}
```

### Sensor Data Format

**YAML Format:**
```yaml
sensor_id: "esp32_temp_001"
sensor_type: "temperature"
timestamp: "2025-01-03T14:30:00Z"
values:
  temperature: 72.5
  humidity: 45.0
equipment_id: "HVAC-301"
building: "ps-118"
floor: 2
room: "Conference Room"
```

**JSON Format:**
```json
{
  "sensor_id": "rp2040_air_001",
  "sensor_type": "air_quality",
  "timestamp": "2025-01-03T14:30:00Z",
  "values": {
    "pm2_5": 12.5,
    "pm10": 18.3,
    "co2": 420
  },
  "equipment_id": "HVAC-205",
  "building": "ps-118",
  "floor": 2,
  "room": "Conference Room"
}
```

---

## Additional Resources

- **User Guide:** See `docs/core/USER_GUIDE.md`
- **Integration Examples:** See `docs/INTEGRATION_EXAMPLES.md`
- **Troubleshooting:** See `docs/TROUBLESHOOTING.md`
- **Rust Documentation:** Generate with `cargo doc --open`

---

**Note:** This API reference is automatically generated from source code. For the most up-to-date information, refer to the inline documentation in the source code.

