# ArxOS API Reference

**Version:** 2.0  
**Last Updated:** December 2024

## Table of Contents

1. [Introduction](#introduction)
2. [CLI Commands](#cli-commands)
   - [Core Commands](#core-commands)
   - [Git Operations](#git-operations)
   - [Data Management](#data-management)
   - [Visualization](#visualization)
   - [Search & Filter](#search--filter)
   - [AR Integration](#ar-integration)
   - [Sensor Processing](#sensor-processing)
   - [System Commands](#system-commands)
3. [Configuration API](#configuration-api)
4. [Mobile FFI API](#mobile-ffi-api)
   - [C FFI Functions](#c-ffi-functions)
   - [JNI Functions](#jni-functions)
   - [Data Structures](#data-structures)
5. [Core Rust API](#core-rust-api)
6. [Error Reference](#error-reference)
7. [Examples](#examples)

---

## Introduction

This document provides a comprehensive reference for all public APIs in ArxOS. It covers CLI commands, configuration options, mobile FFI bindings, core Rust types, and error handling.

**For users:** See the [User Guide](./USER_GUIDE.md) for tutorials and workflows.  
**For developers:** This document provides complete API specifications.

---

## CLI Commands

All ArxOS commands follow the pattern: `arx <command> [options] [arguments]`

### Core Commands

#### `arx import`

Import an IFC building file into the ArxOS repository.

**Signature:**
```bash
arx import <IFC_FILE> [OPTIONS]
```

**Arguments:**
- `IFC_FILE` (required): Path to IFC file to import

**Options:**
- `--repo <REPO>` (optional): Git repository URL (default: current directory)
- `--dry-run` (flag): Preview changes without making them

**Examples:**

```bash
# Basic import
arx import building.ifc

# Import to specific repository
arx import building.ifc --repo https://github.com/company/buildings.git

# Preview import changes
arx import building.ifc --dry-run
```

**Related Commands:**
- [`arx export`](#arx-export) - Export building data
- [`arx validate`](#arx-validate) - Validate IFC files

---

#### `arx export`

Export building data to a Git repository.

**Signature:**
```bash
arx export --repo <REPO>
```

**Options:**
- `--repo <REPO>` (required): Git repository URL

**Examples:**

```bash
# Export to remote repository
arx export --repo https://github.com/company/buildings.git
```

**Related Commands:**
- [`arx import`](#arx-import) - Import IFC files
- [`arx status`](#arx-status) - Check repository status

---

#### `arx validate`

Validate building data files.

**Signature:**
```bash
arx validate [--path <PATH>]
```

**Options:**
- `--path <PATH>` (optional): Path to building data (default: current directory)

**Examples:**

```bash
# Validate current directory
arx validate

# Validate specific path
arx validate --path ./buildings/main-building.yaml
```

---

### Git Operations

#### `arx status`

Show repository status and changes.

**Signature:**
```bash
arx status [--verbose]
```

**Options:**
- `--verbose` (flag): Show detailed status information

**Examples:**

```bash
# Basic status
arx status

# Detailed status
arx status --verbose
```

---

#### `arx stage`

Stage changes in the working directory.

**Signature:**
```bash
arx stage [--all] [<FILE>]
```

**Options:**
- `--all` (flag): Stage all modified files (default behavior)
- `<FILE>` (optional): Specific file to stage

**Examples:**

```bash
# Stage all changes
arx stage --all

# Stage specific file
arx stage main-building.yaml
```

**Related Commands:**
- [`arx commit`](#arx-commit) - Commit staged changes
- [`arx unstage`](#arx-unstage) - Unstage changes

---

#### `arx commit`

Commit staged changes to Git.

**Signature:**
```bash
arx commit <MESSAGE>
```

**Arguments:**
- `MESSAGE` (required): Commit message

**Examples:**

```bash
# Commit with message
arx commit "Add new HVAC equipment to floor 3"
```

**Related Commands:**
- [`arx stage`](#arx-stage) - Stage changes
- [`arx history`](#arx-history) - View commit history

---

#### `arx unstage`

Unstage changes from the staging area.

**Signature:**
```bash
arx unstage [--all] [<FILE>]
```

**Options:**
- `--all` (flag): Unstage all files
- `<FILE>` (optional): Specific file to unstage

**Examples:**

```bash
# Unstage all files
arx unstage --all

# Unstage specific file
arx unstage main-building.yaml
```

---

#### `arx diff`

Show differences between commits or files.

**Signature:**
```bash
arx diff [--commit <COMMIT>] [--file <FILE>] [--stat]
```

**Options:**
- `--commit <COMMIT>` (optional): Compare with specific commit hash
- `--file <FILE>` (optional): Show diff for specific file
- `--stat` (flag): Show file statistics only

**Examples:**

```bash
# Show diff for working directory
arx diff

# Compare with specific commit
arx diff --commit abc123

# Show diff for specific file
arx diff --file main-building.yaml

# Show statistics
arx diff --stat
```

---

#### `arx history`

Show commit history.

**Signature:**
```bash
arx history [--limit <N>] [--verbose] [--file <FILE>]
```

**Options:**
- `--limit <N>` (optional, default: 10): Number of commits to show
- `--verbose` (flag): Show detailed commit information
- `--file <FILE>` (optional): Show history for specific file

**Examples:**

```bash
# Show last 10 commits
arx history

# Show last 20 commits with details
arx history --limit 20 --verbose

# Show history for specific file
arx history --file main-building.yaml
```

---

### Data Management

#### `arx room`

Room management commands.

**Subcommands:**

##### `arx room create`

Create a new room.

**Signature:**
```bash
arx room create --building <BUILDING> --floor <FLOOR> --wing <WING> --name <NAME> --room-type <TYPE> [OPTIONS]
```

**Required Options:**
- `--building <BUILDING>`: Building name
- `--floor <FLOOR>`: Floor level (integer)
- `--wing <WING>`: Wing identifier
- `--name <NAME>`: Room name
- `--room-type <TYPE>`: Room type

**Optional Options:**
- `--dimensions <WIDTH>x<DEPTH>x<HEIGHT>`: Room dimensions
- `--position <X,Y,Z>`: Room position coordinates
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Create a room with dimensions
arx room create --building "Main Building" --floor 2 --wing "A" --name "Conference Room 201" --room-type "Office" --dimensions "10x8x3" --position "5,10,2"

# Create and commit
arx room create --building "Main Building" --floor 1 --wing "B" --name "Lab 101" --room-type "Laboratory" --commit
```

---

##### `arx room list`

List rooms.

**Signature:**
```bash
arx room list [--building <BUILDING>] [--floor <FLOOR>] [--wing <WING>] [--verbose]
```

**Options:**
- `--building <BUILDING>` (optional): Filter by building
- `--floor <FLOOR>` (optional): Filter by floor
- `--wing <WING>` (optional): Filter by wing
- `--verbose` (flag): Show detailed information

**Examples:**

```bash
# List all rooms
arx room list

# List rooms on floor 2
arx room list --floor 2 --verbose

# List rooms in specific building
arx room list --building "Main Building"
```

---

##### `arx room show`

Show room details.

**Signature:**
```bash
arx room show <ROOM> [--equipment]
```

**Arguments:**
- `ROOM` (required): Room ID or name

**Options:**
- `--equipment` (flag): Show equipment in room

**Examples:**

```bash
# Show room details
arx room show "Conference Room 201"

# Show room with equipment
arx room show "Conference Room 201" --equipment
```

---

##### `arx room update`

Update room properties.

**Signature:**
```bash
arx room update <ROOM> --property <KEY=VALUE> [--commit]
```

**Arguments:**
- `ROOM` (required): Room ID or name

**Options:**
- `--property <KEY=VALUE>` (repeatable): Property to update
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Update room name
arx room update "Conference Room 201" --property "name=Conference Room 201A" --commit
```

---

##### `arx room delete`

Delete a room.

**Signature:**
```bash
arx room delete <ROOM> [--confirm] [--commit]
```

**Arguments:**
- `ROOM` (required): Room ID or name

**Options:**
- `--confirm` (flag): Confirm deletion
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Delete room with confirmation
arx room delete "Conference Room 201" --confirm --commit
```

---

#### `arx equipment`

Equipment management commands.

**Subcommands:**

##### `arx equipment add`

Add equipment to a room.

**Signature:**
```bash
arx equipment add --room <ROOM> --name <NAME> --equipment-type <TYPE> [OPTIONS]
```

**Required Options:**
- `--room <ROOM>`: Room ID or name
- `--name <NAME>`: Equipment name
- `--equipment-type <TYPE>`: Equipment type (HVAC, Electrical, AV, etc.)

**Optional Options:**
- `--position <X,Y,Z>`: Equipment position
- `--property <KEY=VALUE>` (repeatable): Equipment properties
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Add HVAC equipment
arx equipment add --room "Conference Room 201" --name "VAV-301" --equipment-type "HVAC" --position "5,8,2" --commit

# Add equipment with properties
arx equipment add --room "Lab 101" --name "Camera-101" --equipment-type "AV" --property "resolution=4K" --property "model=Sony"
```

**Equipment Types:**
- `HVAC` - Heating, ventilation, air conditioning
- `Electrical` - Electrical equipment
- `AV` - Audio/visual equipment
- `Furniture` - Furniture items
- `Safety` - Safety equipment
- `Plumbing` - Plumbing fixtures
- `Network` - Network equipment
- `Other` - Other equipment types

---

##### `arx equipment list`

List equipment.

**Signature:**
```bash
arx equipment list [--room <ROOM>] [--equipment-type <TYPE>] [--verbose]
```

**Options:**
- `--room <ROOM>` (optional): Filter by room
- `--equipment-type <TYPE>` (optional): Filter by equipment type
- `--verbose` (flag): Show detailed information

**Examples:**

```bash
# List all equipment
arx equipment list

# List HVAC equipment
arx equipment list --equipment-type "HVAC" --verbose

# List equipment in room
arx equipment list --room "Conference Room 201"
```

---

##### `arx equipment update`

Update equipment properties.

**Signature:**
```bash
arx equipment update <EQUIPMENT> [--property <KEY=VALUE>] [--position <X,Y,Z>] [--commit]
```

**Arguments:**
- `EQUIPMENT` (required): Equipment ID or name

**Options:**
- `--property <KEY=VALUE>` (repeatable): Property to update
- `--position <X,Y,Z>` (optional): New position
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Update equipment status
arx equipment update "VAV-301" --property "status=Maintenance" --commit

# Update equipment position
arx equipment update "VAV-301" --position "6,8,2" --commit
```

---

##### `arx equipment remove`

Remove equipment.

**Signature:**
```bash
arx equipment remove <EQUIPMENT> [--confirm] [--commit]
```

**Arguments:**
- `EQUIPMENT` (required): Equipment ID or name

**Options:**
- `--confirm` (flag): Confirm removal
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Remove equipment
arx equipment remove "VAV-301" --confirm --commit
```

---

#### `arx spatial`

Spatial operations and queries.

**Subcommands:**

##### `arx spatial query`

Query spatial relationships.

**Signature:**
```bash
arx spatial query --query-type <TYPE> --entity <ENTITY> [--params <PARAMS>]
```

**Options:**
- `--query-type <TYPE>`: Query type
- `--entity <ENTITY>`: Target entity (room or equipment)
- `--params <PARAMS>` (repeatable): Additional parameters

**Examples:**

```bash
# Query nearby equipment
arx spatial query --query-type "nearby" --entity "VAV-301" --params "radius=10"
```

---

##### `arx spatial relate`

Set spatial relationships.

**Signature:**
```bash
arx spatial relate --entity1 <ENTITY1> --entity2 <ENTITY2> --relationship <REL>
```

**Options:**
- `--entity1 <ENTITY1>`: First entity
- `--entity2 <ENTITY2>`: Second entity
- `--relationship <REL>`: Relationship type

---

##### `arx spatial transform`

Transform coordinates.

**Signature:**
```bash
arx spatial transform --from <FROM> --to <TO> --entity <ENTITY>
```

**Options:**
- `--from <FROM>`: Source coordinate system
- `--to <TO>`: Target coordinate system
- `--entity <ENTITY>`: Entity to transform

---

##### `arx spatial validate`

Validate spatial data.

**Signature:**
```bash
arx spatial validate [--entity <ENTITY>] [--tolerance <TOL>]
```

**Options:**
- `--entity <ENTITY>` (optional): Entity to validate
- `--tolerance <TOL>` (optional): Validation tolerance

---

### Visualization

#### `arx render`

Render building visualization.

**Signature:**
```bash
arx render --building <BUILDING> [OPTIONS]
```

**Required Options:**
- `--building <BUILDING>`: Building identifier

**Optional Options:**
- `--floor <FLOOR>` (integer): Floor number to render
- `--three-d` (flag): Enable 3D multi-floor visualization
- `--show-status` (flag): Show equipment status indicators
- `--show-rooms` (flag): Show room boundaries
- `--format <FORMAT>` (default: "ascii"): Output format (ascii, advanced, json, yaml)
- `--projection <TYPE>` (default: "isometric"): Projection type (isometric, orthographic, perspective)
- `--view-angle <ANGLE>` (default: "isometric"): View angle (topdown, front, side, isometric)
- `--scale <SCALE>` (default: 1.0): Scale factor for 3D rendering
- `--spatial-index` (flag): Enable spatial index integration

**Examples:**

```bash
# Basic render
arx render --building "Main Building"

# 3D render with status indicators
arx render --building "Main Building" --three-d --show-status

# Render specific floor in JSON format
arx render --building "Main Building" --floor 2 --format json

# 3D render with custom projection
arx render --building "Main Building" --three-d --projection perspective --view-angle front --scale 1.5
```

---

#### `arx interactive`

Interactive 3D building visualization with real-time controls.

**Signature:**
```bash
arx interactive --building <BUILDING> [OPTIONS]
```

**Required Options:**
- `--building <BUILDING>`: Building identifier

**Optional Options:**
- `--projection <TYPE>` (default: "isometric"): Projection type (isometric, orthographic, perspective)
- `--view-angle <ANGLE>` (default: "isometric"): View angle (topdown, front, side, isometric)
- `--scale <SCALE>` (default: 1.0): Scale factor for rendering
- `--width <WIDTH>` (default: 120): Canvas width in characters
- `--height <HEIGHT>` (default: 40): Canvas height in characters
- `--spatial-index` (flag): Enable spatial index integration
- `--show-status` (flag): Show equipment status indicators
- `--show-rooms` (flag): Show room boundaries
- `--show-connections` (flag): Show equipment connections
- `--fps <FPS>` (default: 30): Target FPS for rendering
- `--show-fps` (flag): Show FPS counter
- `--show-help` (flag): Show help overlay by default

**Examples:**

```bash
# Start interactive mode
arx interactive --building "Main Building"

# Interactive with custom view and FPS display
arx interactive --building "Main Building" --view-angle topdown --show-fps --fps 60

# Interactive with all features enabled
arx interactive --building "Main Building" --show-status --show-rooms --show-connections --spatial-index
```

**Controls:**
- Arrow keys: Pan view
- `+/-`: Zoom in/out
- `R`: Reset view
- `Q`: Quit
- `H`: Toggle help

---

### Search & Filter

#### `arx search`

Search building data.

**Signature:**
```bash
arx search <QUERY> [OPTIONS]
```

**Arguments:**
- `QUERY` (required): Search query string

**Options:**
- `--equipment` (flag): Search in equipment names
- `--rooms` (flag): Search in room names
- `--buildings` (flag): Search in building names
- `--case-sensitive` (flag): Case-sensitive search
- `--regex` (flag): Use regex pattern matching
- `--limit <N>` (default: 50): Maximum number of results
- `--verbose` (flag): Show detailed results

**Examples:**

```bash
# Basic search
arx search "VAV"

# Regex search in equipment
arx search "HVAC.*301" --equipment --regex

# Case-sensitive room search
arx search "Conference" --rooms --case-sensitive --verbose

# Search with limit
arx search "main" --limit 20
```

**Search Behavior:**
- By default, searches in equipment names unless `--rooms` or `--buildings` is specified
- If multiple flags are specified, searches in all specified types
- Regex patterns use Rust regex syntax

---

#### `arx filter`

Filter building data by criteria.

**Signature:**
```bash
arx filter [OPTIONS]
```

**Options:**
- `--equipment-type <TYPE>` (optional): Filter by equipment type
- `--status <STATUS>` (optional): Filter by equipment status
- `--floor <FLOOR>` (optional): Filter by floor number
- `--room <ROOM>` (optional): Filter by room
- `--building <BUILDING>` (optional): Filter by building
- `--critical-only` (flag): Show only critical equipment
- `--healthy-only` (flag): Show only healthy equipment
- `--alerts-only` (flag): Show only equipment with alerts
- `--format <FORMAT>` (default: "table"): Output format (table, json, yaml)
- `--limit <N>` (default: 100): Maximum number of results
- `--verbose` (flag): Show detailed results

**Examples:**

```bash
# Filter by equipment type
arx filter --equipment-type "HVAC"

# Filter by status and floor
arx filter --status "Maintenance" --floor 2

# Filter critical equipment in JSON format
arx filter --critical-only --format json

# Filter with limit
arx filter --equipment-type "Electrical" --limit 50 --verbose
```

**Equipment Status Values:**
- `Active`
- `Inactive`
- `Maintenance`
- `OutOfOrder`
- `Unknown`

---

### AR Integration

#### `arx ar-integrate`

Integrate AR scan data.

**Signature:**
```bash
arx ar-integrate --scan-file <FILE> --room <ROOM> --floor <FLOOR> --building <BUILDING> [OPTIONS]
```

**Required Options:**
- `--scan-file <FILE>`: AR scan data file (JSON)
- `--room <ROOM>`: Room name for the scan
- `--floor <FLOOR>`: Floor level (integer)
- `--building <BUILDING>`: Building identifier

**Optional Options:**
- `--commit` (flag): Commit changes to Git
- `--message <MESSAGE>` (optional): Commit message

**Examples:**

```bash
# Integrate AR scan
arx ar-integrate --scan-file scan.json --room "Conference Room 201" --floor 2 --building "Main Building"

# Integrate and commit
arx ar-integrate --scan-file scan.json --room "Lab 101" --floor 1 --building "Main Building" --commit --message "AR scan integration"
```

---

#### `arx ar pending`

Pending equipment management commands.

**Subcommands:**

##### `arx ar pending list`

List all pending equipment.

**Signature:**
```bash
arx ar pending list --building <BUILDING> [--floor <FLOOR>] [--verbose]
```

**Required Options:**
- `--building <BUILDING>`: Building name

**Optional Options:**
- `--floor <FLOOR>` (integer): Filter by floor level
- `--verbose` (flag): Show detailed information

**Examples:**

```bash
# List all pending equipment
arx ar pending list --building "Main Building"

# List pending equipment on floor 2
arx ar pending list --building "Main Building" --floor 2 --verbose
```

---

##### `arx ar pending confirm`

Confirm pending equipment.

**Signature:**
```bash
arx ar pending confirm <PENDING_ID> --building <BUILDING> [--commit]
```

**Arguments:**
- `PENDING_ID` (required): Pending equipment ID

**Options:**
- `--building <BUILDING>`: Building name
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Confirm pending equipment
arx ar pending confirm "pending-123" --building "Main Building" --commit
```

---

##### `arx ar pending reject`

Reject pending equipment.

**Signature:**
```bash
arx ar pending reject <PENDING_ID>
```

**Arguments:**
- `PENDING_ID` (required): Pending equipment ID

**Examples:**

```bash
# Reject pending equipment
arx ar pending reject "pending-123"
```

---

##### `arx ar pending batch-confirm`

Batch confirm multiple pending items.

**Signature:**
```bash
arx ar pending batch-confirm <ID1> <ID2> ... --building <BUILDING> [--commit]
```

**Arguments:**
- `<ID1> <ID2> ...` (required): Comma-separated list of pending IDs

**Options:**
- `--building <BUILDING>`: Building name
- `--commit` (flag): Commit changes to Git

**Examples:**

```bash
# Batch confirm multiple items
arx ar pending batch-confirm "pending-123" "pending-124" "pending-125" --building "Main Building" --commit
```

---

### Sensor Processing

#### `arx process-sensors`

Process sensor data and update equipment status.

**Signature:**
```bash
arx process-sensors --building <BUILDING> [--sensor-dir <DIR>] [--commit] [--watch]
```

**Required Options:**
- `--building <BUILDING>`: Building name to update

**Optional Options:**
- `--sensor-dir <DIR>` (default: "./sensor-data"): Directory containing sensor data files
- `--commit` (flag): Commit changes to Git
- `--watch` (flag): Continuously monitor for new sensor data

**Examples:**

```bash
# Process sensor data once
arx process-sensors --building "Main Building" --commit

# Process from custom directory
arx process-sensors --building "Main Building" --sensor-dir "./sensors" --commit

# Watch mode for continuous processing
arx process-sensors --building "Main Building" --watch
```

---

### System Commands

#### `arx config`

Manage configuration.

**Signature:**
```bash
arx config [--show] [--set <KEY=VALUE>] [--reset] [--edit]
```

**Options:**
- `--show` (flag): Show current configuration
- `--set <KEY=VALUE>` (optional): Set configuration value (format: section.key=value)
- `--reset` (flag): Reset to defaults
- `--edit` (flag): Edit configuration file

**Examples:**

```bash
# Show current configuration
arx config --show

# Set configuration value
arx config --set "building.auto_commit=false"

# Reset to defaults
arx config --reset

# Edit configuration file
arx config --edit
```

**Configuration Format:**
Configuration keys use dot notation: `section.key=value`

Example:
- `user.name="John Doe"`
- `building.auto_commit=true`
- `performance.max_parallel_threads=8`

---

#### `arx health`

Run system health diagnostics.

**Signature:**
```bash
arx health [--component <COMPONENT>] [--verbose]
```

**Options:**
- `--component <COMPONENT>` (optional): Check specific component (all, git, config, persistence, yaml)
- `--verbose` (flag): Show detailed diagnostics

**Examples:**

```bash
# Check all components
arx health

# Check specific component
arx health --component git --verbose

# Detailed health check
arx health --verbose
```

**Components:**
- `all` (default): Check all components
- `git`: Git integration
- `config`: Configuration loading
- `persistence`: Data persistence
- `yaml`: YAML processing

---

#### `arx watch`

Live monitoring dashboard.

**Signature:**
```bash
arx watch [--building <BUILDING>] [--floor <FLOOR>] [--room <ROOM>] [--refresh-interval <SEC>] [--sensors-only] [--alerts-only] [--log-level <LEVEL>]
```

**Options:**
- `--building <BUILDING>` (optional): Filter by building
- `--floor <FLOOR>` (optional): Filter by floor
- `--room <ROOM>` (optional): Filter by room
- `--refresh-interval <SEC>` (default: 5): Refresh interval in seconds
- `--sensors-only` (flag): Show only sensor data
- `--alerts-only` (flag): Show only alerts
- `--log-level <LEVEL>` (optional): Log level (error, warn, info, debug)

**Examples:**

```bash
# Watch all buildings
arx watch

# Watch specific building with custom refresh
arx watch --building "Main Building" --refresh-interval 10

# Watch only alerts
arx watch --alerts-only --log-level warn
```

---

#### `arx ifc`

IFC file processing commands.

**Subcommands:**

##### `arx ifc extract-hierarchy`

Extract building hierarchy from IFC file.

**Signature:**
```bash
arx ifc extract-hierarchy --file <FILE> [--output <OUTPUT>]
```

**Required Options:**
- `--file <FILE>`: IFC file path

**Optional Options:**
- `--output <OUTPUT>` (optional): Output YAML file path

**Examples:**

```bash
# Extract hierarchy
arx ifc extract-hierarchy --file building.ifc

# Extract hierarchy to specific output file
arx ifc extract-hierarchy --file building.ifc --output hierarchy.yaml
```

---

## Configuration API

ArxOS uses a hierarchical configuration system with environment variable overrides.

### Configuration Structure

```toml
[user]
name = "User Name"
email = "user@example.com"
organization = "Organization Name"  # Optional
commit_template = "feat: {operation} {building_name}"

[paths]
default_import_path = "./buildings"
backup_path = "./backups"
template_path = "./templates"
temp_path = "./temp"

[building]
default_coordinate_system = "WGS84"  # Options: WGS84, UTM, LOCAL
auto_commit = true
naming_pattern = "{building_name}-{timestamp}"
validate_on_import = true

[performance]
max_parallel_threads = 8  # Default: number of CPU cores
memory_limit_mb = 1024    # Default: 1024 MB (1 GB)
cache_enabled = true
cache_path = "./cache"
show_progress = true

[ui]
use_emoji = true
verbosity = "Normal"  # Options: Silent, Normal, Verbose, Debug
color_scheme = "Auto"  # Options: Auto, Always, Never
detailed_help = false
```

### Configuration Precedence

Configuration is loaded in the following order (highest to lowest priority):

1. **Environment Variables** (highest priority)
2. **Project Config** (`arx.toml` in current directory)
3. **User Config** (`~/.arx/config.toml`)
4. **Global Config** (`/etc/arx/config.toml`)
5. **Default Values** (lowest priority)

### Environment Variables

All configuration can be overridden using environment variables with the `ARX_` prefix:

| Configuration Key | Environment Variable | Type |
|------------------|---------------------|------|
| `user.name` | `ARX_USER_NAME` | String |
| `user.email` | `ARX_USER_EMAIL` | String |
| `user.organization` | `ARX_USER_ORGANIZATION` | String |
| `paths.default_import_path` | `ARX_DEFAULT_IMPORT_PATH` | Path |
| `paths.backup_path` | `ARX_BACKUP_PATH` | Path |
| `building.auto_commit` | `ARX_AUTO_COMMIT` | Boolean (true/false) |
| `performance.max_parallel_threads` | `ARX_MAX_THREADS` | Integer |
| `performance.memory_limit_mb` | `ARX_MEMORY_LIMIT_MB` | Integer |
| `ui.verbosity` | `ARX_VERBOSITY` | Enum (silent, normal, verbose, debug) |

### Default Values

| Setting | Default Value |
|---------|--------------|
| `user.name` | "ArxOS User" |
| `user.email` | "user@arxos.com" |
| `building.auto_commit` | `true` |
| `building.default_coordinate_system` | "WGS84" |
| `performance.max_parallel_threads` | Number of CPU cores |
| `performance.memory_limit_mb` | 1024 |
| `ui.verbosity` | "Normal" |
| `ui.use_emoji` | `true` |

For complete configuration documentation, see [Configuration Guide](./CONFIGURATION.md).

---

## Mobile FFI API

ArxOS provides Foreign Function Interface (FFI) bindings for iOS and Android applications.

### C FFI Functions

All C FFI functions are exported with the `arxos_` prefix and return JSON strings. All returned strings must be freed using `arxos_free_string()`.

#### Memory Management

**Critical:** All strings returned by FFI functions must be freed using `arxos_free_string()` to prevent memory leaks.

```c
// Correct usage pattern
char* result = arxos_list_rooms(building_name);
// Use result...
arxos_free_string(result);  // Must free!
```

---

#### `arxos_free_string`

Free a C string allocated by ArxOS.

**C Signature:**
```c
void arxos_free_string(char* ptr);
```

**Parameters:**
- `ptr`: Pointer to string returned from ArxOS FFI function

**Safety:**
- Must only be called with pointers returned from ArxOS FFI functions
- Safe to call with `NULL` pointer
- Must not be called twice with the same pointer

**Example:**
```c
char* rooms = arxos_list_rooms("Main Building");
// Use rooms...
arxos_free_string(rooms);
```

---

#### `arxos_last_error`

Get the last error code from the last operation.

**C Signature:**
```c
int arxos_last_error();
```

**Returns:**
- Error code as integer:
  - `0` = Success
  - `1` = NotFound
  - `2` = InvalidData
  - `3` = IoError
  - `99` = Unknown

**Example:**
```c
char* result = arxos_list_rooms(building_name);
int error_code = arxos_last_error();
if (error_code != 0) {
    // Handle error
    char* error_msg = arxos_last_error_message();
    printf("Error %d: %s\n", error_code, error_msg);
    arxos_free_string(error_msg);
}
arxos_free_string(result);
```

---

#### `arxos_last_error_message`

Get the last error message.

**C Signature:**
```c
char* arxos_last_error_message();
```

**Returns:**
- Error message string (must be freed with `arxos_free_string()`)
- Empty string if no error occurred

**Example:**
```c
if (arxos_last_error() != 0) {
    char* msg = arxos_last_error_message();
    printf("Error: %s\n", msg);
    arxos_free_string(msg);
}
```

---

#### `arxos_list_rooms`

List all rooms in a building.

**C Signature:**
```c
char* arxos_list_rooms(const char* building_name);
```

**Parameters:**
- `building_name`: UTF-8 null-terminated string with building identifier

**Returns:**
- JSON string with array of room objects
- Error JSON on failure (format: `{"error": "message"}`)
- Must be freed with `arxos_free_string()`

**Error Codes:**
- `NotFound` (1): Building not found
- `InvalidData` (2): Invalid building name format

**Example (C):**
```c
char* rooms_json = arxos_list_rooms("Main Building");
if (arxos_last_error() == 0) {
    // Parse JSON...
    printf("Rooms: %s\n", rooms_json);
}
arxos_free_string(rooms_json);
```

**Example (iOS/Swift):**
```swift
if let roomsJson = arxos_list_rooms("Main Building") {
    let roomsJsonString = String(cString: roomsJson)
    let rooms = try JSONDecoder().decode([Room].self, from: roomsJsonString.data(using: .utf8)!)
    arxos_free_string(roomsJson)
}
```

**Example (Android/Kotlin via JNI):**
```kotlin
val roomsJson = nativeListRooms("Main Building")
val rooms = Gson().fromJson(roomsJson, Array<Room>::class.java)
```

---

#### `arxos_get_room`

Get a specific room by ID.

**C Signature:**
```c
char* arxos_get_room(const char* building_name, const char* room_id);
```

**Parameters:**
- `building_name`: UTF-8 null-terminated string with building identifier
- `room_id`: UTF-8 null-terminated string with room ID or name

**Returns:**
- JSON string with room object
- Error JSON on failure
- Must be freed with `arxos_free_string()`

**Error Codes:**
- `NotFound` (1): Building or room not found
- `InvalidData` (2): Invalid parameter format

**Example:**
```c
char* room_json = arxos_get_room("Main Building", "room-123");
if (arxos_last_error() == 0) {
    // Parse JSON...
}
arxos_free_string(room_json);
```

---

#### `arxos_list_equipment`

List all equipment in a building.

**C Signature:**
```c
char* arxos_list_equipment(const char* building_name);
```

**Parameters:**
- `building_name`: UTF-8 null-terminated string with building identifier

**Returns:**
- JSON string with array of equipment objects
- Error JSON on failure
- Must be freed with `arxos_free_string()`

**Error Codes:**
- `NotFound` (1): Building not found
- `InvalidData` (2): Invalid building name format

**Example:**
```c
char* equipment_json = arxos_list_equipment("Main Building");
if (arxos_last_error() == 0) {
    // Parse JSON...
}
arxos_free_string(equipment_json);
```

---

#### `arxos_get_equipment`

Get a specific equipment item by ID.

**C Signature:**
```c
char* arxos_get_equipment(const char* building_name, const char* equipment_id);
```

**Parameters:**
- `building_name`: UTF-8 null-terminated string with building identifier
- `equipment_id`: UTF-8 null-terminated string with equipment ID or name

**Returns:**
- JSON string with equipment object
- Error JSON on failure
- Must be freed with `arxos_free_string()`

**Error Codes:**
- `NotFound` (1): Building or equipment not found
- `InvalidData` (2): Invalid parameter format

**Example:**
```c
char* equipment_json = arxos_get_equipment("Main Building", "VAV-301");
if (arxos_last_error() == 0) {
    // Parse JSON...
}
arxos_free_string(equipment_json);
```

---

#### `arxos_parse_ar_scan`

Parse AR scan data from JSON string.

**C Signature:**
```c
char* arxos_parse_ar_scan(const char* json_data);
```

**Parameters:**
- `json_data`: UTF-8 null-terminated JSON string with AR scan data

**Returns:**
- JSON string with parsed AR scan data
- Error JSON on failure
- Must be freed with `arxos_free_string()`

**Error Codes:**
- `InvalidData` (2): Invalid JSON format or missing required fields

**Example:**
```c
const char* scan_json = "{...}";  // AR scan JSON
char* result = arxos_parse_ar_scan(scan_json);
if (arxos_last_error() == 0) {
    // Use parsed scan data...
}
arxos_free_string(result);
```

---

#### `arxos_extract_equipment`

Process AR scan and extract equipment.

**C Signature:**
```c
char* arxos_extract_equipment(const char* json_data);
```

**Parameters:**
- `json_data`: UTF-8 null-terminated JSON string with AR scan data

**Returns:**
- JSON string with array of extracted equipment
- Error JSON on failure
- Must be freed with `arxos_free_string()`

**Error Codes:**
- `InvalidData` (2): Invalid JSON format or missing required fields

**Example:**
```c
const char* scan_json = "{...}";  // AR scan JSON
char* equipment_json = arxos_extract_equipment(scan_json);
if (arxos_last_error() == 0) {
    // Use extracted equipment...
}
arxos_free_string(equipment_json);
```

---

### JNI Functions

JNI functions follow the Java naming convention: `Java_com_arxos_mobile_service_ArxOSCoreJNI_<function_name>`

All JNI functions return JSON strings that must be parsed in Java/Kotlin code.

#### `nativeListRooms`

List all rooms in a building (JNI).

**Java Signature:**
```java
public native String nativeListRooms(String buildingName);
```

**Kotlin Signature:**
```kotlin
external fun nativeListRooms(buildingName: String): String
```

**Parameters:**
- `buildingName`: Building identifier

**Returns:**
- JSON string with array of room objects
- Error JSON on failure (format: `{"error": "message"}`)

**Example (Kotlin):**
```kotlin
val roomsJson = nativeListRooms("Main Building")
val rooms = Gson().fromJson(roomsJson, Array<RoomInfo>::class.java)
```

---

#### `nativeGetRoom`

Get a specific room by ID (JNI).

**Java Signature:**
```java
public native String nativeGetRoom(String buildingName, String roomId);
```

**Parameters:**
- `buildingName`: Building identifier
- `roomId`: Room ID or name

**Returns:**
- JSON string with room object
- Error JSON on failure

**Example:**
```kotlin
val roomJson = nativeGetRoom("Main Building", "room-123")
val room = Gson().fromJson(roomJson, RoomInfo::class.java)
```

---

#### `nativeListEquipment`

List all equipment in a building (JNI).

**Java Signature:**
```java
public native String nativeListEquipment(String buildingName);
```

**Returns:**
- JSON string with array of equipment objects
- Error JSON on failure

**Example:**
```kotlin
val equipmentJson = nativeListEquipment("Main Building")
val equipment = Gson().fromJson(equipmentJson, Array<EquipmentInfo>::class.java)
```

---

#### `nativeGetEquipment`

Get a specific equipment item by ID (JNI).

**Java Signature:**
```java
public native String nativeGetEquipment(String buildingName, String equipmentId);
```

**Parameters:**
- `buildingName`: Building identifier
- `equipmentId`: Equipment ID or name

**Returns:**
- JSON string with equipment object
- Error JSON on failure

**Example:**
```kotlin
val equipmentJson = nativeGetEquipment("Main Building", "VAV-301")
val equipment = Gson().fromJson(equipmentJson, EquipmentInfo::class.java)
```

---

#### `nativeParseARScan`

Parse AR scan data from JSON string (JNI).

**Java Signature:**
```java
public native String nativeParseARScan(String jsonData);
```

**Parameters:**
- `jsonData`: JSON string with AR scan data

**Returns:**
- JSON string with parsed AR scan data
- Error JSON on failure

**Example:**
```kotlin
val scanJson = "{...}"  // AR scan JSON
val result = nativeParseARScan(scanJson)
val scanData = Gson().fromJson(result, ARScanData::class.java)
```

---

#### `nativeExtractEquipment`

Process AR scan and extract equipment (JNI).

**Java Signature:**
```java
public native String nativeExtractEquipment(String jsonData);
```

**Parameters:**
- `jsonData`: JSON string with AR scan data

**Returns:**
- JSON string with array of extracted equipment
- Error JSON on failure

**Example:**
```kotlin
val scanJson = "{...}"  // AR scan JSON
val equipmentJson = nativeExtractEquipment(scanJson)
val equipment = Gson().fromJson(equipmentJson, Array<EquipmentInfo>::class.java)
```

---

### Data Structures

#### `RoomInfo`

Room information for mobile apps.

**JSON Structure:**
```json
{
  "id": "room-uuid",
  "name": "Conference Room 201",
  "type": "Office",
  "position": {
    "x": 5.0,
    "y": 10.0,
    "z": 2.0,
    "coordinate_system": "WGS84"
  },
  "equipment_count": 3
}
```

---

#### `EquipmentInfo`

Equipment information for mobile apps.

**JSON Structure:**
```json
{
  "id": "equipment-uuid",
  "name": "VAV-301",
  "type": "HVAC",
  "status": "Active",
  "position": {
    "x": 5.0,
    "y": 8.0,
    "z": 2.0,
    "coordinate_system": "WGS84"
  },
  "room_id": "room-uuid"
}
```

---

#### `ARScanData`

AR scan data structure.

**JSON Structure:**
```json
{
  "detectedEquipment": [
    {
      "name": "VAV Unit",
      "type": "HVAC",
      "position": {"x": 5.0, "y": 8.0, "z": 2.0},
      "confidence": 0.95,
      "boundingBox": {...}
    }
  ],
  "roomBoundaries": {
    "corners": [...]
  },
  "roomName": "Conference Room 201",
  "floorLevel": 2,
  "deviceType": "iOS",
  "appVersion": "1.0.0"
}
```

For complete mobile FFI documentation, see [Mobile FFI Integration](./MOBILE_FFI_INTEGRATION.md).

---

## Core Rust API

The core Rust API provides programmatic access to building data structures and operations.

### Main Types

#### `Building`

Root entity representing a building.

**Location:** `arxos::core::Building`

**Fields:**
- `id: String` - Unique identifier (UUID)
- `name: String` - Human-readable building name
- `path: String` - Universal path identifier
- `created_at: DateTime<Utc>` - Creation timestamp
- `updated_at: DateTime<Utc>` - Last modification timestamp
- `floors: Vec<Floor>` - Collection of floors

**Methods:**
- `new(name: String, path: String) -> Building` - Create new building
- `add_floor(floor: Floor)` - Add floor to building
- `find_floor(level: i32) -> Option<&Floor>` - Find floor by level

**Example:**
```rust
use arxos::core::Building;

let building = Building::new("Main Building".to_string(), "main-building".to_string());
building.add_floor(floor);
```

---

#### `Floor`

Represents a floor in a building.

**Location:** `arxos::core::Floor`

**Fields:**
- `level: i32` - Floor level number
- `name: String` - Floor name
- `wings: Vec<Wing>` - Collection of wings

---

#### `Wing`

Represents a wing on a floor.

**Location:** `arxos::core::Wing`

**Fields:**
- `name: String` - Wing name
- `rooms: Vec<Room>` - Collection of rooms

---

#### `Room`

Represents a room in a building.

**Location:** `arxos::core::Room`

**Fields:**
- `id: String` - Unique identifier (UUID)
- `name: String` - Human-readable room name
- `room_type: RoomType` - Type categorization
- `equipment: Vec<Equipment>` - Collection of equipment
- `spatial_properties: SpatialProperties` - Position, dimensions, bounding box
- `properties: HashMap<String, String>` - Key-value metadata
- `created_at: DateTime<Utc>` - Creation timestamp
- `updated_at: DateTime<Utc>` - Last modification timestamp

**Room Types:**
- `Classroom`
- `Laboratory`
- `Office` (default)
- `Gymnasium`
- `Cafeteria`
- `Library`
- `Auditorium`
- `Hallway`
- `Restroom`
- `Storage`
- `Mechanical`
- `Electrical`
- `Other(String)`

---

#### `Equipment`

Represents equipment in a building.

**Location:** `arxos::core::Equipment`

**Fields:**
- `id: String` - Unique identifier (UUID)
- `name: String` - Human-readable equipment name
- `path: String` - Universal path identifier
- `equipment_type: EquipmentType` - Type categorization
- `position: Position` - 3D spatial position
- `properties: HashMap<String, String>` - Key-value metadata
- `status: EquipmentStatus` - Operational status
- `room_id: Option<String>` - Reference to parent room

**Equipment Types:**
- `HVAC`
- `Electrical`
- `AV`
- `Furniture`
- `Safety`
- `Plumbing`
- `Network`
- `Other(String)`

**Equipment Status:**
- `Active`
- `Inactive`
- `Maintenance`
- `OutOfOrder`
- `Unknown`

---

#### `Position`

3D position with coordinate system.

**Location:** `arxos::core::Position`

**Fields:**
- `x: f64` - X coordinate
- `y: f64` - Y coordinate
- `z: f64` - Z coordinate
- `coordinate_system: String` - Coordinate system identifier

---

#### `Dimensions`

3D dimensions.

**Location:** `arxos::core::Dimensions`

**Fields:**
- `width: f64` - Width
- `height: f64` - Height
- `depth: f64` - Depth

---

#### `SpatialProperties`

Spatial properties of an entity.

**Location:** `arxos::core::SpatialProperties`

**Fields:**
- `position: Position` - 3D position
- `dimensions: Dimensions` - 3D dimensions
- `bounding_box: BoundingBox` - Bounding box
- `coordinate_system: String` - Coordinate system

**Methods:**
- `new(position: Position, dimensions: Dimensions, coordinate_system: String) -> SpatialProperties`

---

### Core Operations

#### `create_room`

Create a new room.

**Signature:**
```rust
pub fn create_room(
    building: &mut Building,
    floor_level: i32,
    wing_name: &str,
    name: String,
    room_type: RoomType,
    dimensions: Option<Dimensions>,
    position: Option<Position>
) -> Result<String, Box<dyn std::error::Error>>
```

**Returns:**
- `Ok(room_id)` on success
- `Err` on failure

---

#### `add_equipment`

Add equipment to a room.

**Signature:**
```rust
pub fn add_equipment(
    building: &mut Building,
    room_id: &str,
    name: String,
    equipment_type: EquipmentType,
    position: Position
) -> Result<String, Box<dyn std::error::Error>>
```

---

#### `list_rooms`

List all rooms in a building.

**Signature:**
```rust
pub fn list_rooms(building: &Building) -> Vec<Room>
```

---

#### `list_equipment`

List all equipment in a building or room.

**Signature:**
```rust
pub fn list_equipment(building: &Building, room_id: Option<&str>) -> Vec<Equipment>
```

---

#### `spatial_query`

Query spatial relationships.

**Signature:**
```rust
pub fn spatial_query(
    building: &Building,
    query_type: &str,
    entity_id: &str,
    params: &HashMap<String, String>
) -> Result<SpatialQueryResult, Box<dyn std::error::Error>>
```

---

For complete Rust API documentation, use `cargo doc --open` to view rustdoc documentation.

---

## Error Reference

### Error Types

#### `ArxError`

Main error type for ArxOS operations.

**Location:** `arxos::error::ArxError`

**Variants:**

##### `IfcProcessing`

IFC processing error.

```rust
ArxError::IfcProcessing {
    message: String,
    context: ErrorContext,
    source: Option<Box<dyn std::error::Error + Send + Sync>>,
}
```

---

##### `Configuration`

Configuration error.

```rust
ArxError::Configuration {
    message: String,
    context: ErrorContext,
    field: Option<String>,
}
```

---

##### `GitOperation`

Git operation error.

```rust
ArxError::GitOperation {
    message: String,
    context: ErrorContext,
    operation: String,
}
```

---

##### `Validation`

Validation error.

```rust
ArxError::Validation {
    message: String,
    context: ErrorContext,
    file_path: Option<String>,
}
```

---

##### `IoError`

I/O error.

```rust
ArxError::IoError {
    message: String,
    context: ErrorContext,
    path: Option<String>,
}
```

---

##### `YamlProcessing`

YAML processing error.

```rust
ArxError::YamlProcessing {
    message: String,
    context: ErrorContext,
    file_path: Option<String>,
}
```

---

##### `SpatialData`

Spatial data error.

```rust
ArxError::SpatialData {
    message: String,
    context: ErrorContext,
    entity_type: Option<String>,
}
```

---

### Error Codes (Mobile FFI)

| Code | Name | Description |
|------|------|-------------|
| `0` | `Success` | Operation completed successfully |
| `1` | `NotFound` | Resource not found |
| `2` | `InvalidData` | Invalid data format or content |
| `3` | `IoError` | I/O or file system error |
| `99` | `Unknown` | Unknown error |

### Error Context

All errors include an `ErrorContext` with:
- `suggestions: Vec<String>` - Helpful suggestions for resolving the error
- `recovery_steps: Vec<String>` - Step-by-step recovery instructions
- `debug_info: Option<String>` - Additional debugging information
- `help_url: Option<String>` - URL to help documentation
- `file_path: Option<String>` - File path where error occurred
- `line_number: Option<usize>` - Line number where error occurred

For complete error handling documentation, see [Error Handling Guide](./ERROR_HANDLING_GUIDE.md).

---

## Examples

### CLI Usage Examples

#### Complete Workflow: Import, Search, Render

```bash
# 1. Import building from IFC
arx import building.ifc --dry-run  # Preview first
arx import building.ifc

# 2. Search for HVAC equipment
arx search "VAV" --equipment --verbose

# 3. Filter by floor
arx filter --floor 2 --equipment-type "HVAC"

# 4. Render 3D visualization
arx render --building "Main Building" --three-d --show-status
```

---

#### AR Integration Workflow

```bash
# 1. Process AR scan
arx ar-integrate --scan-file scan.json --room "Conference Room 201" --floor 2 --building "Main Building"

# 2. List pending equipment
arx ar pending list --building "Main Building" --verbose

# 3. Confirm pending equipment
arx ar pending confirm "pending-123" --building "Main Building" --commit

# 4. Verify with render
arx render --building "Main Building" --floor 2 --show-rooms
```

---

#### Sensor Processing Workflow

```bash
# Process sensor data
arx process-sensors --building "Main Building" --commit

# Watch for new sensor data
arx process-sensors --building "Main Building" --watch

# Monitor with watch dashboard
arx watch --building "Main Building" --alerts-only
```

---

### FFI Integration Examples

#### iOS Swift Example

```swift
import Foundation

// List rooms
guard let roomsJson = arxos_list_rooms("Main Building") else {
    print("Failed to get rooms")
    return
}

let roomsString = String(cString: roomsJson)
let roomsData = roomsString.data(using: .utf8)!

do {
    let rooms = try JSONDecoder().decode([RoomInfo].self, from: roomsData)
    print("Found \(rooms.count) rooms")
    
    for room in rooms {
        print("- \(room.name)")
    }
} catch {
    print("Failed to parse rooms: \(error)")
}

// Always free the string
arxos_free_string(roomsJson)

// Check for errors
let errorCode = arxos_last_error()
if errorCode != 0 {
    let errorMsg = arxos_last_error_message()
    print("Error \(errorCode): \(String(cString: errorMsg!))")
    arxos_free_string(errorMsg)
}
```

---

#### Android Kotlin Example

```kotlin
import com.google.gson.Gson

// List rooms
val roomsJson = nativeListRooms("Main Building")
val rooms = Gson().fromJson(roomsJson, Array<RoomInfo>::class.java)

for (room in rooms) {
    println("- ${room.name}")
}

// Get specific room
val roomJson = nativeGetRoom("Main Building", "room-123")
val room = Gson().fromJson(roomJson, RoomInfo::class.java)

// Process AR scan
val scanJson = """
{
  "roomName": "Conference Room 201",
  "floorLevel": 2,
  "detectedEquipment": [...]
}
""".trimIndent()

val equipmentJson = nativeExtractEquipment(scanJson)
val equipment = Gson().fromJson(equipmentJson, Array<EquipmentInfo>::class.java)
```

---

#### Rust Programmatic Example

```rust
use arxos::core::{Building, Room, RoomType};
use arxos::core::operations::create_room;
use arxos::persistence::PersistenceManager;

// Load building data
let persistence = PersistenceManager::new("Main Building")?;
let mut building_data = persistence.load_building_data()?;

// Create a room
let room_id = create_room(
    &mut building_data,
    2,  // floor level
    "A",  // wing
    "Conference Room 201".to_string(),
    RoomType::Office,
    None,  // dimensions
    None,  // position
)?;

// Save changes
persistence.save_building_data(&building_data)?;

println!("Created room: {}", room_id);
```

---

## See Also

- [User Guide](./USER_GUIDE.md) - Tutorials and workflows
- [Configuration Guide](./CONFIGURATION.md) - Configuration details
- [Mobile FFI Integration](./MOBILE_FFI_INTEGRATION.md) - Mobile integration guide
- [Error Handling Guide](./ERROR_HANDLING_GUIDE.md) - Error handling patterns
- [Architecture](./ARCHITECTURE.md) - System architecture
- [Operations Guide](./OPERATIONS.md) - Operational procedures

---

**Document Version:** 2.0  
**Last Updated:** December 2024

