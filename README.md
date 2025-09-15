# ArxOS - Building Operating System

[![CI/CD Pipeline](https://github.com/joelpate/arxos/actions/workflows/ci.yml/badge.svg)](https://github.com/joelpate/arxos/actions/workflows/ci.yml)
[![Go Version](https://img.shields.io/badge/Go-1.21-blue.svg)](https://go.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ArxOS is a comprehensive building management platform that treats buildings as code, providing a universal addressing system and powerful automation capabilities for modern smart buildings.

## 🎯 Features

### Core Innovation: Universal Addressing
Every piece of equipment has a hierarchical address:
```
ARXOS-NA-US-NY-NYC-0001/N/3/A/301/E/OUTLET_02
│                       │ │ │ │   │ └─ Equipment ID
│                       │ │ │ │   └─── Wall (East)
│                       │ │ │ └─────── Room 301
│                       │ │ └───────── Zone A (northwest)
│                       │ └─────────── Floor 3
│                       └───────────── Tower (North)
└───────────────────────────────────── Building ID
```

### Platform Capabilities
- **Building-as-Code**: Text-based BIM format with Git version control
- **Real-time Monitoring**: Live equipment status and sensor data
- **Energy Management**: Track and optimize energy consumption
- **Maintenance Scheduling**: Automated maintenance tracking and alerts
- **Multi-layer Visualization**: Terminal-based and web UI visualization
- **API-First Architecture**: RESTful API with OpenAPI documentation
- **Cloud & On-Premise**: Flexible deployment options
- **Mobile AR Support**: Augmented reality for field workers

## 🚀 Quick Start

### Prerequisites

- Go 1.21 or later
- Docker and Docker Compose (optional)
- PostgreSQL 16+ or SQLite

### Installation

#### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/joelpate/arxos.git
cd arxos

# Copy environment configuration
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

The ArxOS server will be available at `http://localhost:8080`

#### Manual Installation

```bash
# Clone the repository
git clone https://github.com/joelpate/arxos.git
cd arxos

# Install dependencies
go mod download

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
go run cmd/arxos-server/main.go migrate

# Build all binaries
go build -o bin/arx ./cmd/arx
go build -o bin/arxd ./cmd/arxd
go build -o bin/arxos-server ./cmd/arxos-server

# Start the server
./bin/arxos-server
```

### CLI Usage

```bash
# Import a building from BIM file
arx import building.bim

# List all buildings
arx list buildings

# Get building details
arx get building ARXOS-NA-US-NY-NYC-0001

# Monitor equipment status
arx monitor --building ARXOS-NA-US-NY-NYC-0001

# Export building data
arx export ARXOS-NA-US-NY-NYC-0001 --format json > building.json

# Watch for BIM file changes
arxd watch ./buildings --auto-sync
```

## 📁 Project Structure

```
arxos/
├── cmd/                    # Application entrypoints
│   ├── arx/               # CLI tool
│   ├── arxd/              # Daemon service
│   └── arxos-server/      # API server
├── internal/              # Private application code
│   ├── api/              # API handlers and routing
│   ├── bim/              # BIM format parser
│   ├── common/           # Shared utilities
│   │   ├── errors/       # Error handling
│   │   ├── logger/       # Logging
│   │   ├── resources/    # Resource management
│   │   └── retry/        # Retry logic
│   ├── config/           # Configuration management
│   ├── database/         # Database layer
│   ├── energy/           # Energy management
│   ├── middleware/       # HTTP middleware
│   ├── metrics/          # Metrics collection
│   └── rendering/        # Visualization layers
├── pkg/                   # Public packages
│   └── models/           # Data models
├── migrations/            # Database migrations
├── web/                   # Web UI assets
├── docs/                  # Documentation
└── examples/              # Example BIM files
```

## 🏗️ Architecture

ArxOS follows a microservices architecture with clean separation of concerns:

### Components

- **API Server**: RESTful API with OpenAPI documentation
- **Daemon (arxd)**: File watcher and background processor
- **CLI (arx)**: Command-line interface for operations
- **Database**: PostgreSQL or SQLite for persistence
- **Cache**: Optional Redis for performance

### Technology Stack

- **Backend**: Go 1.21 with standard library focus
- **Database**: PostgreSQL 16 / SQLite
- **API**: RESTful with OpenAPI 3.0
- **Authentication**: JWT with refresh tokens
- **Web UI**: HTMX for progressive enhancement
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker with multi-stage builds
- **CI/CD**: GitHub Actions

## 📊 API Documentation

### Authentication

```bash
# Register a new user
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user","password":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"SecurePass123!"}'
```

### Building Operations

```bash
# Create a building
curl -X POST http://localhost:8080/api/v1/buildings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "arxos_id": "ARXOS-NA-US-NY-NYC-0001",
    "name": "Empire State Building",
    "address": "350 5th Ave",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "latitude": 40.7484,
    "longitude": -73.9857
  }'

# Get building details
curl http://localhost:8080/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001 \
  -H "Authorization: Bearer YOUR_TOKEN"

# List all equipment in a building
curl http://localhost:8080/api/v1/buildings/ARXOS-NA-US-NY-NYC-0001/equipment \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Full API documentation is available at `http://localhost:8080/swagger` when the server is running.

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Database
ARXOS_DB_DRIVER=postgres
ARXOS_DATABASE_URL=postgres://arxos:password@localhost:5432/arxos

# Security
ARXOS_JWT_SECRET=your-secret-key-min-32-chars
ARXOS_ENABLE_AUTH=true
ARXOS_ENABLE_TLS=false

# Server
ARXOS_SERVER_PORT=8080
ARXOS_LOG_LEVEL=info

# Features
ARXOS_METRICS_ENABLED=true
ARXOS_TELEMETRY=false
ARXOS_CLOUD_SYNC=false
```

### Configuration File

Create `arxos.json`:

```json
{
  "mode": "hybrid",
  "version": "1.0.0",
  "database": {
    "driver": "postgres",
    "max_connections": 25,
    "auto_migrate": true
  },
  "security": {
    "enable_auth": true,
    "jwt_expiry": "24h",
    "bcrypt_cost": 12,
    "api_rate_limit": 100
  },
  "storage": {
    "backend": "local",
    "local_path": "./data"
  },
  "features": {
    "cloud_sync": false,
    "ai_integration": false,
    "offline_mode": true
  }
}
```

## 🧪 Testing

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run integration tests
go test -tags=integration ./...

# Run benchmarks
go test -bench=. ./...

# Run with race detection
go test -race ./...
```

## 📈 Monitoring

ArxOS includes comprehensive monitoring:

### Health Endpoints
- **Health Check**: `GET /health` - Overall system health
- **Readiness**: `GET /ready` - Ready to serve traffic
- **Liveness**: `GET /live` - Process is alive
- **Metrics**: `GET /metrics` - Prometheus metrics

### Grafana Dashboard

```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access services
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9091  # Prometheus
```

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t arxos:latest .

# Run container
docker run -d \
  -p 8080:8080 \
  -v arxos_data:/app/data \
  -e ARXOS_DATABASE_URL=postgres://... \
  -e ARXOS_JWT_SECRET=... \
  --name arxos \
  arxos:latest
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arxos
  template:
    metadata:
      labels:
        app: arxos
    spec:
      containers:
      - name: arxos
        image: arxos:latest
        ports:
        - containerPort: 8080
        env:
        - name: ARXOS_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: database-url
```

### Production Checklist

- [ ] Set secure JWT secret (min 32 chars)
- [ ] Configure TLS/SSL certificates
- [ ] Enable authentication and authorization
- [ ] Set up automated database backups
- [ ] Configure monitoring and alerting
- [ ] Set resource limits and autoscaling
- [ ] Enable rate limiting and DDoS protection
- [ ] Configure centralized logging
- [ ] Set up CI/CD pipeline
- [ ] Create disaster recovery plan

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/arxos.git
cd arxos

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
go test ./...

# Commit with conventional commits
git commit -m "feat: add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

### Code Standards
- Follow Go best practices and idioms
- Write tests for new functionality
- Update documentation
- Use conventional commits
- Run `go fmt` and `go vet`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Building Automation Systems community
- Go community and standard library
- HTMX for progressive enhancement
- OpenAPI Initiative

## 📞 Support

- **Documentation**: [https://arxos.io/docs](https://arxos.io/docs)
- **Issues**: [GitHub Issues](https://github.com/joelpate/arxos/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joelpate/arxos/discussions)

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- ✅ Core BIM parser
- ✅ Database layer
- ✅ REST API
- ✅ CLI tool
- ✅ Docker support

### Phase 2: Enhancement (Q1 2025)
- [ ] Web UI with HTMX
- [ ] Mobile application
- [ ] Advanced analytics
- [ ] AI integration

### Phase 3: Scale (Q2 2025)
- [ ] Multi-tenant SaaS
- [ ] GraphQL API
- [ ] Real-time collaboration
- [ ] IoT integration

### Phase 4: Innovation (Q3 2025)
- [ ] AR/VR support
- [ ] Blockchain audit logs
- [ ] Predictive maintenance ML
- [ ] Energy optimization AI

---

Built with ❤️ by the ArxOS Team