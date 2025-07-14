# Arx SVG Parser - Developer Onboarding

## 🚀 **Quick Start**

Welcome to the Arx SVG Parser! This is the Python service that handles SVG to BIM conversion, symbol management, and validation for the Arxos platform.

### **Prerequisites**
- **Python**: 3.11+ (required)
- **Git**: Latest version
- **PostgreSQL**: 15+ with PostGIS extension
- **Redis**: 6+ (for caching and Celery)
- **Docker**: 20.10+ (optional, for containerized development)

### **1. Clone and Setup**
```bash
# Clone the repository (if not already done)
git clone https://github.com/arxos/arxos.git
cd arxos/arx_svg_parser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
# See Environment Variables section below
```

### **3. Database Setup**
```bash
# Start PostgreSQL (if using Docker)
docker run -d \
  --name arx-postgres \
  -e POSTGRES_DB=arxos_svg_db \
  -e POSTGRES_USER=arxos \
  -e POSTGRES_PASSWORD=arxos_password \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# Run migrations
alembic upgrade head
```

### **4. Verify Setup**
```bash
# Run tests
pytest

# Start development server
uvicorn arx_svg_parser.main:app --reload
```

---

## 🔧 **Environment Variables**

Create a `.env` file based on `env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://arxos:arxos_password@localhost:5432/arxos_svg_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=arxos_svg_db
DATABASE_USER=arxos
DATABASE_PASSWORD=arxos_password

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Configuration
SERVER_PORT=8082
SERVER_HOST=0.0.0.0
ENVIRONMENT=development
LOG_LEVEL=debug

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRY=24h
BCRYPT_COST=12

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOWED_HEADERS=Content-Type,Authorization

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC

# File Upload Configuration
UPLOAD_MAX_SIZE=10MB
UPLOAD_PATH=./uploads
UPLOAD_ALLOWED_TYPES=image/svg+xml,application/svg+xml

# Validation Configuration
VALIDATION_STRICT_MODE=true
VALIDATION_MAX_FILE_SIZE=5MB
VALIDATION_ALLOWED_SVG_TAGS=path,rect,circle,ellipse,line,polyline,polygon,text,g,defs,use

# Symbol Management
SYMBOL_CATALOG_PATH=./data/symbols
SYMBOL_CACHE_ENABLED=true
SYMBOL_CACHE_TTL=3600

# AI/ML Configuration
ML_MODEL_PATH=./models
ML_ENABLED=true
ML_CONFIDENCE_THRESHOLD=0.8

# External Services
ARX_BACKEND_URL=http://localhost:8080
CMMS_SERVICE_URL=http://localhost:8081
```

---

## 🛠️ **Development Commands**

### **Build and Run**
```bash
# Install in development mode
pip install -e .

# Run the FastAPI server
uvicorn arx_svg_parser.main:app --reload --host 0.0.0.0 --port 8082

# Run with production server
gunicorn arx_svg_parser.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Run Celery worker
celery -A arx_svg_parser.celery_app worker --loglevel=info

# Run Celery beat (for scheduled tasks)
celery -A arx_svg_parser.celery_app beat --loglevel=info
```

### **Testing**
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=arx_svg_parser --cov-report=html

# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_parsers.py::test_svg_parser

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/benchmark/

# Run linting
black arx_svg_parser/
isort arx_svg_parser/
flake8 arx_svg_parser/
mypy arx_svg_parser/
```

### **Database Operations**
```bash
# Run migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "description"

# Seed database
python scripts/seed_database.py

# Reset database
alembic downgrade base
alembic upgrade head
```

### **Code Quality**
```bash
# Format code
black arx_svg_parser/
isort arx_svg_parser/

# Lint code
flake8 arx_svg_parser/
mypy arx_svg_parser/

# Security check
bandit -r arx_svg_parser/
safety check

# Type checking
mypy arx_svg_parser/
```

---

## 🏗️ **Project Structure**

```
arx_svg_parser/
├── arx_svg_parser/           # Main package
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── config.py             # Configuration management
│   ├── api/                  # API routes
│   │   ├── __init__.py
│   │   ├── v1/              # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── parsers.py   # Parser endpoints
│   │   │   ├── symbols.py   # Symbol endpoints
│   │   │   └── validation.py # Validation endpoints
│   │   └── dependencies.py  # API dependencies
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── parsers.py       # SVG parsing logic
│   │   ├── validators.py    # Validation logic
│   │   ├── converters.py    # BIM conversion logic
│   │   └── models.py        # Data models
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   ├── parser_service.py
│   │   ├── symbol_service.py
│   │   └── validation_service.py
│   ├── models/               # Database models
│   │   ├── __init__.py
│   │   ├── symbol.py        # Symbol model
│   │   ├── parser_result.py # Parser result model
│   │   └── validation.py    # Validation model
│   ├── schemas/              # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── requests.py      # Request schemas
│   │   ├── responses.py     # Response schemas
│   │   └── validation.py    # Validation schemas
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   ├── file_utils.py    # File handling
│   │   ├── svg_utils.py     # SVG utilities
│   │   └── validation.py    # Validation utilities
│   ├── tasks/                # Celery tasks
│   │   ├── __init__.py
│   │   ├── parsing.py       # Parsing tasks
│   │   └── validation.py    # Validation tasks
│   └── celery_app.py        # Celery configuration
├── tests/                    # Test files
│   ├── __init__.py
│   ├── conftest.py          # Test configuration
│   ├── unit/                # Unit tests
│   │   ├── test_parsers.py
│   │   ├── test_validators.py
│   │   └── test_converters.py
│   ├── integration/         # Integration tests
│   │   ├── test_api.py
│   │   └── test_database.py
│   └── fixtures/            # Test fixtures
│       ├── sample_svgs/
│       └── expected_results/
├── migrations/               # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── data/                     # Data files
│   ├── symbols/             # Symbol catalog
│   ├── schemas/             # JSON schemas
│   └── models/              # ML models
├── scripts/                  # Utility scripts
│   ├── seed_database.py
│   ├── validate_symbols.py
│   └── benchmark_parser.py
├── docs/                     # Documentation
│   ├── api.md
│   ├── parsers.md
│   └── validation.md
├── pyproject.toml           # Project configuration
├── requirements.txt          # Dependencies
├── requirements-dev.txt      # Development dependencies
├── env.example              # Environment template
├── .gitignore               # Git ignore rules
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── alembic.ini             # Alembic configuration
└── README.md               # Project documentation
```

---

## 🧪 **Testing**

### **Test Structure**
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/

# Performance tests
pytest tests/benchmark/

# All tests with coverage
pytest --cov=arx_svg_parser --cov-report=html --cov-report=term
```

### **Test Database**
```bash
# Set up test database
createdb arxos_svg_test

# Run tests with test database
DATABASE_URL=postgresql://localhost:5432/arxos_svg_test pytest
```

### **Test Coverage**
```bash
# Generate coverage report
pytest --cov=arx_svg_parser --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### **Test Fixtures**
```bash
# Create test fixtures
python scripts/create_test_fixtures.py

# Validate test fixtures
python scripts/validate_fixtures.py
```

---

## 🐳 **Docker Development**

### **Using Docker Compose**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f arx-svg-parser

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### **Docker Compose Configuration**
```yaml
# docker-compose.yml
version: '3.8'
services:
  arx-svg-parser:
    build: .
    ports:
      - "8082:8082"
    environment:
      - DATABASE_URL=postgresql://arxos:arxos_password@postgres:5432/arxos_svg_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=arxos_svg_db
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=arxos_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery-worker:
    build: .
    command: celery -A arx_svg_parser.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://arxos:arxos_password@postgres:5432/arxos_svg_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

---

## 🔍 **Debugging**

### **Logging**
```bash
# Set log level
export LOG_LEVEL=debug

# View structured logs
uvicorn arx_svg_parser.main:app --reload --log-level debug
```

### **Profiling**
```bash
# CPU profiling
python -m cProfile -o profile.stats scripts/benchmark_parser.py

# Memory profiling
python -m memory_profiler scripts/benchmark_parser.py

# Analyze profiles
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

### **Hot Reload**
```bash
# Run with hot reload
uvicorn arx_svg_parser.main:app --reload --host 0.0.0.0 --port 8082
```

---

## 📚 **API Documentation**

### **Swagger/OpenAPI**
```bash
# Start server
uvicorn arx_svg_parser.main:app --reload

# View documentation
# Visit http://localhost:8082/docs
# Visit http://localhost:8082/redoc
```

### **API Endpoints**
```bash
# Health check
curl http://localhost:8082/health

# Parse SVG
curl -X POST http://localhost:8082/api/v1/parsers/svg \
  -H "Content-Type: application/json" \
  -d '{"svg_content": "<svg>...</svg>"}'

# Validate SVG
curl -X POST http://localhost:8082/api/v1/validation/svg \
  -H "Content-Type: application/json" \
  -d '{"svg_content": "<svg>...</svg>"}'

# Get symbols
curl http://localhost:8082/api/v1/symbols
```

---

## 🚀 **Deployment**

### **Production Build**
```bash
# Build for production
pip install -e ".[production]"

# Create Docker image
docker build -t arx-svg-parser:latest .
```

### **Environment Configuration**
```bash
# Production environment variables
export ENVIRONMENT=production
export LOG_LEVEL=info
export JWT_SECRET=your-production-secret
export DATABASE_URL=postgresql://user:pass@prod-db:5432/arxos_svg_db
```

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Database Connection**
```bash
# Check database connectivity
psql -h localhost -U arxos -d arxos_svg_db -c "SELECT 1;"

# Reset database
dropdb arxos_svg_db
createdb arxos_svg_db
alembic upgrade head
```

#### **Dependencies**
```bash
# Clean pip cache
pip cache purge

# Update dependencies
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-dev.txt
```

#### **Port Conflicts**
```bash
# Check port usage
lsof -i :8082

# Kill process using port
kill -9 $(lsof -t -i:8082)
```

#### **Celery Issues**
```bash
# Check Celery status
celery -A arx_svg_parser.celery_app inspect active

# Restart Celery worker
celery -A arx_svg_parser.celery_app control restart
```

### **Getting Help**
- **GitHub Issues**: [github.com/arxos/arxos/issues](https://github.com/arxos/arxos/issues)
- **Discord**: [discord.gg/arxos](https://discord.gg/arxos)
- **Email**: dev@arxos.com

---

## 📋 **Onboarding Checklist**

### **For New Developers**
- [ ] Install Python 3.11+ and verify installation
- [ ] Clone the repository and navigate to arx_svg_parser
- [ ] Create virtual environment and activate it
- [ ] Install dependencies with `pip install -e .`
- [ ] Set up PostgreSQL with PostGIS extension
- [ ] Set up Redis for Celery
- [ ] Copy and configure `env.example`
- [ ] Run database migrations with Alembic
- [ ] Start the development server
- [ ] Run tests and verify they pass
- [ ] Start Celery worker
- [ ] Make a small change and test it
- [ ] Review the codebase structure
- [ ] Read the API documentation

### **For Repository Maintainers**
- [ ] Ensure all dependencies are up to date
- [ ] Verify tests pass on all supported Python versions
- [ ] Update documentation for new features
- [ ] Review and merge pull requests
- [ ] Monitor CI/CD pipeline
- [ ] Maintain security best practices
- [ ] Update symbol catalog and schemas
- [ ] Validate ML models and performance

---

*This onboarding guide is maintained by the Arxos development team. Last updated: 2024-01-15* 