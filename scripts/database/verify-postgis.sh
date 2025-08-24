#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Verifying PostgreSQL/PostGIS Setup for Arxos...${NC}"

# Load environment variables
if [ -f "/Users/joelpate/repos/arxos/core/.env" ]; then
    export $(cat /Users/joelpate/repos/arxos/core/.env | grep -v '^#' | xargs)
fi

# Test PostgreSQL connection
echo -e "${YELLOW}Testing PostgreSQL connection...${NC}"
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" &>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL connection successful${NC}"
else
    echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
    exit 1
fi

# Verify PostGIS extension
echo -e "${YELLOW}Verifying PostGIS extension...${NC}"
POSTGIS_VERSION=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT PostGIS_version();" 2>/dev/null | xargs)
if [ -n "$POSTGIS_VERSION" ]; then
    echo -e "${GREEN}✓ PostGIS installed: $POSTGIS_VERSION${NC}"
else
    echo -e "${RED}✗ PostGIS not installed${NC}"
    exit 1
fi

# Check for spatial tables
echo -e "${YELLOW}Checking spatial tables...${NC}"
SPATIAL_TABLES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE data_type = 'USER-DEFINED' 
    AND udt_name = 'geometry';" | xargs)

if [ "$SPATIAL_TABLES" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $SPATIAL_TABLES spatial columns${NC}"
else
    echo -e "${YELLOW}⚠ No spatial columns found (migrations may not have run)${NC}"
fi

# Check for ArxObjects table
echo -e "${YELLOW}Checking ArxObjects table...${NC}"
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\d arx_objects" &>/dev/null; then
    echo -e "${GREEN}✓ ArxObjects table exists${NC}"
    
    # Check for spatial columns in ArxObjects
    GEOM_COLS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'arx_objects' 
        AND udt_name = 'geometry';" | xargs)
    
    if [ -n "$GEOM_COLS" ]; then
        echo -e "${GREEN}✓ Spatial columns in ArxObjects: $GEOM_COLS${NC}"
    else
        echo -e "${YELLOW}⚠ No spatial columns in ArxObjects (using coordinate columns)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ ArxObjects table not found (migrations may not have run)${NC}"
fi

# Check spatial indexes
echo -e "${YELLOW}Checking spatial indexes...${NC}"
SPATIAL_INDEXES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "
    SELECT COUNT(*) 
    FROM pg_indexes 
    WHERE indexdef LIKE '%gist%';" | xargs)

if [ "$SPATIAL_INDEXES" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $SPATIAL_INDEXES GIST spatial indexes${NC}"
else
    echo -e "${YELLOW}⚠ No GIST spatial indexes found${NC}"
fi

# Test spatial query capability
echo -e "${YELLOW}Testing spatial query capability...${NC}"
TEST_QUERY="SELECT ST_Distance(
    ST_SetSRID(ST_MakePoint(-73.935242, 40.730610), 4326),
    ST_SetSRID(ST_MakePoint(-73.935242, 40.730610), 4326)
) as distance;"

if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "$TEST_QUERY" &>/dev/null; then
    echo -e "${GREEN}✓ Spatial queries working${NC}"
else
    echo -e "${RED}✗ Spatial queries not working${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}PostgreSQL/PostGIS Verification Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Database Details:${NC}"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Database: $DB_NAME"
echo "  PostGIS: $POSTGIS_VERSION"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Run migrations: cd core && make migrate"
echo "2. Start the server: cd core && make run"
echo "3. For tests: make test-with-db"