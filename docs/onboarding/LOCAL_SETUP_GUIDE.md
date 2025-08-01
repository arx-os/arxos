# Arxos Local Development Setup Guide

This guide provides step-by-step instructions to set up and test the entire Arxos product locally.

## 🏗️ System Architecture Overview

Arxos consists of multiple interconnected services:

- **Core Services**: SVG Parser (Python/FastAPI), Backend (Go/Chi)
- **Frontend**: Web interface (HTML/HTMX/Tailwind), Mobile apps (iOS/Android)
- **Specialized Services**: AI, IoT, CMMS, Data Vendor
- **Infrastructure**: PostgreSQL, Redis, Monitoring
- **SVGX Engine**: Advanced CAD-grade processing engine

## 📋 Prerequisites

### Required Software
- **Python 3.8+** (3.11 recommended)
- **Go 1.19+** (1.21 recommended)
- **Node.js 16+** (18 recommended)
- **Docker & Docker Compose**
- **PostgreSQL 13+** with PostGIS extension
- **Redis 6+**

### Optional Software
- **Xcode** (for iOS development)
- **Android Studio** (for Android development)
- **Git** (for version control)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **OS**: macOS, Linux, or Windows (WSL2)

## 🚀 Quick Start (Docker Method)

### 1. Clone and Navigate
```bash
git clone https://github.com/arxos/arxos.git
cd arxos
```

### 2. Set Environment Variables
```bash
# Create environment file
cp .env.example .env

# Edit .env with your configuration
# Key variables to set:
# - DATABASE_URL
# - REDIS_URL
# - JWT_SECRET
# - API_HOST
# - API_PORT
```

### 3. Start All Services
```bash
# Start everything with Docker Compose
docker-compose up -d

# Or use the Makefile
make dev
```

### 4. Verify Services
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔧 Manual Setup (Development Method)

### 1. Database Setup

#### PostgreSQL with PostGIS
```bash
# Install PostgreSQL and PostGIS
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib postgis

# macOS:
brew install postgresql postgis

# Windows: Download from https://www.postgresql.org/download/windows/

# Create database and user
sudo -u postgres psql
CREATE DATABASE arxos;
CREATE USER arxos WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE arxos TO arxos;
\q

# Enable PostGIS extension
psql -U arxos -d arxos -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

#### Redis
```bash
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis

# Start Redis
redis-server
```

### 2. Core Services Setup



#### Backend (Go/Chi)
```bash
cd core/backend

# Install Go dependencies
go mod download

# Build the application
go build -o bin/arx-backend ./cmd/main.go

# Start the service
./bin/arx-backend
# Or: go run main.go
```

### 3. SVGX Engine Setup

#### Install SVGX Engine
```bash
cd arxos/svgx_engine

# Install in editable mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Start the SVGX Engine
python app.py
# Or: uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Frontend Setup

#### Web Frontend
```bash
cd arxos/frontend/web

# Serve static files (no build required for HTMX)
# Using Python's built-in server
python -m http.server 3000

# Or using Node.js if you have a package.json
npm install
npm start
```

### 5. Specialized Services (Optional)

#### AI Service
```bash
cd arxos/services/ai
pip install -r requirements.txt
python main.py
```

#### IoT Service
```bash
cd arxos/services/iot
pip install -r requirements.txt
python main.py
```

#### CMMS Service
```bash
cd arxos/services/cmms
pip install -r requirements.txt
python main.py
```

## 🧪 Testing the System

### 1. Health Checks

#### API Endpoints
```bash
# SVG Parser Health
curl http://localhost:8000/health

# Backend Health
curl http://localhost:8080/api/health

# SVGX Engine Health
curl http://localhost:8001/health

# Database Connection
psql -U arxos -d arxos -c "SELECT version();"
```

#### Web Interface
- Open browser to: `http://localhost:3000`
- Login with test credentials (see test data below)

### 2. Manual Testing Workflow

#### 1. User Registration/Login
```bash
# Register a new user
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# Login
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

#### 2. Upload SVG File
```bash
# Upload an SVG file
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@path/to/your/floorplan.svg" \
  -F "building_id=1" \
  -F "name=Ground Floor"
```

#### 3. Process with SVGX Engine
```bash
# Parse SVG with SVGX Engine
curl -X POST http://localhost:8001/parse \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<svg>...</svg>",
    "options": {"precision": "high"}
  }'
```

#### 4. View in Web Interface
- Navigate to: `http://localhost:3000`
- Select building and floor
- View SVG BIM visualization

### 3. Test Data

#### Sample Buildings
```sql
-- Insert test building
INSERT INTO buildings (name, address, created_at) 
VALUES ('Test Building', '123 Test St', NOW());

-- Insert test floor
INSERT INTO floors (building_id, name, svg_content) 
VALUES (1, 'Ground Floor', '<svg>...</svg>');
```

#### Sample SVG Content
```xml
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect x="100" y="100" width="200" height="150" fill="white" stroke="black"/>
  <circle cx="200" cy="175" r="20" fill="red"/>
</svg>
```

## 🔍 Monitoring and Debugging

### 1. Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f svg-parser
docker-compose logs -f backend
docker-compose logs -f svgx-engine
```

### 2. Database Monitoring
```bash
# Connect to database
psql -U arxos -d arxos

# Check tables
\dt

# View recent activity
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```

### 3. Performance Monitoring
```bash
# SVGX Engine metrics
curl http://localhost:8001/metrics

# Backend performance
curl http://localhost:8080/api/health
```

### 4. Grafana Dashboard (if using Docker)
- URL: `http://localhost:3001`
- Username: `admin`
- Password: `admin`

## 🛠️ Development Workflow

### 1. Code Changes
```bash
# Make changes to any service
# The services will auto-reload (if using --reload flag)

# For Go backend, rebuild:
cd core/backend
go build -o bin/arx-backend ./cmd/main.go
```

### 2. Database Migrations
```bash
# Run migrations
cd arxos/core/svg-parser
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

### 3. Testing
```bash
# Run all tests
make test

# Run specific service tests
cd arxos/core/backend && go test ./...
cd arxos/svgx_engine && python -m pytest
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check what's using a port
lsof -i :8000
lsof -i :8080
lsof -i :3000

# Kill process using port
kill -9 <PID>
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check connection
psql -U arxos -d arxos -c "SELECT 1;"
```

#### 3. Import Errors
```bash
# Ensure you're in the correct directory
cd arxos

# Install packages in editable mode
pip install -e ./svgx_engine
```

#### 4. Docker Issues
```bash
# Clean up Docker
docker-compose down
docker system prune -f

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### Performance Issues

#### 1. Memory Usage
```bash
# Monitor memory usage
htop
free -h

# Check Docker resource usage
docker stats
```

#### 2. Slow Response Times
- Check database indexes
- Monitor Redis cache hit rate
- Review SVGX Engine performance metrics

## 📊 Verification Checklist

### ✅ Core Services
- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible

- [ ] Backend API responding on port 8080
- [ ] SVGX Engine responding on port 8001

### ✅ Frontend
- [ ] Web interface accessible on port 3000
- [ ] User registration/login working
- [ ] SVG upload functionality working
- [ ] Floor plan visualization working

### ✅ Integration
- [ ] SVG files can be uploaded and processed
- [ ] SVGX Engine can parse and validate SVGs
- [ ] Web interface can display processed SVGs
- [ ] User authentication working across services

### ✅ Advanced Features
- [ ] Real-time collaboration working
- [ ] Performance monitoring active
- [ ] Audit logging functional
- [ ] Error handling working properly

## 🎯 Next Steps

After successful local setup:

1. **Explore the API Documentation**
   - SVG Parser: `http://localhost:8000/docs`
   - Backend: `http://localhost:8080/docs`
   - SVGX Engine: `http://localhost:8001/docs`

2. **Test Advanced Features**
   - Real-time collaboration
   - SVGX constraint system
   - Performance monitoring
   - Export functionality

3. **Develop Custom Features**
   - Add new SVGX symbols
   - Implement custom logic rules
   - Extend the API endpoints

4. **Production Deployment**
   - Review security configurations
   - Set up proper monitoring
   - Configure backup strategies

## 📞 Support

- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issues
- **Discussions**: Use GitHub Discussions
- **Development**: Follow the engineering playbook in `engineering_playbook.json`

---

**Note**: This setup guide assumes you're running on a Unix-like system (Linux/macOS). For Windows, use WSL2 or adjust paths and commands accordingly. 