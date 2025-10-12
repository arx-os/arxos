# Universal Naming Convention - Technical Reference

**For:** System Administrators, Integrators, Developers
**Last Updated:** October 12, 2025

---

## Path Specification

### Format (EBNF)
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

3. **Canonical Examples:**
   ```
   VALID:
   /B1/3/301/HVAC/VAV-301
   /MAIN/2/IDF-2A/NETWORK/SW-01
   /HS-LINCOLN/1/MDF/NETWORK/CORE-SW-1

   INVALID:
   B1/3/301/HVAC/VAV-301          # Missing leading /
   /b1/3/301/hvac/vav-301         # Lowercase
   /B1//301/HVAC/VAV-301          # Empty segment
   /B1/3/Room 301/HVAC/VAV-301    # Spaces
   /B1/3/301/HVAC/VAV_301         # Underscore
   ```

---

## System Codes

### Standard System Taxonomy

| System Code | Full Name | Domain | Typical Equipment |
|-------------|-----------|--------|-------------------|
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

### System Code Aliases

For import/integration, these aliases map to standard codes:

| Alias | Maps To | Use Case |
|-------|---------|----------|
| `electrical` | `ELEC` | IFC imports, external systems |
| `hvac` | `HVAC` | IFC imports, external systems |
| `plumbing` | `PLUMB` | IFC imports, external systems |
| `network` | `NETWORK` | IT asset management systems |
| `fire` | `SAFETY` | Fire alarm systems |
| `security` | `SAFETY` | Access control systems |
| `it` | `NETWORK` | IT ticketing systems |
| `audiovisual` | `AV` | AV control systems |

---

## Path Generation Rules

### Building Code Generation

**Input:** Building name
**Output:** UPPERCASE alphanumeric code

**Rules:**
1. Convert to uppercase
2. Remove common building type words ("BUILDING", "WING", "TOWER")
3. Replace spaces with hyphens
4. Apply abbreviations:
   - "HIGH SCHOOL" → "HS"
   - "MIDDLE SCHOOL" → "MS"
   - "ELEMENTARY" → "ES"
5. Truncate if > 15 characters
6. Fallback to "B1" if empty

**Examples:**
```
"Main Building" → "MAIN"
"North Wing" → "NORTH"
"Lincoln High School" → "LINCOLN-HS"
"Building 1" → "1"
```

### Floor Code Generation

**Input:** Floor level or name
**Output:** Floor code

**Rules:**
1. Convert to uppercase
2. Apply standard mappings:
   - "GROUND", "GROUND FLOOR", "FIRST" → "1"
   - "BASEMENT", "CELLAR" → "B"
   - "ROOF", "ROOFTOP" → "R"
   - "PENTHOUSE" → "P"
   - "MEZZANINE" → "M"
3. Extract number if present ("Level 3" → "3")
4. Fallback to "1" if empty

**Examples:**
```
"Ground Floor" → "1"
"Basement" → "B"
"Roof" → "R"
"Level 3" → "3"
"Mezzanine" → "M"
```

### Room Code Generation

**Input:** Room name or number
**Output:** Room code

**Rules:**
1. Convert to uppercase
2. Apply abbreviations:
   - "CONFERENCE" → "CONF"
   - "MECHANICAL" → "MECH"
   - "ELECTRICAL" → "ELEC"
3. Remove "ROOM" keyword
4. Replace spaces with hyphens
5. Fallback to "GEN" if empty

**Examples:**
```
"Room 301" → "301"
"Conference Room 301" → "CONF-301"
"Mechanical Room A" → "MECH-A"
"MDF" → "MDF"
"IDF 2A" → "IDF-2A"
```

### Equipment Code Generation

**Input:** Equipment name, optional identifier
**Output:** Equipment code

**Rules:**
1. Detect equipment type from name
2. Apply standard abbreviations:
   - "PANEL" → "PANEL"
   - "TRANSFORMER" → "XFMR"
   - "AIR HANDLER" → "AHU"
   - "VAV BOX" → "VAV"
   - "SWITCH" → "SW"
   - "WIRELESS", "ACCESS POINT" → "WAP"
3. Append identifier if provided
4. Format: `[TYPE]-[IDENTIFIER]`

**Examples:**
```
("Electrical Panel", "1A") → "PANEL-1A"
("VAV Box", "301") → "VAV-301"
("Transformer", "T1") → "XFMR-T1"
("Network Switch", "2F-01") → "SW-2F-01"
```

---

## Path Query Patterns

### Wildcard Syntax

**Single-level wildcard:** `*`
- Matches any single path segment
- Does not match across path separators

**Examples:**
```
/B1/3/*/HVAC/*           # Any room on floor 3, any HVAC equipment
/*/*/301/HVAC/*          # Room 301 on any floor in any building
/B1/*/IDF-*/NETWORK/*    # Any IDF on any floor in B1
```

### SQL Translation

Path patterns translate to SQL LIKE patterns:

| Path Pattern | SQL Pattern | Matches |
|--------------|-------------|---------|
| `/B1/3/301/HVAC/VAV-301` | `/B1/3/301/HVAC/VAV-301` | Exact match |
| `/B1/3/*/HVAC/*` | `/B1/3/%/HVAC/%` | Any room on floor 3 |
| `/B1/*/HVAC/VAV-*` | `/B1/%/HVAC/VAV-%` | Any VAV on any floor |
| `/*/*/HVAC/*` | `/%/%/HVAC/%` | All HVAC (4-segment paths) |
| `/*/*/*/HVAC/*` | `/%/%/%/HVAC/%` | All HVAC (5-segment paths) |

### Query Examples

**PostgreSQL:**
```sql
-- Find all HVAC equipment on floor 3
SELECT * FROM equipment
WHERE path LIKE '/B1/3/%/HVAC/%';

-- Find all electrical panels
SELECT * FROM equipment
WHERE path LIKE '%/ELEC/PANEL-%';

-- Find equipment in specific room
SELECT * FROM equipment
WHERE path LIKE '/B1/2/205/%';

-- Find all BAS points in room 301
SELECT * FROM bas_points
WHERE path LIKE '%/301/BAS/%';
```

---

## Database Schema

### Equipment Table
```sql
CREATE TABLE equipment (
    id UUID PRIMARY KEY,
    building_id UUID NOT NULL,
    floor_id UUID,
    room_id UUID,
    name TEXT NOT NULL,
    path TEXT,  -- Universal naming convention path
    type TEXT,
    category TEXT,
    -- ... other fields ...

    CONSTRAINT equipment_path_unique UNIQUE (path)
);

CREATE INDEX idx_equipment_path ON equipment(path);
CREATE INDEX idx_equipment_path_prefix ON equipment(path text_pattern_ops);
```

### BAS Points Table
```sql
CREATE TABLE bas_points (
    id UUID PRIMARY KEY,
    building_id UUID NOT NULL,
    bas_system_id UUID NOT NULL,
    room_id UUID,
    point_name TEXT NOT NULL,
    path TEXT,  -- Universal naming convention path
    -- ... other fields ...

    CONSTRAINT bas_points_path_unique UNIQUE (path)
);

CREATE INDEX idx_bas_points_path ON bas_points(path);
CREATE INDEX idx_bas_points_path_prefix ON bas_points(path text_pattern_ops);
```

---

## API Integration

### REST API

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

### CLI

**Commands:**
```bash
# Get by exact path
arx get /B1/3/301/HVAC/VAV-301

# Query by pattern
arx query /B1/3/*/HVAC/*

# List by system
arx list /B1/*/HVAC/*

# Create with path
arx create equipment \
    --path /B1/3/301/HVAC/VAV-301 \
    --name "VAV Box 301" \
    --category hvac
```

---

## Import/Export

### IFC Import Path Generation

When importing IFC files:

1. Extract building name → Generate building code
2. Extract floor level → Generate floor code
3. Extract space/room name → Generate room code
4. Map IFC entity type → System code
5. Extract equipment tag → Equipment code
6. Assemble path

**Example:**
```
IFC: IfcBuildingStorey
  Name: "Level 3"
  → Floor code: "3"

IFC: IfcSpace
  Name: "Conference Room 301"
  → Room code: "CONF-301"

IFC: IfcFlowTerminal
  ObjectType: "IfcAirTerminalBox"
  Tag: "VAV-301"
  → System: "HVAC"
  → Equipment: "VAV-301"

Generated Path: /B1/3/CONF-301/HVAC/VAV-301
```

### BAS Import Path Generation

When importing BAS points from CSV:

**Initial path (unmapped):**
```
/B1/BAS/[POINT-NAME]
```

**After room mapping:**
```
/B1/[FLOOR]/[ROOM]/BAS/[POINT-NAME]
```

**Example:**
```
Import: AI-1-1, Location: "Floor 3 Room 301"
Initial: /B1/BAS/AI-1-1
Mapped:  /B1/3/301/BAS/AI-1-1
```

---

## Path Validation Algorithm

### Pseudocode
```python
def validate_path(path: str) -> bool:
    # Check leading slash
    if not path.startswith('/'):
        return False

    # Split into segments
    segments = path[1:].split('/')

    # Check segment count (4 or 5)
    if len(segments) < 4 or len(segments) > 5:
        return False

    # Validate each segment
    for segment in segments:
        if not segment:  # Empty segment
            return False
        if not re.match(r'^[A-Z0-9]+(-[A-Z0-9]+)*$', segment):
            return False

    return True
```

### Validation States
```
VALID   - Path meets all requirements
INVALID - Path format incorrect
PARTIAL - Path incomplete (during construction)
```

---

## Backward Compatibility

### Legacy System Integration

**If legacy systems use different identifiers:**

1. Store both in metadata:
   ```json
   {
       "path": "/B1/3/301/HVAC/VAV-301",
       "legacy_id": "AHU-3-301-VAV",
       "asset_tag": "HVAC-12345"
   }
   ```

2. Maintain lookup table:
   ```sql
   CREATE TABLE legacy_id_mapping (
       legacy_id TEXT PRIMARY KEY,
       arxos_path TEXT NOT NULL,
       system_source TEXT
   );
   ```

3. Provide translation API:
   ```
   GET /api/v1/equipment/translate?legacy_id=AHU-3-301-VAV
   → {"path": "/B1/3/301/HVAC/VAV-301"}
   ```

---

## Performance Considerations

### Indexing Strategy

**PostgreSQL:**
```sql
-- Standard B-tree index for exact matches
CREATE INDEX idx_equipment_path ON equipment(path);

-- Operator class index for LIKE queries
CREATE INDEX idx_equipment_path_prefix
    ON equipment(path text_pattern_ops);

-- Partial indexes for common queries
CREATE INDEX idx_equipment_hvac
    ON equipment(path)
    WHERE category = 'hvac';

CREATE INDEX idx_equipment_floor3
    ON equipment(path)
    WHERE path LIKE '/B1/3/%';
```

### Query Optimization

**Use specific patterns when possible:**
```sql
-- Good: Uses index efficiently
SELECT * FROM equipment WHERE path LIKE '/B1/3/%/HVAC/%';

-- Less efficient: Broader pattern
SELECT * FROM equipment WHERE path LIKE '%/HVAC/%';

-- Best: Exact match
SELECT * FROM equipment WHERE path = '/B1/3/301/HVAC/VAV-301';
```

---

## Security Considerations

### Path-Based Access Control

**Example:**
```yaml
roles:
  floor_tech:
    permissions:
      - read: "/B1/3/*"    # Can read everything on floor 3
      - write: "/B1/3/*/HVAC/*"  # Can modify HVAC on floor 3

  hvac_tech:
    permissions:
      - read: "/*/*/HVAC/*"  # Can read all HVAC
      - write: "/*/*/HVAC/*" # Can modify all HVAC

  admin:
    permissions:
      - read: "/*"   # Can read everything
      - write: "/*"  # Can modify everything
```

---

## References

- **Implementation:** `/pkg/naming/path.go`
- **Tests:** `/pkg/naming/path_test.go`
- **User Guide:** `/docs/USER_GUIDE_NAMING_CONVENTION.md`
- **Quick Start:** `/docs/NAMING_CONVENTION_QUICK_START.md`
- **Specification:** `/docs/architecture/UNIVERSAL_NAMING_CONVENTION.md`

---

**Version History:**
- 1.0 (2025-10-12): Initial specification

