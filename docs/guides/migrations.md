# Database Migrations Guide

**Last Updated:** October 15, 2025  
**For:** IT techs, developers, and database administrators

---

## Table of Contents

- [What Are Migrations?](#what-are-migrations)
- [Quick Start](#quick-start)
- [Understanding Migrations](#understanding)
- [Running Migrations](#running)
- [Creating Migrations](#creating)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## What Are Migrations? {#what-are-migrations}

### Simple Explanation

A **migration** is a set of instructions that changes the structure of your database. Think of it as a **work order for the database**.

**Real-World Analogy (Electrical Panel):**
```
Current panel:  20 circuits
Migration:      "Add 4 new circuit breakers"
Result:         Panel now has 24 circuits
```

**Database Example:**
```
Current table:  Equipment has columns for ID, Name, Type
Migration:      "Add a column called 'path'"
Result:         Equipment table now has ID, Name, Type, AND Path
```

### Why Do We Need Migrations?

Without migrations, if you try to save a path in your code, the database will say:
> ❌ "Error: Column 'path' doesn't exist in table 'equipment'"

It's like trying to plug something into a circuit that doesn't exist yet!

With migrations:
1. Tell the database: "Create a new column called 'path'"
2. Database creates the column
3. Now code can save paths successfully ✅

---

## Quick Start {#quick-start}

### Running Existing Migrations

```bash
# Navigate to project
cd /path/to/arxos

# Check which migrations have run
go run cmd/arx/main.go migrate status

# Run all pending migrations
go run cmd/arx/main.go migrate up

# Rollback last migration (if needed)
go run cmd/arx/main.go migrate down

# Check database health
go run cmd/arx/main.go health
```

### Creating a New Migration

```bash
# Create migration files
go run cmd/arx/main.go migrate create add_new_feature

# Edit the generated files:
# - internal/migrations/XXX_add_new_feature.up.sql
# - internal/migrations/XXX_add_new_feature.down.sql

# Test the migration
go run cmd/arx/main.go migrate up
```

---

## Understanding Migrations {#understanding}

### Migration Files Come in Pairs

```
023_add_equipment_paths.up.sql     ← Goes UP (adds the column)
023_add_equipment_paths.down.sql   ← Goes DOWN (removes it if needed)
```

**UP** = Apply the change (move forward)  
**DOWN** = Undo the change (rollback)

### Why Have Both?

If something goes wrong, you can **rollback**:
1. Run `.up.sql` → Column added
2. Realize there's a problem
3. Run `.down.sql` → Column removed
4. Fix the issue
5. Run `.up.sql` again → Column added correctly

### Migration Numbering

Migrations are numbered sequentially:
```
001_initial_schema.up.sql
002_postgres_enhancements.up.sql
003_spatial_anchors.up.sql
...
023_add_equipment_paths.up.sql
```

The number determines the order migrations run. Always use the next available number.

---

## Running Migrations {#running}

### Check Migration Status

**See what's been applied:**
```bash
go run cmd/arx/main.go migrate status
```

**Output:**
```
✓ 001_initial_schema.up.sql - Applied
✓ 002_postgres_enhancements.up.sql - Applied
✓ 003_spatial_anchors.up.sql - Applied
...
⏳ 024_new_feature.up.sql - Pending

Total applied: 23
Total pending: 1
```

### Run Migrations

**Apply all pending migrations:**
```bash
go run cmd/arx/main.go migrate up
```

**Apply specific number of migrations:**
```bash
# Run next 2 migrations only
go run cmd/arx/main.go migrate up 2
```

**Apply to specific version:**
```bash
go run cmd/arx/main.go migrate up 023
```

### Rollback Migrations

**Rollback last migration:**
```bash
go run cmd/arx/main.go migrate down
```

**Rollback specific number:**
```bash
# Rollback last 2 migrations
go run cmd/arx/main.go migrate down 2
```

**Rollback to specific version:**
```bash
go run cmd/arx/main.go migrate down 020
```

### Alternative Methods

**Using Make:**
```bash
make db-migrate        # Run migrations
make db-migrate-down   # Rollback
make db-migrate-status # Check status
```

**Direct SQL (for emergencies):**
```bash
psql -U youruser -d arxos_dev -f internal/migrations/023_add_equipment_paths.up.sql
```

---

## Creating Migrations {#creating}

### Step 1: Determine Migration Number

```bash
cd /path/to/arxos
ls internal/migrations/*.up.sql | tail -1
```

If the last migration is `022_item_relationships.up.sql`, your new migration will be `023`.

### Step 2: Create Migration Files

**Automated (Recommended):**
```bash
go run cmd/arx/main.go migrate create add_equipment_paths
```

This creates:
- `023_add_equipment_paths.up.sql`
- `023_add_equipment_paths.down.sql`

**Manual:**
```bash
touch internal/migrations/023_add_equipment_paths.up.sql
touch internal/migrations/023_add_equipment_paths.down.sql
```

### Step 3: Write the UP Migration

**File:** `internal/migrations/023_add_equipment_paths.up.sql`

```sql
-- Migration 023: Add path columns for universal naming convention
-- Author: Joel
-- Date: 2025-10-15
-- Purpose: Add path column to store equipment addresses

-- Start transaction
BEGIN;

-- Add path column to equipment table
ALTER TABLE equipment
ADD COLUMN IF NOT EXISTS path TEXT;

-- Add path column to bas_points table
ALTER TABLE bas_points
ADD COLUMN IF NOT EXISTS path TEXT;

-- Create indexes for fast searching
CREATE INDEX IF NOT EXISTS idx_equipment_path
ON equipment(path);

CREATE INDEX IF NOT EXISTS idx_bas_points_path
ON bas_points(path);

-- Special indexes for wildcard searches (e.g., /B1/3/*/HVAC/*)
CREATE INDEX IF NOT EXISTS idx_equipment_path_prefix
ON equipment(path text_pattern_ops);

CREATE INDEX IF NOT EXISTS idx_bas_points_path_prefix
ON bas_points(path text_pattern_ops);

-- Add documentation
COMMENT ON COLUMN equipment.path IS
'Universal naming convention path (e.g., /B1/3/301/HVAC/VAV-301)';

COMMENT ON COLUMN bas_points.path IS
'Universal naming convention path (e.g., /B1/3/301/BAS/AI-1-1)';

-- Commit transaction
COMMIT;
```

### Step 4: Write the DOWN Migration

**File:** `internal/migrations/023_add_equipment_paths.down.sql`

```sql
-- Migration 023 DOWN: Remove path columns
-- This removes the changes if we need to rollback

-- Start transaction
BEGIN;

-- Drop indexes first (must be done before dropping column)
DROP INDEX IF EXISTS idx_equipment_path_prefix;
DROP INDEX IF EXISTS idx_bas_points_path_prefix;
DROP INDEX IF EXISTS idx_equipment_path;
DROP INDEX IF EXISTS idx_bas_points_path;

-- Drop the columns
ALTER TABLE equipment DROP COLUMN IF EXISTS path;
ALTER TABLE bas_points DROP COLUMN IF EXISTS path;

-- Commit transaction
COMMIT;
```

### Step 5: Test the Migration

**On test database first:**
```bash
# Set test database
export POSTGIS_DATABASE=arxos_test

# Run migration
go run cmd/arx/main.go migrate up

# Verify it worked
psql arxos_test -c "\d equipment"

# Test rollback
go run cmd/arx/main.go migrate down

# Verify rollback worked
psql arxos_test -c "\d equipment"
```

**Then on dev database:**
```bash
# Set dev database
export POSTGIS_DATABASE=arxos_dev

# Run migration
go run cmd/arx/main.go migrate up
```

---

## Migration Patterns

### Adding a Column

```sql
ALTER TABLE table_name
ADD COLUMN IF NOT EXISTS column_name TYPE;
```

**Example:**
```sql
ALTER TABLE equipment
ADD COLUMN IF NOT EXISTS path TEXT;
```

### Removing a Column

```sql
ALTER TABLE table_name
DROP COLUMN IF EXISTS column_name;
```

### Creating an Index

```sql
CREATE INDEX IF NOT EXISTS index_name
ON table_name(column_name);
```

### Creating a Table

```sql
CREATE TABLE IF NOT EXISTS table_name (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Adding a Foreign Key

```sql
ALTER TABLE child_table
ADD CONSTRAINT fk_name
FOREIGN KEY (parent_id)
REFERENCES parent_table(id)
ON DELETE CASCADE;
```

### Creating an Enum

```sql
CREATE TYPE status_type AS ENUM ('active', 'inactive', 'pending');

ALTER TABLE table_name
ADD COLUMN status status_type DEFAULT 'pending';
```

### Data Migration

```sql
-- Update existing records
UPDATE equipment
SET path = '/B1/' || floor_level || '/' || room_number || '/HVAC/' || name
WHERE category = 'hvac' AND path IS NULL;
```

---

## Troubleshooting {#troubleshooting}

### Migration Already Applied

**Symptom:**
```
Error: column "path" already exists
```

**Solution:**
This is usually fine if you're using `IF NOT EXISTS`. The migration is idempotent.

If it's failing, check:
```bash
# See what's been applied
go run cmd/arx/main.go migrate status
```

### Permission Denied

**Symptom:**
```
ERROR: permission denied for table equipment
```

**Solution:**
```bash
# Run as database owner
sudo -u postgres go run cmd/arx/main.go migrate up

# Or grant permissions
psql arxos_dev -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO youruser;"
```

### Database Not Found

**Symptom:**
```
FATAL: database "arxos_dev" does not exist
```

**Solution:**
```bash
# Create database first
createdb arxos_dev
psql arxos_dev -c "CREATE EXTENSION postgis;"

# Then run migrations
go run cmd/arx/main.go migrate up
```

### Migration Stuck

**Symptom:**
Migration hangs or takes too long

**Solution:**
```bash
# Check for locks
psql arxos_dev -c "SELECT * FROM pg_locks WHERE granted = false;"

# Kill blocking queries (if safe)
psql arxos_dev -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction';"
```

### Rollback Failed

**Symptom:**
```
Error: could not rollback migration
```

**Solution:**
```bash
# Check what went wrong
psql arxos_dev

# Manually fix the issue
-- See what's in the down migration
\i internal/migrations/023_add_equipment_paths.down.sql

# Or manually run the fixes
DROP INDEX IF EXISTS idx_equipment_path;
ALTER TABLE equipment DROP COLUMN IF EXISTS path;
```

### Test Migration Failed

**Symptom:**
Migration works on test but fails on production

**Common causes:**
1. Different PostgreSQL versions
2. Different data in tables
3. Missing dependencies

**Solution:**
```bash
# Check PostgreSQL version
psql --version

# Check table data
psql arxos_dev -c "SELECT COUNT(*) FROM equipment;"

# Test on copy of production data
pg_dump arxos_production | psql arxos_staging
psql arxos_staging -f internal/migrations/XXX_migration.up.sql
```

---

## Best Practices {#best-practices}

### 1. Always Use Transactions

```sql
BEGIN;
-- Your migration code here
COMMIT;
```

This ensures either all changes succeed or all fail together.

### 2. Use IF NOT EXISTS / IF EXISTS

```sql
ALTER TABLE equipment
ADD COLUMN IF NOT EXISTS path TEXT;

DROP INDEX IF EXISTS idx_old_name;
```

Makes migrations idempotent (safe to run multiple times).

### 3. Test Rollback

Always test that your DOWN migration works:
```bash
go run cmd/arx/main.go migrate up
go run cmd/arx/main.go migrate down
```

### 4. Add Comments

Document why the migration exists:
```sql
-- Migration 023: Add path columns
-- Purpose: Support universal naming convention for equipment
-- Related: GitHub issue #123
```

### 5. Keep Migrations Small

One logical change per migration:
- ✅ Good: `023_add_equipment_paths.sql`
- ✅ Good: `024_add_user_roles.sql`
- ❌ Bad: `023_add_paths_and_roles_and_fix_indexes.sql`

### 6. Never Edit Applied Migrations

Once a migration has run in production, never edit it. Create a new migration instead.

**Wrong:**
```
Edit 023_add_equipment_paths.sql
```

**Right:**
```
Create 024_fix_equipment_paths.sql
```

### 7. Backup Before Major Migrations

```bash
# Backup before running migration
pg_dump arxos_production > backup_pre_migration.sql

# Run migration
go run cmd/arx/main.go migrate up

# Verify
go run cmd/arx/main.go health
```

### 8. Test on Staging First

```bash
# Test on staging
POSTGIS_DATABASE=arxos_staging go run cmd/arx/main.go migrate up

# Verify staging works
# Then apply to production
POSTGIS_DATABASE=arxos_production go run cmd/arx/main.go migrate up
```

### 9. Handle Data Carefully

When migrating data, handle NULL values and edge cases:
```sql
-- Update with careful NULL handling
UPDATE equipment
SET path = COALESCE(
    '/B1/' || COALESCE(floor_level::text, '1') || '/' || 
    COALESCE(room_number, 'UNKNOWN') || '/HVAC/' || name,
    '/B1/UNKNOWN/HVAC/' || name
)
WHERE category = 'hvac' AND path IS NULL;
```

### 10. Monitor Performance

For large tables, migrations can take time:
```sql
-- Check table size before migration
SELECT pg_size_pretty(pg_total_relation_size('equipment'));

-- Add index concurrently (doesn't lock table)
CREATE INDEX CONCURRENTLY idx_equipment_path ON equipment(path);
```

---

## Advanced Topics

### Concurrent Index Creation

For large tables, create indexes without locking:
```sql
-- Regular index (locks table)
CREATE INDEX idx_name ON table(column);

-- Concurrent index (no lock, but slower)
CREATE INDEX CONCURRENTLY idx_name ON table(column);
```

### Data Migrations with Validation

```sql
-- Migrate data with validation
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN SELECT * FROM equipment WHERE path IS NULL LOOP
        -- Validate and migrate
        IF rec.building_id IS NOT NULL THEN
            UPDATE equipment
            SET path = generate_path(rec.building_id, rec.floor_id, rec.room_id)
            WHERE id = rec.id;
        END IF;
    END LOOP;
END $$;
```

### Conditional Migrations

```sql
-- Only run if condition is met
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'equipment') THEN
        CREATE TABLE equipment (...);
    END IF;
END $$;
```

---

## Historical Documents

This guide consolidates and supersedes:
- [DATABASE_MIGRATION_SIMPLE_GUIDE.md](../archive/database-migration-simple-guide-oct-2025.md) - Simple guide for non-developers
- [MIGRATION_INSTRUCTIONS.md](../archive/migration-instructions-oct-2025.md) - Quick instructions
- [docs/DATABASE_MIGRATIONS_GUIDE.md](../archive/database-migrations-guide-oct-2025.md) - Technical guide

For historical reference, see the [Archive](../archive/).

---

## Next Steps

- **[Database Setup](database-setup.md)** - Set up PostgreSQL and PostGIS
- **[Postgres Reference](postgres-reference.md)** - PostgreSQL command reference
- **[Development Guide](../DEVELOPMENT.md)** - General development information

---

*For questions or improvements, see the [Documentation Index](../DOCUMENTATION_INDEX.md).*

