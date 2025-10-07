#!/bin/bash
# Demo script for ArxOS Phase 1 Manual Entry

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

echo "ArxOS Phase 1 - Manual Equipment Entry Demo"
echo "============================================"
echo ""

# Build the application
echo "Building ArxOS..."
go build -o arx ./cmd/arx
echo ""

echo "1. Importing Alafia ES floor plan..."
./arx import Alafia_ES_IDF_CallOut.ifc 2>/dev/null || echo "   IFC already imported"

echo ""
echo "2. Current floor plan status..."
./arx status Alafia_ES_IDF_CallOut

echo ""
echo "3. Adding IDF equipment from the floor plan..."
./arx add "IDF 800b" --type idf --room area_13 --location 75,10 --floor Alafia_ES_IDF_CallOut.ifc
./arx add "IDF 606a" --type idf --room area_31 --location 15,50 --floor Alafia_ES_IDF_CallOut.ifc
./arx add "IDF 507a" --type idf --room area_32 --location 45,50 --floor Alafia_ES_IDF_CallOut.json
./arx add "IDF 516" --type idf --room area_33 --location 75,50 --floor Alafia_ES_IDF_CallOut.json

echo ""
echo "4. Viewing ASCII map with equipment..."
./arx map Alafia_ES_IDF_CallOut

echo ""
echo "5. Marking equipment status..."
./arx mark "IDF 507a" --status needs-repair --notes "Port 24 not responding" --floor Alafia_ES_IDF_CallOut.json
./arx mark "MDF 300c" --status failed --notes "Power failure" --floor Alafia_ES_IDF_CallOut.json

echo ""
echo "6. Final status summary..."
./arx status Alafia_ES_IDF_CallOut

echo ""
echo "7. Viewing updated map with status indicators..."
./arx map Alafia_ES_IDF_CallOut

echo ""
echo "Demo complete!"
echo "State files saved in .arxos/"
