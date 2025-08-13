# Arxos Platform

A clean, focused infrastructure platform for building information modeling, featuring CAD-level precision, AI assistance, and spatial data management.

> **🎯 Codebase recently cleaned (August 2024)** - Reduced by 70% for better maintainability and developer onboarding

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Go 1.21+
- Python 3.11+
- Node.js 18+ (for web frontend)

### Setup
```bash
# Clone the repository
git clone https://github.com/[your-username]/arxos.git
cd arxos

# Start development environment
make dev
```

## 📋 Core Architecture (Post-Cleanup)

The Arxos platform now focuses on essential components:

### Backend Services
- **`core/backend/`** - Go backend with Chi framework (main API)
- **`services/gus/`** - GUS AI agent for intelligent assistance
- **`services/iot/`** - IoT device integration and telemetry
- **`services/arxobject/`** - ArxObject spatial data service
- **`services/scale-engine/`** - Performance scaling service
- **`services/tile-server/`** - Spatial tile serving

### Frontend
- **`frontend/web/`** - Modern web interface (HTML/CSS/JS with Canvas 2D)

### Core Engine
- **ArxObject System** - Intelligent object-based architecture for SVG rendering and behavior

### Infrastructure
- **PostgreSQL 17/PostGIS 3.5.3** - Spatial database
- **Redis** - Caching and real-time features
- **Docker** - Containerized development environment

## 🛠️ Available Commands

```bash
# Development
make dev          # Start all services
make build        # Build all services
make test         # Run all tests
make clean        # Clean build artifacts

# Dependencies
make install      # Install all dependencies
make deps         # Install development tools

# Code Quality
make lint         # Run linting
make format       # Format code

# Docker
make docker-up    # Start Docker services
make docker-down  # Stop Docker services

# Database
make db-migrate   # Run migrations
make db-seed      # Seed database

# Health Check
make health       # Check service health
```

## 🌐 Service URLs

Once running, services are available at:

- **Web Interface**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **GUS Agent**: http://localhost:8000
- **PostgreSQL**: localhost:5432 (arxos_db_pg17)
- **Redis**: localhost:6379

## 🏗️ Simplified Architecture

### What We Kept (Essential Components)
- **ArxObject System** - Intelligent object-based SVG processing with CAD capabilities
- **GUS Agent** - AI-powered assistance for design and compliance  
- **Web Interface** - Primary user interface for CAD operations
- **IoT Integration** - Device telemetry and real-time data
- **Spatial Database** - PostGIS-powered spatial data management

### What We Removed (70% reduction)
- ❌ Desktop applications (ArxIDE)
- ❌ Mobile frontends (iOS/Android)
- ❌ Unused services (CMMS, construction, partners, etc.)
- ❌ Example/demo code
- ❌ Excessive documentation
- ❌ SDK generation tools

### Technology Stack
- **Backend**: Go with Chi framework
- **AI Services**: Python with FastAPI
- **Frontend**: Modern HTML/CSS/JS with Canvas 2D
- **Database**: PostgreSQL 17 with PostGIS 3.5.3
- **Cache**: Redis
- **Development**: Docker Compose

## 📚 Documentation

- [Architecture Overview](docs/architecture/README.md)
- [API Reference](docs/api/README.md)
- [User Guides](docs/user-guides/README.md)
- [Database Documentation](docs/database/README.md)

### Cleanup Information
- **[Cleanup Preview](CLEANUP_PREVIEW.md)** - What was removed and why
- **Backup Location**: `../arxos_cleanup_backup_YYYYMMDD_HHMMSS/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/[your-username]/arxos/issues)
- **Discussions**: [GitHub Discussions](https://github.com/[your-username]/arxos/discussions)

---

**Note**: This platform is designed for development and prototyping. Production deployment requires additional security and performance considerations.
