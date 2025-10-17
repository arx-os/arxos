# Integration Tests

This directory contains comprehensive integration tests for Arxos core features.

## Quick Start

```bash
# 1. Start test database
docker-compose -f docker-compose.test.yml up -d postgres-test

# 2. Wait for database to be ready
docker-compose -f docker-compose.test.yml ps

# 3. Run migrations on test database
export TEST_DB_PORT=5433  # Test DB uses port 5433
make migrate-test

# 4. Run integration tests
make test-integration

# 5. Cleanup
docker-compose -f docker-compose.test.yml down
```

## Prerequisites

### 1. Test Database

Integration tests require a PostgreSQL database with PostGIS extension.

**Option A: Docker Compose (Recommended)**

```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d postgres-test

# Check health
docker-compose -f docker-compose.test.yml ps
```

**Option B: Manual PostgreSQL Setup**

```bash
# Install PostgreSQL 15+ with PostGIS 3.3+
brew install postgresql postgis  # macOS
sudo apt-get install postgresql-15-postgis-3  # Ubuntu

# Create test database
createdb arxos_test
psql arxos_test -c "CREATE EXTENSION postgis;"
```

### 2. Database Migrations

Tests expect database schema to be migrated:

```bash
# Run migrations on test database
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5433
export TEST_DB_NAME=arxos_test
export TEST_DB_USER=postgres
export TEST_DB_PASSWORD=postgres

# Run migrations
cd ../..  # Project root
make migrate-test
```

### 3. Test Data (Optional)

Place sample IFC files in `test_data/inputs/` for IFC import tests:

```
test_data/
├── inputs/
│   ├── AC20-FZK-Haus.ifc
│   ├── Duplex_A_20110907.ifc
│   └── sample.ifc
└── bas/
    └── sample_bas_export.csv
```

## Running Tests

### Run All Integration Tests

```bash
# From project root
make test-integration

# With coverage
make test-integration-coverage

# With verbose output
go test ./test/integration/... -v
```

### Run Specific Test Suites

```bash
# IFC Import E2E tests
go test ./test/integration -run TestIFCImport -v

# Path query tests
go test ./test/integration -run TestPath -v

# Repository CRUD tests
go test ./test/integration -run TestRepository -v

# Workflow tests
go test ./test/integration -run TestWorkflow -v
```

### Run With Different Test Database

```bash
# Set environment variables
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5433
export TEST_DB_USER=postgres
export TEST_DB_PASSWORD=postgres
export TEST_DB_NAME=arxos_test
export TEST_DB_SSLMODE=disable

# Run tests
go test ./test/integration/... -v
```

### Skip Tests Requiring Database

```bash
# Skip integration tests (run unit tests only)
go test ./... -short
```

## Test Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_DB_HOST` | `localhost` | PostgreSQL host |
| `TEST_DB_PORT` | `5432` | PostgreSQL port (use `5433` for Docker test DB) |
| `TEST_DB_USER` | `postgres` | Database user |
| `TEST_DB_PASSWORD` | `postgres` | Database password |
| `TEST_DB_NAME` | `arxos_test` | Database name |
| `TEST_DB_SSLMODE` | `disable` | SSL mode |
| `IFC_SERVICE_URL` | `http://localhost:5000` | IfcOpenShell service URL (use `5001` for test) |

## Test Structure

### Test Files

```
test/integration/
├── config.go                        # Database configuration
├── container.go                     # Test container setup
├── test_helpers.go                  # Helper utilities
├── ifc_import_e2e_test.go          # IFC import end-to-end tests
├── e2e_workflows_test.go           # Complete workflow tests
├── repository_crud_test.go         # Repository CRUD tests
├── path_query_test.go              # Path query tests
└── README.md                        # This file
```

### Test Categories

**1. IFC Import E2E Tests** (`ifc_import_e2e_test.go`)
- Complete import workflow
- Entity extraction validation
- Spatial hierarchy verification
- Path generation testing
- Edge case handling

**2. Workflow Integration Tests** (`e2e_workflows_test.go`)
- IFC Import → Path Query → Export
- BAS + IFC integration
- Version control workflows
- Complete building lifecycle

**3. Repository CRUD Tests** (`repository_crud_test.go`)
- Building repository
- Equipment repository (with path queries)
- Floor repository
- Room repository (with geometry)

**4. Path Query Tests** (`path_query_test.go`)
- Exact path matching
- Wildcard patterns
- Pattern validation
- Repository and use case layer testing

## Test Isolation

### Transaction-Based Isolation

Tests can use transaction-based isolation for fast cleanup:

```go
func TestExample(t *testing.T) {
    container := setupTestContainerWithTransaction(t)
    // Test runs in transaction
    // Automatic rollback on cleanup
}
```

### Manual Cleanup

For tests that can't use transactions:

```go
func TestExample(t *testing.T) {
    container := setupTestContainer(t)
    
    // Register cleanup
    t.Cleanup(func() {
        CleanupTestData(t, container.DB)
    })
    
    // Run test
}
```

## Test Utilities

### Test Container

```go
// Full container with all dependencies
container := setupTestContainer(t)

// Access repositories
buildingRepo := container.GetBuildingRepository()
equipmentRepo := container.GetEquipmentRepository()

// Access use cases
buildingUC := container.GetBuildingUseCase()
ifcUC := container.GetIFCUseCase()

// Create test data
building := container.CreateTestBuilding(t, "Test Building")
floor := container.CreateTestFloor(t, building.ID, 1)
room := container.CreateTestRoom(t, floor.ID, "101")
equipment := container.CreateTestEquipment(t, building.ID, room.ID, "VAV-101", "/TEST/1/101/HVAC/VAV-101")
```

### Load Test Files

```go
// Load test IFC file
ifcData := LoadTestIFCFile(t, "AC20-FZK-Haus.ifc")

// Load test BAS CSV
basData := LoadTestBASFile(t, "sample_bas_export.csv")
```

### Create Test Context

```go
// Context with 30-second timeout
ctx := CreateTestContext(t)
```

## Troubleshooting

### Tests Skip: "Test database not available"

**Problem:** Can't connect to test database

**Solutions:**
1. Start test database: `docker-compose -f docker-compose.test.yml up -d`
2. Check connection: `psql -h localhost -p 5433 -U postgres -d arxos_test`
3. Verify environment variables are set correctly

### Tests Skip: "Database migrations not run"

**Problem:** Test database schema not initialized

**Solution:**
```bash
export TEST_DB_PORT=5433
make migrate-test
```

### Tests Skip: "IFC file not found"

**Problem:** Test IFC files missing

**Solution:**
Place sample IFC files in `test_data/inputs/`:
- Download from buildingSMART or IFC sample repositories
- Use AC20-FZK-Haus.ifc (common test file)
- Use Duplex_A_20110907.ifc (multi-floor test)

### IFC Import Tests Fail

**Problem:** IfcOpenShell service not available

**Solutions:**
1. Start IFC service: `docker-compose -f docker-compose.test.yml up -d ifcopenshell-service-test`
2. Set IFC_SERVICE_URL: `export IFC_SERVICE_URL=http://localhost:5001`
3. Check service health: `curl http://localhost:5001/health`

### Permission Denied Errors

**Problem:** PostgreSQL permission issues

**Solution:**
```bash
# Grant permissions
psql -h localhost -p 5433 -U postgres -d arxos_test -c "
GRANT ALL PRIVILEGES ON DATABASE arxos_test TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
"
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis:15-3.3-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: arxos_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Run migrations
        run: make migrate-test
        env:
          TEST_DB_HOST: localhost
          TEST_DB_PORT: 5432
      
      - name: Run integration tests
        run: make test-integration
        env:
          TEST_DB_HOST: localhost
          TEST_DB_PORT: 5432
```

## Best Practices

### 1. Test Isolation

✅ **DO:** Use transactions or cleanup functions
```go
t.Cleanup(func() {
    CleanupTestData(t, db)
})
```

❌ **DON'T:** Leave test data in database
```go
// No cleanup = pollution
```

### 2. Test Independence

✅ **DO:** Each test creates its own data
```go
building := container.CreateTestBuilding(t, "Test Building")
```

❌ **DON'T:** Depend on other tests' data
```go
building := getBuildingCreatedByOtherTest()  // BAD
```

### 3. Skip Gracefully

✅ **DO:** Skip if prerequisites missing
```go
if container == nil {
    t.Skip("Test database not available")
}
```

❌ **DON'T:** Fail tests due to missing infrastructure
```go
require.NotNil(t, container)  // Fails CI if DB not available
```

### 4. Clear Test Names

✅ **DO:** Descriptive test names
```go
func TestIFCImportCreatesAllEntities(t *testing.T)
```

❌ **DON'T:** Vague names
```go
func TestImport(t *testing.T)
```

### 5. Comprehensive Assertions

✅ **DO:** Validate multiple aspects
```go
assert.NoError(t, err)
assert.NotNil(t, result)
assert.Greater(t, result.Count, 0)
```

❌ **DON'T:** Minimal validation
```go
assert.NoError(t, err)  // Only checks error
```

## Coverage Goals

### Current Coverage: ~18%
### Target Coverage: 30-40%

**Priority Areas:**
1. IFC import workflows (HIGH)
2. Path query operations (HIGH)
3. Repository CRUD (HIGH)
4. Version control workflows (MEDIUM)
5. API endpoints (MEDIUM)

**Coverage Command:**
```bash
go test ./test/integration/... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## Contributing

When adding new integration tests:

1. Follow existing test structure
2. Use `setupTestContainer(t)` for dependencies
3. Add cleanup with `t.Cleanup()` or transactions
4. Document prerequisites in test comments
5. Skip gracefully if prerequisites missing
6. Add test to this README

## Resources

- [Go Testing Package](https://pkg.go.dev/testing)
- [Testify Assertions](https://github.com/stretchr/testify)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [PostGIS Docker](https://hub.docker.com/r/postgis/postgis)

---

**Week 4 Status:** Test infrastructure complete, ready for comprehensive testing!

