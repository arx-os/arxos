# Arxos Construction Management Service

A Go-based construction project management service built with Chi router, designed for performance-critical construction project management features backed by SVGX BIM.

## Features

- **Project Management**: Create, manage, and track construction projects
- **Scheduling**: Gantt charts and critical path analysis
- **Document Management**: Upload, version, and manage construction documents
- **Quality Control**: Inspection workflows and approval processes
- **Safety Management**: Incident reporting and compliance tracking
- **Reporting**: Analytics and dashboard functionality
- **SVGX Integration**: BIM markup synchronization and behavior integration

## Technology Stack

- **Language**: Go 1.21+
- **Web Framework**: Chi router
- **ORM**: GORM/SQLC
- **Database**: PostgreSQL + PostGIS (production), SQLite (edge/offline)
- **SVGX Integration**: Custom Go package (`pkg/svgxbridge`)
- **Authentication**: JWT (via ArxAuth)
- **Testing**: Go test, testify

## Directory Structure

```
arxos/services/construction/
├── cmd/
│   └── main.go                       # Application entry point
├── api/                              # HTTP route handlers
│   ├── projects.go                   # Project management API
│   ├── schedules.go                  # Scheduling and Gantt charts
│   ├── documents.go                  # Document management
│   ├── inspections.go                # Quality control and inspections
│   ├── safety.go                     # Safety management
│   └── reporting.go                  # Analytics and reporting
├── internal/
│   ├── core/                         # Core construction logic
│   ├── models/                       # Data models
│   ├── templates/                    # Construction templates
│   └── config/                       # Configuration
├── pkg/
│   └── svgxbridge/                   # SVGX BIM integrations
├── tests/                            # Test suites
├── go.mod                            # Go module definition
└── README.md                         # Service documentation
```

## Quick Start

1. **Navigate to the service directory**:
   ```bash
   cd arxos/services/construction
   ```

2. **Install dependencies**:
   ```bash
   go mod tidy
   ```

3. **Run the service**:
   ```bash
   go run ./cmd/main.go
   ```

4. **Test the API**:
   ```bash
   curl http://localhost:8080/api/v1/projects
   ```

## Development

### Running Tests
```bash
go test ./... -v
```

### Building
```bash
go build ./cmd/main.go
```

### Linting
```bash
golangci-lint run
```

## API Endpoints

- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/schedules` - List schedules
- `GET /api/v1/schedules/{id}/gantt` - Get Gantt chart
- `GET /api/v1/documents` - List documents
- `GET /api/v1/inspections` - List inspections
- `GET /api/v1/safety` - List safety incidents
- `GET /api/v1/reporting/dashboard` - Get dashboard data

## Environment Variables

- `PORT` - Server port (default: 8080)
- `DATABASE_URL` - Database connection string
- `LOG_LEVEL` - Logging level (default: info)
- `ENVIRONMENT` - Environment (development/production)
- `SVGX_ENDPOINT` - SVGX engine endpoint

## SVGX Integration

The service includes a dedicated `pkg/svgxbridge` package for SVGX BIM integrations:

- Syncing construction progress with SVGX markups
- Validating as-built vs design drawings
- Injecting safety or QA overlays in real-time
- Triggering logic updates from project status changes

## Contributing

1. Follow Go best practices and conventions
2. Write tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass before submitting changes
