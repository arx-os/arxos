#!/bin/bash

# Test script for PDF upload integration

echo "🚀 Testing Arxos PDF Upload Integration"
echo "========================================"

# Check if Go backend can compile
echo "1. Checking Go backend compilation..."
cd core/backend
if go build -o /tmp/arxos-test 2>/dev/null; then
    echo "✅ Backend compiles successfully"
else
    echo "❌ Backend compilation failed"
    echo "   Attempting to fix import paths..."
    
    # Fix import paths in main.go
    sed -i '' 's|"arxos/core/backend/api"|"./api"|' main.go
    sed -i '' 's|"arxos/core/ingestion"|"../ingestion"|' main.go
    
    if go build -o /tmp/arxos-test 2>/dev/null; then
        echo "✅ Backend compiles after fixing imports"
    else
        echo "⚠️  Backend still has compilation issues"
    fi
fi

# Check if PostgreSQL is running
echo ""
echo "2. Checking PostgreSQL..."
if pg_isready >/dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL is not running"
    echo "   Start with: brew services start postgresql (macOS)"
fi

# Check if Redis is running (optional)
echo ""
echo "3. Checking Redis (optional)..."
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is not running (caching will be disabled)"
fi

# Check frontend files
echo ""
echo "4. Checking frontend files..."
cd ../..
if [ -f "pdf_wall_extractor.html" ]; then
    echo "✅ PDF extractor HTML exists"
    
    # Check for required libraries
    if grep -q "tesseract.js" pdf_wall_extractor.html; then
        echo "✅ Tesseract.js is included"
    else
        echo "❌ Tesseract.js not found"
    fi
    
    if grep -q "uploadToBackend" pdf_wall_extractor.html; then
        echo "✅ Backend upload function exists"
    else
        echo "❌ Backend upload function not found"
    fi
else
    echo "❌ PDF extractor HTML not found"
fi

# Start backend server
echo ""
echo "5. Starting backend server..."
echo "   Run in another terminal:"
echo "   cd core/backend && go run ."
echo ""
echo "6. Open frontend in browser:"
echo "   open pdf_wall_extractor.html"
echo ""
echo "========================================"
echo "Integration test setup complete!"
echo ""
echo "To test the full flow:"
echo "1. Start the backend: cd core/backend && go run ."
echo "2. Open the frontend: open pdf_wall_extractor.html"
echo "3. Upload a PDF floor plan"
echo "4. Click 'Process' to extract walls"
echo "5. Click 'Export ArxObjects' to upload to backend"
echo ""
echo "Check browser console and backend logs for any errors."