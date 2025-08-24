# Arxos CLI Development Guide

## Architecture Overview

The CLI is organized into clear, modular components:

```
arxos/
├── main.go              # Entry point (minimal)
├── commands/            # All CLI commands (organized by category)
├── aql/                 # Query language parser and executor
├── client/              # Backend API client
├── config/              # Configuration management
├── display/             # Output formatting (tables, JSON, etc.)
└── utils/               # Shared utilities
```

## Adding New Commands

### 1. Create Command File

Create new file in appropriate category:
```go
// commands/ingest/pdf.go
package ingest

import (
    "github.com/spf13/cobra"
)

func init() {
    pdfCmd.Flags().StringP("confidence", "c", "0.7", "confidence threshold")
}

func runPDFIngest(cmd *cobra.Command, args []string) error {
    // Implementation
    return nil
}
```

### 2. Register with Parent

Add to parent command in category file:
```go
// commands/ingest/ingest.go
func init() {
    IngestCmd.AddCommand(pdfCmd)  // Add your new command
}
```

### 3. Test Command

```bash
go run main.go ingest pdf --help
go run main.go ingest pdf floor-plan.pdf
```

## AQL (Arxos Query Language)

The query language follows SQL-like syntax with spatial extensions:

### Query Types
- `SELECT` - Query objects
- `UPDATE` - Modify properties
- `VALIDATE` - Mark as field-validated
- `HISTORY` - View versions
- `DIFF` - Compare versions

### Spatial Operators
- `NEAR` - Find objects within distance
- `WITHIN` - Objects inside boundary
- `CONNECTED_TO` - Relationship queries

### Examples
```sql
-- Find all walls on floor 3
SELECT * FROM building:hq:floor:3 WHERE type = 'wall'

-- Find low-confidence objects
SELECT * FROM building:* WHERE confidence < 0.7

-- Validate with evidence
VALIDATE wall_123 WITH photo='wall.jpg', notes='Verified on-site'

-- Spatial query
SELECT * FROM building:* WHERE geometry NEAR '100,200,50'
```

## Client-Backend Communication

### REST API
```go
client := client.GetClient()
result, err := client.ExecuteQuery(query)
```

### WebSocket (for streaming)
```go
ws, err := client.StreamLiDAR()
ws.Send(pointCloudData)
```

## Configuration

### User Config: `~/.arxos/config.yaml`
```yaml
backend:
  url: http://localhost:8080
  token: "your-auth-token"

display:
  format: table
  color: true

defaults:
  confidence_threshold: 0.7
```

### Environment Variables
```bash
export ARXOS_BACKEND_URL=http://production:8080
export ARXOS_BACKEND_TOKEN=secret-token
```

## Display Formatting

### Table Output (default)
```go
table := display.NewTableDisplay()
table.SetHeaders("ID", "Type", "Confidence")
table.AddRow("wall_123", "wall", "85%")
table.Render()
```

### JSON Output
```bash
arxos query select "..." --format=json
```

### Progress Bars
```go
progress := display.NewProgress(100)
for i := 0; i < 100; i++ {
    progress.Update(i)
}
```

## Testing

### Unit Tests
```go
// commands/query/select_test.go
func TestSelectCommand(t *testing.T) {
    cmd := selectCmd
    cmd.SetArgs([]string{"* FROM building:*"})
    err := cmd.Execute()
    assert.NoError(t, err)
}
```

### Integration Tests
```bash
# Test full pipeline
go test ./tests/integration/...
```

## Common Patterns

### Error Handling
```go
if err != nil {
    return fmt.Errorf("failed to ingest: %w", err)
}
```

### Validation
```go
if len(args) == 0 {
    return fmt.Errorf("filename required")
}
```

### Progress Feedback
```go
fmt.Fprintf(os.Stderr, "Processing %d objects...\n", count)
```

## Dependencies

- `cobra` - Command structure
- `viper` - Configuration
- `color` - Terminal colors
- Standard library for most functionality

## Build and Release

```bash
# Development build
go build -o arxos-cli

# Production build with version info
go build -ldflags "-X main.Version=1.0.0 -X main.BuildDate=$(date -u +%Y-%m-%d)" -o arxos

# Cross-compile
GOOS=linux GOARCH=amd64 go build -o arxos-linux
GOOS=darwin GOARCH=arm64 go build -o arxos-mac
GOOS=windows GOARCH=amd64 go build -o arxos.exe
```

## Next Steps

1. **Implement AQL Executor** - Connect parser to backend
2. **Add Progress Indicators** - For long operations
3. **Implement Streaming** - WebSocket for real-time
4. **Add Shell Completion** - Bash/Zsh completion
5. **Create Plugin System** - For extensions

## Key Files to Implement

Priority implementations needed:
- [ ] `aql/executor.go` - Execute parsed queries
- [ ] `commands/query/interactive.go` - REPL mode
- [ ] `client/websocket.go` - WebSocket client
- [ ] `commands/ai/detect.go` - Symbol detection
- [ ] `commands/serve/serve.go` - Local server mode