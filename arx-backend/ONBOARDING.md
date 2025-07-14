# Arx Backend - Developer Onboarding

## 🚀 **Quick Start**

Welcome to the Arx Backend! This is the main Go service that provides the core API and business logic for the Arxos platform.

### **Prerequisites**
- **Go**: 1.23+ (required)
- **Git**: Latest version
- **PostgreSQL**: 15+ with PostGIS extension
- **Redis**: 6+ (for caching and sessions)
- **Docker**: 20.10+ (optional, for containerized development)

### **1. Clone and Setup**
```bash
# Clone the repository (if not already done)
git clone https://github.com/arxos/arxos.git
cd arxos/arx-backend

# Install Go dependencies
go mod tidy
go mod download
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# See Environment Variables section below
```

### **3. Database Setup**
```bash
# Start PostgreSQL (if using Docker)
docker run -d \
  --name arx-postgres \
  -e POSTGRES_DB=arxos_db \
  -e POSTGRES_USER=arxos \
  -e POSTGRES_PASSWORD=arxos_password \
  -p 5432:5432 \
  postgres:15

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

Create a `.env` file based on `.env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://arxos:arxos_password@localhost:5432/arxos_db?sslmode=disable
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=arxos_db
DATABASE_USER=arxos
DATABASE_PASSWORD=arxos_password

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Configuration
SERVER_PORT=8080
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

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# External Services
CMMS_SERVICE_URL=http://localhost:8081
SVG_PARSER_SERVICE_URL=http://localhost:8082
```

---

## 🛠️ **Development Commands**

### **Build and Run**
```bash
# Build the application
go build -o arx-backend cmd/server/main.go

# Run the server
./arx-backend

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
go test -v ./handlers -run TestUserHandler

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
arx-backend/
├── cmd/                    # Application entry points
│   ├── server/            # Main server binary
│   ├── migrate/           # Database migration tool
│   └── seed/              # Database seeding tool
├── handlers/              # HTTP request handlers
│   ├── admin.go          # Admin endpoints
│   ├── auth.go           # Authentication endpoints
│   ├── buildings.go      # Building management
│   └── users.go          # User management
├── middleware/            # HTTP middleware
│   ├── auth.go           # Authentication middleware
│   ├── cors.go           # CORS middleware
│   └── logging.go        # Request logging
├── models/               # Data models
│   ├── user.go          # User model
│   ├── building.go      # Building model
│   └── project.go       # Project model
├── services/             # Business logic
│   ├── auth.go          # Authentication service
│   ├── user.go          # User service
│   └── building.go      # Building service
├── database/             # Database configuration
│   └── db.go            # Database connection
├── migrations/           # Database migrations
│   ├── 001_init.sql     # Initial schema
│   └── 002_users.sql    # User table
├── tests/               # Test files
│   ├── handlers/        # Handler tests
│   ├── services/        # Service tests
│   └── integration/     # Integration tests
├── docs/                # API documentation
├── scripts/             # Utility scripts
├── go.mod               # Go module file
├── go.sum               # Dependency checksums
├── .env.example         # Environment template
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
createdb arxos_test

# Run tests with test database
DATABASE_URL=postgresql://localhost:5432/arxos_test go test ./...
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
docker-compose logs -f arx-backend

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
  arx-backend:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://arxos:arxos_password@postgres:5432/arxos_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=arxos_db
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
curl http://localhost:8080/debug/pprof/profile -o cpu.prof

# Memory profiling
curl http://localhost:8080/debug/pprof/heap -o mem.prof

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
# Visit http://localhost:8080/swagger/index.html
```

### **API Endpoints**
```bash
# Health check
curl http://localhost:8080/health

# Authentication
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Get users
curl http://localhost:8080/api/v1/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🚀 **Deployment**

### **Production Build**
```bash
# Build for production
CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o arx-backend cmd/server/main.go

# Create Docker image
docker build -t arx-backend:latest .
```

### **Environment Configuration**
```bash
# Production environment variables
export ENVIRONMENT=production
export LOG_LEVEL=info
export JWT_SECRET=your-production-secret
export DATABASE_URL=postgresql://user:pass@prod-db:5432/arxos_db
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
lsof -i :8080

# Kill process using port
kill -9 $(lsof -t -i:8080)
```

### **Getting Help**
- **GitHub Issues**: [github.com/arxos/arxos/issues](https://github.com/arxos/arxos/issues)
- **Discord**: [discord.gg/arxos](https://discord.gg/arxos)
- **Email**: dev@arxos.com

---

## 📋 **Onboarding Checklist**

### **For New Developers**
- [ ] Install Go 1.23+ and verify installation
- [ ] Clone the repository and navigate to arx-backend
- [ ] Install dependencies with `go mod tidy`
- [ ] Set up PostgreSQL and Redis
- [ ] Copy and configure `.env.example`
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

---

*This onboarding guide is maintained by the Arxos development team. Last updated: 2024-01-15* 