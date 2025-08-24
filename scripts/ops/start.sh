#!/bin/bash

# Arxos Unified Start Script
# This is THE ONLY way to start services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting Arxos Services...${NC}"

# Clean up any existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "go run.*main.go" 2>/dev/null || true
pkill -f "uvicorn.*main:app" 2>/dev/null || true
pkill -f "python.*http.server" 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

sleep 2

# Start Backend
echo -e "${YELLOW}Starting Backend (port 8080)...${NC}"
cd core/backend
go run main.go > ../../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ../..
sleep 2

# Check backend started
if lsof -ti:8080 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend started${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    exit 1
fi

# Start AI Service
echo -e "${YELLOW}Starting AI Service (port 8000)...${NC}"
cd ai_service
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/ai_service.log 2>&1 &
    AI_PID=$!
else
    echo -e "${RED}Python venv not found. Run 'make setup' first.${NC}"
    exit 1
fi
cd ..
sleep 3

# Check AI service started
if lsof -ti:8000 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ AI Service started${NC}"
else
    echo -e "${RED}✗ AI Service failed to start${NC}"
    exit 1
fi

# Start Frontend Server
echo -e "${YELLOW}Starting Frontend (port 3000)...${NC}"
python3 -m http.server 3000 --directory . > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 1

# Check frontend started
if lsof -ti:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend started${NC}"
else
    echo -e "${RED}✗ Frontend failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All services started successfully!${NC}"
echo ""
echo "Service URLs:"
echo "  Backend:    http://localhost:8080"
echo "  AI Service: http://localhost:8000"
echo "  Demo:       http://localhost:3000/demo"
echo ""
echo "Run 'make demo' to open the demo"
echo "Run 'make logs' to see service logs"
echo "Run 'make stop' to stop all services"