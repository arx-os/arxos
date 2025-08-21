#!/bin/bash

# Arxos Startup Script - Runs both AI service and Go backend
# This ensures the PDF processing works correctly

set -e

echo "🏗️ Starting Arxos Services..."

# Check if Python AI service dependencies are installed
if [ ! -d "ai_service/venv" ]; then
    echo "📦 Setting up Python virtual environment..."
    cd ai_service
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Python environment ready"
fi

# Start the Python AI service in background
echo "🤖 Starting AI service on port 8000..."
cd ai_service
source venv/bin/activate
python main.py &
AI_PID=$!
cd ..

# Wait for AI service to be ready
echo "⏳ Waiting for AI service to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ AI service is ready"
        break
    fi
    sleep 1
done

# Set environment variables for Go backend
export AI_SERVICE_URL="http://localhost:8000"
export DEFAULT_BUILDING_TYPE="school"  # For Alafia Elementary testing

# Build and start Go backend
echo "🔨 Building Go backend..."
cd core/backend
go build -o arxos_server main.go

echo "🚀 Starting Go backend on port 8080..."
./arxos_server &
GO_PID=$!

echo ""
echo "✨ Arxos is running!"
echo "   - Web Interface: http://localhost:8080"
echo "   - AI Service: http://localhost:8000/api/docs"
echo "   - Backend API: http://localhost:8080/api/health"
echo ""
echo "🌐 Open http://localhost:8080 in your browser to upload PDFs and view BIM"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Arxos services..."
    kill $AI_PID 2>/dev/null || true
    kill $GO_PID 2>/dev/null || true
    echo "👋 Arxos stopped"
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Wait for processes
wait