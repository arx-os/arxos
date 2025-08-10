# Arxos Platform Development Guide

## Overview

This guide provides comprehensive information for developers working on the Arxos platform. It covers development setup, coding standards, testing practices, and deployment procedures.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Security Best Practices](#security-best-practices)
6. [Performance Optimization](#performance-optimization)
7. [Database Management](#database-management)
8. [API Development](#api-development)
9. [Deployment Procedures](#deployment-procedures)
10. [Monitoring and Debugging](#monitoring-and-debugging)

## Development Environment Setup

### Prerequisites

- **Python 3.9+**: Primary development language
- **PostgreSQL 13+**: Database server
- **Redis 6+**: Caching and session storage
- **Docker**: Containerization (optional)
- **Git**: Version control

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arx-os/arxos.git
   cd arxos
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Database setup:**
   ```bash
   # Create database
   createdb arxos_dev
   
   # Run migrations
   alembic upgrade head
   
   # Seed development data (optional)
   python scripts/seed_dev_data.py
   ```

6. **Start development server:**
   ```bash
   python main.py
   # Or using uvicorn
   uvicorn main:app --reload --port 8000
   ```

### Docker Development Environment

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head

# View logs
docker-compose logs -f app
```

### IDE Configuration

#### VS Code Setup

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreter": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

## Project Structure

```
arxos/
├── application/                 # Application Layer
│   ├── services/               # Application Services
│   ├── dto/                   # Data Transfer Objects
│   ├── exceptions/            # Application Exceptions
│   └── commands/              # Command Objects
├── domain/                     # Domain Layer
│   ├── entities/              # Domain Entities
│   ├── value_objects/         # Value Objects
│   ├── repositories/          # Repository Interfaces
│   ├── events/               # Domain Events
│   ├── services/             # Domain Services
│   └── exceptions/           # Domain Exceptions
├── infrastructure/            # Infrastructure Layer
│   ├── database/             # Database Configuration
│   ├── repositories/         # Repository Implementations
│   ├── services/            # External Service Integrations
│   ├── security/            # Security Infrastructure
│   ├── performance/         # Performance Monitoring
│   ├── logging/            # Logging Infrastructure
│   └── error_handling/     # Error Handling
├── presentation/             # Presentation Layer
│   ├── api/                # REST API Endpoints
│   ├── graphql/           # GraphQL Schema & Resolvers
│   ├── web/               # Web Interface
│   └── cli/               # Command Line Interface
├── tests/                   # Test Suite
│   ├── unit/              # Unit Tests
│   ├── integration/       # Integration Tests
│   ├── framework/         # Test Framework
│   └── fixtures/          # Test Fixtures
├── docs/                   # Documentation
├── scripts/               # Utility Scripts
├── migrations/           # Database Migrations
├── config/              # Configuration Files
└── deployment/         # Deployment Scripts
```

### Layer Responsibilities

#### Domain Layer
- Core business logic and rules
- Domain entities and value objects
- Domain events and services
- Repository interfaces
- No dependencies on external frameworks

#### Application Layer
- Orchestrate business operations
- Handle use cases and workflows
- Coordinate between domain and infrastructure
- Data transformation and validation
- Transaction management

#### Infrastructure Layer
- External service integrations
- Database access and persistence
- Security implementation
- Performance optimization
- Cross-cutting concerns

#### Presentation Layer
- API endpoints and request handling
- Data serialization/deserialization
- Authentication and authorization
- Input validation
- Response formatting

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with additional conventions:

#### Code Formatting

Use **Black** for code formatting:
```bash
black --line-length 100 .
```

#### Import Organization

Use **isort** for import sorting:
```bash
isort --profile black .
```

Import order:
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Third-party
from sqlalchemy import Column, Integer, String
from fastapi import HTTPException

# Local
from domain.entities import Building
from application.services import BuildingService
```

#### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import Dict, List, Optional, Union

def create_building(name: str, address: Dict[str, str], 
                   created_by: str) -> Optional[Building]:
    """Create a new building with the given parameters."""
    # Implementation here
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def update_building_status(building_id: str, status: BuildingStatus, 
                         updated_by: str) -> bool:
    """Update the status of a building.
    
    Args:
        building_id: Unique identifier for the building
        status: New status to set
        updated_by: User ID who made the change
    
    Returns:
        True if update was successful, False otherwise
    
    Raises:
        BuildingNotFoundError: If building doesn't exist
        ValidationError: If status transition is invalid
    """
    # Implementation here
    pass
```

#### Error Handling

Use specific exception types and proper error handling:

```python
from domain.exceptions import BuildingNotFoundError
from application.exceptions import ValidationError

def get_building(building_id: str) -> Building:
    """Retrieve building by ID."""
    if not building_id:
        raise ValidationError("Building ID is required")
    
    building = repository.get_by_id(building_id)
    if not building:
        raise BuildingNotFoundError(f"Building {building_id} not found")
    
    return building
```

### Code Quality Tools

#### Linting

**Pylint Configuration** (`.pylintrc`):
```ini
[MASTER]
load-plugins=pylint_django

[FORMAT]
max-line-length=100

[MESSAGES CONTROL]
disable=missing-docstring,too-few-public-methods

[DESIGN]
max-args=10
max-locals=20
```

**Flake8 Configuration** (`.flake8`):
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,migrations
ignore = E203,W503
```

#### Pre-commit Hooks

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## Testing Guidelines

### Test Structure

Follow the Test Pyramid approach:

1. **Unit Tests (70%)**: Test individual components in isolation
2. **Integration Tests (20%)**: Test component interactions
3. **End-to-End Tests (10%)**: Test complete workflows

### Test Organization

```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_building_entity.py
│   │   └── test_value_objects.py
│   ├── application/
│   │   └── test_building_service.py
│   └── infrastructure/
│       └── test_repositories.py
├── integration/
│   ├── test_api_workflows.py
│   └── test_database_integration.py
├── framework/
│   ├── test_base.py
│   └── fixtures.py
└── conftest.py
```

### Unit Testing

#### Domain Entity Tests

```python
import pytest
from domain.entities import Building
from domain.value_objects import BuildingId, Address
from domain.exceptions import InvalidBuildingError

class TestBuildingEntity:
    """Test cases for Building entity."""
    
    def test_building_creation_with_valid_data(self):
        """Test successful building creation."""
        address = Address(
            street="123 Test St",
            city="Test City",
            state="TS",
            postal_code="12345"
        )
        
        building = Building(
            id=BuildingId(),
            name="Test Building",
            address=address,
            created_by="test_user"
        )
        
        assert building.name == "Test Building"
        assert building.address == address
        assert building.status == BuildingStatus.PLANNED
    
    def test_building_creation_fails_with_empty_name(self):
        """Test building creation with invalid data."""
        address = Address(
            street="123 Test St",
            city="Test City", 
            state="TS",
            postal_code="12345"
        )
        
        with pytest.raises(InvalidBuildingError, match="name cannot be empty"):
            Building(
                id=BuildingId(),
                name="",
                address=address,
                created_by="test_user"
            )
```

#### Application Service Tests

```python
import pytest
from unittest.mock import Mock, patch
from application.services.building_service import BuildingApplicationService
from domain.entities import Building
from tests.framework.test_base import ServiceTestCase

class TestBuildingApplicationService(ServiceTestCase):
    """Test cases for Building Application Service."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.service = BuildingApplicationService(
            unit_of_work=self.mock_unit_of_work,
            cache_service=self.mock_cache_service
        )
    
    def test_create_building_success(self):
        """Test successful building creation."""
        # Arrange
        self.mock_building_repository.save.return_value = self.test_building
        
        # Act
        response = self.service.create_building(
            name="Test Building",
            address=self.test_address,
            created_by="test_user"
        )
        
        # Assert
        assert response.success is True
        assert response.building_id is not None
        self.mock_building_repository.save.assert_called_once()
        self.mock_unit_of_work.commit.assert_called_once()
```

### Integration Testing

#### Database Integration

```python
import pytest
from tests.framework.test_base import IntegrationTestCase
from infrastructure.repositories.building_repository import SQLAlchemyBuildingRepository

class TestBuildingRepository(IntegrationTestCase):
    """Integration tests for Building repository."""
    
    def test_save_and_retrieve_building(self):
        """Test saving and retrieving building from database."""
        # Arrange
        building = self.test_data.create_test_building()
        repository = SQLAlchemyBuildingRepository(self.session)
        
        # Act
        saved_building = repository.save(building)
        retrieved_building = repository.get_by_id(saved_building.id)
        
        # Assert
        assert retrieved_building is not None
        assert retrieved_building.name == building.name
        assert retrieved_building.id == building.id
```

#### API Integration

```python
import pytest
from fastapi.testclient import TestClient
from main import app

class TestBuildingAPI:
    """Integration tests for Building API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.auth_headers = {"Authorization": "Bearer test-token"}
    
    def test_create_building_endpoint(self):
        """Test building creation endpoint."""
        building_data = {
            "name": "API Test Building",
            "address": {
                "street": "123 API Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345"
            }
        }
        
        response = self.client.post(
            "/api/v1/buildings",
            json=building_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "building_id" in data["data"]
```

### Test Configuration

#### pytest Configuration

`pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=application
    --cov=domain
    --cov=infrastructure
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    external: Tests requiring external services
```

#### Test Fixtures

`tests/conftest.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.database.models import Base
from tests.framework.test_base import TestDataFactory

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def test_session(test_engine):
    """Create test database session."""
    SessionFactory = sessionmaker(bind=test_engine)
    session = SessionFactory()
    yield session
    session.close()

@pytest.fixture
def test_data():
    """Provide test data factory."""
    return TestDataFactory()
```

### Test Data Management

#### Test Data Factory

```python
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_test_building(**overrides):
        """Create test building with default values."""
        defaults = {
            "id": BuildingId(),
            "name": "Test Building",
            "address": TestDataFactory.create_test_address(),
            "created_by": "test_user"
        }
        defaults.update(overrides)
        return Building(**defaults)
    
    @staticmethod
    def create_test_address(**overrides):
        """Create test address with default values."""
        defaults = {
            "street": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345"
        }
        defaults.update(overrides)
        return Address(**defaults)
```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run with coverage
pytest --cov=application --cov=domain --cov=infrastructure

# Run specific test file
pytest tests/unit/domain/test_building_entity.py

# Run tests with specific marker
pytest -m integration

# Run tests in parallel
pytest -n auto
```

## Security Best Practices

### Authentication and Authorization

#### JWT Token Implementation

```python
from infrastructure.security import AuthenticationService, require_permission, Permission

# Service with authentication
@require_permission(Permission.CREATE_BUILDING)
def create_building(request: CreateBuildingRequest, 
                   current_user: AuthenticationToken) -> CreateBuildingResponse:
    """Create building with proper authorization."""
    # Implementation here
    pass
```

#### Input Validation

```python
from infrastructure.security.input_validation import input_validator, ValidationRule

# Custom validation rule
building_name_rule = ValidationRule(
    name="building_name",
    pattern=r"^[a-zA-Z0-9\s\-_.()]{1,100}$",
    min_length=1,
    max_length=100,
    forbidden_chars="<>\"';|`${}[]"
)

# Validate input
is_valid, errors = input_validator.validate_field("name", building_name, building_name_rule)
if not is_valid:
    raise ValidationError(f"Invalid building name: {', '.join(errors)}")
```

#### Sensitive Data Handling

```python
from infrastructure.security.encryption import EncryptionService

# Encrypt sensitive data
encryption_service = EncryptionService()
encrypted_data = encryption_service.encrypt_sensitive_data(
    data={"ssn": "123-45-6789", "credit_card": "1234-5678-9012-3456"},
    sensitive_fields=["ssn", "credit_card"]
)

# Decrypt sensitive data
decrypted_data = encryption_service.decrypt_sensitive_data(
    encrypted_data=encrypted_data,
    sensitive_fields=["ssn", "credit_card"]
)
```

### Security Testing

```python
import pytest
from infrastructure.security.input_validation import input_validator

class TestSecurityValidation:
    """Security validation tests."""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection pattern detection."""
        malicious_input = "'; DROP TABLE buildings; --"
        is_valid, errors = input_validator.validate_field("name", malicious_input)
        
        assert not is_valid
        assert any("injection" in error.lower() for error in errors)
    
    def test_xss_prevention(self):
        """Test XSS pattern detection."""
        malicious_input = "<script>alert('xss')</script>"
        is_valid, errors = input_validator.validate_field("description", malicious_input)
        
        assert not is_valid
        assert any("script" in error.lower() for error in errors)
```

## Performance Optimization

### Caching Implementation

```python
from infrastructure.performance.caching_strategies import cached, intelligent_cache

@cached(ttl=3600, key_prefix="building_summary")
def get_building_summary(building_id: str) -> dict:
    """Get building summary with caching."""
    # Expensive operation here
    return expensive_operation(building_id)

# Manual cache management
def update_building(building_id: str, updates: dict):
    """Update building and invalidate cache."""
    # Update building
    building = repository.update(building_id, updates)
    
    # Invalidate related cache
    intelligent_cache.delete(f"building_summary:{building_id}")
    intelligent_cache.invalidate_by_tags({f"building:{building_id}"})
    
    return building
```

### Database Optimization

```python
from infrastructure.performance.query_optimization import optimized_query_execution

def get_buildings_with_optimization(filters: dict):
    """Get buildings with query optimization."""
    with optimized_query_execution(session, enable_caching=True) as optimizer:
        query = session.query(Building)
        
        # Apply filters
        if filters.get('status'):
            query = query.filter(Building.status == filters['status'])
        
        # Enable query caching
        cache_key = f"buildings_query_{hash(str(filters))}"
        cached_result = optimizer['cache'].get_cached_result(cache_key, str(filters))
        
        if cached_result:
            return cached_result
        
        # Execute query
        results = query.all()
        
        # Cache results
        optimizer['cache'].cache_result(cache_key, str(filters), results, ttl=1800)
        
        return results
```

### Performance Monitoring

```python
from infrastructure.performance.monitoring import performance_monitor, monitor_performance

@monitor_performance("building_creation", tags={"operation": "create"})
def create_building_with_monitoring(building_data: dict):
    """Create building with performance monitoring."""
    # Implementation here
    pass

# Custom metrics
performance_monitor.record_custom_metric(
    "buildings.created_today",
    count,
    MetricType.GAUGE,
    tags={"date": today.isoformat()}
)
```

## Database Management

### Migration Management

#### Creating Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add building status column"

# Manual migration
alembic revision -m "Add custom indexes"
```

#### Migration Structure

```python
"""Add building status column

Revision ID: abc123
Revises: def456
Create Date: 2024-01-15 10:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade database schema."""
    op.add_column('buildings', 
                  sa.Column('status', sa.String(50), nullable=False, default='planned'))
    
    # Create index
    op.create_index('ix_buildings_status', 'buildings', ['status'])

def downgrade():
    """Downgrade database schema."""
    op.drop_index('ix_buildings_status', table_name='buildings')
    op.drop_column('buildings', 'status')
```

#### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade abc123

# Rollback migration
alembic downgrade def456

# Show migration history
alembic history

# Show current revision
alembic current
```

### Database Optimization

#### Indexing Strategy

```python
# SQLAlchemy model with indexes
class Building(Base):
    __tablename__ = 'buildings'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    
    # Composite indexes
    __table_args__ = (
        Index('ix_buildings_status_created', 'status', 'created_at'),
        Index('ix_buildings_name_status', 'name', 'status'),
    )
```

#### Query Performance

```python
from sqlalchemy.orm import selectinload, joinedload

def get_buildings_with_floors_optimized(session):
    """Get buildings with floors using optimized loading."""
    return session.query(Building)\
                 .options(selectinload(Building.floors))\
                 .filter(Building.status == 'operational')\
                 .all()

def get_building_summary_optimized(session, building_id):
    """Get building with related data in single query."""
    return session.query(Building)\
                 .options(
                     joinedload(Building.floors).selectinload(Floor.rooms),
                     selectinload(Building.devices)
                 )\
                 .filter(Building.id == building_id)\
                 .first()
```

## API Development

### FastAPI Implementation

#### Endpoint Structure

```python
from fastapi import APIRouter, Depends, HTTPException, status
from application.dto.building_dto import CreateBuildingRequest, CreateBuildingResponse
from presentation.api.dependencies import get_current_user, get_building_service

router = APIRouter(prefix="/buildings", tags=["buildings"])

@router.post("", response_model=CreateBuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    request: CreateBuildingRequest,
    current_user: AuthenticationToken = Depends(get_current_user),
    building_service: BuildingApplicationService = Depends(get_building_service)
) -> CreateBuildingResponse:
    """Create a new building."""
    try:
        response = building_service.create_building(
            name=request.name,
            address=request.address,
            description=request.description,
            created_by=current_user.user_id
        )
        return response
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Building creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_ERROR", "message": "Building creation failed"}
        )
```

#### Request/Response Models

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class CreateBuildingRequest(BaseModel):
    """Request model for creating a building."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Building name")
    address: Dict[str, str] = Field(..., description="Building address")
    description: Optional[str] = Field(None, max_length=1000, description="Building description")
    coordinates: Optional[Dict[str, float]] = Field(None, description="GPS coordinates")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Building name cannot be empty')
        return v.strip()
    
    @validator('address')
    def address_must_be_complete(cls, v):
        required_fields = ['street', 'city', 'state', 'postal_code']
        for field in required_fields:
            if field not in v or not v[field].strip():
                raise ValueError(f'Address must include {field}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Corporate Headquarters",
                "address": {
                    "street": "123 Business Ave",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                },
                "description": "Main corporate office building",
                "coordinates": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            }
        }

class BuildingResponse(BaseModel):
    """Response model for building data."""
    
    id: str
    name: str
    status: str
    address: Dict[str, str]
    description: Optional[str]
    coordinates: Optional[Dict[str, float]]
    floors_count: int = 0
    rooms_count: int = 0
    devices_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    class Config:
        orm_mode = True
```

#### Error Handling

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": exc.errors if hasattr(exc, 'errors') else str(exc),
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "field_errors": {
                        ".".join(str(loc) for loc in error["loc"]): error["msg"]
                        for error in exc.errors()
                    }
                }
            }
        }
    )
```

### API Testing

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

class TestBuildingAPI:
    """API endpoint tests."""
    
    def test_create_building_success(self, client: TestClient, auth_headers: dict):
        """Test successful building creation."""
        building_data = {
            "name": "Test Building",
            "address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "postal_code": "12345"
            }
        }
        
        response = client.post(
            "/api/v1/buildings",
            json=building_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "building_id" in data["data"]
    
    def test_create_building_validation_error(self, client: TestClient, auth_headers: dict):
        """Test building creation with invalid data."""
        building_data = {
            "name": "",  # Invalid empty name
            "address": {
                "street": "123 Test St"
                # Missing required fields
            }
        }
        
        response = client.post(
            "/api/v1/buildings",
            json=building_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
```

## Deployment Procedures

### Environment Configuration

#### Production Settings

```python
# config/production.py
import os
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    BCRYPT_ROUNDS = 12
    
    # Cache
    REDIS_URL = os.getenv("REDIS_URL")
    CACHE_DEFAULT_TIMEOUT = 3600
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "json"
    
    # Monitoring
    METRICS_ENABLED = True
    TRACING_ENABLED = True
```

#### Docker Configuration

`Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash arxos
RUN chown -R arxos:arxos /app
USER arxos

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/arxos_prod
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=arxos_prod
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  redis:
    image: redis:6-alpine
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

### CI/CD Pipeline

`.github/workflows/ci-cd.yml`:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          flake8 .
          pylint application domain infrastructure
      
      - name: Run type checking
        run: mypy .
      
      - name: Run tests
        run: |
          pytest --cov=application --cov=domain --cov=infrastructure \
                 --cov-report=xml --cov-report=term-missing
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
  
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run security scan
        uses: pypa/gh-action-pip-audit@v1.0.0
      
      - name: Run Bandit security check
        run: |
          pip install bandit
          bandit -r application domain infrastructure
  
  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [test, security]
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to staging
        run: |
          # Deployment script here
          echo "Deploying to staging..."
      
      - name: Run smoke tests
        run: |
          # Smoke tests here
          echo "Running smoke tests..."
      
      - name: Deploy to production
        if: success()
        run: |
          # Production deployment here
          echo "Deploying to production..."
```

### Monitoring Setup

#### Application Monitoring

```python
# monitoring/health_check.py
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from infrastructure.database import get_session
from infrastructure.services.cache_service import redis_client

app = FastAPI()

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from infrastructure.performance.monitoring import performance_monitor
    return performance_monitor.get_performance_report()
```

This comprehensive development guide provides all the necessary information for developers to work effectively on the Arxos platform while maintaining high code quality, security, and performance standards.