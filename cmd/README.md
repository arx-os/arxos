# ArxOS Command Line Interface

This directory contains the command-line interface (CLI) for ArxOS, a building operating system with PostGIS spatial database integration.

## Architecture

```
cmd/
└── arx/                    # Main CLI application (thin UX layer)
    ├── main.go            # Entry point and initialization
    ├── cmd_*.go           # Command implementations (UX only)
    └── *.go               # Support files

internal/                   # Business logic services
├── simulation/            # Simulation service
├── services/              # Service layer
│   ├── bim_sync.go       # BIM synchronization
│   ├── export_command.go # Export operations
│   ├── import_command.go # Import operations
│   └── query_service.go  # Database queries
└── [other packages]      # Core business logic
```

## Command Structure

The ArxOS CLI uses [Cobra](https://github.com/spf13/cobra) for command parsing and follows a modular architecture where each major command group has its own file(s).

### Core Commands

#### System Commands
- **`main.go`** - Application entry point, database initialization, PostGIS setup
- **`cmd_install.go`** - System installation and initialization
- **`cmd_health.go`** - System health checks including PostGIS connectivity
- **`cmd_daemon.go`** - Background daemon for file watching and auto-import

#### CRUD Operations
- **`cmd_add.go`** - Add equipment with 3D spatial coordinates
- **`cmd_get.go`** - Retrieve equipment with spatial data
- **`cmd_update.go`** - Update equipment positions and metadata
- **`cmd_remove.go`** - Remove equipment with cascade options
- **`cmd_list.go`** - List equipment with spatial filtering
- **`cmd_trace.go`** - Trace equipment dependencies and relationships

#### Import/Export Pipeline
- **`cmd_import.go`** - Import IFC/BIM files to PostGIS
- **`cmd_export.go`** - Export to multiple formats (IFC, CSV, JSON, BIM)
- **`cmd_convert.go`** - Convert between building data formats

#### Repository Management
- **`cmd_repo_common.go`** - Shared repository types and utilities
- **`cmd_repo_init.go`** - Initialize BIM repository with version control
- **`cmd_repo_clone.go`** - Clone remote repositories
- **`cmd_repo_status.go`** - Repository status with spatial statistics
- **`cmd_repo_sync.go`** - Push/Pull/Diff operations
- **`cmd_repo_history.go`** - Commit history and branch management

#### Query & Analysis
- **`cmd_query.go`** - Spatial queries using PostGIS
- **`cmd_report.go`** - Generate building reports
- **`cmd_visualize.go`** - Create visualizations with spatial data

#### Services
- **`cmd_serve.go`** - REST API server
- **`cmd_watch.go`** - File system monitoring

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
SQLite (Fallback)     → Offline operation, metadata
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
- Fall back to SQLite when PostGIS unavailable

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
- `github.com/mattn/go-sqlite3` - SQLite fallback
- Internal packages for spatial operations, database abstraction

## Performance Considerations

1. **Spatial Indices**: Automatically created for PostGIS tables
2. **Connection Pooling**: Reuse database connections
3. **Batch Operations**: Group multiple operations when possible
4. **Caching**: Local SQLite cache for offline operation
5. **Lazy Loading**: Load spatial data only when needed

## Future Enhancements

- [ ] Real-time spatial tracking with WebSockets
- [ ] Advanced spatial analytics commands
- [ ] Machine learning integration for predictive maintenance
- [ ] AR/VR visualization export
- [ ] Multi-building federation support

## License

See LICENSE file in repository root.

## Contributing

See CONTRIBUTING.md for development guidelines and code standards.