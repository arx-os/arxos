# Arxos SVG-BIM Integration System

A comprehensive SVG to BIM conversion and symbol management system with advanced validation, API services, and CLI tools.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arxos/arxos.git
   cd arxos/arx_svg_parser
   ```

2. **Set up the environment:**
   ```bash
   # Run the automated setup script
   python setup_env.py
   
   # Or manually:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Configure the environment:**
   ```bash
   # Copy and edit the environment file
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the application:**
   ```bash
   # Development mode
   uvicorn api.main:app --reload
   
   # Production mode
   python main.py
   ```

## 📋 Features

### Core Functionality
- **SVG to BIM Conversion**: Advanced conversion pipeline with symbol recognition
- **Symbol Management**: CRUD operations, bulk import/export, validation
- **JSON Schema Validation**: Comprehensive validation with detailed error reporting
- **REST API**: Full-featured API with authentication and role-based access
- **CLI Tools**: Command-line interface for symbol management
- **Background Processing**: Async job processing for bulk operations

### Advanced Features
- **Machine Learning Recognition**: AI-powered symbol recognition
- **Geometric Analysis**: Advanced geometric pattern matching
- **System-based Organization**: Automatic symbol categorization
- **Performance Optimization**: Caching, indexing, and optimization
- **Security**: JWT authentication, role-based access control
- **Monitoring**: Comprehensive logging and health checks

## 🏗️ Architecture

```
arx_svg_parser/
├── api/                    # FastAPI application and routers
├── services/              # Business logic and core services
├── models/                # Data models and schemas
├── utils/                 # Utilities and helpers
├── cmd/                   # CLI tools
├── tests/                 # Test suite
├── docs/                  # Documentation
└── scripts/              # Utility scripts
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_NAME=arx_svg_parser
DEBUG=false
ENVIRONMENT=development

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=sqlite:///./data/arx_svg_parser.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/arx_svg_parser.log
LOG_JSON=true

# Symbol Library
SYMBOL_LIBRARY_PATH=../arx-symbol-library
SYMBOL_CACHE_SIZE=1000
```

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Symbol Management
- `GET /symbols` - List symbols with filtering and pagination
- `POST /symbols` - Create new symbol
- `GET /symbols/{symbol_id}` - Get symbol details
- `PUT /symbols/{symbol_id}` - Update symbol
- `DELETE /symbols/{symbol_id}` - Delete symbol

#### Bulk Operations
- `POST /symbols/bulk-import` - Import symbols from file
- `POST /symbols/bulk-export` - Export symbols to file
- `GET /symbols/bulk-export/{job_id}/download` - Download export file
- `GET /symbols/bulk-export/{job_id}/progress` - Get export progress

#### Validation
- `GET /symbols/validate/{symbol_id}` - Validate single symbol
- `POST /symbols/validate-library` - Validate entire library
- `GET /symbols/validation-report` - Download validation report

#### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout

## 🛠️ CLI Tools

### Symbol Management CLI

```bash
# List symbols
arx-symbol-cli list

# Create symbol
arx-symbol-cli create --name "Fire Alarm" --system fire_alarm

# Update symbol
arx-symbol-cli update --id "fire_alarm_001" --name "Updated Fire Alarm"

# Delete symbol
arx-symbol-cli delete --id "fire_alarm_001"

# Bulk import
arx-symbol-cli bulk-import --file symbols.json

# Validate symbols
arx-symbol-cli validate --file symbols.json
```

### Validation CLI

```bash
# Validate single symbol
arx-validate-symbols --symbol fire_alarm_001

# Validate library
arx-validate-symbols --library ../arx-symbol-library

# Generate validation report
arx-validate-symbols --library ../arx-symbol-library --report
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/api/

# Run with coverage
pytest --cov=arx_svg_parser --cov-report=html

# Run performance tests
pytest tests/performance/ -m "slow"
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: REST API endpoint testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization testing

## 📊 Monitoring

### Logging

The system uses structured logging with JSON format:

```bash
# View logs
tail -f logs/arx_svg_parser.log

# Filter by level
grep '"level":"ERROR"' logs/arx_svg_parser.log
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed
```

### Metrics

```bash
# Application metrics
curl http://localhost:8000/metrics
```

## 🔒 Security

### Authentication

The system uses JWT-based authentication:

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/symbols
```

### Role-Based Access Control

- **Admin**: Full access to all operations
- **Manager**: Read/write access to symbols
- **Viewer**: Read-only access to symbols
- **Validator**: Access to validation operations

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t arx-svg-parser .

# Run container
docker run -p 8000:8000 arx-svg-parser
```

### Production Deployment

```bash
# Install production dependencies
pip install -e .[production]

# Start with Gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📈 Performance

### Optimization Features

- **Symbol Caching**: In-memory cache for frequently accessed symbols
- **Database Indexing**: Optimized database queries
- **Background Processing**: Async processing for bulk operations
- **Connection Pooling**: Efficient database connection management
- **Compression**: Gzip compression for API responses

### Performance Monitoring

```bash
# Monitor API performance
curl http://localhost:8000/metrics/performance

# Monitor cache hit rates
curl http://localhost:8000/metrics/cache
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style

```bash
# Format code
black arx_svg_parser/
isort arx_svg_parser/

# Lint code
flake8 arx_svg_parser/
mypy arx_svg_parser/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [User Guide](docs/USAGE_GUIDE.md)

### Issues
- [Bug Reports](https://github.com/arxos/arxos/issues)
- [Feature Requests](https://github.com/arxos/arxos/issues)

### Community
- [Discussions](https://github.com/arxos/arxos/discussions)
- [Wiki](https://github.com/arxos/arxos/wiki)

---

**Arxos SVG-BIM Integration System** - Transforming SVG to BIM with intelligence and precision.
