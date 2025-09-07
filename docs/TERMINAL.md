# ArxOS Terminal Guide

## Overview

The ArxOS terminal provides a filesystem-like interface for navigating and querying building infrastructure. Buildings are organized as hierarchical paths that can be explored and queried like a database.

## Starting the Terminal

```bash
# Basic startup
arxos

# With specific database
arxos -d postgresql://localhost/arxos

# With specific building
arxos -b building_42
```

## Command Reference

### Navigation Commands

#### `CD <path>`
Change to a different directory in the building hierarchy.

```
arxos:/> cd electrical
arxos:/electrical> cd circuits/2
arxos:/electrical/circuits/2> cd /plumbing
arxos:/plumbing> cd ..
arxos:/> 
```

#### `LS [path]`
List contents of current or specified directory.

```
arxos:/electrical> ls
  panels/
  circuits/
  outlets/
  breaker_main [OK]
  meter_1 [OK]

arxos:/electrical> ls circuits
  1/
  2/
  3/
  main_breaker [OK]
```

#### `PWD`
Print current working directory.

```
arxos:/electrical/circuits/2> pwd
/electrical/circuits/2
```

#### `LOOK`
Describe the current location and nearby objects.

```
arxos:/electrical/circuits/2> look
Current location: /electrical/circuits/2

You see:
  - outlet_2A (outlet)
  - outlet_2B (outlet)
  - outlet_2C (outlet)
  - switch_2A (switch)
```

### Inspection Commands

#### `INSPECT <object>`
Show detailed information about an object.

```
arxos:/electrical> inspect outlet_2B
╔════════════════════════════════════════════╗
║ Object: outlet_2B                          ║
╚════════════════════════════════════════════╝

Path:     /electrical/circuits/2/outlet_2B
Type:     outlet
Status:   active
Health:   95

Properties:
  voltage: 120
  amperage: 15
  ground_fault: false

Metrics:
  power_draw: 250
  last_trip: null
```

#### `TRACE <object> <UPSTREAM|DOWNSTREAM>`
Trace connections through the building systems.

```
arxos:/electrical> trace outlet_2B upstream
Tracing upstream from outlet_2B:
  → circuit_2
    → panel_1
      → main_breaker
        → meter_1
          → utility_connection
```

#### `NEAR [radius]`
Find objects within a specified radius (default 5 meters).

```
arxos:/electrical/outlets> near 3
Objects within 3m:
  switch_2A - 1.2m away
  outlet_2C - 2.4m away
  thermostat_1 - 2.8m away
```

### Query Commands

#### `SELECT`
Execute SQL-like queries on building objects.

```sql
-- Find all objects needing repair
SELECT * FROM objects WHERE needs_repair = true

-- Find outlets on specific circuit
SELECT * FROM objects WHERE type = 'outlet' AND circuit = 2

-- Find high-power consumers
SELECT * FROM objects WHERE power_draw > 1000
```

### System Commands

#### `HELP`
Display available commands.

```
arxos:/> help
ArxOS Terminal Commands
═══════════════════════

Navigation:
  CD <path>           - Change directory
  LS [path]           - List directory contents
  PWD                 - Print working directory
  LOOK                - Describe current location

Inspection:
  INSPECT <object>    - Show detailed object info
  TRACE <obj> <dir>   - Trace connections
  NEAR [radius]       - Find nearby objects

Queries:
  SELECT * FROM objects WHERE <condition>

Other:
  HELP                - Show this help
  EXIT                - Exit terminal
```

#### `EXIT` / `QUIT`
Exit the terminal.

```
arxos:/> exit
Goodbye!
```

## Building Organization

Buildings are organized as hierarchical filesystem-like paths:

```
/
├── electrical/
│   ├── panels/
│   │   ├── panel_1/
│   │   └── panel_2/
│   ├── circuits/
│   │   ├── 1/
│   │   ├── 2/
│   │   └── 3/
│   └── outlets/
├── plumbing/
│   ├── supply/
│   │   ├── hot/
│   │   └── cold/
│   └── drainage/
├── hvac/
│   ├── equipment/
│   └── zones/
└── spaces/
    ├── floor_1/
    ├── floor_2/
    └── floor_3/
```

## Query Syntax

### Basic Queries

```sql
-- Select all objects
SELECT * FROM objects

-- Filter by type
SELECT * FROM objects WHERE type = 'outlet'

-- Filter by status
SELECT * FROM objects WHERE status = 'failed'

-- Multiple conditions
SELECT * FROM objects WHERE type = 'outlet' AND needs_repair = true
```

### Path-Based Queries

```sql
-- Objects in specific path
SELECT * FROM objects WHERE path LIKE '/electrical/circuits/2/%'

-- Objects on floor 2
SELECT * FROM objects WHERE path LIKE '/spaces/floor_2/%'
```

### Maintenance Queries

```sql
-- Objects needing repair
SELECT * FROM objects WHERE needs_repair = true

-- Failed equipment
SELECT * FROM objects WHERE status = 'failed'

-- Low health objects
SELECT * FROM objects WHERE health < 50
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate command history |
| `Ctrl+C` | Cancel current command |
| `Ctrl+D` | Exit terminal |

## Configuration

ArxOS configuration is stored in `config.toml`:

```toml
[database]
url = "postgresql://localhost/arxos"

[terminal]
default_building = "building_42"
history_size = 1000
prompt_format = "arxos:{}> "
```

## Tips

### 1. Efficient Navigation
Use absolute paths to jump directly to locations:
```
arxos:/> cd /electrical/circuits/2/outlet_2B
```

### 2. Wildcard Queries
Use SQL LIKE patterns for flexible searches:
```sql
SELECT * FROM objects WHERE path LIKE '%/outlets/%'
```

### 3. System Health Checks
Quick queries for maintenance:
```sql
-- All issues
SELECT * FROM objects WHERE needs_repair = true OR status = 'failed'

-- By severity
SELECT * FROM objects WHERE health < 25
```

### 4. Tracing Problems
Use TRACE to follow issues to their source:
```
arxos:/> trace outlet_2B upstream
```

## Integration

The terminal can be integrated with external systems:

```bash
# Execute single command
arxos -c "SELECT * FROM objects WHERE needs_repair = true"

# Pipe commands
echo "SELECT * FROM objects" | arxos

# Output to file
arxos -c "ls /electrical" > electrical_inventory.txt
```