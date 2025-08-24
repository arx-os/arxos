#!/bin/bash

# ARXOS ArxObject Pipeline Test Script
# This script validates the complete ArxObject creation and storage pipeline

echo "🚀 ARXOS ArxObject Pipeline Validation"
echo "======================================"
echo ""

# Configuration
BACKEND_URL="http://localhost:8080"
AI_SERVICE_URL="http://localhost:5000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2
    local expected_status=$3
    
    echo "Testing: $description"
    echo "Endpoint: $endpoint"
    
    response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL$endpoint")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_status" ]; then
        print_status "SUCCESS" "HTTP $http_code - $description"
        echo "Response: $body" | jq '.' 2>/dev/null || echo "Response: $body"
    else
        print_status "ERROR" "HTTP $http_code (expected $expected_status) - $description"
        echo "Response: $body"
    fi
    echo ""
}

# Check if backend is running
echo "🔍 Checking Backend Status..."
if curl -s "$BACKEND_URL/api/health" > /dev/null 2>&1; then
    print_status "SUCCESS" "Backend is running on $BACKEND_URL"
else
    print_status "ERROR" "Backend is not running on $BACKEND_URL"
    echo "Please start the backend server first:"
    echo "  cd core/backend && go run main.go"
    exit 1
fi

echo ""

# Test 1: Basic Health Check
echo "📋 Test 1: Basic Health Check"
test_endpoint "/api/health" "Health Check" "200"

# Test 2: Database Connection
echo "📋 Test 2: Database Connection"
test_endpoint "/api/test/db" "Database Connection Test" "200"

# Test 3: ArxObject Pipeline
echo "📋 Test 3: ArxObject Pipeline"
test_endpoint "/api/test/arxobject-pipeline" "ArxObject Pipeline Test" "200"

# Test 4: AI Service Integration (Mock)
echo "📋 Test 4: AI Service Integration (Mock)"
test_endpoint "/api/test/ai-integration" "AI Service Integration Test" "200"

# Test 5: Check AI Service (if running)
echo "📋 Test 5: AI Service Status"
if curl -s "$AI_SERVICE_URL/health" > /dev/null 2>&1; then
    print_status "SUCCESS" "AI Service is running on $AI_SERVICE_URL"
else
    print_status "WARNING" "AI Service is not running on $AI_SERVICE_URL"
    echo "This is expected if you haven't started the AI service yet."
    echo "The mock tests will still work to validate the backend pipeline."
fi

echo ""

# Summary
echo "🎯 Test Summary"
echo "==============="
echo "All tests completed. Check the results above."
echo ""
echo "Next Steps:"
echo "1. If all tests pass, your ArxObject pipeline is working correctly"
echo "2. If any tests fail, check the error messages and database configuration"
echo "3. Once validated, you can test with real PDF uploads"
echo ""
echo "To test with a real PDF:"
echo "  curl -X POST -F 'file=@your_floorplan.pdf' $BACKEND_URL/api/pdf/upload"
echo ""
echo "Happy testing! 🚀"
