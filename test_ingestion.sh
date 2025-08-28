#!/bin/bash

# Test ingestion pipeline with sample PDF
set -e

echo "=== ArxOS Ingestion Pipeline Test ==="
echo

# Configuration
API_URL="http://localhost:8080"
TEST_PDF="${1:-/Users/joelpate/Downloads/Alafia_ES_IDF_CallOut.pdf}"

# Check if PDF exists
if [ ! -f "$TEST_PDF" ]; then
    echo "❌ Test PDF not found: $TEST_PDF"
    echo "Usage: $0 [path-to-pdf]"
    exit 1
fi

echo "📄 Testing with PDF: $(basename "$TEST_PDF")"
echo

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed (HTTP $HEALTH_RESPONSE)"
    exit 1
fi
echo

# Test PDF upload
echo "2. Testing PDF upload..."
UPLOAD_RESPONSE=$(curl -s -X POST \
    -F "file=@$TEST_PDF" \
    -F "projectId=test-project" \
    $API_URL/api/ingestion/upload)

if echo "$UPLOAD_RESPONSE" | grep -q "processing_id"; then
    PROCESSING_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"processing_id":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Upload successful - Processing ID: $PROCESSING_ID"
    echo
    
    # Poll for status
    echo "3. Polling for processing status..."
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        STATUS_RESPONSE=$(curl -s "$API_URL/api/ingestion/status/$PROCESSING_ID")
        STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        
        echo -n "   Attempt $((ATTEMPT + 1))/$MAX_ATTEMPTS: Status = $STATUS"
        
        if [ "$STATUS" = "completed" ]; then
            echo
            echo "✅ Processing completed successfully!"
            echo
            echo "4. Results:"
            echo "$STATUS_RESPONSE" | python3 -m json.tool
            break
        elif [ "$STATUS" = "failed" ]; then
            echo
            echo "❌ Processing failed"
            echo "$STATUS_RESPONSE" | python3 -m json.tool
            exit 1
        fi
        
        echo " (waiting...)"
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo
        echo "⏱️ Processing timeout - check logs for details"
        exit 1
    fi
else
    echo "❌ Upload failed"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

echo
echo "=== Test Complete ===
"