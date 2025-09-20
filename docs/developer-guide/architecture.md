# ArxOS Architecture

## Overview

ArxOS follows Clean Architecture principles with clear separation of concerns and dependency inversion. The system is designed to be modular, testable, and maintainable.

## Architecture Principles

### 1. Clean Architecture Layers

```
┌──────────────────────────────────────────┐
│            External Systems              │
│  (PostgreSQL, File System, HTTP, etc.)   │
└─────────────────┬────────────────────────┘
                  │
┌─────────────────▼────────────────────────┐
│              Adapters Layer              │
│  (Database, Import/Export, API handlers) │
└─────────────────┬────────────────────────┘
                  │
┌─────────────────▼────────────────────────┐
│            Service Layer                 │
│  (Business Logic Orchestration)          │
└─────────────────┬────────────────────────┘
                  │
┌─────────────────▼────────────────────────┐
│              Core Domain                 │
│  (Entities, Value Objects, Interfaces)   │
└──────────────────────────────────────────┘
```

### 2. Dependency Rule
- Dependencies point inward only
- Core domain has no external dependencies
- Outer layers depend on inner layers
- Interfaces defined in inner layers, implemented in outer layers

### 3. Package Structure

```
arxos/
├── cmd/
│   └── arxos/              # Application entry points
│       └── main.go
├── internal/
│   ├── core/              # Domain logic (no external deps)
│   │   ├── building/      # Building aggregate
│   │   ├── equipment/     # Equipment entities
│   │   ├── spatial/       # Spatial value objects
│   │   └── types/         # Shared types
│   ├── adapters/          # External integrations
│   │   ├── database/      # PostgreSQL/PostGIS
│   │   ├── cache/         # Ristretto cache
│   │   └── storage/       # File system
│   ├── api/               # HTTP/WebSocket handlers
│   │   ├── rest/          # REST endpoints
│   │   ├── websocket/     # Real-time streams
│   │   └── middleware/    # Auth, logging, etc.
│   ├── services/          # Application services
│   │   ├── building/      # Building operations
│   │   ├── import/        # Import orchestration
│   │   └── spatial/       # Spatial queries
│   └── importer/          # Import implementations
│       └── formats/       # IFC, PDF, CSV parsers
├── pkg/                   # Public packages
│   ├── arxid/            # ArxOS ID generation
│   └── confidence/       # Confidence scoring
└── migrations/           # Database migrations
```

## Core Domain

### Building Aggregate

```go
// internal/core/building/building.go
package building

import (
    "github.com/google/uuid"
    "github.com/arxos/arxos/internal/core/spatial"
)

type Building struct {
    ID          uuid.UUID
    ArxosID     string
    Name        string
    Origin      spatial.GPSCoordinate
    Floors      []Floor
    Metadata    map[string]interface{}
    CreatedAt   time.Time
    UpdatedAt   time.Time
}

type Repository interface {
    Create(ctx context.Context, building *Building) error
    GetByID(ctx context.Context, id uuid.UUID) (*Building, error)
    Update(ctx context.Context, building *Building) error
    Delete(ctx context.Context, id uuid.UUID) error
}
```

### Equipment Entity

```go
// internal/core/equipment/equipment.go
package equipment

type Equipment struct {
    ID         string
    ArxosID    string
    Name       string
    Type       EquipmentType
    Position   *spatial.Point3D
    Confidence spatial.Confidence
    Attributes map[string]interface{}
}

type EquipmentType string

const (
    TypeHVAC       EquipmentType = "hvac"
    TypeElectrical EquipmentType = "electrical"
    TypePlumbing   EquipmentType = "plumbing"
    TypeSensor     EquipmentType = "sensor"
    TypeSecurity   EquipmentType = "security"
)
```

### Spatial Value Objects

```go
// internal/core/spatial/types.go
package spatial

type Point3D struct {
    X float64
    Y float64
    Z float64
}

type GPSCoordinate struct {
    Latitude  float64
    Longitude float64
    Altitude  float64
}

type BoundingBox struct {
    Min Point3D
    Max Point3D
}

type Confidence string

const (
    ConfidenceLow    Confidence = "low"
    ConfidenceMedium Confidence = "medium"
    ConfidenceHigh   Confidence = "high"
)
```

## Service Layer

### Building Service

```go
// internal/services/building/service.go
package building

type Service struct {
    repo      building.Repository
    events    EventPublisher
    validator Validator
}

func (s *Service) CreateBuilding(ctx context.Context, req CreateBuildingRequest) (*building.Building, error) {
    // Validate request
    if err := s.validator.Validate(req); err != nil {
        return nil, err
    }

    // Create building
    b := &building.Building{
        ID:      uuid.New(),
        ArxosID: arxid.Generate("BLD"),
        Name:    req.Name,
        Origin:  req.Origin,
    }

    // Persist
    if err := s.repo.Create(ctx, b); err != nil {
        return nil, err
    }

    // Publish event
    s.events.Publish(BuildingCreatedEvent{Building: b})

    return b, nil
}
```

### Import Service

```go
// internal/services/import/service.go
package import

type Service struct {
    importers map[string]Importer
    repo      building.Repository
    jobs      JobQueue
}

func (s *Service) Import(ctx context.Context, req ImportRequest) (*Job, error) {
    // Select importer
    importer, ok := s.importers[req.Format]
    if !ok {
        return nil, ErrUnsupportedFormat
    }

    // Create job
    job := &Job{
        ID:     uuid.New(),
        Status: StatusPending,
    }

    // Queue async processing
    s.jobs.Enqueue(func() {
        model, err := importer.Import(req.Data)
        if err != nil {
            job.Status = StatusFailed
            job.Error = err.Error()
            return
        }

        // Save to database
        if err := s.repo.Create(ctx, model); err != nil {
            job.Status = StatusFailed
            job.Error = err.Error()
            return
        }

        job.Status = StatusCompleted
    })

    return job, nil
}
```

## Adapter Layer

### Database Adapter

```go
// internal/adapters/database/postgis.go
package database

import (
    "database/sql"
    _ "github.com/lib/pq"
)

type PostGISRepository struct {
    db *sql.DB
}

func (r *PostGISRepository) Create(ctx context.Context, b *building.Building) error {
    query := `
        INSERT INTO buildings (id, arxos_id, name, origin, metadata)
        VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5, $6), 4326), $7)
    `

    _, err := r.db.ExecContext(ctx, query,
        b.ID, b.ArxosID, b.Name,
        b.Origin.Longitude, b.Origin.Latitude, b.Origin.Altitude,
        b.Metadata,
    )

    return err
}
```

### Cache Adapter

```go
// internal/adapters/cache/ristretto.go
package cache

import "github.com/dgraph-io/ristretto"

type RistrettoCache struct {
    cache *ristretto.Cache
}

func (c *RistrettoCache) Get(key string) (interface{}, bool) {
    return c.cache.Get(key)
}

func (c *RistrettoCache) Set(key string, value interface{}, ttl time.Duration) {
    c.cache.SetWithTTL(key, value, 1, ttl)
}
```

## API Layer

### REST Handlers

```go
// internal/api/rest/building_handler.go
package rest

type BuildingHandler struct {
    service *building.Service
}

func (h *BuildingHandler) Create(w http.ResponseWriter, r *http.Request) {
    var req CreateBuildingRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, http.StatusBadRequest, err)
        return
    }

    building, err := h.service.CreateBuilding(r.Context(), req)
    if err != nil {
        respondError(w, http.StatusInternalServerError, err)
        return
    }

    respondJSON(w, http.StatusCreated, building)
}
```

### WebSocket Streams

```go
// internal/api/websocket/spatial_stream.go
package websocket

type SpatialStreamHandler struct {
    upgrader websocket.Upgrader
    spatial  *spatial.Service
}

func (h *SpatialStreamHandler) Stream(w http.ResponseWriter, r *http.Request) {
    conn, err := h.upgrader.Upgrade(w, r, nil)
    if err != nil {
        return
    }
    defer conn.Close()

    // Parse query parameters
    center := parsePoint3D(r.URL.Query())
    radius := parseFloat(r.URL.Query().Get("radius"))

    // Subscribe to spatial changes
    events := h.spatial.StreamProximityChanges(r.Context(), center, radius)

    for event := range events {
        if err := conn.WriteJSON(event); err != nil {
            return
        }
    }
}
```

## Database Schema

### Core Tables

```sql
-- Buildings table
CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxos_id VARCHAR(12) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    origin GEOMETRY(PointZ, 4326),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Floors table
CREATE TABLE floors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    level INTEGER NOT NULL,
    height DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Equipment table
CREATE TABLE equipment (
    id VARCHAR(50) PRIMARY KEY,
    arxos_id VARCHAR(12) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    building_id UUID REFERENCES buildings(id),
    floor_id UUID REFERENCES floors(id),
    attributes JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Equipment positions (separate for optimization)
CREATE TABLE equipment_positions (
    equipment_id VARCHAR(50) PRIMARY KEY REFERENCES equipment(id),
    position GEOMETRY(PointZ, 4326) NOT NULL,
    confidence VARCHAR(10) NOT NULL,
    source VARCHAR(50),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Spatial Indices

```sql
-- Multi-resolution spatial indices
CREATE INDEX idx_equipment_position_coarse
    ON equipment_positions USING GIST (ST_SnapToGrid(position, 10.0));

CREATE INDEX idx_equipment_position_medium
    ON equipment_positions USING GIST (ST_SnapToGrid(position, 1.0));

CREATE INDEX idx_equipment_position_fine
    ON equipment_positions USING GIST (ST_SnapToGrid(position, 0.1));

-- Type-specific indices
CREATE INDEX idx_hvac_equipment
    ON equipment_positions USING GIST (position)
    WHERE equipment_id IN (SELECT id FROM equipment WHERE type = 'hvac');
```

## Design Patterns

### Repository Pattern
- Abstracts data persistence
- Enables testing with mocks
- Supports multiple implementations

### Service Layer Pattern
- Orchestrates business logic
- Manages transactions
- Handles cross-cutting concerns

### Factory Pattern
- Creates appropriate importers
- Configures complex objects
- Manages dependencies

### Observer Pattern
- Event-driven architecture
- Real-time notifications
- Decoupled components

### Strategy Pattern
- Query optimization selection
- Import format handling
- Export format selection

## Error Handling

### Error Types

```go
// internal/core/errors/errors.go
package errors

type DomainError struct {
    Code    string
    Message string
    Cause   error
}

var (
    ErrBuildingNotFound = &DomainError{
        Code:    "BUILDING_NOT_FOUND",
        Message: "Building not found",
    }

    ErrInvalidCoordinates = &DomainError{
        Code:    "INVALID_COORDINATES",
        Message: "Invalid GPS coordinates",
    }
)
```

### Error Propagation
1. Domain errors bubble up unchanged
2. Infrastructure errors wrapped with context
3. API layer translates to HTTP status codes
4. Logging at service boundaries

## Testing Strategy

### Unit Tests
- Pure functions in core domain
- Mock external dependencies
- Table-driven tests for edge cases

### Integration Tests
- Database operations
- API endpoints
- Import/export pipelines

### Performance Tests
- Spatial query benchmarks
- Concurrent load testing
- Memory profiling

### Example Test

```go
// internal/services/building/service_test.go
package building_test

func TestCreateBuilding(t *testing.T) {
    // Setup
    repo := &mockRepository{}
    events := &mockEventPublisher{}
    service := building.NewService(repo, events)

    // Test
    req := CreateBuildingRequest{
        Name: "Test Building",
        Origin: spatial.GPSCoordinate{
            Latitude:  37.7749,
            Longitude: -122.4194,
        },
    }

    building, err := service.CreateBuilding(context.Background(), req)

    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, building)
    assert.Equal(t, "Test Building", building.Name)
    assert.True(t, repo.CreateCalled)
    assert.True(t, events.PublishCalled)
}
```

## Deployment Architecture

### Container Structure

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    environment:
      DATABASE_URL: postgres://arxos:password@db:5432/arxos
      REDIS_URL: redis://cache:6379
    depends_on:
      - db
      - cache
    ports:
      - "8080:8080"

  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: arxos
      POSTGRES_USER: arxos
      POSTGRES_PASSWORD: password
    volumes:
      - db_data:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    volumes:
      - cache_data:/data

volumes:
  db_data:
  cache_data:
```

### Production Considerations

1. **High Availability**
   - PostgreSQL streaming replication
   - Load balancer with health checks
   - Rolling deployments

2. **Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Alert manager

3. **Security**
   - JWT authentication
   - Role-based access control
   - API rate limiting
   - SQL injection prevention

4. **Performance**
   - Connection pooling
   - Query result caching
   - Spatial index optimization
   - Horizontal scaling

## Development Workflow

### Local Development

```bash
# Start dependencies
docker-compose up -d db

# Run migrations
go run cmd/arxos/main.go migrate up

# Run with hot reload
air

# Run tests
go test ./...

# Run benchmarks
go test -bench=. ./internal/database/...
```

### Code Quality

```bash
# Format code
gofmt -w .

# Lint
golangci-lint run

# Security scan
gosec ./...

# Test coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## Next Steps

- [API Documentation](../api/): Complete API reference
- [Contributing Guide](../contributing.md): How to contribute
- [Deployment Guide](./deployment.md): Production deployment
- [Performance Tuning](./performance.md): Optimization guide