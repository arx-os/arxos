#!/bin/bash

# Test Arxos Ingestion Pipeline
echo "🏗️  Testing Arxos Ingestion Pipeline"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for test PDF
TEST_PDF=""
if [ -f "core/backend/uploads/*.pdf" ]; then
    TEST_PDF=$(ls core/backend/uploads/*.pdf | head -1)
    echo -e "${GREEN}✓${NC} Found test PDF: $TEST_PDF"
else
    echo -e "${YELLOW}⚠${NC} No PDFs found in uploads directory"
    echo "   Please upload a PDF using the web interface first"
fi

# Test 1: Check if services are running
echo ""
echo "1. Checking services..."

# Check Go backend
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓${NC} Go backend is running on port 8080"
else
    echo -e "${RED}✗${NC} Go backend is not running"
    echo "   Start with: cd core/backend && go run ."
fi

# Check Python AI service
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓${NC} Python AI service is running on port 8000"
else
    echo -e "${YELLOW}⚠${NC} Python AI service is not running"
    echo "   AI-powered extraction will not be available"
fi

# Test 2: Test PDF upload endpoint
echo ""
echo "2. Testing PDF upload endpoint..."

if [ ! -z "$TEST_PDF" ]; then
    response=$(curl -s -X POST \
        -F "pdf=@$TEST_PDF" \
        http://localhost:8080/api/pdf/upload)
    
    if echo "$response" | grep -q "success.*true"; then
        echo -e "${GREEN}✓${NC} PDF upload successful"
        
        # Extract statistics
        if command -v jq &> /dev/null; then
            objects=$(echo "$response" | jq '.data.extracted_objects | length')
            echo "   Extracted $objects objects"
            
            # Show object types
            echo "   Object types found:"
            echo "$response" | jq -r '.data.extracted_objects[].type' | sort | uniq -c
        fi
    else
        echo -e "${RED}✗${NC} PDF upload failed"
        echo "   Response: $response"
    fi
fi

# Test 3: Test health endpoint
echo ""
echo "3. Testing health endpoints..."

health=$(curl -s http://localhost:8080/health)
if echo "$health" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Health check passed"
    
    if command -v jq &> /dev/null; then
        # Show service statuses
        echo "   Service statuses:"
        echo "$health" | jq -r '.services | to_entries[] | "   - \(.key): \(.value)"'
    fi
else
    echo -e "${RED}✗${NC} Health check failed"
fi

# Test 4: List uploaded PDFs
echo ""
echo "4. Checking uploaded PDFs..."

pdfs=$(curl -s http://localhost:8080/api/pdf/list)
if echo "$pdfs" | grep -q "success.*true"; then
    if command -v jq &> /dev/null; then
        count=$(echo "$pdfs" | jq '.total')
        echo -e "${GREEN}✓${NC} Found $count uploaded PDFs"
        
        if [ "$count" -gt 0 ]; then
            echo "   Recent uploads:"
            echo "$pdfs" | jq -r '.data[] | "   - \(.filename) (\(.size | tonumber / 1024 / 1024 | floor)MB)"' | head -5
        fi
    else
        echo -e "${GREEN}✓${NC} PDF list endpoint working"
    fi
fi

# Test 5: Test with Hillsborough County Schools PDF
echo ""
echo "5. Testing with real building PDF..."

HCPS_PDF=""
for pdf in $(find . -name "*Alafia*.pdf" -o -name "*HCPS*.pdf" 2>/dev/null); do
    HCPS_PDF=$pdf
    break
done

if [ ! -z "$HCPS_PDF" ]; then
    echo -e "${GREEN}✓${NC} Found HCPS PDF: $HCPS_PDF"
    echo "   Uploading..."
    
    response=$(curl -s -X POST \
        -F "pdf=@$HCPS_PDF" \
        http://localhost:8080/api/pdf/upload)
    
    if echo "$response" | grep -q "success.*true"; then
        echo -e "${GREEN}✓${NC} HCPS PDF processed successfully"
        
        if command -v jq &> /dev/null; then
            # Show extraction summary
            echo "   Extraction summary:"
            echo "$response" | jq -r '.data.statistics | 
                "   - Total objects: \(.TotalObjects)
   - High confidence: \(.HighConfidence)
   - Medium confidence: \(.MediumConfidence)  
   - Low confidence: \(.LowConfidence)
   - Average confidence: \(.AverageConfidence | . * 100 | floor)%"'
        fi
    else
        echo -e "${RED}✗${NC} HCPS PDF processing failed"
    fi
else
    echo -e "${YELLOW}⚠${NC} No HCPS PDF found for testing"
    echo "   Download from your source and place in project directory"
fi

# Summary
echo ""
echo "===================================="
echo "Test Summary:"
echo ""
echo "To improve extraction quality:"
echo "1. Ensure Python AI service is running for advanced extraction"
echo "2. Upload high-quality vector PDFs (not scanned images)"
echo "3. Check logs for any extraction errors:"
echo "   - Backend: tail -f logs/backend.log"
echo "   - AI Service: tail -f logs/ai_service.log"
echo ""
echo "Next steps:"
echo "- Open pdf_wall_extractor.html to visualize extracted objects"
echo "- Use the ArxOS CLI to query extracted data:"
echo "  go run cmd/arxos/main.go 'SELECT * FROM building:* WHERE type=\"wall\"'"