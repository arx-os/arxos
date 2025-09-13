# ArxOS Developer Guide

## Overview

ArxOS (Augmented Reality Extended Operating System) is a comprehensive building management platform with AR visualization capabilities. This guide provides developers with everything needed to understand, contribute to, and extend the ArxOS platform.

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │   Web Client    │    │   CLI Tools     │
│   (React Native)│    │   (React)       │    │   (Go)          │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │       API Gateway        │
                    │     (Go + Chi Router)    │
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│  Auth Service   │    │ Building Service │    │ Telemetry      │
│                 │    │                 │    │ Service        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      SQLite Database     │
                    └─────────────────────────────┘
```

### Core Technologies

- **Backend**: Go 1.24+ with Chi router
- **Database**: SQLite with modernc.org/sqlite driver
- **Mobile**: React Native with ViroReact for AR
- **Authentication**: JWT with refresh tokens
- **Observability**: Prometheus metrics, distributed tracing
- **Documentation**: OpenAPI/Swagger 3.0

## Getting Started

### Prerequisites

- Go 1.24 or higher
- Node.js 18+ (for mobile development)
- Git
- SQLite3

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/arx-os/arxos.git
   cd arxos
   ```

2. **Install Go dependencies**
   ```bash
   go mod download
   ```

3. **Build the server**
   ```bash
   go build ./cmd/arxos-server
   ```

4. **Run the development server**
   ```bash
   ./arxos-server --verbose
   ```

5. **Access the services**
   - API: http://localhost:8080/api/v1/
   - Documentation: http://localhost:8080/docs/
   - Metrics: http://localhost:9090/metrics
   - Dashboard: http://localhost:8090/

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Server Configuration
PORT=8080
DATABASE_PATH=./data/arxos.db
LOG_LEVEL=debug

# Security
JWT_SECRET=your-secret-key-here
JWT_EXPIRES_IN=24h
REFRESH_TOKEN_EXPIRES_IN=7d

# Telemetry
TELEMETRY_ENABLED=true
METRICS_PORT=9090
DASHBOARD_PORT=8090

# External Services
API_BASE_URL=http://localhost:8080
```

## API Development

### Creating New Endpoints

1. **Define the handler function**
   ```go
   // internal/api/handlers/example_handler.go
   func (h *Handler) HandleExample(w http.ResponseWriter, r *http.Request) {
       // Implementation
   }
   ```

2. **Add route to router**
   ```go
   // cmd/arxos-server/router.go
   r.Route("/examples", func(r chi.Router) {
       r.Get("/", h.HandleListExamples)
       r.Post("/", h.HandleCreateExample)
       r.Get("/{id}", h.HandleGetExample)
   })
   ```

3. **Add Swagger documentation**
   ```go
   // handleExample godoc
   //  @Summary      Get example
   //  @Description  Get example by ID
   //  @Tags         Examples
   //  @Accept       json
   //  @Produce      json
   //  @Param        id   path      string  true  "Example ID"
   //  @Success      200  {object}  Example
   //  @Failure      404  {object}  ErrorResponse
   //  @Router       /api/v1/examples/{id} [get]
   func (h *Handler) HandleGetExample(w http.ResponseWriter, r *http.Request) {
       // Implementation
   }
   ```

### Authentication & Authorization

ArxOS uses JWT-based authentication with role-based access control:

```go
// Example protected endpoint
func (h *Handler) ProtectedEndpoint(w http.ResponseWriter, r *http.Request) {
    // Get user from context (added by auth middleware)
    user := middleware.GetUser(r)
    if user == nil {
        respondError(w, http.StatusUnauthorized, "Authentication required")
        return
    }
    
    // Check user role
    if user.Role != "admin" {
        respondError(w, http.StatusForbidden, "Admin access required")
        return
    }
    
    // Implementation
}
```

### Error Handling

Consistent error responses using standardized format:

```go
type ErrorResponse struct {
    Error   string                 `json:"error"`
    Details map[string]interface{} `json:"details,omitempty"`
    Code    string                 `json:"code,omitempty"`
}

func respondError(w http.ResponseWriter, status int, message string) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(ErrorResponse{
        Error: message,
        Code:  fmt.Sprintf("ERR_%d", status),
    })
}
```

## Database Operations

### Models

Define models in `pkg/models/`:

```go
// pkg/models/example.go
type Example struct {
    ID          string    `json:"id" db:"id"`
    Name        string    `json:"name" db:"name"`
    Description string    `json:"description" db:"description"`
    CreatedAt   time.Time `json:"created_at" db:"created_at"`
    UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}
```

### Database Service

Implement database operations in service layer:

```go
// internal/api/example_service.go
type ExampleService interface {
    CreateExample(ctx context.Context, example *models.Example) error
    GetExample(ctx context.Context, id string) (*models.Example, error)
    ListExamples(ctx context.Context, limit, offset int) ([]*models.Example, error)
    UpdateExample(ctx context.Context, example *models.Example) error
    DeleteExample(ctx context.Context, id string) error
}

type ExampleServiceImpl struct {
    db database.Database
}

func (s *ExampleServiceImpl) CreateExample(ctx context.Context, example *models.Example) error {
    query := `
        INSERT INTO examples (id, name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    `
    _, err := s.db.ExecContext(ctx, query, 
        example.ID, example.Name, example.Description, 
        example.CreatedAt, example.UpdatedAt)
    return err
}
```

## Testing

### Unit Tests

```go
// internal/api/example_service_test.go
func TestExampleService_CreateExample(t *testing.T) {
    // Setup
    db := setupTestDB(t)
    service := NewExampleService(db)
    
    example := &models.Example{
        ID:          "test-123",
        Name:        "Test Example",
        Description: "Test description",
        CreatedAt:   time.Now(),
        UpdatedAt:   time.Now(),
    }
    
    // Execute
    err := service.CreateExample(context.Background(), example)
    
    // Assert
    assert.NoError(t, err)
    
    // Verify
    retrieved, err := service.GetExample(context.Background(), example.ID)
    assert.NoError(t, err)
    assert.Equal(t, example.Name, retrieved.Name)
}
```

### Integration Tests

```go
// cmd/arxos-server/integration_test.go
func TestAPI_Examples(t *testing.T) {
    // Setup test server
    server := setupTestServer(t)
    defer server.Close()
    
    client := &http.Client{}
    
    // Test create example
    payload := `{"name": "Test", "description": "Test description"}`
    req, _ := http.NewRequest("POST", server.URL+"/api/v1/examples", 
        strings.NewReader(payload))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("Authorization", "Bearer "+getTestToken())
    
    resp, err := client.Do(req)
    assert.NoError(t, err)
    assert.Equal(t, http.StatusCreated, resp.StatusCode)
}
```

### Running Tests

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Run specific package tests
go test ./internal/api/...

# Run integration tests
go test ./cmd/arxos-server/ -tags=integration
```

## Mobile Development

### AR Integration

The mobile app uses ViroReact for AR capabilities:

```typescript
// mobile/src/components/ar/ARScene.tsx
import { ViroARScene, ViroBox, ViroNode } from 'react-viro';

const ARFloorPlanScene: React.FC = () => {
  const { arObjects } = useAR();
  
  return (
    <ViroARScene>
      {arObjects.map((object) => (
        <ViroNode key={object.id} position={object.position}>
          <ViroBox
            scale={object.scale}
            materials={[object.material]}
            onTap={() => handleObjectTap(object)}
          />
        </ViroNode>
      ))}
    </ViroARScene>
  );
};
```

### State Management

Using React Context for global state:

```typescript
// mobile/src/contexts/ARContext.tsx
interface ARContextType {
  isAREnabled: boolean;
  arObjects: ARObject[];
  enableAR: () => Promise<void>;
  loadFloorPlan: (id: string) => Promise<void>;
}

export const ARProvider: React.FC = ({ children }) => {
  const [isAREnabled, setIsAREnabled] = useState(false);
  const [arObjects, setArObjects] = useState<ARObject[]>([]);
  
  // Implementation
  
  return (
    <ARContext.Provider value={value}>
      {children}
    </ARContext.Provider>
  );
};
```

## Observability

### Metrics

Add custom metrics using the telemetry package:

```go
import "github.com/joelpate/arxos/internal/telemetry"

// Record a metric
telemetry.RecordMetric("api_requests_total", 1, map[string]string{
    "endpoint": "/api/v1/buildings",
    "method":   "GET",
    "status":   "200",
})

// Increment a counter
telemetry.IncrementCounter("user_registrations", map[string]string{
    "source": "web",
})

// Record timing
timer := telemetry.StartTimer("database_query", map[string]interface{}{
    "table": "buildings",
    "operation": "select",
})
defer timer.Stop()
```

### Distributed Tracing

Add tracing to functions:

```go
func (s *BuildingService) GetBuilding(ctx context.Context, id string) (*models.Building, error) {
    ctx, span := telemetry.StartSpan(ctx, "BuildingService.GetBuilding")
    defer span.Finish()
    
    span.SetAttribute("building.id", id)
    
    // Implementation
    building, err := s.db.GetBuilding(ctx, id)
    if err != nil {
        span.RecordError(err)
        return nil, err
    }
    
    span.SetAttribute("building.name", building.Name)
    return building, nil
}
```

### Structured Logging

Use structured logging with correlation:

```go
import "github.com/joelpate/arxos/internal/telemetry"

func HandleRequest(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    
    telemetry.InfoWithContext(ctx, "Processing request", map[string]interface{}{
        "method": r.Method,
        "path":   r.URL.Path,
        "user_id": getUserID(ctx),
    })
    
    // Implementation
    
    telemetry.InfoWithContext(ctx, "Request completed successfully")
}
```

## Performance Guidelines

### Database Optimization

1. **Use prepared statements**
   ```go
   stmt, err := db.Prepare("SELECT * FROM buildings WHERE org_id = ?")
   defer stmt.Close()
   ```

2. **Implement pagination**
   ```go
   func ListBuildings(ctx context.Context, limit, offset int) ([]*Building, error) {
       query := "SELECT * FROM buildings LIMIT ? OFFSET ?"
       // Implementation
   }
   ```

3. **Add database indexes**
   ```sql
   CREATE INDEX idx_buildings_org_id ON buildings(org_id);
   CREATE INDEX idx_equipment_building_id ON equipment(building_id);
   ```

### API Performance

1. **Use response compression**
   ```go
   r.Use(middleware.Compress(5))
   ```

2. **Implement caching headers**
   ```go
   w.Header().Set("Cache-Control", "public, max-age=300")
   w.Header().Set("ETag", generateETag(data))
   ```

3. **Optimize JSON responses**
   ```go
   type PublicBuilding struct {
       ID   string `json:"id"`
       Name string `json:"name"`
       // Only include necessary fields
   }
   ```

## Security Best Practices

### Input Validation

```go
func validateBuildingRequest(req *CreateBuildingRequest) error {
    if req.Name == "" {
        return errors.New("name is required")
    }
    if len(req.Name) > 100 {
        return errors.New("name too long")
    }
    if !isValidBuildingType(req.Type) {
        return errors.New("invalid building type")
    }
    return nil
}
```

### SQL Injection Prevention

Always use parameterized queries:

```go
// Good
query := "SELECT * FROM buildings WHERE id = ?"
rows, err := db.Query(query, buildingID)

// Bad - never do this
query := fmt.Sprintf("SELECT * FROM buildings WHERE id = '%s'", buildingID)
```

### Authentication

Implement proper JWT validation:

```go
func validateJWT(tokenString string) (*models.User, error) {
    token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        return []byte(secretKey), nil
    })
    
    if !token.Valid {
        return nil, errors.New("invalid token")
    }
    
    // Extract and validate claims
    return user, nil
}
```

## Deployment

### Building for Production

```bash
# Build optimized binary
CGO_ENABLED=1 GOOS=linux go build -ldflags="-w -s" ./cmd/arxos-server

# Build Docker image
docker build -t arxos:latest .

# Run with Docker Compose
docker-compose up -d
```

### Configuration Management

Use environment-specific configs:

```yaml
# config/production.yaml
database:
  path: "/data/arxos.db"
  
telemetry:
  enabled: true
  endpoint: "https://metrics.arxos.io"
  
security:
  jwt_secret: "${JWT_SECRET}"
  cors_origins:
    - "https://app.arxos.io"
```

## Contributing

### Code Style

- Follow Go conventions (gofmt, golint)
- Use meaningful variable names
- Write godoc comments for public functions
- Keep functions small and focused

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `go test ./...`
5. Update documentation
6. Submit a pull request

### Code Review Checklist

- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance impact evaluated
- [ ] API documentation updated
- [ ] Backward compatibility maintained

## Troubleshooting

### Common Issues

1. **Database locked errors**
   - Ensure proper connection pooling
   - Close database connections properly
   - Check for long-running transactions

2. **JWT token issues**
   - Verify token expiration
   - Check secret key configuration
   - Validate token format

3. **AR scene not loading**
   - Check device AR support
   - Verify camera permissions
   - Ensure network connectivity

### Debug Mode

Enable debug logging:

```bash
./arxos-server --verbose --log-level=debug
```

Monitor metrics at http://localhost:9090/metrics

View traces in the observability dashboard at http://localhost:8090/

## Resources

- [Go Documentation](https://golang.org/doc/)
- [Chi Router](https://github.com/go-chi/chi)
- [React Native](https://reactnative.dev/)
- [ViroReact](https://github.com/ViroCommunity/viro)
- [SQLite](https://sqlite.org/docs.html)
- [OpenAPI Specification](https://swagger.io/specification/)

## Support

- GitHub Issues: https://github.com/arx-os/arxos/issues
- Documentation: https://docs.arxos.io
- API Reference: http://localhost:8080/docs/