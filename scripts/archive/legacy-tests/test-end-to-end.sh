#!/bin/bash

# ArxOS End-to-End Test Script
# This script tests the complete flow: CLI → API → Database → Mobile

set -e

echo "🧪 Starting ArxOS End-to-End Test..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:8080"
DB_URL="postgres://arxos:arxos_dev_password@localhost:5432/arxos?sslmode=disable"

echo -e "${BLUE}📋 Test Configuration:${NC}"
echo "  API URL: $API_URL"
echo "  Database: $DB_URL"
echo ""

# Test 1: Database Connection
echo -e "${YELLOW}🔍 Test 1: Database Connection${NC}"
if PGPASSWORD=arxos_dev_password psql -h localhost -p 5432 -U arxos -d arxos -c "SELECT 'Database connection successful' as status;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    echo "Please run: ./scripts/setup-database.sh"
    exit 1
fi

# Test 2: Build ArxOS CLI
echo -e "${YELLOW}🔨 Test 2: Building ArxOS CLI${NC}"
cd "$(dirname "$0")/.."

if go build -o arx ./cmd/arx; then
    echo -e "${GREEN}✅ ArxOS CLI built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build ArxOS CLI${NC}"
    exit 1
fi

# Test 3: Health Check
echo -e "${YELLOW}🏥 Test 3: Health Check${NC}"
if ./arx health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

# Test 4: Start API Server (in background)
echo -e "${YELLOW}🚀 Test 4: Starting API Server${NC}"

# Set environment variables
export ARXOS_DATABASE_URL="$DB_URL"
export ARXOS_ENV="development"
export ARXOS_JWT_SECRET="dev_jwt_secret_key_change_in_production"
export ARXOS_LOG_LEVEL="debug"
export ARXOS_API_PORT="8080"

# Start server in background
./arx serve --port 8080 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Test 5: API Health Endpoint
echo -e "${YELLOW}🌐 Test 5: API Health Endpoint${NC}"
if curl -s "$API_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ API health endpoint responding${NC}"
else
    echo -e "${RED}❌ API health endpoint failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test 6: API Building Endpoints
echo -e "${YELLOW}🏢 Test 6: API Building Endpoints${NC}"

# Test list buildings
if curl -s "$API_URL/api/v1/buildings" | grep -q "buildings"; then
    echo -e "${GREEN}✅ List buildings endpoint working${NC}"
else
    echo -e "${RED}❌ List buildings endpoint failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test create building
BUILDING_DATA='{"name":"Test Building","address":"123 Test St","building_type":"office"}'
if curl -s -X POST -H "Content-Type: application/json" -d "$BUILDING_DATA" "$API_URL/api/v1/buildings" | grep -q "name"; then
    echo -e "${GREEN}✅ Create building endpoint working${NC}"
else
    echo -e "${RED}❌ Create building endpoint failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test 7: Database Integration
echo -e "${YELLOW}🗄️ Test 7: Database Integration${NC}"
if PGPASSWORD=arxos_dev_password psql -h localhost -p 5432 -U arxos -d arxos -c "SELECT COUNT(*) FROM buildings;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database integration working${NC}"
else
    echo -e "${RED}❌ Database integration failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test 8: Mobile API Compatibility
echo -e "${YELLOW}📱 Test 8: Mobile API Compatibility${NC}"
if curl -s -H "Accept: application/json" "$API_URL/api/v1/buildings" | grep -q "buildings"; then
    echo -e "${GREEN}✅ Mobile API compatibility confirmed${NC}"
else
    echo -e "${RED}❌ Mobile API compatibility failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Cleanup
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
kill $SERVER_PID 2>/dev/null || true
sleep 2

echo ""
echo -e "${GREEN}🎉 All End-to-End Tests Passed!${NC}"
echo ""
echo -e "${BLUE}📋 Test Summary:${NC}"
echo "  ✅ Database Connection"
echo "  ✅ CLI Build"
echo "  ✅ Health Check"
echo "  ✅ API Server Start"
echo "  ✅ API Health Endpoint"
echo "  ✅ Building Endpoints"
echo "  ✅ Database Integration"
echo "  ✅ Mobile API Compatibility"
echo ""
echo -e "${BLUE}🚀 ArxOS is ready for development!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Start the server: ./arx serve"
echo "2. Test the API: curl http://localhost:8080/api/v1/buildings"
echo "3. Check the mobile app: cd mobile && npm start"
echo "4. Import IFC files: ./arx import <file.ifc>"
