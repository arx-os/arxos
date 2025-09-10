# ArxOS Architecture

## Vision
Buildings as queryable, version-controlled databases - navigate through building systems like a file system, query equipment with SQL, and track as-built changes through Git-like workflows.

## Core Concept
Every outlet, light, valve, and piece of equipment becomes part of a hierarchical data structure that can be:
- **Navigated** like a file system (`cd /electrical/circuits/15`)
- **Queried** like a database (`SELECT * FROM objects WHERE needs_repair = true`)
- **Traced** through connections (`trace outlet_2B UPSTREAM`)
- **Version-controlled** like code (branches, commits, pull requests)
- **Field-verified** through AR mobile interfaces

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Terminal UI   │    │   Mobile AR     │    │  Web Interface  │
│      (Go)       │    │   (iOS/Android) │    │   (Basic HTML)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     Data Storage Layer    │
                    │   (JSON + SQLite Index)   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    BIM/CAD Sync Daemon    │
                    │   (Bidirectional Sync)    │
                    └───────────────────────────┘
```

## Data Model

### File Structure
```
buildings/
├── building_001/
│   ├── metadata.json          # Building info, settings
│   ├── objects/
│   │   ├── electrical.json    # Equipment by system
│   │   ├── mechanical.json
│   │   └── plumbing.json
│   ├── spaces/
│   │   └── floor_2.json       # Spatial organization
│   ├── index.db               # SQLite for fast queries
│   └── .git/                  # Version control
└── building_002/
    └── ...
```

### Object Structure (JSON)
```json
{
  "id": "uuid",
  "path": "/electrical/outlets/outlet_2B",
  "type": "outlet",
  "space": "/spaces/floor_2/room_2B",
  "location": {
    "x": 15.2,
    "y": 8.4,
    "mounting": "wall"
  },
  "connections": [
    {"to": "circuit_15", "type": "power"}
  ],
  "state": {
    "status": "normal",
    "health": "good",
    "needs_repair": false
  },
  "properties": {
    "voltage": 120,
    "amperage": 20
  }
}
```

## Core Components

### 1. Terminal Interface (Go)
**Primary command-line interface for building operations**

#### Starting the Terminal
```bash
# Basic startup (connects to last building)
arx

# Connect to specific building
arx connect building_42

# List available buildings
arx list

# Create new building
arx init my_building
```

#### Navigation Commands

**`cd <path>`** - Change directory in the building hierarchy
```
arxos:/> cd electrical/circuits/2
arxos:/electrical/circuits/2> cd /plumbing
arxos:/plumbing> cd ..
```

**`ls [path]`** - List directory contents
```
arxos:/electrical> ls
  panels/
  circuits/
  outlets/
  breaker_main [OK]
  meter_1 [OK]
```

**`pwd`** - Print working directory
```
arxos:/electrical/circuits/2> pwd
/electrical/circuits/2
```

**`look`** - Describe current location
```
arxos:/electrical/circuits/2> look
Current location: /electrical/circuits/2
You see:
  - outlet_2A (outlet)
  - outlet_2B (outlet) [NEEDS REPAIR]
  - outlet_2C (outlet)
  - switch_2A (switch)
```

#### Inspection Commands

**`inspect <object>`** - Show detailed object information
```
arxos:/electrical> inspect outlet_2B
╔════════════════════════════════════════════╗
║ Object: outlet_2B                          ║
╚════════════════════════════════════════════╝

Path:     /electrical/circuits/2/outlet_2B
Type:     outlet
Status:   degraded
Health:   fair
Circuit:  15
Voltage:  120V
⚠ NEEDS REPAIR: Ground fault detected

Last modified: 2024-01-15 by john.smith
Branch: main
```

**`trace <object> <upstream|downstream>`** - Trace connections
```
arxos:/electrical> trace outlet_2B upstream
Tracing upstream from outlet_2B:
  → circuit_2 (20A breaker)
    → panel_1 (100A subpanel)
      → main_breaker (200A)
        → meter_1
          → utility_connection
```

**`near [radius]`** - Find nearby objects
```
arxos:/electrical/outlets> near 3
Objects within 3m:
  switch_2A - 1.2m away
  outlet_2C - 2.4m away
  thermostat_1 - 2.8m away
```

#### Query Commands

**`SELECT`** - SQL-like queries on building data
```sql
-- Find all objects needing repair
SELECT * FROM objects WHERE needs_repair = true

-- Find outlets on specific circuit
SELECT * FROM objects WHERE type = 'outlet' AND circuit = 2

-- Complex queries
SELECT path, type, power_draw FROM objects 
WHERE power_draw > 1000 AND space LIKE '%floor_2%'

-- Aggregations
SELECT type, COUNT(*) FROM objects GROUP BY type
```

#### Version Control Commands

**`branch [name]`** - Create or switch branches
```
arxos:/> branch
* main
  field/2024-01-15/outlet-repair
  maintenance/hvac-upgrade

arxos:/> branch field/panel-inspection
Switched to new branch 'field/panel-inspection'
```

**`status`** - Show uncommitted changes
```
arxos:/> status
On branch: field/panel-inspection
Modified objects:
  M /electrical/panels/panel_2b
  M /electrical/circuits/15
```

**`diff [branch]`** - Show differences
```
arxos:/> diff main
--- main
+++ field/panel-inspection
  /electrical/circuits/15:
    - amperage: 15
    + amperage: 20
```

**`commit -m <message>`** - Commit changes
```
arxos:/> commit -m "Updated circuit 15 amperage per field inspection"
[field/panel-inspection 3a4f5b2] Updated circuit 15 amperage per field inspection
 2 objects changed
```

**`merge <branch>`** - Merge branches
```
arxos:/> checkout main
arxos:/> merge field/panel-inspection
Merge complete. 2 objects updated.
```

**`push` / `pull`** - Sync with remote
```
arxos:/> push
Pushed branch 'field/panel-inspection'
Created pull request #47
```

#### Update Commands

**`update <object> --<property> <value>`** - Modify objects
```
arxos:/> update outlet_2B --status normal --health good
Updated outlet_2B

arxos:/> update circuit_15 --amperage 20
Updated circuit_15
```

**`create <path> --type <type>`** - Create new objects
```
arxos:/> create /electrical/outlets/outlet_2D --type outlet
Created outlet_2D at /electrical/outlets/outlet_2D
```

**`delete <object>`** - Remove objects
```
arxos:/> delete outlet_2D
Are you sure you want to delete outlet_2D? [y/N]: y
Deleted outlet_2D
```

#### Sync Commands

**`sync import <file>`** - Import from BIM/CAD
```
arxos:/> sync import building.ifc
Importing IFC file... 
Created 1,247 objects
Import complete.

arxos:/> sync import floor2.pdf
Processing PDF floor plan...
Extracted 47 objects
Import complete.
```

**`sync export --format <format>`** - Export to BIM/CAD
```
arxos:/> sync export --format ifc
Exporting to building_export.ifc...
Export complete.
```

**`sync status`** - Show sync daemon status
```
arxos:/> sync status
Sync Daemon: Active
Watching: /var/arxos/bim/
Last sync: 2024-01-15 14:30:22
Pending changes: 3
```

#### Visualization Commands

**`map [floor]`** - ASCII floor plan
```
arxos:/> map floor_2
Floor 2 - Electrical Layout
═════════════════════════════════════
┌─────────────┬─────────────┬────────┐
│  Room 2A    │  Room 2B    │ Mech   │
│  ● ● ●      │  ○ ● ●      │  ⚡    │
│  Circuit 14 │  Circuit 15 │  Panel │
└─────────────┴─────────────┴────────┘
  ● Active    ○ Needs Repair   ⚡ Equipment
```

**`tree [depth]`** - Hierarchical view
```
arxos:/electrical> tree 2
/electrical
├── panels/
│   ├── main_panel
│   └── panel_2b
├── circuits/
│   ├── 1/
│   ├── 2/
│   └── 15/
└── outlets/
    ├── outlet_2A
    └── outlet_2B [NEEDS REPAIR]
```

#### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate command history |
| `Tab` | Auto-complete paths |
| `Ctrl+C` | Cancel current command |
| `Ctrl+D` | Exit terminal |
| `Ctrl+L` | Clear screen |
| `Ctrl+R` | Reverse search history |

### 2. Data Storage Layer

#### JSON Files
- **Usage**: Equipment metadata, configurations
- **Benefits**: Human-readable, Git-friendly diffs
- **Structure**: Organized by system (electrical, mechanical, etc.)

#### SQLite Index
- **Usage**: Fast queries and spatial searches
- **Tables**: 
  - `objects`: Denormalized view for queries
  - `connections`: Relationship graph
  - `spatial_index`: 2D coordinate indexing
  - `history`: Change tracking (supplements Git)
- **Updated**: On file changes via fsnotify

##### Index Schema
```sql
-- Objects table (denormalized for fast queries)
CREATE TABLE objects (
    id TEXT PRIMARY KEY,
    building_id TEXT NOT NULL,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    space TEXT,
    location_x REAL,
    location_y REAL,
    mounting TEXT,
    status TEXT DEFAULT 'normal',
    health INTEGER DEFAULT 100,
    needs_repair BOOLEAN DEFAULT 0,
    properties JSON,
    connections JSON,
    last_modified TIMESTAMP,
    last_modified_by TEXT,
    branch TEXT DEFAULT 'main'
);

-- Indexes for performance
CREATE INDEX idx_objects_path ON objects(path);
CREATE INDEX idx_objects_type ON objects(type);
CREATE INDEX idx_objects_status ON objects(status);
CREATE INDEX idx_objects_needs_repair ON objects(needs_repair);
CREATE INDEX idx_objects_space ON objects(space);
CREATE INDEX idx_objects_branch ON objects(branch);

-- Spatial index for proximity queries
CREATE INDEX idx_objects_spatial ON objects(location_x, location_y);

-- Full-text search
CREATE VIRTUAL TABLE objects_fts USING fts5(
    path, name, type, properties,
    content=objects
);

-- Connection graph
CREATE TABLE connections (
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    connection_type TEXT NOT NULL,
    metadata JSON,
    PRIMARY KEY (from_id, to_id, connection_type)
);

-- History tracking (supplements Git)
CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL,
    operation TEXT NOT NULL, -- 'create', 'update', 'delete'
    changed_fields JSON,
    old_values JSON,
    new_values JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user TEXT,
    branch TEXT,
    commit_hash TEXT
);
```

### 3. BIM/CAD Sync Daemon (Go)

#### Supported Formats (MVP)
- **IFC** (Industry Foundation Classes) - Open standard
- **PDF** - Floor plans and schematics
- **DWG/DXF** - Via libraries (future)

#### Sync Operations
```go
// Import from BIM
arx sync import building.ifc

// Export changes back to BIM
arx sync export --format=ifc --branch=field-updates

// Watch for changes
arx sync watch /path/to/bim/files
```

### 4. Mobile AR Interface

#### Core Functions
- **Identify**: Point camera at equipment to query
- **Update**: Mark field changes in AR view
- **Verify**: Confirm as-built matches design
- **Annotate**: Add notes and photos to objects

#### Data Flow
1. Download building data subset for offline use
2. Capture field changes locally
3. Create branch with changes
4. Sync when connected
5. Submit for review via pull request

### 5. Version Control System

#### Git-like Workflow
```bash
# Field technician workflow
arx branch field/2024-01-15/panel-2b
arx cd /electrical/panels/2b
arx inspect breaker_15
arx update breaker_15 --amperage 20  # Was incorrectly labeled as 15A
arx commit -m "Updated breaker 15 amperage per field inspection"
arx push

# Facility manager review
arx checkout field/2024-01-15/panel-2b
arx diff main
arx merge main  # After review
arx sync export  # Push to BIM systems
```

#### Branch Naming Conventions
- `field/<date>/<description>` - Field updates
- `maintenance/<system>/<description>` - Maintenance work
- `design/<change-order>` - Design changes
- `audit/<date>` - Compliance audits

#### Audit Trail Architecture
The system maintains a complete audit trail through multiple layers:

1. **Git History**: Primary audit mechanism
   - Every change is a Git commit
   - Full diff history available
   - Blame tracking for each property
   - Branch protection for approved states

2. **SQLite History Table**: Fast queries on changes
   - Supplements Git for performance
   - Enables queries like "all changes by user X"
   - Tracks which branch changes occurred on
   - Links to Git commit hashes

3. **Change Metadata**: Stored in commits
   ```json
   {
     "user": "john.smith",
     "timestamp": "2024-01-15T14:30:00Z",
     "source": "mobile_ar",
     "location": {"lat": 37.7749, "lon": -122.4194},
     "device": "iPhone 14 Pro",
     "notes": "Field inspection during routine maintenance"
   }
   ```

4. **Bulk Operations Tracking**:
   ```sql
   -- Track batch changes
   CREATE TABLE bulk_operations (
       id TEXT PRIMARY KEY,
       operation_type TEXT, -- 'update', 'create', 'delete'
       filter JSON,         -- Criteria used
       changes JSON,        -- Changes applied
       affected_count INTEGER,
       affected_objects JSON, -- List of object IDs
       user TEXT,
       timestamp TIMESTAMP,
       branch TEXT,
       commit_hash TEXT
   );
   ```

## Key Design Decisions

### Why File-Based Storage?
- **Portability**: No database server required
- **Version Control**: Native Git integration
- **Offline-First**: Full functionality without network
- **Debugging**: Human-readable files
- **Backup**: Simple file copies

### Why SQLite for Indexing?
- **Performance**: Fast queries on large datasets
- **Spatial Queries**: Efficient nearest-neighbor searches
- **Aggregations**: Complex analytics without loading all data
- **Embedded**: No separate database process

### Why Separate BIM Sync?
- **Respect Existing Workflows**: Don't replace CAD tools
- **Incremental Updates**: Most changes are metadata, not geometry
- **Bidirectional**: Field changes flow back to design tools
- **Format Agnostic**: Support multiple CAD formats

## Implementation Phases

### Phase 1: Core Terminal (Months 1-3)
- [ ] Basic file structure and JSON schemas
- [ ] Terminal navigation commands
- [ ] SQLite indexing
- [ ] Simple ASCII rendering
- [ ] Local Git integration

### Phase 2: BIM Integration (Months 4-6)
- [ ] IFC parser and exporter
- [ ] PDF floor plan import
- [ ] Sync daemon with file watching
- [ ] Conflict resolution tools
- [ ] Change review interface

### Phase 3: Mobile AR (Months 7-9)
- [ ] iOS/Android apps with ARKit/ARCore
- [ ] Offline data sync
- [ ] Field markup tools
- [ ] Photo/video attachments
- [ ] Branch creation from mobile

### Phase 4: Advanced Features (Months 10-12)
- [ ] Real-time collaboration
- [ ] Advanced ASCII visualizations
- [ ] Plugin system for custom commands
- [ ] Web dashboard for management
- [ ] Analytics and reporting

## Performance Requirements

### Terminal Interface
- Sub-second response for navigation
- <3 second query time for 100k objects
- Support buildings up to 1M sq ft
- Handle 50+ concurrent users

### Sync Operations
- Process 10MB IFC file in <30 seconds
- Detect file changes within 1 second
- Merge conflicts resolution in <5 seconds
- Batch process 1000 changes/minute

### Mobile AR
- 30+ FPS camera overlay
- <2 second object identification
- Offline cache of 10k objects
- Sync 1000 changes in <30 seconds

## Security Considerations

### Access Control
- Building-level permissions
- Role-based access (viewer, editor, admin)
- Branch protection for main
- Audit log of all changes

### Data Protection
- Encrypted at rest (optional)
- No cloud dependencies
- Local-first architecture
- Backup via standard file tools

## Terminal Usage Examples

### Basic Navigation and Inspection
```bash
$ arx connect building_42
Connected to Building 42 (1,247 objects)

arxos:/> cd /spaces/floor_2/room_2B
arxos:/spaces/floor_2/room_2B> ls
  outlet_2B_north
  outlet_2B_south [NEEDS REPAIR]
  light_2B_ceiling
  thermostat_2B

arxos:/spaces/floor_2/room_2B> inspect outlet_2B_south
╔════════════════════════════════════════════╗
║ Object: outlet_2B_south                   ║
╚════════════════════════════════════════════╝

Path:     /electrical/outlets/outlet_2B_south
Type:     outlet
Status:   degraded
Health:   fair
Circuit:  15
Voltage:  120V
⚠ NEEDS REPAIR: Intermittent ground fault

arxos:/spaces/floor_2/room_2B> trace outlet_2B_south upstream
Tracing power upstream from outlet_2B_south:
  → circuit_15 (20A breaker)
    → panel_2B (subpanel)
      → main_panel (200A service)
```

### Field Update Workflow
```bash
# Create field branch for inspection work
arxos:/> branch field/2024-01-16/morning-inspection
Switched to new branch 'field/2024-01-16/morning-inspection'

# Navigate and update objects
arxos:/> cd /electrical/outlets
arxos:/electrical/outlets> update outlet_2B --status normal --health good
Updated outlet_2B

arxos:/electrical/outlets> update outlet_3A --needs_repair true --notes "Loose ground wire"
Updated outlet_3A

# Review changes
arxos:/> status
On branch: field/2024-01-16/morning-inspection
Modified objects:
  M /electrical/outlets/outlet_2B
  M /electrical/outlets/outlet_3A

arxos:/> diff main
--- main
+++ field/2024-01-16/morning-inspection
  /electrical/outlets/outlet_2B:
    - status: degraded
    + status: normal
    - health: fair
    + health: good
  /electrical/outlets/outlet_3A:
    - needs_repair: false
    + needs_repair: true
    + notes: "Loose ground wire"

# Commit and push
arxos:/> commit -m "Morning inspection - fixed outlet 2B, flagged 3A for repair"
[field/2024-01-16/morning-inspection 3a4f5b2] Morning inspection - fixed outlet 2B, flagged 3A for repair
 2 objects changed

arxos:/> push
Pushed branch 'field/2024-01-16/morning-inspection'
Created pull request #47: "Morning inspection - fixed outlet 2B, flagged 3A for repair"
```

### Query and Maintenance Examples
```bash
# Find all issues on floor 2
arxos:/> SELECT * FROM objects WHERE space LIKE '%floor_2%' AND needs_repair = true
Found 3 objects:
  /electrical/outlets/outlet_2B_south - outlet (degraded)
  /mechanical/hvac/vav_2_3 - vav_box (failed)
  /plumbing/fixtures/faucet_2B_1 - faucet (degraded)

# Check power consumption
arxos:/> SELECT path, type, power_draw FROM objects WHERE power_draw > 1000 ORDER BY power_draw DESC
  /mechanical/hvac/ahu_1 - air_handler - 5500W
  /electrical/panels/panel_2b - panel - 3200W
  /mechanical/hvac/chiller_1 - chiller - 2800W

# System health summary
arxos:/> SELECT type, COUNT(*) as total, 
         SUM(CASE WHEN needs_repair THEN 1 ELSE 0 END) as needs_repair
         FROM objects GROUP BY type
  outlet     - 127 total, 3 needs_repair
  switch     - 89 total, 1 needs_repair
  panel      - 12 total, 0 needs_repair
  vav_box    - 24 total, 2 needs_repair
```

### BIM/CAD Sync Examples
```bash
# Import from IFC file
arxos:/> sync import /shared/bim/building_42_rev3.ifc
Importing IFC file...
Parsing building elements...
Created: 1,247 objects
Updated: 89 objects
Import complete.

# Review import on branch
arxos:/> branch design/ifc-rev3-import
arxos:/> status
1,336 objects modified

# Export current state to IFC
arxos:/> sync export --format ifc --branch main
Exporting to building_42_asbuilt_2024-01-16.ifc...
Processed 1,247 objects
Export complete.

# Set up watch for automatic sync
arxos:/> sync watch /shared/bim/ --auto-import
Watching directory: /shared/bim/
Auto-import enabled for: *.ifc, *.pdf
Sync daemon started.
```

### Emergency Response Example
```bash
# Quick failure check
arxos:/> SELECT * FROM objects WHERE status = 'failed'
Found 1 object:
  /electrical/panels/panel_2b - panel (failed)

# Trace affected systems
arxos:/> trace panel_2b downstream
Tracing downstream from panel_2b:
  → circuit_14 (20A)
    → outlet_2A_1 [NO POWER]
    → outlet_2A_2 [NO POWER]
    → outlet_2A_3 [NO POWER]
  → circuit_15 (20A)
    → outlet_2B_1 [NO POWER]
    → outlet_2B_2 [NO POWER]
  → circuit_16 (20A)
    → lights_hallway_2 [NO POWER]

# Document emergency
arxos:/> branch emergency/panel-2b-failure
arxos:/> update panel_2b --status failed --notes "Main breaker tripped 14:30, investigating"
arxos:/> commit -m "EMERGENCY: Panel 2B failure affecting floor 2 east wing"
arxos:/> push --urgent
```

## Technology Stack

### Backend (Go)
- **CLI Framework**: cobra/viper
- **Terminal UI**: tview or bubbletea
- **Database**: SQLite via modernc.org/sqlite
- **File Watching**: fsnotify
- **Git**: go-git
- **IFC Parsing**: Custom parser or bindings

### Mobile
- **iOS**: Swift + ARKit
- **Android**: Kotlin + ARCore
- **Shared**: REST API for sync

### File Formats
- **Configuration**: YAML (human-editable settings)
- **Building Data**: JSON (equipment metadata, properties)
- **Spatial Index**: SQLite (fast queries, aggregations)
- **Version Control**: Git (native branch/merge support)

### Configuration Structure
```yaml
# ~/.arxos/config.yaml
default_building: building_42
user: john.smith
editor: vim

display:
  colors: true
  ascii_art: true
  page_size: 25

sync:
  auto_pull: true
  auto_push: false
  watch_dirs:
    - /var/arxos/bim/
  formats:
    - ifc
    - pdf

branch:
  naming:
    field: "field/{date}/{description}"
    maintenance: "maintenance/{system}/{task}"
    design: "design/{change-order}"
    audit: "audit/{date}"
  protect:
    - main
    - production
```

## Success Metrics

### Adoption
- Time to update as-built: <5 minutes (vs hours)
- Training time for new users: <30 minutes
- Field technician adoption rate: >80%

### Data Quality
- As-built accuracy: >95%
- Change capture rate: >90%
- Conflict rate: <5%

### Performance
- Query response time: <1 second
- Sync time: <30 seconds
- Mobile app launch: <3 seconds

## Integration and Automation

### Command Line Usage
```bash
# Execute single command
arx exec "SELECT * FROM objects WHERE needs_repair = true"

# Pipe commands
echo "ls /electrical" | arx

# Output to file
arx exec "map floor_2" > floor2_layout.txt

# Watch for changes
watch -n 5 'arx exec "SELECT COUNT(*) FROM objects WHERE needs_repair = true"'
```

### Scripting
```bash
#!/bin/bash
# Daily maintenance report

arx exec "SELECT * FROM objects WHERE needs_repair = true" > needs_repair.txt
arx exec "SELECT * FROM objects WHERE updated_at > 'yesterday'" > recent_changes.txt
arx exec "tree 2" > building_structure.txt

mail -s "Daily ArxOS Report" team@company.com < needs_repair.txt
```

### Batch Operations
```bash
# Create update script
cat > updates.arx << EOF
update outlet_2A --status normal
update outlet_2B --status normal
update circuit_15 --amperage 20
commit -m "Batch outlet repairs"
EOF

# Execute script
arx < updates.arx
```

## Tips and Best Practices

### Efficient Navigation
- Use absolute paths to jump directly: `cd /electrical/circuits/2`
- Use `cd -` to return to previous directory
- Tab completion for faster path entry

### Query Optimization
- Use specific fields instead of `*` for faster queries
- Create indexes on commonly queried fields
- Save frequently used queries as scripts

### Branch Strategy
- **Field updates**: `field/<date>/<description>`
- **Maintenance**: `maintenance/<system>/<task>`
- **Design changes**: `design/<change-order>`
- **Audits**: `audit/<date>`
- Always work on branches, never directly on main
- Keep branches focused on single tasks

### System Health Monitoring
```sql
-- Save as health_check.sql
SELECT 
  type,
  COUNT(*) as total,
  SUM(CASE WHEN needs_repair THEN 1 ELSE 0 END) as repairs_needed,
  AVG(health) as avg_health
FROM objects
GROUP BY type
HAVING repairs_needed > 0 OR avg_health < 80;
```

## Troubleshooting

### Common Issues

**Cannot connect to building:**
```bash
arx list                    # Check available buildings
arx connect building_42 -v  # Verbose mode for debugging
```

**Slow queries:**
```bash
arx reindex                 # Rebuild SQLite index
arx vacuum                  # Optimize database
```

**Merge conflicts:**
```bash
arx status                  # View conflicts
arx diff main              # Compare with main
arx resolve <object>       # Resolve specific conflict
```

**Sync issues:**
```bash
arx sync status            # Check daemon status
arx sync restart           # Restart sync daemon
arx sync logs              # View sync logs
```

## Future Considerations

### Potential Enhancements
- 3D visualization in terminal (ASCII isometric)
- Voice commands for hands-free field work
- ML-based change detection from photos
- Integration with IoT/sensor data
- Blockchain for change verification

### Scaling Considerations
- Sharding large buildings across files
- Distributed sync for multi-site portfolios
- Cloud backup options (optional)
- Enterprise authentication (LDAP/SAML)