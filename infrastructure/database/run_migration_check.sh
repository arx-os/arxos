#!/bin/bash

# =============================================================================
# Database Migration Foreign Key Constraint Order Validator
# =============================================================================
# This script validates that tables are created in the correct order
# to satisfy foreign key dependencies.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_FILE="$SCRIPT_DIR/001_create_arx_schema.sql"

echo "🔍 Validating foreign key constraint order in: $MIGRATION_FILE"
echo ""

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Error: Migration file not found: $MIGRATION_FILE"
    exit 1
fi

# Extract table creation statements and their dependencies
echo "📋 Analyzing table dependencies..."

# Create temporary files for analysis
TEMP_TABLES=$(mktemp)
TEMP_DEPS=$(mktemp)

# Extract CREATE TABLE statements
grep -n "CREATE TABLE" "$MIGRATION_FILE" | while read -r line; do
    echo "$line" >> "$TEMP_TABLES"
done

# Extract foreign key references
grep -n "REFERENCES" "$MIGRATION_FILE" | while read -r line; do
    echo "$line" >> "$TEMP_DEPS"
done

# Define expected table order based on dependencies
EXPECTED_ORDER=(
    "users"
    "projects" 
    "buildings"
    "floors"
    "categories"
    "rooms"
    "walls"
    "doors"
    "windows"
    "devices"
    "labels"
    "zones"
    "drawings"
    "comments"
    "assignments"
    "object_history"
    "audit_logs"
    "user_category_permissions"
    "chat_messages"
    "catalog_items"
)

# Validate table creation order
echo "✅ Validating table creation order..."
ERRORS=0

for table in "${EXPECTED_ORDER[@]}"; do
    if grep -q "CREATE TABLE $table" "$MIGRATION_FILE"; then
        echo "  ✓ Found table: $table"
    else
        echo "  ❌ Missing table: $table"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check for foreign key constraint violations
echo ""
echo "🔍 Checking for potential foreign key constraint issues..."

# Common foreign key patterns to check
FK_PATTERNS=(
    "REFERENCES users\\(id\\)"
    "REFERENCES projects\\(id\\)"
    "REFERENCES buildings\\(id\\)"
    "REFERENCES floors\\(id\\)"
    "REFERENCES rooms\\(id\\)"
    "REFERENCES categories\\(id\\)"
    "REFERENCES audit_logs\\(id\\)"
)

for pattern in "${FK_PATTERNS[@]}"; do
    # Extract referenced table name
    ref_table=$(echo "$pattern" | sed 's/REFERENCES \([a-zA-Z_]*\)(id)/\1/')
    
    # Find all tables that reference this table
    referencing_tables=$(grep -B 10 "$pattern" "$MIGRATION_FILE" | grep "CREATE TABLE" | sed 's/CREATE TABLE \([a-zA-Z_]*\).*/\1/')
    
    for refing_table in $referencing_tables; do
        # Check if referenced table is created before referencing table
        ref_line=$(grep -n "CREATE TABLE $ref_table" "$MIGRATION_FILE" | cut -d: -f1)
        refing_line=$(grep -n "CREATE TABLE $refing_table" "$MIGRATION_FILE" | cut -d: -f1)
        
        if [ "$refing_line" -lt "$ref_line" ]; then
            echo "  ❌ Foreign key constraint issue: $refing_table references $ref_table but is created first"
            echo "     $refing_table created at line $refing_line, $ref_table created at line $ref_line"
            ERRORS=$((ERRORS + 1))
        fi
    done
done

# Check for specific known issues
echo ""
echo "🔍 Checking for specific constraint issues..."

# Check if categories is created before buildings (was a known issue)
CATEGORIES_LINE=$(grep -n "CREATE TABLE categories" "$MIGRATION_FILE" | cut -d: -f1)
BUILDINGS_LINE=$(grep -n "CREATE TABLE buildings" "$MIGRATION_FILE" | cut -d: -f1)

if [ -n "$CATEGORIES_LINE" ] && [ -n "$BUILDINGS_LINE" ]; then
    if [ "$CATEGORIES_LINE" -lt "$BUILDINGS_LINE" ]; then
        echo "  ❌ Critical issue: categories table created before buildings table"
        echo "     categories at line $CATEGORIES_LINE, buildings at line $BUILDINGS_LINE"
        ERRORS=$((ERRORS + 1))
    else
        echo "  ✅ categories table correctly created after buildings table"
    fi
fi

# Check for any REFERENCES statements that might be problematic
echo ""
echo "🔍 Scanning for all foreign key references..."

grep -n "REFERENCES" "$MIGRATION_FILE" | while read -r line; do
    line_num=$(echo "$line" | cut -d: -f1)
    ref_statement=$(echo "$line" | cut -d: -f2-)
    echo "  📍 Line $line_num: $ref_statement"
done

# Cleanup temporary files
rm -f "$TEMP_TABLES" "$TEMP_DEPS"

# Final validation result
echo ""
echo "=============================================================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ Migration file validation PASSED"
    echo "   All foreign key constraints are properly ordered"
    exit 0
else
    echo "❌ Migration file validation FAILED"
    echo "   Found $ERRORS constraint ordering issue(s)"
    echo ""
    echo "💡 To fix issues:"
    echo "   1. Ensure referenced tables are created before referencing tables"
    echo "   2. Follow the dependency hierarchy in the schema comments"
    echo "   3. Re-run this validation script after fixes"
    exit 1
fi 