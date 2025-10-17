# ArxOS Test Suite

**Last Updated:** October 17, 2025  
**Test Coverage:** ~18% (Target: 30-40%)  
**Status:** Infrastructure Complete, Ready for Comprehensive Testing

---

## Overview

The ArxOS test suite provides comprehensive testing for the "Git for Buildings" platform, covering unit tests, integration tests, and end-to-end workflows.

**Testing Philosophy:**
- Write tests that validate real user scenarios
- Use Go's native testing framework
- Maintain test isolation with transactions
- Follow engineering best practices

---

## Quick Start

### 1. Start Test Database

```bash
# Start test database with Docker
make test-db-start

# Run migrations
make migrate-test

# Verify database is ready
docker-compose -f docker-compose.test.yml ps
```

### 2. Run Tests

```bash
# Run all integration tests
make test-integration

# Run with coverage
make test-integration-coverage

# Run only unit tests (no database needed)
make test-short

# Run specific category
go test ./test/integration/api/... -v
go test ./test/integration/workflow/... -v
go test ./test/integration/repository/... -v
```

### 3. View Results

```bash
# Open coverage report
open coverage-integration.html

# Check test output
cat test/results/integration_test_results.json
```

---

## Directory Structure

```
test/
├── README.md                          # This file
├── REORGANIZATION_PLAN.md             # Cleanup documentation
├── CLEANUP_SUMMARY_OCT_17_2025.md     # Recent cleanup summary
│
├── fixtures/                          # Test data files
│   └── sample_buildings.json
│
├── helpers/                           # Shared test utilities
│   ├── assertions.go
│   ├── config_builder.go
│   ├── test_data_builder.go
│   ├── test_server.go
│   └── test_utils.go
│
├── unit/                              # Unit tests (fast, no dependencies)
│   └── domain_agnostic_test.go
│
├── integration/                       # Integration tests (require database)
│   ├── README.md                      # Integration test guide
│   ├── config.go                      # Database config
│   ├── container.go                   # Test container setup
│   ├── test_helpers.go                # Helper utilities
│   │
│   ├── api/                           # HTTP API tests
│   │   ├── README.md
│   │   ├── auth_api_test.go           # Authentication
│   │   ├── building_api_test.go       # Building endpoints
│   │   ├── equipment_api_test.go      # Equipment endpoints
│   │   ├── floor_room_test.go         # Floor/room endpoints
│   │   ├── ifc_import_test.go         # IFC import endpoints
│   │   ├── enhanced_api_test.go       # Enhanced features
│   │   ├── http_api_test.go           # Core HTTP tests
│   │   └── test_helpers.go            # HTTP server setup
│   │
│   ├── repository/                    # Repository/database tests
│   │   ├── README.md
│   │   ├── building_test.go           # Building repository
│   │   └── crud_test.go               # CRUD operations
│   │
│   ├── workflow/                      # End-to-end workflows
│   │   ├── README.md
│   │   ├── complete_workflows_test.go # Complete scenarios
│   │   ├── e2e_workflow_test.go       # E2E validation
│   │   ├── ifc_import_test.go         # IFC import workflow
│   │   ├── path_query_test.go         # Path query testing
│   │   ├── path_query_integration_test.go
│   │   └── version_control_test.go    # Git-like workflow
│   │
│   ├── cli/                           # CLI command tests
│   │   └── cli_integration_test.go
│   │
│   ├── cross_platform/                # Cross-platform tests
│   │   ├── cli_integration_test.go
│   │   └── cli_to_web_test.go
│   │
│   ├── services/                      # Service layer tests
│   │   ├── building_service_test.go
│   │   └── version_control_service_test.go
│   │
│   └── performance/                   # Performance tests
│       └── load_test.go
│
├── load/                              # Standalone load tests
│   └── load_test.go
│
├── chaos/                             # Chaos engineering tests
│   └── chaos_test.go
│
└── config/                            # Test configuration
    ├── test_config.yaml
    └── test_environment.sh
```

---

## Test Categories

### Unit Tests (`test/unit/`)
**Purpose:** Fast, isolated tests with no external dependencies  
**Requires:** Nothing (pure Go)  
**Run:** `go test ./test/unit/... -v`

**What to test:**
- Domain logic
- Business rules
- Algorithms
- Validation functions

### Integration Tests (`test/integration/`)
**Purpose:** Test component interactions with real dependencies  
**Requires:** Test database, migrations  
**Run:** `make test-integration`

**Subcategories:**

#### API Tests (`integration/api/`)
- HTTP endpoint testing
- Authentication flows
- Request/response validation
- Error handling

#### Repository Tests (`integration/repository/`)
- Database CRUD operations
- PostGIS spatial queries
- Transaction handling
- Data persistence

#### Workflow Tests (`integration/workflow/`)
- End-to-end user scenarios
- Multi-step processes (IFC import → query → export)
- Feature integrations (BAS + IFC)
- Complete lifecycle testing

#### CLI Tests (`integration/cli/`)
- Command execution
- Output validation
- Error handling

---

## Running Tests

### All Tests

```bash
# All tests (unit + integration)
go test ./... -v

# Only unit tests (fast)
make test-short

# Only integration tests (requires database)
make test-integration
```

### By Category

```bash
# API tests
go test ./test/integration/api/... -v

# Repository tests
go test ./test/integration/repository/... -v

# Workflow tests
go test ./test/integration/workflow/... -v

# CLI tests
go test ./test/integration/cli/... -v

# Performance tests
go test ./test/integration/performance/... -v
```

### With Options

```bash
# With coverage
make test-integration-coverage

# Specific test function
go test ./test/integration/workflow -run TestIFCImport -v

# With race detection
go test ./test/integration/... -race -v

# With timeout
go test ./test/integration/... -timeout 30m -v
```

---

## Test Infrastructure

### Test Database

**Docker Compose Setup:**
```bash
# Start
make test-db-start

# Check status
docker-compose -f docker-compose.test.yml ps

# Stop
make test-db-stop

# Clean (removes volumes)
make test-db-clean
```

**Manual Setup:**
```bash
# Create test database
createdb arxos_test
psql arxos_test -c "CREATE EXTENSION postgis;"

# Run migrations
export TEST_DB_PORT=5432
make migrate-test
```

### Environment Variables

```bash
# Required for integration tests
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5433          # Use 5433 for Docker test DB
export TEST_DB_USER=postgres
export TEST_DB_PASSWORD=postgres
export TEST_DB_NAME=arxos_test
export TEST_DB_SSLMODE=disable

# Optional for IFC import tests
export IFC_SERVICE_URL=http://localhost:5001
```

### Test Container

Integration tests use a test container that provides:
- Database connection
- Repository access
- Use case access
- Helper methods for test data creation
- Automatic cleanup

```go
func TestExample(t *testing.T) {
    // Setup
    container := setupTestContainer(t)
    if container == nil {
        t.Skip("Test database not available")
    }
    
    // Create test data
    building := container.CreateTestBuilding(t, "Test Building")
    
    // Run test with real database
    // Automatic cleanup on test completion
}
```

---

## Test Data

### Fixtures (`test/fixtures/`)

Place test data files here:
- Sample IFC files
- BAS CSV exports
- Building JSON files
- Equipment data

**Example:**
```
test/fixtures/
├── sample_buildings.json
└── (add your test files)
```

### Test Data in `test_data/`

Sample files for integration tests:
```
test_data/
├── inputs/                    # Sample IFC files
│   ├── AC20-FZK-Haus.ifc
│   ├── Duplex_A_20110907.ifc
│   └── sample.ifc
└── bas/                       # Sample BAS files
    └── sample_bas_export.csv
```

---

## Best Practices

### 1. Test Independence ✅
Each test should be completely independent:
```go
func TestExample(t *testing.T) {
    // Create own test data
    building := container.CreateTestBuilding(t, "Test Building")
    
    // Don't rely on other tests' data
    // Don't assume test execution order
}
```

### 2. Use t.Helper() ✅
Mark helper functions:
```go
func createTestBuilding(t *testing.T) *domain.Building {
    t.Helper()  // Makes error messages point to caller
    // ...
}
```

### 3. Cleanup with t.Cleanup() ✅
Register cleanup automatically:
```go
func TestExample(t *testing.T) {
    db := SetupTestDB(t)
    // Cleanup registered automatically via t.Cleanup()
    // No need for defer or manual cleanup
}
```

### 4. Skip Gracefully ✅
Don't fail tests due to missing infrastructure:
```go
func TestExample(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test in short mode")
    }
    
    container := setupTestContainer(t)
    if container == nil {
        t.Skip("Test database not available")
    }
}
```

### 5. Clear Test Names ✅
Use descriptive names:
```go
// Good
func TestEquipmentRepository_GetByPath_ExactMatch(t *testing.T)

// Bad
func TestGet(t *testing.T)
```

### 6. Table-Driven Tests ✅
Test multiple scenarios:
```go
tests := []struct{
    name     string
    input    string
    expected int
}{
    {"Case 1", "input1", 1},
    {"Case 2", "input2", 2},
}

for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        // Test tt.input, tt.expected
    })
}
```

---

## Coverage Goals

**Current:** ~18%  
**Target:** 30-40%

### Priority Areas:

1. **High Priority:**
   - IFC import workflows
   - Path query operations
   - Repository CRUD
   - Authentication flows

2. **Medium Priority:**
   - HTTP API endpoints
   - Version control workflows
   - Service integrations

3. **Low Priority:**
   - Edge cases
   - Performance tests
   - Chaos tests

**Command:**
```bash
# Generate coverage report
make test-integration-coverage

# View by package
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out
```

---

## Troubleshooting

### Tests Skip: "Test database not available"

**Problem:** Can't connect to database

**Solution:**
```bash
# Start test database
make test-db-start

# Verify connection
psql -h localhost -p 5433 -U postgres -d arxos_test

# Check environment variables
echo $TEST_DB_PORT  # Should be 5433 for Docker
```

### Tests Skip: "Database migrations not run"

**Problem:** Schema not initialized

**Solution:**
```bash
export TEST_DB_PORT=5433
make migrate-test
```

### Tests Fail: Connection refused

**Problem:** Wrong port or database not running

**Solution:**
```bash
# Check what's running
docker-compose -f docker-compose.test.yml ps

# Check port
netstat -an | grep 5433

# Restart services
make test-db-stop
make test-db-start
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis:15-3.3-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: arxos_test
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Run migrations
        run: make migrate-test
        env:
          TEST_DB_PORT: 5432
      
      - name: Run tests
        run: make test-integration
        env:
          TEST_DB_PORT: 5432
```

---

## Recent Cleanup (October 17, 2025)

### Reorganization Completed ✅

- ✅ Moved 11 files to proper locations
- ✅ Deleted 2 obsolete shell scripts
- ✅ Removed 2 redundant directories
- ✅ Fixed 5 linting errors
- ✅ Created 3 category READMEs
- ✅ Consolidated test structure

**See:** `test/CLEANUP_SUMMARY_OCT_17_2025.md` for details

---

## Contributing

### Adding New Tests

1. **Choose correct location:**
   - API test → `integration/api/`
   - Repository test → `integration/repository/`
   - Workflow test → `integration/workflow/`
   - Unit test → `unit/`

2. **Follow naming:**
   - `*_test.go` suffix
   - Descriptive names
   - Clear purpose

3. **Use helpers:**
   - `setupTestContainer(t)` for integration tests
   - `LoadTestIFCFile(t, filename)` for test data
   - `CreateTestContext(t)` for timeouts

4. **Add documentation:**
   - Update relevant README
   - Add comments explaining test purpose
   - Document prerequisites

---

## Resources

- [Integration Test Guide](integration/README.md) - Detailed integration testing guide
- [Go Testing Package](https://pkg.go.dev/testing) - Official Go testing docs
- [Testify](https://github.com/stretchr/testify) - Assertion library we use

---

**Test Suite Status:** Clean, Organized, Production-Ready ✅  
**Ready for:** Comprehensive testing and deployment!
