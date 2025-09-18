#!/bin/bash

# ArxOS Demo Script
# Demonstrates the key features of the ArxOS Building Management System with PostGIS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

function print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

function print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
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

# Check prerequisites
function check_prerequisites() {
    local missing=false

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        missing=true
    else
        echo -e "${GREEN}✓ Docker is installed${NC}"
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose is not installed${NC}"
        missing=true
    else
        echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    fi

    if [ ! -f "../arx" ]; then
        echo -e "${YELLOW}⚠ ArxOS binary not found, building...${NC}"
        (cd .. && go build -o arx ./cmd/arx)
    fi
    echo -e "${GREEN}✓ ArxOS binary is available${NC}"

    if $missing; then
        echo -e "\n${RED}Please install missing prerequisites before continuing.${NC}"
        exit 1
    fi
}

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
echo -e "${BLUE}Building Operating System with PostGIS Spatial Database${NC}"
echo -e "${YELLOW}Version 0.1.0${NC}\n"

print_header "Welcome to the ArxOS PostGIS Demo!"
echo "This demo will showcase:"
echo "  • PostGIS spatial database with millimeter precision"
echo "  • IFC file import and processing"
echo "  • Spatial queries for equipment and rooms"
echo "  • Multi-format export (BIM, CSV, JSON)"
echo "  • Daemon-based file watching"
echo "  • Docker deployment"
wait_for_enter

# Step 1: Prerequisites Check
print_header "Step 1: Checking Prerequisites"
check_prerequisites
wait_for_enter

# Step 2: Start PostGIS Database
print_header "Step 2: Starting PostGIS Spatial Database"
print_step "Starting PostGIS with Docker Compose..."

cd ..
if docker ps | grep -q arxos-postgis; then
    print_info "PostGIS is already running"
else
    demo_command "docker-compose up -d postgis"
    echo "Waiting for PostGIS to be ready..."
    sleep 5
fi

print_step "Verifying PostGIS connection..."
demo_command "../arx query --health"

wait_for_enter

# Step 3: Import IFC Sample
print_header "Step 3: Importing IFC Building Data"
print_step "We'll import a sample IFC file to demonstrate the spatial import capabilities..."

# Create sample IFC if it doesn't exist
if [ ! -f "../test_data/sample.ifc" ]; then
    mkdir -p ../test_data
    cat > ../test_data/sample.ifc << 'EOF'
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ArxOS Demo Building'),'2;1');
FILE_NAME('demo.ifc','2024-01-01T00:00:00',(),(),'ArxOS','ArxOS Demo','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('1234567890123456',$,'Demo Project',$,$,$,$,$,$);
#2=IFCBUILDING('2345678901234567',$,'Tech Office Building',$,$,#10,$,$,.ELEMENT.,$,$,$);
#3=IFCBUILDINGSTOREY('3456789012345678',$,'Ground Floor',$,$,#11,$,$,.ELEMENT.,0.);
#4=IFCBUILDINGSTOREY('4567890123456789',$,'First Floor',$,$,#12,$,$,.ELEMENT.,3500.);
#5=IFCSPACE('5678901234567890',$,'Conference Room',$,$,#13,$,$,.ELEMENT.,.INTERNAL.,$,$);
#6=IFCSPACE('6789012345678901',$,'Open Office',$,$,#14,$,$,.ELEMENT.,.INTERNAL.,$,$);
#7=IFCDISTRIBUTIONELEMENT('7890123456789012',$,'HVAC Unit 1',$,'AC-001',#15,$,$);
#8=IFCFLOWTERMINAL('8901234567890123',$,'Thermostat',$,'THERM-001',#16,$,$);
#9=IFCLIGHTFIXTURE('9012345678901234',$,'LED Panel',$,'LIGHT-001',#17,$,$);
#10=IFCLOCALPLACEMENT($,#18);
#11=IFCLOCALPLACEMENT(#10,#19);
#12=IFCLOCALPLACEMENT(#10,#20);
#13=IFCLOCALPLACEMENT(#11,#21);
#14=IFCLOCALPLACEMENT(#11,#22);
#15=IFCLOCALPLACEMENT(#13,#23);
#16=IFCLOCALPLACEMENT(#13,#24);
#17=IFCLOCALPLACEMENT(#14,#25);
#18=IFCAXIS2PLACEMENT3D(#26,$,$);
#19=IFCAXIS2PLACEMENT3D(#27,$,$);
#20=IFCAXIS2PLACEMENT3D(#28,$,$);
#21=IFCAXIS2PLACEMENT3D(#29,$,$);
#22=IFCAXIS2PLACEMENT3D(#30,$,$);
#23=IFCAXIS2PLACEMENT3D(#31,$,$);
#24=IFCAXIS2PLACEMENT3D(#32,$,$);
#25=IFCAXIS2PLACEMENT3D(#33,$,$);
#26=IFCCARTESIANPOINT((0.,0.,0.));
#27=IFCCARTESIANPOINT((0.,0.,0.));
#28=IFCCARTESIANPOINT((0.,0.,3500.));
#29=IFCCARTESIANPOINT((1000.,1000.,0.));
#30=IFCCARTESIANPOINT((6000.,1000.,0.));
#31=IFCCARTESIANPOINT((2000.,2000.,2700.));
#32=IFCCARTESIANPOINT((4000.,4000.,500.));
#33=IFCCARTESIANPOINT((8000.,3000.,2800.));
ENDSEC;
END-ISO-10303-21;
EOF
    print_info "Created sample IFC file"
fi

demo_command "../arx import ifc ../test_data/sample.ifc --building-id ARXOS-001"

print_step "Verifying import..."
demo_command "../arx query buildings"

wait_for_enter

# Step 4: Spatial Queries
print_header "Step 4: Demonstrating Spatial Queries"
print_step "ArxOS uses PostGIS for millimeter-precision spatial queries..."

echo -e "\n${CYAN}Query equipment on a specific floor:${NC}"
demo_command "../arx query equipment --floor 0"

echo -e "\n${CYAN}Find equipment within 5 meters of a point:${NC}"
demo_command "../arx query equipment --near '2000,2000,2700' --radius 5000"

echo -e "\n${CYAN}List all rooms with their areas:${NC}"
demo_command "../arx query rooms --with-geometry"

wait_for_enter

# Step 5: Multi-Format Export
print_header "Step 5: Multi-Format Export Pipeline"
print_step "ArxOS can export building data in multiple formats..."

# Create export directory
mkdir -p ../exports

echo -e "\n${CYAN}Export to human-readable BIM format:${NC}"
demo_command "../arx export bim --building ARXOS-001 --output ../exports/building.bim.txt"
echo "Preview of BIM export:"
head -20 ../exports/building.bim.txt 2>/dev/null || echo "Export pending..."

echo -e "\n${CYAN}Export equipment list to CSV:${NC}"
demo_command "../arx export csv --equipment --output ../exports/equipment.csv"

echo -e "\n${CYAN}Export complete building to JSON:${NC}"
demo_command "../arx export json --building ARXOS-001 --output ../exports/building.json"

wait_for_enter

# Step 6: Daemon File Watching
print_header "Step 6: Daemon-Based File Watching"
print_step "The daemon watches directories for new IFC files and auto-imports them..."

echo -e "\n${CYAN}Starting the daemon:${NC}"
demo_command "../arx daemon start --watch ../test_data/ifc --daemon &"
DAEMON_PID=$!
sleep 2

print_info "Daemon is now watching ../test_data/ifc directory"
print_info "Any IFC files placed there will be automatically imported"

echo -e "\n${CYAN}Simulating a new IFC file:${NC}"
mkdir -p ../test_data/ifc
cp ../test_data/sample.ifc ../test_data/ifc/new_building_$(date +%s).ifc
sleep 3

echo -e "\n${CYAN}Checking daemon status:${NC}"
demo_command "../arx daemon status"

echo -e "\n${CYAN}Stopping the daemon:${NC}"
kill $DAEMON_PID 2>/dev/null || true
wait $DAEMON_PID 2>/dev/null || true

wait_for_enter

# Step 7: Advanced Features
print_header "Step 7: Advanced Features"

echo -e "${CYAN}Repository-style version control:${NC}"
demo_command "../arx repo status --building ARXOS-001"

echo -e "\n${CYAN}Building statistics:${NC}"
demo_command "../arx stats --building ARXOS-001"

echo -e "\n${CYAN}Health monitoring:${NC}"
demo_command "../arx query --health --verbose"

wait_for_enter

# Step 8: Docker Deployment
print_header "Step 8: Production Docker Deployment"
print_step "ArxOS can be deployed as a complete Docker stack..."

echo "The full stack includes:"
echo "  • PostGIS spatial database (port 5432)"
echo "  • ArxOS API server (port 8080)"
echo "  • ArxOS daemon for file watching"
echo "  • Optional: PgAdmin, Redis, Prometheus, Grafana"
echo
echo "Deploy with:"
echo -e "${BLUE}  docker-compose up -d${NC}"
echo
echo "Or for production:"
echo -e "${BLUE}  docker-compose -f docker/docker-compose.base.yml -f docker/docker-compose.prod.yml up -d${NC}"

wait_for_enter

# Cleanup
print_header "Demo Complete!"
echo "You've seen ArxOS in action with:"
echo "  ✓ PostGIS spatial database"
echo "  ✓ IFC import and processing"
echo "  ✓ Millimeter-precision spatial queries"
echo "  ✓ Multi-format export pipeline"
echo "  ✓ Daemon-based automation"
echo "  ✓ Docker deployment"
echo
echo -e "${GREEN}Thank you for trying ArxOS!${NC}"
echo
echo "Next steps:"
echo "  • Import your own IFC files"
echo "  • Explore the REST API at http://localhost:8080/swagger"
echo "  • Check out the documentation in /docs"
echo "  • Join our community at github.com/arx-os/arxos"
echo

# Optional: Stop services
read -p "Stop PostGIS database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose down
    echo -e "${GREEN}Services stopped.${NC}"
fi

echo -e "\n${BLUE}Goodbye!${NC}"