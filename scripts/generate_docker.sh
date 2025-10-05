#!/bin/bash
# Generate Docker Compose files from Go configuration
# This script calls the Go Docker generation program

set -e

echo "🐳 Generating Docker Compose files from Go configuration..."

# Check if we're in the right directory
if [ ! -f "go.mod" ]; then
    echo "❌ Error: Must be run from the project root directory"
    exit 1
fi

# Run generation using the integrated CLI
echo "🚀 Generating Docker Compose files..."
go run cmd/arx/main.go config generate

echo "✅ Docker Compose files generated successfully!"
echo ""
echo "📁 Updated files:"
echo "   - docker-compose.yml (development)"
echo "   - docker-compose.prod.yml (production)"
echo "   - docker-compose.test.yml (test)"
echo ""
echo "🔄 To use the generated files:"
echo "   - Development: docker-compose up"
echo "   - Production: docker-compose -f docker-compose.prod.yml up"
echo "   - Test: docker-compose -f docker-compose.test.yml up"
