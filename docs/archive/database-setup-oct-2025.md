# ArxOS Database Setup Guide

**Last Updated:** October 11, 2025
**Status:** Tested and Verified

---

## Overview

ArxOS requires PostgreSQL 14+ with PostGIS extension for spatial operations. This guide covers setup for local development and testing.

---

## Quick Start (macOS)

```bash
# 1. Install PostgreSQL + PostGIS
brew install postgresql@14 postgis

# 2. Start PostgreSQL
brew services start postgresql@14

# 3. Run setup script
cd /path/to/arxos
./scripts/setup-dev-database.sh

# 4. Run migrations
go run cmd/arx/main.go migrate up

# 5. Verify
go run cmd/arx/main.go health
```

**Done!** Your database is ready.

---

## Detailed Setup

### Step 1: Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@14 postgis
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-14 postgresql-14-postgis-3
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Docker:**
```bash
docker run -d \
  --name arxos-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=arxos \
  -e POSTGRES_DB=arxos_dev \
  postgis/postgis:14-3.3
```

**Windows:**
1. Download PostgreSQL 14 from https://www.postgresql.org/download/windows/
2. Run installer, enable PostGIS in Stack Builder
3. Start PostgreSQL service

---

### Step 2: Verify PostgreSQL Installation

```bash
# Check PostgreSQL is running
pg_isready

# Should output: /tmp:5432 - accepting connections

# Check version
psql --version

# Should output: psql (PostgreSQL) 14.x
```

---

### Step 3: Run Setup Script

The automated script handles everything:

```bash
cd /path/to/arxos
./scripts/setup-dev-database.sh
```

**What it does:**
- Checks PostgreSQL is running
- Creates database `arxos_dev`
- Enables PostGIS extension
- Creates `.env` file with connection details
- Provides next steps

**Script is idempotent:** Safe to run multiple times.

---

### Step 4: Manual Setup (Alternative)

If you prefer manual setup or the script fails:

```bash
# Create database
createdb arxos_dev

# Enable PostGIS
psql arxos_dev -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql arxos_dev -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"

# Verify PostGIS
psql arxos_dev -c "SELECT PostGIS_Version();"
```

---

### Step 5: Configure ArxOS

Update `configs/environments/development.yml`:

```yaml
postgis:
  host: localhost
  port: 5432
  database: arxos_dev
  user: <your-username>  # Usually same as whoami
  password: ""           # Empty for local development
  sslmode: disable

database:
  max_open_conns: 25
  max_idle_conns: 5
  conn_lifetime: 5m
```

**Or use environment variables:**

```bash
export POSTGIS_HOST=localhost
export POSTGIS_PORT=5432
export POSTGIS_DATABASE=arxos_dev
export POSTGIS_USER=$(whoami)
export POSTGIS_PASSWORD=""
export POSTGIS_SSLMODE=disable
```

---

### Step 6: Run Migrations

Migrations create all tables and indexes:

```bash
cd /path/to/arxos

# Run all migrations
go run cmd/arx/main.go migrate up

# Check migration status
go run cmd/arx/main.go migrate status
```

**Expected output:**
```
✓ 002_postgres_enhancements.up.sql - Applied
✓ 003_spatial_anchors.up.sql - Applied
✓ 004_floor_plans_compat.up.sql - Applied
...
✓ 021_user_management.up.sql - Applied

Total migrations applied: 20
```

---

### Step 7: Verify Setup

```bash
# Check database connection
go run cmd/arx/main.go health

# Should output:
# ✓ Database: Connected
# ✓ PostGIS: Available
# ✓ Cache: Ready
# ✓ System: Operational
```

---

## Test Database

For running tests, create a separate test database:

```bash
# Create test database
createdb arxos_test

# Enable PostGIS
psql arxos_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Set environment variable
export ARXOS_TEST_DB="postgres://$(whoami)@localhost:5432/arxos_test?sslmode=disable"

# Run tests
go test ./...
```

---

## Troubleshooting

### Problem: PostgreSQL Not Running

**Symptoms:**
```
Error: Failed to initialize ArxOS container
Error: could not connect to database
```

**Solution:**
```bash
# Check status
pg_isready

# Start PostgreSQL
# macOS:
brew services start postgresql@14

# Ubuntu:
sudo systemctl start postgresql

# Docker:
docker start arxos-postgres
```

---

### Problem: Database Doesn't Exist

**Symptoms:**
```
FATAL: database "arxos_dev" does not exist
```

**Solution:**
```bash
createdb arxos_dev
```

---

### Problem: PostGIS Not Installed

**Symptoms:**
```
ERROR: could not open extension control file
ERROR: extension "postgis" is not available
```

**Solution:**
```bash
# macOS:
brew install postgis

# Ubuntu:
sudo apt-get install postgresql-14-postgis-3

# Then enable in database:
psql arxos_dev -c "CREATE EXTENSION postgis;"
```

---

### Problem: Permission Denied

**Symptoms:**
```
FATAL: role "youruser" does not exist
```

**Solution:**
```bash
# Create user (as postgres superuser)
sudo -u postgres createuser -s $(whoami)

# Or in psql:
sudo -u postgres psql
CREATE ROLE youruser WITH LOGIN SUPERUSER;
```

---

### Problem: Port Already In Use

**Symptoms:**
```
could not bind IPv4 address "0.0.0.0": Address already in use
```

**Solution:**
```bash
# Find what's using port 5432
lsof -i :5432

# Stop other PostgreSQL instance or use different port
# In config, change:
postgis:
  port: 5433  # Use different port
```

---

### Problem: Migrations Fail

**Symptoms:**
```
Error: migration 014 failed
```

**Solution:**
```bash
# Check which migrations are applied
go run cmd/arx/main.go migrate status

# Roll back one migration
go run cmd/arx/main.go migrate down

# Fix the issue, then reapply
go run cmd/arx/main.go migrate up
```

---

## Database Maintenance

### Reset Database (Clean Slate)

```bash
# Drop and recreate
dropdb arxos_dev
createdb arxos_dev
psql arxos_dev -c "CREATE EXTENSION postgis;"

# Run migrations again
go run cmd/arx/main.go migrate up
```

### Backup Database

```bash
# Backup to file
pg_dump arxos_dev > arxos_backup_$(date +%Y%m%d).sql

# Restore from file
psql arxos_dev < arxos_backup_20251011.sql
```

### Check Database Size

```bash
psql arxos_dev -c "
  SELECT pg_size_pretty(pg_database_size('arxos_dev')) AS size;
"
```

### View Tables

```bash
psql arxos_dev -c "\dt"

# Or with sizes:
psql arxos_dev -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## Docker Compose Setup

For a complete development environment:

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:14-3.3
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: arxos_dev
      POSTGRES_USER: arxos
      POSTGRES_PASSWORD: arxos
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Start with:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

---

## Production Considerations

### Security

1. **Use strong passwords:**
   ```sql
   ALTER USER arxos WITH PASSWORD 'strong-random-password';
   ```

2. **Enable SSL:**
   ```yaml
   postgis:
     sslmode: require
   ```

3. **Restrict access:**
   ```
   # pg_hba.conf
   host    arxos_prod    arxos    10.0.0.0/8    md5
   ```

### Performance

1. **Tune PostgreSQL:**
   ```
   # postgresql.conf
   shared_buffers = 256MB
   effective_cache_size = 1GB
   work_mem = 16MB
   maintenance_work_mem = 128MB
   ```

2. **Create indexes:**
   - Already included in migrations
   - Spatial indexes on geometry columns
   - Regular indexes on foreign keys

3. **Monitor performance:**
   ```sql
   SELECT * FROM pg_stat_activity WHERE datname = 'arxos_prod';
   ```

---

## Verification Checklist

After setup, verify:

- [ ] PostgreSQL is running: `pg_isready`
- [ ] Database created: `psql -l | grep arxos_dev`
- [ ] PostGIS enabled: `psql arxos_dev -c "SELECT PostGIS_Version();"`
- [ ] Config file updated: Check `configs/environments/development.yml`
- [ ] Migrations applied: `go run cmd/arx/main.go migrate status`
- [ ] Health check passes: `go run cmd/arx/main.go health`
- [ ] Can create building: `go run cmd/arx/main.go building create --name "Test"`

**All checked?** You're ready to develop!

---

## Getting Help

- **PostgreSQL Docs:** https://www.postgresql.org/docs/14/
- **PostGIS Docs:** https://postgis.net/documentation/
- **ArxOS Issues:** https://github.com/arx-os/arxos/issues
- **Slack/Discord:** [Your community link]

---

## Summary

```bash
# Complete setup in 5 commands:
brew install postgresql@14 postgis
brew services start postgresql@14
./scripts/setup-dev-database.sh
go run cmd/arx/main.go migrate up
go run cmd/arx/main.go health
```

That's it! Your ArxOS database is ready for development.

