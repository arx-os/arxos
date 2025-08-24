#!/bin/bash

# Arxos Cleanup Script
# Removes all generated files and stops services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Cleaning Arxos project...${NC}"

# Stop all services
echo -e "${YELLOW}Stopping all services...${NC}"
pkill -f "go run.*main.go" 2>/dev/null || true
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "python.*http.server" 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
echo -e "${GREEN}✓ Services stopped${NC}"

# Clean build artifacts
echo -e "${YELLOW}Removing build artifacts...${NC}"
rm -rf build/bin/* build/dist/* 2>/dev/null || true
rm -rf temp_uploads/* 2>/dev/null || true
rm -rf extraction_debug/* 2>/dev/null || true
echo -e "${GREEN}✓ Build artifacts removed${NC}"

# Clean Python cache
echo -e "${YELLOW}Removing Python cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Python cache removed${NC}"

# Clean logs (optional)
read -p "Remove log files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing log files...${NC}"
    rm -f logs/*.log 2>/dev/null || true
    rm -f ai_service/*.log 2>/dev/null || true
    rm -f core/backend/*.log 2>/dev/null || true
    echo -e "${GREEN}✓ Log files removed${NC}"
fi

# Clean test artifacts
echo -e "${YELLOW}Removing test artifacts...${NC}"
rm -f test_*.html test_*.py test_*.sh 2>/dev/null || true
rm -rf .pytest_cache 2>/dev/null || true
echo -e "${GREEN}✓ Test artifacts removed${NC}"

echo -e "${GREEN}✅ Cleanup complete!${NC}"