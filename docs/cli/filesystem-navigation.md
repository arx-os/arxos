# Building Filesystem Navigation

## Overview

Arxos treats buildings as navigable Unix-style filesystems. Every component in a building - from electrical panels to HVAC units to individual outlets - has a path and can be accessed using familiar filesystem commands.

## Filesystem Structure

```
/                                   # Building root
├── /electrical/                    # Electrical system
│   ├── /main-panel/               # Main electrical panel
│   │   ├── circuit-1/             # Individual circuit
│   │   │   ├── outlet-1           # Specific outlet
│   │   │   ├── outlet-2
│   │   │   └── switch-1           # Light switch
│   │   └── circuit-2/
│   └── /sub-panel-a/              # Sub panel
├── /hvac/                         # HVAC system
│   ├── /air-handlers/             # Air handling units
│   │   ├── ahu-1/
│   │   │   ├── supply-fan/        # Components
│   │   │   ├── return-fan/
│   │   │   └── vfd/               # Variable frequency drive
│   └── /thermostats/
├── /plumbing/                     # Plumbing system
│   ├── /water-supply/
│   └── /drainage/
├── /structural/                   # Structural elements
│   ├── /columns/
│   ├── /beams/
│   └── /walls/
├── /floors/                       # Physical floors
│   ├── /1/                        # First floor
│   │   ├── room-101/
│   │   ├── room-102/
│   │   └── corridor/
│   └── /2/                        # Second floor
└── /network/                      # Network infrastructure
    ├── /switches/
    └── /access-points/
```

## Navigation Commands

### cd - Change Directory

Navigate through the building hierarchy exactly like a filesystem:

```bash
# Navigate to electrical system
arxos cd /electrical

# Go to main panel
arxos cd main-panel

# Navigate to specific circuit
arxos cd /electrical/main-panel/circuit-7

# Use relative paths
arxos cd ../circuit-8

# Go to building root
arxos cd /
arxos cd ~  # Same as /

# Navigate to a specific room
arxos cd /floors/2/room-201
```

### pwd - Print Working Directory

Show current location in the building:

```bash
arxos pwd
# Output: /electrical/main-panel/circuit-7
```

### ls - List Directory Contents

View components at current location:

```bash
# List current directory
arxos ls

# List electrical system
arxos ls /electrical

# Long format with properties
arxos ls -l /electrical/main-panel
# Output:
# drwxr-xr-x  circuit-1    20A   breaker  [12.5A load]
# drwxr-xr-x  circuit-2    20A   breaker  [8.3A load]
# drwxr-xr-x  circuit-3    30A   breaker  [22.1A load]

# Tree view
arxos ls --tree /hvac
```

### find - Search for Components

Locate specific components anywhere in the building:

```bash
# Find all outlets
arxos find / -type outlet

# Find outlets with high load
arxos find /electrical -type outlet -load ">15A"

# Find all thermostats
arxos find / -name "*thermostat*"

# Find components needing validation
arxos find / -confidence "<0.5"
```

### tree - Display Hierarchy

Show the building structure as a tree:

```bash
# Show electrical system tree
arxos tree /electrical

# Limit depth
arxos tree -L 2 /

# Show only directories (systems/subsystems)
arxos tree -d /hvac
```

## Path Syntax

### Absolute Paths

Always start with `/` and specify complete path from building root:

```bash
/electrical/main-panel/circuit-1/outlet-3
/hvac/air-handlers/ahu-1/supply-fan
/floors/2/room-201/window-north
```

### Relative Paths

Navigate relative to current location:

```bash
circuit-1           # Child directory
../circuit-2        # Sibling directory
../../sub-panel-a   # Different branch
./outlet-1          # Explicit current directory
```

### Special Paths

```bash
/       # Building root
~       # Also building root (Unix convention)
.       # Current directory
..      # Parent directory
-       # Previous directory (when implemented)
```

## Properties and Metadata

Each path represents an ArxObject with properties:

```bash
# Inspect an object
arxos inspect /electrical/main-panel/circuit-1

# Output:
# Path: /electrical/main-panel/circuit-1
# Type: electrical_circuit
# Properties:
#   breaker_rating: 20A
#   current_load: 12.5A
#   voltage: 120V
#   phase: A
#   wire_gauge: 12AWG
#   confidence: 0.85
#   last_validated: 2024-01-15
```

## Query Syntax

Use AQL (Arxos Query Language) with paths:

```bash
# Query all outlets in a circuit
arxos query "SELECT * FROM /electrical/main-panel/circuit-1 WHERE type='outlet'"

# Find overloaded circuits
arxos query "SELECT path, load FROM /electrical WHERE load > rated * 0.8"

# Get all validated components on floor 2
arxos query "SELECT * FROM /floors/2 WHERE confidence > 0.9"
```

## System Organization

### By System Type

```
/electrical/     # All electrical components
/hvac/          # HVAC systems
/plumbing/      # Plumbing infrastructure
/structural/    # Structural elements
/network/       # IT infrastructure
/fire/          # Fire safety systems
/security/      # Security systems
```

### By Physical Location

```
/floors/1/      # First floor
/floors/2/      # Second floor
/basement/      # Basement level
/roof/          # Roof equipment
/exterior/      # Exterior components
```

### By Zone

```
/zones/north/   # North zone
/zones/hvac-1/  # HVAC zone 1
/zones/secure/  # Secure area
```

## Examples

### Navigate to an Electrical Outlet

```bash
arxos cd /electrical/main-panel/circuit-7
arxos ls
# outlet-1  outlet-2  outlet-3  switch-1

arxos cd outlet-3
arxos pwd
# /electrical/main-panel/circuit-7/outlet-3

arxos inspect .
# Shows outlet properties: voltage, load, location, etc.
```

### Explore HVAC System

```bash
arxos cd /hvac
arxos tree -L 2
# /hvac
# ├── air-handlers/
# │   ├── ahu-1/
# │   └── ahu-2/
# ├── chillers/
# │   └── chiller-1/
# └── thermostats/
#     ├── t-101
#     └── t-102
```

### Find and Navigate to Component

```bash
# Find a specific thermostat
arxos find / -name "t-201"
# /hvac/thermostats/t-201

# Navigate to it
arxos cd /hvac/thermostats/t-201

# Check its properties
arxos ls -l
```

## Integration with Other Commands

The filesystem navigation integrates with all Arxos commands:

```bash
# View ASCII representation of current location
arxos view .

# View electrical panel in ASCII
arxos view /electrical/main-panel

# Validate components in current directory
arxos validate .

# Commit changes at current location
arxos commit -m "Updated circuit configuration"
```

## Best Practices

1. **Use absolute paths** in scripts for reliability
2. **Use relative paths** in interactive sessions for speed
3. **Organize by system** for maintenance tasks
4. **Organize by floor** for physical inspection
5. **Use find** to locate components before navigating
6. **Use tree** to understand structure before changes

## Shortcuts and Aliases

Create aliases for common locations:

```bash
# In ~/.arxos/config.yml
aliases:
  mp: /electrical/main-panel
  f1: /floors/1
  f2: /floors/2
  hvac1: /hvac/air-handlers/ahu-1

# Usage
arxos cd $mp  # Go to main panel
arxos ls $f2  # List floor 2
```

## Related Documentation

- [ASCII-BIM Terminal](../ascii-bim-terminal.md) - Visual representation
- [AQL Query Language](../aql.md) - Query syntax
- [ArxObject System](../arxobjects.md) - Object model
- [CLI Commands](./commands.md) - All available commands