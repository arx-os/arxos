#!/bin/bash

# Test PDF Upload with Authentication
echo "Testing Arxos PDF Upload with Authentication"
echo "==========================================="

# First, register/login to get a token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8080/api/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@arxos.com", "password": "test123"}')

# Try registration if login fails
if ! echo "$LOGIN_RESPONSE" | grep -q "token"; then
    echo "   Login failed, trying registration..."
    REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8080/api/register \
        -H "Content-Type: application/json" \
        -d '{"email": "test@arxos.com", "password": "test123", "name": "Test User"}')
    
    # Now login
    LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8080/api/login \
        -H "Content-Type: application/json" \
        -d '{"email": "test@arxos.com", "password": "test123"}')
fi

# Extract token (simple parsing - would use jq in production)
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "   Failed to get authentication token"
    echo "   Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "   Got token: ${TOKEN:0:20}..."

# 2. Upload PDF with authentication
echo "2. Uploading PDF..."
PDF_FILE="/Users/joelpate/repos/arxos/core/backend/uploads/1755622664_Alafia_ES_IDF_CallOut.pdf"

UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8080/api/buildings/upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "pdf=@$PDF_FILE")

echo "3. Upload Response:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"

# Check if successful
if echo "$UPLOAD_RESPONSE" | grep -q "success"; then
    echo ""
    echo "✅ Upload successful!"
    
    # Try to extract some stats
    if command -v jq &> /dev/null; then
        echo ""
        echo "Extraction Statistics:"
        echo "$UPLOAD_RESPONSE" | jq '.data.statistics // .statistics // empty'
        
        echo ""
        echo "Objects Found:"
        echo "$UPLOAD_RESPONSE" | jq '.data.extracted_objects | length // empty'
    fi
else
    echo ""
    echo "❌ Upload failed"
fi