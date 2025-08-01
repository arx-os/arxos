# Arxos Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Automated Setup (Recommended)

#### For Linux/macOS:
```bash
# Clone the repository
git clone https://github.com/capstanistan/arxos.git
cd arxos

# Run the automated setup script
./scripts/setup_local.sh

# Test the setup
python scripts/test_setup.py
```

#### For Windows:
```cmd
# Clone the repository
git clone https://github.com/capstanistan/arxos.git
cd arxos

# Run the automated setup script
scripts\setup_local.bat

# Test the setup
python scripts\test_setup.py
```

### Option 2: Manual Setup

#### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Go 1.19+
- PostgreSQL 13+ with PostGIS
- Redis 6+

#### Quick Manual Setup
```bash
# 1. Start all services
docker-compose up -d

# 2. Wait for services to be ready (check logs)
docker-compose logs -f

# 3. Run database migrations
docker-compose exec svg-parser alembic upgrade head

# 4. Test the setup
python scripts/test_setup.py
```

## 🌐 Access Your Local Arxos

Once setup is complete, access the services at:

| Service | URL | Description |
|---------|-----|-------------|
| **Web Interface** | http://localhost:3000 | Main user interface |
| **SVG Parser API** | http://localhost:8000 | SVG processing service |
| **Backend API** | http://localhost:8080 | Core backend service |
| **SVGX Engine** | http://localhost:8001 | Advanced CAD processing |
| **Grafana Dashboard** | http://localhost:3001 | Monitoring dashboard |

### API Documentation
- **SVG Parser**: http://localhost:8000/docs
- **Backend**: http://localhost:8080/docs  
- **SVGX Engine**: http://localhost:8001/docs

## 🧪 Test Your Setup

### Quick Test Commands
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8080/api/health
curl http://localhost:8001/health

# User registration
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@arxos.com", "password": "password123"}'

# User login
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

### Run Complete Test Suite
```bash
python scripts/test_setup.py
```

## 📁 Project Structure

```
arxos/
├── core/                    # Core platform services
│   ├── svg-parser/         # SVG/BIM processing (Python/FastAPI)
│   └── backend/            # Backend services (Go/Chi)
├── svgx_engine/            # Advanced CAD processing engine
├── frontend/               # User interfaces
│   └── web/               # Web interface (HTML/HTMX)
├── services/               # Specialized microservices
├── infrastructure/         # DevOps and infrastructure
├── scripts/               # Setup and test scripts
└── docker-compose.yml     # Service orchestration
```

## 🔧 Development Workflow

### Making Changes
```bash
# Services auto-reload when you make changes
# For Go backend, rebuild:
cd core/backend && go build -o bin/arx-backend ./cmd/main.go

# For Python services, they auto-reload with --reload flag
```

### Database Changes
```bash
# Create new migration


# Apply migrations
docker-compose exec svg-parser alembic upgrade head
```

### Testing
```bash
# Run all tests
make test

# Run specific service tests

cd core/backend && go test ./...
cd svgx_engine && python -m pytest
```

## 🛠️ Common Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart svg-parser
```

### Development
```bash
# Install dependencies
make install

# Build all components
make build

# Run tests
make test

# Clean build artifacts
make clean
```

### Monitoring
```bash
# View service status
docker-compose ps

# Monitor resource usage
docker stats

# Check service health
curl http://localhost:8000/health
```

## 🚨 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using a port
lsof -i :8000  # Linux/macOS
netstat -an | findstr :8000  # Windows

# Kill process using port
kill -9 <PID>
```

#### Docker Issues
```bash
# Clean up Docker
docker-compose down -v
docker system prune -f

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

#### Database Issues
```bash
# Reset database
docker-compose exec svg-parser alembic downgrade base
docker-compose exec svg-parser alembic upgrade head
```

### Getting Help

1. **Check the logs**: `docker-compose logs -f`
2. **Run the test script**: `python scripts/test_setup.py`
3. **Review the detailed guide**: `LOCAL_SETUP_GUIDE.md`
4. **Check service health**: Visit the health endpoints listed above

## 📚 Next Steps

After successful setup:

1. **Explore the Web Interface**: http://localhost:3000
2. **Upload a test SVG**: Use the web interface to upload and process SVG files
3. **Try the SVGX Engine**: Test advanced CAD features at http://localhost:8001/docs
4. **Review the API Documentation**: Explore the available endpoints
5. **Check the Monitoring**: View metrics at http://localhost:3001

## 📞 Support

- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issues
- **Discussions**: Use GitHub Discussions
- **Development**: Follow the engineering playbook in `engineering_playbook.json`

---

**Note**: This is a development setup. For production deployment, see the deployment documentation in `infrastructure/deploy/`. 