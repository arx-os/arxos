#!/bin/bash
# ArxOS Database Setup - Terminal Only (No GUI needed)
# This script sets up PostgreSQL and PostGIS for ArxOS development

set -e  # Exit on any error

echo "🚀 ArxOS Database Setup"
echo "======================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if PostgreSQL is running
echo -e "${BLUE}Step 1: Checking PostgreSQL status...${NC}"
if pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not running${NC}"
    echo "Starting PostgreSQL..."
    brew services start postgresql@14
    sleep 3
    if pg_isready > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
        exit 1
    fi
fi
echo ""

# Step 2: Check PostgreSQL version
echo -e "${BLUE}Step 2: Checking PostgreSQL version...${NC}"
PG_VERSION=$(psql --version | grep -oE '[0-9]+' | head -1)
echo -e "${GREEN}✓ PostgreSQL ${PG_VERSION} detected${NC}"
echo ""

# Step 3: Create arxos database and user
echo -e "${BLUE}Step 3: Creating ArxOS database and user...${NC}"

# Connect as current user (usually has superuser privileges on Mac with Homebrew)
psql postgres <<SQL
-- Create arxos user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'arxos') THEN
        CREATE USER arxos WITH PASSWORD 'arxos_dev' CREATEDB;
        RAISE NOTICE 'Created user: arxos';
    ELSE
        RAISE NOTICE 'User arxos already exists';
    END IF;
END
\$\$;

-- Create arxos database if it doesn't exist
SELECT 'CREATE DATABASE arxos OWNER arxos'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'arxos')\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE arxos TO arxos;
SQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database 'arxos' created/verified${NC}"
    echo -e "${GREEN}✓ User 'arxos' created/verified${NC}"
else
    echo -e "${RED}✗ Failed to create database or user${NC}"
    exit 1
fi
echo ""

# Step 4: Install PostGIS extension
echo -e "${BLUE}Step 4: Installing PostGIS extension...${NC}"

# Check if PostGIS is installed on the system
if brew list | grep -q postgis; then
    echo -e "${GREEN}✓ PostGIS is installed via Homebrew${NC}"
else
    echo -e "${YELLOW}⚠ PostGIS not found. Installing...${NC}"
    brew install postgis
fi

# Enable PostGIS in the arxos database
psql arxos <<SQL
-- Create PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify PostGIS version
SELECT PostGIS_Version();
SQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PostGIS extension enabled${NC}"
else
    echo -e "${RED}✗ Failed to enable PostGIS${NC}"
    exit 1
fi
echo ""

# Step 5: Create test database (for running tests)
echo -e "${BLUE}Step 5: Creating test database...${NC}"

psql postgres <<SQL
-- Create arxos_test user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'arxos_test') THEN
        CREATE USER arxos_test WITH PASSWORD 'test_password' CREATEDB SUPERUSER;
        RAISE NOTICE 'Created user: arxos_test';
    ELSE
        RAISE NOTICE 'User arxos_test already exists';
    END IF;
END
\$\$;

-- Create arxos_test database if it doesn't exist
SELECT 'CREATE DATABASE arxos_test OWNER arxos_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'arxos_test')\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE arxos_test TO arxos_test;
SQL

# Enable PostGIS in test database
psql arxos_test <<SQL
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test database 'arxos_test' created/verified${NC}"
else
    echo -e "${YELLOW}⚠ Test database creation had warnings (this is usually okay)${NC}"
fi
echo ""

# Step 6: Verify database connection
echo -e "${BLUE}Step 6: Verifying database connections...${NC}"

# Test main database
if psql -U arxos -d arxos -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected to 'arxos' database as user 'arxos'${NC}"
else
    echo -e "${RED}✗ Failed to connect to 'arxos' database${NC}"
    exit 1
fi

# Test test database
if psql -U arxos_test -d arxos_test -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected to 'arxos_test' database as user 'arxos_test'${NC}"
else
    echo -e "${YELLOW}⚠ Could not connect to test database (this is okay for now)${NC}"
fi
echo ""

# Step 7: Display database info
echo -e "${BLUE}Step 7: Database Information${NC}"
echo "================================"

psql -U arxos -d arxos <<SQL
-- Show database size
SELECT pg_size_pretty(pg_database_size('arxos')) as database_size;

-- Show tables (will be empty before migrations)
\dt

-- Show PostGIS version
SELECT PostGIS_Version() as postgis_version;
SQL

echo ""

# Step 8: Export environment variables
echo -e "${BLUE}Step 8: Environment Variables${NC}"
echo "================================"
echo ""
echo "Add these to your ~/.bashrc or ~/.zshrc:"
echo ""
echo -e "${YELLOW}# ArxOS Database Configuration${NC}"
echo -e "${YELLOW}export ARXOS_DB_HOST=localhost${NC}"
echo -e "${YELLOW}export ARXOS_DB_PORT=5432${NC}"
echo -e "${YELLOW}export ARXOS_DB_NAME=arxos${NC}"
echo -e "${YELLOW}export ARXOS_DB_USER=arxos${NC}"
echo -e "${YELLOW}export ARXOS_DB_PASSWORD=arxos_dev${NC}"
echo -e "${YELLOW}export DATABASE_URL=\"postgres://arxos:arxos_dev@localhost:5432/arxos?sslmode=disable\"${NC}"
echo ""
echo "Or run them now for this session:"
echo ""
cat > /tmp/arxos_env.sh <<'ENV'
export ARXOS_DB_HOST=localhost
export ARXOS_DB_PORT=5432
export ARXOS_DB_NAME=arxos
export ARXOS_DB_USER=arxos
export ARXOS_DB_PASSWORD=arxos_dev
export DATABASE_URL="postgres://arxos:arxos_dev@localhost:5432/arxos?sslmode=disable"
ENV

echo -e "${GREEN}source /tmp/arxos_env.sh${NC}"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Database Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Source environment variables: ${BLUE}source /tmp/arxos_env.sh${NC}"
echo "2. Run ArxOS migrations: ${BLUE}go run cmd/arx/main.go migrate up${NC}"
echo "3. Test database: ${BLUE}go run cmd/arx/main.go health${NC}"
echo ""
echo "Useful commands:"
echo "  Connect to database: ${BLUE}psql -U arxos -d arxos${NC}"
echo "  List databases: ${BLUE}psql -l${NC}"
echo "  Check status: ${BLUE}pg_isready${NC}"
echo "  View tables: ${BLUE}psql -U arxos -d arxos -c '\\dt'${NC}"
echo ""

