# Application Services

This directory contains the application layer services that implement business logic and coordinate use cases. These services follow Clean Architecture principles and provide the interface between the domain layer and infrastructure layer.

## Architecture Overview

```
Application Services
├── Business Services          # Core business logic services
├── External API Services     # External service integrations
└── Infrastructure Services   # Infrastructure coordination
```

## Service Categories

### 🏢 Business Services
Core business logic services that implement domain use cases:

- **`building_service.py`** - Building management and operations
- **`device_service.py`** - Device management and IoT integration
- **`floor_service.py`** - Floor management and spatial organization
- **`project_service.py`** - Project management and workflows
- **`room_service.py`** - Room management and space utilization
- **`user_service.py`** - User management and authentication

### 🔗 External API Services
External service integrations and API clients:

- **`mcp_engineering_service.py`** - MCP-Engineering service integration
- **`arxlogic_service.py`** - ArxLogic service integration
- **`arxlogic_service_mock.py`** - Mock ArxLogic service for testing

### 🛠️ Infrastructure Services
Infrastructure coordination and external system integration:

- **`external_apis/`** - External API client implementations
  - `building_validation_api.py` - Building validation services
  - `ai_ml_apis.py` - AI/ML service integrations

## Service Patterns

### Dependency Injection
All services use dependency injection through the application container:

```python
from application.container import container

class BuildingService:
    def __init__(self):
        self.repository = container.get_building_repository()
        self.event_store = container.get_event_store()
        self.cache = container.get_cache_service()
```

### Error Handling
Services implement consistent error handling:

```python
from application.exceptions import BusinessRuleError, ValidationError

def create_building(self, building_data: BuildingDTO) -> BuildingDTO:
    try:
        # Validate business rules
        self._validate_business_rules(building_data)
        
        # Create building
        building = self.repository.create(building_data)
        
        # Publish events
        self.event_store.publish(BuildingCreatedEvent(building))
        
        return building
    except ValidationError as e:
        raise BusinessRuleError(f"Building validation failed: {e}")
```

### Event Publishing
Services publish domain events for system integration:

```python
from domain.events import BuildingCreatedEvent, BuildingUpdatedEvent

def update_building(self, building_id: str, updates: BuildingDTO) -> BuildingDTO:
    building = self.repository.update(building_id, updates)
    self.event_store.publish(BuildingUpdatedEvent(building))
    return building
```

## Service Responsibilities

### Business Services
- **Validation**: Enforce business rules and domain constraints
- **Orchestration**: Coordinate multiple use cases and operations
- **Event Publishing**: Publish domain events for system integration
- **Transaction Management**: Ensure data consistency across operations

### External API Services
- **API Client Management**: Handle external API connections and authentication
- **Data Transformation**: Transform between internal and external data formats
- **Error Handling**: Handle external service failures and retries
- **Rate Limiting**: Implement rate limiting for external API calls

### Infrastructure Services
- **Resource Management**: Manage database connections, cache, message queues
- **Monitoring**: Implement health checks and metrics collection
- **Configuration**: Handle service-specific configuration management
- **Security**: Implement authentication and authorization

## Testing

### Unit Testing
Each service should have comprehensive unit tests:

```python
import pytest
from unittest.mock import Mock
from application.services.building_service import BuildingService

class TestBuildingService:
    def setup_method(self):
        self.mock_repository = Mock()
        self.mock_event_store = Mock()
        self.service = BuildingService()
        self.service.repository = self.mock_repository
        self.service.event_store = self.mock_event_store
    
    def test_create_building_success(self):
        # Test building creation
        building_data = BuildingDTO(name="Test Building")
        self.mock_repository.create.return_value = building_data
        
        result = self.service.create_building(building_data)
        
        assert result == building_data
        self.mock_repository.create.assert_called_once()
        self.mock_event_store.publish.assert_called_once()
```

### Integration Testing
Services should be tested with real infrastructure components:

```python
import pytest
from application.container import container

class TestBuildingServiceIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        container.initialize(test_config)
        yield
        container.cleanup()
    
    async def test_create_building_integration(self):
        service = container.get_building_service()
        building_data = BuildingDTO(name="Integration Test Building")
        
        result = await service.create_building(building_data)
        
        assert result.id is not None
        assert result.name == "Integration Test Building"
```

## Configuration

Services use the centralized configuration system:

```python
from application.config import get_settings

class BuildingService:
    def __init__(self):
        self.config = get_settings()
        self.repository = container.get_building_repository()
    
    def get_buildings(self, filters: Dict[str, Any]) -> List[BuildingDTO]:
        # Use configuration for pagination, caching, etc.
        page_size = self.config.database.pool_size
        cache_ttl = self.config.cache.ttl_default
        # ... implementation
```

## Performance Considerations

### Caching
Services implement intelligent caching strategies:

```python
def get_building(self, building_id: str) -> BuildingDTO:
    # Try cache first
    cache_key = f"building:{building_id}"
    cached = self.cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from repository
    building = self.repository.get_by_id(building_id)
    
    # Cache for future requests
    self.cache.set(cache_key, building, ttl=3600)
    return building
```

### Connection Pooling
Services use connection pooling for external APIs:

```python
class MCPEngineeringService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
        )
```

### Async Operations
Services use async/await for I/O operations:

```python
async def create_building_async(self, building_data: BuildingDTO) -> BuildingDTO:
    # Async database operation
    building = await self.repository.create_async(building_data)
    
    # Async event publishing
    await self.event_store.publish_async(BuildingCreatedEvent(building))
    
    return building
```

## Security

### Input Validation
All services validate input data:

```python
from pydantic import ValidationError

def create_building(self, building_data: BuildingDTO) -> BuildingDTO:
    try:
        # Validate input
        validated_data = BuildingDTO(**building_data.dict())
        return self.repository.create(validated_data)
    except ValidationError as e:
        raise ValidationError(f"Invalid building data: {e}")
```

### Authentication & Authorization
Services implement proper authentication and authorization:

```python
from application.security import require_auth, require_role

@require_auth
@require_role("building_manager")
def create_building(self, building_data: BuildingDTO, user: User) -> BuildingDTO:
    # Check if user has permission to create buildings
    if not user.can_create_buildings():
        raise AuthorizationError("User cannot create buildings")
    
    return self.repository.create(building_data)
```

## Monitoring & Observability

### Logging
Services implement structured logging:

```python
import structlog

logger = structlog.get_logger(__name__)

def create_building(self, building_data: BuildingDTO) -> BuildingDTO:
    logger.info("Creating building", 
                building_name=building_data.name,
                user_id=building_data.created_by)
    
    try:
        building = self.repository.create(building_data)
        logger.info("Building created successfully", 
                    building_id=building.id)
        return building
    except Exception as e:
        logger.error("Failed to create building", 
                     error=str(e),
                     building_name=building_data.name)
        raise
```

### Metrics
Services collect performance metrics:

```python
from application.monitoring import metrics

def get_buildings(self, filters: Dict[str, Any]) -> List[BuildingDTO]:
    with metrics.timer("building_service.get_buildings"):
        buildings = self.repository.get_all(filters)
        metrics.counter("building_service.buildings_retrieved", len(buildings))
        return buildings
```

## Best Practices

1. **Single Responsibility**: Each service should have a single, well-defined responsibility
2. **Dependency Injection**: Use the container for dependency management
3. **Error Handling**: Implement comprehensive error handling and logging
4. **Event Publishing**: Publish domain events for system integration
5. **Testing**: Maintain high test coverage for all services
6. **Documentation**: Keep service documentation up to date
7. **Performance**: Monitor and optimize service performance
8. **Security**: Implement proper authentication and authorization

## Service Lifecycle

### Initialization
Services are initialized through the application container:

```python
# In application/container.py
def get_building_service(self) -> BuildingService:
    if not self._building_service:
        self._building_service = BuildingService(
            repository=self.get_building_repository(),
            event_store=self.get_event_store(),
            cache=self.get_cache_service()
        )
    return self._building_service
```

### Cleanup
Services implement proper cleanup methods:

```python
class BuildingService:
    async def cleanup(self):
        """Cleanup service resources"""
        await self.repository.close()
        await self.event_store.close()
        await self.cache.close()
```

This documentation provides a comprehensive guide to the application services architecture and implementation patterns. 