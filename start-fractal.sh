#!/bin/bash

# Startup script for Fractal ArxObject Infrastructure
# This script starts all required services for the fractal zoom system

set -e

echo "🚀 Starting Fractal ArxObject Infrastructure..."

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create network if it doesn't exist
echo "📡 Creating Docker network..."
docker network create arxos-network 2>/dev/null || echo "Network already exists"

# Start infrastructure services
echo "🔧 Starting infrastructure services..."
docker-compose -f docker-compose.fractal.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."

# Wait for TimescaleDB
echo -n "Waiting for TimescaleDB..."
until docker exec arxos-timescaledb pg_isready -U arxos -d arxos_fractal > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " ✅"

# Wait for MinIO
echo -n "Waiting for MinIO..."
until curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " ✅"

# Wait for Redis
echo -n "Waiting for Redis..."
until docker exec arxos-redis-fractal redis-cli ping > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo " ✅"

# Run database migrations
echo "🗄️ Running database migrations..."
for migration in migrations/fractal/*.sql; do
    echo "  Applying $(basename $migration)..."
    docker exec -i arxos-timescaledb psql -U arxos -d arxos_fractal < "$migration" > /dev/null 2>&1 || echo "    (may already be applied)"
done

# Build and start tile server
echo "🗺️ Building tile server..."
cd services/tile-server
if [ ! -f go.mod ]; then
    echo "Tile server not found, skipping..."
else
    docker build -t arxos-tile-server . > /dev/null 2>&1
    echo "Starting tile server..."
    docker run -d \
        --name arxos-tile-server-instance \
        --network arxos-network \
        -p 8080:8080 \
        -e DATABASE_URL="postgresql://arxos:arxos_dev_2025@arxos-timescaledb:5432/arxos_fractal?sslmode=disable" \
        -e REDIS_URL="redis://arxos-redis-fractal:6379/1" \
        -e MINIO_ENDPOINT="arxos-minio:9000" \
        arxos-tile-server > /dev/null 2>&1 || echo "Tile server already running"
fi
cd ../..

# Display service URLs
echo ""
echo "✅ Fractal ArxObject Infrastructure is ready!"
echo ""
echo "📍 Service URLs:"
echo "  • TimescaleDB: postgresql://localhost:5433/arxos_fractal (user: arxos, pass: arxos_dev_2025)"
echo "  • MinIO Console: http://localhost:9001 (user: arxos, pass: arxos_minio_2025)"
echo "  • MinIO S3 API: http://localhost:9000"
echo "  • Redis: redis://localhost:6380"
echo "  • Tile Server: http://localhost:8080"
echo "  • Prometheus: http://localhost:9090"
echo "  • Grafana: http://localhost:3001 (user: admin, pass: arxos_grafana_2025)"
echo ""
echo "📊 Health Check URLs:"
echo "  • Tile Server Health: http://localhost:8080/health"
echo "  • Tile Server Stats: http://localhost:8080/stats"
echo ""
echo "🔍 Test the system:"
echo "  • Get campus-level tile: curl 'http://localhost:8080/tiles/10/512/512?scale=10.0'"
echo "  • Get building-level tile: curl 'http://localhost:8080/tiles/14/8192/8192?scale=1.0'"
echo "  • Get room-level tile: curl 'http://localhost:8080/tiles/18/131072/131072?scale=0.01'"
echo ""
echo "💡 To stop all services: docker-compose -f docker-compose.fractal.yml down"
echo ""