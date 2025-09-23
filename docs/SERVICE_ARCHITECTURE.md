# Service Architecture

## Overview

ArxOS follows a service-oriented architecture where business logic is organized into focused, reusable services. This document describes the service layer that was created during the command consolidation process.

## Service Layer Structure

```
internal/
├── simulation/            # Building simulation service
│   ├── engine.go         # Core simulation engine
│   └── service.go        # Simulation service layer
├── services/             # Command services
│   ├── bim_sync.go       # BIM synchronization service
│   ├── export_command.go # Export operations service
│   ├── import_command.go # Import operations service
│   └── query_service.go  # Database query service
└── [other packages]     # Core business logic
```

## Service Principles

### 1. Single Responsibility
Each service has a single, well-defined responsibility:
- **SimulationService**: Building performance simulation
- **BIMSyncService**: Bidirectional BIM synchronization
- **ExportCommandService**: Data export operations
- **ImportCommandService**: Data import operations
- **QueryService**: Database query operations

### 2. Dependency Injection
Services accept dependencies through constructors:
```go
// Example: QueryService
func NewQueryService(db database.DB) *QueryService {
    return &QueryService{db: db}
}
```

### 3. Interface Segregation
Services implement focused interfaces that can be easily mocked for testing.

### 4. Reusability
Services are designed to be used by multiple consumers:
- CLI commands (`cmd/arx`)
- REST API handlers (`internal/api`)
- Daemon processes (`internal/daemon`)
- Background workers

## Service Details

### SimulationService
**Location**: `internal/simulation/service.go`
**Purpose**: Building performance simulation and analysis

**Key Methods**:
- `ExecuteSimulate(opts SimulateOptions) error` - Run simulations
- `parseSimulationTypes(simulations []string) []SimulationType` - Parse simulation types
- `printSimulationMetrics(result *SimulationResult)` - Display results

**Usage**:
```go
simService := simulation.NewService(db)
opts := simulation.SimulateOptions{
    BuildingID: "building-123",
    Simulations: []string{"occupancy", "energy"},
    SaveResults: true,
}
err := simService.ExecuteSimulate(opts)
```

### BIMSyncService
**Location**: `internal/services/bim_sync.go`
**Purpose**: Bidirectional synchronization between database and BIM files

**Key Methods**:
- `ExecuteSync(opts BIMSyncOptions) error` - Main sync operation
- `syncDatabaseToBIM(opts BIMSyncOptions) error` - DB → BIM sync
- `syncBIMToDatabase(opts BIMSyncOptions) error` - BIM → DB sync
- `convertToSimpleBIM(floorPlan *models.FloorPlan) *bim.SimpleBuilding` - Convert models

**Usage**:
```go
syncService := services.NewBIMSyncService(db)
opts := services.BIMSyncOptions{
    Direction: "db-to-bim",
    BuildingID: "building-123",
    GitRepo: "/path/to/repo",
    AutoCommit: true,
}
err := syncService.ExecuteSync(opts)
```

### ExportCommandService
**Location**: `internal/services/export_command.go`
**Purpose**: Export building data to various formats

**Key Methods**:
- `ExecuteExport(opts ExportCommandOptions) error` - Main export operation
- `exportBIM(building *models.FloorPlan, simResults interface{}, opts ExportCommandOptions) error` - BIM export
- `exportJSON(building *models.FloorPlan, simResults interface{}, opts ExportCommandOptions) error` - JSON export

**Usage**:
```go
exportService := services.NewExportCommandService(db)
opts := services.ExportCommandOptions{
    BuildingID: "building-123",
    Format: "bim",
    OutputFile: "building.bim.txt",
    IncludeIntel: true,
}
err := exportService.ExecuteExport(opts)
```

### ImportCommandService
**Location**: `internal/services/import_command.go`
**Purpose**: Import building data from various formats

**Key Methods**:
- `ExecuteImport(opts ImportCommandOptions) error` - Main import operation
- `importBIM(ctx context.Context, opts ImportCommandOptions) error` - BIM import
- `importPDF(ctx context.Context, opts ImportCommandOptions) error` - PDF import

**Usage**:
```go
importService := services.NewImportCommandService(db)
opts := services.ImportCommandOptions{
    InputFile: "building.bim.txt",
    Format: "bim",
    BuildingID: "building-123",
    ValidateOnly: false,
}
err := importService.ExecuteImport(opts)
```

### QueryService
**Location**: `internal/services/query_service.go`
**Purpose**: Database query operations with spatial support

**Key Methods**:
- `ExecuteQuery(ctx context.Context, opts QueryOptions) (*QueryResults, error)` - Execute queries
- `buildQuery(opts QueryOptions) (string, []interface{}, error)` - Build SQL queries

**Usage**:
```go
queryService := services.NewQueryService(db)
opts := services.QueryOptions{
    Building: "building-123",
    Status: "active",
    Type: "sensor",
    Limit: 100,
}
results, err := queryService.ExecuteQuery(ctx, opts)
```

## CLI Integration

CLI commands (`cmd/arx`) are thin wrappers that:
1. Parse command-line arguments and flags
2. Create appropriate service instances
3. Call service methods with parsed options
4. Handle output formatting and error display

**Example Pattern**:
```go
func runCommand(cmd *cobra.Command, args []string) error {
    // Parse flags
    opts := parseOptions(cmd)
    
    // Connect to database
    db, err := database.NewPostGISConnection(ctx)
    if err != nil {
        return err
    }
    defer db.Close()
    
    // Create service
    service := services.NewService(db)
    
    // Execute operation
    return service.ExecuteOperation(opts)
}
```

## Benefits

### 1. Maintainability
- Single source of truth for each operation
- Changes to business logic only need to be made in one place
- Clear separation between UX (CLI) and business logic (services)

### 2. Testability
- Services can be easily unit tested with mocked dependencies
- CLI commands can be tested independently of business logic
- Integration tests can focus on service interactions

### 3. Reusability
- Services can be used by multiple consumers (CLI, API, daemon)
- Business logic is not tied to specific presentation layers
- Easy to add new interfaces (gRPC, GraphQL, etc.)

### 4. Scalability
- Services can be extracted to separate microservices if needed
- Clear boundaries make it easy to optimize individual services
- Database connections and resources are properly managed

## Migration Notes

The consolidation from `internal/commands` to services involved:

1. **Moving Logic**: Business logic moved from command files to service files
2. **Updating CLI**: CLI commands updated to use services instead of direct logic
3. **Removing Duplication**: Eliminated duplicate code between CLI and internal packages
4. **Standardizing Interfaces**: Created consistent service interfaces and patterns

This migration improves code organization while maintaining all existing functionality.
