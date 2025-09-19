# ArxOS - Building Information Management System

[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ArxOS is a building information management system that treats buildings like code repositories. It provides hierarchical equipment tracking, role-based access control, and seamless integration with BIM tools through a simple `.bim.txt` format.

## 🎯 Core Features

**Hierarchical Equipment Management**: Every piece of equipment has a clear path
```
Building: Main Office
├── Floor 1: Ground Floor
│   ├── Room 101: Lobby
│   │   ├── OUTLET-001: Main Outlet [OK]
│   │   └── LIGHT-001: Entry Light [FAILED]
│   └── Room 102: Office
│       └── PANEL-001: Breaker Panel [OK]
└── Floor 2: Second Floor
    └── Room 201: Conference
        └── OUTLET-003: Wall Outlet [UNKNOWN]
```

**Role-Based Access Control**: Like Active Directory for buildings
- **Admin**: Full control over all buildings and equipment
- **Manager**: Manage assigned buildings
- **Technician**: Update equipment status, view coordinates
- **Viewer**: Read-only access

**PostGIS Spatial Database**: Professional-grade spatial operations
- WGS84 coordinate system (SRID 4326)
- Millimeter precision tracking
- Spatial queries (nearby, within bounds, on floor)
- Building origin and rotation support

## 🚀 Quick Start

### Prerequisites

ArxOS requires PostgreSQL with PostGIS extension:

```bash
# Using Docker (recommended)
docker run -d --name arxos-db \
  -e POSTGRES_DB=arxos \
  -e POSTGRES_USER=arxos \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  postgis/postgis:16-3.4

# Or install locally
sudo apt install postgresql postgis
```

### Installation

```bash
# Clone and build
git clone https://github.com/arx-os/arxos.git
cd arxos
go build -o arx ./cmd/arx

# Set environment variables
export POSTGIS_HOST=localhost
export POSTGIS_PORT=5432
export POSTGIS_DB=arxos
export POSTGIS_USER=arxos
export POSTGIS_PASSWORD=secret

# Initialize database
arx init
```

### Basic Usage

```bash
# Import building data
arx import building.bim.txt --building-id MAIN-OFFICE

# Query equipment
arx query --building MAIN-OFFICE --floor 1
arx query --building MAIN-OFFICE --status failed

# Export data
arx export MAIN-OFFICE --format bim > building.bim.txt
arx export MAIN-OFFICE --format json > building.json
arx export MAIN-OFFICE --format csv > equipment.csv
```

## 📁 Project Structure

```
arxos/
├── cmd/arx/                 # CLI application
├── internal/
│   ├── adapters/postgis/    # PostgreSQL/PostGIS adapter
│   ├── api/                 # REST API handlers
│   ├── core/                # Domain models
│   │   ├── building/       # Building entity
│   │   ├── equipment/      # Equipment entity
│   │   └── user/           # User entity
│   ├── services/            # Business logic
│   │   ├── import/         # Import service (IFC, CSV, JSON, BIM)
│   │   └── export/         # Export service
│   └── rendering/           # Tree renderer for .bim.txt
└── pkg/models/              # Shared models
```

## 🔧 Architecture

### Clean Architecture
- **Domain Layer**: Core business entities (Building, Equipment, User)
- **Repository Layer**: Data persistence interfaces
- **Service Layer**: Business logic and workflows
- **Adapter Layer**: PostgreSQL/PostGIS implementation
- **API Layer**: REST endpoints with authentication

### Database Schema
```sql
-- Buildings with GPS origin
buildings (
  id UUID PRIMARY KEY,
  arxos_id TEXT UNIQUE,
  name TEXT,
  address TEXT,
  origin GEOMETRY(Point, 4326),  -- WGS84 coordinates
  rotation FLOAT                  -- Building rotation from north
)

-- Equipment with 3D positions
equipment (
  id UUID PRIMARY KEY,
  building_id UUID REFERENCES buildings,
  path TEXT,                      -- Hierarchical path
  name TEXT,
  type TEXT,
  position GEOMETRY(PointZ, 4326), -- 3D WGS84 coordinates
  status TEXT,
  confidence SMALLINT              -- Position confidence level
)

-- Users with roles
users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  full_name TEXT,
  role TEXT,  -- admin, manager, technician, viewer
  status TEXT
)
```

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Secure password hashing (bcrypt)
- Session management with refresh tokens
- Organization-based multi-tenancy

## 📡 API

### Authentication
```http
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
POST /api/v1/auth/register
```

### Buildings
```http
GET    /api/v1/buildings
POST   /api/v1/buildings
GET    /api/v1/buildings/{id}
PUT    /api/v1/buildings/{id}
DELETE /api/v1/buildings/{id}
```

### Equipment
```http
GET    /api/v1/equipment?building_id={id}
POST   /api/v1/equipment
GET    /api/v1/equipment/{id}
PUT    /api/v1/equipment/{id}
DELETE /api/v1/equipment/{id}
```

### Spatial Queries
```http
GET /api/v1/spatial/nearby?lat={lat}&lon={lon}&radius={meters}
GET /api/v1/spatial/within?bounds={minLon,minLat,maxLon,maxLat}
GET /api/v1/spatial/floor?building={id}&floor={number}
```

## 🧪 Testing

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run integration tests (requires PostgreSQL)
POSTGIS_PASSWORD=secret go test -tags=integration ./...
```

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Development Guide](DEVELOPMENT_PLAN.md)
- [Contributing](CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

- Create an [Issue](https://github.com/arx-os/arxos/issues) for bug reports
- Start a [Discussion](https://github.com/arx-os/arxos/discussions) for questions
- Read the [Wiki](https://github.com/arx-os/arxos/wiki) for detailed guides