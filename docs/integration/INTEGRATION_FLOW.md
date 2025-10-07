# ArxOS IfcOpenShell Integration Architecture

## Overview

The ArxOS system integrates IfcOpenShell with PostGIS and the daemon service to create a complete building data processing pipeline. Here's how they work together:

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ArxOS Complete Data Flow                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   File      │───▶│   Daemon     │───▶│  IfcOpenShell   │───▶│   PostGIS   │  │
│  │   System    │    │   Service    │    │    Service      │    │  Database   │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘  │
│         │                    │                    │                    │        │
│         │                    │                    │                    │        │
│         ▼                    ▼                    ▼                    ▼        │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   IFC       │    │   File       │    │   Python        │    │   Spatial   │  │
│  │   Files     │    │   Watcher    │    │   Processing    │    │   Storage   │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Interactions

### 1. File System → Daemon Service

**Trigger**: File system events (new IFC files)
**Process**: File watching and detection

```go
// internal/infrastructure/services/daemon.go
func (ds *DaemonService) processImport(event *domain.FileEvent, format string) error {
    // Read file data
    data, err := ds.processor.ReadFile(event.Path)
    if err != nil {
        return fmt.Errorf("failed to read file: %w", err)
    }

    // Create import request
    req := &domain.ImportBuildingRequest{
        Format: format,
        Data:   data,
    }

    // Log processing status
    ds.logger.Info("Processing file import",
        "path", event.Path,
        "format", format,
        "size", len(data),
        "request_format", req.Format,
        "status", "ready_for_ifcopenshell_integration")
}
```

### 2. Daemon Service → IfcOpenShell Service

**Trigger**: IFC file detected
**Process**: HTTP API call to Python service

```go
// internal/infrastructure/ifc/ifcopenshell_client.go
func (c *IfcOpenShellClient) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
    var result IFCResult
    var lastErr error

    for i := 0; i < c.retries; i++ {
        req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/parse", bytes.NewReader(data))
        if err != nil {
            return nil, fmt.Errorf("failed to create request: %w", err)
        }
        req.Header.Set("Content-Type", "application/octet-stream")

        resp, err := c.httpClient.Do(req)
        if err != nil {
            lastErr = fmt.Errorf("parse request failed (attempt %d/%d): %w", i+1, c.retries, err)
            time.Sleep(time.Second * time.Duration(i+1))
            continue
        }
        defer resp.Body.Close()

        if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
            lastErr = fmt.Errorf("failed to decode response: %w", err)
            continue
        }

        return &result, nil
    }

    return nil, fmt.Errorf("parse failed after %d retries: %w", c.retries, lastErr)
}
```

### 3. IfcOpenShell Service → PostGIS Database

**Trigger**: Parsed IFC data
**Process**: Spatial data storage and indexing

```go
// internal/infrastructure/ifc/service.go
func (s *IFCService) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
    // Try IfcOpenShell service first
    if s.serviceEnabled && s.ifcOpenShellClient != nil {
        result, err := s.tryIfcOpenShellService(ctx, data)
        if err == nil {
            // Store parsed data in PostGIS
            return s.storeInPostGIS(ctx, result)
        }
    }

    // Fallback to native parser
    if s.fallbackEnabled && s.nativeParser != nil {
        result, err := s.nativeParser.ParseIFC(ctx, data)
        if err != nil {
            return nil, err
        }
        return s.storeInPostGIS(ctx, result)
    }

    return nil, fmt.Errorf("no IFC parser available")
}
```

## Detailed Data Flow

### Phase 1: File Detection
```
File System Event → Daemon Service → File Processor
     │                    │              │
     ▼                    ▼              ▼
  IFC File          File Watcher    Format Detection
  Created           Triggers        (IFC, JSON, etc.)
```

### Phase 2: IFC Processing
```
Daemon Service → IFC Service → IfcOpenShell Client → Python Service
     │              │              │                    │
     ▼              ▼              ▼                    ▼
  File Data    Orchestration   HTTP Request      IfcOpenShell
  Retrieved    & Fallback      to Python        Processing
```

### Phase 3: Data Storage
```
Python Service → Go Client → IFC Service → PostGIS Repository
     │              │           │              │
     ▼              ▼           ▼              ▼
  Parsed Data   JSON Response  Validation   Spatial Storage
  (JSON)        (Go Struct)    & Mapping    & Indexing
```

## Code Integration Points

### 1. Daemon Service Integration

```go
// internal/infrastructure/services/daemon.go
type DaemonService struct {
    processor FileProcessor
    logger    domain.Logger
    ctx       context.Context
    // TODO: Add IFC service integration
    // ifcService ifc.IFCService
}

func (ds *DaemonService) processImport(event *domain.FileEvent, format string) error {
    // Current: Logging and preparation
    // Future: Direct IFC service integration

    // if format == "ifc" {
    //     result, err := ds.ifcService.ParseIFC(ds.ctx, data)
    //     if err != nil {
    //         return fmt.Errorf("failed to parse IFC file: %w", err)
    //     }
    //     ds.logger.Info("IFC file parsed successfully",
    //         "buildings", result.Buildings,
    //         "spaces", result.Spaces,
    //         "equipment", result.Equipment)
    // }
}
```

### 2. IFC Service Orchestration

```go
// internal/infrastructure/ifc/service.go
type IFCService struct {
    ifcOpenShellClient IfcOpenShellClientInterface
    nativeParser       *NativeParser
    serviceEnabled     bool
    fallbackEnabled    bool
    circuitBreaker     *CircuitBreaker
}

func (s *IFCService) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
    // Circuit breaker pattern
    if s.circuitBreaker != nil && s.circuitBreaker.state == Open {
        if time.Since(s.circuitBreaker.lastFailureTime) < s.circuitBreaker.recoveryTimeout {
            return nil, fmt.Errorf("circuit breaker is open")
        }
        s.circuitBreaker.state = HalfOpen
    }

    // Try IfcOpenShell service first
    if s.serviceEnabled && s.ifcOpenShellClient != nil {
        result, err := s.tryIfcOpenShellService(ctx, data)
        if err == nil {
            s.circuitBreaker.reset()
            return result, nil
        }

        s.circuitBreaker.recordFailure()
        fmt.Printf("IfcOpenShell service failed, using fallback: %v\n", err)
    }

    // Fallback to native parser
    if s.fallbackEnabled && s.nativeParser != nil {
        return s.nativeParser.ParseIFC(ctx, data)
    }

    return nil, fmt.Errorf("no IFC parser available")
}
```

### 3. PostGIS Integration

```go
// internal/infrastructure/repository/postgis_ifc_repo.go
type PostGISIFCRepository struct {
    db     *sql.DB
    logger domain.Logger
}

func (r *PostGISIFCRepository) Create(ctx context.Context, ifcFile *building.IFCFile) error {
    query := `
        INSERT INTO ifc_files (
            id, name, path, version, discipline, size, entities, validated, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    `

    _, err := r.db.ExecContext(ctx, query,
        ifcFile.ID,
        ifcFile.Name,
        ifcFile.Path,
        ifcFile.Version,
        ifcFile.Discipline,
        ifcFile.Size,
        ifcFile.Entities,
        ifcFile.Validated,
        ifcFile.CreatedAt,
        ifcFile.UpdatedAt,
    )

    if err != nil {
        return fmt.Errorf("failed to create IFC file record: %w", err)
    }

    return nil
}
```

## Python Service Processing

### IfcOpenShell Service (Python)

```python
# services/ifcopenshell-service/main.py
@app.route('/api/parse', methods=['POST'])
def parse_ifc():
    try:
        ifc_data = request.get_data()

        # Parse with IfcOpenShell
        model = ifcopenshell.open(io.BytesIO(ifc_data))

        # Extract entities
        buildings = len(model.by_type('IfcBuilding'))
        spaces = len(model.by_type('IfcSpace'))
        equipment = len(model.by_type('IfcFlowTerminal'))

        result = {
            "success": True,
            "buildings": buildings,
            "spaces": spaces,
            "equipment": equipment,
            "total_entities": buildings + spaces + equipment,
            "metadata": {
                "ifc_version": model.schema,
                "file_size": len(ifc_data),
                "processing_time": f"{processing_time:.3f}s"
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "IFC_PARSE_ERROR",
                "message": str(e)
            }
        }), 400
```

## Complete Integration Flow

### 1. File Upload/Detection
```
User uploads IFC file → File system → Daemon detects → Triggers processing
```

### 2. IFC Processing Pipeline
```
Daemon → IFC Service → IfcOpenShell Client → Python Service → IfcOpenShell Library
  │         │              │                    │                    │
  ▼         ▼              ▼                    ▼                    ▼
File    Orchestration   HTTP Request      Flask App          C++ Library
Data    & Fallback      (JSON)           (Python)           (IfcOpenShell)
```

### 3. Data Storage Pipeline
```
Python Service → Go Client → IFC Service → PostGIS Repository → Spatial Index
     │              │           │              │                    │
     ▼              ▼           ▼              ▼                    ▼
Parsed Data    JSON Response  Validation   Database Insert    Spatial Index
(Structured)   (Go Struct)   & Mapping    (PostgreSQL)       (PostGIS)
```

### 4. Error Handling & Fallback
```
IfcOpenShell Fails → Circuit Breaker → Native Parser → PostGIS Storage
        │                │                │                │
        ▼                ▼                ▼                ▼
   Service Error    Open Circuit     Go Parser        Fallback Data
   (Network/500)    (Prevent Calls)  (Basic Parse)    (Limited Info)
```

## Benefits of This Architecture

### 1. **Fault Tolerance**
- Circuit breaker prevents cascade failures
- Native parser fallback ensures continuity
- Multiple retry mechanisms

### 2. **Performance**
- Python service handles complex IFC processing
- Go service handles high-performance operations
- PostGIS provides spatial indexing

### 3. **Scalability**
- Services can scale independently
- Load balancing across multiple instances
- Caching at multiple levels

### 4. **Maintainability**
- Clear separation of concerns
- Technology-appropriate implementations
- Comprehensive testing and monitoring

## Configuration Integration

### Docker Compose Orchestration
```yaml
services:
  arxos:
    environment:
      - ARXOS_IFC_SERVICE_URL=http://ifcopenshell-service:5000
    depends_on:
      - ifcopenshell-service
      - postgis

  ifcopenshell-service:
    environment:
      - REDIS_HOST=redis
      - IFC_MAX_FILE_SIZE_MB=200
    depends_on:
      - redis

  postgis:
    environment:
      - POSTGRES_DB=arxos
    volumes:
      - postgis_data:/var/lib/postgresql/data
```

This architecture provides a robust, scalable, and maintainable solution for IFC processing with proper separation of concerns and fault tolerance.
