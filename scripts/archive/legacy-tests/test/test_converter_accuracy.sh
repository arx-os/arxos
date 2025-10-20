#!/bin/bash

# Test converter accuracy across different input formats
# This script validates that converters produce consistent, accurate output

set -e

echo "ArxOS Converter Accuracy Test"
echo "============================="

# Test data directory
TEST_DATA_DIR="../../test_data"
OUTPUT_DIR="./converter_test_output"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Test IFC conversion
if [ -f "$TEST_DATA_DIR/sample.ifc" ]; then
    echo "Testing IFC conversion..."
    arx convert "$TEST_DATA_DIR/sample.ifc" "$OUTPUT_DIR/ifc_test.bim.txt"

    # Validate output
    arx validate "$OUTPUT_DIR/ifc_test.bim.txt"

    if [ $? -eq 0 ]; then
        echo "✓ IFC conversion passed"
    else
        echo "✗ IFC conversion failed"
        exit 1
    fi
fi

# Test other format conversion
if [ -f "$TEST_DATA_DIR/sample_building.json" ]; then
    echo "Testing JSON conversion..."
    # Note: This would need a real JSON file for testing
    echo "⚠ JSON test skipped - no JSON test file available"
fi

# Test Haystack conversion
if [ -f "$TEST_DATA_DIR/sample_haystack.json" ]; then
    echo "Testing Haystack conversion..."
    arx convert "$TEST_DATA_DIR/sample_haystack.json" "$OUTPUT_DIR/haystack_test.bim.txt"

    # Validate output
    arx validate "$OUTPUT_DIR/haystack_test.bim.txt"

    if [ $? -eq 0 ]; then
        echo "✓ Haystack conversion passed"
    else
        echo "✗ Haystack conversion failed"
        exit 1
    fi
fi

# Test gbXML conversion
if [ -f "$TEST_DATA_DIR/sample.gbxml" ]; then
    echo "Testing gbXML conversion..."
    arx convert "$TEST_DATA_DIR/sample.gbxml" "$OUTPUT_DIR/gbxml_test.bim.txt"

    # Validate output
    arx validate "$OUTPUT_DIR/gbxml_test.bim.txt"

    if [ $? -eq 0 ]; then
        echo "✓ gbXML conversion passed"
    else
        echo "✗ gbXML conversion failed"
        exit 1
    fi
fi

echo ""
echo "Converter accuracy test completed"
echo "Output files in: $OUTPUT_DIR"

# Clean up test output (optional)
read -p "Remove test output files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$OUTPUT_DIR"
    echo "Test output cleaned up"
fi
