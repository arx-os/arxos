# Arxos - End-to-End Infrastructure Platform

Arxos is a comprehensive infrastructure platform that treats each building as a version-controlled repository containing SVG-BIM files, ASCII-BIM representations, structured object metadata, and audit logs. The system integrates mobile AR, CLI tools, and a logic engine to simulate infrastructure behavior.

## 🏗️ Architecture Overview

```
arxos/
├── core/                    # Core platform services
│   ├── svg-parser/         # SVG/BIM processing engine
│   ├── backend/            # Go backend services
│   └── common/             # Shared utilities and models
├── frontend/               # User interfaces
│   ├── web/               # Web-based UI
│   ├── ios/               # iOS mobile app
│   └── android/           # Android mobile app
├── services/               # Specialized microservices
│   ├── ai/                # AI and ML services
│   ├── iot/               # Building automation & IoT
│   ├── cmms/              # Maintenance management
│   └── data-vendor/       # Data vendor integrations
├── infrastructure/         # DevOps and infrastructure
│   ├── deploy/            # Deployment configurations
│   ├── database/          # Database schemas and migrations
│   └── monitoring/        # Monitoring and observability
├── tools/                  # Development and operational tools
│   ├── cli/               # Command-line interface
│   ├── symbols/           # Symbol library and definitions
│   └── docs/              # Documentation and guides
└── examples/              # Example implementations and demos
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Go 1.19+
- Node.js 16+
- Docker
- PostgreSQL with PostGIS

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/capstanistan/arxos.git
   cd arxos
   ```

2. **Set up core services**
   ```bash
   # Core SVG parser
   cd core/svg-parser
   pip install -r requirements.txt
   
   # Backend services
   cd ../backend
   go mod download
   ```

3. **Start development environment**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Or start individual services
   make start-core
   make start-frontend
   make start-services
   ```

## 📁 Repository Structure

### Core Platform (`core/`)
- **`svg-parser/`**: Main SVG/BIM processing engine with FastAPI
- **`backend/`**: High-performance Go backend services
- **`common/`**: Shared utilities, models, and configurations

### Frontend Applications (`frontend/`)
- **`web/`**: HTMX-based web interface for viewing and markup
- **`ios/`**: Native iOS app with AR capabilities
- **`android/`**: Android mobile application

### Specialized Services (`services/`)
- **`ai/`**: Machine learning and AI services
- **`iot/`**: Building automation and IoT platform
- **`cmms/`**: Computerized maintenance management
- **`data-vendor/`**: Third-party data integrations

### Infrastructure (`infrastructure/`)
- **`deploy/`**: Deployment configurations and scripts
- **`database/`**: Database schemas, migrations, and data management
- **`monitoring/`**: Observability, logging, and alerting

### Development Tools (`tools/`)
- **`cli/`**: Command-line interface tools
- **`symbols/`**: Symbol library and BIM definitions
- **`docs/`**: Comprehensive documentation

## 🔧 Development Workflow

### Adding New Features
1. Create feature branch from `main`
2. Implement changes in appropriate module
3. Update shared dependencies in `core/common/`
4. Add tests and documentation
5. Submit pull request

### Testing
```bash
# Run all tests
make test

# Run specific module tests
make test-core
make test-frontend
make test-services
```

### Building and Deployment
```bash
# Build all components
make build

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-production
```

## Development Setup for svgx_engine

To ensure robust imports and a stable development environment, follow these steps:

1. **Install in Editable Mode:**
   ```sh
   pip install -e ./arxos/svgx_engine
   ```
   This allows you to make changes to the code and have them reflected immediately.

2. **Run Tests from Project Root:**
   Always run tests and scripts from the project root (where `pyproject.toml` is located) to ensure `svgx_engine` is recognized as a top-level package.
   ```sh
   cd /path/to/arxos
   python -m svgx_engine.test_simple_imports
   python -m svgx_engine.test_migrated_services
   ```

3. **Import Policy:**
   - All imports within `svgx_engine` should use absolute imports (e.g., `from svgx_engine.models...`).
   - Avoid relative imports to ensure compatibility with both development and production environments.
   - If you encounter import errors, check your working directory and ensure you are running from the project root.

4. **Troubleshooting:**
   - If you see `ModuleNotFoundError: No module named 'svgx_engine'`, ensure you are running from the project root and have installed the package in editable mode.
   - For further help, see `DEVELOPMENT.md` (if available) or contact the maintainers.

## Directory Structure Notes

- `svgx_engine/cache/`: Internal cache for SVGX Engine (temporary, not versioned)
- `svgx_symbols/`: Shared symbol library for all Arxos modules (versioned, shared resource)

## 🏛️ System Architecture

### Core Concepts
- **The Hub**: Each building is a repository with SVGs, logs, metadata, and structured data
- **SVG-BIM**: Floor layers with toggleable MEP systems and smart symbols
- **ASCII-BIM**: Lightweight text-based representations for CLI use
- **AR Layer**: iOS app aligns AR overlays to SVG coordinates
- **Object Schema**: SystemCode_ObjectType_Instance naming with JSON structure

### Technology Stack
- **Backend**: Go (Chi framework)
- **Frontend**: HTML/X + Tailwind CSS (HTMX)
- **Database**: PostgreSQL with PostGIS
- **Logic Services**: Python microservices
- **Cloud**: DigitalOcean + Azure
- **Mobile**: iOS (Swift + ARKit + LiDAR)
- **CLI**: Go-based ArxOS with `arx` command suite

## 📊 System Codes
- **E**: Electrical (purple)
- **LV**: Low Voltage (orange)
- **FA**: Fire Alarm (pink)
- **N**: Network/Data (yellow)
- **M**: Mechanical (green)
- **P**: Plumbing (blue/red)
- **S**: Structural (black)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

[License information to be added]

## 🆘 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/capstanistan/arxos/issues)
- Discussions: [GitHub Discussions](https://github.com/capstanistan/arxos/discussions) 