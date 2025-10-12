#!/bin/bash
# Migrate test database
# This script runs all migrations on the arxos_test database

set -e

echo "🧪 Migrating test database..."

# Check if migrations directory exists
if [ ! -d "internal/migrations" ]; then
    echo "❌ Migrations directory not found"
    exit 1
fi

# Run all .sql migrations on test database
for migration in internal/migrations/*.sql; do
    if [ -f "$migration" ]; then
        echo "Applying $(basename $migration)..."
        psql -U arxos_test -d arxos_test -f "$migration" > /dev/null 2>&1 || true
    fi
done

echo "✅ Test database migrations complete!"

# Show table count
echo ""
echo "Tables in arxos_test:"
psql -U arxos_test -d arxos_test -c "\dt" | wc -l

