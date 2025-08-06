# Arxos Platform

End-to-end infrastructure platform for buildings, providing comprehensive building information modeling, IoT integration, and intelligent automation.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (3.13 recommended)
- PostgreSQL 12+
- Redis 6+
- Docker (optional)

### Installation

#### Option 1: Modern Development Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/arxos/arxos.git
cd arxos

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"
```

#### Option 2: Production Setup
```bash
# Install production dependencies only
pip install -e .

# Or use requirements.txt for Docker deployments
pip install -r requirements.txt
```

#### Option 3: Development Tools Only
```bash
# Install development tools separately
pip install -r requirements-dev.txt
```

### Running the Application

```bash
# Start the API server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run with coverage
pytest --cov=application --cov=api --cov=domain --cov=infrastructure
```

## 📁 Project Structure

```
arxos/
├── application/           # Application layer (Clean Architecture)
│   ├── config/          # Configuration management
│   ├── services/        # Business services
│   ├── use_cases/       # Business use cases
│   └── dto/            # Data transfer objects
├── api/                 # API layer (FastAPI)
│   ├── routes/         # API routes
│   └── middleware/     # API middleware
├── domain/             # Domain layer (Core business logic)
├── infrastructure/     # Infrastructure layer
│   ├── database/      # Database models and migrations
│   ├── repositories/  # Data access layer
│   └── services/      # External service integrations
├── services/           # External microservices
│   ├── ai/           # AI/ML services
│   ├── mcp/          # MCP-Engineering services
│   └── iot/          # IoT services
└── tests/             # Test suite
```

## 🛠️ Development

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Type checking
mypy .

# Security scanning
bandit -r .
safety check
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m slow

# Run with coverage
pytest --cov=application --cov=api --cov=domain --cov=infrastructure
```

## 🐳 Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Build production image
docker build -t arxos:latest .
```

## 📊 Monitoring

The platform includes comprehensive monitoring:
- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus metrics
- **Logging**: Structured logging with structlog
- **Tracing**: Distributed tracing support

## 🔧 Configuration

Configuration is managed through:
- **Environment Variables**: `.env` files
- **YAML Files**: `application/config/` directory
- **Pydantic Settings**: Type-safe configuration

## 📚 Documentation

- [API Documentation](docs/api/)
- [Architecture Guide](docs/architecture/)
- [Development Guide](docs/developer/)
- [User Guides](docs/user-guides/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/arxos/arxos/issues)
- **Documentation**: [docs.arxos.com](https://docs.arxos.com)
- **Discord**: [Arxos Community](https://discord.gg/arxos) 