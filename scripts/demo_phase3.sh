#!/bin/bash
# ArxOS Phase 3 Demo Script
# Demonstrates complete hierarchical building management:
# Building -> Floor -> Room -> Equipment

set -e

echo "════════════════════════════════════════════════════════"
echo "  ArxOS Phase 3 - Hierarchical Building Management Demo"
echo "════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if arx binary exists
if [ ! -f "./bin/arx" ]; then
    echo "Building ArxOS..."
    go build -o bin/arx ./cmd/arx/
    echo ""
fi

# Step 1: Create a building
echo -e "${BLUE}Step 1: Creating a building${NC}"
echo "Command: arx building create --name 'Demo HQ' --address '100 Innovation Way, San Francisco, CA' --lat 37.7749 --lon -122.4194"
echo ""

BUILDING_OUTPUT=$(./bin/arx building create \
    --name "Demo HQ" \
    --address "100 Innovation Way, San Francisco, CA" \
    --lat 37.7749 \
    --lon -122.4194 2>&1)

echo "$BUILDING_OUTPUT"
echo ""

# Extract building ID from output (assuming format: "ID:      <id>")
BUILDING_ID=$(echo "$BUILDING_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')

if [ -z "$BUILDING_ID" ]; then
    echo "Failed to extract building ID. Exiting."
    exit 1
fi

echo -e "${GREEN}✓ Building created with ID: $BUILDING_ID${NC}"
echo ""
sleep 1

# Step 2: Create floors
echo -e "${BLUE}Step 2: Creating floors in the building${NC}"
echo ""

echo "Creating Ground Floor (Level 0)..."
FLOOR1_OUTPUT=$(./bin/arx floor create \
    --building "$BUILDING_ID" \
    --name "Ground Floor" \
    --level 0 2>&1)
FLOOR1_ID=$(echo "$FLOOR1_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')
echo -e "${GREEN}✓ Ground Floor created: $FLOOR1_ID${NC}"
echo ""

echo "Creating First Floor (Level 1)..."
FLOOR2_OUTPUT=$(./bin/arx floor create \
    --building "$BUILDING_ID" \
    --name "First Floor" \
    --level 1 2>&1)
FLOOR2_ID=$(echo "$FLOOR2_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')
echo -e "${GREEN}✓ First Floor created: $FLOOR2_ID${NC}"
echo ""

echo "Creating Second Floor (Level 2)..."
FLOOR3_OUTPUT=$(./bin/arx floor create \
    --building "$BUILDING_ID" \
    --name "Second Floor" \
    --level 2 2>&1)
FLOOR3_ID=$(echo "$FLOOR3_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')
echo -e "${GREEN}✓ Second Floor created: $FLOOR3_ID${NC}"
echo ""
sleep 1

# Step 3: List floors
echo -e "${BLUE}Step 3: Listing all floors in the building${NC}"
echo "Command: arx floor list --building $BUILDING_ID"
echo ""

./bin/arx floor list --building "$BUILDING_ID" 2>&1
echo ""
sleep 1

# Step 4: Create equipment on different floors
echo -e "${BLUE}Step 4: Creating equipment on different floors${NC}"
echo ""

echo "Creating HVAC Unit on Ground Floor..."
HVAC1_OUTPUT=$(./bin/arx equipment create \
    --name "HVAC-GF-01" \
    --type hvac \
    --model "Carrier 58MCA" \
    --building "$BUILDING_ID" \
    --floor "$FLOOR1_ID" \
    --x 10.5 --y 20.3 --z 3.0 2>&1)
HVAC1_ID=$(echo "$HVAC1_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')
echo -e "${GREEN}✓ HVAC Unit created: $HVAC1_ID${NC}"
echo ""

echo "Creating Lighting System on First Floor..."
LIGHT1_OUTPUT=$(./bin/arx equipment create \
    --name "Lights-F1-A" \
    --type lighting \
    --model "Philips Hue Pro" \
    --building "$BUILDING_ID" \
    --floor "$FLOOR2_ID" \
    --x 15.0 --y 25.0 --z 3.0 2>&1)
LIGHT1_ID=$(echo "$LIGHT1_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')
echo -e "${GREEN}✓ Lighting System created: $LIGHT1_ID${NC}"
echo ""

echo "Creating Security System on Second Floor..."
SECURITY1_OUTPUT=$(./bin/arx equipment create \
    --name "Security-F2-Main" \
    --type security \
    --model "Honeywell Vista" \
    --building "$BUILDING_ID" \
    --floor "$FLOOR3_ID" 2>&1)
SECURITY1_ID=$(echo "$SECURITY1_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')
echo -e "${GREEN}✓ Security System created: $SECURITY1_ID${NC}"
echo ""
sleep 1

# Step 5: List all equipment
echo -e "${BLUE}Step 5: Listing all equipment${NC}"
echo "Command: arx equipment list"
echo ""

./bin/arx equipment list 2>&1
echo ""
sleep 1

# Step 6: Filter equipment by building
echo -e "${BLUE}Step 6: Filtering equipment by building${NC}"
echo "Command: arx equipment list --building $BUILDING_ID"
echo ""

./bin/arx equipment list --building "$BUILDING_ID" 2>&1
echo ""
sleep 1

# Step 7: Filter equipment by type
echo -e "${BLUE}Step 7: Filtering equipment by type${NC}"
echo "Command: arx equipment list --type hvac"
echo ""

./bin/arx equipment list --type hvac 2>&1
echo ""
sleep 1

# Step 8: Get equipment details
echo -e "${BLUE}Step 8: Getting equipment details${NC}"
echo "Command: arx equipment get $HVAC1_ID"
echo ""

./bin/arx equipment get "$HVAC1_ID" 2>&1
echo ""
sleep 1

# Step 9: Update equipment status
echo -e "${BLUE}Step 9: Updating equipment status${NC}"
echo "Command: arx equipment update $HVAC1_ID --status maintenance"
echo ""

./bin/arx equipment update "$HVAC1_ID" --status maintenance 2>&1
echo ""
sleep 1

# Step 10: Get building with hierarchy
echo -e "${BLUE}Step 10: Getting complete building details${NC}"
echo "Command: arx building get $BUILDING_ID"
echo ""

./bin/arx building get "$BUILDING_ID" 2>&1
echo ""
sleep 1

# Step 11: Get floor details
echo -e "${BLUE}Step 11: Getting floor details${NC}"
echo "Command: arx floor get $FLOOR2_ID"
echo ""

./bin/arx floor get "$FLOOR2_ID" 2>&1
echo ""

echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✓ Phase 3 Demo Complete!${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Summary of what was created:"
echo "  • 1 Building: Demo HQ"
echo "  • 3 Floors: Ground, First, Second"
echo "  • 3 Equipment items: HVAC, Lighting, Security"
echo ""
echo "All data is persisted in PostgreSQL with PostGIS spatial features."
echo "Try exploring with: arx building list, arx equipment list, arx floor list"
echo ""

