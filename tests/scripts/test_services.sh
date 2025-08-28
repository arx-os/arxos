#!/bin/bash

# Test all ArxOS services
set -e

echo "=== ArxOS Services Status Check ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local name=$1
    local check_cmd=$2
    
    echo -n "Checking $name... "
    if eval $check_cmd 2>/dev/null; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Track overall status
ALL_GOOD=true

# Core services
echo "Core Services:"
check_service "Go Backend (8080)" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health | grep -q 200" || ALL_GOOD=false
check_service "Python AI Service (50051)" "nc -zv localhost 50051 2>&1 | grep -q succeeded" || ALL_GOOD=false
echo

# Supporting services
echo "Supporting Services:"
check_service "PostgreSQL (5432)" "pg_isready -h localhost -p 5432 -q" || true
check_service "Redis (6379)" "redis-cli -p 6379 ping | grep -q PONG" || true
echo

# Docker containers
echo "Docker Containers:"
if command -v docker &> /dev/null; then
    echo "Active containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "arxos|backend|ai-service|postgres|redis" || echo "  No ArxOS containers running"
else
    echo -e "${YELLOW}Docker not installed${NC}"
fi
echo

# Quick start commands
echo "Quick Start Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━"
echo "Start all services:     docker-compose up -d"
echo "Start backend only:     cd core && go run cmd/server/main.go"
echo "Start AI service:       cd ai_services && python grpc_server.py"
echo "View logs:             docker-compose logs -f"
echo "Stop all:              docker-compose down"
echo

# Overall status
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✅ All core services are running!${NC}"
    echo "Ready to process PDFs: ./test_ingestion.sh [path-to-pdf]"
else
    echo -e "${YELLOW}⚠️  Some services are not running${NC}"
    echo "Start them with: docker-compose up -d"
fi
echo