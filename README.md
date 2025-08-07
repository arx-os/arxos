# Arxos Platform

A comprehensive infrastructure platform for building information modeling, featuring CAD-level precision, AI assistance, and cloud synchronization.

## 🚀 Quick Start with GitHub Codespaces

### Option 1: One-Click Setup (Recommended)
1. Click the green **"Code"** button above
2. Select the **"Codespaces"** tab
3. Click **"Create codespace on main"**
4. Wait for the environment to build (2-3 minutes)
5. Run `make dev` to start all services

### Option 2: Manual Setup
```bash
# Clone the repository
git clone https://github.com/[your-username]/arxos.git
cd arxos

# Start development environment
make dev
```

## 📋 Development Environment

The Arxos platform includes:

- **Go Backend** (Chi framework) - Core API and business logic
- **Python GUS Agent** - AI assistance and natural language processing
- **Browser CAD** - Web-based CAD interface with Canvas 2D
- **ArxIDE** - Desktop CAD IDE built with Tauri
- **PostgreSQL 17/PostGIS 3.5.3** - Spatial database for CAD/BIM data
- **Redis** - Caching and real-time features

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

- **Browser CAD**: http://localhost:3000
- **ArxIDE**: http://localhost:3001
- **Backend API**: http://localhost:8080
- **GUS Agent**: http://localhost:8000
- **PostgreSQL**: localhost:5432 (arxos_db_pg17)
- **Redis**: localhost:6379

## 🏗️ Architecture

### Core Components

- **SVGX Engine** - High-precision SVG processing with CAD capabilities
- **GUS Agent** - AI-powered assistance for design and compliance
- **Cloud Sync** - Real-time file synchronization across platforms
- **Design Marketplace** - Component library and collaboration platform

### Technology Stack

- **Backend**: Go with Chi framework
- **AI Services**: Python with FastAPI
- **Frontend**: HTML/HTMX/CSS/JS + Canvas 2D
- **Desktop**: Tauri (Rust + WebView)
- **Database**: PostgreSQL 17 with PostGIS 3.5.3
- **Cache**: Redis
- **Development**: Docker Compose

## 📚 Documentation

- **[Development Tracker](ARXOS_DEVELOPMENT_TRACKER.md)** - Single source of truth for development progress
- [Architecture Overview](docs/architecture/README.md)
- [Development Guide](docs/development/README.md)
- [User Guides](docs/user-guides/README.md)
- [API Reference](docs/api/README.md)

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
