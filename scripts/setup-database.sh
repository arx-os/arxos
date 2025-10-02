#!/bin/bash

# ArxOS Database Setup Script
# This script sets up PostgreSQL with PostGIS for local development

set -e

echo "🚀 Setting up ArxOS Database..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL is not installed${NC}"
    echo "Please install PostgreSQL first:"
    echo "  macOS: brew install postgresql postgis"
    echo "  Ubuntu: sudo apt-get install postgresql postgresql-contrib postgis"
    exit 1
fi

# Check if PostGIS is available
if ! psql -d postgres -c "SELECT 1 FROM pg_available_extensions WHERE name = 'postgis';" | grep -q "1"; then
    echo -e "${RED}❌ PostGIS extension is not available${NC}"
    echo "Please install PostGIS:"
    echo "  macOS: brew install postgis"
    echo "  Ubuntu: sudo apt-get install postgis"
    exit 1
fi

# Database configuration
DB_NAME="arxos"
DB_USER="arxos"
DB_PASSWORD="arxos_dev_password"
DB_HOST="localhost"
DB_PORT="5432"

echo -e "${YELLOW}📋 Database Configuration:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"

# Create database and user
echo -e "${YELLOW}🔧 Creating database and user...${NC}"

# Connect as postgres superuser to create database and user
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
EOF

echo -e "${GREEN}✅ Database and user created successfully${NC}"

# Connect to the new database and set up PostGIS
echo -e "${YELLOW}🗺️ Setting up PostGIS extensions...${NC}"

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF
-- Enable PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Verify PostGIS installation
SELECT PostGIS_Version();
EOF

echo -e "${GREEN}✅ PostGIS extensions enabled successfully${NC}"

# Run database migrations
echo -e "${YELLOW}📊 Running database migrations...${NC}"

# Check if migrations directory exists
if [ ! -d "internal/migrations" ]; then
    echo -e "${RED}❌ Migrations directory not found${NC}"
    exit 1
fi

# Run migrations using the ArxOS CLI
echo "Running migrations with ArxOS CLI..."
cd "$(dirname "$0")/.."

# Set environment variables for the CLI
export ARXOS_DATABASE_URL="postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=disable"
export ARXOS_ENV="development"

# Run migrations
if command -v ./arx &> /dev/null; then
    ./arx migrate up
else
    echo -e "${YELLOW}⚠️ ArxOS CLI not found, building it first...${NC}"
    go build -o arx ./cmd/arx
    ./arx migrate up
fi

echo -e "${GREEN}✅ Database migrations completed successfully${NC}"

# Test database connection
echo -e "${YELLOW}🧪 Testing database connection...${NC}"

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF
-- Test basic connection
SELECT 'Database connection successful' as status;

-- Test PostGIS functionality
SELECT ST_AsText(ST_Point(0, 0)) as test_point;

-- Show installed extensions
SELECT extname, extversion FROM pg_extension WHERE extname LIKE 'postgis%';
EOF

echo -e "${GREEN}✅ Database connection test successful${NC}"

# Create environment file
echo -e "${YELLOW}📝 Creating environment configuration...${NC}"

cat > .env << EOF
# ArxOS Development Environment Configuration
ARXOS_ENV=development
ARXOS_DATABASE_URL=postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=disable
ARXOS_JWT_SECRET=dev_jwt_secret_key_change_in_production
ARXOS_LOG_LEVEL=debug
ARXOS_API_PORT=8080
ARXOS_CACHE_ENABLED=true
ARXOS_CACHE_REDIS_URL=redis://localhost:6379
EOF

echo -e "${GREEN}✅ Environment configuration created${NC}"

echo -e "${GREEN}🎉 ArxOS Database Setup Complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Start the ArxOS API server: ./arx serve"
echo "2. Test the API: curl http://localhost:8080/api/v1/health"
echo "3. Check database: psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo ""
echo -e "${YELLOW}🔧 Database Connection String:${NC}"
echo "postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=disable"
