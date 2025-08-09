#!/bin/bash

# Arxos Development Environment Startup Script
# This script starts the complete development environment with all services

set -e

echo "🚀 Starting Arxos Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Set environment variables
export ARXOS_ENV=development
export COMPOSE_PROJECT_NAME=arxos

# Create necessary directories
echo "📁 Creating development directories..."
mkdir -p ../services/gus/data/knowledge/building_codes
mkdir -p ../services/gus/data/knowledge/standards
mkdir -p ../services/gus/data/knowledge/arxos
mkdir -p ../services/gus/data/vector_store
mkdir -p ../services/gus/logs

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
timeout=300
elapsed=0
interval=10

while [ $elapsed -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✅ All services are healthy!"
        break
    fi

    echo "⏳ Waiting for services... ($elapsed/$timeout seconds)"
    sleep $interval
    elapsed=$((elapsed + interval))
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Timeout waiting for services to be ready"
    echo "📋 Service status:"
    docker-compose ps
    exit 1
fi

# Display service information
echo ""
echo "🎉 Arxos Development Environment is ready!"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🌐 Service URLs:"
echo "  - GUS Agent:     http://localhost:9001"
echo "  - Browser CAD:    http://localhost:3000"
echo "  - ArxIDE:         http://localhost:8080"
echo "  - Backend API:    http://localhost:4000"
echo "  - PostgreSQL:     localhost:5432"
echo "  - Redis:          localhost:6379"
echo ""
echo "🔧 CLI Commands:"
echo "  - View logs:      docker-compose logs -f"
echo "  - Stop services:  docker-compose down"
echo "  - Restart:        docker-compose restart"
echo ""
echo "🧠 GUS Agent Commands:"
echo "  - Health check:   arx gus health"
echo "  - Query GUS:      arx gus query 'help me create a wall'"
echo "  - Knowledge:      arx gus knowledge electrical_outlets"
echo "  - Topics:         arx gus help-topics"
echo ""
echo "📚 Documentation:"
echo "  - API Docs:       http://localhost:9001/docs"
echo "  - Health Check:   http://localhost:9001/health"
echo ""

# Optional: Open browser to main services
if command -v xdg-open &> /dev/null; then
    echo "🌐 Opening services in browser..."
    xdg-open http://localhost:9001/docs 2>/dev/null &
    xdg-open http://localhost:3000 2>/dev/null &
elif command -v open &> /dev/null; then
    echo "🌐 Opening services in browser..."
    open http://localhost:9001/docs 2>/dev/null &
    open http://localhost:3000 2>/dev/null &
fi

echo "✅ Development environment started successfully!"
echo "💡 Tip: Use 'docker-compose logs -f' to view real-time logs"
