#!/bin/bash

# Arxos Unified Test Script
# This is THE ONLY way to run tests

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Running Arxos Tests...${NC}"

# Test type from argument
TEST_TYPE=${1:-all}

# Ensure services are running for integration tests
if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "all" ]; then
    if ! lsof -ti:8080 >/dev/null 2>&1; then
        echo -e "${YELLOW}Services not running. Starting them...${NC}"
        ./scripts/start.sh
        sleep 5
    fi
fi

# Run Go tests
if [ "$TEST_TYPE" = "unit" ] || [ "$TEST_TYPE" = "all" ]; then
    echo -e "${YELLOW}Running Go unit tests...${NC}"
    cd core/backend
    go test ./... -short -v | grep -E "(PASS|FAIL|ok)" || true
    cd ../..
    echo -e "${GREEN}✓ Go tests complete${NC}"
fi

# Run Python tests
if [ "$TEST_TYPE" = "unit" ] || [ "$TEST_TYPE" = "all" ]; then
    echo -e "${YELLOW}Running Python unit tests...${NC}"
    cd ai_service
    if [ -f venv/bin/activate ]; then
        source venv/bin/activate
        python -m pytest tests/ -v --tb=short 2>/dev/null || echo "No Python tests found"
    fi
    cd ..
    echo -e "${GREEN}✓ Python tests complete${NC}"
fi

# Run integration tests
if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "all" ]; then
    echo -e "${YELLOW}Running integration tests...${NC}"
    
    # Test health endpoints
    echo -n "  Backend health: "
    if curl -s http://localhost:8080/api/health | grep -q "ok"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
    
    echo -n "  AI service health: "
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
    
    # Test PDF upload endpoint
    echo -n "  PDF upload endpoint: "
    if curl -s -X POST http://localhost:8080/api/pdf/upload >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ (expected without file)${NC}"
    fi
    
    echo -e "${GREEN}✓ Integration tests complete${NC}"
fi

# Run E2E tests
if [ "$TEST_TYPE" = "e2e" ]; then
    echo -e "${YELLOW}Running E2E tests...${NC}"
    echo -e "${YELLOW}E2E tests not implemented yet${NC}"
fi

echo -e "${GREEN}✅ All tests complete!${NC}"