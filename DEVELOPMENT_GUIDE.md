# Arxos Development Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Features](#core-features)
4. [Getting Started](#getting-started)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Deployment](#deployment)

## Project Overview

Arxos is a building intelligence platform that enables maintenance teams to track, analyze, and optimize building infrastructure through innovative ASCII visualization and mobile AR capabilities.

### Key Technologies
- **Backend**: Go 1.24.5
- **Database**: SQLite with optional PostgreSQL support
- **Web Framework**: HTMX (no JavaScript build complexity)
- **Mobile**: React Native with ViroReact for AR (future)
- **Authentication**: JWT with refresh tokens

### Production Domains
- **arxos.io** - Production site for customers
- **arxos.dev** - Internal production site for development

## Architecture

### Directory Structure
```
arxos/
├── cmd/                    # Application entry points
│   ├── arx/               # Main CLI application
│   └── arxd/              # Daemon/server
├── internal/              # Private application code
│   ├── api/              # API server and handlers
│   ├── ascii/            # ASCII floor plan rendering
│   ├── auth/             # Authentication services
│   ├── database/         # Database interfaces
│   ├── pdf/              # PDF parsing
│   ├── search/           # Search engine
│   ├── services/         # Business logic services
│   └── web/              # Web UI handlers
├── pkg/                   # Public packages
│   └── models/           # Data models
├── templates/            # HTML templates
│   ├── layouts/         # Base layouts
│   ├── pages/           # Full pages
│   └── partials/        # HTMX fragments
└── mobile/               # React Native app (future)
```

### Core Components

#### 1. Authentication System
- JWT-based authentication with refresh tokens
- Session management with automatic cleanup
- Role-based access control (RBAC)

#### 2. PDF to ASCII Conversion
- Parses building floor plans from PDFs
- Converts to internal FloorPlan model
- Generates ASCII art visualization

#### 3. HTMX Web Interface
- Server-side rendering with Go templates
- Dynamic updates without full page reloads
- No JavaScript build step required

#### 4. API Services
- RESTful API for all operations
- Building CRUD operations
- Equipment and room management
- Sync capabilities for offline support

## Core Features

### Implementation Status

#### ✅ **Fully Implemented**
1. **CLI Tools** (95% complete)
   - 16 commands for building management
   - Git-like version control
   - ASCII rendering and queries
   - PDF import capabilities

2. **Database Layer** (90% complete)
   - SQLite with spatial indexing
   - Full CRUD operations
   - Migration system
   - Connection graph modeling

#### ⚠️ **Partially Implemented**
3. **Authentication System** (60% complete)
   - Basic JWT authentication works
   - Session management structure in place
   - TODO: Token refresh, proper logout

4. **ASCII Visualization** (70% complete)
   - Basic floor plan rendering works
   - Equipment markers implemented
   - TODO: Advanced layer system, physics simulation

5. **Web Interface** (40% complete)
   - HTMX templates created
   - Basic routing established
   - TODO: Most handlers need implementation

6. **API Endpoints** (50% complete)
   - Routes defined
   - Middleware implemented
   - TODO: Many handlers return "Not implemented"

#### ❌ **Not Started**
7. **Mobile AR Application** (5% complete)
   - Directory structure only
   - React Native setup documented

8. **Sync Engine** (30% complete)
   - Basic structure present
   - TODO: Core sync logic missing

## Getting Started

### Prerequisites
```bash
# Install Go 1.24.5 or later
brew install go

# Install development tools
go install github.com/cosmtrek/air@latest  # Hot reload
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

### Initial Setup
```bash
# Clone repository
git clone https://github.com/joelpate/arxos.git
cd arxos

# Install dependencies
go mod download

# Initialize database
go run cmd/arx/main.go db init

# Run tests
go test ./...
```

### Running the Application

#### Development Mode
```bash
# Start with hot reload
air

# Or manually
go run cmd/arxd/main.go

# Access at http://localhost:8080
```

#### Production Mode
```bash
# Build
go build -o arxd cmd/arxd/main.go

# Run with environment config
ARXOS_ENV=production ./arxd
```

## Development Workflow

### Adding a New Feature

1. **Create feature branch**
```bash
git checkout -b feature/your-feature
```

2. **Update models if needed**
```go
// pkg/models/your_model.go
type YourModel struct {
    ID        string    `json:"id"`
    Name      string    `json:"name"`
    CreatedAt time.Time `json:"created_at"`
}
```

3. **Add service layer**
```go
// internal/services/your_service.go
type YourService struct {
    db database.DB
}

func (s *YourService) Create(ctx context.Context, model *models.YourModel) error {
    // Implementation
}
```

4. **Create API handlers**
```go
// internal/api/your_handlers.go
func (s *Server) handleYourEndpoint(w http.ResponseWriter, r *http.Request) {
    // Handle request
}
```

5. **Add web UI if needed**
```go
// internal/web/your_handler.go
func (h *Handler) HandleYourPage(w http.ResponseWriter, r *http.Request) {
    // Render template
}
```

6. **Write tests**
```go
// internal/services/your_service_test.go
func TestYourService_Create(t *testing.T) {
    // Test implementation
}
```

### Code Style Guidelines
- Use `gofmt` for formatting
- Follow Go idioms and best practices
- Write clear, self-documenting code
- Add comments for exported functions
- Keep functions small and focused

## Testing

### Running Tests
```bash
# All tests
go test ./...

# With coverage
go test -cover ./...

# Specific package
go test ./internal/ascii/...

# Verbose output
go test -v ./...
```

### Test Structure
```go
func TestFeatureName_MethodName(t *testing.T) {
    // Arrange
    service := NewService()
    
    // Act
    result, err := service.Method()
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, expected, result)
}
```

### Integration Tests
Located in `internal/api/server_test.go`, these test the full API flow including:
- Authentication flow
- Building CRUD operations
- PDF to ASCII conversion

## Deployment

### Environment Configuration
```bash
# .env.production
ARXOS_ENV=production
ARXOS_PORT=8080
ARXOS_DB_PATH=/var/lib/arxos/data.db
ARXOS_JWT_SECRET=your-secret-key
ARXOS_DOMAIN=arxos.io
```

### Docker Deployment
```dockerfile
# Dockerfile
FROM golang:1.24.5-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o arxd cmd/arxd/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/arxd .
COPY --from=builder /app/templates ./templates
CMD ["./arxd"]
```

### Database Migrations
```bash
# Run migrations
go run cmd/arx/main.go db migrate

# Rollback
go run cmd/arx/main.go db rollback
```

### Monitoring
- Health endpoint: `/health`
- Ready endpoint: `/ready`
- Metrics: `/metrics` (Prometheus format)

## Current Development Priorities

### Immediate (Week 1)
1. Complete authentication system (token refresh, logout)
2. Implement missing API handlers
3. Fix security issues (remove hard-coded credentials)
4. Address failing tests

### Short-term (Weeks 2-4)
1. Complete web interface handlers
2. Implement sync engine logic
3. Add comprehensive integration tests
4. Production deployment configuration

### Medium-term (Months 2-3)
1. Mobile AR application development
2. Advanced ABIM layer system
3. Performance optimization
4. Multi-tenant support

## Troubleshooting

### Common Issues

1. **Database locked error**
   - Ensure only one instance is running
   - Check for stale lock files

2. **Template not found**
   - Verify templates directory exists
   - Check file paths in templates.go

3. **Authentication failures**
   - Verify JWT secret is set
   - Check token expiration times
   - Note: Token refresh not fully implemented

4. **ASCII rendering issues**
   - Verify floor plan bounds
   - Check equipment coordinates
   - Review scale calculations
   - Known issue: Label truncation in small spaces

5. **"Not Implemented" API errors**
   - Many handlers are still TODO
   - Check DEVELOPMENT_GUIDE.md for status

### Debug Mode
```bash
# Enable debug logging
ARXOS_LOG_LEVEL=debug ./arxd

# Use delve debugger
dlv debug cmd/arxd/main.go
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Commit Message Format
```
type(scope): description

- Detailed change 1
- Detailed change 2

Fixes #issue-number
```

Types: feat, fix, docs, style, refactor, test, chore

## Resources

- [Go Documentation](https://golang.org/doc/)
- [HTMX Documentation](https://htmx.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

## License

Copyright © 2024 Arxos. All rights reserved.