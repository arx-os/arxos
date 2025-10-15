# How to Run the Path Column Migration

**Created:** October 12, 2025
**For:** Adding the `path` column to equipment and BAS points tables

---

## What This Does

Adds a new column called `path` to two database tables:
- `equipment` table → stores paths like `/B1/3/301/HVAC/VAV-301`
- `bas_points` table → stores paths like `/B1/3/301/BAS/AI-1-1`

This column lets you address every piece of equipment with a unique, human-readable path.

---

## Before You Start

**1. Make sure PostgreSQL is running:**
```bash
pg_isready
```

If it says "accepting connections" → You're good!
If not → Start PostgreSQL first.

**2. Make sure you have a backup** (just in case):
```bash
# Option A: pg_dump
pg_dump arxos_db > backup_before_paths_$(date +%Y%m%d).sql

# Option B: If you have a backup script
./scripts/backup.sh
```

---

## Step 1: Check What Migrations Have Run

```bash
cd /Users/joelpate/repos/arxos
arx migrate status
```

This shows you which migrations have already been applied. You should see migrations 001 through 022 marked as "applied" or "done".

---

## Step 2: Run the New Migration

**Option A: Using the ArxOS CLI (recommended):**
```bash
arx migrate up
```

**Option B: Using Make:**
```bash
make db-migrate
```

**Option C: Manual (if the above don't work):**
```bash
# Replace 'your_username' with your actual database username
psql -U your_username -d arxos_db -f internal/migrations/023_add_equipment_paths.up.sql
```

---

## Step 3: Verify It Worked

**Check the equipment table:**
```bash
psql -U your_username -d arxos_db -c "\d equipment"
```

Look for a line that says:
```
path | text |
```

That means the column was added successfully!

**Check the bas_points table:**
```bash
psql -U your_username -d arxos_db -c "\d bas_points"
```

Should also have a `path` column.

---

## Step 4: Test With Sample Data

**Check that the column exists and is queryable:**
```bash
psql -U your_username -d arxos_db -c \
"SELECT id, name, path FROM equipment LIMIT 5;"
```

You should see results (path will be NULL for existing equipment, that's normal).

---

## What You Should See

### Success Looks Like:
```
BEGIN
ALTER TABLE
ALTER TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMIT
```

### If Something Goes Wrong:
- **"column already exists"** → That's fine! It means the column was already added. The migration is smart enough to skip it.
- **"permission denied"** → You need to run as the database owner (usually `postgres` or your username)
- **"database does not exist"** → Check your database name in `configs/environments/development.yml`

---

## If You Need to Rollback

**Only do this if something went wrong:**
```bash
arx migrate down
```

This will:
1. Remove the indexes
2. Remove the `path` columns
3. Put everything back the way it was

Then you can fix the issue and run `arx migrate up` again.

---

## After Migration: Next Steps

### 1. Test IFC Import
Import a building and check if paths are generated:
```bash
arx import test_data/inputs/sample_building.ifc
```

Then check:
```bash
psql -U your_username -d arxos_db -c \
"SELECT name, path FROM equipment WHERE path IS NOT NULL LIMIT 10;"
```

You should see paths like `/B1/3/301/HVAC/VAV-301`!

### 2. Test BAS Import
Import BAS points:
```bash
arx bas import test_data/bas/sample_points.csv --building-id <building-id>
```

Then check:
```bash
psql -U your_username -d arxos_db -c \
"SELECT point_name, path FROM bas_points WHERE path IS NOT NULL LIMIT 10;"
```

You should see paths like `/B1/BAS/AI-1-1` (initially) or `/B1/3/301/BAS/AI-1-1` (after mapping).

### 3. Try Path-Based Queries
Once you have equipment with paths, try searching:
```bash
# Find all HVAC on floor 3 (when path queries are implemented)
arx get /B1/3/*/HVAC/*

# Find specific equipment
arx get /B1/3/301/HVAC/VAV-301
```

---

## Troubleshooting

### "Command 'arx migrate' not found"
**Solution:** Use the full path:
```bash
./bin/arx migrate up
```

Or build it first:
```bash
go build -o bin/arx cmd/arx/main.go
./bin/arx migrate up
```

### "Could not connect to database"
**Solution:** Check your database connection settings:
```bash
# Check config file
cat configs/environments/development.yml | grep -A 5 database

# Test connection manually
psql -U your_username -d arxos_db -c "SELECT version();"
```

### "Migration already applied"
**Solution:** Check migration status:
```bash
arx migrate status
```

If 023 shows as "applied", you're good! The migration already ran.

---

## Files Created

```
internal/migrations/
├── 023_add_equipment_paths.up.sql    ← Adds the columns
└── 023_add_equipment_paths.down.sql  ← Removes them (rollback)
```

---

## What the Migration Does (In Detail)

### Adds These Columns:
- `equipment.path` (TEXT) - Stores equipment paths
- `bas_points.path` (TEXT) - Stores BAS point paths

### Creates These Indexes:
- `idx_equipment_path` - Fast exact path lookups
- `idx_bas_points_path` - Fast exact path lookups
- `idx_equipment_path_prefix` - Fast wildcard searches (`/B1/3/*/HVAC/*`)
- `idx_bas_points_path_prefix` - Fast wildcard searches

### Why Indexes Matter:
Without indexes, searching for equipment by path would be like reading every page of a book to find one word. With indexes, it's like using the index in the back of the book - instant lookup!

---

## Quick Command Reference

```bash
# Check migration status
arx migrate status

# Run migration
arx migrate up

# Rollback if needed
arx migrate down

# Verify columns exist
psql -U your_username -d arxos_db -c "\d equipment"
psql -U your_username -d arxos_db -c "\d bas_points"

# Test queries
psql -U your_username -d arxos_db -c \
"SELECT id, name, path FROM equipment LIMIT 5;"
```

---

**Need more help?** Read the detailed guide:
- [Database Migrations Guide](docs/DATABASE_MIGRATIONS_GUIDE.md) - Complete explanation for beginners

---

**Once migration runs successfully, you're ready to test the universal naming convention with real equipment imports!** 🎉

