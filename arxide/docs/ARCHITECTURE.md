# ArxIDE Architecture Documentation

## Overview

ArxIDE follows Clean Architecture principles with a clear separation of concerns across multiple layers. The architecture is designed to be maintainable, testable, and scalable while adhering to the ARXOS project standards.

## Architecture Layers

### 1. Domain Layer (`src/domain.rs`)

The innermost layer containing the core business logic and domain entities.

#### **Domain Entities**
- **Project**: Aggregate root representing a CAD project
- **CadObject**: Individual CAD objects (lines, circles, walls, etc.)
- **Constraint**: Geometric and business constraints
- **Position**: 2D/3D position value object
- **Dimensions**: Size and dimension value object

#### **Domain Events**
- `ProjectCreated`: When a new project is created
- `ProjectOpened`: When a project is opened
- `ProjectSaved`: When a project is saved
- `ProjectExported`: When a project is exported
- `ObjectAdded`: When a CAD object is added
- `ObjectModified`: When a CAD object is modified
- `ObjectDeleted`: When a CAD object is deleted
- `ConstraintAdded`: When a constraint is added
- `ConstraintViolated`: When a constraint is violated

#### **Domain Services**
- **ProjectService**: Orchestrates project operations
- **ProjectRepository**: Data access interface
- **ExportService**: Export functionality interface
- **EventPublisher**: Event publishing interface

#### **Value Objects**
- **ExportFormat**: Supported export formats (SVGX, DXF, IFC, PDF, PNG)
- **ConstraintSeverity**: Constraint violation levels (Info, Warning, Error, Critical)

### 2. Application Layer (`src/application.rs`)

Contains use cases and application services that orchestrate domain operations.

#### **Use Cases**
- **CreateProjectUseCase**: Creates new projects
- **LoadProjectUseCase**: Loads existing projects
- **SaveProjectUseCase**: Saves projects
- **AddObjectUseCase**: Adds CAD objects to projects
- **UpdateObjectUseCase**: Updates CAD objects
- **RemoveObjectUseCase**: Removes CAD objects
- **AddConstraintUseCase**: Adds constraints to projects
- **ExportProjectUseCase**: Exports projects to various formats
- **ValidateProjectUseCase**: Validates project constraints
- **ListRecentProjectsUseCase**: Lists recent projects

#### **Application Services**
- **ProjectApplicationService**: Orchestrates all project operations
- **ApplicationConfig**: Application configuration management

#### **DTOs (Data Transfer Objects)**
- **CreateProjectRequest/Response**: Project creation
- **AddObjectRequest/Response**: Object addition
- **AddConstraintRequest/Response**: Constraint addition
- **ExportProjectRequest/Response**: Project export
- **ProjectInfo**: Project summary information
- **ConstraintViolationDto**: Constraint violation details

### 3. Infrastructure Layer (`src/infrastructure.rs`)

Handles external concerns like file I/O, persistence, and external services.

#### **Repository Implementations**
- **FileProjectRepository**: File-based project persistence
- **InMemoryProjectRepository**: In-memory repository for testing

#### **Service Implementations**
- **ArxideExportService**: Export functionality implementation
- **LoggingEventPublisher**: Event publishing with logging

#### **Infrastructure Services**
- **InfrastructureServices**: Main infrastructure service container
- **ConfigurationManager**: Configuration management
- **FileSystemService**: File system operations
- **BackupService**: Project backup and restore

## Design Patterns

### 1. Clean Architecture
- **Dependency Rule**: Dependencies point inward
- **Domain Independence**: Domain layer has no external dependencies
- **Framework Independence**: Domain logic is framework-agnostic

### 2. Domain-Driven Design (DDD)
- **Aggregates**: Project as the main aggregate root
- **Entities**: CadObject, Constraint with identity
- **Value Objects**: Position, Dimensions, ExportFormat
- **Domain Events**: Event-driven communication
- **Repository Pattern**: Abstract data access

### 3. SOLID Principles
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Repository implementations are substitutable
- **Interface Segregation**: Small, focused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

### 4. Hexagonal Architecture
- **Ports**: Repository, ExportService, EventPublisher interfaces
- **Adapters**: FileProjectRepository, ArxideExportService implementations
- **Domain Core**: Independent of external concerns

## Data Flow

### 1. Project Creation Flow
```
Frontend → Tauri Command → Application Service → Use Case → Domain Service → Repository
```

### 2. Project Export Flow
```
Frontend → Tauri Command → Application Service → Use Case → Domain Service → Export Service
```

### 3. Event Publishing Flow
```
Domain Event → Event Publisher → Logging/External Systems
```

## Error Handling

### 1. Error Types
- **DomainError**: Business rule violations
- **ApplicationError**: Use case validation errors
- **InfrastructureError**: File system, serialization errors

### 2. Error Propagation
- Errors bubble up through layers
- Each layer adds context
- Final error messages are user-friendly

## Configuration Management

### 1. ApplicationConfig
- **max_project_name_length**: Maximum project name length
- **max_project_description_length**: Maximum description length
- **max_recent_projects**: Number of recent projects to track
- **default_export_format**: Default export format
- **enable_constraint_validation**: Enable/disable constraint validation
- **enable_event_publishing**: Enable/disable event publishing

### 2. Configuration Sources
- Default values
- Configuration files
- Environment variables
- Runtime updates

## Testing Strategy

### 1. Unit Testing
- **Domain Layer**: Test entities, value objects, domain services
- **Application Layer**: Test use cases with mocked dependencies
- **Infrastructure Layer**: Test repository implementations

### 2. Integration Testing
- **End-to-End**: Test complete workflows
- **Repository Testing**: Test with real file system
- **Service Integration**: Test service interactions

### 3. Test Utilities
- **InMemoryProjectRepository**: For fast, isolated testing
- **MockEventPublisher**: For testing event publishing
- **TestDataBuilder**: For creating test data

## Security Considerations

### 1. Input Validation
- All inputs validated at application layer
- Domain entities validate business rules
- File paths sanitized before use

### 2. Error Information
- Sensitive data not exposed in error messages
- Logging levels appropriate for data sensitivity
- User-friendly error messages

### 3. File System Security
- Path validation and sanitization
- Permission checks
- Safe file operations

## Performance Optimizations

### 1. Async Operations
- All I/O operations are asynchronous
- Non-blocking event publishing
- Efficient file operations

### 2. Memory Management
- Efficient data structures
- Proper resource cleanup
- Lazy loading where appropriate

### 3. Caching
- Recent projects cached in memory
- Configuration cached after loading
- Export results cached temporarily

## Deployment Architecture

### 1. Tauri Integration
- **Commands**: Tauri commands interface with application layer
- **State Management**: Global infrastructure services
- **Error Handling**: Proper error propagation to frontend

### 2. File System Layout
```
~/.local/share/arxide/
├── projects/
│   ├── project1.json
│   ├── project2.json
│   └── ...
├── backups/
│   ├── project1_20231201_143022.json
│   └── ...
├── recent_projects.json
└── config.json
```

### 3. Cross-Platform Support
- **macOS**: `~/Library/Application Support/arxide/`
- **Linux**: `~/.local/share/arxide/`
- **Windows**: `%APPDATA%\arxide\`

## Development Guidelines

### 1. Code Organization
- **Layers**: Clear separation between domain, application, infrastructure
- **Modules**: Logical grouping within layers
- **Naming**: Consistent naming conventions

### 2. Documentation
- **API Documentation**: Complete documentation for all public APIs
- **Architecture Decisions**: ADRs for significant decisions
- **Code Comments**: Inline documentation for complex logic

### 3. Testing
- **Test Coverage**: High test coverage for all layers
- **Test Organization**: Tests mirror source code structure
- **Test Data**: Reusable test data builders

### 4. Error Handling
- **Comprehensive**: All error scenarios handled
- **User-Friendly**: Clear error messages for users
- **Logging**: Appropriate logging for debugging

## Future Enhancements

### 1. Database Integration
- **PostgreSQL**: For production data storage
- **Migrations**: Database schema management
- **Connection Pooling**: Efficient database connections

### 2. Cloud Integration
- **Cloud Storage**: Project backup to cloud
- **Collaboration**: Real-time collaboration features
- **Sync**: Multi-device synchronization

### 3. Advanced Features
- **Plugin System**: Extensible architecture for plugins
- **AI Integration**: AI-powered design assistance
- **Version Control**: Project versioning and history

## Compliance with ARXOS Standards

### 1. Architecture Alignment
- **Clean Architecture**: Follows ARXOS Clean Architecture patterns
- **Domain-Driven Design**: Consistent with ARXOS DDD approach
- **SOLID Principles**: Adheres to ARXOS coding standards

### 2. Technology Stack
- **Rust**: Consistent with ARXOS backend technology
- **Tauri**: Desktop application framework
- **Async/Await**: Modern async programming patterns

### 3. Quality Standards
- **Error Handling**: Comprehensive error handling
- **Testing**: Thorough testing strategy
- **Documentation**: Complete documentation
- **Security**: Security best practices

## Conclusion

ArxIDE's architecture provides a solid foundation for a professional CAD IDE while maintaining flexibility for future enhancements. The Clean Architecture approach ensures maintainability, testability, and scalability while adhering to ARXOS project standards.
