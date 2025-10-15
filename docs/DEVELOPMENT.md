# Arxos Development Guide

**Last Updated:** October 15, 2025  
**Status:** Comprehensive guide for developers and contributors

---

## Table of Contents

- [Getting Started](#getting-started)
- [Project Overview](#overview)
- [Architecture](#architecture)
- [Code Organization](#code-organization)
- [Development Workflow](#workflow)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Getting Started {#getting-started}

### Prerequisites

- **Go:** 1.21 or higher
- **PostgreSQL:** 14+ with PostGIS extension
- **Git:** For version control
- **Make:** For build automation (optional)

### Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# 2. Install dependencies
go mod download

# 3. Setup database
./scripts/setup-dev-database.sh

# 4. Run migrations
go run cmd/arx/main.go migrate up

# 5. Build
make build

# 6. Verify
./arx health
```

**See [Database Setup Guide](guides/database-setup.md) for detailed PostgreSQL installation.**

---

## Project Overview {#overview}

### Code Metrics

```
Total Go Code:        ~98,000 lines
├── Domain Layer:      8,150 lines (entities, interfaces, business rules)
├── Use Case Layer:   13,368 lines (business logic orchestration)
├── Infrastructure:   22,834 lines (PostGIS, cache, IFC, BAS)
└── Interfaces:       12,432 lines (HTTP, CLI, TUI)

Database Migrations:  33 files (107+ tables, comprehensive schema)
Documentation:        113 markdown files
Test Files:           53 files
Mobile (TypeScript):  60+ files (React Native app)
Python Services:      ifcopenshell-service (external microservice)
```

### What Arxos Does

**Arxos is version-controlled storage for building data.**

Think of it as "Git for Buildings":
- Store building entities (buildings, floors, rooms, equipment)
- Universal addressing (`/B1/3/301/HVAC/VAV-301`)
- Version control (branches, commits, pull requests)
- Query interface (by path, type, location, system)
- Import/export (IFC, CSV, JSON)

**Three Interfaces:**
1. **CLI + ASCII** - Terminal-based, scriptable
2. **IFC Integration** - Bridge to CAD/BIM tools
3. **React Native + AR** - Mobile field app

---

## Architecture {#architecture}

### Clean Architecture Pattern

Arxos follows Clean Architecture with strict dependency rules:

```
Domain (innermost - no dependencies)
   ↓
Use Cases (depends on Domain interfaces only)
   ↓
Infrastructure (implements Domain interfaces)
   ↓
Interfaces (HTTP/CLI/TUI - depends on Use Cases)
```

**Key Principle:** Dependencies point inward. Domain has zero infrastructure imports.

### Layer Details

**1. Domain Layer (`internal/domain/`)**
- Pure business logic
- Entity definitions
- Repository interfaces (abstract)
- Business rules
- Zero infrastructure dependencies ✅

**2. Use Case Layer (`internal/usecase/`)**
- Business logic orchestration
- Coordinates between repositories
- Implements workflows
- Depends only on domain interfaces

**3. Infrastructure Layer (`internal/infrastructure/`)**
- Concrete implementations
- PostGIS repositories
- BAS CSV parser
- IFC integration
- Cache, logger, monitoring

**4. Interface Layer (`internal/interfaces/`)**
- HTTP API handlers
- CLI commands
- TUI components
- GraphQL (planned)
- WebSocket (planned)

### Dependency Injection

**Container Pattern:**
```go
type Container struct {
    // Infrastructure
    db *sqlx.DB
    cache Cache
    logger Logger

    // Repositories (interfaces)
    buildingRepo BuildingRepository
    equipmentRepo EquipmentRepository
    // ... 15+ repositories

    // Use Cases
    buildingUC *BuildingUseCase
    equipmentUC *EquipmentUseCase
    // ... 15+ use cases
}
```

**Benefits:**
- Single source of truth for dependencies
- Proper lifecycle management
- No global variables
- Testable (inject mocks)

---

## Code Organization {#code-organization}

### Project Structure

```
arxos/
├── cmd/
│   └── arx/                 # CLI application entry point
├── internal/
│   ├── domain/              # Domain models and business logic
│   ├── usecase/             # Use case orchestration
│   ├── infrastructure/      # Infrastructure implementations
│   │   ├── postgis/         # PostgreSQL/PostGIS repositories
│   │   ├── cache/           # 3-tier caching
│   │   ├── bas/             # BAS CSV parser
│   │   └── ifc/             # IFC integration
│   ├── interfaces/          # Interface layer
│   │   ├── http/            # REST API
│   │   ├── cli/             # CLI commands
│   │   └── tui/             # Terminal UI
│   ├── config/              # Configuration management
│   └── migrations/          # Database migrations (SQL)
├── pkg/
│   ├── auth/                # Authentication utilities
│   ├── models/              # Shared models
│   ├── naming/              # Path generation
│   ├── errors/              # Error handling
│   └── validation/          # Validation utilities
├── mobile/                  # React Native mobile app
├── services/                # External microservices
│   └── ifcopenshell-service/ # IFC processing
├── docs/                    # Documentation
├── test/                    # Integration tests
└── scripts/                 # Build and deployment scripts
```

### Domain Model

**Core Spatial Entities:**
```
Organization
  └─ Building
      ├─ Floor (level, elevation, area)
      │   ├─ Zone (HVAC zones, occupancy zones)
      │   └─ Room (number, name, type, geometry)
      │       └─ Equipment (path, type, location, relationships)
      └─ Equipment (building/floor-level)
```

**Every entity has:**
- Unique ID (UUID)
- Spatial coordinates (PostGIS Point/Polygon)
- Metadata JSON (extensible properties)
- Audit timestamps (created_at, updated_at)
- Universal path (e.g., `/B1/3/301/HVAC/VAV-301`)

**Git-Like Version Control:**
```
Repository
  ├─ Branch (main, feature, contractor, vendor, issue, scan)
  │   ├─ Commit (hash, message, changes summary)
  │   └─ WorkingDirectory (user's current state)
  ├─ PullRequest (work orders, contractor projects)
  │   ├─ PRReview, PRComment, PRFile
  └─ Issue (problems, maintenance, safety)
      ├─ IssueComment, IssuePhoto, IssueActivity
```

---

## Development Workflow {#workflow}

### Building the Project

```bash
# Build CLI binary
go build -o arx ./cmd/arx

# Build with Make
make build

# Build for specific platform
GOOS=linux GOARCH=amd64 go build -o arx-linux ./cmd/arx
```

### Running Locally

```bash
# Run without building
go run cmd/arx/main.go <command>

# Examples
go run cmd/arx/main.go health
go run cmd/arx/main.go building list
go run cmd/arx/main.go migrate status
```

### Database Migrations

```bash
# Check migration status
go run cmd/arx/main.go migrate status

# Run pending migrations
go run cmd/arx/main.go migrate up

# Rollback last migration
go run cmd/arx/main.go migrate down

# Create new migration
go run cmd/arx/main.go migrate create my_feature_name
```

**See [Migration Guide](guides/migrations.md) for detailed instructions.**

### Starting the API Server

```bash
# Start HTTP server
go run cmd/arx/main.go serve

# Or with custom port
go run cmd/arx/main.go serve --port 8080

# Test the API
curl http://localhost:8080/health
```

### Hot Reload (Development)

```bash
# Install air for hot reload
go install github.com/cosmtrek/air@latest

# Run with hot reload
air
```

---

## Testing {#testing}

### Running Tests

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run specific package
go test ./internal/domain/...

# Run specific test
go test ./internal/usecase/ -run TestBuildingUseCase

# Verbose output
go test -v ./...
```

### Integration Tests

```bash
# Run integration tests (requires database)
go test ./test/integration/...

# Run with test database
POSTGIS_DATABASE=arxos_test go test ./test/integration/...
```

### Test Coverage

```bash
# Generate coverage report
go test -coverprofile=coverage.out ./...

# View coverage in browser
go tool cover -html=coverage.out

# Coverage by package
go test -cover ./internal/domain/
go test -cover ./internal/usecase/
go test -cover ./internal/infrastructure/
```

**Current Coverage:** ~15% (target: 60%+)

### Writing Tests

**Unit Test Example:**
```go
func TestEquipmentPath(t *testing.T) {
    path := naming.GenerateEquipmentPath(
        "Main Building",
        3,
        "Room 301",
        "hvac",
        "VAV Box",
        "301",
    )
    
    assert.Equal(t, "/MAIN/3/301/HVAC/VAV-301", path)
}
```

**Integration Test Example:**
```go
func TestBuildingCreate(t *testing.T) {
    // Setup test database
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)
    
    // Create use case
    uc := usecase.NewBuildingUseCase(db, logger)
    
    // Test
    building, err := uc.Create(ctx, &domain.Building{
        Name: "Test Building",
    })
    
    assert.NoError(t, err)
    assert.NotNil(t, building.ID)
}
```

### Quick MVP Test

```bash
# Automated integration test
./test_mvp_workflow.sh

# Manual test workflow
./arx building create --name "Test School" --address "123 Main St"
./arx floor create --building <id> --level 3 --name "Third Floor"
./arx room create --floor <id> --name "Room 301" --number "301" --x 0 --y 0 --width 30 --height 20
./arx equipment create --name "VAV-301" --type hvac --building <id> --floor <id> --room <id> --x 15 --y 10
./arx render <building-id> --floor 3
```

---

## Key Subsystems

### BAS Integration

**Features:**
- CSV import with smart column detection
- Support for Metasys, Desigo, Honeywell formats
- Auto-mapping to rooms via location parsing
- Change detection between imports
- 100% test coverage ✅

**Code Location:**
- Parser: `internal/infrastructure/bas/csv_parser.go`
- Tests: `internal/infrastructure/bas/csv_parser_test.go`
- Use Case: `internal/usecase/bas_import_usecase.go`
- Repository: `internal/infrastructure/postgis/bas_point_repo.go`

**Usage:**
```bash
arx bas import points.csv --building <id>
arx bas list --building <id>
arx bas unmapped
arx bas map AI-1-1 --room <room-id>
```

### IFC Integration

**Features:**
- IFC parsing via IfcOpenShell service
- Entity extraction (buildings, floors, rooms, equipment)
- 3D coordinate extraction
- Property set mapping
- IFC type → category mapping

**Code Location:**
- Use Case: `internal/usecase/ifc_usecase.go`
- Service: `internal/infrastructure/ifc/enhanced_service.go`
- Client: `internal/infrastructure/ifc/client.go`

**Status:**
- ✅ Go implementation complete
- ⏳ Python service needs enhancement

**Usage:**
```bash
arx import building.ifc
arx export <building-id> --format ifc
```

### Universal Naming Convention

**Path Format:** `/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT`

**Features:**
- Auto-generation from building/floor/room/equipment data
- Wildcard pattern matching
- SQL query translation
- 100% test coverage ✅

**Code Location:**
- Library: `pkg/naming/path.go`
- Tests: `pkg/naming/path_test.go`

**See [Naming Convention Guide](guides/naming-convention.md) for complete documentation.**

### Git-Like Version Control

**Features:**
- Branch create/merge/delete
- Commit with changesets
- Pull request workflow
- Issue tracking
- Merge conflict detection

**Code Location:**
- Domain: `internal/domain/repository_workflow.go`, `internal/domain/issue.go`
- Use Cases: `internal/usecase/branch_usecase.go`, `internal/usecase/pr_usecase.go`
- Repositories: `internal/infrastructure/postgis/*_repo.go`

**Usage:**
```bash
arx branch create feature/new-equipment
arx commit -m "Added VAV boxes to floor 3"
arx pr create --title "New HVAC Equipment"
arx pr approve <pr-id>
arx pr merge <pr-id>
```

---

## Database Development

### Schema Overview

**107+ tables organized into:**
- Core entities (buildings, floors, rooms, equipment)
- Users & organizations (multi-tenancy)
- BAS integration (systems, points, history)
- Version control (branches, commits, PRs)
- Workflow (issues, reviews, comments)
- Spatial & AR (anchors, point clouds)
- Equipment topology (relationships, network)

### Working with Migrations

```bash
# Create new migration
go run cmd/arx/main.go migrate create add_my_feature

# Edit generated files:
# - internal/migrations/XXX_add_my_feature.up.sql
# - internal/migrations/XXX_add_my_feature.down.sql

# Test migration
go run cmd/arx/main.go migrate up

# Rollback if needed
go run cmd/arx/main.go migrate down
```

**See [Migration Guide](guides/migrations.md) for best practices.**

### PostGIS Spatial Queries

**Example - Find nearby equipment:**
```sql
SELECT * FROM equipment
WHERE ST_DWithin(
    ST_SetSRID(ST_MakePoint(location_x, location_y), 4326),
    ST_SetSRID(ST_MakePoint($1, $2), 4326),
    10  -- 10 meters
);
```

**Example - Equipment within room:**
```sql
SELECT e.* FROM equipment e
JOIN rooms r ON ST_Contains(r.geometry, 
    ST_SetSRID(ST_MakePoint(e.location_x, e.location_y), 4326)
);
```

---

## API Development

### Adding New Endpoints

**1. Define handler in `internal/interfaces/http/handlers/`:**
```go
func (h *MyHandler) HandleCreate(w http.ResponseWriter, r *http.Request) {
    // Parse request
    var req CreateRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    // Call use case
    result, err := h.useCase.Create(r.Context(), &req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    // Return response
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(result)
}
```

**2. Register route in `internal/interfaces/http/router.go`:**
```go
r.Route("/api/v1/myresource", func(r chi.Router) {
    r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
    r.Use(httpmiddleware.RBACMiddleware("myresource:read"))
    
    r.Get("/", myHandler.HandleList)
    r.Post("/", myHandler.HandleCreate)
    r.Get("/{id}", myHandler.HandleGet)
})
```

**3. Test the endpoint:**
```bash
curl -X POST http://localhost:8080/api/v1/myresource \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
```

### Authentication & Authorization

**JWT Authentication:**
```go
// Login returns JWT token
token, err := authUseCase.Login(ctx, email, password)

// Use token in requests
req.Header.Set("Authorization", "Bearer " + token)
```

**RBAC Permissions:**
```go
// Define permissions in use case
requiredPermissions := []string{"equipment:write"}

// Middleware checks automatically
r.Use(httpmiddleware.RBACMiddleware(requiredPermissions...))
```

---

## CLI Development

### Adding New Commands

**1. Create command file in `internal/cli/commands/`:**
```go
package commands

import (
    "github.com/spf13/cobra"
)

var myCmd = &cobra.Command{
    Use:   "mycommand",
    Short: "Description of my command",
    RunE: func(cmd *cobra.Command, args []string) error {
        // Get container
        container := cmd.Context().Value("container").(*app.Container)
        
        // Get use case
        useCase := container.GetMyUseCase()
        
        // Execute
        result, err := useCase.DoSomething(cmd.Context())
        if err != nil {
            return err
        }
        
        // Display result
        fmt.Printf("Result: %v\n", result)
        return nil
    },
}

func init() {
    rootCmd.AddCommand(myCmd)
    myCmd.Flags().StringP("option", "o", "", "Description")
}
```

**2. Register in root command:**
Already done via `init()` function above.

**3. Test the command:**
```bash
go run cmd/arx/main.go mycommand --option value
```

### CLI Best Practices

- Use `cobra.Command` for structure
- Add flags with descriptions
- Return errors (don't panic)
- Use container for dependency injection
- Format output consistently
- Add help text

---

## Testing Guide

### Test Organization

```
test/
├── unit/               # Unit tests (mocked dependencies)
├── integration/        # Integration tests (real database)
├── load/              # Load/performance tests
├── chaos/             # Chaos engineering tests
├── helpers/           # Test utilities
└── fixtures/          # Test data
```

### Unit Tests

**With mocked repositories:**
```go
func TestEquipmentUseCase_Create(t *testing.T) {
    // Create mock repository
    mockRepo := &mocks.EquipmentRepository{}
    mockRepo.On("Create", mock.Anything, mock.Anything).Return(nil)
    
    // Create use case with mock
    uc := usecase.NewEquipmentUseCase(mockRepo, logger)
    
    // Test
    equipment, err := uc.Create(ctx, &domain.Equipment{
        Name: "Test Equipment",
    })
    
    assert.NoError(t, err)
    assert.NotNil(t, equipment.ID)
    mockRepo.AssertExpectations(t)
}
```

### Integration Tests

**With real database:**
```go
func TestBuildingRepository_Create(t *testing.T) {
    // Setup test database
    db := test.SetupTestDB(t)
    defer test.CleanupTestDB(t, db)
    
    // Create repository
    repo := postgis.NewBuildingRepository(db)
    
    // Test
    building := &domain.Building{
        ID:   types.NewID(),
        Name: "Test Building",
    }
    
    err := repo.Create(context.Background(), building)
    assert.NoError(t, err)
    
    // Verify
    retrieved, err := repo.GetByID(context.Background(), building.ID)
    assert.NoError(t, err)
    assert.Equal(t, "Test Building", retrieved.Name)
}
```

### Test Utilities

**Setup test database:**
```go
func SetupTestDB(t *testing.T) *sqlx.DB {
    db, err := sqlx.Connect("postgres", testDSN)
    require.NoError(t, err)
    
    // Run migrations
    runMigrations(t, db)
    
    return db
}

func CleanupTestDB(t *testing.T, db *sqlx.DB) {
    db.Exec("DROP SCHEMA public CASCADE")
    db.Exec("CREATE SCHEMA public")
    db.Close()
}
```

### Running Specific Tests

```bash
# Run BAS parser tests
go test ./internal/infrastructure/bas/...

# Run with verbose output
go test -v ./internal/usecase/...

# Run single test
go test -run TestEquipmentPath ./pkg/naming/...

# Run integration tests only
go test ./test/integration/... -tags=integration
```

---

## Code Style & Standards

### Go Conventions

- Follow [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- Use `gofmt` for formatting
- Use `golint` for linting
- Follow Clean Architecture principles
- Write godoc comments for public APIs

**Example:**
```go
// EquipmentRepository defines the interface for equipment persistence.
// Implementations must handle concurrent access safely.
type EquipmentRepository interface {
    // Create persists a new equipment entity.
    // Returns error if equipment with same ID already exists.
    Create(ctx context.Context, equipment *Equipment) error
    
    // GetByID retrieves equipment by its unique identifier.
    // Returns ErrNotFound if equipment doesn't exist.
    GetByID(ctx context.Context, id string) (*Equipment, error)
}
```

### Error Handling

```go
// Use custom error types
if err != nil {
    return nil, errors.Wrap(err, "failed to create equipment")
}

// Check for specific errors
if errors.Is(err, domain.ErrNotFound) {
    return http.StatusNotFound
}

// Domain errors
var ErrNotFound = errors.New("entity not found")
var ErrInvalidInput = errors.New("invalid input")
```

### Logging

```go
// Use structured logging
logger.Info("equipment created",
    "equipment_id", equipment.ID,
    "name", equipment.Name,
    "path", equipment.Path,
)

logger.Error("failed to create equipment",
    "error", err,
    "building_id", buildingID,
)
```

---

## Mobile Development

### Setup

```bash
cd mobile

# Install dependencies
npm install

# Start Metro bundler
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

### Project Structure

```
mobile/
├── src/
│   ├── screens/          # Screen components
│   ├── services/         # API services
│   ├── store/            # Redux state
│   ├── components/       # Reusable components
│   ├── ar/              # AR engine
│   └── types/           # TypeScript types
├── app.json             # Expo config
├── package.json         # Dependencies
└── tsconfig.json        # TypeScript config
```

**See [Mobile Development Guide](../mobile/DEVELOPMENT_GUIDE.md) for detailed instructions.**

---

## Common Development Tasks

### Adding a New Entity

**1. Define in domain:**
```go
// internal/domain/my_entity.go
type MyEntity struct {
    ID        string    `json:"id"`
    Name      string    `json:"name"`
    CreatedAt time.Time `json:"created_at"`
}
```

**2. Define repository interface:**
```go
type MyEntityRepository interface {
    Create(ctx context.Context, entity *MyEntity) error
    GetByID(ctx context.Context, id string) (*MyEntity, error)
}
```

**3. Implement repository:**
```go
// internal/infrastructure/postgis/my_entity_repo.go
type MyEntityRepository struct {
    db *sqlx.DB
}

func (r *MyEntityRepository) Create(ctx context.Context, entity *MyEntity) error {
    query := `INSERT INTO my_entities (id, name) VALUES ($1, $2)`
    _, err := r.db.ExecContext(ctx, query, entity.ID, entity.Name)
    return err
}
```

**4. Create use case:**
```go
// internal/usecase/my_entity_usecase.go
type MyEntityUseCase struct {
    repo domain.MyEntityRepository
}

func (uc *MyEntityUseCase) Create(ctx context.Context, req *CreateRequest) (*MyEntity, error) {
    // Validate, create, persist
}
```

**5. Add CLI command:**
```go
// internal/cli/commands/my_entity.go
var myEntityCmd = &cobra.Command{
    Use: "myentity",
    Short: "Manage my entities",
}
```

**6. Add HTTP handler:**
```go
// internal/interfaces/http/handlers/my_entity_handler.go
func (h *MyEntityHandler) HandleCreate(w http.ResponseWriter, r *http.Request) {
    // Parse, validate, call use case, return response
}
```

**7. Create migration:**
```sql
-- internal/migrations/XXX_add_my_entities.up.sql
CREATE TABLE my_entities (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Debugging

### Debug Logging

```bash
# Enable debug logging
export LOG_LEVEL=debug

# Run command
go run cmd/arx/main.go building list
```

### Database Query Logging

```bash
# Enable query logging in PostgreSQL
ALTER DATABASE arxos_dev SET log_statement = 'all';

# View logs
tail -f /usr/local/var/postgres/server.log  # macOS
sudo tail -f /var/log/postgresql/postgresql-14-main.log  # Linux
```

### Debugging Tests

```bash
# Run test with debugging
go test -v ./internal/usecase/ -run TestMyFunction

# Use Delve debugger
dlv test ./internal/usecase/ -- -test.run TestMyFunction
```

---

## Performance Optimization

### Database Optimization

**Add indexes:**
```sql
CREATE INDEX idx_equipment_building ON equipment(building_id);
CREATE INDEX idx_equipment_path ON equipment(path);
```

**Use prepared statements:**
```go
stmt, err := db.PrepareContext(ctx, "SELECT * FROM equipment WHERE id = $1")
defer stmt.Close()
```

**Connection pooling:**
```yaml
database:
  max_open_conns: 25
  max_idle_conns: 5
  conn_lifetime: 5m
```

### Caching Strategy

```go
// Check cache first
if cached, found := cache.Get(key); found {
    return cached, nil
}

// Query database
result, err := repo.GetByID(ctx, id)
if err != nil {
    return nil, err
}

// Cache result
cache.Set(key, result, 5*time.Minute)
return result, nil
```

---

## Deployment

### Building for Production

```bash
# Build optimized binary
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
  -ldflags="-w -s" \
  -o arxos-linux-amd64 \
  ./cmd/arx

# Build Docker image
docker build -t arxos:latest .
```

### Environment Configuration

```yaml
# configs/environments/production.yml
postgis:
  host: ${DB_HOST}
  port: 5432
  database: arxos_production
  user: ${DB_USER}
  password: ${DB_PASSWORD}
  sslmode: require

server:
  port: 8080
  timeout: 30s
  
logging:
  level: info
  format: json
```

**See [Deployment Guide](deployment/DEPLOYMENT_GUIDE.md) for production deployment.**

---

## Useful Resources

### Internal Documentation

- [Project Status](STATUS.md) - Current implementation status
- [Architecture Details](architecture/) - Design decisions
- [Integration Guides](integration/) - System integrations
- [API Documentation](api/API_DOCUMENTATION.md) - REST API reference

### External Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Manual](https://postgis.net/documentation/)
- [Go Documentation](https://go.dev/doc/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## Historical Documents

This guide consolidates and supersedes:
- [CODEBASE_DEEP_DIVE.md](archive/codebase-deep-dive-oct-2025.md) - Comprehensive codebase overview
- [TESTING_GUIDE.md](archive/testing-guide-oct-2025.md) - Testing instructions

For historical reference, see the [Archive](archive/).

---

## Quick Reference

### Build Commands
```bash
make build          # Build CLI binary
make test           # Run tests
make lint           # Run linters
make clean          # Clean build artifacts
```

### Database Commands
```bash
arx migrate up      # Run migrations
arx migrate down    # Rollback
arx migrate status  # Check status
arx health          # Verify connection
```

### Development Commands
```bash
arx serve           # Start API server
arx render <id>     # Render floor plan
arx building create # Create test data
```

---

*For questions or improvements, see the [Documentation Index](DOCUMENTATION_INDEX.md).*

