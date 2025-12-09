# CLI Reference

Complete command-line reference for ArxOS.

---

## Global Options

```bash
arx --help        # Show help
arx --version     # Show version
```

---

## Building Management

### `arx init`

Initialize a new building project.

```bash
arx init --name "Building Name" [OPTIONS]

Options:
  --name <NAME>                Building name (required)
  --description <DESC>         Building description
  --location <LOC>             Location/address
  --git-init                   Initialize Git repository
  --commit                     Commit initial building.yaml
  --coordinate-system <SYS>    Coordinate system (default: World)
  --units <UNITS>              Units (default: meters)
```

**Example:**
```bash
arx init --name "Office Tower" --location "NYC" --git-init --commit
```

---

### `arx import`

Import IFC file to building.yaml.

```bash
arx import <IFC_FILE> [OPTIONS]

Arguments:
  <IFC_FILE>    Path to IFC file

Options:
  --repo <URL>  Git repository URL
  --dry-run     Show what would be imported without changes
```

**Example:**
```bash
arx import building.ifc --dry-run
arx import building.ifc
```

---

### `arx export`

Export building data to various formats.

```bash
arx export [OPTIONS]

Options:
  --format <FMT>     Export format: git, ifc, gltf, usdz (default: git)
  --output <FILE>    Output file path (required for non-git formats)
  --repo <URL>       Git repository URL (for git format)
  --delta            Export only changes
```

**Examples:**
```bash
arx export --format ifc --output building-v2.ifc
arx export --format gltf --output model.gltf
arx export --format usdz --output model.usdz
```

---

## Visualization

### `arx render`

Render building visualization.

```bash
arx render --building <NAME> [OPTIONS]

Options:
  --building <NAME>           Building identifier (required)
  --floor <NUM>               Floor number
  --three-d                   Enable 3D multi-floor visualization
  --show-status               Show equipment status indicators
  --show-rooms                Show room boundaries
  --format <FMT>              Output format: ascii, advanced, json, yaml
  --projection <TYPE>         Projection: isometric, orthographic, perspective
  --view-angle <ANGLE>        View angle: topdown, front, side, isometric
  --scale <FACTOR>            Scale factor (default: 1.0)
  --spatial-index             Enable spatial indexing
  --interactive               Interactive WebGL-style renderer
  --brightness-style <STYLE>  ASCII brightness: acerola, classic, extended, unicode
```

**Examples:**
```bash
# Basic ASCII rendering
arx render --building "Office"

# Interactive 3D renderer (requires --features render3d)
arx render --building "Office" --interactive

# Specific floor with room boundaries
arx render --building "Office" --floor 2 --show-rooms
```

---

### `arx interactive`

Interactive 3D building visualization with real-time controls.

```bash
arx interactive --building <NAME> [OPTIONS]

Options:
  --building <NAME>           Building identifier (required)
  --projection <TYPE>         Projection type (default: isometric)
  --view-angle <ANGLE>        View angle (default: isometric)
  --scale <FACTOR>            Scale factor (default: 1.0)
  --width <CHARS>             Canvas width (default: 120)
  --height <CHARS>            Canvas height (default: 40)
  --spatial-index             Enable spatial index
  --show-status               Show equipment status
  --show-rooms                Show room boundaries
  --show-connections          Show equipment connections
  --fps <NUM>                 Target FPS 1-240 (default: 30)
  --show-fps                  Show FPS counter
  --show-help                 Show help overlay
  --brightness-style <STYLE>  Brightness style (default: acerola)
```

---

## Git Operations

### `arx status`

Show repository status and changes.

```bash
arx status [OPTIONS]

Options:
  --verbose      Show detailed status
  --interactive  Open interactive dashboard
```

---

### `arx stage`

Stage changes for commit.

```bash
arx stage [OPTIONS]

Options:
  --all          Stage all modified files
  <file>         Specific file to stage
```

**Examples:**
```bash
arx stage --all
arx stage building.yaml
```

---

### `arx commit`

Commit staged changes.

```bash
arx commit <MESSAGE>

Arguments:
  <MESSAGE>    Commit message (required)
```

**Example:**
```bash
arx commit "Added HVAC equipment to floor 3"
```

---

### `arx unstage`

Unstage changes.

```bash
arx unstage [OPTIONS]

Options:
  --all      Unstage all files
  <file>     Specific file to unstage
```

---

### `arx diff`

Show differences between commits.

```bash
arx diff [OPTIONS]

Options:
  --commit <HASH>   Compare with specific commit
  --file <PATH>     Show diff for specific file
  --stat            Show file statistics only
  --interactive     Open interactive viewer
```

**Examples:**
```bash
arx diff
arx diff --commit abc123
arx diff --file building.yaml --stat
```

---

### `arx history`

Show commit history.

```bash
arx history [OPTIONS]

Options:
  --limit <NUM>    Number of commits to show 1-1000 (default: 10)
  --verbose        Show detailed commit information
  --file <PATH>    Show history for specific file
```

**Examples:**
```bash
arx history
arx history --limit 50 --verbose
arx history --file building.yaml
```

---

## Search and Query

### `arx search`

Search building data.

```bash
arx search <QUERY> [OPTIONS]

Arguments:
  <QUERY>    Search query

Options:
  --equipment        Search in equipment names
  --rooms            Search in room names
  --buildings        Search in building names
  --case-sensitive   Case-sensitive search
  --regex            Use regex pattern matching
  --limit <NUM>      Max results 1-10000 (default: 50)
  --verbose          Show detailed results
  --interactive      Open interactive browser
```

**Examples:**
```bash
arx search "boiler"
arx search "hvac" --equipment --verbose
arx search "room-3.*" --regex --rooms
```

---

### `arx query`

Query equipment by ArxAddress pattern.

```bash
arx query <PATTERN> [OPTIONS]

Arguments:
  <PATTERN>    ArxAddress glob pattern with wildcards

Options:
  --format <FMT>    Output format: table, json, yaml (default: table)
  --verbose         Show detailed results
```

**Examples:**
```bash
# Find all boilers in mech rooms
arx query "/usa/ny/*/floor-*/mech/boiler-*"

# Find all equipment in kitchen on floor 02
arx query "/usa/ny/brooklyn/ps-118/floor-02/kitchen/*"

# Find all HVAC equipment
arx query "/usa/ny/*/ps-118/floor-*/hvac/*"
```

---

### `arx filter`

Filter building data by criteria.

```bash
arx filter [OPTIONS]

Options:
  --equipment-type <TYPE>    Equipment type filter
  --status <STATUS>          Equipment status filter
  --floor <NUM>              Floor filter
  --room <NAME>              Room filter
  --building <NAME>          Building filter
  --critical-only            Show only critical equipment
  --healthy-only             Show only healthy equipment
  --alerts-only              Show only equipment with alerts
  --format <FMT>             Output format: table, json, yaml
  --limit <NUM>              Max results (default: 100)
  --verbose                  Show detailed results
```

**Examples:**
```bash
arx filter --floor 2 --equipment-type HVAC
arx filter --alerts-only --format json
arx filter --building "Office" --critical-only
```

---

## Equipment Management

### `arx equipment list`

List all equipment.

### `arx equipment add`

Add equipment (via subcommand).

### `arx equipment update`

Update equipment properties.

### `arx equipment delete`

Remove equipment.

---

## Room Management

### `arx room list`

List all rooms.

### `arx room add`

Add a new room.

### `arx room update`

Update room properties.

### `arx room delete`

Remove a room.

---

## Sensor Integration

### `arx process-sensors`

Process sensor data files and update equipment status.

```bash
arx process-sensors --building <NAME> [OPTIONS]

Options:
  --building <NAME>          Building name (required)
  --sensor-dir <PATH>        Sensor data directory (default: ./sensor-data)
  --commit                   Commit changes to Git
  --watch                    Continuously monitor for new data
```

**Example:**
```bash
arx process-sensors --building "Office" --watch --commit
```

---

### `arx sensors-http`

Start HTTP server for real-time sensor data ingestion.

```bash
arx sensors-http --building <NAME> [OPTIONS]

Options:
  --building <NAME>    Building name (required)
  --host <ADDR>        Host address (default: 127.0.0.1)
  --port <PORT>        Port 1-65535 (default: 3000)
```

---

### `arx sensors-mqtt`

Start MQTT subscriber for sensor data ingestion.

```bash
arx sensors-mqtt --building <NAME> [OPTIONS]

Options:
  --building <NAME>    Building name (required)
  --broker <HOST>      MQTT broker URL (default: localhost)
  --port <PORT>        MQTT port (default: 1883)
  --username <USER>    MQTT username
  --password <PASS>    MQTT password
  --topics <TOPICS>    Topics to subscribe (default: arxos/sensors/#)
```

---

## AR Integration

### `arx ar-integrate`

Integrate AR scan data directly.

```bash
arx ar-integrate [OPTIONS]

Options:
  --scan-file <FILE>    AR scan JSON file (required)
  --room <NAME>         Room name (required)
  --floor <NUM>         Floor level (required)
  --building <NAME>     Building identifier (required)
  --commit              Commit changes to Git
  --message <MSG>       Commit message
```

---

### `arx ar`

AR integration commands (subcommands for workflow).

---

## IFC Commands

### `arx ifc <subcommand>`

IFC file processing commands. See subcommands for details.

---

## Spreadsheet Interface

### `arx spreadsheet <subcommand>`

Interactive spreadsheet editor for building data.

```bash
arx spreadsheet equipment    # Edit equipment
arx spreadsheet rooms        # Edit rooms
arx spreadsheet floors       # Edit floors
```

---

## Spatial Operations

### `arx spatial <subcommand>`

Spatial queries and coordinate transformations.

---

## Configuration

### `arx config`

Manage ArxOS configuration.

```bash
arx config [OPTIONS]

Options:
  --show           Show current configuration
  --set <KV>       Set config value (format: section.key=value)
  --reset          Reset to defaults
  --edit           Edit configuration file
  --interactive    Open configuration wizard
```

**Examples:**
```bash
arx config --show
arx config --set user.name="John Doe"
arx config --edit
```

---

## System Commands

### `arx health`

Run system health diagnostics.

```bash
arx health [OPTIONS]

Options:
  --component <NAME>    Check specific component: all, git, config, persistence, yaml
  --verbose             Show detailed diagnostics
  --interactive         Open interactive dashboard
  --diagnostic          Generate comprehensive report
```

---

### `arx validate`

Validate building data.

```bash
arx validate [OPTIONS]

Options:
  --path <PATH>    Path to building data
```

---

### `arx verify`

Verify GPG signatures on Git commits.

```bash
arx verify [OPTIONS]

Options:
  --commit <HASH>    Commit hash to verify (default: HEAD)
  --all              Verify all commits in branch
  --verbose          Show detailed verification info
```

---

### `arx migrate`

Migrate existing fixtures to ArxAddress format.

```bash
arx migrate [OPTIONS]

Options:
  --dry-run    Show what would be migrated without changes
```

---

## Web Interface

### `arx web`

Launch the Progressive Web App interface.

```bash
arx web

# Opens browser at http://localhost:8080
```

See [Web Interface](./web.md) for more details.

---

## Dashboard

### `arx dashboard`

Launch interactive TUI dashboard (requires `--features tui` and `--features agent`).

---

### `arx watch`

Live monitoring dashboard.

```bash
arx watch [OPTIONS]

Options:
  --building <NAME>         Building filter
  --floor <NUM>             Floor filter
  --room <NAME>             Room filter
  --refresh-interval <SEC>  Refresh interval 1-3600 (default: 5)
  --sensors-only            Show only sensor data
  --alerts-only             Show only alerts
  --log-level <LEVEL>       Log level
```

---

## User Management

### `arx users <subcommand>`

User management commands (admin permissions required for verify/revoke).

---

## Game System

### `arx game <subcommand>`

Gamified PR review and planning commands.

---

## Economy (Optional)

### `arx economy <subcommand>`

Economy and token operations (requires smart contracts deployment).

---

## Remote Operations

### `arx remote <subcommand>`

Manage remote building connections via SSH (requires `--features agent`).

---

## Advanced

### `arx merge`

Resolve merge conflicts interactively (requires `--features tui`).

### `arx sync`

Sync building data to IFC file (continuous or one-time).

```bash
arx sync [OPTIONS]

Options:
  --ifc <FILE>    Path to IFC file
  --watch         Enable watch mode for continuous sync
  --delta         Export only changes
```

### `arx doc`

Generate HTML documentation for a building.

```bash
arx doc --building <NAME> [--output <FILE>]
```

---

## Getting Help

```bash
arx --help                  # General help
arx <command> --help        # Command-specific help
arx <command> <sub> --help  # Subcommand help
```

---

**See Also:**
- [Getting Started](./getting-started.md)
- [Architecture](./architecture.md)
- [Data Format](./data-format.md)
