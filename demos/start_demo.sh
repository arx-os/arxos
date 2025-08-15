#!/bin/bash

echo "🚀 Starting Arxos PDF Upload Demo"
echo "================================="
echo ""

# Start backend server
echo "Starting backend server..."
cd core/backend
go run . &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Check if server is running
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Backend server is running on http://localhost:8080"
else
    echo "⚠️  Backend might not be fully started, continuing anyway..."
fi

# Open frontend in browser
cd ../..
echo ""
echo "Opening PDF extractor in browser..."
open pdf_wall_extractor.html

echo ""
echo "================================="
echo "✅ Demo is ready!"
echo ""
echo "Instructions:"
echo "1. Upload a PDF floor plan using the upload zone"
echo "2. The system will automatically:"
echo "   - Extract walls using computer vision"
echo "   - Detect rooms from wall boundaries"
echo "   - Run OCR to extract room numbers"
echo "3. Click 'Export ArxObjects' to send to backend"
echo "4. Check browser console for upload response"
echo "5. Check backend logs for received data"
echo ""
echo "To stop the demo, press Ctrl+C"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping backend...'; kill $BACKEND_PID 2>/dev/null; exit" INT
wait $BACKEND_PID