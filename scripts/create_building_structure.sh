#!/bin/bash
# Create directory structure for a building following ArxOS universal addressing

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <building-uuid> [base-dir]"
    echo "Example: $0 ARXOS-NA-US-NY-NYC-0001"
    echo "Example: $0 ARXOS-NA-US-NY-NYC-0001 /opt/buildings"
    exit 1
fi

UUID="$1"
BASE_DIR="${2:-./buildings}"

# Validate UUID format
if ! echo "$UUID" | grep -qE '^ARXOS-[A-Z]{2}-[A-Z]{2}-[A-Z0-9]{2,3}-[A-Z]{3,4}-[0-9]{4}$'; then
    echo "Error: Invalid UUID format. Expected: ARXOS-CONTINENT-COUNTRY-STATE-CITY-SEQUENCE"
    echo "Example: ARXOS-NA-US-NY-NYC-0001"
    exit 1
fi

BUILDING_DIR="$BASE_DIR/$UUID"

echo "Creating building structure for $UUID..."
echo "Base directory: $BUILDING_DIR"

# Create base building directory
mkdir -p "$BUILDING_DIR"

# Define wings
WINGS="N S E W C"

# Define floors
FLOORS="B2 B1 G 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 R"

# Define zones (3x3 grid)
ZONES="A B C D E F G H I"

# Create directory structure
for wing in $WINGS; do
    echo "Creating wing $wing..."
    for floor in $FLOORS; do
        for zone in $ZONES; do
            mkdir -p "$BUILDING_DIR/$wing/$floor/$zone"
        done
    done
done

# Create building.bim.txt
cat > "$BUILDING_DIR/building.bim.txt" << EOF
BUILDING: New Building
UUID: $UUID
VERSION: 2.0
CREATED: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
AUTHOR: Building Structure Generator

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

EQUIPMENT:
  # Add equipment entries here
EOF

# Create README.md
cat > "$BUILDING_DIR/README.md" << EOF
# Building: $UUID

## Structure

This building follows the ArxOS Universal Addressing Specification.

### Path Format
\`\`\`
$UUID/[WING]/[FLOOR]/[ZONE]/[ROOM]/[WALL]/[EQUIPMENT]
\`\`\`

### Wings
- N: North Wing
- S: South Wing
- E: East Wing
- W: West Wing
- C: Central Core

### Floors
- B2, B1: Basement levels
- G: Ground floor
- 1-20: Above ground floors
- R: Roof

### Zones
3x3 grid pattern:
\`\`\`
A B C (North)
D E F (Middle)
G H I (South)
\`\`\`

## Quick Commands

### Navigate to equipment
\`\`\`bash
cd $UUID/N/3/A/301/E
\`\`\`

### Find all failed equipment
\`\`\`bash
grep -r "STATUS: FAILED" --include="*.txt"
\`\`\`

### Track changes
\`\`\`bash
git add .
git commit -m "Updated equipment status"
\`\`\`
EOF

# Initialize git repository
cd "$BUILDING_DIR"
git init
echo "*.log" > .gitignore
echo "*.tmp" >> .gitignore
echo ".DS_Store" >> .gitignore

git add .
git commit -m "Initial building structure for $UUID"

echo ""
echo "✅ Building structure created successfully!"
echo ""
echo "Directory: $BUILDING_DIR"
echo "Total directories created: $(find "$BUILDING_DIR" -type d | wc -l)"
echo ""
echo "Next steps:"
echo "1. cd $BUILDING_DIR"
echo "2. Add equipment files to appropriate directories"
echo "3. Track changes with git"
echo ""
echo "Example - Add an outlet:"
echo "  echo 'STATUS: OPERATIONAL' > N/3/A/301/E/ELEC_OUTLET_01.txt"
echo "  git add N/3/A/301/E/ELEC_OUTLET_01.txt"
echo "  git commit -m 'Added outlet to room 301'"