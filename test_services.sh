#!/bin/bash

echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "python.*main.py" 2>/dev/null
pkill -f "go run main.go" 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

sleep 2

echo "🚀 Starting AI Service on port 8000..."
cd ai_service
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &
AI_PID=$!
cd ..

sleep 3

echo "🚀 Starting Go Backend on port 8080..."
cd core/backend
go run main.go &
BACKEND_PID=$!
cd ../..

sleep 2

echo "✅ Services started!"
echo "   AI Service PID: $AI_PID (port 8000)"
echo "   Backend PID: $BACKEND_PID (port 8080)"
echo ""
echo "Testing endpoints..."

# Test AI service health
echo -n "AI Service health: "
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ OK" || echo "❌ Failed"

# Test backend health
echo -n "Backend health: "
curl -s http://localhost:8080/api/health | grep -q "ok" && echo "✅ OK" || echo "❌ Failed"

echo ""
echo "Services are running. Press Ctrl+C to stop."
echo "Open arxos_demo.html in your browser to test."

trap "kill $AI_PID $BACKEND_PID 2>/dev/null; exit" INT
wait