# Database Migrations - Simple Guide for Non-Developers

**For:** Joel and other IT field techs learning database management
**Last Updated:** October 12, 2025

---

## What Is a Database?

Think of a database like an **Excel spreadsheet on steroids**. Instead of one spreadsheet, you have many "tables" (like tabs in Excel), and each table has rows and columns.

**Example - Equipment Table:**
```
┌──────────┬──────────────┬──────────┬──────────┬────────┐
│    ID    │     Name     │   Type   │ Building │ Status │  ← COLUMNS (headers)
├──────────┼──────────────┼──────────┼──────────┼────────┤
│ eq-001   │ VAV Box 301  │ HVAC     │ B1       │ Active │  ← ROW (one piece of equipment)
│ eq-002   │ Panel 1A     │ Elec     │ B1       │ Active │  ← ROW (another piece)
│ eq-003   │ Outlet 12    │ Elec     │ B1       │ Active │  ← ROW (another piece)
└──────────┴──────────────┴──────────┴──────────┴────────┘
```

**Columns** = The types of information you store (like "Name", "Type", "Status")
**Rows** = The actual data (like "VAV Box 301")

---

## What Is a Database Migration?

A **migration** is a set of instructions that changes the structure of your database. It's like a **work order for the database**.

### Real-World Analogy (Electrical Panel):

**Current panel:** 20 circuits
**Migration:** "Add 4 new circuit breakers"
**Result:** Panel now has 24 circuits

### Database Example:

**Current table:** Equipment has columns for ID, Name, Type
**Migration:** "Add a column called 'path'"
**Result:** Equipment table now has ID, Name, Type, AND Path

---

## Why Do We Need Migrations?

### Problem Without Migration:
If we just start saving paths in the code, the database will say:
> ❌ "Error: Column 'path' doesn't exist in table 'equipment'"

It's like trying to plug something into a circuit that doesn't exist yet!

### Solution With Migration:
1. We tell the database: "Create a new column called 'path'"
2. Database creates the column
3. Now our code can save paths successfully

---

## How Migrations Work in ArxOS

### Migration Files Come in Pairs:

```
023_add_equipment_paths.up.sql     ← Goes UP (adds the column)
023_add_equipment_paths.down.sql   ← Goes DOWN (removes it if needed)
```

**UP** = Apply the change (move forward)
**DOWN** = Undo the change (rollback)

### Why Have Both?

If you mess up or need to test something, you can **rollback**:
- Run `.up.sql` → Column added
- Realize you made a mistake
- Run `.down.sql` → Column removed
- Fix the mistake
- Run `.up.sql` again → Column added correctly

---

## Step-by-Step: Adding the Path Column

### Step 1: Check What Number to Use

```bash
cd /Users/joelpate/repos/arxos
ls internal/migrations/*.up.sql | tail -3
```

You'll see something like:
```
020_uuid_migration.up.sql
021_user_management.up.sql
022_item_relationships.up.sql
```

The last one is **022**, so your new migration will be **023**.

### Step 2: Create the UP Migration File

Create: `internal/migrations/023_add_equipment_paths.up.sql`

**Contents:**
```sql
-- Migration 023: Add path columns for universal naming convention
-- Author: Joel
-- Date: 2025-10-12
-- Purpose: Add path column to store equipment addresses like /B1/3/301/HVAC/VAV-301

-- Add path column to equipment table
ALTER TABLE equipment
ADD COLUMN IF NOT EXISTS path TEXT;

-- Add path column to bas_points table
ALTER TABLE bas_points
ADD COLUMN IF NOT EXISTS path TEXT;

-- Create indexes so we can search by path quickly
-- (Like adding an index to the back of a book)
CREATE INDEX IF NOT EXISTS idx_equipment_path
ON equipment(path);

CREATE INDEX IF NOT EXISTS idx_bas_points_path
ON bas_points(path);

-- Special indexes for wildcard searches (like /B1/3/*/HVAC/*)
CREATE INDEX IF NOT EXISTS idx_equipment_path_prefix
ON equipment(path text_pattern_ops);

CREATE INDEX IF NOT EXISTS idx_bas_points_path_prefix
ON bas_points(path text_pattern_ops);

-- Add documentation about what the column is for
COMMENT ON COLUMN equipment.path IS
'Universal naming convention path (e.g. /B1/3/301/HVAC/VAV-301)';

COMMENT ON COLUMN bas_points.path IS
'Universal naming convention path (e.g. /B1/3/301/BAS/AI-1-1)';
```

### Step 3: Create the DOWN Migration File

Create: `internal/migrations/023_add_equipment_paths.down.sql`

**Contents:**
```sql
-- Migration 023 DOWN: Remove path columns
-- This removes the changes if we need to rollback

-- Drop indexes first
DROP INDEX IF EXISTS idx_equipment_path_prefix;
DROP INDEX IF EXISTS idx_bas_points_path_prefix;
DROP INDEX IF EXISTS idx_equipment_path;
DROP INDEX IF EXISTS idx_bas_points_path;

-- Drop the columns
ALTER TABLE equipment DROP COLUMN IF EXISTS path;
ALTER TABLE bas_points DROP COLUMN IF EXISTS path;
```

### Step 4: Run the Migration

**Option A: Using Make (recommended):**
```bash
cd /Users/joelpate/repos/arxos
make db-migrate
```

**Option B: Using scripts (if available):**
```bash
./scripts/migrate-database.sh
```

**Option C: Manual (if other options don't work):**
```bash
psql -U your_username -d arxos_db -f internal/migrations/023_add_equipment_paths.up.sql
```

### Step 5: Verify It Worked

Check that the column was added:
```bash
psql -U your_username -d arxos_db

-- Then in psql:
\d equipment;
```

You should see the new `path` column listed!

---

## What Each Part Does

### ALTER TABLE
```sql
ALTER TABLE equipment ADD COLUMN path TEXT;
```
**Translation:** "Hey database, take the 'equipment' table and add a new column called 'path' that stores text."

### CREATE INDEX
```sql
CREATE INDEX idx_equipment_path ON equipment(path);
```
**Translation:** "Create a lookup index on the 'path' column so searches are fast."

**Analogy:** Like creating an index at the back of a book. Without it, you'd have to read every page to find something. With it, you jump right to the page you need.

### IF NOT EXISTS
```sql
ADD COLUMN IF NOT EXISTS path TEXT;
```
**Translation:** "Only add this column if it doesn't already exist."

**Why?** If you run the migration twice by accident, it won't crash. It'll just say "Already exists, skipping."

---

## Common Issues & Solutions

### Issue 1: "Migration Already Applied"
**Symptom:** Migration runs but says "column already exists"
**Solution:** This is fine! The `IF NOT EXISTS` prevents errors. The column was already added.

### Issue 2: "Permission Denied"
**Symptom:** Error about not having permission
**Solution:** You need to run as the database user (usually `postgres` or your username)
```bash
sudo -u postgres make db-migrate
```

### Issue 3: "Database Not Found"
**Symptom:** Can't connect to database
**Solution:** Make sure PostgreSQL is running and the database exists
```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it:
brew services start postgresql@14  # Mac
sudo systemctl start postgresql    # Linux
```

### Issue 4: "Can't Find Migration Files"
**Symptom:** Says no migrations to run
**Solution:** Make sure you're in the right directory
```bash
cd /Users/joelpate/repos/arxos
pwd  # Should show /Users/joelpate/repos/arxos
```

---

## Testing Your Migration

### Before Running (What You Should See):
```bash
# Try to query the path column - should fail
psql -U your_username -d arxos_db -c "SELECT path FROM equipment LIMIT 1;"
# Error: column "path" does not exist
```

### After Running (What You Should See):
```bash
# Query should work now
psql -U your_username -d arxos_db -c "SELECT id, name, path FROM equipment LIMIT 5;"
# Shows results (path will be NULL for now, that's fine)
```

---

## Understanding the Results

### What Happens After Migration:

**BEFORE:**
```
equipment table:
┌─────────┬──────────┬──────────┐
│   ID    │   Name   │  Type    │
├─────────┼──────────┼──────────┤
│ eq-001  │ VAV Box  │ HVAC     │
└─────────┴──────────┴──────────┘
```

**AFTER (immediately after migration):**
```
equipment table:
┌─────────┬──────────┬──────────┬───────┐
│   ID    │   Name   │  Type    │ Path  │  ← NEW COLUMN!
├─────────┼──────────┼──────────┼───────┤
│ eq-001  │ VAV Box  │ HVAC     │ NULL  │  ← Empty for now
└─────────┴──────────┴──────────┴───────┘
```

The `path` column exists now, but it's empty (NULL). That's expected!

**AFTER (new equipment is imported):**
```
equipment table:
┌─────────┬──────────┬──────────┬────────────────────────┐
│   ID    │   Name   │  Type    │ Path                   │
├─────────┼──────────┼──────────┼────────────────────────┤
│ eq-001  │ VAV Box  │ HVAC     │ /B1/3/301/HVAC/VAV-301 │  ← Populated!
└─────────┴──────────┴──────────┴────────────────────────┘
```

---

## Next Steps After Migration

Once the migration runs successfully:

1. **Test IFC Import**
   ```bash
   arx import /path/to/building.ifc
   ```
   New equipment should have paths like `/B1/3/301/HVAC/VAV-301`

2. **Test BAS Import**
   ```bash
   arx bas import /path/to/points.csv
   ```
   BAS points should have paths like `/B1/3/301/BAS/AI-1-1`

3. **Verify Paths Saved**
   ```bash
   psql -U your_username -d arxos_db -c \
   "SELECT name, path FROM equipment WHERE path IS NOT NULL LIMIT 10;"
   ```
   You should see equipment with paths!

---

## Quick Reference

### File Locations:
```
/Users/joelpate/repos/arxos/internal/migrations/
  ├── 023_add_equipment_paths.up.sql    ← CREATE THIS
  └── 023_add_equipment_paths.down.sql  ← CREATE THIS
```

### Run Migration:
```bash
cd /Users/joelpate/repos/arxos
make db-migrate
```

### Check Results:
```bash
psql -U your_username -d arxos_db -c "\d equipment;"
```

### Test Query:
```bash
psql -U your_username -d arxos_db -c \
"SELECT id, name, path FROM equipment LIMIT 5;"
```

---

## Glossary for Non-Database People

| Term | What It Means | Real-World Analogy |
|------|---------------|-------------------|
| **Table** | A collection of related data | A spreadsheet tab |
| **Column** | A type of information | A column header in Excel |
| **Row** | A single record | A row in a spreadsheet |
| **Index** | Fast lookup structure | Index in the back of a book |
| **Migration** | Change to database structure | Work order for the database |
| **UP** | Apply changes | Install new circuit |
| **DOWN** | Undo changes | Remove circuit (rollback) |
| **NULL** | Empty/no value | Blank cell in Excel |
| **ALTER TABLE** | Modify a table | Modify a panel |
| **psql** | PostgreSQL command tool | Like SQL Server Management Studio |

---

## Getting Help

**If migration fails:**
1. Read the error message carefully
2. Check the migration file for typos
3. Make sure PostgreSQL is running
4. Verify you're in the correct directory
5. Check database connection settings in `configs/`

**Database connection info** is usually in:
- `configs/environments/development.yml`
- Or environment variables in `.env`

**Common connection settings:**
- Host: `localhost`
- Port: `5432`
- Database: `arxos_db` or `arxos`
- User: Your Mac username or `postgres`

---

**Remember:** Migrations are just SQL files that change your database structure. They're safe to run as long as you have backups and test on development first!

If you're nervous, **test on a copy of the database first** before running on production data.

