#!/bin/bash

# Local test server for Arxos PDF processing
# Works with real PDF files

echo "🧪 Arxos Local Test Environment"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for PDF test files
echo "📁 Checking for test PDFs..."
PDF_COUNT=$(find . -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')

if [ "$PDF_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Found $PDF_COUNT PDF files:"
    find . -name "*.pdf" -type f 2>/dev/null | head -5 | while read pdf; do
        SIZE=$(du -h "$pdf" | cut -f1)
        echo "  - $(basename "$pdf") ($SIZE)"
    done
    if [ "$PDF_COUNT" -gt 5 ]; then
        echo "  ... and $((PDF_COUNT - 5)) more"
    fi
else
    echo -e "${YELLOW}⚠${NC} No PDF files found in current directory"
fi

echo ""
echo "🚀 Starting services..."
echo "------------------------"

# Start backend server
echo -n "Starting backend server... "
cd core/backend 2>/dev/null || {
    echo -e "${RED}✗${NC} Backend directory not found"
    exit 1
}

# Kill any existing backend on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start backend
go run . > /tmp/arxos-backend.log 2>&1 &
BACKEND_PID=$!
sleep 2

if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Running on http://localhost:8080 (PID: $BACKEND_PID)"
else
    echo -e "${RED}✗${NC} Failed to start"
    echo "Check logs: tail -f /tmp/arxos-backend.log"
    exit 1
fi

# Go back to root
cd ../..

# Start Go HTTP server for frontend
echo -n "Starting frontend server... "
go run test_server.go > /tmp/arxos-frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 1

if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Running on http://localhost:3000 (PID: $FRONTEND_PID)"
else
    echo -e "${RED}✗${NC} Failed to start"
    exit 1
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ Test environment ready!${NC}"
echo ""
echo "📋 Quick Test URLs:"
echo "  • PDF Extractor: http://localhost:3000/pdf_wall_extractor.html"
echo "  • Backend Health: http://localhost:8080/health"
echo "  • Upload Endpoint: POST http://localhost:8080/api/buildings/upload"
echo ""
echo "🧪 Test Your PDFs:"
echo "  1. Open http://localhost:3000/pdf_wall_extractor.html"
echo "  2. Upload any of your test PDFs"
echo "  3. Watch the extraction process"
echo "  4. Check OCR results for room numbers"
echo "  5. Export to see the ArxObjects"
echo ""
echo "📊 Monitor Logs:"
echo "  • Backend: tail -f /tmp/arxos-backend.log"
echo "  • Frontend: tail -f /tmp/arxos-frontend.log"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Services stopped."
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Keep script running and show logs
echo "📝 Live Backend Logs:"
echo "----------------------"
tail -f /tmp/arxos-backend.log