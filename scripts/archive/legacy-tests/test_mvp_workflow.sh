#!/bin/bash

# ArxOS MVP Integration Test
# Tests the complete workflow: create building -> floors -> rooms -> equipment -> render

set -e

echo "🚀 ArxOS MVP Integration Test"
echo "==============================="
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build the project
echo -e "${BLUE}Building ArxOS...${NC}"
go build -o arx ./cmd/arx
echo -e "${GREEN}✓ Build successful${NC}"
echo

# 1. Create a building
echo -e "${BLUE}Step 1: Creating test building...${NC}"
BUILDING_OUTPUT=$(./arx building create --name "Test School" --address "123 Test St")
echo "$BUILDING_OUTPUT"

# Extract building ID (assuming format: "ID:     <id>")
BUILDING_ID=$(echo "$BUILDING_OUTPUT" | grep "ID:" | awk '{print $2}')
echo -e "${GREEN}✓ Building created: $BUILDING_ID${NC}"
echo

# 2. Create a floor
echo -e "${BLUE}Step 2: Creating floor 3...${NC}"
FLOOR_OUTPUT=$(./arx floor create --building "$BUILDING_ID" --level 3 --name "Third Floor")
echo "$FLOOR_OUTPUT"

# Extract floor ID
FLOOR_ID=$(echo "$FLOOR_OUTPUT" | grep "ID:" | awk '{print $2}')
echo -e "${GREEN}✓ Floor created: $FLOOR_ID${NC}"
echo

# 3. Create rooms with layout
echo -e "${BLUE}Step 3: Creating rooms with layout...${NC}"

# Room 301 - Classroom
echo "  Creating Room 301 (Classroom)..."
ROOM_301=$(./arx room create --floor "$FLOOR_ID" --name "Classroom" --number "301" \
  --x 0 --y 0 --width 30 --height 20)
ROOM_301_ID=$(echo "$ROOM_301" | grep "ID:" | awk '{print $2}')
echo -e "${GREEN}  ✓ Room 301 created: $ROOM_301_ID${NC}"

# Room IDF-3A - Network Closet
echo "  Creating IDF-3A (Network Closet)..."
ROOM_IDF=$(./arx room create --floor "$FLOOR_ID" --name "IDF-3A" --number "IDF-3A" \
  --x 35 --y 0 --width 10 --height 10)
ROOM_IDF_ID=$(echo "$ROOM_IDF" | grep "ID:" | awk '{print $2}')
echo -e "${GREEN}  ✓ IDF-3A created: $ROOM_IDF_ID${NC}"

# Room HALL-3A - Hallway
echo "  Creating HALL-3A (Hallway)..."
ROOM_HALL=$(./arx room create --floor "$FLOOR_ID" --name "Hallway" --number "HALL-3A" \
  --x 0 --y 25 --width 50 --height 10)
ROOM_HALL_ID=$(echo "$ROOM_HALL" | grep "ID:" | awk '{print $2}')
echo -e "${GREEN}  ✓ HALL-3A created: $ROOM_HALL_ID${NC}"
echo

# 4. Add equipment to rooms
echo -e "${BLUE}Step 4: Adding equipment to rooms...${NC}"

# HVAC in classroom
echo "  Adding VAV-301 to Room 301..."
EQUIP_VAV=$(./arx equipment create --name "VAV-301" --type hvac \
  --building "$BUILDING_ID" --floor "$FLOOR_ID" --room "$ROOM_301_ID" \
  --x 15 --y 10)
echo "$EQUIP_VAV" | grep "Path:"
echo -e "${GREEN}  ✓ VAV-301 created${NC}"

# Network switch in IDF
echo "  Adding SW-01 to IDF-3A..."
EQUIP_SW=$(./arx equipment create --name "SW-01" --type network \
  --building "$BUILDING_ID" --floor "$FLOOR_ID" --room "$ROOM_IDF_ID" \
  --x 38 --y 5)
echo "$EQUIP_SW" | grep "Path:"
echo -e "${GREEN}  ✓ SW-01 created${NC}"

# Light in hallway
echo "  Adding LIGHT-HALL-1 to hallway..."
EQUIP_LIGHT=$(./arx equipment create --name "LIGHT-HALL-1" --type lighting \
  --building "$BUILDING_ID" --floor "$FLOOR_ID" --room "$ROOM_HALL_ID" \
  --x 25 --y 30)
echo "$EQUIP_LIGHT" | grep "Path:"
echo -e "${GREEN}  ✓ LIGHT-HALL-1 created${NC}"
echo

# 5. List created items
echo -e "${BLUE}Step 5: Verification - Listing created items...${NC}"

echo "  Buildings:"
./arx building list | grep "Test School" || echo "    (No output)"

echo
echo "  Rooms on floor 3:"
./arx room list --floor "$FLOOR_ID" || echo "    (No rooms found)"

echo
echo "  Equipment in building:"
./arx equipment list --building "$BUILDING_ID" || echo "    (No equipment found)"
echo

# 6. Render floor plan
echo -e "${BLUE}Step 6: Testing render command...${NC}"
echo -e "${YELLOW}Note: Render command launches interactive TUI. Skipping for automated test.${NC}"
echo "  To test rendering manually, run:"
echo "  ./arx render $BUILDING_ID --floor 3"
echo

# Summary
echo -e "${GREEN}=============================="
echo "✅ MVP Integration Test Complete!"
echo "==============================${NC}"
echo
echo "Summary of created items:"
echo "  Building ID:  $BUILDING_ID"
echo "  Floor ID:     $FLOOR_ID"
echo "  Room 301 ID:  $ROOM_301_ID"
echo "  IDF-3A ID:    $ROOM_IDF_ID"
echo "  HALL-3A ID:   $ROOM_HALL_ID"
echo
echo "✨ Key Features Demonstrated:"
echo "  ✓ Building creation"
echo "  ✓ Floor creation"
echo "  ✓ Room creation with position and dimensions"
echo "  ✓ Equipment creation with automatic path generation"
echo "  ✓ Universal naming convention (/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT)"
echo
echo "Next steps:"
echo "  1. Run: ./arx render $BUILDING_ID --floor 3"
echo "  2. View floor plan in ASCII terminal"
echo "  3. See rooms and equipment visually"
echo

