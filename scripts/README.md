# ArxOS Scripts Directory

**Purpose:** DevOps automation, database setup, demos, and utility scripts

---

## 📁 Active Scripts (22 files)

### 🗄️ Database Setup & Management (5 scripts)

**Essential for development:**
- ✅ **`setup-dev-database.sh`** - Create development database with PostGIS
- ✅ **`setup-database.sh`** - General database setup script
- ✅ **`setup-database-terminal.sh`** - Terminal-only database setup
- ✅ **`migrate-test-database.sh`** - Run migrations on test database
- ✅ **`setup_test_data.sh`** - Seed test data for development

**Usage:**
```bash
# First-time setup
./scripts/setup-dev-database.sh

# Test database
./scripts/migrate-test-database.sh
```

---

### 📊 SQL Utilities (2 files)

**Critical database configuration:**
- ✅ **`init-postgis.sql`** (249 lines) - PostGIS initialization
  - Enables extensions (postgis, postgis_topology, uuid-ossp)
  - Creates custom SRID 900913 (millimeter precision)
  - Defines ENUM types (equipment_status, building_status)
  - Used by Docker Compose on container startup

- ✅ **`optimize-postgis.sql`** (340 lines) - Performance optimization
  - Creates spatial indices
  - Clustering optimization
  - Vacuum and analyze
  - Query optimization

**Usage:**
```bash
# Initialize PostGIS (Docker does this automatically)
psql -d arxos < scripts/init-postgis.sql

# Optimize performance
psql -d arxos < scripts/optimize-postgis.sql
```

---

### 🛠️ Development Utilities (6 scripts)

**Active development tools:**
- ✅ **`lint-interface.sh`** (196 lines) - ⚡ **CRITICAL - Used by CI/CD!**
  - Detects `interface{}` → Should be `any`
  - Used by: Makefile (`make check-interface`), GitHub Actions
  - Enforces Go 1.18+ best practices

- ✅ **`audit_cli_commands.sh`** (220 lines) - CLI command audit
  - Tests all CLI commands
  - Categorizes: working, placeholder, failing
  - Generates audit report

- ✅ **`backup.sh`** (231 lines) - Database backup utility
  - PostgreSQL backup with PostGIS data
  - For production deployments

- ✅ **`restore.sh`** (334 lines) - Database restore utility
  - Restore from backup
  - Includes validation

- ✅ **`create_building_structure.sh`** - Create building directory structure
  - Follows universal addressing convention

- ✅ **`validate_structure.sh`** - Validate building structure
  - Check directory organization

**Usage:**
```bash
# Lint check (used by CI/CD)
./scripts/lint-interface.sh

# Audit CLI commands
./scripts/audit_cli_commands.sh

# Backup database
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh
```

---

### 🎬 Demo Scripts (4 scripts)

**Feature showcases:**
- 📚 **`demo.sh`** - Basic ArxOS demo
- 📚 **`demo_manual.sh`** - Manual entry demo
- 📚 **`demo_phase3.sh`** (207 lines) - Phase 3 hierarchical management
- 📚 **`demo_complete.sh`** (260 lines) - Complete system demo
  - User management
  - Building CRUD
  - Equipment management
  - Spatial queries
  - Authentication

**Usage:**
```bash
# Run complete demo
./scripts/demo_complete.sh

# Quick demo
./scripts/demo.sh
```

---

### 🔧 Migration Utilities (3 scripts)

**One-time migration tools:**
- 🔧 **`migrate_configs.sh`** (29 lines) - Migrate old configs → new Go config
- 🔧 **`migrate_v1_to_v2.sh`** - Migrate BIM v1.0 → v2.0
- 🔧 **`seed_test_data.go`** (174 lines) - Seed database with test data

**Usage:**
```bash
# Config migration (if upgrading from old version)
./scripts/migrate_configs.sh

# Seed test data
go run scripts/seed_test_data.go
```

---

### 🚀 Build/Deploy Utilities (2 scripts)

**Build automation:**
- ⏸️ **`generate_docker.sh`** (26 lines) - Generate Docker Compose from Go config
- ⏸️ **`mobile_api_complete.sh`** - Mobile API demo

**Usage:**
```bash
# Generate Docker config (if needed)
./scripts/generate_docker.sh
```

---

## 🗂️ Archived Scripts

**Location:** `scripts/archive/legacy-tests/`

**17 legacy test scripts** moved to archive:
- All `test-*.sh` scripts (old integration tests)
- `run_tests.sh`, `run_tests.ps1` (outdated test runners)
- `run_integration_tests.sh`, `QUICK_TEST.sh`
- `test/` subdirectory

**Why archived:** Replaced by proper Go integration tests in `test/integration/`

See `scripts/archive/legacy-tests/README.md` for details.

---

## 🎯 Quick Reference

### First-Time Setup
```bash
# 1. Setup database
./scripts/setup-dev-database.sh

# 2. Verify setup
go run cmd/arx/main.go health
```

### Daily Development
```bash
# Run linter (before committing)
./scripts/lint-interface.sh

# Run tests
make test

# Audit CLI
./scripts/audit_cli_commands.sh
```

### Production Deployment
```bash
# Backup database
./scripts/backup.sh

# Optimize performance
psql -d arxos < scripts/optimize-postgis.sql
```

### Demonstrations
```bash
# Show all features
./scripts/demo_complete.sh

# Quick demo
./scripts/demo.sh
```

---

## 🔍 Script Status

| Category | Scripts | Status |
|----------|---------|--------|
| Database Setup | 5 | ✅ Active, essential |
| SQL Files | 2 | ✅ Active, critical |
| Dev Utilities | 6 | ✅ Active, useful |
| Demos | 4 | 📚 Examples, keep |
| Migrations | 3 | 🔧 One-time, keep for reference |
| Build/Deploy | 2 | ⏸️ Rarely used |
| **Archived** | **17** | 🗂️ **Legacy tests** |

---

## 🚨 Critical Scripts (Don't Delete!)

These are actively used by CI/CD or core workflows:

1. **`lint-interface.sh`** ← Used by GitHub Actions + Makefile
2. **`setup-dev-database.sh`** ← First-time development setup
3. **`init-postgis.sql`** ← Docker container initialization
4. **`backup.sh` / `restore.sh`** ← Production database management

---

## 📚 Related Documentation

- **Makefile** - See `make help` for test/build targets
- **test/integration/** - Modern Go integration tests
- **.github/workflows/ci.yml** - CI/CD pipeline using lint-interface.sh
- **QUICKSTART.md** - Quick start guide with setup instructions

---

**Last Updated:** October 19, 2025
**Maintained By:** ArxOS Development Team

