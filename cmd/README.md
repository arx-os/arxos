# Arxos CLI Architecture

## Directory Structure

```
arxos/
├── main.go                 # Entry point
├── commands/              # All CLI commands
│   ├── root.go           # Root command setup
│   ├── query/            # AQL query commands
│   │   ├── select.go
│   │   ├── update.go
│   │   ├── validate.go
│   │   └── history.go
│   ├── ingest/           # Data ingestion
│   │   ├── pdf.go
│   │   ├── ifc.go
│   │   ├── lidar.go
│   │   └── watch.go
│   ├── export/           # Export functionality
│   │   ├── ifc.go
│   │   ├── revit.go
│   │   └── json.go
│   ├── validate/         # Field validation
│   │   ├── validate.go
│   │   └── propagate.go
│   ├── analyze/          # Analysis tools
│   │   ├── confidence.go
│   │   ├── orphaned.go
│   │   └── missing.go
│   ├── serve/            # Server operations
│   │   ├── serve.go
│   │   ├── connect.go
│   │   └── stream.go
│   └── ai/               # AI operations
│       ├── detect.go
│       ├── train.go
│       └── scan.go
├── aql/                   # Arxos Query Language
│   ├── parser.go         # AQL parser
│   ├── executor.go       # Query executor
│   ├── scanner.go        # Lexical scanner
│   └── ast.go           # Abstract syntax tree
├── client/               # Backend client
│   ├── client.go        # API client
│   ├── auth.go          # Authentication
│   └── websocket.go     # WebSocket connection
├── config/               # Configuration
│   ├── config.go        # Config management
│   └── defaults.go      # Default settings
├── display/              # Output formatting
│   ├── table.go         # Table display
│   ├── json.go          # JSON output
│   ├── progress.go      # Progress bars
│   └── colors.go        # Color utilities
└── utils/                # Shared utilities
    ├── files.go         # File operations
    ├── validation.go    # Input validation
    └── errors.go        # Error handling
```

## Command Categories

### 1. Query Commands (`query/`)
- Interactive AQL queries
- SQL-like interface for buildings
- Spatial and relationship queries

### 2. Ingest Commands (`ingest/`)
- Import PDF, IFC, DWG files
- LiDAR point cloud processing
- Watch directories for auto-import

### 3. Export Commands (`export/`)
- Export to various formats (IFC, Revit, JSON)
- Sync with external systems (CMMS)
- Backup and restore

### 4. Validation Commands (`validate/`)
- Field validation with photos
- Confidence score updates
- Propagation to related objects

### 5. Analysis Commands (`analyze/`)
- Find low-confidence objects
- Detect orphaned elements
- Identify missing validations

### 6. Server Commands (`serve/`)
- Start local BIM server
- Connect to remote instances
- Stream real-time data

### 7. AI Commands (`ai/`)
- Symbol detection
- Model training
- iPhone scanning

## Development Guidelines

### Adding New Commands

1. Create new file in appropriate `commands/` subdirectory
2. Implement command using cobra pattern
3. Register in `commands/root.go`
4. Add tests in `commands/[category]/[command]_test.go`

### Command Pattern

```go
// commands/query/select.go
package query

import (
    "github.com/spf13/cobra"
    "github.com/arxos/arxos/cmd/aql"
)

var SelectCmd = &cobra.Command{
    Use:   "select [query]",
    Short: "Query ArxObjects using AQL",
    RunE:  runSelect,
}

func runSelect(cmd *cobra.Command, args []string) error {
    // Implementation
    return nil
}
```

## Configuration

Config file location: `~/.arxos/config.yaml`

```yaml
backend:
  url: http://localhost:8080
  token: "auth-token"

display:
  format: table  # table, json, yaml
  color: true

defaults:
  confidence_threshold: 0.7
  validation_required: true
```

## Testing

```bash
# Run all tests
go test ./...

# Run specific category
go test ./commands/query/...

# Integration tests
go test ./tests/integration/...
```