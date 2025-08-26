# ArxObject File Tree Structure

This document details the ArxObject file tree structure, explaining how buildings are organized as navigable filesystems across various scale levels.

## Table of Contents

1. [Overview](#overview)
2. [Building Filesystem Structure](#building-filesystem-structure)
3. [Scale Levels](#scale-levels)
4. [Navigation Examples](#navigation-examples)
5. [Path Conventions](#path-conventions)
6. [Metadata Directory](#metadata-directory)

## Overview

The ArxObject file tree transforms buildings into navigable filesystems where every building element, system, and component can be accessed through familiar path-based navigation. This structure enables the "Building as Filesystem" paradigm that makes building management as intuitive as file system navigation.

### Key Principles

- **Hierarchical Organization**: Buildings are organized in logical hierarchies from campus to component level
- **Consistent Naming**: All paths follow consistent naming conventions
- **Infinite Zoom**: Seamless navigation between different levels of detail
- **Metadata Integration**: Rich metadata accompanies every object in the tree
- **Version Control**: Complete history and change tracking for all objects

## Building Filesystem Structure

### Complete Building Structure

When you initialize a building with `arx init`, the following structure is created:

```
building:main/                           # Building root
├── .arxos/                             # Metadata directory (hidden)
│   ├── config/                         # Building configuration
│   │   ├── arxos.yml                  # Main building config
│   │   ├── environments/               # Environment-specific configs
│   │   │   ├── development.yml        # Development environment
│   │   │   ├── staging.yml            # Staging environment
│   │   │   └── production.yml         # Production environment
│   │   ├── rules/                     # Building automation rules
│   │   │   ├── building_rules.yml     # General building rules
│   │   │   ├── energy_rules.yml       # Energy optimization rules
│   │   │   └── maintenance_rules.yml  # Maintenance rules
│   │   ├── integrations/               # External system integrations
│   │   │   ├── external_systems.yml   # BMS, CMMS, EMS integration
│   │   │   └── api_config.yml         # REST API configuration
│   │   ├── monitoring/                 # Monitoring and observability
│   │   │   ├── metrics.yml            # Metrics collection
│   │   │   ├── alerts.yml             # Alerting rules
│   │   │   └── dashboards.yml         # Monitoring dashboards
│   │   ├── security/                   # Security and access control
│   │   │   ├── access_control.yml     # Role-based access control
│   │   │   └── compliance_rules.yml   # Compliance requirements
│   │   ├── testing/                    # Testing and validation
│   │   │   └── test_suites.yml        # Test configurations
│   │   ├── backup/                     # Backup and recovery
│   │   │   └── backup_strategy.yml    # Backup strategies
│   │   └── recovery/                   # Disaster recovery
│   │       └── recovery_procedures.yml # Recovery procedures
│   ├── objects/                        # ArxObject database
│   │   ├── index.db                   # Spatial and property indexes
│   │   ├── objects.db                 # ArxObject storage
│   │   └── relationships.db            # Object relationship graph
│   ├── vcs/                           # Version control data
│   │   ├── snapshots/                 # Building state snapshots
│   │   │   ├── HEAD                   # Current state
│   │   │   ├── main                   # Main branch
│   │   │   └── commits/               # Individual commits
│   │   ├── branches/                  # Version branches
│   │   │   ├── main                   # Main branch
│   │   │   └── feature/               # Feature branches
│   │   └── metadata/                  # VCS metadata
│   │       ├── config                 # VCS configuration
│   │       └── hooks/                 # Pre/post commit hooks
│   ├── cache/                         # Temporary data and cache
│   │   ├── ascii/                     # ASCII rendering cache
│   │   ├── spatial/                   # Spatial query cache
│   │   └── validation/                # Validation result cache
│   └── logs/                          # Building operation logs
│       ├── access.log                 # Command access logs
│       ├── error.log                  # Error logs
│       └── audit.log                  # Change audit logs
├── arxos.yml                          # Main building configuration
├── floor:1/                           # First floor
│   ├── arxos.yml                      # Floor configuration
│   ├── room:101/                      # Conference room
│   │   ├── arxos.yml                  # Room configuration
│   │   ├── wall:north/                # North wall
│   │   │   ├── arxos.yml              # Wall configuration
│   │   │   ├── outlet:1/              # Electrical outlet
│   │   │   │   └── arxos.yml          # Outlet configuration
│   │   │   └── switch:1/              # Light switch
│   │   │       └── arxos.yml          # Switch configuration
│   │   ├── wall:south/                # South wall
│   │   │   ├── arxos.yml              # Wall configuration
│   │   │   └── door:main/             # Main door
│   │   │       └── arxos.yml          # Door configuration
│   │   ├── wall:east/                 # East wall
│   │   │   ├── arxos.yml              # Wall configuration
│   │   │   └── window:1/              # Window
│   │   │       └── arxos.yml          # Window configuration
│   │   ├── wall:west/                 # West wall
│   │   │   ├── arxos.yml              # Wall configuration
│   │   │   └── thermostat:1/          # HVAC thermostat
│   │   │       └── arxos.yml          # Thermostat configuration
│   │   ├── ceiling/                   # Ceiling
│   │   │   ├── arxos.yml              # Ceiling configuration
│   │   │   ├── light:1/               # Ceiling light
│   │   │   │   └── arxos.yml          # Light configuration
│   │   │   └── sprinkler:1/           # Fire sprinkler
│   │   │       └── arxos.yml          # Sprinkler configuration
│   │   └── floor/                     # Floor
│   │       ├── arxos.yml              # Floor configuration
│   │       └── carpet:1/              # Floor covering
│   │           └── arxos.yml          # Carpet configuration
│   ├── room:102/                      # Office space
│   │   ├── arxos.yml                  # Room configuration
│   │   ├── wall:north/                # North wall
│   │   ├── wall:south/                # South wall
│   │   ├── wall:east/                 # East wall
│   │   ├── wall:west/                 # West wall
│   │   ├── ceiling/                   # Ceiling
│   │   └── floor/                     # Floor
│   └── room:103/                      # Storage room
│       ├── arxos.yml                  # Room configuration
│       ├── wall:north/                # North wall
│       ├── wall:south/                # South wall
│       ├── wall:east/                 # East wall
│       ├── wall:west/                 # West wall
│       ├── ceiling/                   # Ceiling
│       └── floor/                     # Floor
├── floor:2/                           # Second floor
│   ├── arxos.yml                      # Floor configuration
│   ├── room:201/                      # Executive office
│   ├── room:202/                      # Meeting room
│   └── room:203/                      # Break room
├── floor:3/                           # Third floor
│   ├── arxos.yml                      # Floor configuration
│   ├── room:301/                      # Open office
│   ├── room:302/                      # Conference room
│   └── room:303/                      # Server room
├── systems/                           # Building systems
│   ├── electrical/                    # Electrical system
│   │   ├── arxos.yml                  # Electrical system config
│   │   ├── panel:main/                # Main electrical panel
│   │   │   ├── arxos.yml              # Panel configuration
│   │   │   ├── circuit:1/             # Circuit 1
│   │   │   │   ├── arxos.yml          # Circuit configuration
│   │   │   │   ├── outlet:1/          # Outlet 1
│   │   │   │   ├── outlet:2/          # Outlet 2
│   │   │   │   └── light:1/           # Light 1
│   │   │   ├── circuit:2/             # Circuit 2
│   │   │   │   ├── outlet:3/          # Outlet 3
│   │   │   │   ├── outlet:4/          # Outlet 4
│   │   │   │   └── light:2/           # Light 2
│   │   │   └── circuit:3/             # Circuit 3
│   │   │       ├── outlet:5/          # Outlet 5
│   │   │       ├── outlet:6/          # Outlet 6
│   │   │       └── light:3/           # Light 3
│   │   ├── panel:sub_1/               # Sub-panel 1
│   │   │   ├── arxos.yml              # Sub-panel configuration
│   │   │   ├── circuit:4/             # Circuit 4
│   │   │   ├── circuit:5/             # Circuit 5
│   │   │   └── circuit:6/             # Circuit 6
│   │   ├── panel:sub_2/               # Sub-panel 2
│   │   │   ├── arxos.yml              # Sub-panel configuration
│   │   │   ├── circuit:7/             # Circuit 7
│   │   │   ├── circuit:8/             # Circuit 8
│   │   │   └── circuit:9/             # Circuit 9
│   │   ├── meter:main/                # Main electrical meter
│   │   │   └── arxos.yml              # Meter configuration
│   │   └── generator:backup/           # Backup generator
│   │       └── arxos.yml              # Generator configuration
│   ├── hvac/                          # HVAC system
│   │   ├── arxos.yml                  # HVAC system config
│   │   ├── ahu:1/                     # Air handling unit 1
│   │   │   ├── arxos.yml              # AHU configuration
│   │   │   ├── zone:1/                # Zone 1
│   │   │   │   ├── arxos.yml          # Zone configuration
│   │   │   │   ├── thermostat:1/      # Zone thermostat
│   │   │   │   ├── damper:1/          # Zone damper
│   │   │   │   └── sensor:1/          # Zone sensor
│   │   │   ├── zone:2/                # Zone 2
│   │   │   │   ├── arxos.yml          # Zone configuration
│   │   │   │   ├── thermostat:2/      # Zone thermostat
│   │   │   │   ├── damper:2/          # Zone damper
│   │   │   │   └── sensor:2/          # Zone sensor
│   │   │   ├── zone:3/                # Zone 3
│   │   │   │   ├── arxos.yml          # Zone configuration
│   │   │   │   ├── thermostat:3/      # Zone thermostat
│   │   │   │   ├── damper:3/          # Zone damper
│   │   │   │   └── sensor:3/          # Zone sensor
│   │   │   └── zone:4/                # Zone 4
│   │   │       ├── arxos.yml          # Zone configuration
│   │   │       ├── thermostat:4/      # Zone thermostat
│   │   │       ├── damper:4/          # Zone damper
│   │   │       └── sensor:4/          # Zone sensor
│   │   ├── ahu:2/                     # Air handling unit 2
│   │   │   ├── arxos.yml              # AHU configuration
│   │   │   ├── zone:5/                # Zone 5
│   │   │   ├── zone:6/                # Zone 6
│   │   │   ├── zone:7/                # Zone 7
│   │   │   └── zone:8/                # Zone 8
│   │   ├── chiller:1/                 # Chiller 1
│   │   │   └── arxos.yml              # Chiller configuration
│   │   ├── boiler:1/                  # Boiler 1
│   │   │   └── arxos.yml              # Boiler configuration
│   │   └── pump:1/                    # Pump 1
│   │       └── arxos.yml              # Pump configuration
│   ├── automation/                     # Building automation
│   │   ├── arxos.yml                  # Automation system config
│   │   ├── controller:main/            # Main controller
│   │   │   ├── arxos.yml              # Controller configuration
│   │   │   ├── protocol:bacnet/       # BACnet protocol
│   │   │   │   └── arxos.yml          # BACnet configuration
│   │   │   ├── protocol:modbus/       # Modbus protocol
│   │   │   │   └── arxos.yml          # Modbus configuration
│   │   │   └── network:ethernet/      # Ethernet network
│   │   │       └── arxos.yml          # Network configuration
│   │   ├── controller:floor_1/         # Floor 1 controller
│   │   │   └── arxos.yml              # Controller configuration
│   │   ├── controller:floor_2/         # Floor 2 controller
│   │   │   └── arxos.yml              # Controller configuration
│   │   └── controller:floor_3/         # Floor 3 controller
│   │       └── arxos.yml              # Controller configuration
│   ├── plumbing/                       # Plumbing system
│   │   ├── arxos.yml                  # Plumbing system config
│   │   ├── water:supply/              # Water supply
│   │   │   ├── arxos.yml              # Supply configuration
│   │   │   ├── meter:main/            # Water meter
│   │   │   ├── pump:1/                # Water pump
│   │   │   └── tank:storage/          # Storage tank
│   │   ├── water:return/              # Water return
│   │   │   ├── arxos.yml              # Return configuration
│   │   │   └── pump:1/                # Return pump
│   │   ├── sewer:main/                # Main sewer
│   │   │   └── arxos.yml              # Sewer configuration
│   │   └── gas:natural/                # Natural gas
│   │       ├── arxos.yml              # Gas configuration
│   │       └── meter:main/            # Gas meter
│   ├── fire_protection/                # Fire protection system
│   │   ├── arxos.yml                  # Fire protection config
│   │   ├── sprinkler:main/            # Main sprinkler system
│   │   │   ├── arxos.yml              # Sprinkler configuration
│   │   │   ├── zone:1/                # Zone 1
│   │   │   ├── zone:2/                # Zone 2
│   │   │   └── zone:3/                # Zone 3
│   │   ├── alarm:main/                # Fire alarm system
│   │   │   ├── arxos.yml              # Alarm configuration
│   │   │   ├── detector:smoke/        # Smoke detectors
│   │   │   ├── detector:heat/         # Heat detectors
│   │   │   └── pull_station:1/        # Pull station
│   │   └── extinguisher:1/            # Fire extinguisher
│   │       └── arxos.yml              # Extinguisher configuration
│   └── security/                       # Security system
│       ├── arxos.yml                  # Security system config
│       ├── access:control/             # Access control
│       │   ├── arxos.yml              # Access control config
│       │   ├── reader:main_entrance/  # Main entrance reader
│       │   ├── reader:side_entrance/  # Side entrance reader
│       │   └── reader:parking/        # Parking entrance reader
│       ├── camera:surveillance/        # Surveillance cameras
│       │   ├── arxos.yml              # Camera configuration
│       │   ├── camera:main_entrance/  # Main entrance camera
│       │   ├── camera:parking_lot/    # Parking lot camera
│       │   └── camera:server_room/    # Server room camera
│       └── alarm:burglar/             # Burglar alarm
│           ├── arxos.yml              # Alarm configuration
│           ├── sensor:motion/          # Motion sensors
│           └── sensor:door/            # Door sensors
├── schemas/                            # Configuration schemas
│   ├── arxos.schema.yml               # Building configuration schema
│   └── templates/                      # Building templates
│       ├── standard_office.yml         # Standard office template
│       ├── industrial_warehouse.yml    # Industrial warehouse template
│       └── residential_apartment.yml   # Residential apartment template
├── campus:main/                        # Campus level
│   ├── arxos.yml                      # Campus configuration
│   ├── building:main/                 # Main building (current)
│   ├── building:parking/              # Parking structure
│   │   └── arxos.yml                  # Parking configuration
│   ├── building:maintenance/          # Maintenance building
│   │   └── arxos.yml                  # Maintenance configuration
│   └── infrastructure/                 # Campus infrastructure
│       ├── arxos.yml                  # Infrastructure configuration
│       ├── road:main_drive/           # Main driveway
│       ├── road:side_street/          # Side street
│       ├── parking:surface/            # Surface parking
│       ├── parking:underground/        # Underground parking
│       ├── utility:electrical/         # Electrical utilities
│       ├── utility:water/              # Water utilities
│       ├── utility:gas/                # Gas utilities
│       └── utility:telecom/            # Telecommunications
└── micro:chip_level/                   # Micro level (for future use)
    ├── arxos.yml                      # Micro level configuration
    ├── component:processor/            # Processor component
    ├── component:memory/               # Memory component
    └── component:storage/              # Storage component
```

### Metadata Directory Structure

The `.arxos` directory contains all the metadata needed to operate the building filesystem:

#### Configuration Files

- **`arxos.yml`**: Main building configuration with type, floors, area, location
- **`environments/`**: Environment-specific configurations (development, staging, production)
- **`rules/`**: Building automation rules for energy optimization, maintenance alerts
- **`integrations/`**: External system integrations (BMS, CMMS, EMS)
- **`monitoring/`**: Metrics collection, alerting rules, and dashboards
- **`security/`**: Role-based access control and compliance rules
- **`testing/`**: Test configurations and validation rules
- **`backup/`**: Backup strategies and schedules
- **`recovery/`**: Disaster recovery procedures

#### Database Files

- **`index.db`**: Spatial and property indexes for fast queries
- **`objects.db`**: ArxObject storage with all building elements
- **`relationships.db`**: Object relationship graph for spatial and logical connections

#### Version Control

- **`snapshots/`**: Building state snapshots for rollback capability
- **`branches/`**: Version branches for parallel development
- **`metadata/`**: VCS configuration and hooks

#### Cache and Logs

- **`cache/`**: Temporary data for performance optimization
- **`logs/`**: Complete audit trail of all building operations

## Scale Levels

The ArxObject file tree supports infinite fractal zoom across multiple scale levels:

### 1. Campus Level
- **Path**: `campus:main/`
- **Scale**: 1:10,000 (1cm = 100m)
- **Focus**: Overall campus layout, building relationships, infrastructure
- **Commands**: `arx zoom to campus`, `arx ls campus:main`

### 2. Building Level
- **Path**: `building:main/`
- **Scale**: 1:1,000 (1cm = 10m)
- **Focus**: Building footprint, floor layout, system overview
- **Commands**: `arx zoom to building`, `arx ls building:main`

### 3. Floor Level
- **Path**: `building:main/floor:1/`
- **Scale**: 1:100 (1cm = 1m)
- **Focus**: Floor plan, room layout, floor systems
- **Commands**: `arx zoom to floor`, `arx ls floor:1`

### 4. Room Level
- **Path**: `building:main/floor:1/room:101/`
- **Scale**: 1:10 (1cm = 10cm)
- **Focus**: Room details, wall components, room systems
- **Commands**: `arx zoom to room`, `arx ls room:101`

### 5. Component Level
- **Path**: `building:main/floor:1/room:101/wall:north/`
- **Scale**: 1:1 (1cm = 1cm)
- **Focus**: Individual components, detailed properties, maintenance info
- **Commands**: `arx zoom to component`, `arx inspect wall:north`

### 6. Micro Level (Future)
- **Path**: `micro:chip_level/`
- **Scale**: 1:0.001 (1cm = 0.01mm)
- **Focus**: Microchip internals, sensor details, atomic components
- **Commands**: `arx zoom to micro`, `arx ls micro:chip_level`

## Navigation Examples

### Basic Navigation

```bash
# Navigate to building root
arx cd building:main

# Navigate to specific floor
arx cd floor:1

# Navigate to specific room
arx cd room:101

# Navigate to specific wall
arx cd wall:north

# Navigate to specific component
arx cd outlet:1

# Navigate to building systems
arx cd systems:electrical

# Navigate to specific system component
arx cd systems:electrical/panel:main

# Navigate to campus level
arx cd campus:main

# Navigate to parent directory
arx cd ..

# Navigate to root
arx cd /
```

### Infinite Zoom Navigation

```bash
# Zoom in to next level of detail
arx zoom in

# Zoom out to previous level
arx zoom out

# Zoom to specific level
arx zoom to campus
arx zoom to building
arx zoom to floor
arx zoom to room
arx zoom to component

# Check current zoom level
arx zoom status
```

### Listing and Inspection

```bash
# List current directory contents
arx ls

# List with tree structure
arx ls --tree

# List with ASCII rendering
arx ls --ascii

# List specific path
arx ls building:main/floor:1

# List with details
arx ls -l

# Filter by type
arx ls --type wall

# Filter by system
arx ls --system electrical

# Show tree structure
arx tree

# Show tree with limited depth
arx tree --depth 2

# Show tree with specific types
arx tree --types floor,room
```

## Path Conventions

### Naming Conventions

- **Buildings**: `building:{name}` (e.g., `building:main`, `building:hq`)
- **Floors**: `floor:{number}` (e.g., `floor:1`, `floor:2`)
- **Rooms**: `room:{number}` (e.g., `room:101`, `room:202`)
- **Walls**: `wall:{direction}` (e.g., `wall:north`, `wall:south`)
- **Systems**: `systems:{type}` (e.g., `systems:electrical`, `systems:hvac`)
- **Components**: `{type}:{identifier}` (e.g., `outlet:1`, `switch:main`)

### Path Examples

```bash
# Absolute paths
/building:main/floor:1/room:101/wall:north/outlet:1
/campus:main/building:main/systems:electrical/panel:main

# Relative paths
floor:1/room:101
../room:102
../../systems:electrical

# Special paths
/                    # Building root
~                    # Home building
.                    # Current location
..                   # Parent location
```

### Path Resolution

The path resolution engine handles:

- **Absolute paths**: Starting with `/` from building root
- **Relative paths**: Relative to current working directory
- **Special paths**: `/`, `~`, `.`, `..`
- **Wildcards**: `*` for pattern matching
- **Variables**: `{variable}` for dynamic path resolution

### Working Directory

```bash
# Show current working directory
arx pwd

# Show with details
arx pwd --verbose

# Change working directory
arx cd building:main/floor:1/room:101

# Working directory is maintained across commands
arx ls                    # Lists room:101 contents
arx inspect wall:north    # Inspects north wall in room:101
arx find --type outlet    # Finds outlets in room:101
```

This comprehensive file tree structure provides the foundation for navigating buildings as filesystems, enabling intuitive building management through familiar command-line operations. The infinite zoom capability and rich metadata integration make every level of detail accessible and manageable.
