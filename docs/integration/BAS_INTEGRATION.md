# BAS/BMS Integration Guide

## Overview

ArxOS integrates with Building Automation Systems (BAS) and Building Management Systems (BMS) to provide **spatial reference and version control** for control points. ArxOS operates in **read-only mode by default**, providing visibility without interfering with existing control systems.

## Supported BAS Systems

- ✅ Johnson Controls Metasys
- ✅ Siemens Desigo / Desigo CC
- ✅ Honeywell Enterprise Buildings Integrator (EBI)
- ✅ Tridium Niagara
- ✅ Schneider Electric StruxureWare
- ✅ Generic CSV exports (any BAS with CSV export capability)

## Key Concepts

### Non-Interventionist Approach

ArxOS **does NOT**:
- ❌ Send control commands to BAS
- ❌ Modify setpoints or schedules
- ❌ Override BAS logic
- ❌ Replace BAS dashboards
- ❌ Require live BAS connection

ArxOS **DOES**:
- ✅ Import BAS point lists (CSV exports)
- ✅ Map points to spatial locations (rooms, equipment)
- ✅ Provide version control for BAS configurations
- ✅ Enable spatial queries ("What BAS points control Room 301?")
- ✅ Track changes over time (Git-like history)
- ✅ Integrate with CMMS workflows (issues/PRs reference BAS points)

### Building Repository Model

BAS points are a **data layer** within a building repository:

```
Building Repository: "Main Campus"
├── Architectural Layer (from IFC import)
├── BAS Control Layer (from Metasys export)  ← BAS points here
├── Equipment Layer (from CMMS/manual)
└── Spatial Layer (from LiDAR/manual)

All layers versioned together as one coherent state.
```

## Quick Start

### Prerequisites

What you need from your BAS system:
- CSV export of point list (all BAS systems can do this)
- Building already created in ArxOS
- Optional: Room structure defined

### Step 1: Export BAS Points

**Johnson Controls Metasys:**
1. Open Site Management Portal (SMP)
2. Navigate to Reports → Point Database
3. Select building/site
4. Export → CSV
5. Save as `metasys_export.csv`

**Siemens Desigo:**
1. Open Desigo CC Management Station
2. Go to Engineering → Point Database
3. Select facility
4. Export → CSV
5. Save as `desigo_points.csv`

**Honeywell EBI:**
1. Open EBI R500 interface
2. Navigate to Database Manager
3. Select Points → Export
4. Choose CSV format
5. Save as `honeywell_points.csv`

**Tridium Niagara:**
1. Open Niagara Workbench
2. Navigate to Station
3. Tools → Export Points
4. Select CSV format
5. Save as `niagara_points.csv`

### Step 2: Create BAS System in ArxOS

```bash
# Create BAS system reference
arx bas create-system \
  --building bldg-001 \
  --name "Main Building Metasys" \
  --type metasys \
  --vendor "Johnson Controls" \
  --version "12.0"

# Output:
# ✅ BAS system created: sys-001
# Name: Main Building Metasys
# Type: Johnson Controls Metasys
```

### Step 3: Import BAS Points

```bash
# Import point list
arx bas import metasys_export.csv \
  --building bldg-001 \
  --system metasys

# Output:
# 🔍 Analyzing BAS export file...
#    File: metasys_export.csv
#    Building: bldg-001
#    System: metasys
# 
# 📊 Parsing CSV...
#    ✅ Found columns: Point Name, Device, Type, Description, Location
#    ✅ Detected 145 BAS points
# 
# 📥 Importing points...
#    ✅ Imported 145 BAS points
#    ⚠️  145 points need spatial mapping
# 
# ✅ BAS import complete!
```

### Step 4: Map Points to Locations

**Option A: Auto-Mapping (Recommended)**
```bash
# Attempt automatic mapping based on location text
arx bas import metasys_export.csv \
  --building bldg-001 \
  --system metasys \
  --auto-map

# Output:
# 🗺️  Auto-mapping points...
#    ✅ Mapped 85 points (confidence: medium)
#    ⚠️  60 points could not be auto-mapped
```

**Option B: Manual Mapping**
```bash
# List unmapped points
arx bas unmapped --building bldg-001

# Map specific point to room
arx bas map point-123 --room room-301 --confidence 3

# Map multiple points
arx bas map AI-1-1 --room room-301
arx bas map AV-1-1 --room room-301
arx bas map BO-1-1 --room room-301
```

### Step 5: Query BAS Points

```bash
# Show all BAS points for a room
arx query /main-campus/3/room-301 --show-bas

# Output:
# /main-campus/3/room-301 (Conference Room A)
# ├── BAS Points (4):
# │   ├── AI-1-1: Zone Temperature (Device 100301)
# │   ├── AV-1-1: Cooling Setpoint (Device 100301)
# │   ├── BO-1-1: Damper Command (Device 100301)
# │   └── BI-1-1: Fan Status (Device 100301)
# └── Equipment:
#     └── VAV-301 (VAV Box)

# Show specific point details
arx bas show AI-1-1

# List all points in building
arx bas list --building bldg-001
```

## Advanced Usage

### Version Control Integration

BAS imports create version commits:

```bash
# Import with automatic commit
arx bas import metasys_export.csv \
  --building bldg-001 \
  --repo repo-001 \
  --commit

# Output:
# ✅ Imported 145 points
# 📝 Creating version commit...
#    ✅ Commit created: "Imported BAS points from metasys_export.csv"

# View version history
arx repo log

# Output:
# commit abc123 (2025-01-15 10:30)
#   Imported BAS points from metasys_export.csv
#   + 145 BAS control points added
#
# commit def456 (2025-01-10 09:00)
#   Initial IFC import
#   + 50 rooms, 200 walls, 100 doors

# See what changed
arx repo diff def456 abc123

# Output:
# Changes from def456 to abc123:
# + Added 145 BAS control points
#   - AI-1-1, AV-1-1, BO-1-1 (Device 100301, Room 301)
#   - AI-1-2, AV-1-2, BO-1-2 (Device 100302, Room 302)
#   ...
```

### Daemon Auto-Import

Set up automatic import when BAS exports new files:

```bash
# Configure daemon to watch BAS export folder
arx daemon init

# Configure watcher
# Edit ~/.arxos/config/daemon.yaml:

watchers:
  - name: "Metasys Daily Export"
    path: "C:\\Users\\Facilities\\Documents\\BAS\\Exports\\"
    pattern: "Metasys_*.csv"
    building_id: "bldg-001"
    system_type: "johnson_controls_metasys"
    auto_commit: true
    commit_message_template: "Auto-import from Metasys: {changes}"

# Start daemon
arx daemon start

# Daemon now watches folder and auto-imports new exports
```

### Change Detection

Track BAS configuration changes over time:

```bash
# Import updated point list (after BAS changes)
arx bas import metasys_export_new.csv \
  --building bldg-001 \
  --system metasys

# Output:
# Comparing with existing data...
# Found changes:
#   Added (3 points):
#     - AI-3-4: Zone Temp (Floor 3 Room 304)
#     - AV-3-4: Cool SP (Floor 3 Room 304)
#     - BO-3-4: Damper (Floor 3 Room 304)
#   
#   Modified (1 point):
#     ~ AI-1-1: Description changed
#   
#   Deleted (1 point):
#     - BI-2-5: Fan Status (removed from BAS)
#
# Import changes? [Y/n]: Y
# ✅ Imported 3 new points
# ⚠️  1 point deleted (soft-deleted, preserved in history)
```

## CSV Format Requirements

### Minimum Required Columns

Your CSV must have these columns (names can vary):
- **Point Name**: Unique identifier (AI-1-1, AV-1-1, etc.)
- **Device**: Device ID or instance number
- **Object Type**: BACnet object type (Analog Input, Binary Output, etc.)

### Optional But Recommended Columns

- **Description**: Human-readable description
- **Units**: Engineering units (degF, PSI, CFM, %, etc.)
- **Location**: Location text (Floor 3 Room 301, etc.)
- **Min/Max**: Min/max values for analog points
- **Writeable**: Whether point can be written to

### Example CSV Formats

**Metasys Standard Export:**
```csv
Point Name,Device,Object Type,Description,Units,Location
AI-1-1,100301,Analog Input,Zone Temperature,degF,Floor 3 Room 301
AV-1-1,100301,Analog Value,Cooling Setpoint,degF,Floor 3 Room 301
```

**Siemens Desigo Export:**
```csv
PointID,DeviceInstance,Type,Label,EngineeringUnit,Area
AI_3_301_TEMP,100301,AI,Zone Temperature,°F,Floor 3 Conference Room 301
```

**Generic Format:**
```csv
Name,Device ID,Type,Description
AI-1-1,100301,Analog Input,Temperature Sensor
```

ArxOS automatically detects column names (case-insensitive, handles variations).

## Integration with Other ArxOS Features

### CMMS/Work Orders

BAS points integrate with ArxOS issue/PR workflow:

```bash
# Custodian reports issue (via mobile AR)
# Points at equipment → ArxOS identifies VAV-301

# Issue created automatically:
Issue #234: "VAV not working - Room 301"
- Location: /building/3/room-301
- Equipment: VAV-301
- BAS Points:
  - AI-1-1 (temp sensor)
  - AV-1-1 (setpoint)
  - BO-1-1 (damper)

# BAS tech can now:
# 1. See exact BAS device (100301)
# 2. Look up in Metasys
# 3. Troubleshoot with full context
```

### Mobile App

Building staff can view BAS points without Metasys access:

```
Mobile App → Floor 3 → Room 301:

Conference Room 301
├── Equipment: VAV-301
├── BAS Points (4):
│   ├── AI-1-1: Zone Temp (72.3°F)
│   ├── AV-1-1: Cool SP (74.0°F)
│   ├── BO-1-1: Damper (50%)
│   └── BI-1-1: Fan (ON)
└── Last Service: 2024-12-15
```

### Spatial Queries

Query BAS points spatially:

```bash
# Find all temperature sensors on Floor 3
arx query /building/3/* --type temperature

# Find all control points in HVAC system
arx query /building/*/*/hvac/* --show-bas

# Find nearby points
arx spatial nearby --lat 37.7749 --lon -122.4194 --radius 50 --show-bas
```

## Best Practices

### 1. Import Strategy

**Initial Import:**
- Import complete point list from BAS
- Take time to map points correctly
- Create baseline version commit

**Regular Updates:**
- Set up daemon for automatic import
- Review changes weekly/monthly
- Use version control to track configuration drift

### 2. Mapping Strategy

**Auto-Mapping First:**
- Let ArxOS attempt automatic mapping
- Review low-confidence mappings
- Manually verify critical points

**Progressive Mapping:**
- Don't need to map everything immediately
- Map high-priority areas first (occupied spaces)
- Map equipment rooms later

**Confidence Levels:**
- **0**: Unmapped
- **1**: Auto-mapped, low confidence (fuzzy match)
- **2**: Auto-mapped, high confidence (exact match)
- **3**: Manually verified

### 3. Version Control

**Commit After Major Changes:**
```bash
# Before: Baseline system
arx repo commit -m "BAS baseline - 150 points"

# After equipment installation
arx bas import updated_points.csv --commit
# Commit: "Added 3 VAV units to Floor 3"

# After system upgrade
arx bas import metasys_v12_points.csv --commit
# Commit: "Metasys upgrade to v12"
```

### 4. Documentation

Use ArxOS notes and metadata:

```bash
# Add notes to BAS system
arx bas update sys-001 --notes "Upgraded to Metasys 12.0 on 2025-01-10"

# Add metadata to points
arx bas update-point AI-1-1 --metadata "calibrated=2025-01-15,technician=john"
```

## Troubleshooting

### Common Issues

**Issue: "Cannot find location column"**
- Solution: CSV missing location column is OK, map manually
- Or add location column to BAS export

**Issue: "Points not auto-mapping"**
- Cause: Location text doesn't match room names
- Solution: Review unmapped points, manual map, or improve room naming

**Issue: "Duplicate points on re-import"**
- ArxOS detects duplicates by device+point name
- Won't create duplicates, will update existing

**Issue: "Lost BAS point mappings after upgrade"**
- Mappings preserved in version history
- Check previous version: `arx checkout <previous-commit>`

### Debug Mode

```bash
# Verbose import with detailed logging
arx bas import points.csv \
  --building bldg-001 \
  --verbose

# Check import history
arx bas history --building bldg-001

# Validate CSV before import
arx bas validate points.csv
```

## Examples

### Example 1: School District

**Scenario:** County manages 15 schools with Metasys

**Setup:**
1. District facilities exports Metasys point list
2. Imports to ArxOS (one-time)
3. Maps points to rooms (progressive)
4. Building staff get mobile access

**Result:**
- Principals can see building equipment (no Metasys license needed)
- Custodians can report issues with equipment context
- Work orders include BAS device IDs
- District tracks all BAS changes over time

### Example 2: Commercial Office Building

**Scenario:** Office building with Siemens Desigo

**Setup:**
1. Building engineer exports Desigo point database
2. Imports to ArxOS with auto-mapping
3. Links points to equipment from CMMS
4. Enables daemon for weekly sync

**Result:**
- Facility manager sees BAS points in ArxOS dashboard
- Tenants submit comfort complaints with room context
- Contractors receive work orders with BAS device IDs
- Configuration changes tracked automatically

### Example 3: BAS Contractor Handoff

**Scenario:** Johnson Controls completing HVAC upgrade

**Workflow:**
```bash
# 1. Contractor creates branch
arx checkout -b jci/hvac-upgrade-floor-3

# 2. Installs 3 new VAV units

# 3. Exports new point list from Metasys
# 4. Imports to ArxOS
arx bas import new-vav-points.csv \
  --building bldg-001 \
  --commit \
  --message "Added VAVs 310-312, Floor 3 expansion"

# 5. Creates pull request
arx pr create \
  --title "HVAC Upgrade Complete - Floor 3" \
  --description "Added 3 VAV units with 15 control points" \
  --files commissioning-report.pdf,point-list.csv

# 6. Building manager reviews and merges
# 7. BAS configuration now in main branch
```

## API Reference

### REST API Endpoints

```http
# Create BAS system
POST /api/v1/bas/systems
{
  "building_id": "bldg-001",
  "name": "Main Metasys",
  "system_type": "johnson_controls_metasys"
}

# Import BAS points
POST /api/v1/bas/import
{
  "building_id": "bldg-001",
  "bas_system_id": "sys-001",
  "file_path": "/path/to/export.csv",
  "auto_map": true
}

# List BAS points by room
GET /api/v1/bas/points?room_id=room-301

# Map point to room
PUT /api/v1/bas/points/{point_id}/map
{
  "room_id": "room-301",
  "confidence": 3
}
```

## Security & Access Control

### Read-Only by Default

ArxOS operates in **read-only mode** for safety:
- Cannot send commands to BAS
- Cannot modify setpoints
- Cannot override schedules
- Can only import and reference data

### Access Levels

**Building Owner/Facilities Manager:**
- Import BAS points
- Create BAS system references
- Map points to locations
- View all points

**Building Staff:**
- View mapped points in their assigned areas
- See equipment with BAS context
- Cannot import or modify BAS data

**Contractors:**
- Import points to their branch (isolated)
- Create PRs for review
- Cannot directly modify main branch

## Migration & Data Management

### Updating Point Lists

```bash
# Export fresh point list from BAS
# Import to detect changes
arx bas import metasys_updated.csv --building bldg-001

# ArxOS automatically:
# - Detects new points (added)
# - Detects modified descriptions (updated)
# - Detects removed points (deleted)
# - Preserves spatial mappings
# - Creates version commit
```

### Handling BAS System Upgrades

```bash
# Before upgrade: Snapshot current state
arx repo commit -m "Before Metasys upgrade to v12"

# After upgrade: Import new point list
arx bas import metasys_v12_export.csv \
  --building bldg-001 \
  --commit \
  --message "Metasys upgraded to v12"

# Compare configurations
arx repo diff <before-commit> <after-commit>

# Output shows:
# - New points added in v12
# - Changed point types or descriptions
# - Removed legacy points
```

## FAQ

**Q: Do I need a live connection to the BAS?**
A: No. ArxOS works with CSV exports. Live connection is optional for future features.

**Q: Will ArxOS interfere with my BAS?**
A: No. ArxOS is read-only and doesn't communicate with the BAS system.

**Q: How often should I import BAS points?**
A: Weekly/monthly for most buildings. Use daemon for automatic sync.

**Q: Can I import from multiple BAS systems?**
A: Yes. Create a BAS system for each (Metasys, Desigo, etc.) and import separately.

**Q: What happens if I re-import the same file?**
A: ArxOS detects duplicate (by file hash) and skips or shows no changes.

**Q: Can I export BAS points from ArxOS?**
A: Yes (future feature). Export to CSV for documentation or backup.

## Roadmap

**Phase 1: Import & Reference** (Current)
- ✅ CSV import
- ✅ Spatial mapping
- ✅ Version control
- ✅ CLI and API

**Phase 2: Live Monitoring** (Future)
- Read current values from BAS
- Display live data in mobile app
- Historical trending

**Phase 3: Advanced Features** (Future)
- Anomaly detection
- Energy analytics based on BAS data
- Predictive maintenance alerts

---

**For more information:**
- [Integration Flow](INTEGRATION_FLOW.md)
- [CLI Integration](CLI_INTEGRATION.md)
- [API Documentation](../api/API_DOCUMENTATION.md)

