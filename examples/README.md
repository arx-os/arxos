# ArxOS BIM Examples

This directory contains example Building Information Model (BIM) files in ArxOS format.

## BIM File Format

ArxOS uses a human-readable text format (`.bim.txt`) for building definitions. The format is hierarchical and indentation-based.

### Structure

```
BUILDING: <arxos-id> <name>
ADDRESS: <full-address>

FLOOR: <id> <name>
  ROOM: <id> [type] <name>
    EQUIPMENT: <id> [type] <name>
```

### Universal Addressing

Every component has a unique address following the pattern:
- Building: `ARXOS-<continent>-<country>-<state>-<city>-<building-id>`
- Floor: `<building-id>/<floor-id>`
- Room: `<building-id>/<floor-id>/<room-id>`
- Equipment: `<building-id>/<floor-id>/<room-id>/<equipment-id>`

Example: `ARXOS-NA-US-NY-NYC-0001/3/301/COMP_04`

## Example Files

### office_building.bim.txt
A modern office building with:
- Ground floor with lobby, reception, and conference rooms
- Executive floor with offices and meeting rooms
- Open workspace floor
- Rooftop mechanical systems

### residential_building.bim.txt
An apartment building with:
- Ground floor amenities (gym, laundry)
- Multiple residential units (studio, 1BR, 2BR)
- Rooftop deck
- Basement parking with EV chargers

## Using the Examples

1. Copy an example file to your project directory
2. Modify the building ID, name, and address
3. Adjust floors, rooms, and equipment as needed
4. Use ArxOS commands to query and manage the building:

```bash
# List all components
arx list

# List specific types
arx list --type room
arx list --type equipment

# Search for items
arx search "conference"
arx search "computer"

# Query with SQL-like syntax
arx query --sql "select * from equipment"
```

## Room Types

Common room types used in examples:
- `lobby` - Main entrance areas
- `office` - Individual offices
- `workspace` - Open office areas
- `conference` - Meeting rooms
- `meeting` - Smaller meeting spaces
- `kitchen` - Break rooms, pantries
- `mechanical` - HVAC, electrical rooms
- `security` - Security offices
- `apartment` - Residential units
- `parking` - Parking areas
- `utility` - Utility rooms

## Equipment Types

Common equipment types:
- `computer` - Workstations, servers
- `monitor` - Displays, screens
- `printer` - Printers, copiers
- `phone` - Desk phones, intercoms
- `hvac` - Heating, cooling systems
- `lighting` - Light fixtures, controls
- `security_camera` - Surveillance cameras
- `access_control` - Card readers, gates
- `appliance` - Kitchen appliances
- `exercise` - Gym equipment
- `safety` - Smoke detectors, alarms