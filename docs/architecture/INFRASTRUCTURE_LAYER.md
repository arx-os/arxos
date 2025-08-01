# Infrastructure Layer Documentation

## Overview

The Infrastructure Layer provides all external dependencies, data persistence, and integration with external services for the Arxos platform. It implements the interfaces defined in the domain layer following Clean Architecture principles.

## Architecture Components

### Database Layer (`infrastructure/database/`)

#### Core Components
- **`config.py`** - Database configuration management with PostgreSQL support
- **`connection.py`** - SQLAlchemy connection management with connection pooling
- **`session.py`** - Database session management and transaction handling

#### Database Models (`infrastructure/database/models/`)
- **`base.py`** - Base model with common fields (timestamps, audit, soft delete)
- **`building.py`** - BuildingModel for building entities
- **`floor.py`** - FloorModel for floor entities  
- **`room.py`** - RoomModel for room entities
- **`device.py`** - DeviceModel for device entities
- **`user.py`** - UserModel for user entities
- **`project.py`** - ProjectModel for project entities

### Repository Layer (`infrastructure/repositories/`)

#### Base Repository
- **`base.py`** - BaseRepository with common CRUD operations and entity-model conversion

#### Entity-Specific Repositories
- **`building_repository.py`** - SQLAlchemyBuildingRepository
- **`floor_repository.py`** - SQLAlchemyFloorRepository
- **`room_repository.py`** - SQLAlchemyRoomRepository
- **`device_repository.py`** - SQLAlchemyDeviceRepository
- **`user_repository.py`** - SQLAlchemyUserRepository
- **`project_repository.py`** - SQLAlchemyProjectRepository

### Services Layer (`infrastructure/services/`)

#### External Service Integrations
- **`cache_service.py`** - RedisCacheService for caching functionality
- **`event_store.py`** - EventStoreService for domain event storage
- **`message_queue.py`** - MessageQueueService for message queuing

### Caching Layer (`infrastructure/caching/`)

#### Cache Management
- **`cache_manager.py`** - CacheManager for managing multiple cache strategies
- **`cache_strategy.py`** - CacheStrategy abstract base class for cache implementations

### Monitoring Layer (`infrastructure/monitoring/`)

#### Monitoring Components
- **`health_check.py`** - HealthCheckService for system health monitoring
- **`metrics.py`** - MetricsCollector for gathering system metrics
- **`logging.py`** - StructuredLogger for consistent log formatting

## Key Features

### Database Features
- Connection pooling with SQLAlchemy QueuePool
- Transaction management with context managers
- Soft delete support for all entities
- Audit fields (created_at, updated_at, created_by, updated_by)
- Metadata JSON field for extensibility
- Spatial data support with PostGIS
- Performance optimizations (pool_pre_ping, pool_reset_on_return)

### Repository Features
- Generic CRUD operations (save, get_by_id, find_all, delete)
- Entity-to-model and model-to-entity conversion
- Soft delete support
- Custom query methods for each entity
- Error handling with domain exceptions
- Transaction support

### Caching Features
- Redis-based caching with JSON serialization
- TTL (Time To Live) support
- Bulk operations (get_many, set_many)
- Pattern-based cache clearing
- Health checks and statistics

### Monitoring Features
- Health check service with pluggable checks
- Metrics collection (counters, gauges, histograms, timers)
- Structured logging with structlog
- Performance monitoring
- Error tracking and reporting

### Event-Driven Architecture
- Domain event storage
- Event retrieval by aggregate and type
- Event versioning support
- Event metadata handling

### Message Queuing
- Publish/subscribe pattern
- Queue management
- Message routing
- Health monitoring

## Technology Stack

### Core Technologies
- **SQLAlchemy 2.0** - ORM and database abstraction
- **PostgreSQL** - Primary database with PostGIS extension
- **Redis** - Caching and session storage
- **Alembic** - Database migrations
- **Pydantic** - Data validation and serialization

### Monitoring & Observability
- **Structlog** - Structured logging
- **Prometheus** - Metrics collection (ready for integration)
- **Health checks** - System health monitoring

## Architecture Benefits

### 1. Clean Architecture Compliance
- Clear separation of concerns
- Dependency inversion (domain interfaces implemented by infrastructure)
- Testable components with dependency injection
- Domain-driven design principles

### 2. Enterprise-Grade Features
- Connection pooling for performance
- Transaction management for data consistency
- Soft delete for data integrity
- Audit trails for compliance
- Health monitoring for reliability
- Structured logging for observability

### 3. Scalability Features
- Connection pooling for high concurrency
- Caching for performance optimization
- Event-driven architecture for loose coupling
- Message queuing for asynchronous processing
- Metrics collection for performance monitoring

### 4. Maintainability Features
- Consistent error handling
- Comprehensive logging
- Health checks for monitoring
- Modular design for easy extension
- Type hints for better IDE support

## Usage Examples

### Database Configuration
```python
from infrastructure.database.config import DatabaseConfig

config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="arxos",
    username="arxos_user",
    password="password"
)
```

### Repository Usage
```python
from infrastructure.repositories.building_repository import SQLAlchemyBuildingRepository
from infrastructure.database.session import DatabaseSession

# Create repository with session
session = DatabaseSession(session_factory)
repo = SQLAlchemyBuildingRepository(session)

# Use repository
building = repo.get_by_id(building_id)
buildings = repo.find_by_status(BuildingStatus.ACTIVE)
```

### Caching Usage
```python
from infrastructure.services.cache_service import RedisCacheService

cache = RedisCacheService(host="localhost", port=6379)
cache.set("key", value, ttl=3600)
value = cache.get("key")
```

### Health Monitoring
```python
from infrastructure.monitoring.health_check import HealthCheckService

health_service = HealthCheckService()
health_service.register_check("database", database_health_check)
results = health_service.run_all_checks()
```

## Testing

The infrastructure layer includes comprehensive tests in `tests/test_infrastructure_layer.py` covering:
- Database configuration and connection tests
- Repository CRUD operation tests
- Model conversion tests
- Service instantiation tests
- Health check tests

## Next Steps

The infrastructure layer is ready for integration with the Application Layer, where it will be used to:
1. Wire repositories to application services
2. Add caching to application operations
3. Integrate event publishing with domain events
4. Add health monitoring to application endpoints 