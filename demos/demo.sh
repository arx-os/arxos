#!/bin/bash

# ArxOS Demo Script
# Demonstrates the key features of the ArxOS Building Management System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

function print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

function wait_for_enter() {
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
}

function demo_command() {
    echo -e "${BLUE}$ $1${NC}"
    sleep 0.5
    eval "$1"
    echo
}

# Check if arx is installed
if ! command -v arx &> /dev/null; then
    echo -e "${RED}Error: 'arx' command not found. Please build and install ArxOS first.${NC}"
    echo "Run: go build -o arx ./cmd/arx && sudo mv arx /usr/local/bin/"
    exit 1
fi

# Demo starts here
clear
echo -e "${GREEN}"
echo "    _____                  ________    _________"
echo "   /  _  \\_______ ___  ___\\_____  \\  /   _____/"
echo "  /  /_\\  \\_  __ \\\\  \\/  / /   |   \\ \\_____  \\ "
echo " /    |    \\|  | \\/ >    < /    |    \\/        \\"
echo " \\____|__  /|__|   /__/\\_ \\\\____|__  /_______  /"
echo "         \\/               \\/         \\/        \\/ "
echo -e "${NC}"
echo -e "${BLUE}Building Information Management System${NC}"
echo -e "${YELLOW}Version 1.0.0${NC}\n"

print_header "Welcome to the ArxOS Demo!"
echo "This demo will walk you through the key features of ArxOS:"
echo "  • System installation and setup"
echo "  • Building repository management"
echo "  • Equipment and room tracking"
echo "  • Query and search capabilities"
echo "  • Git-like version control for buildings"
wait_for_enter

# Step 1: System Installation
print_header "Step 1: System Installation"
print_step "First, let's check if ArxOS is installed..."
demo_command "arx status"

if [ ! -d "$HOME/.arxos" ]; then
    print_step "Installing ArxOS system components..."
    demo_command "arx install"
fi

wait_for_enter

# Step 2: Initialize a Building Repository
print_header "Step 2: Initialize a Building Repository"
print_step "Creating a new building repository for our office complex..."

# Create a temporary directory for the demo
DEMO_DIR="/tmp/arxos-demo-$$"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

demo_command "arx repo init ARXOS-NA-US-CA-SFO-0001 --name 'Tech Office Complex'"
demo_command "cd $HOME/.arxos/buildings/ARXOS-NA-US-CA-SFO-0001"
cd "$HOME/.arxos/buildings/ARXOS-NA-US-CA-SFO-0001"

wait_for_enter

# Step 3: Import Building Data
print_header "Step 3: Define Building Structure"
print_step "Let's copy our pre-built office building definition..."

# Get the demos directory path
DEMOS_DIR="$(dirname $(dirname $(which arx)))/repos/arxos/demos"
if [ ! -f "$DEMOS_DIR/office_building.bim.txt" ]; then
    DEMOS_DIR="/Users/joelpate/repos/arxos/demos"
fi

if [ -f "$DEMOS_DIR/office_building.bim.txt" ]; then
    cp "$DEMOS_DIR/office_building.bim.txt" building.bim.txt
    echo "Copied building definition from demos directory"
else
    echo -e "${YELLOW}Demo file not found, creating basic structure...${NC}"
    cat > building.bim.txt << 'EOF'
# ArxOS Building Information Model
# Building: Demo Office
# ArxOS ID: ARXOS-NA-US-CA-SFO-0001

## FLOORS
FLOOR 1 "Ground Floor" 0.0
FLOOR 2 "Second Floor" 4.0

## ROOMS
ROOM 1/101 "Lobby" lobby 100.0
ROOM 1/102 "Server Room" datacenter 50.0
ROOM 2/201 "Office Space" office 200.0
ROOM 2/202 "Conference Room" conference 50.0

## EQUIPMENT
EQUIPMENT 1/101/HVAC_01 "Main HVAC" hvac operational
EQUIPMENT 1/102/RACK_01 "Server Rack" server operational
EQUIPMENT 2/201/COMP_01 "Workstation 1" computer operational
EQUIPMENT 2/201/COMP_02 "Workstation 2" computer offline
EOF
fi

print_step "Viewing building structure..."
demo_command "head -20 building.bim.txt"

wait_for_enter

# Step 4: Commit Changes
print_header "Step 4: Version Control"
print_step "ArxOS uses Git-like version control for building changes..."

demo_command "arx repo status"
demo_command "arx repo commit -m 'Initial building configuration'"
demo_command "arx repo log"

wait_for_enter

# Step 5: Query Building Data
print_header "Step 5: Query Building Data"
print_step "Now let's explore various ways to query our building..."

echo -e "${YELLOW}List all equipment:${NC}"
demo_command "arx list equipment"

echo -e "${YELLOW}Query by floor:${NC}"
demo_command "arx query --floor 1"

echo -e "${YELLOW}Find all computers:${NC}"
demo_command "arx query --type computer"

echo -e "${YELLOW}Check offline equipment:${NC}"
demo_command "arx query --status offline"

if grep -q "CRITICAL" building.bim.txt; then
    echo -e "${YELLOW}Show critical systems:${NC}"
    demo_command "arx query --critical"
fi

wait_for_enter

# Step 6: Modify Building
print_header "Step 6: Making Changes"
print_step "Let's add new equipment to the building..."

demo_command "arx add equipment 2/201/PRINT_01 'Network Printer' printer operational"
demo_command "arx add room 2/203 'Storage Room' storage 30.0"

print_step "View the changes..."
demo_command "arx repo status"
demo_command "arx repo diff | head -30"

print_step "Commit the changes..."
demo_command "arx repo commit -m 'Added printer and storage room'"

wait_for_enter

# Step 7: Search Capabilities
print_header "Step 7: Advanced Search"
print_step "ArxOS provides powerful search capabilities..."

demo_command "arx search server"
demo_command "arx search -f 2"
demo_command "arx get equipment 1/102/RACK_01"

wait_for_enter

# Step 8: Maintenance Tracking
print_header "Step 8: Equipment Status Updates"
print_step "Update equipment status for maintenance..."

if grep -q "COMP_02" building.bim.txt; then
    # Find an operational equipment to mark for maintenance
    EQUIP_ID=$(grep "EQUIPMENT.*operational" building.bim.txt | head -1 | awk '{print $2}')
    if [ ! -z "$EQUIP_ID" ]; then
        echo -e "${YELLOW}Marking $EQUIP_ID for maintenance:${NC}"
        # This would update the status in the BIM file
        sed -i.bak "s|$EQUIP_ID \\(.*\\) operational|$EQUIP_ID \\1 maintenance|" building.bim.txt
        demo_command "arx repo diff | grep maintenance"
        demo_command "arx repo commit -m 'Equipment scheduled for maintenance'"
    fi
fi

wait_for_enter

# Step 9: Export and Reports
print_header "Step 9: Building Summary"
print_step "Generate a building summary report..."

echo -e "${YELLOW}Building Statistics:${NC}"
echo "Floors: $(grep -c '^FLOOR' building.bim.txt)"
echo "Rooms: $(grep -c '^ROOM' building.bim.txt)"
echo "Equipment: $(grep -c '^EQUIPMENT' building.bim.txt)"
echo "Critical Systems: $(grep -c '^CRITICAL' building.bim.txt 2>/dev/null || echo 0)"
echo
echo -e "${YELLOW}Equipment by Status:${NC}"
echo "Operational: $(grep -c 'operational$' building.bim.txt)"
echo "Maintenance: $(grep -c 'maintenance$' building.bim.txt)"
echo "Offline: $(grep -c 'offline$' building.bim.txt)"

wait_for_enter

# Cleanup
print_header "Demo Complete!"
echo "Thank you for exploring ArxOS!"
echo ""
echo "Key features demonstrated:"
echo "  ✅ System installation and setup"
echo "  ✅ Git-like version control for buildings"
echo "  ✅ BIM file format for building definitions"
echo "  ✅ Query and search capabilities"
echo "  ✅ Equipment and room management"
echo "  ✅ Status tracking and maintenance"
echo ""
echo "Your demo building repository is located at:"
echo "  $HOME/.arxos/buildings/ARXOS-NA-US-CA-SFO-0001"
echo ""
echo "To continue exploring:"
echo "  • View the building file: cat building.bim.txt"
echo "  • See commit history: arx repo log"
echo "  • Query equipment: arx query --help"
echo "  • Explore the API: arx serve (starts on port 8080)"
echo ""
echo -e "${GREEN}Visit https://github.com/arx-os/arxos for more information${NC}"

# Clean up temp dir
rm -rf "$DEMO_DIR"