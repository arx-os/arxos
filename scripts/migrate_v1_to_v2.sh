#!/bin/bash
# Migrate BIM v1.0 files to v2.0 with universal addressing

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <input-v1-file> <building-uuid>"
    echo "Example: $0 school.bim.txt ARXOS-NA-US-CA-LAX-0001"
    exit 1
fi

INPUT_FILE="$1"
UUID="$2"
OUTPUT_FILE="${INPUT_FILE%.bim.txt}_v2.bim.txt"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

# Validate UUID format
if ! echo "$UUID" | grep -qE '^ARXOS-[A-Z]{2}-[A-Z]{2}-[A-Z0-9]{2,3}-[A-Z]{3,4}-[0-9]{4}$'; then
    echo "Error: Invalid UUID format. Expected: ARXOS-CONTINENT-COUNTRY-STATE-CITY-SEQUENCE"
    echo "Example: ARXOS-NA-US-NY-NYC-0001"
    exit 1
fi

echo "Migrating $INPUT_FILE to v2.0 format..."

# Start with v2.0 header
cat > "$OUTPUT_FILE" << EOF
BUILDING: $(grep '^BUILDING:' "$INPUT_FILE" | cut -d: -f2- | xargs)
UUID: $UUID
VERSION: 2.0
CREATED: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
AUTHOR: Migration Script

ADDRESS_SCHEME: UNIVERSAL_V1
BASE_PATH: $UUID/<WING>/<FLOOR>/<ZONE>/<ROOM>/<WALL>/<EQUIPMENT>

STRUCTURE:
  WINGS:
    N: North Wing
    S: South Wing
    E: East Wing
    W: West Wing
    C: Central Core

  FLOORS:
    B2: Basement Level 2
    B1: Basement Level 1
    G:  Ground Floor
    1-20: Above ground floors
    R:  Roof

  ZONES: 3x3_GRID
    A B C  (North)
    D E F  (Middle)
    G H I  (South)

EOF

# Process equipment, adding PATH field
echo "EQUIPMENT:" >> "$OUTPUT_FILE"

# Track if we're in an equipment block
in_equipment=false
equipment_id=""
floor="1"
wing="N"
zone="A"
room="101"

while IFS= read -r line; do
    # Skip the old header
    if [[ "$line" =~ ^BUILDING: ]] || [[ "$line" =~ ^CREATED: ]]; then
        continue
    fi

    # Check for floor/wing declarations
    if [[ "$line" =~ ^FLOOR:\ ([0-9BG]+) ]]; then
        floor="${BASH_REMATCH[1]}"
        continue
    fi

    if [[ "$line" =~ ^WING:\ ([NSEWC]+) ]]; then
        wing="${BASH_REMATCH[1]}"
        continue
    fi

    # Process equipment entries
    if [[ "$line" =~ ^ID:\ (.+) ]]; then
        equipment_id="${BASH_REMATCH[1]}"
        echo "  ID: $equipment_id" >> "$OUTPUT_FILE"

        # Generate a default PATH based on equipment type
        if [[ "$equipment_id" =~ OUTLET ]]; then
            echo "  PATH: $wing/$floor/$zone/$room/E" >> "$OUTPUT_FILE"
        elif [[ "$equipment_id" =~ SWITCH|NETWORK ]]; then
            echo "  PATH: $wing/$floor/$zone/$room/N" >> "$OUTPUT_FILE"
        elif [[ "$equipment_id" =~ THERMOSTAT|HVAC ]]; then
            echo "  PATH: $wing/$floor/$zone/$room/W" >> "$OUTPUT_FILE"
        else
            echo "  PATH: $wing/$floor/$zone/$room/C" >> "$OUTPUT_FILE"
        fi

        # Increment room number for next equipment
        room=$((room + 1))
        if [ $room -gt 109 ]; then
            room=101
            # Move to next zone
            case $zone in
                A) zone=B ;;
                B) zone=C ;;
                C) zone=D ;;
                D) zone=E ;;
                E) zone=F ;;
                F) zone=G ;;
                G) zone=H ;;
                H) zone=I ;;
                I) zone=A ;;
            esac
        fi
    elif [[ "$line" =~ ^[[:space:]]+(.+):\ (.+) ]]; then
        # Equipment properties
        echo "$line" >> "$OUTPUT_FILE"
    elif [[ ! -z "$line" ]] && [[ ! "$line" =~ ^EQUIPMENT_REGISTRY: ]]; then
        echo "$line" >> "$OUTPUT_FILE"
    fi
done < "$INPUT_FILE"

echo "Migration complete: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "1. Review the generated PATH fields and adjust as needed"
echo "2. Create directory structure: ./create_building_structure.sh $UUID"
echo "3. Validate: bim validate $OUTPUT_FILE"