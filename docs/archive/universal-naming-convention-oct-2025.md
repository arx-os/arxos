# ArxOS Universal Naming Convention

**Last Updated:** October 12, 2025
**Status:** Core Specification - Required for All Systems
**Priority:** CRITICAL - Nothing works without this

---

## Purpose

Every component in ArxOS (across ALL building systems) needs a **universal, human-readable path** that uniquely identifies it and its location. This convention works for electrical, HVAC, plumbing, network, custodial, safety, AV, and any future systems.

---

## Universal Path Format

```
/[BUILDING]/[FLOOR]/[ROOM]/[SYSTEM]/[EQUIPMENT]
```

### Format Rules:
- **Segments:** Separated by forward slashes `/`
- **Case:** UPPERCASE for consistency
- **Characters:** Alphanumeric only (A-Z, 0-9, hyphens allowed)
- **Hierarchy:** Left to right, general to specific
- **Required:** Building and at least one more level
- **Optional:** Room can be omitted for building-level equipment

---

## Segment Definitions

### 1. BUILDING Segment
**Format:** `B[NUMBER]` or `[BUILDING-CODE]`

**Examples:**
- `B1` - Building 1
- `MAIN` - Main Building
- `NORTH-WING` - North Wing Building
- `HS-LINCOLN` - Lincoln High School

**Purpose:** Uniquely identifies the building/structure

### 2. FLOOR Segment
**Format:** `[NUMBER]` or `[LEVEL-CODE]`

**Examples:**
- `1` - Floor 1 (ground floor)
- `2` - Floor 2
- `B` - Basement
- `R` - Roof
- `M` - Mezzanine

**Purpose:** Identifies vertical level within building

### 3. ROOM Segment (Optional)
**Format:** `[ROOM-NUMBER]` or `[ZONE-CODE]`

**Examples:**
- `101` - Room 101
- `CONF-301` - Conference Room 301
- `MDF` - Main Distribution Frame
- `MECH-A` - Mechanical Room A
- `HALL-2A` - Hallway 2A

**Purpose:** Identifies specific space or zone
**Note:** Can be omitted for building/floor-level equipment (electrical rooms, rooftop units, etc.)

### 4. SYSTEM Segment
**Format:** `[SYSTEM-CATEGORY]`

**Standard Categories:**
- `ELEC` - Electrical
- `HVAC` - Heating, Ventilation, Air Conditioning
- `PLUMB` - Plumbing
- `NETWORK` - IT/Network infrastructure
- `SAFETY` - Fire safety, life safety
- `AV` - Audio/Visual systems
- `CUSTODIAL` - Custodial markers/equipment
- `LIGHTING` - Lighting systems
- `DOORS` - Doors, access control
- `ENERGY` - Energy monitoring
- `BAS` - Building Automation System points

**Purpose:** Groups equipment by building system

### 5. EQUIPMENT Segment
**Format:** `[EQUIPMENT-TYPE]-[NUMBER]` or `[UNIQUE-ID]`

**Examples:**
- `PANEL-1A` - Electrical Panel 1A
- `VAV-301` - VAV Box for Room 301
- `SW-2F-01` - Switch on Floor 2, first switch
- `OUTLET-12` - Outlet number 12
- `TEMP-01` - Temperature sensor 1
- `WAP-205` - Wireless Access Point in Room 205
- `EXTINGUISHER-3` - Fire Extinguisher #3

**Purpose:** Uniquely identifies specific equipment within system

---

## Complete Path Examples (All Systems)

### Electrical System
```
/B1/1/101/ELEC/OUTLET-1        # Outlet in Room 101
/B1/1/ELEC-RM/ELEC/PANEL-1A    # Main Panel in Electrical Room
/B1/1/ELEC-RM/ELEC/XFMR-T1     # Transformer in Electrical Room
/B1/2/204/ELEC/OUTLET-A        # Outlet in Room 204
/B1/R/ELEC/DISCONNECT-ROOF     # Roof disconnect
```

### HVAC System
```
/B1/R/HVAC/AHU-1               # Air Handler on Roof
/B1/3/HVAC/VAV-301             # VAV Box for Floor 3
/B1/3/301/HVAC/STAT-01         # Thermostat in Room 301
/B1/3/301/HVAC/DIFFUSER-A      # Diffuser in Room 301
/B1/B/HVAC/CHILLER-1           # Chiller in Basement
```

### Network/IT System
```
/B1/1/MDF/NETWORK/CORE-SW-1    # Core Switch in MDF
/B1/2/IDF-2A/NETWORK/ACCESS-SW-2A  # Access Switch in IDF
/B1/2/205/NETWORK/WAP-205      # Wireless AP in Room 205
/B1/2/205/NETWORK/JACK-A       # Network Jack in Room 205
/B1/1/SERVER/NETWORK/UPS-1     # UPS in Server Room
```

### Plumbing System
```
/B1/B/PLUMB/WATER-HEATER-1     # Water Heater in Basement
/B1/2/PLUMB/RISER-2A           # Water Riser for Floor 2
/B1/2/203/PLUMB/SINK-01        # Sink in Room 203
/B1/2/204/PLUMB/TOILET-01      # Toilet in Room 204
/B1/3/PLUMB/PRV-3              # Pressure Reducing Valve, Floor 3
```

### Safety/Fire System
```
/B1/1/SAFETY/FIRE-PANEL-1      # Fire Alarm Panel, Floor 1
/B1/2/HALL-2A/SAFETY/DETECTOR-12  # Smoke Detector in Hallway
/B1/3/301/SAFETY/SPRINKLER-A   # Sprinkler Head in Room 301
/B1/2/STAIR-B/SAFETY/EXTINGUISHER-2B  # Fire Extinguisher in Stairwell B
/B1/1/LOBBY/SAFETY/AED-01      # AED in Lobby
```

### Custodial System
```
/B1/1/CUST-01/CUSTODIAL/CLOSET-1  # Custodial Closet
/B1/2/HALL-2A/CUSTODIAL/SPILL-MARKER-001  # Spill Marker
/B1/3/CUSTODIAL/WASTE-CHUTE    # Waste Chute
/B1/R/CUSTODIAL/GREASE-TRAP    # Roof Grease Trap
```

### AV System
```
/B1/3/CONF-301/AV/PROJECTOR-01  # Projector in Conference Room
/B1/3/CONF-301/AV/SCREEN-01     # Projection Screen
/B1/2/CLASSROOM-205/AV/DISPLAY-01  # Display in Classroom
/B1/1/AV-RACK/AV/SWITCHER-1     # AV Switcher in Rack
/B1/3/CONF-301/AV/MIC-PODIUM    # Podium Microphone
```

### BAS Points (Control Points from any system)
```
/B1/3/301/BAS/AI-1-1           # Analog Input (temp sensor) Room 301
/B1/3/301/BAS/AV-1-1           # Analog Value (setpoint) Room 301
/B1/R/BAS/DO-DAMPER-1          # Digital Output (roof damper)
```

---

## Path Component Naming Standards

### Building Identifiers
- **Single Building:** `B1`, `MAIN`, `CENTRAL`
- **Campus/Multiple:** `NORTH`, `SOUTH`, `EAST`, `WEST`
- **Specific Names:** `HS-LINCOLN`, `ADMIN`, `GYM`

### Floor Identifiers
- **Numbered:** `1`, `2`, `3`, `4`, etc.
- **Basement:** `B`, `B1`, `B2` (if multiple basement levels)
- **Roof:** `R`, `ROOF`, `PENTHOUSE`
- **Mezzanine:** `M`, `M2`, etc.

### Room Identifiers
- **Simple Numbers:** `101`, `205`, `301`
- **Named Rooms:** `CONF-301`, `LOBBY`, `GYM`, `CAFETERIA`
- **Special Spaces:** `MDF`, `IDF-2A`, `MECH-A`, `ELEC-RM`, `SERVER-RM`
- **Zones:** `HALL-2A`, `STAIR-B`, `LOADING-DOCK`

### System Categories (Fixed)
- `ELEC` - Electrical
- `HVAC` - HVAC
- `PLUMB` - Plumbing
- `NETWORK` - IT/Network
- `SAFETY` - Fire/Safety
- `AV` - Audio/Visual
- `CUSTODIAL` - Custodial
- `LIGHTING` - Lighting
- `DOORS` - Doors/Access
- `ENERGY` - Energy monitoring
- `BAS` - Building Automation

### Equipment Identifiers
- **Type-Number:** `PANEL-1A`, `VAV-301`, `OUTLET-12`
- **Type-Location:** `SW-2F-01` (Switch Floor 2, #1)
- **Descriptive:** `MAIN-DISCONNECT`, `CORE-SW-1`
- **Sequential:** `DETECTOR-12`, `DIFFUSER-A`, `JACK-A`

---

## Implementation in Code

### Equipment Creation with Path
```go
equipment := &domain.Equipment{
    ID:       types.NewID(),
    Name:     "Electrical Panel 1A",
    Path:     "/B1/1/ELEC-RM/ELEC/PANEL-1A",
    Category: "electrical",
    Subtype:  "distribution_panel",
    BuildingID: buildingID,
    FloorID:    floorID,
    RoomID:     roomID,
    Location: &domain.Location{X: 10.5, Y: 5.2, Z: 1.8},
}
```

### Querying by Path
```go
// Find all electrical equipment in room 101
equipment := equipmentRepo.FindByPath("/B1/1/101/ELEC/*")

// Find all HVAC equipment on floor 3
equipment := equipmentRepo.FindByPath("/B1/3/*/HVAC/*")

// Find specific outlet
outlet := equipmentRepo.GetByPath("/B1/1/101/ELEC/OUTLET-1")
```

### CLI Usage
```bash
# Query by path pattern
arx get /B1/3/*/HVAC/*                    # All HVAC on floor 3
arx query /B1/*/ELEC/PANEL-* --status ok  # All electrical panels
arx set /B1/3/301/HVAC/STAT-01 temp:72    # Set thermostat

# List by system
arx list /B1/*/NETWORK/*                  # All network equipment
arx trace /B1/1/101/ELEC/OUTLET-1 --upstream  # Trace power source
```

---

## Path Generation Rules

### For IFC Import:
```
Building: IfcBuilding.Name → sanitize → Building code
Floor: IfcBuildingStorey.Elevation → Floor number
Room: IfcSpace.Name → Room identifier
Equipment: IfcProduct.ObjectType + Tag → Equipment ID

Example:
IfcBuildingStorey: "Level 1" → /B1/1
IfcSpace: "Conference Room 301" → /B1/3/CONF-301
IfcFlowTerminal: Tag="VAV-301" → /B1/3/301/HVAC/VAV-301
```

### For Manual Creation:
```
User provides:
- Building: "Main Building" → /MAIN
- Floor: 3 → /MAIN/3
- Room: "Room 301" → /MAIN/3/301
- System: "HVAC" → /MAIN/3/301/HVAC
- Equipment: "VAV Box 301" → /MAIN/3/301/HVAC/VAV-301

Full Path: /MAIN/3/301/HVAC/VAV-301
```

### For BAS Points:
```
BAS Point Name: "AI-1-1" (Analog Input, Floor 1, Device 1)
Room: Room 101
System: BAS (control point system)

Generated Path: /B1/1/101/BAS/AI-1-1
```

---

## Path Validation

### Valid Paths:
- ✅ `/B1/1/101/ELEC/OUTLET-1`
- ✅ `/MAIN/3/CONF-301/HVAC/VAV-301`
- ✅ `/B1/R/HVAC/AHU-1`
- ✅ `/HS-LINCOLN/2/IDF-2A/NETWORK/SW-01`

### Invalid Paths:
- ❌ `/b1/1/101/elec/outlet-1` (lowercase)
- ❌ `/B1//101/ELEC/OUTLET-1` (empty segment)
- ❌ `/B1/1/Room 101/ELEC/OUTLET-1` (spaces not allowed)
- ❌ `B1/1/101/ELEC/OUTLET-1` (missing leading slash)

### Validation Function:
```go
func IsValidPath(path string) bool {
    if !strings.HasPrefix(path, "/") {
        return false
    }

    segments := strings.Split(path[1:], "/")
    if len(segments) < 2 {
        return false  // Need at least building + one more level
    }

    for _, segment := range segments {
        if segment == "" {
            return false  // No empty segments
        }
        if !regexp.MustCompile(`^[A-Z0-9-]+$`).MatchString(segment) {
            return false  // Only uppercase alphanumeric + hyphens
        }
    }

    return true
}
```

---

## System-Specific Naming Conventions

### Electrical Equipment
**Naming Pattern:** `[TYPE]-[IDENTIFIER]`

- **Transformers:** `XFMR-T1`, `XFMR-MAIN`
- **Panels:** `PANEL-1A`, `PANEL-MAIN`, `SUBPANEL-2B`
- **Circuits:** `CIRCUIT-12`, `CIRCUIT-A3`
- **Outlets:** `OUTLET-1`, `OUTLET-A`, `RECEP-12`
- **Switches:** `SWITCH-1`, `DIMMER-A`
- **Lights:** `LIGHT-1`, `FIXTURE-A12`

**Example Hierarchy:**
```
/B1/1/ELEC-RM/ELEC/XFMR-T1       (Transformer)
  ↓ feeds
/B1/1/ELEC-RM/ELEC/PANEL-1A      (Main Panel)
  ↓ feeds
/B1/1/ELEC-RM/ELEC/SUBPANEL-1B   (Subpanel)
  ↓ feeds
/B1/1/101/ELEC/OUTLET-1          (Outlet)
```

### HVAC Equipment
**Naming Pattern:** `[TYPE]-[ZONE/NUMBER]`

- **Air Handlers:** `AHU-1`, `AHU-NORTH`
- **VAV Boxes:** `VAV-301`, `VAV-2A`
- **Thermostats:** `STAT-01`, `TSTAT-301`
- **Diffusers:** `DIFFUSER-A`, `DIFFUSER-01`
- **Dampers:** `DAMPER-01`, `DAMPER-MAIN`
- **Chillers:** `CHILLER-1`, `CHILLER-CENTRAL`

**Example Hierarchy:**
```
/B1/R/HVAC/AHU-1                 (Air Handler on Roof)
  ↓ feeds
/B1/3/HVAC/VAV-301               (VAV Box, Floor 3)
  ↓ serves
/B1/3/301/HVAC/DIFFUSER-A        (Diffuser in Room 301)
/B1/3/301/HVAC/STAT-01           (controls) VAV-301
```

### Network Equipment
**Naming Pattern:** `[TYPE]-[LOCATION]-[NUMBER]`

- **Switches:** `CORE-SW-1`, `ACCESS-SW-2A`, `SW-2F-01`
- **Routers:** `ROUTER-MAIN`, `RTR-EDGE-1`
- **Wireless APs:** `WAP-205`, `AP-2F-01`
- **Firewalls:** `FW-DMZ-1`, `FIREWALL-MAIN`
- **Patch Panels:** `PATCH-24P-A`, `PP-2A-01`
- **Network Jacks:** `JACK-A`, `JACK-205-01`

**Example Hierarchy:**
```
/B1/1/MDF/NETWORK/CORE-SW-1      (Core Switch in MDF)
  ↓ connects_to
/B1/2/IDF-2A/NETWORK/ACCESS-SW-2A  (Access Switch in IDF)
  ↓ connects_to
/B1/2/205/NETWORK/WAP-205        (Wireless AP in Room 205)
```

### Plumbing Equipment
**Naming Pattern:** `[TYPE]-[ZONE/NUMBER]`

- **Water Heaters:** `WH-1`, `WATER-HEATER-MAIN`
- **Risers:** `RISER-A`, `RISER-NORTH`
- **Fixtures:** `SINK-01`, `TOILET-01`, `FOUNTAIN-A`
- **Valves:** `VALVE-MAIN`, `PRV-2`, `SHUTOFF-A`
- **Pumps:** `PUMP-CIRC-1`, `PUMP-SUMP-B`

**Example Hierarchy:**
```
/B1/B/PLUMB/WATER-HEATER-1       (Water Heater)
  ↓ feeds
/B1/2/PLUMB/RISER-A              (Riser to Floor 2)
  ↓ feeds
/B1/2/203/PLUMB/SINK-01          (Sink in Room 203)
```

### Safety Equipment
**Naming Pattern:** `[TYPE]-[LOCATION]-[NUMBER]`

- **Fire Panels:** `FIRE-PANEL-1`, `FACP-MAIN`
- **Detectors:** `DETECTOR-12`, `SMOKE-DET-2A-01`
- **Sprinklers:** `SPRINKLER-A`, `SPK-301-A`
- **Extinguishers:** `EXTINGUISHER-3`, `EXTING-2A-01`
- **Pull Stations:** `PULL-STN-A`, `PULL-2A`
- **AEDs:** `AED-01`, `AED-LOBBY`

### AV Equipment
**Naming Pattern:** `[TYPE]-[ROOM]-[NUMBER]`

- **Projectors:** `PROJ-301`, `PROJECTOR-CONF-A`
- **Displays:** `DISPLAY-01`, `TV-LOBBY-1`
- **Switchers:** `SWITCHER-AV-RACK-1`
- **Amplifiers:** `AMP-301`, `AMPLIFIER-A`
- **Microphones:** `MIC-PODIUM`, `MIC-CEILING-01`

### Custodial Markers
**Naming Pattern:** `[TYPE]-[SEQUENCE]`

- **Spill Markers:** `SPILL-MARKER-001`, `SPILL-2A-12`
- **Maintenance Flags:** `MAINT-FLAG-05`, `FLAG-TILE-A3`
- **Cleaning Zones:** `CLEAN-ZONE-A`, `ZONE-RESTROOM-2A`

---

## Path Helper Functions

### Generate Path from Components
```go
func GenerateEquipmentPath(building, floor, room, system, equipment string) string {
    if room == "" {
        // Building/Floor level equipment (no room)
        return fmt.Sprintf("/%s/%s/%s/%s", building, floor, system, equipment)
    }
    // Full path with room
    return fmt.Sprintf("/%s/%s/%s/%s/%s", building, floor, room, system, equipment)
}
```

### Parse Path into Components
```go
func ParseEquipmentPath(path string) (building, floor, room, system, equipment string, err error) {
    if !strings.HasPrefix(path, "/") {
        return "", "", "", "", "", fmt.Errorf("path must start with /")
    }

    segments := strings.Split(path[1:], "/")

    if len(segments) < 4 {
        return "", "", "", "", "", fmt.Errorf("path must have at least 4 segments")
    }

    building = segments[0]
    floor = segments[1]

    if len(segments) == 4 {
        // No room (building/floor level)
        system = segments[2]
        equipment = segments[3]
        room = ""
    } else {
        // Full path with room
        room = segments[2]
        system = segments[3]
        equipment = segments[4]
    }

    return building, floor, room, system, equipment, nil
}
```

### Query by Path Pattern
```go
func MatchPathPattern(path, pattern string) bool {
    // pattern: "/B1/3/*/HVAC/*" matches any HVAC on floor 3
    // pattern: "/B1/*/ELEC/PANEL-*" matches any electrical panel

    pathSegs := strings.Split(path, "/")
    patternSegs := strings.Split(pattern, "/")

    if len(pathSegs) != len(patternSegs) {
        return false
    }

    for i, patternSeg := range patternSegs {
        if patternSeg == "*" {
            continue  // Wildcard matches anything
        }
        if patternSeg != pathSegs[i] {
            return false
        }
    }

    return true
}
```

---

## Database Implementation

### Equipment Table Path Column
```sql
ALTER TABLE equipment ADD COLUMN path TEXT;
CREATE INDEX idx_equipment_path ON equipment(path);
CREATE INDEX idx_equipment_path_prefix ON equipment(path text_pattern_ops);  -- For LIKE queries
```

### Path-Based Queries
```sql
-- Find all HVAC on floor 3
SELECT * FROM equipment WHERE path LIKE '/B1/3/%/HVAC/%';

-- Find all electrical panels
SELECT * FROM equipment WHERE path LIKE '%/ELEC/PANEL-%';

-- Find equipment in specific room
SELECT * FROM equipment WHERE path LIKE '/B1/2/205/%';
```

---

## Integration with Existing Systems

### IFC Import:
When importing IFC, generate paths:
```
IfcSpace: "Conference Room 301", Floor 3
  → Room Path: /B1/3/CONF-301

IfcFlowTerminal (VAV): Tag "VAV-301" in that space
  → Equipment Path: /B1/3/CONF-301/HVAC/VAV-301
```

### BAS Import:
When importing BAS points, map to paths:
```
BAS Point: "AI-3-301" (Analog Input, Floor 3, Room 301)
Location Text: "Floor 3 Room 301"
  → Map to Room: /B1/3/301
  → Full Path: /B1/3/301/BAS/AI-3-301
```

### Manual Equipment Creation:
```bash
arx equipment create \
  --name "Electrical Panel 1A" \
  --building B1 \
  --floor 1 \
  --room ELEC-RM \
  --system ELEC \
  --equipment PANEL-1A

# Auto-generates path: /B1/1/ELEC-RM/ELEC/PANEL-1A
```

---

## Best Practices

### 1. Consistency Across Systems
- ✅ Same building/floor/room codes across all systems
- ✅ System category uppercase and standardized
- ✅ Equipment naming follows type-identifier pattern

### 2. Human Readable
- ✅ Paths should be guessable: `/B1/2/205/NETWORK/WAP-205`
- ✅ Not cryptic: ❌ `/B1/2/205/NW/W205A3F`
- ✅ Self-documenting: WAP = Wireless Access Point

### 3. Query Friendly
- ✅ Wildcards work: `/B1/*/ELEC/*` finds all electrical
- ✅ Prefixes work: LIKE `/B1/3/%` finds floor 3
- ✅ Pattern matching: `/*/*/SAFETY/*` finds all safety equipment

### 4. Scalable
- ✅ Supports multiple buildings: `/NORTH/`, `/SOUTH/`
- ✅ Supports subbasements: `/B1/B2/` (Basement level 2)
- ✅ Supports equipment densities: `/B1/2/205/NETWORK/WAP-205-01` (multiple WAPs)

---

## Implementation Status

### ✅ What Exists:
- Path field in Equipment model
- Path validation function
- Component.Path in domain-agnostic model
- Examples in README

### ⚠️ What Needs Implementation:
- **Path generation during IFC import** (currently not setting paths)
- **Path generation during BAS import** (not setting paths)
- **Path generation during equipment creation** (CLI/API)
- **Path-based query functions** (FindByPath, MatchPattern)
- **Path indexing in database** (for performance)
- **Path display in CLI/API responses**

### ❌ What's Missing (Critical):
- **Automatic path generation** when creating equipment
- **Path-based CLI queries** (`arx get /B1/3/*/HVAC/*`)
- **Path uniqueness validation**
- **Path update when equipment moves**

---

## Next Steps to Implement

### Priority 1: Add Path Generation (4-6 hours)

1. **Update Equipment Creation**
```go
// In EquipmentUseCase.CreateEquipment()
func (uc *EquipmentUseCase) CreateEquipment(ctx context.Context, req CreateEquipmentRequest) (*Equipment, error) {
    // ... validation ...

    // Generate path
    path := GenerateEquipmentPath(
        req.BuildingCode,  // Need to add to request
        req.FloorCode,     // Need to add to request
        req.RoomCode,      // Need to add or derive from RoomID
        req.System,        // Map category → system code
        req.EquipmentCode, // Generate from name or allow custom
    )

    equipment := &Equipment{
        // ... other fields ...
        Path: path,
    }

    return equipment, nil
}
```

2. **Update IFC Import to Generate Paths**
```go
// In ifc_usecase.go extractEquipment()
equipment := &Equipment{
    // ... existing fields ...
    Path: generatePathFromIFC(buildingCode, floor.Level, room.Number, category, equipmentCode),
}
```

3. **Update BAS Import to Generate Paths**
```go
// In bas_import_usecase.go
point := &BASPoint{
    // ... existing fields ...
    Path: fmt.Sprintf("/%s/%s/%s/BAS/%s", buildingCode, floorCode, roomCode, point.PointName),
}
```

### Priority 2: Add Path-Based Queries (3-4 hours)

1. **Repository Methods**
```go
FindByPath(ctx context.Context, pathPattern string) ([]*Equipment, error)
GetByPath(ctx context.Context, path string) (*Equipment, error)
```

2. **CLI Commands**
```bash
arx get /B1/3/*/HVAC/*
arx query /B1/*/ELEC/PANEL-* --status operational
arx set /B1/3/301/HVAC/STAT-01 temp:72
```

### Priority 3: Path Validation & Uniqueness (2-3 hours)

1. **Unique Constraint**
```sql
ALTER TABLE equipment ADD CONSTRAINT equipment_path_unique UNIQUE (path);
```

2. **Validation on Create/Update**
```go
if !IsValidPath(equipment.Path) {
    return fmt.Errorf("invalid equipment path format: %s", equipment.Path)
}
```

---

## Why This Matters

**Without universal naming convention:**
- ❌ Can't query across systems consistently
- ❌ Can't test workflows (equipment has no addressable identity)
- ❌ IFC import creates equipment but no queryable paths
- ❌ BAS points have no standard addressing
- ❌ CLI path queries don't work
- ❌ Equipment relationships unclear
- ❌ Can't demonstrate to workplace (no way to reference specific equipment)

**With universal naming convention:**
- ✅ Every piece of equipment has unique, human-readable address
- ✅ Can query any system the same way (`/*/*/SYSTEM/*`)
- ✅ IFC import creates addressable equipment
- ✅ BAS points integrate naturally (`/B1/3/301/BAS/AI-1-1`)
- ✅ CLI is powerful (`arx get /B1/3/*/HVAC/*`)
- ✅ Relationships are clear (path shows hierarchy)
- ✅ Demo-able to colleagues ("show me all outlets on floor 2")

---

**Status:** Specification complete. Implementation needed for path generation and queries.

**Critical Path:** This must be implemented before meaningful testing of any building system workflows.

**Estimated Effort:** 9-13 hours to implement fully across IFC import, BAS import, equipment creation, and path-based queries.

