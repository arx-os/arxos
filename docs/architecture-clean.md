# ArxOS Clean Architecture Guide

## Overview

ArxOS follows Clean Architecture principles with a domain-driven design approach. The system is built around the concept of Buildings as repositories of equipment, with PostgreSQL/PostGIS providing spatial database capabilities.

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│                   API Layer                     │
│         REST Endpoints / Authentication         │
├─────────────────────────────────────────────────┤
│                Service Layer                    │
│        Business Logic / Workflows               │
├─────────────────────────────────────────────────┤
│                 Domain Layer                    │
│      Core Entities / Business Rules             │
├─────────────────────────────────────────────────┤
│               Repository Layer                  │
│            Data Access Interfaces               │
├─────────────────────────────────────────────────┤
│                Adapter Layer                    │
│         PostgreSQL/PostGIS Implementation       │
└─────────────────────────────────────────────────┘
```

### 1. Domain Layer (`internal/core/`)
Core business entities and rules, independent of infrastructure:
- **Building**: Represents a physical building with GPS origin
- **Equipment**: Items within buildings with 3D positions
- **User**: System users with role-based permissions

```go
// Example: Building Entity
type Building struct {
    ID       uuid.UUID
    ArxosID  string     // Unique identifier like "MAIN-OFFICE"
    Name     string
    Origin   *Origin    // GPS coordinates
    Rotation float64    // Building rotation from north
}
```

### 2. Repository Layer (`internal/core/*/repository.go`)
Interfaces defining data persistence operations:

```go
type BuildingRepository interface {
    Create(ctx context.Context, building *Building) error
    GetByID(ctx context.Context, id uuid.UUID) (*Building, error)
    GetByArxosID(ctx context.Context, arxosID string) (*Building, error)
    Update(ctx context.Context, building *Building) error
    Delete(ctx context.Context, id uuid.UUID) error
}
```

### 3. Service Layer (`internal/services/`)
Business logic and complex workflows:
- **ImportService**: Handles IFC, CSV, JSON, BIM imports
- **ExportService**: Generates various output formats
- **AuthService**: JWT authentication and session management

### 4. Adapter Layer (`internal/adapters/`)
Infrastructure implementations:
- **PostGIS Adapter**: PostgreSQL with spatial extensions
- Implements repository interfaces
- Handles spatial queries and coordinate transformations

### 5. API Layer (`internal/api/`)
REST endpoints with authentication middleware:
- JWT-based authentication
- Role-based access control
- Request validation and error handling

## Core Components

### Spatial Database (PostGIS)
- **Coordinate System**: WGS84 (SRID 4326)
- **3D Support**: GEOMETRY(PointZ, 4326) for equipment positions
- **Spatial Queries**: Nearby, within bounds, on floor
- **Precision**: Millimeter-level accuracy

### Authentication System
```
User Request → JWT Validation → Role Check → Action
```

**Roles**:
- **Admin**: Full system control
- **Manager**: Building management
- **Technician**: Equipment updates, coordinate access
- **Viewer**: Read-only access

### BIM Format (.bim.txt)
Hierarchical text format for building data:
```
Building: Main Office
├── Floor 1: Ground Floor
│   ├── Room 101: Lobby
│   │   ├── OUTLET-001: Main Outlet [OK] @(10,5)
│   │   └── LIGHT-001: Entry Light [FAILED] @(10,10)
```

## Data Flow

### Import Pipeline
```
Input File → Parser → Validator → Domain Objects → Repository → PostGIS
```

Supported formats:
- IFC (Industry Foundation Classes)
- CSV (Equipment lists)
- JSON (Structured data)
- BIM (.bim.txt format)

### Export Pipeline
```
PostGIS → Repository → Domain Objects → Formatter → Output File
```

### Spatial Query Flow
```
API Request → Service → Repository → PostGIS Spatial Query → Results
```

## Coordinate System

### Global Positioning
- **Origin**: Building GPS coordinates (WGS84)
- **Rotation**: Building orientation from north (degrees)
- **Equipment**: Relative positions converted to global coordinates

### Coordinate Transformation
```go
// Local to Global transformation
globalLon = origin.Lon + (localX * cos(rotation) - localY * sin(rotation))
globalLat = origin.Lat + (localX * sin(rotation) + localY * cos(rotation))
globalAlt = origin.Alt + localZ
```

## Security Model

### Authentication Flow
1. User login with credentials
2. Generate JWT access token (1 hour)
3. Generate refresh token (30 days)
4. Include JWT in Authorization header
5. Validate token on each request

### Authorization Matrix
| Action | Admin | Manager | Technician | Viewer |
|--------|-------|---------|------------|--------|
| Create Building | ✓ | ✓ | ✗ | ✗ |
| Update Equipment | ✓ | ✓ | ✓ | ✗ |
| View Coordinates | ✓ | ✓ | ✓ | ✗ |
| Delete Building | ✓ | ✗ | ✗ | ✗ |
| Manage Users | ✓ | ✗ | ✗ | ✗ |

## Database Schema

### Core Tables
```sql
-- Buildings with spatial origin
CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxos_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    origin GEOMETRY(Point, 4326),
    rotation FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment with 3D positions
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    position GEOMETRY(PointZ, 4326),
    status TEXT DEFAULT 'unknown',
    confidence SMALLINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial indexes for performance
CREATE INDEX idx_equipment_position ON equipment USING GIST(position);
CREATE INDEX idx_buildings_origin ON buildings USING GIST(origin);
```

## Error Handling

### Standard Error Types
```go
var (
    ErrNotFound      = errors.New("not found")
    ErrAlreadyExists = errors.New("already exists")
    ErrUnauthorized  = errors.New("unauthorized")
    ErrInvalidInput  = errors.New("invalid input")
)
```

### Error Response Format
```json
{
    "error": "Error message",
    "code": "400",
    "details": "Additional context"
}
```

## Performance Considerations

### Database Optimization
- Spatial indexes on geometry columns
- Connection pooling (25 connections)
- Prepared statements for repeated queries
- Batch operations for bulk imports

### Caching Strategy
- Building metadata: 5 minutes
- Equipment lists: 1 minute
- User sessions: Duration of JWT

### Query Optimization
- Use bounding box filters before distance calculations
- Limit results with pagination
- Project only required fields

## Testing Strategy

### Unit Tests
- Domain entities validation
- Service logic testing
- Repository mocks

### Integration Tests
- PostGIS operations
- API endpoints
- Import/Export pipelines

### Test Coverage Goals
- Domain layer: 90%
- Service layer: 80%
- API layer: 70%

## Deployment

### Environment Variables
```bash
POSTGIS_HOST=localhost
POSTGIS_PORT=5432
POSTGIS_DB=arxos
POSTGIS_USER=arxos
POSTGIS_PASSWORD=secret
JWT_SECRET=your-secret-key
SERVER_PORT=8080
```

### Docker Deployment
```yaml
version: '3.8'
services:
  arxos:
    image: arxos:latest
    environment:
      - POSTGIS_HOST=db
    depends_on:
      - db

  db:
    image: postgis/postgis:16-3.4
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=secret
```

### Health Checks
- `/health`: Basic service health
- `/ready`: Database connectivity
- `/metrics`: Prometheus metrics

## Development Workflow

### Adding New Features
1. Define domain entities
2. Create repository interfaces
3. Implement PostGIS adapters
4. Add service logic
5. Create API endpoints
6. Write tests
7. Update documentation

### Code Standards
- Go 1.21+
- gofmt for formatting
- golint for linting
- 80% test coverage minimum
- Dependency injection
- Interface-based design

## Migration Path

### From Legacy System
1. Export existing data to CSV/JSON
2. Run import service
3. Validate spatial data
4. Update equipment statuses
5. Migrate user accounts
6. Switch DNS/load balancer

### Database Migrations
Using golang-migrate:
```bash
migrate create -ext sql -dir migrations -seq add_equipment_metadata
migrate up
migrate down
```