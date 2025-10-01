# ArxOS: The Git of Buildings

[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

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

## 🚀 Quick Start - The Unified Experience

### **The ArxOS Advantage: One Install = Complete Platform**

Unlike Git (CLI) and GitHub (web) being separate, **ArxOS owns everything**. One install gives you CLI + Web + Mobile + API access instantly.

### **Installation**

```bash
# Install ArxOS
brew install arxos
# OR: go install github.com/arx-os/arxos/cmd/arx@latest

# That's it! Now initialize your platform...
```

### **First-Time Setup**

```bash
$ arx init

╔═══════════════════════════════════════════════════════════╗
║              Welcome to ArxOS! 🏗️                         ║
╚═══════════════════════════════════════════════════════════╝

ArxOS can run locally OR sync with ArxOS Cloud for:
  • 🌐 Web dashboard - manage buildings from anywhere
  • 📱 Mobile app - AR equipment tracking in the field
  • 👥 Team collaboration - share access with your team
  • ☁️  Automatic backups - never lose data
  • 📊 Advanced analytics - energy optimization, insights

Choose your deployment mode:
  1. Cloud-First (recommended for teams)
  2. Hybrid (local database + cloud sync)
  3. Local-Only (no cloud, privacy-focused)
> 1

Create your FREE ArxOS Cloud account:
Email: you@company.com
Password: ********
Organization name: Acme Buildings Inc.
Choose subdomain: acme-buildings
  └─ Your web dashboard: https://acme-buildings.arxos.io

Initializing your platform...
✅ ArxOS Cloud account created
✅ Web dashboard provisioned at https://acme-buildings.arxos.io
✅ Local cache initialized (~/.arxos/)
✅ API access configured
✅ Sync enabled (every 5 minutes)
✅ Mobile app pairing ready

Mobile App Setup:
┌─────────────────┐
│  █████████████  │
│  ██ ▄▄▄▄▄ ██    │  1. Download ArxOS app
│  ██ █   █ ██    │  2. Scan this QR code
│  ██ █▄▄▄█ ██    │  3. Instant access!
└─────────────────┘

🎉 Your complete building management platform is ready!

Access your buildings via:
  • Terminal: arx query /B1/3/*/HVAC
  • Web: https://acme-buildings.arxos.io
  • Mobile: ArxOS app (iOS/Android)
  • API: https://api.arxos.io (auto-authenticated)

Next steps:
  • Import your first building: arx import building.ifc
  • Invite team members: arx team invite user@company.com
  • Explore features: arx help
```

### **Your First Building**

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

# Analytics and optimization
arx analytics energy data --building B1 --period 7d
arx analytics energy recommendations --building B1 --priority high
arx analytics forecast energy --building B1 --duration 24h

# IT asset management
arx it assets list --building B1
arx it rooms setup --room "/buildings/B1/floors/2/rooms/classroom-205" --type traditional
arx it workorders create --room "/buildings/B1/floors/2/rooms/classroom-205" --title "Install Projector"

# Facility management
arx facility workorders list --status open
arx facility maintenance schedule --asset HVAC-001 --frequency monthly
arx facility inspections create --building B1 --type safety

# Hardware management
arx hardware devices list --building B1
arx hardware certifications test device-001 --test-suite safety_basic
arx hardware protocols configure mqtt --host mqtt.arxos.com

# Workflow automation
arx workflow list
arx workflow execute energy-optimization --input '{"building_id": "B1"}'
arx workflow n8n test-connection

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
│   ├── analytics/           # Analytics engine (energy, predictive, performance)
│   ├── api/                 # REST API handlers
│   ├── auth/                # Authentication and authorization
│   ├── cache/               # Caching layer
│   ├── common/              # Shared utilities and logger
│   ├── config/              # Configuration management
│   ├── core/                # Domain models and business logic
│   ├── facility/            # CMMS/CAFM features
│   ├── hardware/            # Hardware platform and certification
│   ├── it/                  # IT asset management
│   ├── middleware/          # HTTP middleware
│   ├── services/            # Application services
│   ├── workflow/            # Workflow automation and n8n integration
│   └── ...                  # Other modules
├── pkg/models/              # Shared models
├── web/                     # Web interface
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

### System Architecture
- **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)** - Complete system overview and module integration
- **[API Reference](docs/API_REFERENCE.md)** - Comprehensive REST API documentation
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete command-line interface guide
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - External system integration and internal module communication
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment and monitoring

### Module Documentation
- **[Analytics Engine](internal/analytics/README.md)** - Energy optimization, predictive analytics, and reporting
- **[IT Asset Management](internal/it/README.md)** - IT infrastructure management and configuration
- **[Workflow Automation](internal/workflow/README.md)** - n8n integration and workflow management
- **[CMMS/CAFM Features](internal/facility/README.md)** - Facility and maintenance management
- **[Hardware Platform](internal/hardware/README.md)** - IoT device management and certification

### Development
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Complete development setup and best practices
- **[Development](CONTRIBUTING.md)** - Development guidelines for ArxOS
- **[Architecture Guide](docs/architecture-clean.md)** - Clean architecture principles
- **[Service Architecture](docs/SERVICE_ARCHITECTURE.md)** - Service layer design

### Business Documentation
- **[Business Model](docs/BUSINESS_MODEL.md)** - Ecosystem strategy and revenue model
- **[Hardware Platform](hardware.md)** - IoT ecosystem and certified devices
- **[Workflow Automation](n8n.md)** - Visual CMMS/CAFM platform with n8n integration

## 📄 License

Proprietary License - All rights reserved

## 🛠️ Development

For development guidelines and setup instructions, please read our [Development Guide](CONTRIBUTING.md).

## 📞 Support

- Contact support for bug reports and questions
- Read the [Wiki](https://github.com/arx-os/arxos/wiki) for detailed guides