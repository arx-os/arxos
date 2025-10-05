#!/bin/bash

# Test Data Validation Script
# Validates that all expected outputs exist and are properly formatted

set -e

echo "🔍 Validating ArxOS Test Data..."
echo "================================="

# Check if we're in the right directory
if [ ! -d "inputs" ] || [ ! -d "expected" ]; then
    echo "❌ Error: Must run from test_data directory"
    exit 1
fi

echo "📁 Checking input files..."
INPUT_FILES=(
    "inputs/sample.ifc"
    "inputs/sample.gbxml"
    "inputs/sample_cobie.csv"
    "inputs/sample_haystack.json"
    "inputs/spatial_building.ifc"
    "inputs/complex_building.ifc"
    "inputs/malformed.ifc"
)

for file in "${INPUT_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        exit 1
    fi
done

echo ""
echo "📁 Checking expected output files..."
EXPECTED_FILES=(
    "expected/building_from_ifc.bim.txt"
    "expected/building_from_gbxml.bim.txt"
    "expected/building_from_cobie.bim.txt"
    "expected/building_from_haystack.bim.txt"
    "expected/merged_building.bim.txt"
    "expected/sample_floorplan.txt"
)

for file in "${EXPECTED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        exit 1
    fi
done

echo ""
echo "🔍 Validating file formats..."

# Check IFC files
echo "  Checking IFC files..."
for ifc_file in inputs/*.ifc; do
    if grep -q "ISO-10303-21" "$ifc_file" && grep -q "ENDSEC" "$ifc_file"; then
        echo "    ✅ $ifc_file (valid IFC format)"
    else
        echo "    ❌ $ifc_file (invalid IFC format)"
        exit 1
    fi
done

# Check gbXML file
echo "  Checking gbXML file..."
if grep -q "gbXML" inputs/sample.gbxml && grep -q "Building" inputs/sample.gbxml; then
    echo "    ✅ inputs/sample.gbxml (valid gbXML format)"
else
    echo "    ❌ inputs/sample.gbxml (invalid gbXML format)"
    exit 1
fi

# Check COBie CSV file
echo "  Checking COBie CSV file..."
if grep -q "SheetName" inputs/sample_cobie.csv && grep -q "Space" inputs/sample_cobie.csv; then
    echo "    ✅ inputs/sample_cobie.csv (valid COBie format)"
else
    echo "    ❌ inputs/sample_cobie.csv (invalid COBie format)"
    exit 1
fi

# Check Haystack JSON file
echo "  Checking Haystack JSON file..."
if python3 -m json.tool inputs/sample_haystack.json > /dev/null 2>&1; then
    echo "    ✅ inputs/sample_haystack.json (valid JSON format)"
else
    echo "    ❌ inputs/sample_haystack.json (invalid JSON format)"
    exit 1
fi

# Check expected output files
echo "  Checking expected output files..."
for expected_file in expected/*.bim.txt; do
    if grep -q "BUILDING DATA" "$expected_file" && grep -q "ArxOS" "$expected_file"; then
        echo "    ✅ $expected_file (valid BIM text format)"
    else
        echo "    ❌ $expected_file (invalid BIM text format)"
        exit 1
    fi
done

echo ""
echo "📊 Test Data Summary:"
echo "  Input files: ${#INPUT_FILES[@]}"
echo "  Expected files: ${#EXPECTED_FILES[@]}"
echo "  Error test files: 1 (malformed.ifc)"
echo "  Complex test files: 1 (complex_building.ifc)"

echo ""
echo "✅ All test data validation passed!"
echo "🎉 ArxOS test data is ready for use"
