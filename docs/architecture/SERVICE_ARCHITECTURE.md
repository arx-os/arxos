# ArxOS Service Architecture

## Overview

ArxOS follows a **hybrid microservices architecture** with clear separation between internal core services and external microservices.

## Directory Structure

```
arxos/
├── internal/                    # ArxOS Core Application (Go)
│   ├── infrastructure/
│   │   └── services/           # Internal ArxOS Services
│   │       ├── daemon.go       # File watching daemon
│   │       ├── file_processor.go # File processing logic
│   │       └── file_watcher.go  # File system watcher
│   └── infrastructure/
│       └── ifc/                # IFC Client Integration
│           ├── ifcopenshell_client.go  # HTTP client for external service
│           ├── native_parser.go        # Fallback parser
│           └── service.go             # Orchestration service
│
└── services/                   # External Microservices
    └── ifcopenshell-service/   # Python Flask Microservice
        ├── main.py            # Flask application
        ├── models/            # Python models
        └── requirements.txt   # Python dependencies
```

## Service Types

### Internal Services (`/internal/infrastructure/services/`)

**Purpose**: Core ArxOS functionality implemented in Go
**Characteristics**:
- Part of the main ArxOS application
- Direct access to ArxOS domain models
- Tightly coupled with ArxOS architecture
- Deployed as part of the main application

**Services**:
- **DaemonService**: File system monitoring and processing
- **FileProcessor**: File processing and validation
- **FileWatcher**: Real-time file system events

### External Microservices (`/services/`)

**Purpose**: Specialized services implemented in other languages
**Characteristics**:
- Independent applications with their own lifecycle
- Communicate via HTTP/gRPC APIs
- Can be deployed separately
- Technology-agnostic (Python, Node.js, Rust, etc.)

**Services**:
- **ifcopenshell-service**: IFC processing using Python + IfcOpenShell

## Communication Patterns

### Internal Services
```go
// Direct function calls within the same process
daemonService := NewDaemonService(fileProcessor, logger)
daemonService.Start(ctx)
```

### External Services
```go
// HTTP client calls to external services
ifcClient := NewIfcOpenShellClient("http://ifcopenshell-service:5000")
result, err := ifcClient.ParseIFC(ctx, ifcData)
```

## Deployment Architecture

### Development
```yaml
# docker-compose.dev.yml
services:
  arxos:                    # Main ArxOS application
    build: .
    depends_on:
      - ifcopenshell-service
  
  ifcopenshell-service:     # External microservice
    build: ./services/ifcopenshell-service
```

### Production
```yaml
# docker-compose.prod.yml
services:
  arxos:
    deploy:
      replicas: 3
    depends_on:
      - ifcopenshell-service
  
  ifcopenshell-service:
    deploy:
      replicas: 5  # Can scale independently
```

## Benefits of This Architecture

### 1. **Technology Flexibility**
- Use the best language for each service
- Go for core ArxOS functionality
- Python for IFC processing (IfcOpenShell)
- Future: Rust for performance-critical services

### 2. **Independent Scaling**
- Scale microservices based on demand
- ArxOS core: 3 replicas
- IFC service: 5 replicas (high processing load)

### 3. **Fault Isolation**
- If IFC service fails, ArxOS core continues
- Circuit breaker pattern for resilience
- Fallback to native Go parser

### 4. **Development Velocity**
- Teams can work on services independently
- Different release cycles
- Technology-specific expertise

## Service Integration Patterns

### 1. **Client-Server Pattern**
```go
// ArxOS (Go) -> IfcOpenShell (Python)
type IfcOpenShellClient struct {
    baseURL string
    httpClient *http.Client
}

func (c *IfcOpenShellClient) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
    // HTTP call to Python service
}
```

### 2. **Circuit Breaker Pattern**
```go
// Fallback mechanism
func (s *IFCService) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
    // Try external service first
    result, err := s.ifcOpenShellClient.ParseIFC(ctx, data)
    if err == nil {
        return result, nil
    }
    
    // Fallback to internal parser
    return s.nativeParser.ParseIFC(ctx, data)
}
```

### 3. **Service Discovery**
```yaml
# Docker Compose service discovery
services:
  arxos:
    environment:
      - IFC_SERVICE_URL=http://ifcopenshell-service:5000
```

## Future Service Additions

### Planned External Services
```
services/
├── ifcopenshell-service/     # IFC processing (Python)
├── mesh-service/            # Mesh processing (Rust)
├── ai-service/              # AI/ML features (Python)
└── analytics-service/       # Analytics (Node.js)
```

### Internal Service Extensions
```
internal/infrastructure/services/
├── daemon.go               # File monitoring
├── file_processor.go       # File processing
├── mesh_processor.go       # Mesh processing (Go)
└── analytics_processor.go  # Analytics processing (Go)
```

## Best Practices

### 1. **Service Boundaries**
- **Internal**: Core ArxOS functionality
- **External**: Specialized processing, third-party integrations

### 2. **Communication**
- **Internal**: Direct function calls, shared memory
- **External**: HTTP/gRPC, message queues

### 3. **Error Handling**
- **Internal**: Go error handling
- **External**: Circuit breakers, retries, fallbacks

### 4. **Testing**
- **Internal**: Unit tests, integration tests
- **External**: Contract tests, end-to-end tests

### 5. **Monitoring**
- **Internal**: Go metrics, logging
- **External**: Service-specific metrics, health checks

## Configuration Management

### Internal Services
```go
// Go configuration
type Config struct {
    Daemon DaemonConfig `json:"daemon"`
    FileProcessor FileProcessorConfig `json:"file_processor"`
}
```

### External Services
```yaml
# Environment variables
services:
  ifcopenshell-service:
    environment:
      - FLASK_ENV=production
      - REDIS_HOST=redis
      - IFC_MAX_FILE_SIZE_MB=200
```

## Conclusion

This architecture provides:
- **Clear separation** between internal and external services
- **Technology flexibility** for specialized processing
- **Independent scaling** and deployment
- **Fault tolerance** with fallback mechanisms
- **Maintainable codebase** with clear boundaries

The `/internal/infrastructure/services/` and `/services/` directories serve different purposes and should remain separate to maintain this architectural clarity.
