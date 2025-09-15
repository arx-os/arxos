#!/bin/bash

# Test converter accuracy for all supported formats

echo "=========================================="
echo "ArxOS Converter Accuracy Test"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if file contains expected content
check_content() {
    local file=$1
    local search=$2
    local description=$3

    if grep -q "$search" "$file"; then
        echo -e "${GREEN}✓${NC} $description found"
        return 0
    else
        echo -e "${RED}✗${NC} $description missing"
        return 1
    fi
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

echo "1. Testing IFC Conversion"
echo "-------------------------"
./arx convert test_data/sample.ifc /tmp/test_ifc.bim.txt --force > /dev/null 2>&1
if [ -f /tmp/test_ifc.bim.txt ]; then
    check_content /tmp/test_ifc.bim.txt "Sample Building" "Building name" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_ifc.bim.txt "Ground Floor" "Floor name" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_ifc.bim.txt "Room 101" "Room name" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_ifc.bim.txt "AHU-01" "Equipment tag" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
else
    echo -e "${RED}✗${NC} IFC conversion failed"
    ((TESTS_FAILED+=4))
fi
echo ""

echo "2. Testing PDF/Text Conversion"
echo "------------------------------"
./arx convert test_data/sample_floorplan.txt /tmp/test_pdf.bim.txt --force > /dev/null 2>&1
if [ -f /tmp/test_pdf.bim.txt ]; then
    check_content /tmp/test_pdf.bim.txt "Reception Area" "Room name" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_pdf.bim.txt "450" "Room area" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_pdf.bim.txt "Server Room" "Server room" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_pdf.bim.txt "HVAC-01" "HVAC equipment" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
else
    echo -e "${RED}✗${NC} PDF conversion failed"
    ((TESTS_FAILED+=4))
fi
echo ""

echo "3. Testing gbXML Conversion"
echo "---------------------------"
./arx convert test_data/sample.gbxml /tmp/test_gbxml.bim.txt --force > /dev/null 2>&1
if [ -f /tmp/test_gbxml.bim.txt ]; then
    check_content /tmp/test_gbxml.bim.txt "Room 101" "Space 1" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_gbxml.bim.txt "150" "Area value" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_gbxml.bim.txt "Room 201" "Space 3" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
else
    echo -e "${RED}✗${NC} gbXML conversion failed"
    ((TESTS_FAILED+=3))
fi
echo ""

echo "4. Testing Haystack IoT Conversion"
echo "----------------------------------"
./arx convert test_data/sample_haystack.json /tmp/test_haystack.bim.txt --force > /dev/null 2>&1
if [ -f /tmp/test_haystack.bim.txt ]; then
    check_content /tmp/test_haystack.bim.txt "Room 101" "IoT space" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_haystack.bim.txt "Air Handler" "AHU equipment" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_haystack.bim.txt "VAV Box" "VAV equipment" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_haystack.bim.txt "hvac" "Equipment type" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
else
    echo -e "${RED}✗${NC} Haystack conversion failed"
    ((TESTS_FAILED+=4))
fi
echo ""

echo "5. Testing COBie Conversion"
echo "---------------------------"
./arx convert test_data/sample_cobie.csv /tmp/test_cobie.bim.txt --force > /dev/null 2>&1
if [ -f /tmp/test_cobie.bim.txt ]; then
    echo -e "${GREEN}✓${NC} COBie conversion succeeded"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} COBie conversion failed"
    ((TESTS_FAILED++))
fi
echo ""

echo "6. Testing Merge Functionality"
echo "------------------------------"
# Create base file
./arx convert test_data/sample.ifc /tmp/test_merge.bim.txt --force > /dev/null 2>&1
ORIGINAL_SIZE=$(wc -c < /tmp/test_merge.bim.txt)

# Merge additional data
./arx convert test_data/sample_haystack.json /tmp/test_merge.bim.txt --merge --force > /dev/null 2>&1
MERGED_SIZE=$(wc -c < /tmp/test_merge.bim.txt)

if [ $MERGED_SIZE -gt $ORIGINAL_SIZE ]; then
    echo -e "${GREEN}✓${NC} Merge increased file size"
    check_content /tmp/test_merge.bim.txt "Sample Building" "Original content preserved" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
    check_content /tmp/test_merge.bim.txt "Air Handler" "New content added" && ((TESTS_PASSED++)) || ((TESTS_FAILED++))
else
    echo -e "${RED}✗${NC} Merge failed"
    ((TESTS_FAILED+=2))
fi
echo ""

echo "=========================================="
echo "Test Results"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}"
    exit 1
fi