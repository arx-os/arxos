# Arx Database Infrastructure - Developer Onboarding

## 🚀 **Quick Start**

Welcome to the Arx Database Infrastructure! This repository contains database management tools, migrations, monitoring, and documentation for the Arxos platform.

### **Prerequisites**
- **Python**: 3.11+ (required)
- **PostgreSQL**: 15+ with PostGIS extension
- **Git**: Latest version
- **Docker**: 20.10+ (optional, for containerized development)
- **Node.js**: 18+ (for documentation generation)

### **1. Clone and Setup**
```bash
# Clone the repository (if not already done)
git clone https://github.com/arxos/arxos.git
cd arxos/infrastructure/database

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
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
  --name arx-db-postgres \
  -e POSTGRES_DB=arxos_db \
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

# Generate documentation
python tools/generate_docs.py

# Validate schema
python tools/validate_schema.py
```

---

## 🔧 **Environment Variables**

Create a `.env` file based on `env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://arxos:arxos_password@localhost:5432/arxos_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=arxos_db
DATABASE_USER=arxos
DATABASE_PASSWORD=arxos_password

# Alembic Configuration
ALEMBIC_CONFIG=alembic.ini
ALEMBIC_SCRIPT_LOCATION=migrations
ALEMBIC_REVISION_TABLE=alembic_version

# Documentation Configuration
DOCS_OUTPUT_PATH=./docs
DOCS_TEMPLATE_PATH=./templates
DOCS_INCLUDE_EXAMPLES=true
DOCS_INCLUDE_DIAGRAMS=true

# Monitoring Configuration
MONITORING_ENABLED=true
MONITORING_INTERVAL=300
MONITORING_RETENTION_DAYS=30
MONITORING_ALERT_EMAIL=admin@arxos.com

# Performance Configuration
PERFORMANCE_MONITORING=true
PERFORMANCE_SLOW_QUERY_THRESHOLD=1000
PERFORMANCE_CONNECTION_POOL_SIZE=20
PERFORMANCE_MAX_CONNECTIONS=100

# Security Configuration
SECURITY_AUDIT_ENABLED=true
SECURITY_SCAN_INTERVAL=3600
SECURITY_REPORT_PATH=./security_reports
```

---

## 🛠️ **Development Commands**

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

### **Documentation Generation**
```bash
# Generate schema documentation
python tools/generate_schema_docs.py

# Generate migration documentation
python tools/generate_migration_docs.py

# Generate ER diagrams
python tools/generate_diagrams.py

# Validate documentation
python tools/validate_documentation.py
```

### **Monitoring and Performance**
```bash
# Run performance analysis
python tools/performance_analysis.py

# Monitor slow queries
python tools/slow_query_monitor.py

# Generate performance reports
python tools/generate_performance_report.py

# Check database health
python tools/health_check.py
```

### **Testing**
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=arx_database --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run linting
black tools/
isort tools/
flake8 tools/
mypy tools/
```

---

## 🏗️ **Project Structure**

```
infrastructure/database/
├── migrations/              # Database migrations
│   ├── env.py              # Alembic environment
│   ├── script.py.mako      # Migration template
│   └── versions/           # Migration files
├── tools/                  # Database tools
│   ├── generate_docs.py    # Documentation generator
│   ├── validate_schema.py  # Schema validator
│   ├── performance_analysis.py
│   ├── slow_query_monitor.py
│   ├── health_check.py
│   └── generate_diagrams.py
├── scripts/                # Utility scripts
│   ├── seed_database.py    # Database seeding
│   ├── backup_database.py  # Backup utilities
│   ├── restore_database.py # Restore utilities
│   └── maintenance.py      # Maintenance tasks
├── docs/                   # Generated documentation
│   ├── schema/             # Schema documentation
│   ├── migrations/         # Migration documentation
│   ├── performance/        # Performance reports
│   └── diagrams/           # ER diagrams
├── templates/              # Documentation templates
│   ├── schema_template.md
│   ├── migration_template.md
│   └── performance_template.md
├── tests/                  # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Performance tests
├── config/                 # Configuration files
│   ├── alembic.ini        # Alembic configuration
│   ├── database.yml       # Database configuration
│   └── monitoring.yml     # Monitoring configuration
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── env.example            # Environment template
├── .gitignore             # Git ignore rules
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── README.md             # Project documentation
```

---

## 🧪 **Testing**

### **Test Structure**
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/

# All tests with coverage
pytest --cov=arx_database --cov-report=html --cov-report=term
```

### **Test Database**
```bash
# Set up test database
createdb arxos_test

# Run tests with test database
DATABASE_URL=postgresql://localhost:5432/arxos_test pytest
```

### **Test Coverage**
```bash
# Generate coverage report
pytest --cov=arx_database --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

---

## 🐳 **Docker Development**

### **Using Docker Compose**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f database-tools

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
  database-tools:
    build: .
    environment:
      - DATABASE_URL=postgresql://arxos:arxos_password@postgres:5432/arxos_db
    depends_on:
      - postgres
    volumes:
      - ./docs:/app/docs
      - ./reports:/app/reports

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=arxos_db
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=arxos_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🔍 **Debugging**

### **Logging**
```bash
# Set log level
export LOG_LEVEL=debug

# View structured logs
python tools/health_check.py | jq
```

### **Database Debugging**
```bash
# Check database connectivity
python tools/health_check.py

# Analyze slow queries
python tools/slow_query_monitor.py --analyze

# Check schema consistency
python tools/validate_schema.py --verbose
```

---

## 📚 **Documentation**

### **Generated Documentation**
```bash
# Generate all documentation
python tools/generate_docs.py --all

# Generate specific documentation
python tools/generate_schema_docs.py
python tools/generate_migration_docs.py
python tools/generate_diagrams.py

# View documentation
open docs/index.html
```

### **Documentation Structure**
```
docs/
├── index.html              # Main documentation
├── schema/                 # Schema documentation
│   ├── tables/            # Table documentation
│   ├── relationships/     # Relationship diagrams
│   └── constraints/       # Constraint documentation
├── migrations/            # Migration documentation
│   ├── history.md        # Migration history
│   ├── rollback_guide.md # Rollback procedures
│   └── best_practices.md # Best practices
├── performance/           # Performance documentation
│   ├── reports/          # Performance reports
│   ├── benchmarks/       # Benchmark results
│   └── optimization.md   # Optimization guide
└── diagrams/             # Visual diagrams
    ├── er_diagram.png    # Entity relationship diagram
    ├── data_flow.png     # Data flow diagram
    └── architecture.png  # Architecture diagram
```

---

## 🚀 **Deployment**

### **Production Setup**
```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@prod-db:5432/arxos_db

# Run migrations
alembic upgrade head

# Generate production documentation
python tools/generate_docs.py --production
```

### **CI/CD Integration**
```bash
# Run in CI/CD pipeline
python tools/validate_schema.py
python tools/generate_docs.py
python tools/performance_analysis.py
```

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Database Connection**
```bash
# Check database connectivity
psql -h localhost -U arxos -d arxos_db -c "SELECT 1;"

# Reset database
dropdb arxos_db
createdb arxos_db
alembic upgrade head
```

#### **Migration Issues**
```bash
# Check migration status
alembic current
alembic history

# Fix migration conflicts
alembic stamp head
alembic revision --autogenerate -m "fix_migration"
```

#### **Documentation Generation**
```bash
# Regenerate documentation
python tools/generate_docs.py --force

# Validate documentation
python tools/validate_documentation.py --fix
```

### **Getting Help**
- **GitHub Issues**: [github.com/arxos/arxos/issues](https://github.com/arxos/arxos/issues)
- **Discord**: [discord.gg/arxos](https://discord.gg/arxos)
- **Email**: dev@arxos.com

---

## 📋 **Onboarding Checklist**

### **For New Developers**
- [ ] Install Python 3.11+ and verify installation
- [ ] Clone the repository and navigate to database infrastructure
- [ ] Create virtual environment and activate it
- [ ] Install dependencies with `pip install -r requirements.txt`
- [ ] Set up PostgreSQL with PostGIS extension
- [ ] Copy and configure `env.example`
- [ ] Run database migrations with Alembic
- [ ] Generate initial documentation
- [ ] Run tests and verify they pass
- [ ] Make a small change and test it
- [ ] Review the codebase structure
- [ ] Read the documentation

### **For Repository Maintainers**
- [ ] Ensure all dependencies are up to date
- [ ] Verify tests pass on all supported Python versions
- [ ] Update documentation for new features
- [ ] Review and merge pull requests
- [ ] Monitor CI/CD pipeline
- [ ] Maintain security best practices
- [ ] Update database schema documentation
- [ ] Validate migration procedures
- [ ] Monitor performance metrics

---

*This onboarding guide is maintained by the Arxos development team. Last updated: 2024-01-15* 