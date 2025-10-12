# Database Setup Progress Report

**Date:** October 11, 2025
**Status:** 🟡 In Progress - Migration Fixes Needed

---

## Successfully Applied Migrations ✅

1. ✅ **001_initial_schema** - Core tables (organizations, users, buildings, floors, rooms, equipment)
2. ✅ **002_postgres_enhancements** - UUID generation, triggers, views, full-text search (fixed JSON GIN index issue)
3. ✅ **003_spatial_anchors** - AR spatial anchors (fixed BLOB→bytea, floor_plans→buildings, type→equipment_type)
4. ✅ **004_floor_plans_compat** - Floor plans view (fixed CREATE VIEW IF NOT EXISTS, INSERT OR IGNORE)
5. ✅ **005_spatial_indices** - Simplified spatial indices (rewrote for current schema)

**Current Version:** 005
**Migrations Applied:** 5/21

---

## Issues Encountered & Fixed

### Migration 002 - JSON GIN Index
**Problem:** `data type json has no default operator class for access method "gin"`
**Fix:** Added conditional check for `jsonb` type before creating GIN index
**Status:** ✅ Fixed

### Migration 003 - PostgreSQL Syntax
**Problems:**
1. `BLOB` type doesn't exist (SQLite syntax)
2. `floor_plans` table doesn't exist
3. `e.type` column should be `e.equipment_type`
4. `CREATE VIEW IF NOT EXISTS` not supported

**Fixes:**
1. Changed `BLOB` → `bytea`
2. Changed `REFERENCES floor_plans(id)` → `REFERENCES buildings(id)`
3. Changed `e.type` → `e.equipment_type`
4. Changed `CREATE VIEW IF NOT EXISTS` → `CREATE OR REPLACE VIEW`

**Status:** ✅ Fixed

### Migration 004 - INSERT Syntax
**Problems:**
1. `CREATE VIEW IF NOT EXISTS` not supported
2. `INSERT OR IGNORE` (SQLite syntax)
3. Foreign key violation (DEFAULT_BUILDING doesn't exist)

**Fixes:**
1. Changed to `CREATE OR REPLACE VIEW`
2. Changed `INSERT OR IGNORE` → `INSERT ... ON CONFLICT DO NOTHING`
3. Removed default floor insert (would violate FK constraint)

**Status:** ✅ Fixed

### Migration 005 - Schema Mismatch
**Problem:** Migration expected PostGIS `GEOMETRY` columns but schema has `location_x/y/z` (REAL)
**Fix:** Created simplified version with basic indices on existing columns
**Status:** ✅ Fixed

### Migration Numbering Conflicts
**Problem:** Duplicate migration numbers (003, 006)
**Fix:** Renamed to avoid conflicts:
- `003_uuid_migration` → `020_uuid_migration`
- `006_user_management` → `021_user_management`

**Status:** ✅ Fixed

---

## Remaining Issues

### Migration 006 - Advanced Spatial Indices
**Status:** ❌ Failing
**Error:** `relation "equipment_positions" does not exist`
**Cause:** References tables from migration 005 that weren't created (simplified version)
**Action Needed:** Simplify or skip

### Migrations 007-011 - Ecosystem Features
**Status:** 🔍 Not yet attempted
**Likely Issues:** Schema mismatches, missing tables
**Priority:** Medium (not critical for BAS import)

### Migrations 012-019 - Core Features ⭐
**Status:** 🔍 Not yet attempted
**Priority:** HIGH - Required for BAS import
- 012: Components table
- 013: Version control
- 014: BAS integration (CRITICAL)
- 015: Git workflow
- 016-017: Pull requests & issues
- 018: Contributor management
- 019: Domain-agnostic rename

---

## Strategy Moving Forward

### Option A: Fix All Migrations Sequentially (Slow)
- Continue fixing each migration one by one
- Time: 2-3 hours estimated
- Risk: More schema mismatches likely

### Option B: Skip to Critical Migrations (Fast) ⭐ RECOMMENDED
- Rename problematic migrations (006-011) to higher numbers or .skip extension
- Jump directly to migrations 012-019 which are critical for BAS
- Come back to advanced spatial features later
- Time: 30 minutes estimated

### Option C: Manual Schema Creation (Fastest)
- Run critical migration SQL files manually in correct order
- Verify tables exist
- Update schema_migrations table
- Time: 15 minutes

---

## Critical Tables Status

**For BAS Import, we need:**
- ✅ `buildings` - EXISTS
- ✅ `floors` - EXISTS
- ✅ `rooms` - EXISTS
- ✅ `equipment` - EXISTS
- ❌ `components` - MISSING (migration 012)
- ❌ `bas_systems` - MISSING (migration 014)
- ❌ `bas_points` - MISSING (migration 014)
- ❌ `version_snapshots` - MISSING (migration 013)
- ❌ `branches` - MISSING (migration 015)

---

## Recommendation

**Implement Option B:**

1. Skip migrations 006-011 for now:
```bash
cd /Users/joelpate/repos/arxos/internal/migrations
for i in {006..011}; do
  find . -name "${i}_*.up.sql" -exec mv {} {}.skip \;
done
```

2. Continue with migrations 012-019:
```bash
export DATABASE_URL="postgres://joelpate@localhost:5432/arxos_dev?sslmode=disable"
./bin/arx migrate up
```

3. Test BAS import:
```bash
./bin/arx bas import test_data/bas/metasys_sample_export.csv --building test-001
```

4. Come back to advanced spatial features (006-011) after core functionality works

---

## Next Steps

1. Decide on strategy (recommend Option B)
2. Execute chosen strategy
3. Verify critical tables exist
4. Test BAS import end-to-end
5. Document any remaining issues

---

**Ready for decision on how to proceed.**

