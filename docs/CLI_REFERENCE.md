# ArxOS CLI Reference Guide

## Command Structure

```bash
arx [verb] [path] [parameters] [options]
```

## Query Commands (Read Operations)

### Basic Queries

```bash
# Get specific equipment information
arx get /B1/3/SENSORS/TEMP-01

# Query with wildcards
arx query /B1/*/SENSORS/*
arx query /B1/3/*/HVAC/*

# List components in a location
arx list /B1/3/CONF-301
```

### Advanced Queries

```bash
# Filter by value thresholds
arx query /B1/*/SENSORS/TEMP-* --above 75
arx query /B1/*/ENERGY/* --below 50

# Filter by status
arx query /B1/3/*/HVAC/* --status failed
arx query /B1/*/*/* --status maintenance

# Search by type
arx find --type sensor --building B1 --floor 3
arx find --type outlet --status available

# Spatial queries (PostGIS-powered)
arx query --near "12.5,8.3,1.1" --radius 2.0
arx query --within-bounds "x1,y1,x2,y2"
arx query --on-floor 3 --building B1
```

### Live Monitoring

```bash
# Watch for changes
arx watch /B1/3/SENSORS/* --interval 5s

# Monitor with visualization
arx monitor /B1/3/*/ENERGY/* --graph
arx monitor /B1/*/TEMP/* --heatmap

# Stream real-time data
arx stream /B1/3/SENSORS/* --format json
```

### Historical Data

```bash
# View history
arx history /B1/3/HVAC/UNIT-01 --days 7
arx history /B1/*/ENERGY/* --since "2024-01-01"

# Analyze trends
arx trends /B1/*/ENERGY/* --compare yesterday
arx trends /B1/3/SENSORS/TEMP-* --period weekly
```

## Control Commands (Write Operations)

### Direct Control

```bash
# Set specific values
arx set /B1/3/HVAC/DAMPER-01 position:50
arx set /B1/3/LIGHTS/ZONE-A brightness:75
arx set /B1/3/DOORS/MAIN state:locked

# Adjust values
arx adjust /B1/3/HVAC/SETPOINT +2
arx adjust /B1/*/LIGHTS/* brightness:-10

# Toggle states
arx toggle /B1/3/LIGHTS/*
arx toggle /B1/*/DOORS/* --type magnetic
```

### Batch Operations

```bash
# Control multiple paths
arx set /B1/*/LIGHTS/* state:off
arx set /B1/3/*/HVAC/* mode:eco
arx set /B1/*/*/DOORS/* state:locked

# Apply configuration file
arx apply --file weekend-settings.yaml
arx apply --file emergency-shutdown.yaml --force

# Execute command list
arx batch execute commands.txt
```

### Scene Management

```bash
# Activate scenes
arx scene /B1/3/CONF-301 presentation
arx scene /B1/* night-mode
arx scene /B1/3/* energy-saving

# Save current state as scene
arx scene --save current-state --name comfortable
arx scene --save /B1/3/* --name "floor-3-default"

# List available scenes
arx scene --list
arx scene --list --location /B1/3/CONF-301

# Delete scene
arx scene --delete comfortable
```

### Scheduled Operations

```bash
# Schedule one-time actions
arx schedule /B1/*/LIGHTS/* off --at "10:00 PM"
arx schedule /B1/3/HVAC/* eco --at "2024-12-25 18:00"

# Recurring schedules
arx schedule /B1/3/HVAC/* eco --days "Sat,Sun"
arx schedule /B1/*/LIGHTS/* dim:30 --daily "22:00"
arx schedule /B1/*/HVAC/* maintenance --monthly 15

# View schedules
arx schedule --list
arx schedule --list --path /B1/3/*

# Cancel schedule
arx schedule --cancel schedule-id-123
```

## Natural Language Commands

### Basic Natural Language

```bash
# Simple commands
arx do "turn off all lights"
arx do "lock all doors"
arx do "set temperature to 72"

# Location-specific
arx do "turn off lights in conference room"
arx do "make it cooler on floor 3"
arx do "secure the east wing"
```

### Context-Aware Commands

```bash
# With context hints
arx do "make it cooler" --room /B1/3/CONF-301
arx do "save energy" --building B1
arx do "prepare for meeting" --room /B1/3/CONF-301

# Time-based context
arx do "prepare building for weekend"
arx do "activate night mode"
arx do "start morning routine"
```

### Complex Natural Language

```bash
# Conditional commands
arx do "if temperature above 75, increase cooling"
arx do "turn on lights where motion detected"
arx do "lock doors where nobody present"

# Multi-step operations
arx do "prepare conference room for presentation then dim lobby lights"
arx do "secure building and set HVAC to eco mode"
```

## Workflow Commands

### Workflow Management

```bash
# List workflows
arx workflow list
arx workflow list --active
arx workflow list --category maintenance

# Run workflows
arx workflow run emergency-shutdown
arx workflow run comfort-optimization --building B1
arx workflow trigger fire-evacuation --zone /B1/3/EAST

# Create workflows
arx workflow create --from-template hvac-optimization
arx workflow create --name "custom-routine" --file routine.yaml
```

### n8n Integration

```bash
# Connect to n8n
arx workflow connect --n8n-url http://localhost:5678
arx workflow connect --n8n-url https://n8n.company.com --api-key KEY

# Import/Export workflows
arx workflow import my-workflow.json
arx workflow export comfort-control --format n8n
arx workflow sync --bidirectional

# Workflow status
arx workflow status
arx workflow status workflow-id-123
arx workflow logs workflow-id-123 --tail 50
```

### Testing & Simulation

```bash
# Test workflows
arx workflow test fire-evacuation --dry-run
arx workflow test maintenance-routine --verbose

# Simulate scenarios
arx workflow simulate power-failure
arx workflow simulate fire-alarm --zone /B1/3/*
arx workflow simulate sensor-failure /B1/3/SENSORS/TEMP-01

# Validate workflows
arx workflow validate my-workflow.json
arx workflow validate --all
```

## Building Management Commands

### Building Operations

```bash
# Building status
arx building status B1
arx building status --all
arx building health B1

# Building control
arx building shutdown B1 --emergency
arx building startup B1 --normal
arx building optimize B1 --target energy
arx building optimize B1 --target comfort

# Building modes
arx building mode B1 --eco
arx building mode B1 --comfort
arx building mode B1 --security
```

### Floor Operations

```bash
# Floor control
arx floor /B1/3 --lights off
arx floor /B1/3 --hvac eco
arx floor /B1/3 --secure

# Floor status
arx floor status /B1/3
arx floor occupancy /B1/3
arx floor energy /B1/3 --period today
```

### Zone Operations

```bash
# Zone control
arx zone /B1/3/EAST --evacuate
arx zone /B1/*/PUBLIC --lights auto
arx zone /B1/3/SECURE --lockdown

# Zone management
arx zone create /B1/3/NEW --type office
arx zone delete /B1/3/OLD --confirm
arx zone merge /B1/3/EAST /B1/3/WEST --name COMBINED
```

## Diagnostic Commands

### System Health

```bash
# Health checks
arx health /B1
arx health /B1/3/HVAC/*
arx health --all --verbose

# Diagnostics
arx diagnose /B1/3/HVAC/*
arx diagnose /B1/*/SENSORS/* --deep
arx diagnose --system-wide

# Testing
arx test /B1/3/SENSORS/*
arx test /B1/*/SAFETY/* --emergency
arx test --all --report diagnostic.pdf
```

### Troubleshooting

```bash
# Troubleshoot equipment
arx troubleshoot /B1/3/HVAC/UNIT-01
arx troubleshoot /B1/*/FAILED/* --auto-fix
arx troubleshoot --wizard

# Validation
arx validate /B1/*/SAFETY/*
arx validate /B1/3/* --strict
arx validate --building B1 --compliance

# Calibration
arx calibrate /B1/3/SENSORS/TEMP-*
arx calibrate /B1/*/SENSORS/* --auto
arx calibrate --all --baseline reset
```

## Import/Export Commands

### Import Operations

```bash
# Import from files
arx import building.ifc --building B1
arx import floor-plan.pdf --building B1 --floor 3
arx import sensors.csv --merge

# Import with options
arx import data.ifc --validate --dry-run
arx import legacy.bim --confidence medium
arx import scan.las --point-cloud --align
```

### Export Operations

```bash
# Export formats
arx export B1 --format ifc
arx export B1 --format bim
arx export B1 --format pdf --template report
arx export B1 --format csv --data sensors

# Export with filters
arx export B1 --floor 3 --format ifc
arx export B1 --type HVAC --format json
arx export B1 --modified-since yesterday
```

## Repository Commands (Git-like)

### Repository Management

```bash
# Initialize repository
arx repo init B1
arx repo init B1 --remote https://github.com/org/building

# Status and changes
arx repo status
arx repo diff
arx repo diff --cached

# Commits
arx repo commit -m "Update HVAC settings"
arx repo commit --amend
arx repo log --oneline --graph
```

### Branching

```bash
# Branch operations
arx repo branch
arx repo branch renovation
arx repo checkout renovation
arx repo checkout -b emergency-fix

# Merging
arx repo merge renovation
arx repo merge --no-ff feature-branch
arx repo rebase main
```

## System Commands

### Installation & Setup

```bash
# Installation
arx install
arx install --with-postgis
arx install --professional --with-daemon
arx install --minimal

# Configuration
arx config set postgis.host localhost
arx config get server.port
arx config list
arx config reset
```

### Service Management

```bash
# Daemon control
arx daemon start
arx daemon stop
arx daemon restart
arx daemon status

# Server control
arx serve
arx serve --port 8080 --daemon
arx serve --stop
arx serve --status
```

### Maintenance

```bash
# Database operations
arx db backup
arx db restore backup-2024-01-01.sql
arx db optimize
arx db migrate

# System maintenance
arx cache clear
arx logs clean --older-than 30d
arx update
arx self-test
```

## Options & Flags

### Global Options

```bash
--verbose, -v        # Verbose output
--quiet, -q          # Suppress output
--format, -f         # Output format (json, yaml, table)
--config             # Custom config file
--no-color           # Disable colored output
--dry-run            # Preview without changes
--force              # Skip confirmations
--help, -h           # Show help
```

### Output Formats

```bash
# Format options
--format json        # JSON output
--format yaml        # YAML output
--format csv         # CSV output
--format table       # Table output (default)
--format raw         # Raw output
```

### Authentication

```bash
# Auth options
--api-key KEY        # API key authentication
--token TOKEN        # Bearer token
--user USER          # Username
--password PASS      # Password (not recommended in CLI)
```

## Environment Variables

```bash
# Configuration
ARXOS_CONFIG_PATH    # Config file location
ARXOS_DATABASE_URL   # Database connection
ARXOS_LOG_LEVEL      # Log verbosity

# Authentication
ARXOS_API_KEY        # API key
ARXOS_TOKEN          # Auth token

# Defaults
ARXOS_DEFAULT_BUILDING  # Default building ID
ARXOS_DEFAULT_FLOOR     # Default floor
ARXOS_OUTPUT_FORMAT     # Default output format
```

## Examples

### Morning Startup Routine

```bash
# Automated morning routine
arx scene /B1/* morning
arx set /B1/*/HVAC/* mode:comfort
arx set /B1/*/LIGHTS/PUBLIC/* state:on
arx workflow run morning-checks
```

### Emergency Response

```bash
# Fire emergency
arx workflow trigger fire-evacuation
arx set /B1/*/DOORS/* state:unlocked
arx set /B1/*/LIGHTS/EMERGENCY/* state:on
arx building broadcast "Emergency evacuation in progress"
```

### Energy Optimization

```bash
# Nightly energy saving
arx query /B1/*/SENSORS/OCCUPANCY/* --status empty | \
  xargs -I {} arx set {}/../../HVAC/* mode:eco
arx set /B1/*/LIGHTS/* state:off --except EMERGENCY
arx building mode B1 --eco
```

### Maintenance Mode

```bash
# Maintenance preparation
arx workflow run pre-maintenance-checks
arx zone /B1/3/EAST --maintenance-mode
arx set /B1/3/EAST/*/HVAC/* state:off
arx notify --team maintenance --message "Zone ready for maintenance"
```

## See Also

- [Architecture Documentation](ARCHITECTURE.md)
- [Hardware Integration Guide](../hardware.md)
- [n8n Workflow Documentation](../n8n.md)
- [API Reference](api.md)