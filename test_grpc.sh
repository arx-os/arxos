#!/bin/bash

# Test gRPC connectivity between Go and Python services
set -e

echo "=== gRPC Service Connectivity Test ==="
echo

# Check if Python service is running
echo "1. Checking Python AI service..."
nc -zv localhost 50051 2>&1 | grep -q succeeded
if [ $? -eq 0 ]; then
    echo "✅ Python gRPC service is listening on port 50051"
else
    echo "❌ Python gRPC service is not running"
    echo "   Start it with: docker-compose up ai-service"
    exit 1
fi
echo

# Check if Go backend is running
echo "2. Checking Go backend service..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health | grep -q 200
if [ $? -eq 0 ]; then
    echo "✅ Go backend is running"
else
    echo "❌ Go backend is not running"
    echo "   Start it with: docker-compose up backend"
    exit 1
fi
echo

# Test gRPC health check
echo "3. Testing gRPC health endpoint..."
grpcurl -plaintext localhost:50051 ingestion.IngestionService/Health 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ gRPC health check successful"
else
    echo "⚠️  grpcurl not installed or health check failed"
    echo "   Install with: brew install grpcurl"
fi
echo

# Check Redis
echo "4. Checking Redis cache..."
redis-cli -p 6379 ping 2>/dev/null | grep -q PONG
if [ $? -eq 0 ]; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is not running (optional for caching)"
fi
echo

# Check PostgreSQL
echo "5. Checking PostgreSQL..."
pg_isready -h localhost -p 5432 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL is not running (optional for persistence)"
fi

echo
echo "=== Test Complete ===
"