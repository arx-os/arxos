#!/bin/bash

# Test script to verify PDF processing is working correctly

echo "🧪 Testing PDF Processing Pipeline"
echo "=================================="

# Check if AI service is running
echo -n "Checking AI service health... "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ AI service is running"
else
    echo "❌ AI service is not running. Please run ./start_arxos.sh first"
    exit 1
fi

# Check if Go backend is running
echo -n "Checking Go backend health... "
if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ Go backend is running"
else
    echo "❌ Go backend is not running. Please run ./start_arxos.sh first"
    exit 1
fi

# Find a test PDF
TEST_PDF=""
if [ -f "test_floor_plan.pdf" ]; then
    TEST_PDF="test_floor_plan.pdf"
elif [ -f "Alafia_ES_IDF_CallOut.pdf" ]; then
    TEST_PDF="Alafia_ES_IDF_CallOut.pdf"
else
    echo "⚠️  No test PDF found. Please provide a PDF file path as argument:"
    echo "   ./test_pdf_processing.sh path/to/your/floor_plan.pdf"
    exit 1
fi

if [ ! -z "$1" ]; then
    TEST_PDF="$1"
fi

echo ""
echo "📄 Testing with PDF: $TEST_PDF"
echo ""

# Test direct AI service
echo "1️⃣  Testing direct AI service PDF processing..."
echo "------------------------------------------------"
RESPONSE=$(curl -s -X POST \
    -F "file=@$TEST_PDF" \
    -F "building_type=school" \
    http://localhost:8000/api/v1/convert)

if [ $? -eq 0 ]; then
    OBJECT_COUNT=$(echo "$RESPONSE" | grep -o '"arxobjects":\[.*\]' | grep -o '"id"' | wc -l)
    CONFIDENCE=$(echo "$RESPONSE" | grep -o '"overall_confidence":[0-9.]*' | cut -d: -f2)
    
    echo "✅ AI service processed PDF successfully"
    echo "   - Objects extracted: $OBJECT_COUNT"
    echo "   - Overall confidence: $CONFIDENCE"
    
    # Show object types
    echo "   - Object types found:"
    echo "$RESPONSE" | grep -o '"type":"[^"]*"' | cut -d'"' -f4 | sort | uniq -c | sed 's/^/      /'
else
    echo "❌ AI service failed to process PDF"
fi

echo ""
echo "2️⃣  Testing Go backend PDF upload..."
echo "------------------------------------"
RESPONSE=$(curl -s -X POST \
    -F "pdf=@$TEST_PDF" \
    http://localhost:8080/api/pdf/upload)

if [ $? -eq 0 ]; then
    SUCCESS=$(echo "$RESPONSE" | grep -o '"success":true')
    if [ ! -z "$SUCCESS" ]; then
        echo "✅ Go backend processed PDF successfully"
        
        # Extract statistics
        STATS=$(echo "$RESPONSE" | grep -o '"statistics":{[^}]*}')
        if [ ! -z "$STATS" ]; then
            echo "   Statistics:"
            echo "$STATS" | sed 's/,/\n/g' | sed 's/[{}]//g' | sed 's/^/      /'
        fi
    else
        echo "❌ Go backend returned an error:"
        echo "$RESPONSE" | head -3
    fi
else
    echo "❌ Go backend failed to process PDF"
fi

echo ""
echo "3️⃣  Checking for common issues..."
echo "--------------------------------"

# Check if mock data is being returned
if echo "$RESPONSE" | grep -q '"start_x":100.*"start_y":100.*"end_x":500.*"end_y":100'; then
    echo "⚠️  WARNING: Mock data detected! The Go backend is still using hardcoded test data."
    echo "   Please ensure pdf_processor.go is using the real AI service."
fi

# Check object count
if [ "$OBJECT_COUNT" -lt 10 ]; then
    echo "⚠️  WARNING: Very few objects extracted ($OBJECT_COUNT). Expected more for a floor plan."
    echo "   Possible issues:"
    echo "   - Confidence threshold too high (try lowering from 0.6 to 0.3)"
    echo "   - Classification rules too restrictive"
    echo "   - PDF quality issues"
fi

echo ""
echo "✨ Test complete!"