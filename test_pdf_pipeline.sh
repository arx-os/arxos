#!/bin/bash

# Test script for PDF to ArxObject to SVG pipeline
# This helps verify each step is working correctly

echo "🚀 Arxos PDF Pipeline Test"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python AI service is running
echo -e "\n${YELLOW}1. Checking Python AI Service...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health | grep -q "200"; then
    echo -e "${GREEN}✓ AI Service is running on port 5000${NC}"
else
    echo -e "${RED}✗ AI Service not running. Starting it...${NC}"
    cd ai_service
    python main.py &
    AI_PID=$!
    sleep 3
    cd ..
fi

# Check if Go backend is running
echo -e "\n${YELLOW}2. Checking Go Backend...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health | grep -q "200"; then
    echo -e "${GREEN}✓ Go Backend is running on port 8080${NC}"
else
    echo -e "${RED}✗ Go Backend not running. Starting it...${NC}"
    cd core/backend
    go run main.go &
    GO_PID=$!
    sleep 3
    cd ../..
fi

# Test PDF upload with a sample file
echo -e "\n${YELLOW}3. Testing PDF Upload...${NC}"
if [ -f "test.pdf" ]; then
    echo "Using test.pdf for upload test..."
    
    # Upload the PDF
    RESPONSE=$(curl -s -X POST \
        -F "file=@test.pdf" \
        http://localhost:8080/upload/pdf)
    
    # Check if we got ArxObjects back
    if echo "$RESPONSE" | grep -q "arxobjects"; then
        OBJECT_COUNT=$(echo "$RESPONSE" | grep -o '"id"' | wc -l)
        echo -e "${GREEN}✓ Successfully extracted $OBJECT_COUNT ArxObjects${NC}"
        
        # Save response for inspection
        echo "$RESPONSE" | python -m json.tool > test_response.json
        echo "Response saved to test_response.json"
    else
        echo -e "${RED}✗ No ArxObjects extracted${NC}"
        echo "Response: $RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠ No test.pdf found. Please provide a test PDF.${NC}"
fi

# Open the frontend
echo -e "\n${YELLOW}4. Opening Frontend...${NC}"
if [ -f "frontend/index.html" ]; then
    echo -e "${GREEN}✓ Frontend available at: file://$(pwd)/frontend/index.html${NC}"
    
    # Try to open in browser (works on Mac)
    if command -v open &> /dev/null; then
        open frontend/index.html
    fi
else
    echo -e "${RED}✗ Frontend not found${NC}"
fi

echo -e "\n${GREEN}Pipeline test complete!${NC}"
echo "Next steps:"
echo "1. Upload a PDF through the web interface"
echo "2. Check browser console for any errors"
echo "3. Verify ArxObjects are rendering correctly"

# Keep script running if we started services
if [ ! -z "$AI_PID" ] || [ ! -z "$GO_PID" ]; then
    echo -e "\n${YELLOW}Press Ctrl+C to stop services${NC}"
    wait
fi