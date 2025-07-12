# Arxos CMMS Integration Package

This package provides CMMS (Computerized Maintenance Management System) integration functionality for the Arxos platform. It handles connections to external CMMS systems, data synchronization, and maintenance workflow management.

## Architecture

The package is organized into the following structure:

```
arx-cmms/
├── cmd/cmms-service/     # Standalone CMMS service
├── internal/
│   ├── connector/        # CMMS connection management
│   ├── models/          # Internal database models
│   └── sync/            # Data synchronization logic
├── pkg/
│   ├── cmms/            # Public API for CMMS operations
│   └── models/          # Public models for external use
└── go.mod               # Go module definition
```

## Features

### CMMS Connection Management
- Support for multiple CMMS systems (Upkeep, Fiix, custom)
- Authentication methods: API Key, Basic Auth, OAuth2
- Connection testing and validation
- Configurable sync intervals

### Data Synchronization
- Maintenance schedules sync
- Work orders sync
- Equipment specifications sync
- Field mapping and transformation
- Error handling and retry logic

### Maintenance Workflow
- Task management and tracking
- Asset lifecycle management
- Warranty tracking
- Replacement planning
- Cost tracking and reporting

## Usage

### As a Library

The package can be used as a library in the main Arxos backend:

```go
import (
    "arx-cmms/pkg/cmms"
    "arx-cmms/pkg/models"
)

// Initialize CMMS client
client := cmms.NewClient(db)

// List CMMS connections
connections, err := client.ListConnections()

// Test a connection
err := client.TestConnection(connectionID)

// Sync data
err := client.SyncConnection(ctx, connectionID, "schedules")
```

### As a Standalone Service

The package can also run as a standalone service:

```bash
cd cmd/cmms-service
go run main.go
```

The service will:
- Connect to the database
- Start the sync scheduler
- Run background sync operations
- Handle CMMS API interactions

## Configuration

The service uses environment variables for configuration:

- `DATABASE_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Logging level (debug, info, warn, error)
- `SYNC_INTERVAL`: Default sync interval in minutes

## API Endpoints

The package provides the following API endpoints when used with the main backend:

### CMMS Connections
- `GET /cmms/connections` - List all connections
- `GET /cmms/connections/{id}` - Get connection details
- `POST /cmms/connections` - Create new connection
- `PUT /cmms/connections/{id}` - Update connection
- `DELETE /cmms/connections/{id}` - Delete connection
- `POST /cmms/connections/{id}/test` - Test connection
- `POST /cmms/connections/{id}/sync` - Manual sync

### Maintenance Data
- `GET /maintenance/schedules` - Get maintenance schedules
- `GET /maintenance/work-orders` - Get work orders
- `GET /maintenance/equipment-specs` - Get equipment specifications
- `GET /maintenance/tasks` - Get maintenance tasks
- `POST /maintenance/tasks` - Create maintenance task
- `PUT /maintenance/tasks/{id}` - Update maintenance task

### Sync Management
- `GET /cmms/connections/{id}/sync-logs` - Get sync logs
- `POST /cmms/connections/{id}/sync` - Trigger manual sync

## Database Schema

The package requires the following database tables:

- `cmms_connections` - CMMS system connections
- `cmms_mappings` - Field mappings between Arxos and CMMS
- `maintenance_schedules` - Maintenance schedules from CMMS
- `work_orders` - Work orders from CMMS
- `equipment_specifications` - Equipment specs from CMMS
- `cmms_sync_logs` - Sync operation logs

## Development

### Building

```bash
# Build the package
go build ./...

# Build the standalone service
go build ./cmd/cmms-service

# Run tests
go test ./...
```

### Testing

The package includes comprehensive tests for:
- Connection management
- Data synchronization
- Error handling
- API endpoints

Run tests with:
```bash
go test ./... -v
```

## Integration with Main Backend

The main Arxos backend imports this package and uses it to:

1. **Initialize CMMS client** in `main.go`
2. **Handle API requests** through the handlers in `handlers/cmms.go`
3. **Access CMMS functionality** through the public API
4. **Manage database operations** using the provided models

## Migration from Previous Implementation

This package refactors the previous CMMS functionality that was embedded in the main backend:

### Moved Components
- CMMS connector service (`services/cmms_connector.go` → `internal/connector/`)
- CMMS models (`models/models.go` → `internal/models/` and `pkg/models/`)
- Sync logic (new `internal/sync/` package)
- Public API (new `pkg/cmms/` package)

### Benefits
- **Separation of concerns**: CMMS logic is isolated
- **Reusability**: Can be used as a standalone service
- **Maintainability**: Clear package structure
- **Testability**: Easier to test individual components
- **Scalability**: Can be deployed independently

## Future Enhancements

- Support for additional CMMS systems
- Real-time sync via webhooks
- Advanced data transformation rules
- Bulk data import/export
- Performance monitoring and metrics
- Multi-tenant support
