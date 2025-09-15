#!/bin/bash

# ArxOS Universal Building File Converter Demo
# Demonstrates converting various building file formats to BIM

set -e

echo "=========================================="
echo "ArxOS Universal Building File Converter"
echo "=========================================="
echo ""

# Setup
DEMO_DIR="demo_converter_output"
rm -rf $DEMO_DIR
mkdir -p $DEMO_DIR

echo "📋 Supported file formats:"
./arx convert list

echo ""
echo "=========================================="
echo "1. Converting IFC (Industry Foundation Classes)"
echo "=========================================="
if [ -f test_data/sample.ifc ]; then
    echo "Converting test_data/sample.ifc..."
    ./arx convert test_data/sample.ifc $DEMO_DIR/building_from_ifc.bim.txt
    echo "✅ IFC converted successfully"
    echo "Preview:"
    head -15 $DEMO_DIR/building_from_ifc.bim.txt
fi

echo ""
echo "=========================================="
echo "2. Converting gbXML (Energy Models)"
echo "=========================================="
if [ -f test_data/sample.gbxml ]; then
    echo "Converting test_data/sample.gbxml..."
    ./arx convert test_data/sample.gbxml $DEMO_DIR/building_from_gbxml.bim.txt
    echo "✅ gbXML converted successfully"
    echo "Preview:"
    head -15 $DEMO_DIR/building_from_gbxml.bim.txt
fi

echo ""
echo "=========================================="
echo "3. Converting Haystack IoT Data"
echo "=========================================="
if [ -f test_data/sample_haystack.json ]; then
    echo "Converting test_data/sample_haystack.json..."
    ./arx convert test_data/sample_haystack.json $DEMO_DIR/building_from_haystack.bim.txt
    echo "✅ Haystack IoT data converted successfully"
    echo "Preview:"
    head -20 $DEMO_DIR/building_from_haystack.bim.txt
fi

echo ""
echo "=========================================="
echo "4. Converting COBie Spreadsheets"
echo "=========================================="
if [ -f test_data/sample_cobie.csv ]; then
    echo "Converting test_data/sample_cobie.csv..."
    ./arx convert test_data/sample_cobie.csv $DEMO_DIR/building_from_cobie.bim.txt
    echo "✅ COBie spreadsheet converted successfully"
fi

echo ""
echo "=========================================="
echo "5. Merging Multiple Sources"
echo "=========================================="
echo "Starting with IFC as base..."
./arx convert test_data/sample.ifc $DEMO_DIR/merged_building.bim.txt
echo "Merging Haystack IoT data..."
./arx convert test_data/sample_haystack.json $DEMO_DIR/merged_building.bim.txt --merge --force
echo "✅ Multiple sources merged successfully"
echo ""
echo "Final merged file size:"
ls -lh $DEMO_DIR/merged_building.bim.txt | awk '{print $5}'

echo ""
echo "=========================================="
echo "Summary of Converted Files"
echo "=========================================="
echo ""
echo "📁 Output directory: $DEMO_DIR"
echo ""
ls -la $DEMO_DIR/*.bim.txt

echo ""
echo "=========================================="
echo "💡 Key Features Demonstrated:"
echo "=========================================="
echo "✓ IFC (Industry standard BIM) → BIM.txt"
echo "✓ gbXML (Energy models) → BIM.txt"
echo "✓ Haystack (IoT/sensor data) → BIM.txt"
echo "✓ COBie (FM spreadsheets) → BIM.txt"
echo "✓ Merge multiple sources into single BIM"
echo ""
echo "🎯 Use Cases:"
echo "• Import existing BIM models (IFC, Revit)"
echo "• Extract data from PDF floor plans"
echo "• Integrate IoT sensor networks"
echo "• Convert FM/O&M spreadsheets"
echo "• Merge as-built + as-designed + as-operated"
echo ""
echo "Demo complete! Files saved in $DEMO_DIR/"