# Arxos Core

The core backend system for the Arxos platform, providing building intelligence and digital twin capabilities.

## Architecture

```
core/
├── cmd/                    # Application entry points
│   └── server/            # Main server executable
├── internal/              # Private application code
│   ├── arxobject/        # Core data model
│   ├── auth/             # Authentication
│   ├── handlers/         # HTTP request handlers
│   ├── middleware/       # HTTP middleware
│   ├── models/           # Database models
│   ├── pipeline/         # Processing pipeline
│   ├── repository/       # Data access layer
│   └── services/         # Business logic
├── pkg/                   # Public libraries
│   ├── aql/              # Arxos Query Language
│   ├── bim/              # Building Information Modeling
│   ├── topology/         # Spatial analysis
│   └── wall_composition/ # Wall processing
├── migrations/           # Database migrations
└── tests/               # Integration tests
```

## Quick Start

### Prerequisites

- Go 1.21 or higher
- PostgreSQL 14+
- Redis (for caching)
- Python 3.9+ (for AI processing scripts)

### Development Setup

1. **Clone and setup**:
```bash
cd core
cp .env.example .env
# Edit .env with your configuration
```

2. **Install dependencies**:
```bash
make deps
```

3. **Run migrations**:
```bash
make migrate
```

4. **Start development server**:
```bash
make dev  # Hot reload enabled
# or
make run  # Standard run
```

### Building

```bash
# Development build
make build

# Production build
make prod

# Docker build
make docker
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run benchmarks
make benchmark
```

## Key Components

### ArxObject

The core data model representing any building element with:
- Spatial geometry and positioning
- Validation and confidence tracking
- Relationships to other objects
- Version history
- Field validation support

### AQL (Arxos Query Language)

SQL-like query language for building data:
```sql
SELECT * FROM building:hq:floor:3 WHERE type = 'wall'
SELECT * FROM building:* WHERE confidence < 0.7
```

### Processing Pipeline

Multi-stage pipeline for ingesting building data:
1. **Ingestion** - PDF, IFC, LiDAR, Images
2. **Extraction** - AI-powered element detection
3. **Validation** - Confidence scoring
4. **Storage** - Optimized spatial indexing

### API Endpoints

Core endpoints:
- `/api/v1/arxobjects` - CRUD operations
- `/api/v1/query` - AQL queries
- `/api/v1/ingest` - File ingestion
- `/api/v1/validate` - Field validation
- `/health` - Health check

## Configuration

Configuration via environment variables or `.env` file:

```env
# Server
PORT=8080
ENV=development

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=arxos
DB_USER=arxos
DB_PASSWORD=secret

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AI Service
AI_SERVICE_URL=http://localhost:8000

# Auth
JWT_SECRET=your-secret-key
ADMIN_PASSWORD=admin-password
```

## Development

### Code Organization

- **`internal/`** - Private code, not importable by other projects
- **`pkg/`** - Public libraries, can be imported
- **`cmd/`** - Executable entry points
- **Keep handlers thin** - Business logic in services
- **Repository pattern** - Database access abstraction
- **Dependency injection** - For testability

### Making Changes

1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Run `make fmt vet lint test`
5. Submit PR

### Common Tasks

```bash
# Format code
make fmt

# Run linter
make lint

# Update dependencies
make mod-update

# Generate code
make generate

# Security scan
make security
```

## Scripts

All scripts have been consolidated in `/arxos/scripts/` directory.
See [Scripts Documentation](/scripts/README.md) for details.

## Testing

### Unit Tests
```go
go test ./internal/arxobject
```

### Integration Tests
```go
go test ./tests/...
```

### Load Testing
```bash
go test -bench=. ./internal/handlers
```

## Deployment

### Docker

```bash
# Build image
make docker

# Run container
docker run -p 8080:8080 --env-file .env arxos-server
```

### Kubernetes

See `/deploy/k8s/` for Kubernetes manifests.

### Direct Binary

```bash
make prod
./build/arxos-server-linux-amd64
```

## Monitoring

- Health endpoint: `GET /health`
- Metrics: Prometheus format at `/metrics`
- Logging: Structured JSON logs

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow code style (run `make fmt`)
4. Write tests
5. Submit PR

## License

Proprietary - Arxos Inc.

## Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Contact: support@arxos.io