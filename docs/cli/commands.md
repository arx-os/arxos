# Arxos CLI Commands Reference

This document provides a comprehensive reference for all Arxos CLI commands, organized by category and including usage examples, options, and detailed explanations.

## Table of Contents

1. [Initialization](#initialization)
2. [Navigation](#navigation)
3. [Inspection](#inspection)
4. [Search](#search)
5. [Management](#management)
6. [Version Control](#version-control)
7. [Operations](#operations)
8. [Export](#export)

## Initialization

### `arx init`

Initialize a new building workspace with the specified configuration.

**Usage:**
```bash
arx init [flags] <building-id>
```

**Flags:**
- `--area <area>`: Building area in square meters (e.g., "5000m²", "10,000 sqft")
- `--type <type>`: Building type (office, residential, industrial, retail, healthcare, educational)
- `--template <template>`: Use a predefined building template
- `--config <file>`: Path to custom configuration file
- `--force`: Overwrite existing building workspace

**Examples:**
```bash
# Basic initialization
arx init office-building-001

# With specific area and type
arx init warehouse-001 --area "25000m²" --type industrial

# Using a predefined template
arx init hospital-001 --template healthcare --area "15000m²"

# With custom configuration
arx init custom-building --config building-config.yaml
```

**What it creates:**
```
building-workspace/
├── .arxos/
│   ├── config/
│   │   ├── building.yaml          # Building configuration
│   │   ├── session.json           # Navigation session state
│   │   └── templates/             # Building templates
│   ├── cache/
│   │   └── index.json             # Building structure index
│   └── metadata/
│       ├── building-info.json     # Building metadata
│       └── version-info.json      # Version control info
├── floors/                        # Floor directories
├── systems/                       # Building systems
├── zones/                         # Functional zones
├── assets/                        # Building assets
└── config/                        # Additional configuration
```

## Navigation Commands

### `arx pwd` - Print Working Directory

Displays the current virtual working directory within the building structure.

**Usage:**
```bash
arx pwd
```

**Output:**
```
building:office-building-001/floor-1/systems/electrical
```

**Description:**
- Shows the current working directory in the virtual building filesystem
- Format: `building:<building-id><virtual-path>`
- Automatically detects building workspace and loads session state

---

### `arx cd` - Change Directory

Changes the current working directory within the virtual building structure.

**Usage:**
```bash
arx cd <path>
arx cd ..                    # Go to parent directory
arx cd /                     # Go to root
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

# Go back to parent directory
arx cd ..
```

**Features:**
- **Path Validation**: Ensures paths exist in the building structure
- **Relative/Absolute**: Supports both relative and absolute path navigation
- **Session Persistence**: Automatically saves navigation state
- **History Tracking**: Maintains previous working directory

**Output:**
```
✅ Changed directory to: /floor-1/systems/electrical
Current location: building:office-building-001/floor-1/systems/electrical
```

---

### `arx ls` - List Directory Contents

Lists the contents of the current or specified directory.

**Usage:**
```bash
arx ls [path] [options]
```

**Options:**
- `-l, --long`: Long format with detailed information
- `-t, --types`: Group entries by type
- `--tree`: Display as tree structure
- `-a, --all`: Show all entries including hidden

**Examples:**
```bash
# List current directory
arx ls

# List specific directory
arx ls /systems

# Long format
arx ls -l

# Group by type
arx ls -t

# Tree view
arx ls --tree
```

**Output Formats:**

**Standard List:**
```
📁 floor-1/          # Floor directory
📁 floor-2/          # Floor directory
📁 systems/          # Systems directory
📄 building.yaml     # Configuration file
```

**Long Format (`-l`):**
```
drwxr-xr-x  floor-1          floor     /floor-1
drwxr-xr-x  floor-2          floor     /floor-2
drwxr-xr-x  systems          system    /systems
-rw-r--r--  building.yaml    file      /building.yaml
```

**Type Grouping (`-t`):**
```
📁 FLOORS:
  floor-1/          /floor-1
  floor-2/          /floor-2

📁 SYSTEMS:
  systems/           /systems

📄 FILES:
  building.yaml      /building.yaml
```

---

### `arx tree` - Display Directory Tree

Displays the directory structure as a hierarchical tree.

**Usage:**
```bash
arx tree [path] [options]
```

**Options:**
- `-d, --depth <n>`: Limit tree depth (default: 3)
- `-c, --compact`: Compact display mode
- `-a, --all`: Show all entries including hidden

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
```

**Output:**
```
📁 /
├── 📁 floor-1/
│   ├── 📁 systems/
│   │   ├── 📁 electrical/
│   │   │   ├── 📄 panel-a.yaml
│   │   │   └── 📄 panel-b.yaml
│   │   └── 📁 hvac/
│   │       ├── 📄 unit-1.yaml
│   │       └── 📄 ductwork.yaml
│   └── 📁 floor-plan.pdf
├── 📁 floor-2/
└── 📄 building.yaml
```

---

### `arx find` - Search Building Objects

Search for building objects using text, filters, and advanced queries.

**Usage:**
```bash
arx find [query] [options]
```

**Options:**
- `-l, --limit <n>`: Maximum number of results (default: 50)
- `-f, --format <format>`: Output format (table, json, csv)

**Query Syntax:**
```
Text Search:     "search term"              # Search in names and descriptions
Type Filter:     type:floor                 # Filter by object type
Status Filter:   status:active              # Filter by status
Path Filter:     path:/systems/*            # Filter by path pattern
Property Filter: voltage:480V               # Filter by property values
Wildcard:        *                          # Find all objects
```

**Examples:**
```bash
# Find all electrical objects
arx find "electrical"

# Find all floors
arx find type:floor

# Find active systems
arx find status:active

# Find objects in systems directory
arx find path:/systems/*

# Combined search
arx find "hvac" type:system

# Find all objects (limit results)
arx find * --limit 10

# JSON output
arx find type:floor --format json

# CSV output
arx find status:active --format csv
```

**Output Formats:**

**Table Format (default):**
```
Name                                    Type           Path                         Metadata
---------------------------------------- --------------- ---------------------------- ------------------------------------------------
Electrical Panel A                      electrical_panel /systems/electrical/panel-a  status=active;voltage=480V
HVAC Unit 1                             hvac_unit      /systems/hvac/unit-1         status=active;capacity=5ton
Floor 1                                 floor          /floor-1                      level=1;area=10000sqft
```

**JSON Format:**
```json
[
  {
    "name": "Electrical Panel A",
    "type": "electrical_panel",
    "path": "/systems/electrical/panel-a",
    "is_dir": false
  }
]
```

**CSV Format:**
```csv
Name,Type,Path,IsDir,Metadata
"Electrical Panel A","electrical_panel","/systems/electrical/panel-a",false,"status=active;voltage=480V"
```

**Search Features:**
- **Text Search**: Searches names, descriptions, and metadata
- **Type Filtering**: Filter by object type (floor, system, equipment, etc.)
- **Status Filtering**: Filter by operational status
- **Path Filtering**: Filter by location in building structure
- **Property Filtering**: Filter by custom properties and metadata
- **Result Limiting**: Control number of results returned
- **Multiple Formats**: Table, JSON, and CSV output options
- **Case Insensitive**: All searches are case-insensitive
- **Wildcard Support**: Use `*` to find all objects

**Performance:**
- **Index-Based**: Uses the ArxObject indexer for fast searches
- **Caching**: Results are cached for improved performance
- **Efficient Filtering**: Applies filters during search execution
- **Scalable**: Handles large building structures efficiently

---

## Building Management Commands

### `arx add`

Add new components or files to the building workspace.

**Usage:**
```bash
arx add [path] [flags]
```

**Examples:**
```bash
# Add new floor
arx add /floors/3

# Add new system
arx add /systems/plumbing
```

### `arx remove`

Remove components or files from the building workspace.

**Usage:**
```bash
arx remove [path] [flags]
```

**Examples:**
```bash
# Remove floor
arx remove /floors/3

# Remove system
arx remove /systems/plumbing
```

### `arx move`

Move or rename building components.

**Usage:**
```bash
arx move [source] [destination]
```

**Examples:**
```bash
# Rename floor
arx move /floors/1 /floors/ground

# Move system
arx move /systems/hvac /systems/climate
```

## Version Control

### `arx commit`

Commit changes to the building workspace with a descriptive message.

**Usage:**
```bash
arx commit -m "message"
```

**Examples:**
```bash
# Commit with message
arx commit -m "Added new HVAC system"

# Commit all changes
arx commit -m "Updated building configuration"
```

### `arx log`

Display commit history for the building workspace.

**Usage:**
```bash
arx log [flags]
```

**Flags:**
- `--oneline`: Compact one-line format
- `--graph`: Show commit graph
- `--since <date>`: Show commits since date

**Examples:**
```bash
# Show commit history
arx log

# Compact format
arx log --oneline

# Show recent commits
arx log --since "2024-01-01"
```

### `arx diff`

Show differences between working directory and last commit.

**Usage:**
```bash
arx diff [path]
```

**Examples:**
```bash
# Show all changes
arx diff

# Show changes in specific path
arx diff /systems/hvac
```

## Operations

### `arx validate`

Validate the building configuration and identify any issues.

**Usage:**
```bash
arx validate [flags]
```

**Flags:**
- `--strict`: Enable strict validation
- `--fix`: Automatically fix minor issues

**Examples:**
```bash
# Basic validation
arx validate

# Strict validation
arx validate --strict

# Auto-fix issues
arx validate --fix
```

### `arx deploy`

Deploy building configuration to target environment.

**Usage:**
```bash
arx deploy [environment] [flags]
```

**Examples:**
```bash
# Deploy to development
arx deploy dev

# Deploy to production
arx deploy prod
```

### `arx rollback`

Rollback to previous building configuration version.

**Usage:**
```bash
arx rollback [commit] [flags]
```

**Examples:**
```bash
# Rollback to last commit
arx rollback HEAD~1

# Rollback to specific commit
arx rollback abc123
```

## Export

### `arx export`

Export building data in various formats.

**Usage:**
```bash
arx export [format] [path] [flags]
```

**Formats:**
- `json`: JSON format
- `yaml`: YAML format
- `csv`: CSV format
- `pdf`: PDF report

**Examples:**
```bash
# Export to JSON
arx export json

# Export specific system
arx export yaml /systems/hvac

# Export to PDF
arx export pdf --output building-report.pdf
```

## Watch Command

Monitor building files and ArxObjects for real-time changes and automatically update the index.

```bash
arx watch [options]
```

### Description

The `arx watch` command starts a comprehensive monitoring system that watches both file system changes and
ArxObject-specific events. When changes are detected, it can automatically rebuild the index, track ArxObject
properties, relationships, and validation status.

### Features

- **Real-time file system monitoring** - Watch for file creation, modification, deletion, and permission changes
- **ArxObject monitoring** - Track ArxObject properties, relationships, and validation status
- **Automatic index rebuilding** - Keep the building index up-to-date automatically
- **Change notifications** - Get real-time alerts for building modifications
- **Performance metrics** - Track event processing times and memory usage
- **Configurable ignore patterns** - Skip temporary files, logs, and build artifacts
- **Debounced event processing** - Batch rapid changes to avoid excessive updates

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--events, -e <types>` | Event types to watch (all, modify, create, delete, move, chmod) | `all` |
| `--severity, -s <level>` | Minimum severity level (debug, info, warning, error, critical) | `info` |
| `--format, -f <format>` | Output format (text, json, csv, xml) | `text` |
| `--alerts, -a` | Enable alert system | `false` |
| `--dashboard, -d` | Start live dashboard mode | `false` |
| `--refresh, -r <duration>` | Refresh rate for dashboard mode | `1s` |
| `--filters, -F <key=value>` | Additional filters | `[]` |
| `--no-auto-rebuild` | Disable automatic index rebuilding | `false` |
| `--debounce <duration>` | Set debounce delay for file events | `2s` |
| `--ignore <patterns>` | Additional patterns to ignore | `.git`, `.arxos/cache`, `*.tmp`, `*.log` |
| `--status` | Show watcher status and exit | `false` |
| `--quiet`, `-q` | Quiet mode (minimal output) | `false` |
| `--arxobject` | Enable ArxObject monitoring | `false` |
| `--properties` | Monitor ArxObject properties | `false` |
| `--relationships` | Monitor ArxObject relationships | `false` |
| `--validation` | Monitor validation status | `false` |

### Examples

```bash
# Start watching with default settings
arx watch

# Watch without auto-index rebuilding
arx watch --no-auto-rebuild

# Set 5-second debounce delay
arx watch --debounce 5s

# Ignore temporary and log files
arx watch --ignore "*.tmp,*.log"

# Show current watcher status
arx watch --status

# Quiet mode for background operation
arx watch --quiet

# Enable ArxObject monitoring
arx watch --arxobject

# Monitor specific ArxObject aspects
arx watch --arxobject --properties --relationships --validation

# Comprehensive monitoring with custom settings
arx watch --arxobject --properties --relationships --validation --debounce 1s --quiet
```

### Subcommands

#### `arx watch dashboard`

Start live dashboard for real-time building monitoring.

**Flags:**
- `--fullscreen, -F`: Fullscreen dashboard mode
- `--theme, -t <theme>`: Dashboard theme (default, dark, light, high-contrast)
- `--layout, -l <layout>`: Dashboard layout (standard, compact, detailed, minimal)
- `--refresh, -r <duration>`: Refresh rate for dashboard updates (default: 1s)
- `--auto-start, -a`: Auto-start monitoring on dashboard launch

**Examples:**
```bash
# Start dashboard with default view
arx watch dashboard

# Fullscreen dashboard mode
arx watch dashboard --fullscreen

# Use dark theme with compact layout
arx watch dashboard --theme=dark --layout=compact

# Set 5-second refresh rate
arx watch dashboard --refresh=5s
```

**Dashboard Features:**
- Live ArxObject changes and events
- Building health metrics and validation status
- Real-time performance statistics
- Alert notifications and status
- Multiple layout options
- Configurable themes and refresh rates

#### `arx watch alerts`

Manage and view alert rules and notifications.

**Flags:**
- `--action, -a <action>`: Action to perform (list, create, modify, delete, test, history)
- `--rule, -r <name>`: Alert rule name for specific actions
- `--condition, -c <expr>`: Alert condition expression
- `--severity, -s <level>`: Alert severity level

**Examples:**
```bash
# List all alert rules
arx watch alerts list

# Create new alert rule
arx watch alerts create --rule="validation_failure" --condition="validation_error"

# Test alert rule
arx watch alerts test --rule="high_frequency"

# View alert history
arx watch alerts history
```

#### `arx watch stats`

Show real-time watch statistics and metrics.

**Flags:**
- `--live, -l`: Live updating statistics
- `--export, -e <format>`: Export format (csv, json, xml)
- `--period, -p <duration>`: Statistics period (1s, 1m, 5m, 1h)

**Examples:**
```bash
# Show current statistics
arx watch stats

# Live updating statistics
arx watch stats --live

# Export statistics to CSV
arx watch stats --export=csv
```

#### `arx watch status`

Show the current status of the file watcher.

```bash
arx watch status
```

Displays information about:
- Whether the watcher is running
- Number of directories being monitored
- Total changes detected
- Last index update time
- Current configuration

#### `arx watch start`

Start the file watcher in the background.

```bash
arx watch start [options]
```

This command starts the file watcher and returns immediately, allowing you to continue using the terminal while the watcher runs in the background.

#### `arx watch stop`

Stop the currently running file watcher.

```bash
arx watch stop
```

This command stops the file watcher if it's currently running in the background.

### Configuration

The watcher can be configured through the `WatcherConfig` structure:

```go
type WatcherConfig struct {
    Enabled           bool          // Whether the watcher is enabled
    WatchInterval     time.Duration // How often to check for changes
    DebounceDelay    time.Duration // Delay before processing events
    MaxConcurrent    int           // Maximum concurrent operations
    IgnorePatterns   []string      // Patterns to ignore
    AutoRebuildIndex bool          // Auto-rebuild index on changes
    NotifyOnChange   bool          // Send notifications on changes
}
```

### Performance

The file watcher is designed for high performance:

- **Event batching** - Multiple rapid changes are batched together
- **Debounced processing** - Configurable delay prevents excessive updates
- **Efficient monitoring** - Uses native file system events when available
- **Memory management** - Automatic cleanup of old events and metadata
- **Concurrent processing** - Multiple events processed simultaneously

### Integration

The watcher integrates seamlessly with other Arxos commands:

- **Index updates** - Automatically keeps the building index current
- **Search results** - Real-time updates to search queries
- **Navigation** - Live updates to directory listings and tree views
- **Session management** - Works with existing CLI session state

### Use Cases

- **Development workflows** - Monitor building changes during development
- **CI/CD pipelines** - Automatic index updates in build processes
- **Field operations** - Real-time updates from field users
- **Building maintenance** - Track changes to building infrastructure
- **Audit trails** - Maintain history of building modifications

## Workflow Examples

### Basic Building Navigation
```bash
# Initialize building
arx init office-building-001 --type office --area "5000m²"

# Navigate and explore
arx cd /systems
arx ls -l
arx cd hvac
arx tree

# Return to root
arx cd /
arx pwd
```

### System Management
```bash
# Navigate to systems
arx cd /systems

# List all systems
arx ls -t

# Explore specific system
arx cd hvac
arx tree --depth 2

# Check system status
arx status
```

### Configuration Review
```bash
# Navigate to config
arx cd /config

# List configuration files
arx ls -l

# Search for specific settings
arx grep "temperature"

# Validate configuration
arx validate
```

## Indexer Integration

All navigation commands now use the **ArxObject Indexer** which:

- **Scans the building workspace** to discover the actual structure
- **Caches building data** under `.arxos/cache/index.json` for performance
- **Provides real-time data** instead of placeholder information
- **Automatically rebuilds** when the cache is stale or missing
- **Supports all building types** with consistent navigation patterns

The indexer ensures that `cd`, `ls`, and `tree` commands always show accurate, up-to-date information about your building structure, making navigation reliable and informative.

---

## AQL Query Commands

The `arx query` command provides access to the Arxos Query Language (AQL) for building data operations.

### Basic Query Commands

#### `arx query select [query]`
Execute SELECT queries on ArxObjects.

**Examples:**
```bash
arx query select "* FROM building:hq:floor:3 WHERE type = 'wall'"
arx query select "id, type, confidence FROM building:* WHERE confidence < 0.7"
```

#### `arx query update [query]`
Update ArxObject properties.

**Examples:**
```bash
arx query update "wall_123 SET confidence = 0.95"
```

#### `arx query validate [object_id]`
Mark objects as field-validated.

**Examples:**
```bash
arx query validate wall_123 --photo=wall.jpg
```

#### `arx query history [object_id]`
View object version history.

**Examples:**
```bash
arx query history wall_123
```

#### `arx query diff [object_id]`
Compare object versions.

**Examples:**
```bash
arx query diff wall_123 --from=2024-01-01 --to=2024-01-15
```

### Power User Experience Commands (Sprint 2)

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

#### `arx query shell`
Start interactive AQL shell for building and testing queries.

**Features:**
- REPL (Read-Eval-Print Loop) experience
- Command history with up/down arrows
- Auto-completion for ArxObject types and properties
- Query templates and examples
- Built-in help system

**Examples:**
```bash
arx query shell
arx query shell --format=json --history=false
arx query shell --auto-complete=false
```

**Shell Commands:**
- `help`: Show available commands
- `:format <format>`: Set output format
- `:history`: Show command history
- `:clear`: Clear screen
- `:templates`: Show query templates
- `:examples`: Show query examples
- `exit` or `quit`: Exit shell

**Flags:**
- `--format`: Default output format
- `--history`: Enable command history
- `--auto-complete`: Enable auto-completion

#### `arx query navigate [path]`
Navigate through building hierarchy with spatial awareness.

**Features:**
- Hierarchical path navigation (building:floor:room:equipment)
- Spatial queries (near, within, connected)
- Relationship traversal (parent, children, siblings)
- Breadcrumb navigation
- Spatial context awareness

**Examples:**
```bash
arx query navigate building:hq:floor:3
arx query navigate --near=room:305 --radius=10m
arx query navigate --connected=electrical_panel:e1
arx query navigate --spatial=3d --view=ascii-bim
arx query navigate --view=tree --breadcrumbs=true
```

**Flags:**
- `--near`: Navigate to objects near specified location
- `--radius`: Radius for near queries (e.g., 5m, 10ft)
- `--connected`: Navigate through connected objects
- `--spatial`: Spatial mode (2d, 3d, ascii-bim)
- `--view`: View mode (tree, list, ascii-bim, spatial)
- `--breadcrumbs`: Show navigation breadcrumbs
- `--relationships`: Show object relationships

#### `arx query templates [category]`
Show and use AQL query templates for common building operations.

**Features:**
- Pre-built templates for common operations
- Categorized templates (equipment, spatial, maintenance, energy, validation)
- Parameterized templates with type validation
- Template examples and usage documentation

**Categories:**
- **equipment**: HVAC, electrical, mechanical equipment queries
- **spatial**: Room, floor, building spatial queries
- **maintenance**: Maintenance schedules and work orders
- **energy**: Energy consumption and efficiency
- **validation**: Field validation and quality checks

**Examples:**
```bash
arx query templates equipment
arx query templates --use=hvac_equipment --params="floor=3,status=active"
arx query templates --list --category=spatial
arx query templates --use=maintenance_schedule --params="days=7,priority=high"
```

**Flags:**
- `--use`: Use a specific template by name
- `--params`: Template parameters (key=value,key=value)
- `--list`: List available templates
- `--category`: Filter templates by category
- `--format`: Output format for template results

**Built-in Templates:**
- **hvac_equipment**: Find HVAC equipment with optional filters
- **electrical_panels**: Find electrical panels and distribution equipment
- **room_contents**: Find all objects within a specific room
- **floor_overview**: Get overview of all objects on a specific floor
- **maintenance_schedule**: Find equipment requiring maintenance
- **energy_consumption**: Analyze energy consumption patterns
- **validation_status**: Check field validation status of objects

---

## Dashboard Commands

The `arx dashboard` command provides live monitoring and real-time intelligence for building operations.

### `arx dashboard`

Start live dashboard for real-time building monitoring.

**Flags:**
- `--theme, -t <theme>`: Dashboard theme (default, dark, light, high-contrast)
- `--layout, -l <layout>`: Dashboard layout (standard, compact, detailed, minimal)
- `--fullscreen, -F`: Fullscreen dashboard mode
- `--refresh, -r <duration>`: Refresh rate for dashboard updates (default: 1s)
- `--auto-start, -a`: Auto-start monitoring on dashboard launch

**Examples:**
```bash
# Start dashboard with default view
arx dashboard

# Start with custom configuration
arx dashboard --theme=dark --layout=compact --refresh=5s

# Fullscreen dashboard with auto-start monitoring
arx dashboard --fullscreen --auto-start
```

**Dashboard Features:**
- Live ArxObject changes and events
- Building health metrics and validation status
- Real-time performance statistics
- Alert notifications and status
- Multiple layout options (standard, compact, detailed, minimal)
- Configurable themes and refresh rates
- Auto-start monitoring capabilities

**Layout Options:**
- **Standard**: Comprehensive overview with all metrics
- **Compact**: Condensed view for quick monitoring
- **Detailed**: Extended view with recent events and data quality
- **Minimal**: Single-line status display

---

## Alert Management Commands

The `arx alerts` command provides comprehensive alert management and notification system for building operations.

### `arx alerts`

Manage building alerts and notifications.

**Flags:**
- `--action, -a <action>`: Action to perform (list, create, modify, delete, test, history, configure)
- `--rule, -r <name>`: Alert rule name for specific actions
- `--condition, -c <expr>`: Alert condition expression
- `--severity, -s <level>`: Alert severity level
- `--threshold, -t <count>`: Alert threshold count
- `--time-window, -w <duration>`: Alert time window

**Examples:**
```bash
# List all alert rules
arx alerts list

# Create new alert rule
arx alerts create --rule="high_frequency" --condition="events_per_second > 10" --severity=warning

# Test alert rule
arx alerts test --rule="validation_failure"

# View alert history
arx alerts history

# Configure alert system
arx alerts configure
```

**Alert System Features:**
- Rule-based alert triggering with configurable conditions
- Multiple severity levels (debug, info, warning, error, critical)
- Threshold and time window configuration
- Multi-channel notification system (console, email, Slack, webhook)
- Alert lifecycle management (active, acknowledged, resolved)
- Escalation policies for critical alerts
- Auto-resolution with configurable timeouts

---

## ArxObject Management Commands

The ArxObject management commands provide comprehensive control over building components, including metadata persistence, relationship management, validation, and lifecycle tracking.

### `arx arxobject [command]`

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

#### `arx arxobject relate [source-id] [target-id]`
Manage relationships between ArxObjects.

**Features:**
- Bidirectional relationship creation
- Multiple relationship types (contains, connects_to, adjacent_to, etc.)
- Confidence scoring for relationships
- Relationship properties and metadata
- Automatic relationship cleanup

**Examples:**
```bash
arx arxobject relate building:main:floor:1 building:main:system:electrical --type contains
arx arxobject relate building:main:room:101 building:main:room:102 --type adjacent_to --confidence 0.9
arx arxobject relate building:main:panel:e1 building:main:outlet:o1 --type connects_to --action remove
```

**Flags:**
- `--type`: Relationship type (contains, connects_to, adjacent_to, etc.)
- `--confidence`: Relationship confidence (0.0 to 1.0)
- `--action`: Action to perform (add, remove)

#### `arx arxobject lifecycle [object-id]`
Manage ArxObject lifecycle status and phases.

**Features:**
- Lifecycle status management (active, inactive, retired, maintenance, testing)
- Phase tracking and transitions
- Automatic timestamp recording
- Lifecycle notes and documentation
- Status history tracking

**Examples:**
```bash
arx arxobject lifecycle building:main:system:hvac --status active --phase operational
arx arxobject lifecycle building:main:equipment:chiller --status maintenance --phase repair
arx arxobject lifecycle building:main:panel:old --status retired --phase decommissioned --notes "Replaced with new panel"
```

**Flags:**
- `--status`: Lifecycle status (active, inactive, retired, maintenance, testing)
- `--phase`: Lifecycle phase description
- `--notes`: Lifecycle notes and comments

#### `arx arxobject search [query]`
Search ArxObjects with advanced filtering capabilities.

**Features:**
- Text-based search across names, descriptions, and types
- Multiple filter criteria (type, status, validation, floor, confidence)
- Tag-based filtering
- Location-based filtering
- Confidence threshold filtering

**Examples:**
```bash
arx arxobject search "electrical" --building building:main --type system
arx arxobject search "hvac" --building building:main --floor 1 --status active
arx arxobject search "panel" --building building:main --validation validated --confidence-min 0.8
arx arxobject search "equipment" --building building:main --tags "critical,maintenance"
```

**Flags:**
- `--building`: Building ID to search in (required)
- `--type`: Filter by object type
- `--status`: Filter by status
- `--validation`: Filter by validation status
- `--floor`: Filter by floor number
- `--confidence-min`: Minimum confidence threshold
- `--tags`: Filter by tags (comma-separated)

#### `arx arxobject stats [building-id]`
Display comprehensive ArxObject statistics for a building.

**Features:**
- Total ArxObject counts
- Breakdown by type, status, and validation
- Floor-by-floor statistics
- Confidence metrics and averages
- Validation coverage statistics

**Examples:**
```bash
arx arxobject stats building:main
arx arxobject stats building:hq
```

#### `arx arxobject export [building-id]`
Export ArxObjects to various formats for external analysis.

**Features:**
- Multiple export formats (JSON, CSV)
- Filtered exports based on criteria
- File output or stdout
- Comprehensive metadata inclusion
- Customizable export fields

**Examples:**
```bash
arx arxobject export building:main --format json
arx arxobject export building:main --format csv --type system --output systems.csv
arx arxobject export building:main --format csv --status active --floor 1 --output active_floor1.csv
```

**Flags:**
- `--format`: Export format (json, csv)
- `--output`: Output file path (default: stdout)
- `--type`: Filter by object type
- `--status`: Filter by status
- `--floor`: Filter by floor number

### ArxObject Management Workflow

**Typical Workflow:**
1. **Initialize Building**: `arx init building:main --type office --floors 3`
2. **Validate Components**: `arx arxobject validate building:main:floor:1 --method photo --confidence 0.9`
3. **Create Relationships**: `arx arxobject relate building:main:floor:1 building:main:system:electrical --type contains`
4. **Update Lifecycle**: `arx arxobject lifecycle building:main:system:hvac --status active --phase operational`
5. **Search and Analyze**: `arx arxobject search "electrical" --type system --floor 1`
6. **Export Data**: `arx arxobject export building:main --format csv --type system --output systems.csv`

**Use Cases:**
- **Field Validation**: Photo-based validation with confidence scoring
- **Maintenance Planning**: Lifecycle status tracking for proactive maintenance
- **Compliance Reporting**: Comprehensive audit trails and validation history
- **Data Analysis**: Export capabilities for external analysis tools
- **Relationship Mapping**: Understanding building component connections
- **Quality Assurance**: Confidence scoring and validation tracking
