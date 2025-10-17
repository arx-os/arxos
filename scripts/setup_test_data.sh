#!/bin/bash
# Setup test database and sample data for ArxOS testing
#
# Usage: ./scripts/setup_test_data.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARX_BIN="$PROJECT_ROOT/bin/arx"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ArxOS Test Data Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if database is running
echo -e "${BLUE}Checking database connection...${NC}"
if psql -h localhost -U joelpate -d arxos_dev -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connected${NC}"
else
    echo -e "${YELLOW}⚠ Database not available. Trying default connection...${NC}"
    if ! psql -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
        echo "❌ Cannot connect to database. Please ensure PostgreSQL is running."
        echo ""
        echo "To start PostgreSQL:"
        echo "  brew services start postgresql@15"
        echo ""
        echo "Or use Docker:"
        echo "  docker-compose up -d postgis"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Running migrations...${NC}"
if $ARX_BIN migrate up; then
    echo -e "${GREEN}✓ Migrations complete${NC}"
else
    echo -e "${YELLOW}⚠ Migrations failed or already applied${NC}"
fi

echo ""
echo -e "${BLUE}Creating test building...${NC}"
BUILDING_OUTPUT=$($ARX_BIN building create \
    --name "Test School" \
    --address "123 Main Street" \
    2>&1 || echo "CREATE_FAILED")

if echo "$BUILDING_OUTPUT" | grep -q "CREATE_FAILED"; then
    echo -e "${YELLOW}⚠ Building creation needs review${NC}"
    echo "$BUILDING_OUTPUT"
else
    echo -e "${GREEN}✓ Building created${NC}"
    # Try to extract building ID from output
    BUILDING_ID=$(echo "$BUILDING_OUTPUT" | grep -oE 'ID: [a-zA-Z0-9-]+' | head -1 | cut -d' ' -f2 || echo "")
    if [ -n "$BUILDING_ID" ]; then
        echo "  Building ID: $BUILDING_ID"
    fi
fi

echo ""
echo -e "${BLUE}Testing path-based query infrastructure...${NC}"

# Check if path column exists in equipment table
if psql -h localhost -U joelpate -d arxos_dev -c "SELECT column_name FROM information_schema.columns WHERE table_name='equipment' AND column_name='path';" 2>/dev/null | grep -q "path"; then
    echo -e "${GREEN}✓ Path column exists in equipment table${NC}"
else
    echo -e "${YELLOW}⚠ Path column not found in equipment table${NC}"
    echo "  This may need migration 023_add_equipment_paths"
fi

# Check for path index
if psql -h localhost -U joelpate -d arxos_dev -c "SELECT indexname FROM pg_indexes WHERE tablename='equipment' AND indexname LIKE '%path%';" 2>/dev/null | grep -q "idx"; then
    echo -e "${GREEN}✓ Path index exists${NC}"
else
    echo -e "${YELLOW}⚠ Path index not found${NC}"
fi

echo ""
echo -e "${BLUE}Creating test BAS CSV file...${NC}"

# Create a sample BAS CSV file for testing
TEST_BAS_DIR="$PROJECT_ROOT/test_data/bas"
mkdir -p "$TEST_BAS_DIR"

cat > "$TEST_BAS_DIR/test_points.csv" << 'EOF'
Point Name,Object Type,Description,Address,Building,Floor,Room
AI-1-1,Analog Input,Room Temperature Sensor,12345,Main Building,1,101
AI-1-2,Analog Input,Room Temperature Sensor,12346,Main Building,1,102
DI-1-1,Digital Input,Door Status Sensor,12347,Main Building,1,101
AO-1-1,Analog Output,VAV Damper Position,12348,Main Building,1,101
DO-1-1,Digital Output,Light Control,12349,Main Building,1,102
AI-2-1,Analog Input,Room Temperature Sensor,12350,Main Building,2,201
AI-2-2,Analog Input,Room Temperature Sensor,12351,Main Building,2,202
DI-2-1,Digital Input,Occupancy Sensor,12352,Main Building,2,201
AO-2-1,Analog Output,VAV Damper Position,12353,Main Building,2,201
DO-2-1,Digital Output,Fan Control,12354,Main Building,2,202
EOF

echo -e "${GREEN}✓ Test BAS CSV created${NC}"
echo "  Location: $TEST_BAS_DIR/test_points.csv"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test Data Setup Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Test path queries: $ARX_BIN get --help"
echo "  2. Test BAS import: $ARX_BIN bas import $TEST_BAS_DIR/test_points.csv"
echo "  3. Run integration tests: go test ./test/integration/..."
echo ""

