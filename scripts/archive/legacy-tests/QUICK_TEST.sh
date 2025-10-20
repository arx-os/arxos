#!/bin/bash
# ArxOS MVP - Quick Manual Test
# Copy-paste these commands one at a time to see each step

echo "🚀 ArxOS MVP Quick Test"
echo "======================="
echo
echo "Step 1: Build ArxOS"
echo "-------------------"

cd /Users/joelpate/repos/arxos
go build -o arx ./cmd/arx

echo
echo "✅ Build complete! Testing database connection..."
echo

./arx health

echo
echo "📋 Copy-paste the following commands ONE AT A TIME"
echo "   Watch the output after each command!"
echo
echo "================================================================"
echo

cat << 'EOF'

# ============================================================
# STEP 2: Create Building
# ============================================================

./arx building create --name "Main School" --address "123 Main Street"

# 👆 COPY THE BUILDING ID FROM OUTPUT! (looks like: abc123def456...)
# Store it:

export BUILDING_ID="<paste-building-id-here>"


# ============================================================
# STEP 3: Create Floor
# ============================================================

./arx floor create --building $BUILDING_ID --level 3 --name "Third Floor"

# 👆 COPY THE FLOOR ID FROM OUTPUT!
# Store it:

export FLOOR_ID="<paste-floor-id-here>"


# ============================================================
# STEP 4: Create Rooms with Positions
# ============================================================

# Room 301 - Classroom (top-left corner)
./arx room create --floor $FLOOR_ID --name "Classroom" --number "301" \
  --x 0 --y 0 --width 30 --height 20

# 👆 COPY THE ROOM ID! Store it:
export ROOM_301_ID="<paste-room-id-here>"


# IDF-3A - Network Closet (top-right)
./arx room create --floor $FLOOR_ID --name "Network Closet" --number "IDF-3A" \
  --x 35 --y 0 --width 10 --height 10

# 👆 COPY THE ROOM ID! Store it:
export ROOM_IDF_ID="<paste-room-id-here>"


# HALL-3A - Hallway (bottom)
./arx room create --floor $FLOOR_ID --name "Hallway" --number "HALL-3A" \
  --x 0 --y 25 --width 50 --height 10

# 👆 COPY THE ROOM ID! Store it:
export ROOM_HALL_ID="<paste-room-id-here>"


# ============================================================
# STEP 5: Add Equipment - WATCH THE PATHS AUTO-GENERATE! 🎯
# ============================================================

# HVAC in classroom
./arx equipment create --name "VAV-301" --type hvac \
  --building $BUILDING_ID --floor $FLOOR_ID --room $ROOM_301_ID \
  --x 15 --y 10

# 👆 Look for: Path: /MAIN-SCHOOL/3/301/HVAC/VAV-301 🎯


# Network switch in IDF
./arx equipment create --name "SW-01" --type network \
  --building $BUILDING_ID --floor $FLOOR_ID --room $ROOM_IDF_ID \
  --x 38 --y 5

# 👆 Look for: Path: /MAIN-SCHOOL/3/IDF-3A/NETWORK/SW-01 🎯


# Light in hallway
./arx equipment create --name "LIGHT-HALL-1" --type lighting \
  --building $BUILDING_ID --floor $FLOOR_ID --room $ROOM_HALL_ID \
  --x 25 --y 30

# 👆 Look for: Path: /MAIN-SCHOOL/3/HALL-3A/LIGHTING/LIGHT-HALL-1 🎯


# ============================================================
# STEP 6: Verify What You Created
# ============================================================

# List all buildings
./arx building list

# List rooms on floor 3
./arx room list --floor $FLOOR_ID

# List equipment in building
./arx equipment list --building $BUILDING_ID


# ============================================================
# STEP 7: TEST ROOM MOVE/RESIZE 🎨
# ============================================================

# Move classroom to new position
./arx room move $ROOM_301_ID --x 5 --y 5

# Resize classroom
./arx room resize $ROOM_301_ID --width 35 --height 25


# ============================================================
# STEP 8: RENDER THE FLOOR PLAN! 🎨
# ============================================================

./arx render $BUILDING_ID --floor 3

# 👆 This launches the interactive TUI!
# Press 'q' to quit when done viewing


# ============================================================
# BONUS: Test Path Generation
# ============================================================

# Create more equipment to see different path formats

# Electrical panel (different system)
./arx equipment create --name "Panel-1A" --type electrical \
  --building $BUILDING_ID --floor $FLOOR_ID --room $ROOM_IDF_ID \
  --x 36 --y 2

# Expected path: /MAIN-SCHOOL/3/IDF-3A/ELEC/PANEL-1A


# Plumbing equipment
./arx equipment create --name "Water-Heater-1" --type plumbing \
  --building $BUILDING_ID --floor $FLOOR_ID --room $ROOM_IDF_ID \
  --x 40 --y 8

# Expected path: /MAIN-SCHOOL/3/IDF-3A/PLUMB/WATER-HEATER-1


# Render again to see all equipment
./arx render $BUILDING_ID --floor 3


# ============================================================
# CLEANUP (Optional)
# ============================================================

# Delete the test building (removes everything)
./arx building delete $BUILDING_ID --force

EOF

echo
echo "================================================================"
echo
echo "✨ Ready to test! Copy the commands above one at a time."
echo

