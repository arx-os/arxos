# ArxOS: The Git of Buildings

[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ArxOS is the **next-generation Building Operating System** that treats buildings like code repositories. Just as Git revolutionized software development, ArxOS is revolutionizing building management by providing a universal platform for building data, control, and automation.

## 🌟 **The Vision: Buildings as Codebases**

ArxOS transforms buildings into version-controlled, queryable, and automatable systems:

```bash
# Traditional Building Management
- Static PDFs that become outdated immediately
- Siloed systems that don't communicate
- Manual processes for everything
- No version control for building changes

# ArxOS Building Management
arx query /B1/3/*/HVAC/* --status failed
arx set /B1/3/CONF-301/HVAC mode:presentation
arx workflow trigger emergency-shutdown --building B1
arx history /B1/3/A/301 --since "1 week ago"
```

## 🏗️ **Three-Tier Ecosystem Architecture**

### **Layer 1: ArxOS Core (FREE - Like Git)**
- **Pure Go/TinyGo codebase** - completely open source
- **Path-based architecture** - universal building addressing (`/B1/3/A/301/HVAC/UNIT-01`)
- **PostGIS spatial intelligence** - native location awareness with millimeter precision
- **CLI commands** - direct terminal control of building systems
- **Basic REST APIs** - core functionality for integrations
- **Version control** - Git-like tracking of all building changes

### **Layer 2: Hardware Platform (FREEMIUM - Like GitHub Free)**
- **Open source hardware designs** - community-driven IoT ecosystem
- **$3-15 sensors** - accessible building automation for everyone
- **Pure Go/TinyGo edge devices** - no C complexity, just Go everywhere
- **Gateway translation layer** - handles complex protocols (BACnet, Modbus)
- **ArxOS Certified Hardware Program** - partner ecosystem and marketplace

### **Layer 3: Workflow Automation (PAID - Like GitHub Pro)**
- **Visual workflow automation** - drag-and-drop building control via n8n
- **CMMS/CAFM features** - complete maintenance management system
- **Physical automation** - actual control of building systems
- **Enterprise integrations** - 400+ connectors to existing systems
- **Advanced analytics** - energy optimization, predictive maintenance, compliance

## 🎯 **Core Features**

### **BuildingOps Platform**: Three Ways to Control Your Building
- **CLI**: `arx set /B1/3/HVAC/DAMPER-01 position:50`
- **Natural Language**: `arx do "make conference room cooler"`
- **Visual Workflows**: Drag-and-drop n8n automation

### **Bidirectional Physical Control**: Not Just Monitoring, Actual Control
```
Path Command → Gateway → Hardware → Physical Action
/B1/3/LIGHTS/ZONE-A brightness:75 → ESP32 → PWM → Lights dim to 75%
/B1/3/DOORS/MAIN state:unlocked → ESP32 → Relay → Door unlocks
/B1/3/HVAC/DAMPER-01 position:50 → ESP32 → Servo → Damper opens 50%
```

### **Universal Path System**: Every Component Has an Address
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

### **Open Hardware Ecosystem**: Build Your Own Devices
- **TinyGo edge devices** ($3-15 ESP32/RP2040) - no C required
- **Pure Go gateways** (Raspberry Pi) - handles complex protocols
- **100% Go family** - single language from edge to cloud
- **Pre-built templates** for common sensors/actuators
- **ArxOS Certified Hardware** - partner ecosystem

### **Enterprise Workflow Automation**: Complete CMMS/CAFM Platform
- **Visual workflow builder** - drag-and-drop building automation
- **400+ integrations** - connect to any system
- **Physical automation** - actual control of building systems
- **Maintenance management** - work orders, PM schedules, asset lifecycle
- **Energy optimization** - predictive analytics and demand response

## 💰 **Business Model: Following Git's Success**

### **Why This Model Works**
Just as Git became the standard because it was free and powerful, ArxOS follows the same strategy:

1. **ArxOS Core (FREE)** - becomes the standard building management platform
2. **Hardware Platform (FREEMIUM)** - creates ecosystem and community
3. **Workflow Automation (PAID)** - monetizes the platform through enterprise features

### **Revenue Streams**
- **FREE**: Core ArxOS engine, CLI, basic APIs, open source hardware designs
- **FREEMIUM**: Certified hardware marketplace, community support
- **PAID**: Enterprise workflow automation, CMMS/CAFM features, professional support

### **Competitive Advantages**
- **80% cost reduction** vs traditional BAS systems
- **Pure Go/TinyGo** - unique technical advantage
- **Open hardware** - no vendor lock-in
- **Network effects** - more users → better platform → more users

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

### Ecosystem Documentation
- **[ArxOS Core](docs/ARCHITECTURE.md)** - The Git-like building management engine
- **[Hardware Platform](hardware.md)** - Open source IoT ecosystem and certified devices
- **[Workflow Automation](n8n.md)** - Visual CMMS/CAFM platform with n8n integration
- **[Business Model](docs/BUSINESS_MODEL.md)** - Ecosystem strategy and revenue model

### Technical Documentation
- **[API Reference](docs/api.md)** - REST API documentation
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Command-line interface guide
- **[Architecture Guide](docs/architecture-clean.md)** - Clean architecture principles
- **[Service Architecture](docs/SERVICE_ARCHITECTURE.md)** - Service layer design

### Development
- **[Contributing](CONTRIBUTING.md)** - How to contribute to ArxOS
- **[Developer Guide](docs/developer-guide/architecture.md)** - Development setup and practices

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

- Create an [Issue](https://github.com/arx-os/arxos/issues) for bug reports
- Start a [Discussion](https://github.com/arx-os/arxos/discussions) for questions
- Read the [Wiki](https://github.com/arx-os/arxos/wiki) for detailed guides