# ArxOS - Building Intelligence Platform

ArxOS is a comprehensive building management platform that combines traditional database-driven features with innovative Building-as-Code capabilities. Built with Go and HTMX, it offers enterprise-grade facility management with unique version control and portability features.

## 🚀 Platform Overview

ArxOS provides multiple ways to manage building infrastructure:

### 1. Building-as-Code Innovation
- **Text-Based BIM (.bim.txt)** - Human-readable building files
- **Universal Addressing** - Every equipment gets a hierarchical path
- **Git-Native** - Full version control with meaningful diffs
- **Portable** - Edit anywhere, sync everywhere

### 2. Enterprise Platform
- **PostgreSQL Database** - Fast queries and multi-user access
- **Web Interface** - HTMX-based UI for non-technical users
- **REST API** - Integration with existing systems
- **Mobile AR** - Augmented reality for field workers
- **Multi-Tenant SaaS** - Cloud-hosted subscription service

## Core Innovation: Universal Addressing

```bash
# Every piece of equipment has a universal address
ARXOS-NA-US-NY-NYC-0001/N/3/A/301/E/OUTLET_02
│                       │ │ │ │   │ └─ Equipment ID
│                       │ │ │ │   └─── Wall (East)
│                       │ │ │ └─────── Room 301
│                       │ │ └───────── Zone A (northwest)
│                       │ └─────────── Floor 3
│                       └───────────── Wing (North)
└───────────────────────────────────── Building UUID
```

## 🎯 Key Features

### For Developers
- **Plain Text Format** - Edit .bim.txt files with any editor
- **Git Workflows** - Branch, merge, diff building configurations
- **CLI Tools** - Powerful command-line interface
- **Scriptable** - Automate with bash, Python, etc.
- **API Access** - RESTful endpoints for integration

### For Facility Managers
- **Web Dashboard** - Visual building management
- **Real-time Status** - Equipment monitoring
- **Report Generation** - PDF, CSV exports
- **Mobile Access** - iOS/Android apps
- **Maintenance Scheduling** - Automated workflows

### For Enterprises
- **Multi-Building Support** - Manage entire portfolios
- **User Management** - Role-based access control
- **Audit Trails** - Complete change history
- **Integrations** - Connect with existing BMS/CMMS
- **White-Label Options** - Custom branding

## 📦 Installation

### Quick Start (Building-as-Code)
```bash
# Clone and build
git clone https://github.com/joelpate/arxos.git
cd arxos
go build -o bim ./cmd/bim

# Import a building
./bim import building.pdf > building.bim.txt

# Track with Git
git init
git add building.bim.txt
git commit -m "Initial building import"
```

### Full Platform Setup
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run migrations
./scripts/migrate.sh

# Start API server
go run ./cmd/arxos-server

# Access web interface
open http://localhost:8080
```

## 🔄 Hybrid Workflows

ArxOS seamlessly combines database and text-based approaches:

```bash
# Export from database to Building-as-Code
arx export building-123 --format bim > building.bim.txt

# Edit offline with vim
vim building.bim.txt

# Sync changes back to database
arx import building.bim.txt --update building-123

# Or use web interface for visual editing
open http://localhost:8080/buildings/123
```

## 🏗️ Architecture

```
arxos/
├── cmd/
│   ├── bim/              # Building-as-Code CLI
│   ├── arxos-server/     # API & Web server
│   ├── arxd/             # File watcher daemon
│   └── arx-legacy/       # Database CLI tools
├── internal/
│   ├── api/              # REST API handlers
│   ├── bim/              # BIM parser/writer
│   ├── database/         # PostgreSQL models
│   ├── importer/         # PDF/IFC importers
│   ├── web/              # HTMX interface
│   └── rendering/        # Visualization
├── docs/                 # Specifications
├── examples/             # Sample buildings
└── scripts/              # Utilities
```

## 📊 Use Cases

### Small Business
- Single building management
- Basic equipment tracking
- PDF import/export
- Git-based backups

### Enterprise
- Portfolio management
- API integrations
- Custom workflows
- Compliance reporting

### Developers
- Building-as-Code workflows
- CI/CD integration
- Automated testing
- Version control

## 🌐 API Examples

### Database Operations
```bash
# Get building info
curl http://localhost:8080/api/v1/buildings/123

# Update equipment status
curl -X PATCH http://localhost:8080/api/v1/equipment/456 \
  -d '{"status": "FAILED"}'

# Generate report
curl http://localhost:8080/api/v1/reports/maintenance?building=123
```

### Building-as-Code Operations
```bash
# Import BIM file
curl -X POST http://localhost:8080/api/v1/bim/import \
  -F "file=@building.bim.txt"

# Export to BIM format
curl http://localhost:8080/api/v1/buildings/123/export?format=bim

# Validate BIM file
curl -X POST http://localhost:8080/api/v1/bim/validate \
  -F "file=@building.bim.txt"
```

## 📱 Mobile AR Features

- **Equipment Scanning** - Point camera to identify equipment
- **Spatial Anchoring** - Persistent AR overlays
- **Offline Mode** - Sync when connected
- **Voice Commands** - Hands-free updates

## 💼 Business Model

### Open Source Core
- BIM text format specification
- Basic CLI tools
- File parsers/validators

### Commercial Platform
- Web interface
- Database backend
- API server
- Mobile apps
- Priority support
- Custom features

### SaaS Offering
- Cloud hosting
- Automatic backups
- Multi-tenant isolation
- Usage analytics
- Enterprise SSO

## 📖 Documentation

- [Architecture](ARCHITECTURE.md) - Technical decisions and data flow
- [Specifications](docs/SPECIFICATIONS.md) - UUID format, paths, BIM format

## 🚀 Next Steps

1. **Core**: Complete BIM tool (query/render commands)
2. **Integration**: Build sync between .bim.txt and SQLite
3. **API**: Connect database to Building-as-Code files
4. **Mobile**: Store AR anchors, start with simple 2D
5. **Scale**: Move to PostGIS when spatial queries needed

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Install dependencies
go mod download

# Run tests
go test ./...

# Start development server
air

# Run linter
golangci-lint run
```

## 📄 License

- **Core**: MIT License (open source)
- **Platform**: Commercial license
- **SaaS**: Subscription-based

See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **HTMX** - For simple, powerful web development
- **PostgreSQL** - Reliable database foundation
- **Go** - Fast, maintainable backend
- **pdfcpu** - PDF processing capabilities

---

**ArxOS** - Where Building Intelligence Meets Code

*Manage buildings with the power of both databases and version control*