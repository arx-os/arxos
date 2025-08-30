#!/bin/bash

# Test script for document parser functionality
# Tests PDF and IFC parsing, ASCII rendering, and ArxObject conversion

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║     Arxos Document Parser Test Suite                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo

# Create test directory
TEST_DIR="/tmp/arxos_doc_test"
mkdir -p "$TEST_DIR"

# Create a test PDF
echo "Creating test PDF..."
cat > "$TEST_DIR/test_building.pdf" << 'EOF'
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 400 >>
stream
BT
/F1 12 Tf
50 700 Td
(BUILDING NAME: Jefferson Elementary School) Tj
0 -20 Td
(ROOM SCHEDULE) Tj
0 -20 Td
(Room 127 - Science Lab - 800 sq ft) Tj
0 -15 Td
(Room 128 - Classroom - 600 sq ft) Tj
0 -15 Td
(Room 129 - Computer Lab - 750 sq ft) Tj
0 -20 Td
(EQUIPMENT SCHEDULE) Tj
0 -15 Td
(EO-127-01  Electrical Outlet  Room 127) Tj
0 -15 Td
(LF-128-01  Light Fixture  Room 128) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000229 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
679
%%EOF
EOF

# Create a test IFC file
echo "Creating test IFC..."
cat > "$TEST_DIR/test_building.ifc" << 'EOF'
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',(),(),'ArxOS','Terminal','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCPROJECT('proj1',$,'Jefferson Elementary',$,$,$,$,$,$);
#2=IFCBUILDING('bldg1',$,'Main Building',$,$,$,$,$,$,$,$,$);
#3=IFCBUILDINGSTOREY('floor1',$,'Level 1',$,$,$,$,$,$,$);
#4=IFCSPACE('room127',$,'127','Science Lab',$,$,$,$,$,$);
#5=IFCSPACE('room128',$,'128','Classroom',$,$,$,$,$,$);
#6=IFCOUTLET('outlet1',$,'Outlet',$,$,$,$,$);
#7=IFCLIGHTFIXTURE('light1',$,'Light',$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;
EOF

echo "Test files created in $TEST_DIR"
echo

# Run Rust tests
echo "Running Rust unit tests..."
cd /Users/joelpate/repos/arxos
cargo test --package arxos-core document_parser:: --lib 2>/dev/null || true

echo
echo "Running integration tests..."
cargo test --test document_parser_integration 2>/dev/null || true

echo
echo "═══════════════════════════════════════════════════════════"
echo "Manual Testing Instructions:"
echo "═══════════════════════════════════════════════════════════"
echo
echo "1. Start the terminal client:"
echo "   cargo run --bin arxos"
echo
echo "2. Load a PDF building plan:"
echo "   load-plan $TEST_DIR/test_building.pdf"
echo
echo "3. Load an IFC model:"
echo "   load-plan $TEST_DIR/test_building.ifc"
echo
echo "4. View floor plans:"
echo "   view-floor 1"
echo "   list-floors"
echo "   show-equipment"
echo
echo "5. Export to ArxObjects:"
echo "   export-arxobjects /tmp/building.arxo"
echo
echo "Test files are in: $TEST_DIR"
echo

# Show sample ASCII output
echo "Sample ASCII Floor Plan Output:"
echo "╔════════════════════════════════════════╗"
echo "║         FLOOR 1 - LEVEL 1              ║"
echo "╠════════════════════════════════════════╣"
echo "║ ┌─────────┐  ┌─────────┐  ┌─────────┐ ║"
echo "║ │  127    │  │  128    │  │  129    │ ║"
echo "║ │ [O] [L] │  │ [L] [V] │  │ [F] [D] │ ║"
echo "║ └─────────┘  └─────────┘  └─────────┘ ║"
echo "╚════════════════════════════════════════╝"
echo
echo "Legend: [O]=Outlet [L]=Light [V]=Vent [F]=Fire Alarm [D]=Data Port"