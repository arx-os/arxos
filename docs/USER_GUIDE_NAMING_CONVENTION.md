# ArxOS Universal Naming Convention - User Guide

**Last Updated:** October 12, 2025
**For:** Facility Managers, Technicians, Building Operators
**Version:** 1.0

---

## Table of Contents

1. [What is the Universal Naming Convention?](#what-is-it)
2. [Why Does This Matter?](#why-it-matters)
3. [Understanding Equipment Paths](#understanding-paths)
4. [Path Format Explained](#path-format)
5. [Finding Equipment](#finding-equipment)
6. [System-Specific Examples](#system-examples)
7. [Common Tasks](#common-tasks)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## What is the Universal Naming Convention? {#what-is-it}

Every piece of equipment in your building gets a **unique address** - like a street address for physical items.

**Example:**
```
/B1/3/301/HVAC/VAV-301
```

This address tells you exactly where to find a VAV box:
- **B1** - Building 1 (Main Building)
- **3** - Floor 3
- **301** - Room 301
- **HVAC** - Heating/Cooling system
- **VAV-301** - VAV Box serving this room

**Just like a street address:**
- `123 Main Street, Boston, MA` tells you where a house is
- `/B1/3/301/HVAC/VAV-301` tells you where equipment is

---

## Why Does This Matter? {#why-it-matters}

### Before (Traditional Way):
❌ "The thermostat in that conference room on the third floor"
❌ "Outlet near the door, you know, the one by the window"
❌ "Panel 1A... or was it 1B? In the electrical room, I think?"

### After (With Universal Paths):
✅ `/B1/3/CONF-301/HVAC/STAT-01` - Thermostat in Conference Room 301
✅ `/B1/2/205/ELEC/OUTLET-A` - Outlet A in Room 205
✅ `/B1/1/ELEC-RM/ELEC/PANEL-1A` - Panel 1A in Electrical Room

### Benefits for You:

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

**3. Better Tracking**
- Know when equipment was last serviced
- Track all outlets in a room
- Find all fire extinguishers in the building

**4. Smart Queries**
```bash
# Find ALL HVAC equipment on floor 3
arx get /B1/3/*/HVAC/*

# Find ALL electrical panels
arx get /*/*/ELEC-RM/ELEC/PANEL-*

# Check status of specific equipment
arx status /B1/3/301/HVAC/VAV-301
```

---

## Understanding Equipment Paths {#understanding-paths}

Think of equipment paths as **GPS coordinates for your building**.

### The Five Levels:

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
- Can be skipped for building-level equipment (roof, basement)

**Level 4: System**
- What type of system? (`ELEC`, `HVAC`, `NETWORK`, `PLUMB`, `SAFETY`)
- Like the utility type (electric, water, etc.)

**Level 5: Equipment**
- Specific equipment identifier (`VAV-301`, `PANEL-1A`, `OUTLET-12`)
- Like the specific fixture

---

## Path Format Explained {#path-format}

### Standard Format:
```
/[BUILDING]/[FLOOR]/[ROOM]/[SYSTEM]/[EQUIPMENT]
```

### Examples by Type:

**With Room:**
```
/B1/3/301/HVAC/VAV-301
└─┬─┘─┬─┘─┬──┘──┬───┘─────┬────┘
  │   │   │     │         └─ VAV Box 301
  │   │   │     └─────────── HVAC System
  │   │   └───────────────── Room 301
  │   └───────────────────── Floor 3
  └───────────────────────── Building 1
```

**Building-Level (No Room):**
```
/B1/R/HVAC/AHU-1
└─┬─┘┬┘─┬──┘──┬──┘
  │  │  │     └─ Air Handler Unit 1
  │  │  └─────── HVAC System
  │  └────────── Roof
  └───────────── Building 1
```

### System Codes Reference:

| System | Code | Examples |
|--------|------|----------|
| Electrical | `ELEC` | Panels, outlets, transformers |
| HVAC | `HVAC` | Air handlers, VAVs, thermostats |
| Plumbing | `PLUMB` | Sinks, toilets, water heaters |
| Network | `NETWORK` | Switches, wireless APs, routers |
| Fire/Safety | `SAFETY` | Fire panels, detectors, sprinklers |
| Audio/Visual | `AV` | Projectors, displays, speakers |
| Custodial | `CUSTODIAL` | Closets, markers |
| Lighting | `LIGHTING` | Light fixtures, switches |
| Doors/Access | `DOORS` | Door controllers, card readers |
| Building Automation | `BAS` | Control points, sensors |

---

## Finding Equipment {#finding-equipment}

### Method 1: Exact Path (If You Know It)
```bash
arx get /B1/3/301/HVAC/VAV-301
```
Returns: Specific VAV box in Room 301

### Method 2: Wildcard Search (Find Multiple)
```bash
# All HVAC equipment on floor 3
arx get /B1/3/*/HVAC/*

# All electrical panels in any room
arx get /*/*/*/ELEC/PANEL-*

# All equipment in room 301
arx get /B1/3/301/*/*
```

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

### Task 2: Room Setup for New Office

**Scenario:** Setting up Room 205 as new office

```bash
# Step 1: See what's already there
arx get /B1/2/205/*/*

# Step 2: Check power outlets
arx get /B1/2/205/ELEC/OUTLET-*

# Step 3: Check network jacks
arx get /B1/2/205/NETWORK/JACK-*

# Step 4: Verify HVAC coverage
arx get /B1/2/205/HVAC/*

# Step 5: Check safety equipment
arx get /B1/2/205/SAFETY/*
```

### Task 3: Preventive Maintenance Round

**Scenario:** Monthly PM on floor 3

```bash
# Check all HVAC equipment on floor 3
arx list /B1/3/*/HVAC/* --status operational

# Check all fire safety equipment
arx list /B1/3/*/SAFETY/* --last-inspected ">30days"

# List equipment needing maintenance
arx query /B1/3/*/* --status maintenance

# Generate maintenance report
arx report /B1/3/*/* --type maintenance
```

### Task 4: Emergency Shutoff

**Scenario:** Water leak on floor 2

```bash
# Find the floor shutoff valve
arx get /B1/2/PLUMB/SHUTOFF-*

# Get valve location details
arx show /B1/2/PLUMB/SHUTOFF-2A

# Log the shutoff action
arx log /B1/2/PLUMB/SHUTOFF-2A "Emergency shutoff due to leak in Room 203"

# Find all affected fixtures
arx list /B1/2/*/PLUMB/*
```

### Task 5: Network Troubleshooting

**Scenario:** No network in Room 205

```bash
# Step 1: Check the wall jack
arx status /B1/2/205/NETWORK/JACK-A

# Step 2: Find which switch it connects to
arx trace /B1/2/205/NETWORK/JACK-A --upstream

# Step 3: Check the access switch
arx status /B1/2/IDF-2A/NETWORK/ACCESS-SW-2A

# Step 4: Check the core switch
arx status /B1/1/MDF/NETWORK/CORE-SW-1

# Step 5: Check wireless as backup
arx status /B1/2/205/NETWORK/WAP-*
```

---

## Best Practices {#best-practices}

### 1. Use Full Paths When Documenting Issues

**❌ Bad:**
```
"The thermostat in 301 isn't working"
```

**✅ Good:**
```
"Check /B1/3/301/HVAC/STAT-01 - not responding to setpoint changes"
```

### 2. Reference Paths in Work Orders

**Example Work Order:**
```
ISSUE: No power to outlet
LOCATION: /B1/2/205/ELEC/OUTLET-2
UPSTREAM: /B1/1/ELEC-RM/ELEC/SUBPANEL-2A
STATUS: Breaker tripped, reset required
```

### 3. Use Wildcards for Inspections

**Instead of checking each room individually:**
```bash
# Efficient: Check all smoke detectors on floor
arx list /B1/2/*/SAFETY/DETECTOR-*

# Less efficient: Check room by room
arx get /B1/2/201/SAFETY/DETECTOR-*
arx get /B1/2/202/SAFETY/DETECTOR-*
arx get /B1/2/203/SAFETY/DETECTOR-*
# ... 20 more commands
```

### 4. Document Equipment Relationships

**When installing new equipment, document connections:**
```bash
# New VAV box installed
arx create /B1/4/401/HVAC/VAV-401

# Link to air handler
arx link /B1/4/401/HVAC/VAV-401 --feeds-from /B1/R/HVAC/AHU-2

# Link to thermostat
arx link /B1/4/401/HVAC/VAV-401 --controlled-by /B1/4/401/HVAC/STAT-01
```

### 5. Use Tags for Additional Context

**Add tags for easier filtering:**
```bash
# Mark equipment requiring annual inspection
arx tag /B1/*/SAFETY/EXTING-* annual-inspection

# Mark equipment under warranty
arx tag /B1/3/301/HVAC/VAV-301 warranty:2026-06

# Mark equipment for replacement
arx tag /B1/1/ELEC-RM/ELEC/PANEL-1A needs-replacement
```

### 6. Keep Location Text Consistent

**When adding new equipment, use consistent naming:**

**✅ Good:**
```
/B1/2/CONF-205/HVAC/STAT-01
/B1/2/CONF-206/HVAC/STAT-01
/B1/2/CONF-207/HVAC/STAT-01
```

**❌ Inconsistent:**
```
/B1/2/Conference-Room-205/HVAC/STAT-01
/B1/2/205/HVAC/STAT-01
/B1/2/MEETING-RM-205/HVAC/STAT-01
```

---

## Troubleshooting {#troubleshooting}

### Problem: "I can't find equipment"

**Solution 1: Use broader wildcards**
```bash
# Instead of:
arx get /B1/3/301/HVAC/VAV-301

# Try:
arx get /B1/3/*/HVAC/VAV-*
```

**Solution 2: Search by name**
```bash
arx search "VAV 301"
arx search "Room 301" --type hvac
```

**Solution 3: List all equipment in area**
```bash
# See everything in room 301
arx get /B1/3/301/*/*
```

### Problem: "Path doesn't work"

**Common mistakes:**

❌ Missing leading slash
```bash
arx get B1/3/301/HVAC/VAV-301  # Wrong
arx get /B1/3/301/HVAC/VAV-301 # Correct
```

❌ Lowercase (paths are UPPERCASE)
```bash
arx get /b1/3/301/hvac/vav-301  # Wrong
arx get /B1/3/301/HVAC/VAV-301  # Correct
```

❌ Spaces in path
```bash
arx get "/B1/3/Room 301/HVAC/VAV-301"  # Wrong
arx get /B1/3/301/HVAC/VAV-301         # Correct
```

### Problem: "Too many results"

**Solution: Add more specific filters**
```bash
# Instead of all HVAC:
arx get /*/*/HVAC/*

# Narrow to floor 3:
arx get /B1/3/*/HVAC/*

# Narrow to just VAVs:
arx get /B1/3/*/HVAC/VAV-*

# Narrow to just thermostats:
arx get /B1/3/*/HVAC/STAT-*
```

### Problem: "Equipment not showing up after import"

**Possible causes:**

1. **Equipment needs mapping**
   ```bash
   # Check unmapped equipment
   arx bas unmapped --building B1

   # Map to room
   arx bas map AI-1-1 --room 301 --floor 3
   ```

2. **Import failed or partial**
   ```bash
   # Check last import status
   arx import status

   # Re-import if needed
   arx import bas /path/to/points.csv
   ```

3. **Equipment in different building/floor**
   ```bash
   # Search all buildings
   arx search "VAV-301"
   ```

### Problem: "Path changed after mapping"

**This is normal!** BAS points start with simple paths and get full paths when mapped.

**Before mapping:**
```
/B1/BAS/AI-1-1
```

**After mapping to Room 301:**
```
/B1/3/301/BAS/AI-1-1
```

This is expected behavior - the path gets more specific once we know the room.

---

## Quick Reference Card

### Path Structure
```
/[BUILDING]/[FLOOR]/[ROOM]/[SYSTEM]/[EQUIPMENT]
Example: /B1/3/301/HVAC/VAV-301
```

### System Codes
- `ELEC` - Electrical
- `HVAC` - Heating/Cooling
- `NETWORK` - IT/Network
- `PLUMB` - Plumbing
- `SAFETY` - Fire/Safety
- `BAS` - Building Automation
- `AV` - Audio/Visual
- `CUSTODIAL` - Custodial

### Common Commands
```bash
# Get specific equipment
arx get /B1/3/301/HVAC/VAV-301

# Find multiple items
arx get /B1/3/*/HVAC/*

# Check status
arx status /B1/3/301/HVAC/VAV-301

# Trace connections
arx trace /B1/2/205/ELEC/OUTLET-1 --upstream

# List by system
arx list /B1/*/HVAC/*

# Search by name
arx search "Room 301"
```

### Wildcards
- `*` - Matches any single segment
- `/*/*/HVAC/*` - All HVAC in any building/floor
- `/B1/3/*/HVAC/*` - All HVAC on floor 3 of B1
- `/B1/*/ELEC/PANEL-*` - All electrical panels in B1

---

## Getting Help

**Need assistance?**
- Run `arx help` for command documentation
- Run `arx examples` for more usage examples
- Run `arx search --help` for search syntax
- Contact your facility manager or IT department

**Finding your way around:**
```bash
# List all buildings
arx buildings

# List floors in a building
arx floors --building B1

# List rooms on a floor
arx rooms --building B1 --floor 3

# See all systems
arx systems
```

---

**Remember:** The universal naming convention makes your job easier. Every piece of equipment has ONE address that everyone uses. No more confusion, faster troubleshooting, better maintenance tracking.

**Start simple:**
1. Learn to read paths
2. Practice with `arx get` commands
3. Use wildcards for inspections
4. Reference paths in work orders

You've got this! 🏢🔧

