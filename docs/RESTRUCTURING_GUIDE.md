# ArxOS Restructuring Guide

## Overview

This guide outlines the migration from ArxOS's current 30+ package structure to a Clean Architecture with go-blueprint patterns, reducing complexity and improving maintainability.

## 🎯 Goals

1. **Reduce Package Complexity**: From 30+ packages to 8 focused packages
2. **Implement Clean Architecture**: Clear separation of concerns
3. **Add Missing Features**: WebSocket support, dependency injection
4. **Improve Testability**: Better mocking and isolation
5. **Enhance Maintainability**: Consistent patterns across the codebase

## 📊 Current vs Target Structure

### Current Structure (30+ packages)
```
internal/
├── adapters/          # Database adapters
├── analytics/         # Analytics engine
├── api/              # API handlers + services (mixed concerns)
├── auth/             # Authentication
├── bim/              # BIM processing
├── cache/            # Caching layer
├── common/           # Common utilities
├── compliance/       # Compliance features
├── config/           # Configuration
├── connections/      # Connection management
├── converter/        # File conversion
├── core/             # Core business logic
├── daemon/           # Background services
├── database/         # Database layer
├── ecosystem/        # Ecosystem management
├── email/            # Email services
├── errors/           # Error handling
├── exporter/         # Data export
├── facility/         # Facility management
├── handlers/         # Web handlers
├── hardware/         # Hardware platform
├── importer/         # Data import
├── integration/      # External integrations
├── interfaces/       # Interface definitions
├── it/              # IT management
├── metrics/         # Metrics collection
├── middleware/      # HTTP middleware
├── migration/       # Database migrations
├── notifications/   # Notification system
├── rendering/       # Rendering services
├── search/          # Search functionality
├── security/        # Security features
├── services/        # Business services
├── simulation/      # Building simulation
├── spatial/         # Spatial operations
├── storage/         # Storage management
├── telemetry/       # Telemetry collection
├── types/           # Type definitions
├── validation/      # Data validation
├── visualization/   # Visualization
└── workflow/        # Workflow management
```

### Target Structure (8 packages)
```
internal/
├── app/             # Application layer
│   ├── handlers/    # HTTP handlers (merge api/handlers + handlers/web)
│   ├── services/    # Application services (merge services/)
│   ├── middleware/  # HTTP middleware (merge middleware/)
│   └── cli/         # CLI commands (move from cmd/)
├── domain/          # Business logic (pure, no dependencies)
│   ├── building/   # Building management
│   ├── equipment/   # Equipment operations
│   ├── spatial/     # Spatial operations
│   ├── analytics/   # Analytics & reporting
│   └── workflow/    # Workflow management
├── infra/           # Infrastructure (external dependencies)
│   ├── database/    # Database layer
│   ├── cache/       # Caching
│   ├── storage/     # File storage
│   └── messaging/   # WebSocket, notifications
└── web/             # Web interface
    ├── static/      # Static assets
    └── templates/   # HTML templates
```

## 🚀 Migration Plan

### Phase 1: Package Consolidation (Week 1-2)

#### Step 1: Create New Package Structure
```bash
# Create new directories
mkdir -p internal/app/handlers
mkdir -p internal/app/services
mkdir -p internal/app/middleware
mkdir -p internal/app/cli
mkdir -p internal/domain/building
mkdir -p internal/domain/equipment
mkdir -p internal/domain/spatial
mkdir -p internal/domain/analytics
mkdir -p internal/domain/workflow
mkdir -p internal/infra/database
mkdir -p internal/infra/cache
mkdir -p internal/infra/storage
mkdir -p internal/infra/messaging
mkdir -p internal/web/static
mkdir -p internal/web/templates
```

#### Step 2: Move and Consolidate Packages

**Application Layer Consolidation:**
- `internal/api/handlers/` + `internal/handlers/web/` → `internal/app/handlers/`
- `internal/services/` → `internal/app/services/`
- `internal/middleware/` → `internal/app/middleware/`
- `cmd/arx/` → `internal/app/cli/`

**Domain Layer Consolidation:**
- `internal/core/building/` → `internal/domain/building/`
- `internal/core/equipment/` → `internal/domain/equipment/`
- `internal/spatial/` → `internal/domain/spatial/`
- `internal/analytics/` → `internal/domain/analytics/`
- `internal/workflow/` → `internal/domain/workflow/`

**Infrastructure Layer Consolidation:**
- `internal/database/` → `internal/infra/database/`
- `internal/cache/` → `internal/infra/cache/`
- `internal/storage/` → `internal/infra/storage/`
- `internal/notifications/` → `internal/infra/messaging/`

**Web Interface Consolidation:**
- `web/static/` → `internal/web/static/`
- `web/templates/` → `internal/web/templates/`

### Phase 2: Add Missing Features (Week 3-4)

#### Step 1: WebSocket Support
```go
// internal/infra/messaging/websocket.go
type BuildingMonitor struct {
    clients map[string][]*websocket.Conn
    hub     chan BuildingUpdate
}

func (bm *BuildingMonitor) BroadcastUpdate(buildingID string, update BuildingUpdate) {
    // Broadcast real-time building updates
}
```

#### Step 2: Dependency Injection
```go
// internal/app/container.go
type Container struct {
    db     database.Interface
    cache  cache.Interface
    ws     messaging.WebSocketHub
}

func NewContainer(config *config.Config) *Container {
    // Initialize dependencies
}
```

#### Step 3: Clean Architecture Interfaces
```go
// internal/domain/building/repository.go
type BuildingRepository interface {
    Create(ctx context.Context, building *Building) error
    GetByID(ctx context.Context, id string) (*Building, error)
    Update(ctx context.Context, building *Building) error
    Delete(ctx context.Context, id string) error
}
```

### Phase 3: Update Imports and Dependencies

#### Step 1: Update Import Statements
```go
// Before
import "github.com/arx-os/arxos/internal/api/handlers"
import "github.com/arx-os/arxos/internal/services"

// After
import "github.com/arx-os/arxos/internal/app/handlers"
import "github.com/arx-os/arxos/internal/app/services"
```

#### Step 2: Update Build Scripts
```bash
# Update Makefile targets
# Update Docker configurations
# Update CI/CD workflows
```

## 🔧 Implementation Details

### Dependency Injection Pattern
```go
// internal/app/services/building_service.go
type BuildingService struct {
    repo   domain.BuildingRepository
    cache  infra.CacheInterface
    logger common.Logger
}

func NewBuildingService(
    repo domain.BuildingRepository,
    cache infra.CacheInterface,
    logger common.Logger,
) *BuildingService {
    return &BuildingService{
        repo:   repo,
        cache:  cache,
        logger: logger,
    }
}
```

### WebSocket Integration
```go
// internal/infra/messaging/websocket.go
type WebSocketHub struct {
    clients    map[string][]*websocket.Conn
    register   chan *websocket.Conn
    unregister chan *websocket.Conn
    broadcast  chan []byte
}

func (h *WebSocketHub) Run() {
    for {
        select {
        case conn := <-h.register:
            // Register new client
        case conn := <-h.unregister:
            // Unregister client
        case message := <-h.broadcast:
            // Broadcast to all clients
        }
    }
}
```

### Clean Architecture Boundaries
```go
// Domain layer (no external dependencies)
type Building struct {
    ID       string
    Name     string
    Location *Location
}

// Infrastructure layer (external dependencies)
type PostGISBuildingRepository struct {
    db *sql.DB
}

func (r *PostGISBuildingRepository) Create(ctx context.Context, building *Building) error {
    // Database implementation
}
```

## 📋 Migration Checklist

### Phase 1: Package Consolidation
- [ ] Create new directory structure
- [ ] Move packages to new locations
- [ ] Update import statements
- [ ] Update build configurations
- [ ] Run tests to ensure functionality

### Phase 2: Add Missing Features
- [ ] Implement WebSocket support
- [ ] Add dependency injection
- [ ] Create clean architecture interfaces
- [ ] Update service constructors
- [ ] Add integration tests

### Phase 3: Cleanup and Optimization
- [ ] Remove old package directories
- [ ] Update documentation
- [ ] Optimize build times
- [ ] Update CI/CD workflows
- [ ] Performance testing

## 🚨 Breaking Changes

### Import Path Changes
```go
// Breaking changes in import paths
- "github.com/arx-os/arxos/internal/api/handlers"
+ "github.com/arx-os/arxos/internal/app/handlers"

- "github.com/arx-os/arxos/internal/services"
+ "github.com/arx-os/arxos/internal/app/services"
```

### Service Constructor Changes
```go
// Before: Direct instantiation
service := services.NewBuildingService(db)

// After: Dependency injection
container := app.NewContainer(config)
service := container.BuildingService()
```

## 🎯 Benefits After Migration

1. **Reduced Complexity**: 8 packages instead of 30+
2. **Better Testability**: Dependency injection and interfaces
3. **Real-time Features**: WebSocket support for building monitoring
4. **Cleaner Architecture**: Clear separation of concerns
5. **Easier Maintenance**: Consistent patterns across codebase
6. **Better Performance**: Optimized package structure and caching

## 📚 Additional Resources

- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Go-Blueprint Patterns](https://github.com/Melkeydev/go-blueprint)
- [Dependency Injection in Go](https://blog.drewolson.org/dependency-injection-in-go/)
- [WebSocket Implementation Guide](https://github.com/gorilla/websocket)

## 🤝 Contributing

When contributing to the restructured codebase:

1. Follow Clean Architecture principles
2. Use dependency injection for services
3. Keep domain logic pure (no external dependencies)
4. Write tests for all new functionality
5. Update documentation for any changes

## 📞 Support

For questions about the restructuring process:
- Create an issue in the repository
- Review the updated architecture documentation
- Check the migration examples in this guide
