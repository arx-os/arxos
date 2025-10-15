# Universal Naming Convention - Complete Guide

**Last Updated:** October 15, 2025  
**Version:** 1.0  
**Status:** Implemented and Ready for Use

---

## Table of Contents

- [Quick Start (5 Minutes)](#quick-start)
- [What Is This?](#what-is-it)
- [Path Format](#path-format)
- [System Codes](#system-codes)
- [Finding Equipment](#finding-equipment)
- [System-Specific Examples](#system-examples)
- [Common Tasks](#common-tasks)
- [Technical Reference](#technical-reference)
- [Implementation Details](#implementation)
- [Historical Documents](#historical)

---

## Quick Start (5 Minutes) {#quick-start}

### The Basics

Every piece of equipment gets an address like this:

```
/B1/3/301/HVAC/VAV-301
 │   │  │   │     │
 │   │  │   │     └─ Equipment name
 │   │  │   └─────── System (HVAC, ELEC, NETWORK, etc.)
 │   │  └─────────── Room number
 │   └────────────── Floor number
 └────────────────── Building code
```

**That's it.** Now you can find any equipment instantly.

### The 5 Essential Commands

```bash
# 1. Find specific equipment
arx get /B1/3/301/HVAC/VAV-301

# 2. Find multiple items (wildcards)
arx get /B1/3/*/HVAC/*

# 3. Check status
arx status /B1/3/301/HVAC/VAV-301

# 4. Trace connections
arx trace /B1/2/205/ELEC/OUTLET-1 --upstream

# 5. List by system
arx list /B1/*/HVAC/*
```

### Real-World Example

**"AC not working in Room 301"**
```bash
# Check thermostat
arx status /B1/3/301/HVAC/STAT-01

# Check VAV box
arx status /B1/3/301/HVAC/VAV-301

# Find air handler
arx trace /B1/3/301/HVAC/VAV-301 --upstream
```

---

## What Is This? {#what-is-it}

### The Problem It Solves

**Before (Traditional Way):**
- ❌ "The thermostat in that conference room on the third floor"
- ❌ "Outlet near the door, you know, the one by the window"
- ❌ "Panel 1A... or was it 1B? In the electrical room, I think?"

**After (With Universal Paths):**
- ✅ `/B1/3/CONF-301/HVAC/STAT-01` - Everyone knows exactly what and where
- ✅ `/B1/2/205/ELEC/OUTLET-A` - Precise, unambiguous
- ✅ `/B1/1/ELEC-RM/ELEC/PANEL-1A` - Standard format across all systems

### Benefits

**1. No More Confusion**
- Everyone uses the same address
- New techs can find equipment immediately
- No more "which outlet?" conversations

**2. Fast Work Orders**
```
OLD: "AC not working in room 301"
NEW: "Check /B1/3/301/HVAC/VAV-301 - no airflow"
```
You know EXACTLY what to check before you even leave your desk.

**3. Smart Queries**
```bash
# Find ALL HVAC equipment on floor 3
arx get /B1/3/*/HVAC/*

# Find ALL electrical panels
arx get /*/*/ELEC-RM/ELEC/PANEL-*

# Check status of specific equipment
arx status /B1/3/301/HVAC/VAV-301
```

---

## Path Format {#path-format}

### Standard Format

```
/[BUILDING]/[FLOOR]/[ROOM]/[SYSTEM]/[EQUIPMENT]
```

### The Five Levels

```
    /B1    /3    /301    /HVAC    /VAV-301
     ↓      ↓      ↓       ↓         ↓
  Building Floor Room  System   Equipment
```

**Level 1: Building**
- Which building? (`B1`, `MAIN`, `NORTH-WING`)
- Like the street name

**Level 2: Floor**
- Which floor? (`1`, `2`, `3`, `B` for basement, `R` for roof)
- Like the floor of an apartment

**Level 3: Room (Optional)**
- Which room? (`301`, `LOBBY`, `MECH-A`, `MDF`)
- Like the apartment number
- Can be skipped for building-level equipment

**Level 4: System**
- What type? (`ELEC`, `HVAC`, `NETWORK`, `PLUMB`, `SAFETY`)
- Like the utility type

**Level 5: Equipment**
- Specific identifier (`VAV-301`, `PANEL-1A`, `OUTLET-12`)
- Like the specific fixture

### Format Rules

- **Segments:** Separated by forward slashes `/`
- **Case:** UPPERCASE for consistency
- **Characters:** Alphanumeric only (A-Z, 0-9, hyphens allowed)
- **No spaces:** Use hyphens instead (`CONF-301` not `CONF 301`)
- **Must start with `/`**

**Valid Examples:**
- ✅ `/B1/3/301/HVAC/VAV-301`
- ✅ `/MAIN/2/IDF-2A/NETWORK/SW-01`
- ✅ `/HS-LINCOLN/1/MDF/NETWORK/CORE-SW-1`

**Invalid Examples:**
- ❌ `B1/3/301/HVAC/VAV-301` (missing leading /)
- ❌ `/b1/3/301/hvac/vav-301` (lowercase)
- ❌ `/B1//301/HVAC/VAV-301` (empty segment)
- ❌ `/B1/3/Room 301/HVAC/VAV-301` (spaces)

---

## System Codes {#system-codes}

### Standard System Taxonomy

| Code | System | Domain | Typical Equipment |
|------|--------|--------|-------------------|
| `ELEC` | Electrical | Power Distribution | Transformers, panels, outlets, circuits |
| `HVAC` | HVAC | Climate Control | Air handlers, VAVs, chillers, boilers |
| `PLUMB` | Plumbing | Water/Waste | Fixtures, valves, heaters, pumps |
| `NETWORK` | Network | IT Infrastructure | Switches, routers, WAPs, jacks |
| `SAFETY` | Safety | Life Safety | Fire panels, detectors, sprinklers |
| `LIGHTING` | Lighting | Illumination | Fixtures, switches, controls |
| `DOORS` | Doors/Access | Access Control | Door controllers, card readers, locks |
| `AV` | Audio/Visual | Presentation | Projectors, displays, amplifiers |
| `CUSTODIAL` | Custodial | Maintenance | Closets, markers, equipment |
| `ENERGY` | Energy | Energy Management | Meters, submeters, monitoring |
| `BAS` | Building Automation | Control Systems | Control points, sensors, actuators |

### Quick Reference Card

Print and post in your workspace:

```
┌─────────────────────────────────────┐
│  SYSTEM CODES QUICK REFERENCE       │
├─────────────────────────────────────┤
│  ELEC      = Electrical             │
│  HVAC      = Heating/Cooling        │
│  NETWORK   = IT/Network             │
│  PLUMB     = Plumbing               │
│  SAFETY    = Fire/Safety            │
│  BAS       = Building Automation    │
│  AV        = Audio/Visual           │
│  LIGHTING  = Lights                 │
│  DOORS     = Access Control         │
│  CUSTODIAL = Maintenance            │
│  ENERGY    = Meters/Monitoring      │
└─────────────────────────────────────┘
```

---

## Finding Equipment {#finding-equipment}

### Method 1: Exact Path

```bash
arx get /B1/3/301/HVAC/VAV-301
```
Returns: Details about VAV-301 in Room 301

### Method 2: Wildcard Search

```bash
# All HVAC equipment on floor 3
arx get /B1/3/*/HVAC/*

# All electrical panels in any room
arx get /*/*/*/ELEC/PANEL-*

# All equipment in room 301
arx get /B1/3/301/*/*
```

**Wildcard Rules:**
- `*` matches any single segment
- Use multiple `*` for multiple segments
- Does not match across `/` separators

### Method 3: Filter by Status

```bash
# All HVAC equipment on floor 3 that needs attention
arx query /B1/3/*/HVAC/* --status maintenance

# All operational electrical panels
arx query /*/*/ELEC-RM/ELEC/PANEL-* --status operational
```

### Method 4: List by System

```bash
# See all network equipment
arx list /B1/*/NETWORK/*

# See all safety equipment on floor 2
arx list /B1/2/*/SAFETY/*
```

### Common Query Patterns

```bash
# All equipment in a room
arx get /B1/3/301/*/*

# All panels in the building
arx get /*/*/ELEC-RM/ELEC/PANEL-*

# All WAPs on floor 2
arx get /B1/2/*/NETWORK/WAP-*

# All smoke detectors
arx get /*/*/SAFETY/DETECTOR-*
```

---

## System-Specific Examples {#system-examples}

### Electrical System

**Common Equipment:**
```
/B1/1/ELEC-RM/ELEC/XFMR-T1         # Main transformer
/B1/1/ELEC-RM/ELEC/PANEL-1A        # Main electrical panel
/B1/1/ELEC-RM/ELEC/SUBPANEL-2A     # Subpanel for floor 2
/B1/2/205/ELEC/OUTLET-1            # First outlet in Room 205
/B1/2/205/ELEC/OUTLET-2            # Second outlet in Room 205
/B1/3/HALL-3A/ELEC/LIGHT-12        # Hallway light fixture
```

**Use Cases:**
```bash
# Find which panel feeds Room 205
arx trace /B1/2/205/ELEC/OUTLET-1 --upstream

# List all outlets on floor 2
arx list /B1/2/*/ELEC/OUTLET-*

# Check panel load
arx status /B1/1/ELEC-RM/ELEC/PANEL-1A
```

### HVAC System

**Common Equipment:**
```
/B1/R/HVAC/AHU-1                   # Air handler on roof
/B1/B/HVAC/CHILLER-1               # Chiller in basement
/B1/3/HVAC/VAV-301                 # VAV box for floor 3
/B1/3/301/HVAC/STAT-01             # Thermostat in Room 301
/B1/3/301/HVAC/DIFFUSER-A          # Diffuser in ceiling
/B1/3/HVAC/DAMPER-01               # Floor damper
```

**Use Cases:**
```bash
# Check all thermostats on floor 3
arx get /B1/3/*/HVAC/STAT-*

# Find which AHU serves Room 301
arx trace /B1/3/301/HVAC/VAV-301 --upstream

# List all VAV boxes
arx list /B1/*/HVAC/VAV-*

# Adjust thermostat setpoint
arx set /B1/3/301/HVAC/STAT-01 cooling_setpoint:72
```

### Network/IT System

**Common Equipment:**
```
/B1/1/MDF/NETWORK/CORE-SW-1        # Core switch in MDF
/B1/2/IDF-2A/NETWORK/ACCESS-SW-2A  # Access switch in IDF
/B1/2/IDF-2A/NETWORK/PATCH-24P-A   # 24-port patch panel
/B1/2/205/NETWORK/WAP-205          # Wireless access point
/B1/2/205/NETWORK/JACK-A           # Network jack
/B1/1/SERVER/NETWORK/UPS-1         # UPS in server room
```

**Use Cases:**
```bash
# Check all wireless APs on floor 2
arx get /B1/2/*/NETWORK/WAP-*

# Find which switch feeds Room 205
arx trace /B1/2/205/NETWORK/JACK-A --upstream

# List all network equipment
arx list /B1/*/NETWORK/*

# Check WAP status
arx status /B1/2/205/NETWORK/WAP-205
```

### Plumbing System

**Common Equipment:**
```
/B1/B/PLUMB/WATER-HEATER-1         # Water heater in basement
/B1/2/PLUMB/RISER-A                # Water riser for floor 2
/B1/2/PLUMB/PRV-2                  # Pressure reducing valve
/B1/2/203/PLUMB/SINK-01            # Sink in Room 203
/B1/2/204/PLUMB/TOILET-01          # Toilet in restroom 204
/B1/2/PLUMB/SHUTOFF-2A             # Floor shutoff valve
```

**Use Cases:**
```bash
# Find all sinks on floor 2
arx get /B1/2/*/PLUMB/SINK-*

# Trace water source for sink
arx trace /B1/2/203/PLUMB/SINK-01 --upstream

# List all plumbing on floor 2
arx list /B1/2/*/PLUMB/*
```

### Fire/Safety System

**Common Equipment:**
```
/B1/1/SAFETY/FIRE-PANEL-1          # Main fire alarm panel
/B1/2/HALL-2A/SAFETY/DETECTOR-12   # Smoke detector in hallway
/B1/2/STAIR-B/SAFETY/PULL-STN-2B   # Pull station in stairwell
/B1/3/301/SAFETY/SPRINKLER-A       # Sprinkler head in room
/B1/2/STAIR-B/SAFETY/EXTING-2B-01  # Fire extinguisher
/B1/1/LOBBY/SAFETY/AED-01          # AED in lobby
```

**Use Cases:**
```bash
# Check all smoke detectors on floor 2
arx get /B1/2/*/SAFETY/DETECTOR-*

# Find all fire extinguishers
arx get /*/*/SAFETY/EXTING-*

# Verify sprinkler coverage in room 301
arx get /B1/3/301/SAFETY/SPRINKLER-*
```

### Building Automation System (BAS)

**Common Control Points:**
```
/B1/3/301/BAS/AI-1-1               # Analog Input (temp sensor)
/B1/3/301/BAS/AV-1-1               # Analog Value (setpoint)
/B1/3/301/BAS/BO-1-1               # Binary Output (damper control)
/B1/R/BAS/AI-AHU1-TEMP             # AHU temperature sensor
/B1/R/BAS/DO-DAMPER-1              # Digital output for damper
```

**Use Cases:**
```bash
# Check all BAS points in Room 301
arx get /B1/3/301/BAS/*

# Read temperature sensor
arx read /B1/3/301/BAS/AI-1-1

# Set cooling setpoint
arx write /B1/3/301/BAS/AV-1-1 72

# List all unmapped BAS points
arx bas unmapped --building B1
```

---

## Common Tasks {#common-tasks}

### Task 1: Respond to Work Order

**Scenario:** "AC not cooling in Room 301"

```bash
# Step 1: Check the thermostat
arx status /B1/3/301/HVAC/STAT-01

# Step 2: Check the VAV box
arx status /B1/3/301/HVAC/VAV-301

# Step 3: Find what feeds this VAV
arx trace /B1/3/301/HVAC/VAV-301 --upstream

# Step 4: Check the air handler
arx status /B1/R/HVAC/AHU-1
```

### Task 2: Monthly Safety Check

**Scenario:** Fire extinguisher inspection

```bash
# List all fire extinguishers
arx get /*/*/SAFETY/EXTING-*

# Just floor 2
arx get /B1/2/*/SAFETY/EXTING-*

# Check last inspection date
arx query /*/*/SAFETY/EXTING-* --show last_inspection
```

### Task 3: Network Troubleshooting

**Scenario:** "No network in Room 205"

```bash
# Check wall jack
arx status /B1/2/205/NETWORK/JACK-A

# Find the switch
arx trace /B1/2/205/NETWORK/JACK-A --upstream

# Check wireless as backup
arx get /B1/2/*/NETWORK/WAP-*
```

### Task 4: Room Setup

**Scenario:** Setting up Room 205 as new office

```bash
# Step 1: See what's already there
arx get /B1/2/205/*/*

# Step 2: Check power outlets
arx get /B1/2/205/ELEC/OUTLET-*

# Step 3: Check network jacks
arx get /B1/2/205/NETWORK/JACK-*

# Step 4: Check HVAC
arx get /B1/2/205/HVAC/*
```

---

## Technical Reference {#technical-reference}

### Path Specification (EBNF)

```ebnf
path = "/" building "/" floor ["/" room] "/" system "/" equipment ;
building = segment ;
floor = segment ;
room = segment ;
system = segment ;
equipment = segment ;
segment = uppercase_char { uppercase_char | digit | "-" } ;
uppercase_char = "A" | "B" | ... | "Z" ;
digit = "0" | "1" | ... | "9" ;
```

### Validation Rules

1. **Path Structure:**
   - Must start with `/`
   - Minimum 4 segments (building/floor/system/equipment)
   - Maximum 5 segments (building/floor/room/system/equipment)
   - Segments separated by `/`

2. **Segment Rules:**
   - UPPERCASE alphanumeric only (`A-Z`, `0-9`)
   - Hyphens allowed within segment (not leading/trailing)
   - No spaces, underscores, or special characters
   - No empty segments

### Path Generation Rules

**Building Code:**
1. Convert to uppercase
2. Remove common building type words ("BUILDING", "WING", "TOWER")
3. Replace spaces with hyphens
4. Apply abbreviations: "HIGH SCHOOL" → "HS"
5. Truncate if > 15 characters
6. Fallback to "B1" if empty

**Examples:**
- "Main Building" → "MAIN"
- "Lincoln High School" → "LINCOLN-HS"
- "Building 1" → "1"

**Floor Code:**
1. Convert to uppercase
2. Apply standard mappings:
   - "GROUND", "FIRST" → "1"
   - "BASEMENT" → "B"
   - "ROOF" → "R"
3. Extract number if present
4. Fallback to "1" if empty

**Examples:**
- "Ground Floor" → "1"
- "Basement" → "B"
- "Level 3" → "3"

**Room Code:**
1. Convert to uppercase
2. Apply abbreviations: "CONFERENCE" → "CONF"
3. Remove "ROOM" keyword
4. Replace spaces with hyphens
5. Fallback to "GEN" if empty

**Examples:**
- "Room 301" → "301"
- "Conference Room 301" → "CONF-301"
- "MDF" → "MDF"

**Equipment Code:**
1. Detect equipment type from name
2. Apply standard abbreviations:
   - "PANEL" → "PANEL"
   - "TRANSFORMER" → "XFMR"
   - "AIR HANDLER" → "AHU"
   - "VAV BOX" → "VAV"
3. Append identifier
4. Format: `[TYPE]-[IDENTIFIER]`

**Examples:**
- ("Electrical Panel", "1A") → "PANEL-1A"
- ("VAV Box", "301") → "VAV-301"

### SQL Query Translation

Path patterns translate to SQL LIKE patterns:

| Path Pattern | SQL Pattern | Matches |
|--------------|-------------|---------|
| `/B1/3/301/HVAC/VAV-301` | `/B1/3/301/HVAC/VAV-301` | Exact match |
| `/B1/3/*/HVAC/*` | `/B1/3/%/HVAC/%` | Any room on floor 3 |
| `/B1/*/HVAC/VAV-*` | `/B1/%/HVAC/VAV-%` | Any VAV on any floor |

**PostgreSQL Example:**
```sql
-- Find all HVAC equipment on floor 3
SELECT * FROM equipment
WHERE path LIKE '/B1/3/%/HVAC/%';

-- Find all electrical panels
SELECT * FROM equipment
WHERE path LIKE '%/ELEC/PANEL-%';
```

### Database Schema

```sql
-- Equipment table
CREATE TABLE equipment (
    id UUID PRIMARY KEY,
    building_id UUID NOT NULL,
    floor_id UUID,
    room_id UUID,
    name TEXT NOT NULL,
    path TEXT,  -- Universal naming convention path
    type TEXT,
    category TEXT,
    CONSTRAINT equipment_path_unique UNIQUE (path)
);

CREATE INDEX idx_equipment_path ON equipment(path);
CREATE INDEX idx_equipment_path_prefix ON equipment(path text_pattern_ops);

-- BAS Points table
CREATE TABLE bas_points (
    id UUID PRIMARY KEY,
    building_id UUID NOT NULL,
    bas_system_id UUID NOT NULL,
    room_id UUID,
    point_name TEXT NOT NULL,
    path TEXT,  -- Universal naming convention path
    CONSTRAINT bas_points_path_unique UNIQUE (path)
);

CREATE INDEX idx_bas_points_path ON bas_points(path);
CREATE INDEX idx_bas_points_path_prefix ON bas_points(path text_pattern_ops);
```

### REST API Integration

**Get equipment by path:**
```
GET /api/v1/equipment/by-path?path=/B1/3/301/HVAC/VAV-301
```

**Query equipment by pattern:**
```
GET /api/v1/equipment/by-pattern?pattern=/B1/3/*/HVAC/*
```

**Create equipment with path:**
```json
POST /api/v1/equipment
{
    "name": "VAV Box 301",
    "path": "/B1/3/301/HVAC/VAV-301",
    "category": "hvac",
    "building_id": "uuid...",
    "floor_id": "uuid...",
    "room_id": "uuid..."
}
```

---

## Implementation Details {#implementation}

### What's Implemented

**Core Functions** (`pkg/naming/path.go`):
- ✅ `GenerateEquipmentPath()` - Creates universal paths
- ✅ `ParseEquipmentPath()` - Parses paths into components
- ✅ `IsValidPath()` - Validates path format
- ✅ `MatchPathPattern()` - Wildcard matching
- ✅ `BuildingCodeFromName()` - Generate building codes
- ✅ `FloorCodeFromLevel()` - Generate floor codes
- ✅ `RoomCodeFromName()` - Generate room codes
- ✅ `GenerateEquipmentCode()` - Generate equipment codes
- ✅ `GetSystemCode()` - Map categories to system codes

**Integration:**
- ✅ IFC import automatically generates paths
- ✅ BAS import generates paths
- ✅ Paths stored in Equipment and BASPoint models
- ✅ Database columns and indexes added (migration complete)

**Test Coverage:**
- ✅ 100% test coverage on path helper library
- ✅ All tests passing

### Usage in Code

**Generate a path:**
```go
import "github.com/arx-os/arxos/pkg/naming"

path := naming.GenerateEquipmentPath(
    "Main Building",  // building name
    3,                // floor level
    "Conference Room 301",  // room name
    "hvac",          // category
    "VAV Box",       // equipment name
    "301",           // equipment identifier
)
// Result: /MAIN/3/CONF-301/HVAC/VAV-301
```

**Validate a path:**
```go
if naming.IsValidPath("/B1/3/301/HVAC/VAV-301") {
    // Path is valid
}
```

**Match a pattern:**
```go
if naming.MatchPathPattern("/B1/3/*/HVAC/*", "/B1/3/301/HVAC/VAV-301") {
    // Path matches pattern
}
```

---

## Best Practices

### For Work Orders

**Instead of:**
> "Outlet not working in conference room on 3rd floor"

**Write:**
> `Check /B1/3/CONF-301/ELEC/OUTLET-2 - no power`

Now the next tech knows EXACTLY which outlet without searching.

### For Documentation

Always include the full path when documenting equipment:
- Installation date
- Maintenance history
- Warranty information
- Vendor contact

**Example:**
```
Equipment: /B1/3/301/HVAC/VAV-301
Installed: 2023-05-15
Last Service: 2024-10-01
Warranty: Expires 2026-05-15
```

### For Preventive Maintenance

Use path patterns to generate PM schedules:
```bash
# Monthly: Check all fire extinguishers
arx query /*/*/SAFETY/EXTING-* --schedule monthly

# Quarterly: Service all VAV boxes
arx query /*/*/HVAC/VAV-* --schedule quarterly

# Annual: Test all smoke detectors
arx query /*/*/SAFETY/DETECTOR-* --schedule annual
```

### For Troubleshooting

Always start with the path:
1. Identify the equipment path
2. Check status
3. Trace upstream/downstream
4. Document findings using paths

---

## Troubleshooting

**Path doesn't work?**
- Must start with `/`
- Must be UPPERCASE
- No spaces (use hyphens)
- Check for typos

**Can't find equipment?**
```bash
# Search by name instead
arx search "VAV 301"

# Or list everything in the room
arx get /B1/3/301/*/*
```

**Too many results?**
- Add more specifics to your path
- Use `--status` filters
- Narrow down to specific system

**Wrong path generated automatically?**
- Check building/floor/room names in database
- Verify system category is correct
- Equipment name should include type

---

## Historical Documents {#historical}

This guide consolidates information from the following superseded documents:

- [NAMING_CONVENTION_SUMMARY.md](../archive/naming-convention-summary-oct-2025.md) - Original summary
- [NAMING_CONVENTION_QUICK_START.md](../archive/naming-convention-quickstart-oct-2025.md) - Original quick start
- [NAMING_CONVENTION_REFERENCE.md](../archive/naming-convention-reference-oct-2025.md) - Original technical reference
- [USER_GUIDE_NAMING_CONVENTION.md](../archive/user-guide-naming-convention-oct-2025.md) - Original user guide
- [UNIVERSAL_NAMING_CONVENTION.md](../archive/universal-naming-convention-oct-2025.md) - Original specification
- [NAMING_CONVENTION_IMPLEMENTATION.md](../archive/naming-convention-implementation-oct-2025.md) - Original implementation notes

All original documents have been preserved in the archive for historical reference.

---

## Summary

**You now have:**
- ✅ Universal equipment addressing for ALL building systems
- ✅ Complete documentation for end users, administrators, and developers
- ✅ Working code with 100% test coverage
- ✅ Database schema with indexes
- ✅ Integration with IFC and BAS imports

**The foundation is solid. Time to use it!** 🚀

---

*For questions or improvements to this guide, see the [Documentation Index](../DOCUMENTATION_INDEX.md).*

