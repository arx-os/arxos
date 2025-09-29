# ArxOS Developer Guide

## Overview

This guide provides comprehensive information for developers working with the ArxOS codebase, including architecture patterns, development workflows, and best practices.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment](#development-environment)
4. [Code Organization](#code-organization)
5. [Module Development](#module-development)
6. [API Development](#api-development)
7. [Testing](#testing)
8. [Database Management](#database-management)
9. [Deployment](#deployment)
10. [Development](#development)

## Getting Started

### Prerequisites

- Go 1.21 or later
- Docker and Docker Compose
- PostgreSQL with PostGIS extension
- Redis (optional, for caching)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Install dependencies
go mod download

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Start development environment
docker-compose -f docker/docker-compose.dev.yml up -d

# Run migrations
go run cmd/arx/main.go migrate up

# Start the application
go run cmd/arx/main.go daemon start
```

## Architecture Overview

### Clean Architecture Principles

ArxOS follows **Clean Architecture principles** with **go-blueprint patterns**, implementing clear separation of concerns and dependency inversion:

```
internal/
├── app/           # Application layer (HTTP, CLI, TUI)
│   ├── handlers/  # HTTP handlers (consolidated from api/handlers + handlers/web)
│   ├── services/  # Application services (consolidated from services/)
│   ├── middleware/ # HTTP middleware (consolidated from middleware/)
│   └── cli/       # CLI commands (moved from cmd/)
├── domain/        # Business logic (pure, no external dependencies)
│   ├── building/  # Building management
│   ├── equipment/ # Equipment operations  
│   ├── spatial/   # Spatial operations
│   ├── analytics/ # Analytics & reporting
│   └── workflow/  # Workflow management
├── infra/         # Infrastructure (external dependencies)
│   ├── database/  # Database layer
│   ├── cache/     # Caching
│   ├── storage/   # File storage
│   └── messaging/ # WebSocket, notifications
└── web/           # Web interface
    ├── static/    # Static assets
    └── templates/ # HTML templates
```

### Architecture Principles

1. **Dependency Inversion**: High-level modules don't depend on low-level modules
2. **Interface Segregation**: Small, focused interfaces for better testability
3. **Single Responsibility**: Each package has one clear purpose
4. **Clean Boundaries**: Domain logic is independent of infrastructure concerns

### Key Design Patterns

- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic encapsulation
- **Dependency Injection**: Better testability and modularity
- **WebSocket Support**: Real-time building monitoring
- **Command Query Separation**: Clear separation of read/write operations
- **Event Sourcing**: Audit trail and state reconstruction

## Development Environment

### Project Structure

```
arxos/
├── cmd/                    # Application entry points
│   └── arx/               # CLI application
├── internal/              # Private application code
│   ├── adapters/          # External adapters (database, APIs)
│   ├── analytics/         # Analytics engine
│   ├── api/               # REST API handlers
│   ├── auth/              # Authentication and authorization
│   ├── cache/             # Caching layer
│   ├── common/            # Shared utilities
│   ├── config/            # Configuration management
│   ├── core/              # Core business logic
│   ├── database/          # Database layer
│   ├── facility/          # CMMS/CAFM features
│   ├── hardware/          # Hardware platform
│   ├── it/                # IT asset management
│   ├── middleware/        # HTTP middleware
│   ├── services/          # Application services
│   ├── workflow/          # Workflow automation
│   └── ...                # Other modules
├── pkg/                   # Public packages
├── web/                   # Web interface
├── docs/                  # Documentation
├── scripts/               # Build and deployment scripts
└── test/                  # Test utilities
```

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgres://user:password@localhost:5432/arxos?sslmode=disable
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=arxos
POSTGRES_USER=arxos
POSTGRES_PASSWORD=arxos

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
API_HOST=localhost
API_PORT=8080
API_BASE_URL=http://localhost:8080

# Authentication
JWT_SECRET=your-jwt-secret
JWT_EXPIRY=24h

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=1h
CACHE_MAX_SIZE=100MB
```

### Development Tools

#### Required Tools
```bash
# Install Go tools
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
go install github.com/goreleaser/goreleaser@latest

# Install development dependencies
go install github.com/air-verse/air@latest  # Hot reload
go install github.com/swaggo/swag/cmd/swag@latest  # API documentation
```

#### VS Code Extensions
- Go (official)
- GitLens
- Docker
- PostgreSQL
- REST Client
- YAML

## Code Organization

### Module Structure

Each module follows a consistent structure:

```
internal/{module}/
├── {module}.go           # Main module interface
├── {module}_test.go      # Unit tests
├── api.go                # REST API handlers
├── cli.go                # CLI commands
├── {submodule}.go        # Submodule implementations
├── {submodule}_test.go   # Submodule tests
└── README.md             # Module documentation
```

### Package Naming

- **Internal packages**: `github.com/arx-os/arxos/internal/{module}`
- **Public packages**: `github.com/arx-os/arxos/pkg/{package}`
- **External packages**: Use full import paths

### Interface Design

```go
// Define interfaces for external dependencies
type Repository interface {
    Get(ctx context.Context, id string) (*Entity, error)
    Create(ctx context.Context, entity *Entity) error
    Update(ctx context.Context, entity *Entity) error
    Delete(ctx context.Context, id string) error
}

// Implement interfaces in adapters
type postgresRepository struct {
    db *sql.DB
}

func (r *postgresRepository) Get(ctx context.Context, id string) (*Entity, error) {
    // Implementation
}
```

## Module Development

### Creating a New Module

1. **Create module directory**:
```bash
mkdir internal/newmodule
cd internal/newmodule
```

2. **Create main module file**:
```go
// internal/newmodule/newmodule.go
package newmodule

import (
    "context"
    "sync"
    "github.com/arx-os/arxos/internal/common/logger"
)

// NewModule represents the main module interface
type NewModule struct {
    mu    sync.RWMutex
    data  map[string]*Data
    logger logger.Logger
}

// New creates a new module instance
func New() *NewModule {
    return &NewModule{
        data:   make(map[string]*Data),
        logger: logger.New("newmodule"),
    }
}

// Data represents module data
type Data struct {
    ID        string    `json:"id"`
    Name      string    `json:"name"`
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}
```

3. **Create API handlers**:
```go
// internal/newmodule/api.go
package newmodule

import (
    "encoding/json"
    "net/http"
    "github.com/arx-os/arxos/internal/common/logger"
)

// API provides HTTP handlers for the module
type API struct {
    module *NewModule
    logger logger.Logger
}

// NewAPI creates a new API instance
func NewAPI(module *NewModule) *API {
    return &API{
        module: module,
        logger: logger.New("newmodule.api"),
    }
}

// GetData handles GET /api/newmodule/data
func (a *API) GetData(w http.ResponseWriter, r *http.Request) {
    // Implementation
}
```

4. **Create CLI commands**:
```go
// internal/newmodule/cli.go
package newmodule

import (
    "github.com/spf13/cobra"
    "github.com/arx-os/arxos/internal/common/logger"
)

// CLI provides command-line interface for the module
type CLI struct {
    module *NewModule
    logger logger.Logger
}

// NewCLI creates a new CLI instance
func NewCLI(module *NewModule) *CLI {
    return &CLI{
        module: module,
        logger: logger.New("newmodule.cli"),
    }
}

// GetCommands returns CLI commands for the module
func (c *CLI) GetCommands() []*cobra.Command {
    var cmd = &cobra.Command{
        Use:   "newmodule",
        Short: "Manage new module data",
        Long:  "Manage new module data and operations",
    }
    
    cmd.AddCommand(c.getDataCommand())
    return []*cobra.Command{cmd}
}
```

5. **Create tests**:
```go
// internal/newmodule/newmodule_test.go
package newmodule

import (
    "testing"
    "time"
)

func TestNewModule(t *testing.T) {
    module := New()
    
    // Test module creation
    if module == nil {
        t.Fatal("Expected module to be created")
    }
    
    // Test data operations
    data := &Data{
        ID:   "test-001",
        Name: "Test Data",
    }
    
    err := module.CreateData(data)
    if err != nil {
        t.Fatalf("Failed to create data: %v", err)
    }
    
    // Test data retrieval
    retrieved, err := module.GetData("test-001")
    if err != nil {
        t.Fatalf("Failed to get data: %v", err)
    }
    
    if retrieved.Name != "Test Data" {
        t.Errorf("Expected name 'Test Data', got '%s'", retrieved.Name)
    }
}
```

### Module Integration

1. **Register module in main application**:
```go
// cmd/arx/main.go
import "github.com/arx-os/arxos/internal/newmodule"

func main() {
    // Initialize module
    newModule := newmodule.New()
    
    // Register CLI commands
    rootCmd.AddCommand(newModule.GetCommands()...)
    
    // Register API routes
    api.RegisterNewModuleRoutes(newModule)
}
```

2. **Add module to configuration**:
```yaml
# configs/development.yml
modules:
  newmodule:
    enabled: true
    config:
      setting1: value1
      setting2: value2
```

## API Development

### REST API Design

#### Resource-Based URLs
```
GET    /api/v1/{resource}           # List resources
GET    /api/v1/{resource}/{id}      # Get specific resource
POST   /api/v1/{resource}           # Create resource
PUT    /api/v1/{resource}/{id}      # Update resource
DELETE /api/v1/{resource}/{id}      # Delete resource
```

#### Request/Response Format
```go
// Request structure
type CreateRequest struct {
    Name        string                 `json:"name" validate:"required"`
    Description string                 `json:"description"`
    Metadata    map[string]interface{} `json:"metadata"`
}

// Response structure
type Response struct {
    Data    interface{} `json:"data"`
    Meta    *Meta       `json:"meta,omitempty"`
    Error   *Error      `json:"error,omitempty"`
}

type Meta struct {
    Timestamp string `json:"timestamp"`
    RequestID string `json:"request_id"`
}

type Error struct {
    Code    string      `json:"code"`
    Message string      `json:"message"`
    Details interface{} `json:"details,omitempty"`
}
```

#### Handler Implementation
```go
func (h *Handler) CreateResource(w http.ResponseWriter, r *http.Request) {
    var req CreateRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        h.respondWithError(w, http.StatusBadRequest, "INVALID_REQUEST", err.Error())
        return
    }
    
    // Validate request
    if err := h.validator.Struct(req); err != nil {
        h.respondWithError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
        return
    }
    
    // Create resource
    resource, err := h.service.CreateResource(r.Context(), &req)
    if err != nil {
        h.respondWithError(w, http.StatusInternalServerError, "CREATE_ERROR", err.Error())
        return
    }
    
    h.respondWithData(w, http.StatusCreated, resource)
}
```

### OpenAPI Documentation

#### Generate Documentation
```bash
# Install swag
go install github.com/swaggo/swag/cmd/swag@latest

# Generate documentation
swag init -g cmd/arx/main.go -o docs/swagger
```

#### API Documentation Comments
```go
// CreateResource creates a new resource
// @Summary Create resource
// @Description Create a new resource with the provided data
// @Tags resources
// @Accept json
// @Produce json
// @Param request body CreateRequest true "Resource data"
// @Success 201 {object} Response{data=Resource}
// @Failure 400 {object} Response{error=Error}
// @Failure 500 {object} Response{error=Error}
// @Router /api/v1/resources [post]
func (h *Handler) CreateResource(w http.ResponseWriter, r *http.Request) {
    // Implementation
}
```

## Testing

### Unit Testing

#### Test Structure
```go
func TestService_CreateResource(t *testing.T) {
    // Arrange
    service := NewService(mockRepository)
    req := &CreateRequest{
        Name: "Test Resource",
    }
    
    // Act
    result, err := service.CreateResource(context.Background(), req)
    
    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, result)
    assert.Equal(t, "Test Resource", result.Name)
}
```

#### Mocking
```go
// Mock repository
type mockRepository struct {
    resources map[string]*Resource
}

func (m *mockRepository) Create(ctx context.Context, resource *Resource) error {
    m.resources[resource.ID] = resource
    return nil
}

func (m *mockRepository) Get(ctx context.Context, id string) (*Resource, error) {
    resource, exists := m.resources[id]
    if !exists {
        return nil, ErrNotFound
    }
    return resource, nil
}
```

### Integration Testing

#### Test Database Setup
```go
func setupTestDB(t *testing.T) *sql.DB {
    db, err := sql.Open("postgres", testDBURL)
    require.NoError(t, err)
    
    // Run migrations
    err = runMigrations(db)
    require.NoError(t, err)
    
    return db
}

func teardownTestDB(t *testing.T, db *sql.DB) {
    // Clean up test data
    _, err := db.Exec("DELETE FROM resources")
    require.NoError(t, err)
    
    db.Close()
}
```

#### Integration Test Example
```go
func TestResourceIntegration(t *testing.T) {
    db := setupTestDB(t)
    defer teardownTestDB(t, db)
    
    repo := NewPostgresRepository(db)
    service := NewService(repo)
    
    // Test complete workflow
    resource, err := service.CreateResource(context.Background(), &CreateRequest{
        Name: "Integration Test Resource",
    })
    require.NoError(t, err)
    
    retrieved, err := service.GetResource(context.Background(), resource.ID)
    require.NoError(t, err)
    assert.Equal(t, resource.ID, retrieved.ID)
}
```

### End-to-End Testing

#### API Testing
```go
func TestAPI_CreateResource(t *testing.T) {
    // Setup test server
    server := setupTestServer(t)
    defer server.Close()
    
    // Create request
    reqBody := `{"name": "E2E Test Resource"}`
    req, err := http.NewRequest("POST", server.URL+"/api/v1/resources", strings.NewReader(reqBody))
    require.NoError(t, err)
    req.Header.Set("Content-Type", "application/json")
    
    // Execute request
    resp, err := http.DefaultClient.Do(req)
    require.NoError(t, err)
    defer resp.Body.Close()
    
    // Assert response
    assert.Equal(t, http.StatusCreated, resp.StatusCode)
    
    var response Response
    err = json.NewDecoder(resp.Body).Decode(&response)
    require.NoError(t, err)
    assert.NotNil(t, response.Data)
}
```

## Database Management

### Migrations

#### Creating Migrations
```bash
# Create new migration
go run cmd/arx/main.go migrate create add_resources_table

# This creates:
# migrations/007_add_resources_table.up.sql
# migrations/007_add_resources_table.down.sql
```

#### Migration Files
```sql
-- migrations/007_add_resources_table.up.sql
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_resources_name ON resources(name);
CREATE INDEX idx_resources_created_at ON resources(created_at);
```

```sql
-- migrations/007_add_resources_table.down.sql
DROP TABLE resources;
```

#### Running Migrations
```bash
# Run all pending migrations
go run cmd/arx/main.go migrate up

# Run specific migration
go run cmd/arx/main.go migrate up 007

# Rollback last migration
go run cmd/arx/main.go migrate down

# Rollback to specific migration
go run cmd/arx/main.go migrate down 006
```

### Database Queries

#### Query Optimization
```go
// Use prepared statements
func (r *repository) GetResource(ctx context.Context, id string) (*Resource, error) {
    query := `
        SELECT id, name, description, metadata, created_at, updated_at
        FROM resources
        WHERE id = $1
    `
    
    var resource Resource
    err := r.db.QueryRowContext(ctx, query, id).Scan(
        &resource.ID,
        &resource.Name,
        &resource.Description,
        &resource.Metadata,
        &resource.CreatedAt,
        &resource.UpdatedAt,
    )
    
    if err != nil {
        if err == sql.ErrNoRows {
            return nil, ErrNotFound
        }
        return nil, err
    }
    
    return &resource, nil
}
```

#### Spatial Queries
```go
// PostGIS spatial queries
func (r *repository) GetResourcesNearLocation(ctx context.Context, lat, lng float64, radius float64) ([]*Resource, error) {
    query := `
        SELECT id, name, description, metadata, created_at, updated_at
        FROM resources
        WHERE ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint($1, $2), 4326),
            $3
        )
        ORDER BY ST_Distance(location, ST_SetSRID(ST_MakePoint($1, $2), 4326))
    `
    
    rows, err := r.db.QueryContext(ctx, query, lng, lat, radius)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    var resources []*Resource
    for rows.Next() {
        var resource Resource
        err := rows.Scan(
            &resource.ID,
            &resource.Name,
            &resource.Description,
            &resource.Metadata,
            &resource.CreatedAt,
            &resource.UpdatedAt,
        )
        if err != nil {
            return nil, err
        }
        resources = append(resources, &resource)
    }
    
    return resources, nil
}
```

## Deployment

### Docker

#### Dockerfile
```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o arx cmd/arx/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/arx .
COPY --from=builder /app/configs ./configs

EXPOSE 8080
CMD ["./arx", "daemon", "start"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  arxos:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://arxos:arxos@postgres:5432/arxos?sslmode=disable
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=arxos
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arxos
  template:
    metadata:
      labels:
        app: arxos
    spec:
      containers:
      - name: arxos
        image: arxos:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: arxos-service
spec:
  selector:
    app: arxos
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### CI/CD Pipeline

#### GitHub Actions
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  merge_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:15-3.3
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: arxos_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Go
      uses: actions/setup-go@v3
      with:
        go-version: 1.21
    
    - name: Install dependencies
      run: go mod download
    
    - name: Run tests
      run: go test ./...
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/arxos_test?sslmode=disable
    
    - name: Run linter
      uses: golangci/golangci-lint-action@v3
      with:
        version: latest
    
    - name: Run security scan
      uses: securecodewarrior/github-action-gosec@master
      with:
        args: './...'

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v3
      with:
        context: .
        push: true
        tags: arxos:latest,arxos:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Kubernetes
      run: |
        echo "Deploying to Kubernetes..."
        # Add deployment commands here
```

## Development

### Development Workflow

1. **Clone the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write tests** for your changes
5. **Run tests and linters**:
   ```bash
   go test ./...
   golangci-lint run
   gosec ./...
   ```
6. **Commit your changes**:
   ```bash
   git commit -m "feat: add your feature description"
   ```
7. **Push to your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a merge request**

### Code Style

#### Go Code Style
- Follow standard Go formatting (`go fmt`)
- Use meaningful variable and function names
- Add comments for exported functions and types
- Keep functions small and focused
- Use interfaces for external dependencies

#### Commit Messages
Follow conventional commit format:
```
type(scope): description

feat(api): add user authentication endpoint
fix(database): resolve connection pool issue
docs(readme): update installation instructions
test(analytics): add unit tests for energy module
```

#### Merge Request Guidelines
- Provide a clear description of changes
- Include tests for new functionality
- Update documentation as needed
- Ensure all tests pass
- Request review from maintainers

### Code Review Process

1. **Automated Checks**: All PRs must pass automated tests and linters
2. **Manual Review**: At least one maintainer must approve
3. **Testing**: New features must include comprehensive tests
4. **Documentation**: Update relevant documentation
5. **Performance**: Consider performance implications
6. **Security**: Security-sensitive changes require additional review

### Issue Reporting

When reporting issues, please include:
- ArxOS version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs and error messages
- Screenshots (if applicable)

### Feature Requests

For feature requests, please include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Impact on existing functionality
- Implementation complexity estimate

## Best Practices

### Error Handling

```go
// Use custom error types
type ValidationError struct {
    Field   string
    Message string
}

func (e ValidationError) Error() string {
    return fmt.Sprintf("validation error on field %s: %s", e.Field, e.Message)
}

// Wrap errors with context
func (s *Service) CreateResource(ctx context.Context, req *CreateRequest) (*Resource, error) {
    if err := s.validateRequest(req); err != nil {
        return nil, fmt.Errorf("failed to validate request: %w", err)
    }
    
    resource, err := s.repository.Create(ctx, req)
    if err != nil {
        return nil, fmt.Errorf("failed to create resource: %w", err)
    }
    
    return resource, nil
}
```

### Logging

```go
// Use structured logging
logger.Info("resource created",
    "resource_id", resource.ID,
    "user_id", userID,
    "duration", time.Since(start),
)

// Use appropriate log levels
logger.Debug("processing request", "request_id", requestID)
logger.Info("user authenticated", "user_id", userID)
logger.Warn("rate limit exceeded", "user_id", userID)
logger.Error("database connection failed", "error", err)
```

### Configuration

```go
// Use environment-specific configuration
type Config struct {
    Database DatabaseConfig `yaml:"database"`
    API      APIConfig      `yaml:"api"`
    Cache    CacheConfig    `yaml:"cache"`
}

type DatabaseConfig struct {
    URL            string        `yaml:"url" env:"DATABASE_URL"`
    MaxConnections int           `yaml:"max_connections" env:"DB_MAX_CONNECTIONS" envDefault:"10"`
    Timeout        time.Duration `yaml:"timeout" env:"DB_TIMEOUT" envDefault:"30s"`
}

// Load configuration
func LoadConfig() (*Config, error) {
    config := &Config{}
    
    if err := env.Parse(config); err != nil {
        return nil, fmt.Errorf("failed to parse environment: %w", err)
    }
    
    return config, nil
}
```

### Performance

```go
// Use connection pooling
func NewRepository(db *sql.DB) *Repository {
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(25)
    db.SetConnMaxLifetime(5 * time.Minute)
    
    return &Repository{db: db}
}

// Use caching
func (s *Service) GetResource(ctx context.Context, id string) (*Resource, error) {
    // Check cache first
    if cached, found := s.cache.Get(id); found {
        return cached.(*Resource), nil
    }
    
    // Fetch from database
    resource, err := s.repository.Get(ctx, id)
    if err != nil {
        return nil, err
    }
    
    // Cache the result
    s.cache.Set(id, resource, time.Hour)
    
    return resource, nil
}
```

This developer guide provides comprehensive information for working with the ArxOS codebase. For additional help, please refer to the specific module documentation or contact the development team.
