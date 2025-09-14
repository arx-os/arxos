# ArxOS Specifications

## Building UUID Format

Every building gets a globally unique identifier:

```
ARXOS-[CONTINENT]-[COUNTRY]-[STATE]-[CITY]-[SEQUENCE]

Examples:
ARXOS-NA-US-NY-NYC-0001   # First building in New York City
ARXOS-EU-UK-ENG-LON-0042  # 42nd building in London
ARXOS-AS-JP-KAN-TYO-0001  # First building in Tokyo
```

**Components:**
- `CONTINENT`: NA, SA, EU, AF, AS, OC, AN
- `COUNTRY`: ISO 3166-1 alpha-2 codes
- `STATE`: State/region code (2-3 chars)
- `CITY`: Typically airport code (3-4 chars)
- `SEQUENCE`: 4-digit number (0001-9999)

## Universal Path Structure

Every piece of equipment has a hierarchical address:

```
[BUILDING_UUID]/[WING]/[FLOOR]/[ZONE]/[ROOM]/[WALL]/[EQUIPMENT]

Example:
ARXOS-NA-US-NY-NYC-0001/N/3/A/301/E/OUTLET_02
```

**Path Components:**
- `WING`: N, S, E, W, C (cardinal directions or A, B, C...)
- `FLOOR`: B2, B1, G, 1-99, M, R, P
- `ZONE`: 3x3 grid (A-I) or numeric (01-99)
- `ROOM`: Numeric (101, 102...) or functional (CONF_A, SERVER_1)
- `WALL`: N, S, E, W, C (ceiling), F (floor)
- `EQUIPMENT`: Category_Type_ID format

## Equipment Naming Convention

```
[CATEGORY]_[TYPE]_[IDENTIFIER]

Examples:
NETWORK_SWITCH_01
ELEC_PANEL_MAIN
HVAC_RTU_01
PLUMB_VALVE_SHUT_301
FIRE_PULL_3A
SEC_CAMERA_PTZ_LOBBY
```

## BIM Text Format v2.0

```
BUILDING: Manhattan Corporate Tower
UUID: ARXOS-NA-US-NY-NYC-0001
VERSION: 2.0
CREATED: 2024-01-15T10:00:00Z
AUTHOR: John Smith

EQUIPMENT:
  ID: NETWORK_SWITCH_CORE_01
  PATH: N/3/A/301/E
  STATUS: OPERATIONAL
  TYPE: Network.Switch.Core
  MODEL: Cisco Catalyst 9300
  SERIAL: FCW2145N0XY
  INSTALLED: 2023-06-15
  MAINTAINED: 2024-01-10
  NOTES: Core switch for north wing
```

**Required Fields:**
- `ID`: Unique equipment identifier
- `PATH`: Location within building
- `STATUS`: OPERATIONAL|DEGRADED|FAILED|MAINTENANCE|OFFLINE|UNKNOWN
- `TYPE`: Category.Subcategory

**Optional Fields:**
- `MODEL`, `SERIAL`, `INSTALLED`, `MAINTAINED`
- `WARRANTY`, `SPECS`, `NOTES`, `TAGS`

## Status Values

**Standard:**
- `OPERATIONAL` - Working normally
- `DEGRADED` - Working but impaired
- `FAILED` - Not working
- `MAINTENANCE` - Under maintenance
- `OFFLINE` - Intentionally off
- `UNKNOWN` - Status unknown

**Extended (optional):**
- `OPERATIONAL-BYPASS` - Operating on bypass
- `OPERATIONAL-BACKUP` - On backup power
- `FAILED-POWER` - Power failure
- `FAILED-MECHANICAL` - Mechanical failure