#!/bin/bash
# Migrate configuration files to use the new Go config system
# This script calls the Go migration program

set -e

echo "🔄 Migrating configuration files to new Go config system..."

# Check if we're in the right directory
if [ ! -f "go.mod" ]; then
    echo "❌ Error: Must be run from the project root directory"
    exit 1
fi

# Run migration using the integrated CLI
echo "🚀 Running configuration migration..."
go run cmd/arx/main.go config migrate

echo "✅ Configuration migration completed!"
echo ""
echo "📁 New configuration templates are available in:"
echo "   - internal/config/templates/development.yml"
echo "   - internal/config/templates/production.yml"
echo "   - internal/config/templates/test.yml"
echo ""
echo "🔄 To use the new configurations:"
echo "   - Copy a template to configs/ directory"
echo "   - Update values as needed"
echo "   - Use with: arx --config configs/your-config.yml"
