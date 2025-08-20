#!/bin/bash

echo "🛑 Stopping Arxos Services..."
echo "================================"

# Stop Python AI Service
echo "Stopping Python AI Service..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ AI Service stopped"
else
    echo "⚠️ AI Service was not running"
fi

# Stop Go Backend
echo "Stopping Go Backend..."
lsof -ti:8080 | xargs kill -9 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backend stopped"
else
    echo "⚠️ Backend was not running"
fi

echo ""
echo "All services stopped."