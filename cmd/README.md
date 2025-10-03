# ArxOS Command Line Interface

This directory contains the command-line interface (CLI) for ArxOS, a building operating system with PostGIS spatial database integration.

## Architecture

```
cmd/
└── arx/                    # Main CLI application entry point
    └── main.go            # Application entry point and initialization

internal/cli/               # CLI implementation (Clean Architecture)
├── app.go                 # CLI application setup and DI container
├── cli.go                 # CLI utilities and validation helpers
├── context.go             # Service context for dependency injection
├── errors.go              # Sophisticated error handling
└── commands/              # Command implementations
    ├── system.go          # System management (install, health, migrate)
    ├── crud.go            # CRUD operations (add, get, update, remove)
    ├── repository.go      # Repository management (init, clone, status, sync)
    ├── import_export.go   # Import/Export operations (import, export, convert)
    ├── component.go       # Component management commands
    ├── services.go        # Service commands (serve, watch)
    ├── utility.go         # Utility commands (query, trace, visualize, report)
    ├── cadtui.go         # CAD Terminal User Interface
    └── serve.go          # HTTP server command
```

## Command Structure

The ArxOS CLI uses [Cobra](https://github.com/spf13/cobra) for command parsing and follows Clean Architecture principles with proper dependency injection and service context.

### Core Commands

#### System Commands (`system.go`)
- **`install`** - System installation and initialization
- **`health`** - System health checks including PostGIS connectivity
- **`migrate`** - Database migration commands

#### CRUD Operations (`crud.go`)
- **`add`** - Add building components (equipment, rooms, floors)
- **`get`** - Retrieve building component details
- **`update`** - Update building components
- **`remove`** - Remove building components

#### Repository Management (`repository.go`)
- **`repo init`** - Initialize building repository with version control
- **`repo clone`** - Clone remote repositories
- **`repo status`** - Repository status with spatial statistics
- **`repo commit`** - Commit changes to repository
- **`repo push`** - Push changes to remote
- **`repo pull`** - Pull changes from remote

#### Import/Export Pipeline (`import_export.go`)
- **`import`** - Import IFC/BIM files to PostGIS
- **`export`** - Export to multiple formats (IFC, CSV, JSON, BIM)
- **`convert`** - Convert between building data formats

#### Component Management (`component.go`)
- **`component`** - Component management commands

#### Services (`services.go`)
- **`serve`** - REST API server
- **`watch`** - File system monitoring

#### Utility Commands (`utility.go`)
- **`query`** - Spatial queries using PostGIS
- **`trace`** - Trace building component connections
- **`visualize`** - Generate building visualizations
- **`report`** - Generate building reports
- **`version`** - Print version information

#### Interactive Interface (`cadtui.go`)
- **`cadtui`** - Computer-Aided Design Terminal User Interface

## PostGIS Integration

ArxOS leverages PostGIS for millimeter-precision spatial tracking:

### Spatial Features
- **SRID 900913**: Custom coordinate system for building-local measurements
- **3D Coordinates**: POINTZ geometry for X, Y, Z positioning
- **Millimeter Precision**: All measurements in millimeters
- **Spatial Indices**: Automatic indexing for performance
- **Coverage Tracking**: Monitor scanned vs unscanned areas

### Database Architecture
```go
// Hybrid database pattern
PostGIS (Primary)     → Spatial queries, 3D coordinates
PostGIS Only          → Spatial operations, metadata
```

## Command Examples

### Basic Operations
```bash
# System setup
arx install --with-postgis
arx health --check postgis

# Import building model
arx import ifc building.ifc --building-id ARXOS-001

# Add equipment with 3D coordinates
arx add HVAC-001 --type "Air Handler" \
  --location "1000,2000,2700" \  # X,Y,Z in millimeters
  --room 101

# Spatial query
arx query equipment --near "2000,2000,2700" --radius 5000
```

### Repository Operations
```bash
# Initialize repository
arx repo init "MyBuilding"

# Clone remote repository
arx repo clone https://github.com/org/building.arxos

# Commit changes
arx repo commit -m "Updated HVAC positions on floor 3"

# Check status
arx repo status
```

### Visualization
```bash
# Generate dashboard
arx visualize dashboard --output dashboard.html

# Energy heatmap
arx visualize energy --floor 1 --format svg

# Equipment status
arx visualize status --building ARXOS-001
```

## File Organization

### Command Naming Convention
- `cmd_<command>.go` - Single command implementation
- `cmd_<group>_<subcommand>.go` - Grouped command implementation
- `cmd_<group>_common.go` - Shared utilities for command group

### Code Structure
Each command file typically contains:
1. Command definition (`cobra.Command`)
2. Flag definitions
3. `init()` function for flag registration
4. `RunE` function that calls appropriate service
5. Service integration (no business logic in CLI)

**Important**: CLI commands are thin UX layers that delegate to services in `internal/` packages.

## Development Guidelines

### Adding New Commands

1. Create a new file `cmd_<name>.go`
2. Define the command structure:
```go
var myCmd = &cobra.Command{
    Use:   "mycommand",
    Short: "Brief description",
    Long:  `Detailed description with PostGIS features`,
    RunE:  runMyCommand,
}
```

3. Add to parent command in `main.go` or appropriate parent file
4. Implement PostGIS integration where applicable

### PostGIS Integration Pattern
```go
// Get spatial database connection
if hybridDB != nil {
    if spatialDB, err := hybridDB.GetSpatialDB(); err == nil {
        // Perform spatial operations
        position := spatial.Point3D{X: 1000, Y: 2000, Z: 2700}
        spatialDB.UpdateEquipmentPosition(id, position, confidence, source)
    }
}
```

### Error Handling
- Use `RunE` for commands that can return errors
- Provide clear error messages with context
- Log warnings for non-critical failures
- Requires PostGIS for spatial operations

## Testing

```bash
# Build the CLI
go build -o arx ./cmd/arx

# Run tests
go test ./cmd/arx/...

# Test individual commands
./arx <command> --help
```

## Configuration

The CLI reads configuration from:
1. Command-line flags (highest priority)
2. Environment variables (`ARX_*`, `POSTGIS_*`)
3. Configuration file (`.arxos/config.yaml`)
4. Default values

### Environment Variables
```bash
# PostGIS configuration
export POSTGIS_HOST=localhost
export POSTGIS_PORT=5432
export POSTGIS_DB=arxos
export POSTGIS_USER=arxos
export POSTGIS_PASSWORD=secret

# Application settings
export ARX_LOG_LEVEL=debug
export ARX_STATE_DIR=.arxos
```

## Dependencies

Key dependencies managed via `go.mod`:
- `github.com/spf13/cobra` - Command-line interface
- `github.com/lib/pq` - PostgreSQL/PostGIS driver
- `github.com/lib/pq` - PostGIS connection
- Internal packages for spatial operations, database abstraction

## Performance Considerations

1. **Spatial Indices**: Automatically created for PostGIS tables
2. **Connection Pooling**: Reuse database connections
3. **Batch Operations**: Group multiple operations when possible
4. **Caching**: Local cache for performance optimization
5. **Lazy Loading**: Load spatial data only when needed

## Future Enhancements

- [ ] Real-time spatial tracking with WebSockets
- [ ] Advanced spatial analytics commands
- [ ] Machine learning integration for predictive maintenance
- [ ] AR/VR visualization export
- [ ] Multi-building federation support

## License

See LICENSE file in repository root.

## Development

See CONTRIBUTING.md for development guidelines and code standards.