#!/bin/bash

# Enhanced Pipeline Test Script
# Tests the improved PDF to BIM conversion

echo "🏗️  Arxos Enhanced Pipeline Test"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check Python AI Service
echo -e "\n${YELLOW}Step 1: Starting Python AI Service...${NC}"

# Check if already running
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ AI Service already running on port 5000${NC}"
else
    echo "Starting AI service..."
    cd ai_service
    python main.py > ../logs/ai_service.log 2>&1 &
    AI_PID=$!
    echo "AI Service PID: $AI_PID"
    cd ..
    
    # Wait for service to start
    echo "Waiting for AI service to start..."
    for i in {1..10}; do
        if curl -s http://localhost:5000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✓ AI Service started successfully${NC}"
            break
        fi
        sleep 1
    done
fi

# Step 2: Check Go Backend
echo -e "\n${YELLOW}Step 2: Starting Go Backend...${NC}"

# Check if already running
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Go Backend already running on port 8080${NC}"
else
    echo "Building and starting Go backend..."
    cd core/backend
    
    # Build first to check for errors
    echo "Building backend..."
    if go build -o ../../arxos_backend main.go; then
        echo -e "${GREEN}✓ Backend built successfully${NC}"
        
        # Run the backend
        ../../arxos_backend > ../../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo "Backend PID: $BACKEND_PID"
        cd ../..
        
        # Wait for backend to start
        echo "Waiting for backend to start..."
        for i in {1..10}; do
            if curl -s http://localhost:8080/api/health >/dev/null 2>&1; then
                echo -e "${GREEN}✓ Backend started successfully${NC}"
                break
            fi
            sleep 1
        done
    else
        echo -e "${RED}✗ Backend build failed. Check for compilation errors.${NC}"
        cd ../..
        exit 1
    fi
fi

# Step 3: Open Frontend
echo -e "\n${YELLOW}Step 3: Opening Frontend...${NC}"

FRONTEND_PATH="file://$(pwd)/frontend/index.html"
echo -e "${BLUE}Frontend URL: $FRONTEND_PATH${NC}"

# Try to open in default browser (Mac)
if command -v open &> /dev/null; then
    open "$FRONTEND_PATH"
    echo -e "${GREEN}✓ Frontend opened in browser${NC}"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "$FRONTEND_PATH"
    echo -e "${GREEN}✓ Frontend opened in browser${NC}"
else
    echo "Please open this URL in your browser:"
    echo "$FRONTEND_PATH"
fi

# Step 4: Provide test instructions
echo -e "\n${YELLOW}Step 4: Testing Instructions${NC}"
echo "=============================="
echo ""
echo "1. In the browser window that just opened:"
echo "   - Click 'Upload PDF' button"
echo "   - Select your Alafia_ES_IDF_CallOut.pdf"
echo ""
echo "2. Watch for:"
echo "   ✓ Status message showing processing"
echo "   ✓ Building renders with walls"
echo "   ✓ Statistics showing object count"
echo "   ✓ Confidence coloring (green/yellow/red)"
echo ""
echo "3. Use controls:"
echo "   - Mouse drag to pan"
echo "   - Scroll to zoom"
echo "   - '+/-' buttons for zoom"
echo "   - '⊡' to fit to view"
echo ""
echo "4. Check improvements:"
echo "   - Walls should be continuous (not fragmented)"
echo "   - Rooms should be detected (if closed loops exist)"
echo "   - Scale should match PDF (1:1)"
echo ""

# Step 5: Monitor logs
echo -e "${YELLOW}Step 5: Monitoring Services${NC}"
echo "============================"
echo ""
echo "Logs are being written to:"
echo "  - AI Service: logs/ai_service.log"
echo "  - Backend: logs/backend.log"
echo ""
echo -e "${BLUE}Tail logs in real-time:${NC}"
echo "  tail -f logs/ai_service.log"
echo "  tail -f logs/backend.log"
echo ""

# Step 6: Test with curl (optional)
echo -e "${YELLOW}Step 6: Quick API Test${NC}"
echo "======================"

# Test health endpoints
echo -n "AI Service Health: "
if curl -s http://localhost:5000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

echo -n "Backend Health: "
if curl -s http://localhost:8080/api/health | grep -q "ok"; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

# Provide sample curl command for manual testing
echo ""
echo -e "${BLUE}Manual upload test with curl:${NC}"
echo 'curl -X POST -F "file=@Alafia_ES_IDF_CallOut.pdf" http://localhost:8080/api/v1/upload/pdf'
echo ""

# Keep script running
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}Pipeline is ready for testing!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Trap Ctrl+C to cleanup
cleanup() {
    echo -e "\n${YELLOW}Stopping services...${NC}"
    
    if [ ! -z "$AI_PID" ]; then
        kill $AI_PID 2>/dev/null
        echo "Stopped AI service"
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "Stopped backend"
    fi
    
    # Also try to stop by port in case PIDs are lost
    lsof -ti:5000 | xargs kill 2>/dev/null
    lsof -ti:8080 | xargs kill 2>/dev/null
    
    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}

trap cleanup INT

# Keep script running
while true; do
    sleep 1
done