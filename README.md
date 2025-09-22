# ArxOS - Building Information Management System

[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ArxOS is a next-generation Building Operating System (BuildingOps) that enables complete control of physical building systems through three unified interfaces: CLI commands, natural language, and visual workflows. It treats buildings like code repositories where every component has a path, and that path can control physical hardware - from sensors to actuators.

## 🎯 Core Features

**BuildingOps Platform**: Three ways to control your building
- **CLI**: `arx set /B1/3/HVAC/DAMPER-01 position:50`
- **Natural Language**: `arx do "make conference room cooler"`
- **Visual Workflows**: Drag-and-drop n8n automation

**Bidirectional Physical Control**: Not just monitoring, actual control
```
Path Command → Gateway → Hardware → Physical Action
/B1/3/LIGHTS/ZONE-A brightness:75 → ESP32 → PWM → Lights dim to 75%
/B1/3/DOORS/MAIN state:unlocked → ESP32 → Relay → Door unlocks
/B1/3/HVAC/DAMPER-01 position:50 → ESP32 → Servo → Damper opens 50%
```

**Hierarchical Path System**: Every component has an address
```
Building: Main Office
├── Floor 1: Ground Floor
│   ├── Room 101: Lobby
│   │   ├── SENSORS/TEMP-01 [72°F]
│   │   ├── LIGHTS/ZONE-A [ON: 75%]
│   │   └── HVAC/DAMPER-01 [POSITION: 50%]
│   └── Room 102: Office
│       ├── DOORS/MAIN [LOCKED]
│       └── ENERGY/METER-01 [15.2 kW]
└── Floor 2: Second Floor
    └── Room 201: Conference
        └── SCENES/presentation [READY]
```

**Open Hardware Integration**: Build your own devices
- TinyGo edge devices ($3-15 ESP32/RP2040)
- Pure Go gateways (Raspberry Pi)
- No C required - 100% Go family
- Pre-built templates for common sensors/actuators

**Workflow Automation (n8n)**: Visual building automation
- Drag-and-drop physical control
- Integrate with 400+ services
- CMMS/CAFM workflows included
- Real-time bidirectional control

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
# Query operations (read sensors, check status)
arx get /B1/3/SENSORS/TEMP-01
arx query /B1/*/SENSORS/* --above 75
arx watch /B1/3/ENERGY/* --interval 5s

# Control operations (actuate physical devices)
arx set /B1/3/LIGHTS/ZONE-A brightness:75
arx set /B1/3/HVAC/DAMPER-01 position:50
arx set /B1/*/LIGHTS/* state:off

# Natural language commands
arx do "turn off all lights on floor 3"
arx do "set conference room to presentation mode"
arx do "make it cooler in here"

# Scene control
arx scene /B1/3/CONF-301 presentation
arx scene /B1/* night-mode

# Workflow automation
arx workflow trigger emergency-shutdown
arx workflow run comfort-optimization

# Import/Export building data
arx import building.bim.txt --building-id B1
arx export B1 --format json > building.json
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

### Core Documentation
- [BuildingOps Platform](BUILDINGOPS.md) - Complete control interface guide
- [Hardware Integration](hardware.md) - Build your own IoT devices
- [n8n Workflow Automation](n8n.md) - Visual automation platform
- [API Documentation](docs/api.md) - REST API reference

### Development
- [Architecture Guide](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)
- [Development Guide](DEVELOPMENT_PLAN.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

- Create an [Issue](https://github.com/arx-os/arxos/issues) for bug reports
- Start a [Discussion](https://github.com/arx-os/arxos/discussions) for questions
- Read the [Wiki](https://github.com/arx-os/arxos/wiki) for detailed guides