#!/bin/bash

# ArxOS IFC Import/Export Demo
# Demonstrates converting IFC files and exporting to various formats

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo "ArxOS IFC Import & Export Pipeline"
echo "==========================================${NC}"
echo ""

# Setup
DEMO_DIR="demo_converter_output"
rm -rf $DEMO_DIR
mkdir -p $DEMO_DIR

# Ensure we're in the right directory
cd "$(dirname "$0")"
cd ..

# Build if necessary
if [ ! -f "./arx" ]; then
    echo -e "${YELLOW}Building ArxOS...${NC}"
    go build -o arx ./cmd/arx
fi

echo -e "${CYAN}📋 Supported operations:${NC}"
echo "  • Import: IFC, IFCZip, IFCXML"
echo "  • Export: BIM (human-readable), CSV, JSON"
echo ""

# Start PostGIS if not running
if ! docker ps | grep -q arxos-postgis; then
    echo -e "${YELLOW}Starting PostGIS database...${NC}"
    docker-compose up -d postgis
    sleep 5
fi

echo ""
echo -e "${GREEN}=========================================="
echo "1. Importing IFC (Industry Foundation Classes)"
echo "==========================================${NC}"

# Create sample IFC if needed
if [ ! -f test_data/sample.ifc ]; then
    mkdir -p test_data
    echo -e "${YELLOW}Creating sample IFC file...${NC}"
    cat > test_data/sample.ifc << 'EOF'
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Converter Demo Building'),'2;1');
FILE_NAME('converter_demo.ifc','2024-01-01T00:00:00',(),(),'ArxOS','Converter Demo','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('PROJ001',$,'Converter Demo Project',$,$,$,$,$,$);
#2=IFCBUILDING('BLDG001',$,'Office Complex',$,'Main office building',$,$,$,.ELEMENT.,$,$,$);
#3=IFCBUILDINGSTOREY('FLR001',$,'Ground Floor',$,'Entry level',$,$,$,.ELEMENT.,0.);
#4=IFCBUILDINGSTOREY('FLR002',$,'First Floor',$,'Office level',$,$,$,.ELEMENT.,3500.);
#5=IFCBUILDINGSTOREY('FLR003',$,'Second Floor',$,'Executive level',$,$,$,.ELEMENT.,7000.);
#6=IFCSPACE('SPC001',$,'Lobby',$,'Main entrance',$,$,$,.ELEMENT.,.INTERNAL.,$,$);
#7=IFCSPACE('SPC002',$,'Conference Room A',$,'Large meeting room',$,$,$,.ELEMENT.,.INTERNAL.,$,$);
#8=IFCSPACE('SPC003',$,'Open Office',$,'Collaborative workspace',$,$,$,.ELEMENT.,.INTERNAL.,$,$);
#9=IFCSPACE('SPC004',$,'Server Room',$,'IT infrastructure',$,$,$,.ELEMENT.,.INTERNAL.,$,$);
#10=IFCDISTRIBUTIONELEMENT('HVAC001',$,'HVAC Unit 1',$,'AC-001',$,$,$);
#11=IFCDISTRIBUTIONELEMENT('HVAC002',$,'HVAC Unit 2',$,'AC-002',$,$,$);
#12=IFCFLOWTERMINAL('TERM001',$,'Thermostat Zone 1',$,'THERM-001',$,$,$);
#13=IFCFLOWTERMINAL('TERM002',$,'Thermostat Zone 2',$,'THERM-002',$,$,$);
#14=IFCLIGHTFIXTURE('LIGHT001',$,'LED Panel Grid A',$,'LIGHT-A01',$,$,$);
#15=IFCLIGHTFIXTURE('LIGHT002',$,'LED Panel Grid B',$,'LIGHT-B01',$,$,$);
#16=IFCFLOWSEGMENT('DUCT001',$,'Supply Duct Main',$,'DUCT-SUPPLY-01',$,$,$);
#17=IFCFLOWSEGMENT('PIPE001',$,'Water Main',$,'PIPE-WATER-01',$,$,$);
#18=IFCDOOR('DOOR001',$,'Main Entrance',$,'DOOR-MAIN',$,$,$,$,$);
#19=IFCWINDOW('WIN001',$,'Window Bank North',$,'WIN-N-01',$,$,$,$,$);
#20=IFCFURNISHINGELEMENT('FURN001',$,'Reception Desk',$,'FURN-RECEP',$,$,$);
ENDSEC;
END-ISO-10303-21;
EOF
fi

echo "Converting test_data/sample.ifc..."
./arx import ifc test_data/sample.ifc --building-id ARXOS-DEMO
echo -e "${GREEN}✅ IFC imported successfully${NC}"

# Show what was imported
echo ""
echo "Imported building structure:"
./arx query buildings --id ARXOS-DEMO

echo ""
echo -e "${GREEN}=========================================="
echo "2. Querying Imported Data with PostGIS"
echo "==========================================${NC}"

echo -e "\n${CYAN}Floors in building:${NC}"
./arx query floors --building ARXOS-DEMO

echo -e "\n${CYAN}Equipment count by type:${NC}"
./arx query equipment --building ARXOS-DEMO --group-by type

echo -e "\n${CYAN}Spatial distribution:${NC}"
./arx query rooms --building ARXOS-DEMO --with-geometry

echo ""
echo -e "${GREEN}=========================================="
echo "3. Exporting to BIM Text Format"
echo "==========================================${NC}"

echo "Generating human-readable BIM file..."
./arx export bim --building ARXOS-DEMO --output demos/$DEMO_DIR/building.bim.txt
echo -e "${GREEN}✅ BIM export complete${NC}"
echo ""
echo "Preview of BIM file:"
head -30 demos/$DEMO_DIR/building.bim.txt
echo "..."
echo ""

echo -e "${GREEN}=========================================="
echo "4. Exporting Equipment to CSV"
echo "==========================================${NC}"

echo "Generating CSV equipment schedule..."
./arx export csv --equipment --building ARXOS-DEMO --output demos/$DEMO_DIR/equipment.csv
echo -e "${GREEN}✅ CSV export complete${NC}"
echo ""
echo "CSV Preview:"
head -10 demos/$DEMO_DIR/equipment.csv
echo ""

echo -e "${GREEN}=========================================="
echo "5. Exporting to JSON (API Format)"
echo "==========================================${NC}"

echo "Generating JSON export..."
./arx export json --building ARXOS-DEMO --output demos/$DEMO_DIR/building.json
echo -e "${GREEN}✅ JSON export complete${NC}"
echo ""
echo "JSON structure preview:"
cat demos/$DEMO_DIR/building.json | python3 -m json.tool | head -50 2>/dev/null || \
    cat demos/$DEMO_DIR/building.json | head -50

echo ""
echo -e "${GREEN}=========================================="
echo "6. Advanced Export Options"
echo "==========================================${NC}"

echo -e "\n${CYAN}Export specific floor:${NC}"
./arx export bim --building ARXOS-DEMO --floor 0 --output demos/$DEMO_DIR/ground_floor.bim.txt
echo "Created: demos/$DEMO_DIR/ground_floor.bim.txt"

echo -e "\n${CYAN}Export maintenance schedule:${NC}"
./arx export csv --maintenance --building ARXOS-DEMO --output demos/$DEMO_DIR/maintenance.csv
echo "Created: demos/$DEMO_DIR/maintenance.csv"

echo -e "\n${CYAN}Export for visualization:${NC}"
./arx export json --building ARXOS-DEMO --include-geometry --output demos/$DEMO_DIR/visualization.json
echo "Created: demos/$DEMO_DIR/visualization.json"

echo ""
echo -e "${GREEN}=========================================="
echo "7. Batch Processing with Daemon"
echo "==========================================${NC}"

echo "The ArxOS daemon can watch directories and automatically:"
echo "  • Import new IFC files"
echo "  • Generate exports on schedule"
echo "  • Sync with remote repositories"
echo ""
echo "Start daemon with:"
echo -e "${BLUE}  ./arx daemon start --watch /path/to/ifc/files --auto-export${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "8. File Statistics"
echo "==========================================${NC}"

echo "Generated files summary:"
ls -lh demos/$DEMO_DIR/*.* 2>/dev/null | awk '{print $9 ": " $5}' | column -t

echo ""
echo -e "${GREEN}=========================================="
echo "Conversion Demo Complete!"
echo "==========================================${NC}"

echo ""
echo "Summary:"
echo "  ✓ Imported IFC building data to PostGIS"
echo "  ✓ Performed spatial queries on building data"
echo "  ✓ Exported to human-readable BIM format"
echo "  ✓ Generated CSV equipment schedules"
echo "  ✓ Created JSON for API integration"
echo "  ✓ Demonstrated advanced export options"
echo ""
echo "Output files are in: demos/$DEMO_DIR/"
echo ""