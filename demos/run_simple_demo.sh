#!/bin/bash

# Simple ArxOS Demo Runner
# This script demonstrates basic ArxOS functionality

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}ArxOS Simple Demo${NC}\n"

# Build the CLI if needed
if [ ! -f "/Users/joelpate/repos/arxos/arx" ]; then
    echo -e "${YELLOW}Building ArxOS CLI...${NC}"
    cd /Users/joelpate/repos/arxos
    go build -o arx ./cmd/arx
fi

# Use local arx binary
ARX="/Users/joelpate/repos/arxos/arx"

echo -e "${BLUE}1. Checking ArxOS status:${NC}"
$ARX status || true

echo -e "\n${BLUE}2. Installing ArxOS (if needed):${NC}"
if [ ! -d "$HOME/.arxos" ]; then
    $ARX install
else
    echo "ArxOS already installed"
fi

echo -e "\n${BLUE}3. Creating a demo building:${NC}"
DEMO_ID="ARXOS-NA-US-CA-TEST-$(date +%s)"
echo "Creating building: $DEMO_ID"
$ARX repo init $DEMO_ID --name "Demo Building" || true

echo -e "\n${BLUE}4. Setting up building structure:${NC}"
BUILDING_DIR="$HOME/.arxos/buildings/$DEMO_ID"
if [ -d "$BUILDING_DIR" ]; then
    cat > "$BUILDING_DIR/building.bim.txt" << 'EOF'
# ArxOS Demo Building
## FLOORS
FLOOR 1 "Ground Floor" 0.0
FLOOR 2 "Second Floor" 4.0

## ROOMS  
ROOM 1/101 "Lobby" lobby 100.0
ROOM 1/102 "Server Room" datacenter 50.0
ROOM 2/201 "Office" office 80.0

## EQUIPMENT
EQUIPMENT 1/102/RACK_01 "Server Rack" server operational
EQUIPMENT 2/201/COMP_01 "Workstation" computer operational
EOF
    echo "Building structure created"
    
    cd "$BUILDING_DIR"
    
    echo -e "\n${BLUE}5. Committing initial configuration:${NC}"
    $ARX repo commit -m "Initial building setup"
    
    echo -e "\n${BLUE}6. Querying building data:${NC}"
    echo "All equipment:"
    cd "$BUILDING_DIR" && $ARX list equipment

    echo -e "\nFloor 1 items:"
    cd "$BUILDING_DIR" && $ARX query --floor 1

    echo -e "\n${BLUE}7. Adding new equipment:${NC}"
    cd "$BUILDING_DIR" && $ARX add 2/201/PRINT_01 --name "Office Printer" --type printer --status operational

    echo -e "\n${BLUE}8. Viewing changes:${NC}"
    cd "$BUILDING_DIR" && $ARX repo status
    
    echo -e "\n${GREEN}Demo Complete!${NC}"
    echo "Building repository: $BUILDING_DIR"
else
    echo -e "${YELLOW}Failed to create building directory${NC}"
fi