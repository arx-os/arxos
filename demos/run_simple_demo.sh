#!/bin/bash

# Simple ArxOS Demo - Quick 5-minute demonstration
# Shows core PostGIS functionality without detailed explanations

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}ArxOS Simple Demo - PostGIS Spatial Database${NC}\n"

# Navigate to project root
cd "$(dirname "$0")/.."

# Build if needed
if [ ! -f "./arx" ]; then
    echo "Building ArxOS..."
    go build -o arx ./cmd/arx
fi

# Start PostGIS
echo -e "${BLUE}1. Starting PostGIS Database${NC}"
if ! docker ps | grep -q arxos-postgis; then
    docker-compose up -d postgis
    sleep 3
fi
echo "✓ PostGIS running"
echo

# Import sample building
echo -e "${BLUE}2. Importing Sample Building${NC}"
mkdir -p test_data
cat > test_data/demo.ifc << 'EOF'
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Simple Demo'),'2;1');
FILE_NAME('demo.ifc','2024-01-01T00:00:00',(),(),'ArxOS','Demo','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('PROJ1',$,'Demo Building',$,$,$,$,$,$);
#2=IFCBUILDING('BLDG1',$,'Office Tower',$,$,$,$,$,.ELEMENT.,$,$,$);
#3=IFCBUILDINGSTOREY('FLR1',$,'Ground Floor',$,$,$,$,$,.ELEMENT.,0.);
#4=IFCBUILDINGSTOREY('FLR2',$,'First Floor',$,$,$,$,$,.ELEMENT.,3500.);
#5=IFCSPACE('SPC1',$,'Lobby',$,$,$,$,$,.ELEMENT.,.INTERNAL.,$,$);
#6=IFCSPACE('SPC2',$,'Server Room',$,$,$,$,$,.ELEMENT.,.INTERNAL.,$,$);
#7=IFCDISTRIBUTIONELEMENT('HVAC1',$,'AC Unit 1',$,'AC-001',$,$,$);
#8=IFCFLOWTERMINAL('THERM1',$,'Thermostat',$,'THERM-001',$,$,$);
#9=IFCFURNISHINGELEMENT('DESK1',$,'Reception Desk',$,'FURN-001',$,$,$);
#10=IFCLIGHTFIXTURE('LIGHT1',$,'LED Panel',$,'LIGHT-001',$,$,$);
ENDSEC;
END-ISO-10303-21;
EOF

./arx import ifc test_data/demo.ifc --building-id ARXOS-DEMO
echo "✓ Building imported to PostGIS"
echo

# Query with spatial functions
echo -e "${BLUE}3. Spatial Queries with PostGIS${NC}"
echo "All buildings:"
./arx query buildings

echo -e "\nFloors in building:"
./arx query floors --building ARXOS-DEMO

echo -e "\nEquipment with locations:"
./arx query equipment --building ARXOS-DEMO --with-geometry
echo

# Export data
echo -e "${BLUE}4. Multi-Format Export${NC}"
mkdir -p exports

echo "Exporting BIM..."
./arx export bim --building ARXOS-DEMO --output exports/demo.bim.txt

echo "Exporting CSV..."
./arx export csv --equipment --output exports/equipment.csv

echo "Exporting JSON..."
./arx export json --building ARXOS-DEMO --output exports/building.json

echo "✓ All exports complete"
echo

# Show results
echo -e "${BLUE}5. Results${NC}"
echo "BIM Export Preview:"
head -20 exports/demo.bim.txt 2>/dev/null || echo "Pending..."
echo
echo "Files created:"
ls -lh exports/ 2>/dev/null | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
echo

# Health check
echo -e "${BLUE}6. System Health${NC}"
./arx query --health
echo

echo -e "${GREEN}✅ Demo Complete!${NC}"
echo
echo "Next steps:"
echo "  • Try spatial query: ./arx query equipment --near '0,0,0' --radius 10000"
echo "  • Start daemon: ./arx daemon start --watch test_data/ifc"
echo "  • View API: http://localhost:8080/swagger"
echo "  • Full stack: docker-compose up -d"