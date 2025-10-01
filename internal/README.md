# ArxOS Internal Architecture

This directory contains the internal implementation of ArxOS following **Clean Architecture** principles and [Go Blueprint](https://github.com/Melkeydev/go-blueprint) standards.

## 🏗️ Architecture Overview

ArxOS follows Clean Architecture with clear separation of concerns across four main layers:

```
internal/
├── app/           # Dependency Injection Container
├── domain/        # Business Logic & Entities  
├── usecase/       # Application Business Rules
├── infrastructure/ # External Concerns
├── interfaces/    # Interface Adapters
└── config/        # Configuration Management
```

## ✅ **Go Blueprint Compliance**

The `/internal` directory now fully complies with [Go Blueprint](https://github.com/Melkeydev/go-blueprint) standards:

- **Clean Architecture Layers**: Proper separation of concerns
- **Dependency Inversion**: Inner layers don't depend on outer layers  
- **Interface-Based Design**: All dependencies through interfaces
- **Professional Structure**: Follows enterprise Go standards
- **Testable Architecture**: Easy to mock and unit test

## 📁 Directory Structure

### `/app` - Dependency Injection Container
- **`container.go`** - Main DI container managing all dependencies

### `/domain` - Business Logic & Entities
- **`entities.go`** - Core domain entities (User, Building, Equipment, etc.)
- **`interfaces.go`** - Repository and service interfaces
- **Pure business logic** - No external dependencies

### `/usecase` - Application Business Rules
- **`user_usecase.go`** - User management business logic
- **`building_usecase.go`** - Building management business logic
- **`equipment_usecase.go`** - Equipment management business logic
- **`organization_usecase.go`** - Organization management business logic
- **`analytics_usecase.go`** - Analytics and reporting business logic
- **`buildingops_usecase.go`** - Building operations and control logic

### `/infrastructure` - External Concerns
- **`cache.go`** - Caching implementations
- **`database.go`** - Database interface implementations
- **`logger.go`** - Logging implementations
- **`repositories.go`** - Concrete repository implementations
- **`postgis/`** - PostGIS-specific database implementations
- **`logging/`** - Logging infrastructure
- **`utils/`** - Infrastructure utilities (ID generation, etc.)
- **`services/`** - Background services (daemon, file processing)

### `/interfaces` - Interface Adapters
- **`http/`** - HTTP handlers and middleware
  - **`handlers/`** - HTTP request handlers
  - **`middleware/`** - HTTP middleware (auth, CORS, rate limiting)
  - **`models/`** - HTTP request/response models
  - **`types/`** - HTTP server types

### `/config` - Configuration Management
- **`config.go`** - Configuration loading and validation
- **`environments.go`** - Environment-specific configurations
- **`loader.go`** - Configuration file loading
- **`manager.go`** - Configuration management
- **`templates.go`** - Configuration templates
- **`validator.go`** - Configuration validation

## 🔄 **How BuildingOps and Daemon Fit in Go Blueprint**

### **BuildingOps** → **Use Case Layer** (`/usecase/buildingops_usecase.go`)
- **Purpose**: Building operations and control business logic
- **Responsibilities**: Equipment control, building mode management, health monitoring
- **Why Use Case**: Contains business rules for building operations
- **Dependencies**: Only depends on domain interfaces (repositories, logger)

### **Daemon** → **Infrastructure Layer** (`/infrastructure/services/`)
- **Purpose**: Background service for file watching and processing
- **Responsibilities**: File system monitoring, auto-import/export, background processing
- **Why Infrastructure**: External concern (file system, background processing)
- **Dependencies**: Can depend on use cases and domain interfaces

## 🎯 **Benefits of This Structure**

**Clean Separation of Concerns:**
- Business logic isolated from technical implementation
- Easy to test and maintain
- Clear boundaries between layers

**Dependency Inversion:**
- Inner layers don't depend on outer layers
- All dependencies flow inward through interfaces
- Easy to swap implementations

**Testability:**
- Each layer can be tested independently
- Business logic can be unit tested without external dependencies
- Easy to mock interfaces for testing

**Scalability:**
- Easy to add new features without affecting existing code
- Supports multiple interface types (HTTP, CLI, etc.)
- Clear structure supports team development

## 🔄 Dependency Flow

The architecture enforces dependency direction following Clean Architecture:

```
┌─────────────────┐
│   Interfaces    │ → HTTP handlers, CLI, etc.
└─────────────────┘
         ↓
┌─────────────────┐
│    Use Cases    │ → Business logic, validation
└─────────────────┘
         ↓
┌─────────────────┐
│     Domain      │ → Entities, interfaces
└─────────────────┘
         ↑
┌─────────────────┐
│ Infrastructure  │ → Database, cache, logging
└─────────────────┘
```

**Key Principles:**
- **Dependencies point inward** - Outer layers depend on inner layers
- **Interfaces define contracts** - Domain defines what it needs, infrastructure implements
- **No circular dependencies** - Clean separation prevents coupling
- **Testability** - Easy to mock interfaces for unit testing

## 🚀 Usage Example

```go
// Initialize the application
container := app.NewContainer()
ctx := context.Background()
config := &config.Config{...}

// Initialize all dependencies
err := container.Initialize(ctx, config)
if err != nil {
    log.Fatal(err)
}

// Use services through the container
userUC := container.GetUserUseCase()
user, err := userUC.CreateUser(ctx, &domain.CreateUserRequest{
    Email: "user@example.com",
    Name:  "John Doe",
    Role:  "user",
})
```

## 🧪 Testing Strategy

Each layer can be tested independently:

- **Domain**: Pure unit tests with no dependencies
- **Use Cases**: Mock repositories and test business logic
- **Infrastructure**: Integration tests with real external systems
- **Interfaces**: HTTP tests with mocked use cases

## 📈 Benefits

1. **Maintainability**: Clear separation makes code easier to understand and modify
2. **Testability**: Each layer can be tested in isolation
3. **Flexibility**: Easy to swap implementations (e.g., different databases)
4. **Scalability**: Clean boundaries support team development
5. **Go Blueprint Compliance**: Follows industry-standard Go project structure

## 🔧 Configuration

The container accepts a `config.Config` object that defines:
- Database connection settings
- Cache configuration
- Logging levels
- Environment-specific settings

## 📚 Related Documentation

- [Go Blueprint Repository](https://github.com/Melkeydev/go-blueprint)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [ArxOS Building Repository Design](../BUILDING_REPOSITORY_DESIGN.md)
