# ArxOS: The Git of Buildings

[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]

ArxOS is the **next-generation Building Operating System** that treats buildings like code repositories. Just as Git revolutionized software development, ArxOS is revolutionizing building management by providing a universal platform for building data, control, and automation.

## 🌟 **The Vision: Buildings as Codebases**

ArxOS transforms buildings into version-controlled, queryable, and automatable systems with a **unified platform experience**:

```bash
# Traditional Building Management
- Static PDFs that become outdated immediately
- Siloed systems that don't communicate
- Manual processes for everything
- No version control for building changes
- Separate tools for CLI, web, mobile

# ArxOS Building Management - ONE Install, EVERYTHING Connected
$ brew install arxos && arx init
✅ CLI installed
✅ Web dashboard provisioned at https://your-org.arxos.io
✅ Mobile app ready (scan QR to pair)
✅ API access configured

$ arx query /B1/3/*/HVAC/* --status failed
✅ Results in terminal
✅ Instantly visible on web dashboard
✅ Mobile app notification sent

$ arx set /B1/3/CONF-301/HVAC mode:presentation
✅ Equipment controlled
✅ Change synced to cloud
✅ Visible everywhere: CLI, Web, Mobile, API
```

### **🚀 The Game-Changing Difference**

Unlike Git (CLI) ≠ GitHub (web), ArxOS gives you **everything in one install**:

| What You Get | Traditional Tools | ArxOS |
|--------------|-------------------|-------|
| **CLI Tool** | ✅ Separate install | ✅ One install |
| **Web Dashboard** | ❌ Separate sign-up | ✅ Auto-provisioned |
| **Mobile App** | ❌ Separate app | ✅ Auto-paired |
| **Cloud Sync** | ❌ Manual setup | ✅ Automatic |
| **Team Access** | ❌ Manual invites | ✅ One command |
| **API Keys** | ❌ Generate manually | ✅ Auto-configured |

**Result**: Install once, access everywhere. Work in terminal, see updates on web. Add equipment on mobile, query in CLI. **Seamless.**

## 🏗️ **Three-Tier Ecosystem Architecture**

### **Layer 1: ArxOS Core (FREE - Like Git)**
- **Pure Go/TinyGo codebase** - modern, efficient architecture
- **Path-based architecture** - universal building addressing (`/B1/3/A/301/HVAC/UNIT-01`)
- **PostGIS spatial intelligence** - native location awareness with millimeter precision
- **CLI commands** - direct terminal control of building systems
- **Basic REST APIs** - core functionality for integrations
- **Version control** - Git-like tracking of all building changes

### **Layer 2: Hardware Platform (FREEMIUM - Like GitHub Free)**
- **Hardware designs** - comprehensive IoT ecosystem
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

### **Advanced Analytics Engine**: Intelligent Building Optimization
- **Energy Optimization**: Real-time energy consumption analysis and optimization recommendations
- **Predictive Analytics**: Machine learning models for forecasting and trend analysis
- **Performance Monitoring**: KPI tracking and threshold-based alerting
- **Anomaly Detection**: Statistical analysis for identifying unusual patterns
- **Report Generation**: Multi-format reports with templates and scheduling

### **IT Asset Management**: Complete IT Infrastructure Control
- **Asset Lifecycle Management**: From procurement to disposal with full tracking
- **Configuration Management**: Template-based hardware/software configurations
- **Room Setup Management**: Room-specific IT equipment layouts and connections
- **Inventory Management**: Parts and supplies tracking with supplier integration
- **Work Order Management**: IT work order creation, tracking, and resolution

### **CMMS/CAFM Features**: Complete Facility Management
- **Facility Management**: Building, space, and asset management
- **Work Order Management**: Maintenance work order lifecycle
- **Maintenance Scheduling**: Preventive and reactive maintenance planning
- **Inspection Management**: Inspection workflows and compliance tracking
- **Vendor Management**: External service provider and contract management

### **Open Hardware Ecosystem**: Build Your Own Devices
- **TinyGo edge devices** ($3-15 ESP32/RP2040) - no C required
- **Pure Go gateways** (Raspberry Pi) - handles complex protocols
- **100% Go family** - single language from edge to cloud
- **Pre-built templates** for common sensors/actuators
- **ArxOS Certified Hardware** - partner ecosystem with testing framework

### **Enterprise Workflow Automation**: Complete CMMS/CAFM Platform
- **Visual workflow builder** - drag-and-drop building automation
- **n8n Integration** - seamless integration with n8n workflow automation platform
- **400+ integrations** - connect to any system
- **Physical automation** - actual control of building systems
- **Maintenance management** - work orders, PM schedules, asset lifecycle
- **Energy optimization** - predictive analytics and demand response

## 💰 **Business Model: Following Git's Success**

### **Why This Model Works**
Just as Git became the standard because it was free and powerful, ArxOS follows the same strategy:

1. **ArxOS Core (FREE)** - becomes the standard building management platform
2. **Hardware Platform (FREEMIUM)** - creates ecosystem and partnerships
3. **Workflow Automation (PAID)** - monetizes the platform through enterprise features

### **Revenue Streams**
- **FREE**: Core ArxOS engine, CLI, basic APIs, hardware designs
- **FREEMIUM**: Certified hardware marketplace, partner support
- **PAID**: Enterprise workflow automation, CMMS/CAFM features, professional support

### **Competitive Advantages**
- **80% cost reduction** vs traditional BAS systems
- **Pure Go/TinyGo** - unique technical advantage
- **Open architecture** - no vendor lock-in
- **Network effects** - more users → better platform → more users

## 🚀 Quick Start

### **⚠️ Current Status: Active Development - Not Production Ready**

**Completion: 60-70%**

ArxOS has excellent architecture and solid foundations, but integration work remains. Many CLI commands and API endpoints need wiring to use cases. See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for brutally honest assessment of what works vs what's placeholder code.

**What Works:**
- ✅ Database schema (107 tables, spatial intelligence)
- ✅ Auth/JWT system
- ✅ BAS CSV import (fully functional)
- ✅ Git-like version control (branches, commits, PRs)
- ✅ Equipment topology with graph queries
- ✅ Basic building/equipment CRUD

**What Needs Work:**
- ⚠️ CLI commands (some show fake data)
- ⚠️ IFC import (metadata only, not full conversion)
- ⚠️ HTTP API (40% coverage, workflow endpoints missing)
- ⚠️ Test coverage (~15%)
- ⚠️ Mobile app (placeholder implementations)

**See [`docs/WIRING_PLAN.md`](docs/WIRING_PLAN.md) for systematic completion plan.**

### **Installation (Development)**

```bash
# Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Install dependencies
go mod download

# Setup database
./scripts/setup-dev-database.sh

# Run migrations
go run cmd/arx/main.go migrate up

# Build
make build
```

### **Development Setup**

```bash
# After installation, verify setup
$ go run cmd/arx/main.go health

Expected output:
✓ Database: Connected
✓ PostGIS: Available
✓ Cache: Ready
✓ System: Operational

# Check migration status
$ go run cmd/arx/main.go migrate status

# Try real working commands
$ go run cmd/arx/main.go building create --name "Test School" --address "123 Main St"
$ go run cmd/arx/main.go branch list --repo <repo-id>
$ go run cmd/arx/main.go bas import points.csv --building <building-id>
```

**⚠️ Note:** Some CLI commands show placeholder data. See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for command-by-command status and [`docs/WIRING_PLAN.md`](docs/WIRING_PLAN.md) for completion plan.

### **Your First Building**

```bash
# Query operations (read sensors, check status)
arx get /B1/3/SENSORS/TEMP-01
arx query /B1/*/SENSORS/* --above 75
arx watch /B1/3/ENERGY/* --interval 5s

# Component management
arx component add --path /B1/3/LIGHTS/ZONE-A --type light --name "Zone A Lights"
arx component update /B1/3/LIGHTS/ZONE-A --status on --brightness 75
arx component remove /B1/3/LIGHTS/ZONE-A

# Building repository operations
arx repo init --name "Main Campus"
arx repo status
arx repo commit --message "Added new HVAC system"

# Data conversion and import
arx convert ifc-to-bim /path/to/building.ifc
arx import /path/to/building.bim.txt --building-id B1
arx export B1 --format json > building.json

# System management
arx health
arx version
arx serve --port 8080

# Database operations
arx migrate up
arx migrate down
arx migrate status

# Reporting and visualization
arx report energy --building B1 --period 7d
arx visualize /B1/3 --format svg > floor_plan.svg

# Component tracing
arx trace /B1/3/HVAC/UNIT-01 --upstream
arx trace /B1/3/LIGHTS/ZONE-A --downstream

# Watch for changes
arx watch /B1/3/SENSORS/* --interval 5s
```

## 📁 Project Structure

```
arxos/
├── cmd/arx/                 # CLI application
├── internal/
│   ├── domain/              # Domain models and business logic
│   ├── infrastructure/      # Infrastructure layer (PostGIS, cache, etc.)
│   │   ├── postgis/         # PostgreSQL/PostGIS adapter
│   │   ├── cache/           # Caching layer
│   │   └── services/        # Infrastructure services
│   ├── interfaces/          # Interface layer
│   │   ├── http/            # REST API handlers
│   │   ├── graphql/         # GraphQL API
│   │   ├── websocket/       # WebSocket handlers
│   │   └── tui/             # Terminal UI
│   ├── usecase/             # Use case layer
│   ├── config/              # Configuration management
│   └── migrations/          # Database migrations
├── pkg/                     # Shared packages
│   ├── auth/                # Authentication and authorization
│   ├── models/              # Shared models
│   ├── errors/              # Error handling
│   └── validation/          # Validation utilities
├── mobile/                  # React Native mobile app
├── services/                # External microservices
│   └── ifcopenshell-service/ # IFC processing service
├── docs/                    # Comprehensive documentation
└── scripts/                 # Build and deployment scripts
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
-- Organizations for multi-tenancy
organizations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Users with organization-based access
users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT,
  organization_id TEXT,
  role TEXT NOT NULL DEFAULT 'user',
  is_active BOOLEAN DEFAULT true,
  last_login TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id)
)

-- Buildings with location data
buildings (
  id TEXT PRIMARY KEY,
  arxos_id TEXT UNIQUE NOT NULL,  -- e.g., ARXOS-NA-US-NY-NYC-0001
  name TEXT NOT NULL,
  address TEXT,
  city TEXT,
  state TEXT,
  country TEXT,
  postal_code TEXT,
  latitude REAL,
  longitude REAL,
  organization_id TEXT,
  total_area REAL,
  floors_count INTEGER,
  year_built INTEGER,
  building_type TEXT,
  status TEXT DEFAULT 'OPERATIONAL',
  metadata JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (organization_id) REFERENCES organizations(id)
)

-- Floors within buildings
floors (
  id TEXT PRIMARY KEY,
  building_id TEXT NOT NULL,
  level INTEGER NOT NULL,
  name TEXT NOT NULL,
  area REAL,
  height REAL,
  floor_type TEXT,
  status TEXT DEFAULT 'OPERATIONAL',
  metadata JSON,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
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
make test

# Run tests with coverage
make test-coverage

# Run integration tests (requires PostgreSQL)
make test-integration

# Run specific module tests
go test ./internal/domain/...
```

## 📚 Documentation

### System Architecture
- **[Service Architecture](docs/architecture/SERVICE_ARCHITECTURE.md)** - Complete system overview and module integration
- **[API Documentation](docs/api/API_DOCUMENTATION.md)** - Comprehensive REST API documentation
- **[Integration Flow](docs/integration/INTEGRATION_FLOW.md)** - External system integration and internal module communication
- **[Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md)** - Production deployment and monitoring

### Module Documentation
- **[CLI Integration](docs/integration/CLI_INTEGRATION.md)** - Command-line interface integration
- **[IFC Integration](docs/integration/IFCOPENSHELL_INTEGRATION.md)** - IFC file processing integration
- **[CADTUI Workflow](docs/architecture/CADTUI_VISUAL_CONTEXT.md)** - Computer-Aided Design Terminal UI

### Development
- **[Quick Start](QUICKSTART.md)** - Complete development setup and first steps
- **[Development Guide](mobile/DEVELOPMENT_GUIDE.md)** - Mobile development guidelines
- **[Technical Specifications](mobile/TECHNICAL_SPECIFICATIONS.md)** - Technical implementation details
- **[Implementation Plan](mobile/IMPLEMENTATION_PLAN.md)** - Development roadmap

### Business Documentation
- **[Automation Examples](docs/automation/AUTOMATION_EXAMPLE.md)** - Workflow automation examples
- **[Intelligent Automation](docs/automation/INTELLIGENT_AUTOMATION.md)** - AI-powered automation features

## 📄 License

Proprietary License - All rights reserved

## 🛠️ Development

For development guidelines and setup instructions, please read our [Quick Start Guide](QUICKSTART.md).

## 📞 Support

- Contact support for bug reports and questions
- Read the [Wiki](https://github.com/arx-os/arxos/wiki) for detailed guides# Trigger fresh CI run after formatting fixes
