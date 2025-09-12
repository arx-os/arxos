# ArxOS Development Guide

## Prerequisites

- Go 1.21 or higher
- SQLite 3
- Git
- Make (optional but recommended)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/joelpate/arxos.git
cd arxos
```

### 2. Install Dependencies

```bash
go mod download
```

### 3. Build the Project

```bash
# Build all binaries
make build

# Or build individually
go build -o bin/arx ./cmd/arx
go build -o bin/arxos-server ./cmd/arxos-server
go build -o bin/arxd ./cmd/arxd
```

### 4. Run Tests

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run with verbose output
go test -v ./...
```

## Project Structure

```
arxos/
├── cmd/                    # Application entry points
│   ├── arx/               # CLI tool
│   ├── arxos-server/      # API & Web server
│   └── arxd/              # Background daemon
├── internal/              # Private packages
│   ├── api/              # API handlers and services
│   ├── web/              # Web UI (HTMX templates)
│   ├── database/         # Database layer
│   ├── sync/             # Sync engine
│   ├── storage/          # Storage abstraction
│   ├── config/           # Configuration
│   ├── auth/             # Authentication
│   ├── logger/           # Logging
│   └── telemetry/        # Metrics & monitoring
├── pkg/                   # Public packages
│   └── models/           # Core data models
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── test/                  # Integration tests
└── templates/             # HTML templates
```

## Development Workflow

### Running the Server

```bash
# Start the server
./bin/arxos-server -port 8080 -verbose

# Or use air for hot reload (install: go install github.com/cosmtrek/air@latest)
air
```

### Using the CLI

```bash
# Configure CLI for local development
./bin/arx config set mode local
./bin/arx config set cloud.url http://localhost:8080

# Test commands
./bin/arx import test_data/sample.pdf
./bin/arx query "SELECT * FROM equipment"
```

## Architecture Overview

### Technology Choices

#### Why HTMX Instead of React/Vue?

1. **Simplicity**: No build step, no webpack, no node_modules
2. **Performance**: Server-side rendering is faster
3. **Maintainability**: One language (Go) instead of Go + JS
4. **Size**: 14kb HTMX vs 45kb+ for React
5. **SEO**: Works perfectly with search engines

#### Why SQLite?

1. **Embedded**: No separate database server
2. **Performance**: Excellent for read-heavy workloads
3. **Reliability**: Battle-tested, used everywhere
4. **Simplicity**: Zero configuration
5. **Portability**: Single file database

### Key Design Patterns

#### 1. Interface-Driven Design

All services are defined as interfaces:

```go
type BuildingService interface {
    GetBuilding(ctx context.Context, id string) (*models.FloorPlan, error)
    ListBuildings(ctx context.Context, userID string, limit, offset int) ([]*models.FloorPlan, error)
    CreateBuilding(ctx context.Context, building *models.FloorPlan) error
}
```

#### 2. Context Propagation

Always pass context for cancellation and timeout:

```go
func (s *Service) DoWork(ctx context.Context) error {
    // Check if context is cancelled
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
        // Do work
    }
}
```

#### 3. Error Wrapping

Use error wrapping for better debugging:

```go
if err := db.Query(sql); err != nil {
    return fmt.Errorf("failed to query database: %w", err)
}
```

## Adding New Features

### 1. Adding a New API Endpoint

```go
// 1. Define the interface in internal/api/interfaces.go
type NewService interface {
    DoSomething(ctx context.Context, param string) (*Result, error)
}

// 2. Implement the service in internal/api/new_service.go
type NewServiceImpl struct {
    db database.DB
}

func (s *NewServiceImpl) DoSomething(ctx context.Context, param string) (*Result, error) {
    // Implementation
}

// 3. Add handler in internal/api/handlers.go
func (s *Server) handleNewEndpoint(w http.ResponseWriter, r *http.Request) {
    // Handle request
}

// 4. Register route in internal/api/server.go
mux.HandleFunc("/api/v1/new", s.handleNewEndpoint)
```

### 2. Adding a New Web Page

```html
<!-- 1. Create template in internal/web/templates/newpage.html -->
{{template "base" .}}

{{define "content"}}
<div class="space-y-6">
    <!-- Page content with HTMX -->
    <div hx-get="/api/data" hx-trigger="load">
        Loading...
    </div>
</div>
{{end}}
```

```go
// 2. Add handler in internal/web/handlers.go
func (h *Handler) handleNewPage(w http.ResponseWriter, r *http.Request) {
    data := PageData{
        Title: "New Page",
        NavActive: "newpage",
    }
    h.templates.Render(w, "newpage", data)
}

// 3. Register route
mux.HandleFunc("/newpage", h.handleNewPage)
```

### 3. Adding a Database Migration

```go
// internal/database/migrations.go
var migrations = []Migration{
    {
        Version: 4,
        Name: "Add new feature tables",
        Up: `
            CREATE TABLE new_feature (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        `,
        Down: `DROP TABLE IF EXISTS new_feature;`,
    },
}
```

## Testing

### Unit Tests

```go
// service_test.go
func TestService_DoSomething(t *testing.T) {
    // Arrange
    mockDB := &MockDB{}
    service := NewService(mockDB)
    
    // Act
    result, err := service.DoSomething(context.Background(), "param")
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, expected, result)
}
```

### Integration Tests

```go
// integration_test.go
// +build integration

func TestAPIIntegration(t *testing.T) {
    // Start test server
    server := httptest.NewServer(handler)
    defer server.Close()
    
    // Make request
    resp, err := http.Get(server.URL + "/api/v1/buildings")
    assert.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode)
}
```

### HTMX Testing

```javascript
// For HTMX pages, use Playwright or similar
test('building list loads', async ({ page }) => {
    await page.goto('http://localhost:8080/buildings');
    await expect(page.locator('.building-row')).toBeVisible();
});
```

## Code Style

### Go Guidelines

1. Use `gofmt` for formatting
2. Use `golangci-lint` for linting
3. Follow [Effective Go](https://golang.org/doc/effective_go.html)
4. Keep functions small and focused
5. Use meaningful variable names

### HTML/HTMX Guidelines

1. Use semantic HTML
2. Keep HTMX attributes simple
3. Prefer `hx-get` over `hx-post` when possible
4. Use fragments for partial updates
5. Add loading states with `htmx-indicator`

## Debugging

### Enable Debug Logging

```bash
# Set log level
export ARXOS_LOG_LEVEL=debug

# Or use verbose flag
./bin/arxos-server -verbose
```

### Database Debugging

```bash
# Open SQLite CLI
sqlite3 ~/.arxos/arxos.db

# Useful queries
.tables
.schema equipment
SELECT * FROM equipment WHERE status = 'failed';
```

### HTMX Debugging

```javascript
// Enable HTMX logging in browser console
htmx.logAll();

// Watch specific events
document.body.addEventListener('htmx:beforeRequest', (e) => {
    console.log('Request:', e.detail);
});
```

## Performance Optimization

### Database

1. **Indexes**: Add indexes for frequently queried columns
2. **Prepared Statements**: Use for repeated queries
3. **Connection Pooling**: Already handled by database/sql
4. **PRAGMA**: Use SQLite pragmas for performance

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;
```

### Web UI

1. **Template Caching**: Templates are cached in production
2. **Partial Updates**: Use HTMX fragments
3. **Debouncing**: Add delay to search inputs
4. **Compression**: Enable gzip compression

```go
// Enable compression
handler = gziphandler.GzipHandler(handler)
```

## Security Best Practices

1. **Input Validation**: Always validate user input
2. **SQL Injection**: Use parameterized queries
3. **XSS Prevention**: HTML escape all output
4. **CSRF Protection**: Use CSRF tokens for state-changing operations
5. **Rate Limiting**: Already implemented in middleware

## Deployment

### Docker

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o arxos-server ./cmd/arxos-server

FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/arxos-server /arxos-server
EXPOSE 8080
CMD ["/arxos-server"]
```

### Environment Variables

```bash
ARXOS_PORT=8080
ARXOS_STATE_DIR=/var/lib/arxos
ARXOS_LOG_LEVEL=info
ARXOS_MODE=production
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### PR Checklist

- [ ] Tests pass (`go test ./...`)
- [ ] Code is formatted (`go fmt ./...`)
- [ ] Linter passes (`golangci-lint run`)
- [ ] Documentation updated
- [ ] Commits are meaningful

## Common Issues

### Port Already in Use

```bash
# Find process using port
lsof -i:8080

# Kill process
kill -9 <PID>
```

### Template Not Found

Ensure templates are embedded:
```go
//go:embed templates/*.html
var templateFS embed.FS
```

### Database Locked

SQLite can lock with concurrent writes. Use WAL mode:
```sql
PRAGMA journal_mode = WAL;
```

## Resources

- [HTMX Documentation](https://htmx.org/docs/)
- [Go Documentation](https://golang.org/doc/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Tailwind CSS](https://tailwindcss.com/docs)

## Support

- GitHub Issues: https://github.com/joelpate/arxos/issues
- Discord: https://discord.gg/arxos
- Email: dev@arxos.io