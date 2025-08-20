#!/bin/bash

# Start Arxos Services
echo "🚀 Starting Arxos Services..."
echo "================================"

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Go environment
if ! command -v go &> /dev/null; then
    echo "❌ Go not found. Please install Go 1.19+"
    exit 1
fi

# Kill any existing services
echo "🔄 Stopping any existing services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start Python AI Service
echo ""
echo "1️⃣ Starting Python AI Service on port 8000..."
cd ai_service

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install requirements
source venv/bin/activate
pip install -q -r requirements.txt

# Start AI service in background
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
nohup python main.py > ../logs/ai_service.log 2>&1 &
AI_PID=$!
echo "   ✅ AI Service started (PID: $AI_PID)"

# Wait for AI service to be ready
sleep 3
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ AI Service is healthy"
else
    echo "   ⚠️ AI Service may not be ready yet"
fi

# Start Go Backend
echo ""
echo "2️⃣ Starting Go Backend on port 8080..."
cd ../core/backend

# Set environment variables
export USE_AI_PDF_PROCESSOR=true
export AI_SERVICE_URL=http://localhost:8000

# Build and run Go backend
go build -o arxos_server
nohup ./arxos_server > ../../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
sleep 3
if curl -s http://localhost:8080/health > /dev/null; then
    echo "   ✅ Backend is healthy"
else
    echo "   ⚠️ Backend may not be ready yet"
fi

echo ""
echo "================================"
echo "✅ All services started!"
echo ""
echo "Services running:"
echo "  - Python AI Service: http://localhost:8000"
echo "  - Go Backend: http://localhost:8080"
echo ""
echo "View logs:"
echo "  - AI Service: tail -f logs/ai_service.log"
echo "  - Backend: tail -f logs/backend.log"
echo ""
echo "Test PDF upload:"
echo "  1. Open test_pdf_batch.html in browser"
echo "  2. Upload a PDF floor plan"
echo "  3. Click 'Process' to extract building elements"
echo ""
echo "To stop services: ./stop_services.sh"