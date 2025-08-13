# Arxos Deployment Guide

This guide covers the complete deployment of the Arxos system with all critical next steps implemented.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Go 1.21+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if running without Docker)
- Redis 7+ (if running without Docker)

### Environment Configuration

1. Copy the environment template:
```bash
cp .env.example .env.production
```

2. Edit `.env.production` with your production values:
```bash
# CRITICAL: Change these in production!
POSTGRES_PASSWORD=your_secure_database_password_here
JWT_SECRET=your_super_secure_jwt_secret_key_change_this_in_production
GRAFANA_PASSWORD=secure_grafana_password

# API Keys (optional)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Domain Configuration
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com
ALLOWED_HOSTS=yourapp.com,www.yourapp.com
```

### Production Deployment

1. **Deploy with Docker Compose:**
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Scale services if needed
docker-compose -f docker-compose.production.yml up -d --scale arxos-api=3
```

2. **Verify deployment:**
```bash
# Run comprehensive tests
python scripts/test_all.py

# Check service health
curl http://localhost/health
curl http://localhost/api/v1/health
```

## 🏗️ Architecture Overview

The Arxos system consists of several interconnected services:

### Core Services

1. **Arxos API (Go)** - Main REST API with JWT authentication
   - Port: 8080
   - Features: ArxObject CRUD, JWT auth, symbol recognition bridge
   - Roles: admin, field_worker, validator, manager, operator, viewer, guest

2. **SVGX Engine (Python)** - Advanced SVG and CAD processing
   - Port: 8081
   - Features: Symbol recognition, SVG processing, CAD integration

3. **Python API Services** - Additional Python-based APIs
   - Port: 8082
   - Features: Extended business logic, data analysis

4. **GUS Agent (Python)** - AI-powered assistant
   - Port: 8083
   - Features: Natural language processing, intelligent assistance

### Infrastructure Services

5. **PostgreSQL** - Primary database
   - Port: 5432
   - Features: ArxObject storage, user management, audit logs

6. **Redis** - Caching and sessions
   - Port: 6379
   - Features: Session storage, caching, rate limiting

7. **Nginx** - Reverse proxy and load balancer
   - Ports: 80, 443
   - Features: SSL termination, load balancing, rate limiting

8. **Monitoring Stack**
   - Prometheus (9090) - Metrics collection
   - Grafana (3000) - Visualization and dashboards

## 🔐 Authentication & Authorization

### JWT Authentication

The system uses JWT tokens with role-based access control:

```bash
# Login to get JWT token
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token in requests
curl -H "Authorization: Bearer <token>" \
  http://localhost/api/v1/arxobjects
```

### User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **admin** | Full system access, user management, system configuration |
| **field_worker** | Create/update ArxObjects, ingest data, export data |
| **validator** | Read/update ArxObjects, validate data, limited ingestion |
| **manager** | Broad access except system management, can delete objects |
| **operator** | Read/update operations, limited ingestion access |
| **viewer** | Read-only access to buildings and objects |
| **guest** | Minimal read access to buildings only |

### Default Test Users

```bash
# Admin user
username: admin
password: admin123

# Field worker
username: fieldworker  
password: field123

# Validator
username: validator
password: valid123
```

## 🧪 Testing

### Run All Tests

```bash
# Comprehensive test suite
python scripts/test_all.py -v

# Run specific test suite
python scripts/test_all.py --suite bridge
python scripts/test_all.py --suite auth
python scripts/test_all.py --suite arxobject
```

### Test Components Individually

1. **Symbol Recognition Bridge:**
```bash
python tests/integration/test_symbol_recognition_bridge.py bridge
```

2. **API Authentication:**
```bash
python tests/integration/test_api_authentication.py auth
```

3. **ArxObject Operations:**
```bash
python tests/unit/test_arxobject_operations.py validation
```

## 🔄 Symbol Recognition Integration

### Python-Go Bridge

The system includes a complete bridge between Go and Python for symbol recognition:

1. **Go Service** (`arxos-ingestion/symbol_recognizer.go`)
   - Calls Python bridge script
   - Handles PDF, image, and SVG processing
   - Manages errors and timeouts

2. **Python Bridge** (`svgx_engine/services/symbols/recognize.py`)
   - Processes recognition requests via stdin/stdout
   - Supports multiple content types
   - Integrates with advanced symbol recognition engine

3. **Recognition Engine** (`svgx_engine/services/symbols/symbol_recognition.py`)
   - Advanced fuzzy matching
   - Context-aware interpretation
   - Comprehensive symbol library

### Usage Example

```bash
# Test symbol recognition
echo '{"content": "electrical outlet", "content_type": "text", "options": {"fuzzy_threshold": 0.6}}' | \
  python svgx_engine/services/symbols/recognize.py
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login

### ArxObjects
- `GET /api/v1/arxobjects` - List objects (requires read permission)
- `POST /api/v1/arxobjects` - Create object (requires create permission)
- `GET /api/v1/arxobjects/{id}` - Get object
- `PUT /api/v1/arxobjects/{id}` - Update object (requires update permission)
- `DELETE /api/v1/arxobjects/{id}` - Delete object (requires delete permission)

### Hierarchy
- `GET /api/v1/arxobjects/{id}/children` - Get child objects
- `GET /api/v1/arxobjects/{id}/parent` - Get parent object
- `GET /api/v1/arxobjects/{id}/ancestors` - Get ancestor chain

### Spatial Queries
- `POST /api/v1/arxobjects/spatial/viewport` - Objects in viewport
- `GET /api/v1/arxobjects/spatial/overlaps/{id}` - Overlapping objects
- `GET /api/v1/arxobjects/spatial/nearby/{id}` - Nearby objects

### Data Ingestion
- `POST /api/v1/ingest/pdf` - Ingest PDF (requires ingest_pdf permission)
- `POST /api/v1/ingest/image` - Ingest image (requires ingest_image permission)
- `POST /api/v1/ingest/lidar` - Start LiDAR session (requires ingest_lidar permission)

### System
- `GET /api/v1/systems` - List building systems
- `GET /api/v1/symbols` - Symbol library
- `GET /api/v1/health` - Health check (public)
- `GET /api/v1/ws` - WebSocket connection

## 🐳 Docker Configuration

### Multi-Stage Builds

All services use optimized multi-stage Docker builds:

1. **Go API** (`Dockerfile.go-api`)
   - Builder stage with Go compilation
   - Production stage with Alpine Linux
   - Includes Python for symbol recognition bridge

2. **SVGX Engine** (`Dockerfile.svgx`)
   - Python dependencies in builder stage
   - Optimized runtime with only required packages
   - Includes OpenCV and Tesseract for image processing

3. **Python API** (`Dockerfile.python-api`)
   - Comprehensive Python service setup
   - Optimized for FastAPI/Uvicorn deployment

4. **GUS Agent** (`Dockerfile.gus`)
   - AI agent with LLM integration
   - Includes conversation management

### Production Compose

The `docker-compose.production.yml` includes:

- Health checks for all services
- Proper networking and dependencies
- Volume mounts for persistence
- Environment variable configuration
- Resource limits and restart policies

## 🔧 Configuration Management

### Environment Variables

All services use environment variables for configuration:

#### Database
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=arxos
POSTGRES_USER=arxos
POSTGRES_PASSWORD=your_password_here
```

#### Redis
```bash
REDIS_URL=redis://redis:6379
```

#### JWT
```bash
JWT_SECRET=your_secret_here
JWT_EXPIRATION=3600
JWT_REFRESH_EXPIRATION=604800
```

#### Service-Specific
```bash
# Go API
PORT=8080
ENVIRONMENT=production
LOG_LEVEL=info
ENABLE_AUTH=true
MAX_UPLOAD_SIZE=104857600
CORS_ORIGINS=https://yourapp.com
RATE_LIMIT_PER_MINUTE=60

# Python Services
SERVICE_NAME=arxos-service
WORKERS=4
PYTHONPATH=/app

# External APIs
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Feature Flags
```bash
ENABLE_SYMBOL_RECOGNITION=true
ENABLE_PDF_INGESTION=true
ENABLE_LIDAR_CAPTURE=true
ENABLE_AI_FEATURES=true
ENABLE_REALTIME_UPDATES=true
```

## 📈 Monitoring & Observability

### Prometheus Metrics

Access Prometheus at http://localhost:9090

Key metrics to monitor:
- API request rates and latencies
- Database connection pool usage
- Authentication success/failure rates
- Symbol recognition processing times
- Memory and CPU usage per service

### Grafana Dashboards

Access Grafana at http://localhost:3000

Default dashboards include:
- Service health overview
- API performance metrics
- Database performance
- Authentication metrics
- Symbol recognition statistics

### Log Aggregation

All services use structured logging:
- JSON format in production
- Centralized log collection
- Error tracking and alerting
- Audit log for security events

## 🚨 Troubleshooting

### Common Issues

1. **JWT Secret Not Set**
   ```
   Error: JWT_SECRET must be changed in production environment
   ```
   Solution: Set JWT_SECRET environment variable

2. **Database Connection Failed**
   ```
   Error: failed to connect to database
   ```
   Solution: Check POSTGRES_PASSWORD and database connectivity

3. **Symbol Recognition Bridge Failed**
   ```
   Error: Python script execution failed
   ```
   Solution: Ensure Python dependencies are installed and script is executable

4. **Authentication Failed**
   ```
   Error: Invalid credentials
   ```
   Solution: Check default user credentials or create new users

### Health Checks

```bash
# Check all service health
curl http://localhost/health

# Check specific services
curl http://localhost:8080/api/v1/health  # Go API
curl http://localhost:8081/health         # SVGX Engine
curl http://localhost:8082/health         # Python API
curl http://localhost:8083/health         # GUS Agent
```

### Log Analysis

```bash
# View all service logs
docker-compose -f docker-compose.production.yml logs -f

# View specific service logs
docker-compose -f docker-compose.production.yml logs -f arxos-api
docker-compose -f docker-compose.production.yml logs -f postgres
```

## 🔄 Scaling & Performance

### Horizontal Scaling

```bash
# Scale API services
docker-compose -f docker-compose.production.yml up -d --scale arxos-api=3 --scale svgx-engine=2

# Update nginx for load balancing
# Edit nginx/conf.d/arxos.conf to add multiple upstream servers
```

### Performance Tuning

1. **Database Optimization**
   - Adjust PostgreSQL connection pool sizes
   - Enable query optimization
   - Configure appropriate indexes

2. **Redis Caching**
   - Tune cache TTL values
   - Monitor memory usage
   - Configure eviction policies

3. **Rate Limiting**
   - Adjust rate limits per endpoint
   - Configure burst allowances
   - Monitor and alert on rate limit hits

## 📋 Maintenance

### Regular Tasks

1. **Database Maintenance**
   ```bash
   # Backup database
   docker exec postgres pg_dump -U arxos arxos > backup.sql
   
   # Monitor database size and performance
   docker exec postgres psql -U arxos -c "SELECT schemaname,tablename,attname,n_distinct,correlation FROM pg_stats;"
   ```

2. **Log Rotation**
   ```bash
   # Configure log rotation in production
   # Monitor disk space usage
   ```

3. **Security Updates**
   ```bash
   # Update Docker images regularly
   docker-compose -f docker-compose.production.yml pull
   docker-compose -f docker-compose.production.yml up -d
   ```

### Backup & Recovery

1. **Database Backup**
   ```bash
   # Automated backup script
   docker exec postgres pg_dump -U arxos arxos | gzip > "arxos_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
   ```

2. **Configuration Backup**
   ```bash
   # Backup environment files and configurations
   tar -czf config_backup.tar.gz .env.production nginx/ monitoring/
   ```

## 🎯 Production Checklist

Before deploying to production:

- [ ] Set secure JWT_SECRET
- [ ] Configure strong POSTGRES_PASSWORD
- [ ] Set appropriate CORS_ORIGINS
- [ ] Configure SSL certificates
- [ ] Set up monitoring and alerting
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Test disaster recovery procedures
- [ ] Configure firewall rules
- [ ] Set up health check monitoring
- [ ] Configure resource limits
- [ ] Review security settings
- [ ] Test authentication flows
- [ ] Verify symbol recognition bridge
- [ ] Test all API endpoints
- [ ] Validate environment configuration

## 📚 Additional Resources

- [API Documentation](docs/API_SPECIFICATION.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT_GUIDE.md)
- [Symbol Library Documentation](ARXOBJECT_SYMBOL_LIBRARY_SPECIFICATION.md)
- [ArxObject Specification](ARXOBJECT_COMPLETE_SPECIFICATION.md)

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the test output from `python scripts/test_all.py`
3. Check service logs for detailed error information
4. Consult the comprehensive documentation in the `docs/` directory

---

**🏁 The Arxos system is now production-ready with all critical next steps implemented:**

✅ **Complete Python Bridge** - Symbol recognition bridge between Go and Python  
✅ **JWT Authentication** - Role-based access control with field_worker, validator, admin roles  
✅ **Docker Setup** - Multi-stage builds and production-ready containers  
✅ **Core Tests** - Comprehensive test suite for critical paths  
✅ **Environment Configuration** - All hardcoded values replaced with environment variables  

The system maintains the Arxos vision of "Google Maps for Buildings" with ArxObject as the core DNA, now enhanced with enterprise-grade security, scalability, and deployment capabilities.