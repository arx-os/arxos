# Database Setup Guide

**Last Updated:** October 15, 2025  
**Status:** Tested and Verified

---

## Overview

Arxos requires PostgreSQL 14+ with PostGIS extension for spatial operations. This guide covers setup for local development, testing, and production environments.

---

## Quick Start

### macOS
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

### Windows
```powershell
# 1. Install PostgreSQL 14 from https://www.postgresql.org/download/windows/
# 2. Enable PostGIS in Stack Builder during installation
# 3. Start PostgreSQL service

# 4. Run setup
cd C:\path\to\arxos
.\scripts\setup-dev-database.sh

# 5. Run migrations
go run cmd\arx\main.go migrate up

# 6. Verify
go run cmd\arx\main.go health
```

### Ubuntu/Debian
```bash
# 1. Install PostgreSQL + PostGIS
sudo apt-get update
sudo apt-get install postgresql-14 postgresql-14-postgis-3

# 2. Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

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
3. Start PostgreSQL service from Services panel

---

### Step 2: Verify Installation

```bash
# Check PostgreSQL is running
pg_isready

# Should output: /tmp:5432 - accepting connections

# Check version
psql --version

# Should output: psql (PostgreSQL) 14.x
```

---

### Step 3: Create Database

**Option A: Automated Setup (Recommended)**

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

**Option B: Manual Setup**

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

### Step 4: Configure Arxos

**Method 1: Configuration File**

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

**Method 2: Environment Variables**

```bash
export POSTGIS_HOST=localhost
export POSTGIS_PORT=5432
export POSTGIS_DATABASE=arxos_dev
export POSTGIS_USER=$(whoami)
export POSTGIS_PASSWORD=""
export POSTGIS_SSLMODE=disable
```

**Method 3: .env File**

Create `.env` in project root:

```env
POSTGIS_HOST=localhost
POSTGIS_PORT=5432
POSTGIS_DATABASE=arxos_dev
POSTGIS_USER=youruser
POSTGIS_PASSWORD=
POSTGIS_SSLMODE=disable
```

---

### Step 5: Run Migrations

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
✓ 001_initial_schema.up.sql - Applied
✓ 002_postgres_enhancements.up.sql - Applied
✓ 003_spatial_anchors.up.sql - Applied
...
✓ 023_add_equipment_paths.up.sql - Applied

Total migrations applied: 23
```

**See [Migration Guide](migrations.md) for detailed migration instructions.**

---

### Step 6: Verify Setup

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

## Test Database Setup

For running tests, create a separate test database:

```bash
# Create test database
createdb arxos_test

# Enable PostGIS
psql arxos_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql arxos_test -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"

# Set environment variable
export ARXOS_TEST_DB="postgres://$(whoami)@localhost:5432/arxos_test?sslmode=disable"

# Run migrations on test database
go run cmd/arx/main.go migrate up --database arxos_test

# Run tests
go test ./...
```

**Best Practice:** Keep test and dev databases separate to avoid data contamination.

---

## Production Setup

### Database Configuration

For production deployments:

```yaml
postgis:
  host: your-db-host.example.com
  port: 5432
  database: arxos_production
  user: arxos_app
  password: ${DB_PASSWORD}  # From environment variable
  sslmode: require          # Always use SSL in production

database:
  max_open_conns: 100       # Higher for production
  max_idle_conns: 25
  conn_lifetime: 15m
  
  # Connection pooling
  pool_max_lifetime: 1h
  pool_health_check: 30s
```

### Security Best Practices

**1. Use Strong Passwords:**
```bash
# Generate strong password
openssl rand -base64 32
```

**2. Restrict Network Access:**
```bash
# Edit pg_hba.conf
# Only allow connections from app servers
hostssl arxos_production arxos_app 10.0.1.0/24 md5
```

**3. Enable SSL:**
```bash
# In postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
```

**4. Regular Backups:**
```bash
# Daily backup script
pg_dump -Fc arxos_production > backup_$(date +%Y%m%d).dump

# Automated with cron
0 2 * * * /path/to/backup-script.sh
```

---

## Troubleshooting

### PostgreSQL Not Running

**Symptoms:**
```
Error: Failed to initialize Arxos container
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

### Database Doesn't Exist

**Symptoms:**
```
FATAL: database "arxos_dev" does not exist
```

**Solution:**
```bash
createdb arxos_dev
psql arxos_dev -c "CREATE EXTENSION postgis;"
```

---

### PostGIS Not Installed

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

### Permission Denied

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

### Connection Refused

**Symptoms:**
```
could not connect to server: Connection refused
Is the server running on host "localhost" and accepting TCP/IP connections on port 5432?
```

**Solution:**
```bash
# Check if PostgreSQL is listening
sudo lsof -i :5432

# Check postgresql.conf
# Make sure listen_addresses is not commented out
listen_addresses = 'localhost'

# Restart PostgreSQL
brew services restart postgresql@14
```

---

### Slow Queries

**Symptoms:**
- Database operations taking a long time
- High CPU usage on database server

**Solutions:**

**1. Check Missing Indexes:**
```sql
-- Find tables without indexes
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public';
```

**2. Analyze Query Performance:**
```sql
-- Use EXPLAIN ANALYZE
EXPLAIN ANALYZE 
SELECT * FROM equipment WHERE building_id = 'xxx';
```

**3. Vacuum and Analyze:**
```bash
# Regular maintenance
psql arxos_dev -c "VACUUM ANALYZE;"

# For specific table
psql arxos_dev -c "VACUUM ANALYZE equipment;"
```

**4. Connection Pool Tuning:**
```yaml
database:
  max_open_conns: 50  # Adjust based on load
  max_idle_conns: 10
  conn_lifetime: 10m
```

---

## Database Maintenance

### Regular Tasks

**Daily:**
```bash
# Backup
pg_dump arxos_production > backup_daily.sql
```

**Weekly:**
```bash
# Vacuum and analyze
psql arxos_production -c "VACUUM ANALYZE;"

# Check database size
psql arxos_production -c "SELECT pg_size_pretty(pg_database_size('arxos_production'));"
```

**Monthly:**
```bash
# Full backup
pg_dump -Fc arxos_production > backup_monthly_$(date +%Y%m).dump

# Check for bloat
psql arxos_production -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
LIMIT 10;"
```

### Performance Monitoring

**Check Active Connections:**
```sql
SELECT count(*) FROM pg_stat_activity 
WHERE datname = 'arxos_production';
```

**Check Long-Running Queries:**
```sql
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
  AND now() - pg_stat_activity.query_start > interval '5 minutes';
```

**Check Table Sizes:**
```sql
SELECT tablename, 
       pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
```

---

## Backup and Restore

### Backup

**Full Backup:**
```bash
# Text format (human-readable)
pg_dump arxos_production > backup.sql

# Custom format (compressed, for pg_restore)
pg_dump -Fc arxos_production > backup.dump

# Directory format (parallel dump)
pg_dump -Fd arxos_production -j 4 -f backup_dir/
```

**Schema Only:**
```bash
pg_dump --schema-only arxos_production > schema.sql
```

**Data Only:**
```bash
pg_dump --data-only arxos_production > data.sql
```

**Single Table:**
```bash
pg_dump -t equipment arxos_production > equipment_backup.sql
```

### Restore

**From Text Format:**
```bash
psql arxos_production < backup.sql
```

**From Custom Format:**
```bash
pg_restore -d arxos_production backup.dump
```

**From Directory Format:**
```bash
pg_restore -d arxos_production -j 4 backup_dir/
```

**Clean and Restore (drops existing data):**
```bash
pg_restore -d arxos_production --clean --if-exists backup.dump
```

---

## Next Steps

- **[Migration Guide](migrations.md)** - Learn how to create and run database migrations
- **[Postgres Terminal Guide](postgres-reference.md)** - Command reference for PostgreSQL
- **[Development Guide](../DEVELOPMENT.md)** - General development setup

---

## Historical Documents

This guide consolidates and supersedes:
- [docs/DATABASE_SETUP.md](../archive/database-setup-oct-2025.md) - Original setup guide

For historical reference, see the [Archive](../archive/).

---

*For questions or improvements, see the [Documentation Index](../DOCUMENTATION_INDEX.md).*

