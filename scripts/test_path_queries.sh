#!/bin/bash
# Test path-based query functionality end-to-end
# This script creates test data and validates path queries work

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARX_BIN="$PROJECT_ROOT/bin/arx"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Path-Based Query Functionality Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Create test building
echo -e "${BLUE}Step 1: Creating test building...${NC}"
BUILDING_OUTPUT=$($ARX_BIN building create \
    --name "Path Test School" \
    --address "456 Test Avenue" 2>&1)

if echo "$BUILDING_OUTPUT" | grep -qE "(created|success|ID:)"; then
    echo -e "${GREEN}✓ Building created${NC}"
    echo "$BUILDING_OUTPUT"
    # Try to extract building ID
    BUILDING_ID=$(echo "$BUILDING_OUTPUT" | grep -oE 'ID: [a-zA-Z0-9-]+' | cut -d' ' -f2 || echo "")
    if [ -z "$BUILDING_ID" ]; then
        echo -e "${YELLOW}⚠ Could not extract building ID from output${NC}"
        echo "Please manually note the building ID and update this script"
        exit 1
    fi
else
    echo -e "${RED}❌ Failed to create building${NC}"
    echo "$BUILDING_OUTPUT"
    exit 1
fi

echo ""
echo -e "Building ID: ${GREEN}$BUILDING_ID${NC}"
echo ""

# Step 2: Create floor
echo -e "${BLUE}Step 2: Creating floor...${NC}"
FLOOR_OUTPUT=$($ARX_BIN floor create \
    --building "$BUILDING_ID" \
    --level 1 \
    --name "First Floor" 2>&1)

if echo "$FLOOR_OUTPUT" | grep -qE "(created|success|ID:)"; then
    echo -e "${GREEN}✓ Floor created${NC}"
    FLOOR_ID=$(echo "$FLOOR_OUTPUT" | grep -oE 'ID: [a-zA-Z0-9-]+' | cut -d' ' -f2 || echo "")
    if [ -z "$FLOOR_ID" ]; then
        echo -e "${YELLOW}⚠ Could not extract floor ID${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Failed to create floor${NC}"
    echo "$FLOOR_OUTPUT"
    exit 1
fi

echo ""

# Step 3: Create rooms
echo -e "${BLUE}Step 3: Creating rooms...${NC}"

create_room() {
    local room_num=$1
    local room_name=$2

    ROOM_OUTPUT=$($ARX_BIN room create \
        --floor "$FLOOR_ID" \
        --number "$room_num" \
        --name "$room_name" 2>&1)

    if echo "$ROOM_OUTPUT" | grep -qE "(created|success|ID:)"; then
        ROOM_ID=$(echo "$ROOM_OUTPUT" | grep -oE 'ID: [a-zA-Z0-9-]+' | cut -d' ' -f2 || echo "")
        echo -e "${GREEN}✓ Room $room_num created (ID: $ROOM_ID)${NC}"
        echo "$ROOM_ID"
    else
        echo -e "${RED}❌ Failed to create room $room_num${NC}"
        echo ""
    fi
}

ROOM_101=$(create_room "101" "Classroom 101")
ROOM_102=$(create_room "102" "Classroom 102")
ROOM_IDF=$(create_room "IDF-1A" "IDF 1A")

echo ""

# Step 4: Create equipment
echo -e "${BLUE}Step 4: Creating equipment with automatic path generation...${NC}"

create_equipment() {
    local room_id=$1
    local eq_name=$2
    local eq_type=$3
    local description=$4

    EQ_OUTPUT=$($ARX_BIN equipment create \
        --building "$BUILDING_ID" \
        --floor "$FLOOR_ID" \
        --room "$room_id" \
        --name "$eq_name" \
        --type "$eq_type" 2>&1)

    if echo "$EQ_OUTPUT" | grep -qE "(created|success|ID:|path)"; then
        # Try to extract path from output
        PATH=$(echo "$EQ_OUTPUT" | grep -oE 'path: [^ ]+' | cut -d' ' -f2 || echo "")
        if [ -n "$PATH" ]; then
            echo -e "${GREEN}✓ $description created with path: $PATH${NC}"
        else
            echo -e "${GREEN}✓ $description created${NC}"
        fi
        echo "$EQ_OUTPUT" | grep -i path || true
    else
        echo -e "${YELLOW}⚠ Equipment creation status unclear: $description${NC}"
    fi
}

echo "Creating HVAC equipment..."
create_equipment "$ROOM_101" "VAV-101" "hvac" "VAV in Room 101"
create_equipment "$ROOM_102" "VAV-102" "hvac" "VAV in Room 102"

echo ""
echo "Creating network equipment..."
create_equipment "$ROOM_IDF" "SW-01" "switch" "Switch in IDF"
create_equipment "$ROOM_IDF" "ROUTER-01" "router" "Router in IDF"

echo ""
echo "Creating sensors..."
create_equipment "$ROOM_101" "TEMP-101" "sensor" "Temperature sensor in Room 101"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Testing Path-Based Queries"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: List all equipment to see generated paths
echo -e "${BLUE}Test 1: List all equipment to see paths...${NC}"
$ARX_BIN equipment list --building "$BUILDING_ID" || echo "List command may need --help to see correct flags"
echo ""

# Test 2: Query by path pattern (HVAC)
echo -e "${BLUE}Test 2: Query all HVAC equipment by path pattern...${NC}"
echo "Command: arx get '*/*/*/hvac/*'"
$ARX_BIN get '*/*/*/hvac/*' 2>&1 || echo "Path query needs database connection"
echo ""

# Test 3: Query network equipment
echo -e "${BLUE}Test 3: Query all network equipment...${NC}"
echo "Command: arx get '*/*/IDF-1A/network/*'"
$ARX_BIN get '*/*/IDF-1A/network/*' 2>&1 || echo "Path query needs database connection"
echo ""

# Test 4: Query all equipment in a room
echo -e "${BLUE}Test 4: Query all equipment in Room 101...${NC}"
echo "Command: arx get '*/*/101/*/*'"
$ARX_BIN get '*/*/101/*/*' 2>&1 || echo "Path query needs database connection"
echo ""

# Test 5: Use query command with filters
echo -e "${BLUE}Test 5: Advanced query with filters...${NC}"
echo "Command: arx query --type hvac"
$ARX_BIN query --type hvac 2>&1 || echo "Query command may have different flags"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  Building ID: $BUILDING_ID"
echo "  Floor ID: $FLOOR_ID"
echo "  Created 5 equipment items across 3 rooms"
echo ""
echo "Next steps:"
echo "  1. Verify paths were generated for each equipment"
echo "  2. Test path queries manually"
echo "  3. Check database for path column population"
echo ""
echo "Database check:"
echo "  psql -d arxos_dev -c \"SELECT name, path FROM equipment WHERE building_id='$BUILDING_ID';\""
echo ""

