#!/bin/bash

# Complete startup script for Fractal ArxObject System with Scale Engine
# This script starts all infrastructure services and the Scale Engine

set -e

echo "🚀 Starting Complete Fractal ArxObject System with Scale Engine..."
echo ""

# Check dependencies
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create network if it doesn't exist
echo "📡 Creating Docker network..."
docker network create arxos-network 2>/dev/null || echo "   Network already exists"

# Stop any existing services
echo "🛑 Stopping any existing services..."
docker-compose -f docker-compose.fractal.yml down 2>/dev/null || true
docker-compose -f docker-compose.scale-engine.yml down 2>/dev/null || true

# Start infrastructure services
echo "🔧 Starting infrastructure services..."
docker-compose -f docker-compose.fractal.yml up -d

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure services to be ready..."

# Wait for TimescaleDB
echo -n "   Waiting for TimescaleDB..."
until docker exec arxos-timescaledb pg_isready -U arxos -d arxos_fractal > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " ✅"

# Wait for MinIO
echo -n "   Waiting for MinIO..."
until curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " ✅"

# Wait for Redis
echo -n "   Waiting for Redis..."
until docker exec arxos-redis-fractal redis-cli ping > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " ✅"

# Run database migrations
echo "🗄️  Running database migrations..."
for migration in migrations/fractal/*.sql; do
    echo "   Applying $(basename $migration)..."
    docker exec -i arxos-timescaledb psql -U arxos -d arxos_fractal < "$migration" 2>&1 | grep -v "already exists" || true
done
echo "   ✅ Migrations complete"

# Build and start tile server
echo "🗺️  Starting Tile Server..."
cd services/tile-server
if [ -f go.mod ]; then
    docker build -t arxos-tile-server . > /dev/null 2>&1
    docker run -d \
        --name arxos-tile-server-instance \
        --network arxos-network \
        -p 8080:8080 \
        -e DATABASE_URL="postgresql://arxos:arxos_dev_2025@arxos-timescaledb:5432/arxos_fractal?sslmode=disable" \
        -e REDIS_URL="redis://arxos-redis-fractal:6379/1" \
        -e MINIO_ENDPOINT="arxos-minio:9000" \
        arxos-tile-server > /dev/null 2>&1 || echo "   Tile server already running"
fi
cd ../..

# Build and start Scale Engine
echo "⚙️  Building Scale Engine Service..."
cd services/scale-engine
if [ -f package.json ]; then
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env 2>/dev/null || true
    fi
    
    # Build the Scale Engine
    docker build -t arxos-scale-engine . > /dev/null 2>&1
    echo "   ✅ Scale Engine built"
fi
cd ../..

# Start Scale Engine and Nginx
echo "🎯 Starting Scale Engine and API Gateway..."
docker-compose -f docker-compose.scale-engine.yml up -d

# Wait for Scale Engine to be ready
echo -n "   Waiting for Scale Engine..."
until curl -f http://localhost:3000/health > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " ✅"

# Display status
echo ""
echo "=================================================================================="
echo "✅ Fractal ArxObject System with Scale Engine is ready!"
echo "=================================================================================="
echo ""
echo "📍 Service URLs:"
echo "   • API Gateway:         http://localhost"
echo "   • Scale Engine API:    http://localhost:3000/api"
echo "   • Tile Server:         http://localhost:8080"
echo "   • MinIO Console:       http://localhost:9001"
echo "   • Grafana Dashboard:   http://localhost:3001"
echo "   • Prometheus Metrics:  http://localhost:9090"
echo ""
echo "🔍 API Endpoints:"
echo "   • Swagger Docs:        http://localhost:3000/api"
echo "   • Health Check:        http://localhost/health"
echo "   • Metrics:             http://localhost/metrics"
echo ""
echo "📊 Scale Engine Endpoints:"
echo "   • Get Visible Objects: GET  /api/v1/scale/visible-objects"
echo "   • Initialize Viewport: POST /api/v1/viewport/initialize"
echo "   • Zoom:                POST /api/v1/viewport/zoom"
echo "   • Pan:                 POST /api/v1/viewport/pan"
echo "   • Get Viewport State:  GET  /api/v1/viewport/state"
echo ""
echo "🧪 Test Commands:"
echo ""
echo "   # Initialize viewport at building scale"
echo "   curl -X POST http://localhost:3000/api/v1/viewport/initialize \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"center\":{\"x\":0,\"y\":0},\"scale\":1.0,\"viewportSize\":{\"width\":1920,\"height\":1080}}'"
echo ""
echo "   # Get visible objects"
echo "   curl 'http://localhost:3000/api/v1/scale/visible-objects?minX=-100&minY=-100&maxX=100&maxY=100&scale=1.0'"
echo ""
echo "   # Zoom in to room scale"
echo "   curl -X POST http://localhost:3000/api/v1/viewport/zoom \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"targetScale\":0.01,\"focalX\":100,\"focalY\":50,\"duration\":200}'"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose -f docker-compose.fractal.yml down"
echo "   docker-compose -f docker-compose.scale-engine.yml down"
echo ""
echo "📝 View logs:"
echo "   docker logs arxos-scale-engine -f"
echo "   docker logs arxos-tile-server-instance -f"
echo ""
echo "=================================================================================="