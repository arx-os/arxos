# PostgreSQL Terminal Guide
## Everything You Need Without GUI Tools

**For:** Joel (IT field tech)
**Goal:** Manage PostgreSQL entirely from terminal
**No GUI Required:** pgAdmin, TablePlus, etc. not needed

---

## Quick Start

### 1. Run the Setup Script
```bash
cd /Users/joelpate/repos/arxos
./scripts/setup-database-terminal.sh
```

This creates:
- `arxos` database (for development)
- `arxos_test` database (for running tests)
- Users with correct permissions
- PostGIS extension enabled

### 2. Set Environment Variables
```bash
# For current session
source /tmp/arxos_env.sh

# Or add to ~/.zshrc (permanent)
echo 'export DATABASE_URL="postgres://arxos:arxos_dev@localhost:5432/arxos?sslmode=disable"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Run ArxOS Migrations
```bash
go run cmd/arx/main.go migrate up
```

### 4. Test It Works
```bash
go run cmd/arx/main.go health
```

---

## Essential PostgreSQL Commands

### Connecting to Database

```bash
# Connect to arxos database
psql -U arxos -d arxos

# Connect as your Mac user (usually has admin privileges)
psql postgres

# Connect with password prompt
psql -U arxos -d arxos -W

# Connect with inline password (not recommended for production)
PGPASSWORD=arxos_dev psql -U arxos -d arxos
```

### Inside psql (After Connecting)

```sql
-- Basic Commands (start with backslash)
\?              -- Show all psql commands
\q              -- Quit psql
\l              -- List all databases
\c arxos        -- Connect to 'arxos' database
\dt             -- List all tables
\d buildings    -- Describe 'buildings' table (show columns)
\du             -- List all users/roles
\dn             -- List all schemas

-- Database Info
SELECT version();                           -- PostgreSQL version
SELECT PostGIS_Version();                   -- PostGIS version
SELECT current_database();                  -- Current database name
SELECT current_user;                        -- Current user

-- Table Info
SELECT count(*) FROM buildings;            -- Count rows in buildings table
SELECT * FROM buildings LIMIT 5;           -- Show first 5 buildings
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';             -- List all tables

-- Disk Usage
SELECT pg_size_pretty(pg_database_size('arxos')) as size;
SELECT pg_size_pretty(pg_total_relation_size('buildings')) as table_size;
```

### One-Line Commands (Without Entering psql)

```bash
# List all databases
psql -l

# Run a single query
psql -U arxos -d arxos -c "SELECT * FROM buildings;"

# Run a SQL file
psql -U arxos -d arxos -f my_query.sql

# Export query results to CSV
psql -U arxos -d arxos -c "SELECT * FROM buildings;" --csv > buildings.csv

# Count rows in table
psql -U arxos -d arxos -c "SELECT count(*) FROM buildings;"

# Show table structure
psql -U arxos -d arxos -c "\d buildings"
```

---

## Common Tasks

### View All Buildings

```bash
# Quick view
psql -U arxos -d arxos -c "SELECT id, name, address FROM buildings;"

# Formatted output
psql -U arxos -d arxos -c "SELECT id, name, address FROM buildings;" -x

# Save to file
psql -U arxos -d arxos -c "SELECT * FROM buildings;" > buildings.txt
```

### Create a Building Manually

```bash
psql -U arxos -d arxos <<SQL
INSERT INTO buildings (id, name, address, city, state, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'Test School',
    '123 Main St',
    'San Francisco',
    'CA',
    NOW(),
    NOW()
);
SQL
```

### Check Migration Status

```bash
# Via ArxOS CLI
go run cmd/arx/main.go migrate status

# Directly in database
psql -U arxos -d arxos -c "SELECT * FROM schema_migrations ORDER BY version;"
```

### View Recent Changes

```bash
# Show recently created buildings
psql -U arxos -d arxos -c "
SELECT id, name, created_at
FROM buildings
ORDER BY created_at DESC
LIMIT 10;
"
```

### Search for Equipment

```bash
# Find all HVAC equipment
psql -U arxos -d arxos -c "
SELECT id, name, type, status
FROM equipment
WHERE type = 'hvac';
"

# Find equipment in specific building
psql -U arxos -d arxos -c "
SELECT e.id, e.name, e.type, b.name as building
FROM equipment e
JOIN buildings b ON e.building_id = b.id
WHERE b.name = 'Lincoln Elementary';
"
```

---

## Database Management

### Start/Stop PostgreSQL

```bash
# Check if running
pg_isready

# Start PostgreSQL
brew services start postgresql@14

# Stop PostgreSQL
brew services stop postgresql@14

# Restart PostgreSQL
brew services restart postgresql@14

# Check status
brew services list | grep postgresql
```

### Backup Database

```bash
# Backup entire database
pg_dump -U arxos arxos > arxos_backup_$(date +%Y%m%d).sql

# Backup just the schema (no data)
pg_dump -U arxos arxos --schema-only > arxos_schema.sql

# Backup just the data (no schema)
pg_dump -U arxos arxos --data-only > arxos_data.sql

# Backup specific tables
pg_dump -U arxos arxos -t buildings -t equipment > buildings_backup.sql
```

### Restore Database

```bash
# Restore from backup
psql -U arxos -d arxos < arxos_backup_20251011.sql

# Create new database and restore
createdb -U arxos arxos_restore
psql -U arxos -d arxos_restore < arxos_backup_20251011.sql
```

### Reset Database (Careful!)

```bash
# Drop and recreate database
psql postgres <<SQL
DROP DATABASE IF EXISTS arxos;
CREATE DATABASE arxos OWNER arxos;
SQL

# Re-enable PostGIS
psql -U arxos -d arxos <<SQL
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
CREATE EXTENSION "uuid-ossp";
SQL

# Re-run migrations
go run cmd/arx/main.go migrate up
```

---

## Troubleshooting

### Can't Connect to Database

```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it
brew services start postgresql@14

# Check connection with verbose output
psql -U arxos -d arxos -h localhost -p 5432 -W
```

### Permission Denied

```bash
# Grant permissions to user
psql postgres <<SQL
GRANT ALL PRIVILEGES ON DATABASE arxos TO arxos;
\c arxos
GRANT ALL ON ALL TABLES IN SCHEMA public TO arxos;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO arxos;
SQL
```

### Database Doesn't Exist

```bash
# Create it
psql postgres -c "CREATE DATABASE arxos OWNER arxos;"

# Or re-run setup script
./scripts/setup-database-terminal.sh
```

### PostGIS Extension Missing

```bash
# Install PostGIS
brew install postgis

# Enable in database
psql -U arxos -d arxos -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Forgot Password

```bash
# Reset password for arxos user
psql postgres -c "ALTER USER arxos WITH PASSWORD 'arxos_dev';"
```

### Too Many Connections

```bash
# Check current connections
psql -U arxos -d arxos -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'arxos';"

# Kill idle connections
psql postgres <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'arxos'
AND state = 'idle'
AND pid <> pg_backend_pid();
SQL
```

---

## Useful Queries

### Show All Tables and Row Counts

```sql
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### Find Largest Tables

```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

### Show Recent Activity

```sql
SELECT
    datname as database,
    usename as user,
    application_name,
    client_addr,
    state,
    query
FROM pg_stat_activity
WHERE datname = 'arxos';
```

### Check Index Usage

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

---

## ArxOS-Specific Queries

### Count Everything

```bash
psql -U arxos -d arxos <<SQL
SELECT 'Buildings' as entity, count(*) as count FROM buildings
UNION ALL
SELECT 'Floors', count(*) FROM floors
UNION ALL
SELECT 'Rooms', count(*) FROM rooms
UNION ALL
SELECT 'Equipment', count(*) FROM equipment
UNION ALL
SELECT 'Users', count(*) FROM users
ORDER BY count DESC;
SQL
```

### View Building Hierarchy

```bash
psql -U arxos -d arxos <<SQL
SELECT
    b.name as building,
    f.name as floor,
    r.name as room,
    count(e.id) as equipment_count
FROM buildings b
LEFT JOIN floors f ON f.building_id = b.id
LEFT JOIN rooms r ON r.floor_id = f.id
LEFT JOIN equipment e ON e.room_id = r.id
GROUP BY b.name, f.name, r.name
ORDER BY b.name, f.level, r.name;
SQL
```

### Find Orphaned Equipment (No Room Assigned)

```bash
psql -U arxos -d arxos -c "
SELECT id, name, type, status
FROM equipment
WHERE room_id IS NULL;
"
```

### Show Spatial Data (PostGIS)

```bash
psql -U arxos -d arxos <<SQL
SELECT
    id,
    name,
    ST_X(location::geometry) as longitude,
    ST_Y(location::geometry) as latitude
FROM buildings
WHERE location IS NOT NULL;
SQL
```

---

## psql Configuration

### Create ~/.psqlrc for Better Defaults

```bash
cat > ~/.psqlrc <<'PSQLRC'
-- Show query execution time
\timing

-- Use extended display for wide results
\x auto

-- Better NULL display
\pset null '∅'

-- Show line numbers in editor
\set HISTSIZE 10000

-- Use vim as editor
\setenv EDITOR vi

-- Shortcuts
\set show_slow_queries 'SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;'
\set show_tables 'SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||''.''||tablename)) as size FROM pg_tables WHERE schemaname = ''public'' ORDER BY pg_total_relation_size(schemaname||''.''||tablename) DESC;'
PSQLRC

echo "✓ Created ~/.psqlrc with better defaults"
```

Now you can use shortcuts:
```bash
psql -U arxos -d arxos
# Inside psql:
:show_tables    # Shows all tables with sizes
:show_slow_queries  # Shows slow queries
```

---

## Integration with ArxOS

### After Database Setup, Use ArxOS CLI

```bash
# Health check (tests database connection)
go run cmd/arx/main.go health

# Run migrations
go run cmd/arx/main.go migrate up

# Check migration status
go run cmd/arx/main.go migrate status

# Create a building (after migrations)
go run cmd/arx/main.go building create \
  --name "Lincoln Elementary" \
  --address "123 Main St, San Francisco, CA"

# List buildings
go run cmd/arx/main.go building list

# View in database
psql -U arxos -d arxos -c "SELECT id, name, address FROM buildings;"
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│ PostgreSQL Terminal Quick Reference                 │
├─────────────────────────────────────────────────────┤
│ Connect:                                            │
│   psql -U arxos -d arxos                            │
│                                                      │
│ List databases:                                     │
│   psql -l                                           │
│                                                      │
│ Run query:                                          │
│   psql -U arxos -d arxos -c "SELECT * FROM table;" │
│                                                      │
│ Backup:                                             │
│   pg_dump -U arxos arxos > backup.sql              │
│                                                      │
│ Restore:                                            │
│   psql -U arxos -d arxos < backup.sql              │
│                                                      │
│ Check status:                                       │
│   pg_isready                                        │
│                                                      │
│ Inside psql:                                        │
│   \l        List databases                          │
│   \dt       List tables                             │
│   \d table  Describe table                          │
│   \q        Quit                                    │
└─────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Run Setup Script:**
   ```bash
   ./scripts/setup-database-terminal.sh
   ```

2. **Source Environment Variables:**
   ```bash
   source /tmp/arxos_env.sh
   ```

3. **Run Migrations:**
   ```bash
   go run cmd/arx/main.go migrate up
   ```

4. **Test Connection:**
   ```bash
   go run cmd/arx/main.go health
   ```

5. **Create First Building:**
   ```bash
   go run cmd/arx/main.go building create \
     --name "Test Building" \
     --address "123 Test St"
   ```

6. **Verify in Database:**
   ```bash
   psql -U arxos -d arxos -c "SELECT * FROM buildings;"
   ```

---

## Learning Resources

- **PostgreSQL Docs:** https://www.postgresql.org/docs/14/
- **PostGIS Manual:** https://postgis.net/docs/manual-3.3/
- **psql Guide:** https://www.postgresql.org/docs/14/app-psql.html

---

**Remember:** No GUI needed! Everything can be done from terminal. This is actually better for:
- Scripting and automation
- Remote server management
- Speed (no clicking around)
- Reproducibility (scripts > manual steps)

You're already good with terminal from IT work - PostgreSQL is just another CLI tool.


