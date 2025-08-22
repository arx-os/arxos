#!/bin/bash

echo "🚀 Starting Arxos Demo..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.${NC}"
    exit 1
fi

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo -e "${RED}Go is not installed. Please install Go.${NC}"
    exit 1
fi

# Start AI Service
echo -e "${YELLOW}Starting AI Service...${NC}"
cd ai_service

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install fastapi uvicorn pdfplumber pillow opencv-python-headless numpy pydantic
}

# Start AI service in background
echo -e "${GREEN}Starting AI service on port 5000...${NC}"
python main.py &
AI_PID=$!

# Give AI service time to start
sleep 2

# Start Go Backend
cd ../core/backend
echo -e "${YELLOW}Starting Go backend...${NC}"

# Check if Go modules are initialized
if [ ! -f "go.mod" ]; then
    echo "Initializing Go modules..."
    go mod init arxos-backend
    go get github.com/go-chi/chi/v5
    go get github.com/rs/cors
fi

# Build and run backend
echo -e "${GREEN}Starting backend on port 8080...${NC}"
go run main.go &
BACKEND_PID=$!

# Give backend time to start
sleep 2

# Open browser
echo -e "${GREEN}Opening Arxos Demo in browser...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    open ../../arxos_demo.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open ../../arxos_demo.html
fi

echo ""
echo -e "${GREEN}✅ Arxos Demo is running!${NC}"
echo ""
echo "Services:"
echo "  - AI Service: http://localhost:5000"
echo "  - Backend API: http://localhost:8080"
echo "  - Demo UI: file://$(pwd)/../../arxos_demo.html"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
trap "echo ''; echo 'Stopping services...'; kill $AI_PID $BACKEND_PID 2>/dev/null; exit" INT
wait