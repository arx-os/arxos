#!/bin/bash
# Validate an ArxOS building structure

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <building-directory>"
    echo "Example: $0 buildings/ARXOS-NA-US-NY-NYC-0001"
    exit 1
fi

BUILDING_DIR="$1"

if [ ! -d "$BUILDING_DIR" ]; then
    echo "Error: Directory '$BUILDING_DIR' not found"
    exit 1
fi

# Extract UUID from path
UUID=$(basename "$BUILDING_DIR")

echo "Validating building structure: $UUID"
echo "========================================="

# Check for required files
echo -n "Checking building.bim.txt... "
if [ -f "$BUILDING_DIR/building.bim.txt" ]; then
    echo "✓"
else
    echo "✗ Missing"
fi

echo -n "Checking README.md... "
if [ -f "$BUILDING_DIR/README.md" ]; then
    echo "✓"
else
    echo "✗ Missing"
fi

echo -n "Checking git repository... "
if [ -d "$BUILDING_DIR/.git" ]; then
    echo "✓"
else
    echo "✗ Not initialized"
fi

# Count structure elements
echo ""
echo "Structure Analysis:"
echo "-------------------"

# Count wings
wings=$(find "$BUILDING_DIR" -maxdepth 1 -type d -name "[NSEWC]" | wc -l)
echo "Wings: $wings"

# Count total directories
total_dirs=$(find "$BUILDING_DIR" -type d | wc -l)
echo "Total directories: $total_dirs"

# Count equipment files
equipment_files=$(find "$BUILDING_DIR" -name "*.txt" -not -name "building.bim.txt" 2>/dev/null | wc -l)
echo "Equipment files: $equipment_files"

# Check for any failed equipment
echo ""
echo "Equipment Status:"
echo "-----------------"

failed=$(grep -r "STATUS: FAILED" "$BUILDING_DIR" --include="*.txt" 2>/dev/null | wc -l)
degraded=$(grep -r "STATUS: DEGRADED" "$BUILDING_DIR" --include="*.txt" 2>/dev/null | wc -l)
operational=$(grep -r "STATUS: OPERATIONAL" "$BUILDING_DIR" --include="*.txt" 2>/dev/null | wc -l)

echo "Operational: $operational"
echo "Degraded: $degraded"
echo "Failed: $failed"

# Show recent changes if git repo
if [ -d "$BUILDING_DIR/.git" ]; then
    echo ""
    echo "Recent Git Activity:"
    echo "--------------------"
    cd "$BUILDING_DIR"
    git log --oneline -5 2>/dev/null || echo "No commits yet"
fi

# Validate UUID format
echo ""
echo "UUID Validation:"
echo "----------------"
if echo "$UUID" | grep -qE '^ARXOS-[A-Z]{2}-[A-Z]{2}-[A-Z0-9]{2,3}-[A-Z]{3,4}-[0-9]{4}$'; then
    echo "✓ Valid UUID format: $UUID"

    # Parse UUID components
    IFS='-' read -r prefix continent country state city seq <<< "$UUID"
    echo "  Continent: $continent"
    echo "  Country: $country"
    echo "  State/Region: $state"
    echo "  City: $city"
    echo "  Sequence: $seq"
else
    echo "✗ Invalid UUID format"
fi

echo ""
echo "Validation complete!"