# Arx CMMS - Developer Onboarding

## 🚀 **Quick Start**

Welcome to the Arx CMMS (Computerized Maintenance Management System)! This is the Go service that handles maintenance management, work orders, and asset tracking for the Arxos platform.

### **Prerequisites**
- **Go**: 1.21+ (required)
- **Git**: Latest version
- **PostgreSQL**: 15+ with PostGIS extension
- **Redis**: 6+ (for caching and sessions)
- **Docker**: 20.10+ (optional, for containerized development)

### **1. Clone and Setup**
```bash
# Clone the repository (if not already done)
git clone https://github.com/arxos/arxos.git
cd arxos/services/cmms

# Install Go dependencies
go mod tidy
go mod download
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
  --name arx-cmms-postgres \
  -e POSTGRES_DB=arxos_cmms_db \
  -e POSTGRES_USER=arxos \
  -e POSTGRES_PASSWORD=arxos_password \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# Run migrations
go run cmd/migrate/main.go
```

### **4. Verify Setup**
```bash
# Run tests
go test ./...

# Start development server
go run cmd/server/main.go
```

---

## 🔧 **Environment Variables**

Create a `.env` file based on `env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://arxos:arxos_password@localhost:5432/arxos_cmms_db?sslmode=disable
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=arxos_cmms_db
DATABASE_USER=arxos
DATABASE_PASSWORD=arxos_password

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Configuration
SERVER_PORT=8081
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

# CMMS Configuration
CMMS_WORK_ORDER_AUTO_ASSIGN=true
CMMS_PREVENTIVE_MAINTENANCE_ENABLED=true
CMMS_ASSET_TRACKING_ENABLED=true
CMMS_INVENTORY_MANAGEMENT_ENABLED=true

# Notification Configuration
NOTIFICATION_EMAIL_ENABLED=true
NOTIFICATION_SMS_ENABLED=false
NOTIFICATION_PUSH_ENABLED=false

# External Services
BILT_BACKEND_URL=http://localhost:8080
SVG_PARSER_SERVICE_URL=http://localhost:8082
```

---

## 🛠️ **Development Commands**

### **Build and Run**
```bash
# Build the application
go build -o arx-cmms cmd/server/main.go

# Run the server
./arx-cmms

# Or run directly
go run cmd/server/main.go

# Run with hot reload (requires air)
air
```

### **Testing**
```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run tests with verbose output
go test -v ./...

# Run specific test
go test -v ./handlers -run TestWorkOrderHandler

# Run integration tests
go test -tags=integration ./...

# Run benchmarks
go test -bench=. ./...
```

### **Linting and Code Quality**
```bash
# Run linter
golangci-lint run

# Run linter with specific checks
golangci-lint run --enable=govet,errcheck,staticcheck

# Format code
go fmt ./...

# Organize imports
goimports -w .

# Check for security issues
gosec ./...
```

### **Database Operations**
```bash
# Run migrations
go run cmd/migrate/main.go

# Rollback migrations
go run cmd/migrate/main.go rollback

# Seed database
go run cmd/seed/main.go

# Generate new migration
go run cmd/migrate/main.go create migration_name
```

---

## 🏗️ **Project Structure**

```
arx-cmms/
├── cmd/                    # Application entry points
│   ├── server/            # Main server binary
│   ├── migrate/           # Database migration tool
│   └── seed/              # Database seeding tool
├── handlers/              # HTTP request handlers
│   ├── work_orders.go     # Work order endpoints
│   ├── assets.go          # Asset management
│   ├── maintenance.go     # Maintenance schedules
│   ├── inventory.go       # Inventory management
│   └── reports.go         # Reporting endpoints
├── middleware/            # HTTP middleware
│   ├── auth.go           # Authentication middleware
│   ├── cors.go           # CORS middleware
│   └── logging.go        # Request logging
├── models/               # Data models
│   ├── work_order.go     # Work order model
│   ├── asset.go          # Asset model
│   ├── maintenance.go    # Maintenance model
│   └── inventory.go      # Inventory model
├── services/             # Business logic
│   ├── work_order.go     # Work order service
│   ├── asset.go          # Asset service
│   ├── maintenance.go    # Maintenance service
│   └── inventory.go      # Inventory service
├── database/             # Database configuration
│   └── db.go            # Database connection
├── migrations/           # Database migrations
│   ├── 001_init.sql     # Initial schema
│   └── 002_cmms.sql     # CMMS tables
├── tests/               # Test files
│   ├── handlers/        # Handler tests
│   ├── services/        # Service tests
│   └── integration/     # Integration tests
├── docs/                # API documentation
├── scripts/             # Utility scripts
├── go.mod               # Go module file
├── go.sum               # Dependency checksums
├── env.example          # Environment template
├── .gitignore           # Git ignore rules
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
└── README.md           # Project documentation
```

---

## 🧪 **Testing**

### **Test Structure**
```bash
# Unit tests
go test ./handlers
go test ./services
go test ./models

# Integration tests
go test -tags=integration ./tests/integration

# API tests
go test ./tests/api

# Performance tests
go test -bench=. ./tests/benchmark
```

### **Test Database**
```bash
# Set up test database
createdb arxos_cmms_test

# Run tests with test database
DATABASE_URL=postgresql://localhost:5432/arxos_cmms_test go test ./...
```

### **Test Coverage**
```bash
# Generate coverage report
go test -coverprofile=coverage.out ./...

# View coverage in browser
go tool cover -html=coverage.out -o coverage.html
open coverage.html
```

---

## 🐳 **Docker Development**

### **Using Docker Compose**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f arx-cmms

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
  arx-cmms:
    build: .
    ports:
      - "8081:8081"
    environment:
      - DATABASE_URL=postgresql://arxos:arxos_password@postgres:5432/arxos_cmms_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=arxos_cmms_db
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
go run cmd/server/main.go | jq
```

### **Profiling**
```bash
# CPU profiling
go run cmd/server/main.go &
curl http://localhost:8081/debug/pprof/profile -o cpu.prof

# Memory profiling
curl http://localhost:8081/debug/pprof/heap -o mem.prof

# Analyze profiles
go tool pprof cpu.prof
go tool pprof mem.prof
```

### **Hot Reload**
```bash
# Install air for hot reload
go install github.com/cosmtrek/air@latest

# Run with hot reload
air
```

---

## 📚 **API Documentation**

### **Swagger/OpenAPI**
```bash
# Generate API documentation
swag init -g cmd/server/main.go

# View documentation
go run cmd/server/main.go
# Visit http://localhost:8081/swagger/index.html
```

### **API Endpoints**
```bash
# Health check
curl http://localhost:8081/health

# Get work orders
curl http://localhost:8081/api/v1/work-orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Create work order
curl -X POST http://localhost:8081/api/v1/work-orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"title":"Maintenance","description":"Regular maintenance","priority":"medium"}'

# Get assets
curl http://localhost:8081/api/v1/assets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🚀 **Deployment**

### **Production Build**
```bash
# Build for production
CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o arx-cmms cmd/server/main.go

# Create Docker image
docker build -t arx-cmms:latest .
```

### **Environment Configuration**
```bash
# Production environment variables
export ENVIRONMENT=production
export LOG_LEVEL=info
export JWT_SECRET=your-production-secret
export DATABASE_URL=postgresql://user:pass@prod-db:5432/arxos_cmms_db
```

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **Database Connection**
```bash
# Check database connectivity
psql -h localhost -U arxos -d arxos_cmms_db -c "SELECT 1;"

# Reset database
dropdb arxos_cmms_db
createdb arxos_cmms_db
go run cmd/migrate/main.go
```

#### **Dependencies**
```bash
# Clean module cache
go clean -modcache

# Update dependencies
go get -u ./...
go mod tidy
```

#### **Port Conflicts**
```bash
# Check port usage
lsof -i :8081

# Kill process using port
kill -9 $(lsof -t -i:8081)
```

### **Getting Help**
- **GitHub Issues**: [github.com/arxos/arxos/issues](https://github.com/arxos/arxos/issues)
- **Discord**: [discord.gg/arxos](https://discord.gg/arxos)
- **Email**: dev@arxos.com

---

## 📋 **Onboarding Checklist**

### **For New Developers**
- [ ] Install Go 1.21+ and verify installation
- [ ] Clone the repository and navigate to arx-cmms
- [ ] Install dependencies with `go mod tidy`
- [ ] Set up PostgreSQL and Redis
- [ ] Copy and configure `env.example`
- [ ] Run database migrations
- [ ] Start the development server
- [ ] Run tests and verify they pass
- [ ] Make a small change and test it
- [ ] Review the codebase structure
- [ ] Read the API documentation

### **For Repository Maintainers**
- [ ] Ensure all dependencies are up to date
- [ ] Verify tests pass on all supported Go versions
- [ ] Update documentation for new features
- [ ] Review and merge pull requests
- [ ] Monitor CI/CD pipeline
- [ ] Maintain security best practices
- [ ] Update CMMS workflows and processes
- [ ] Validate maintenance schedules and rules

---

*This onboarding guide is maintained by the Arxos development team. Last updated: 2024-01-15* 