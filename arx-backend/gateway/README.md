# API Gateway Implementation

This directory contains the API Gateway implementation for the Arxos platform. The gateway serves as a central entry point for all platform APIs, providing unified routing, authentication, rate limiting, monitoring, and service discovery.

## 🏗️ Architecture

The API Gateway is built with a modular architecture consisting of several key components:

### Core Components

- **Gateway**: Main orchestrator that coordinates all components
- **Router**: Handles request routing to appropriate services
- **ServiceDiscovery**: Manages service health checks and discovery
- **LoadBalancer**: Distributes requests across service instances
- **Middleware**: Authentication, rate limiting, monitoring, and security

### Middleware Stack

1. **Authentication**: JWT token validation and role-based access control
2. **Rate Limiting**: Per-user and per-service rate limiting
3. **Monitoring**: Metrics collection and request tracing
4. **Security**: CORS, security headers, and audit logging

## 📁 File Structure

```
gateway/
├── gateway.go              # Main gateway implementation
├── router.go               # Service routing logic
├── discovery.go            # Service discovery and health checks
├── loadbalancer.go         # Load balancing logic
├── main.go                 # Gateway entry point
├── gateway_test.go         # Gateway tests
└── middleware/
    ├── auth.go             # Authentication middleware
    ├── rate_limit.go       # Rate limiting middleware
    └── monitoring.go       # Monitoring middleware
```

## 🚀 Quick Start

### Prerequisites

- Go 1.19 or later
- Required dependencies (see go.mod)

### Configuration

1. Copy the example configuration:
```bash
cp config/gateway.yaml config/gateway.local.yaml
```

2. Update the configuration for your environment:
```yaml
# Server settings
port: 8080
host: "0.0.0.0"

# Authentication
auth:
  jwt_secret: "your-super-secret-jwt-key"
  token_expiry: 24h

# Services
services:
  svg-parser:
    url: "http://localhost:8000"
    health: "http://localhost:8000/health"
```

### Running the Gateway

```bash
# From the arx-backend directory
go run gateway/main.go -config config/gateway.local.yaml
```

### Docker

```bash
docker build -t arxos-gateway .
docker run -p 8080:8080 arxos-gateway
```

## 🔧 Configuration

### Server Configuration

```yaml
port: 8080                    # Gateway port
host: "0.0.0.0"              # Gateway host
read_timeout: 30s             # Request read timeout
write_timeout: 30s            # Response write timeout
idle_timeout: 60s             # Connection idle timeout
max_connections: 1000         # Maximum concurrent connections
```

### Authentication Configuration

```yaml
auth:
  jwt_secret: "your-secret"   # JWT signing secret
  token_expiry: 24h           # Token expiration time
  refresh_expiry: 168h        # Refresh token expiration
  roles: ["admin", "user"]    # Available roles
  skip_auth_paths:            # Paths that skip authentication
    - "/health"
    - "/metrics"
```

### Rate Limiting Configuration

```yaml
rate_limit:
  requests_per_second: 100    # Requests per second limit
  burst: 200                  # Burst limit
  per_user: true              # Enable per-user rate limiting
  per_service: true           # Enable per-service rate limiting
  skip_paths:                 # Paths that skip rate limiting
    - "/health"
```

### Service Configuration

```yaml
services:
  service-name:
    name: "service-name"       # Service identifier
    url: "http://localhost:8000"  # Service URL
    health: "http://localhost:8000/health"  # Health check URL
    timeout: 30               # Request timeout
    retries: 3                # Retry attempts
    weight: 1                 # Load balancer weight
    routes:                   # Route definitions
      - path: "/api/v1/*"
        service: "service-name"
        methods: ["GET", "POST"]
        auth: true
```

## 🔌 API Endpoints

### Gateway Endpoints

- `GET /health` - Gateway health check
- `GET /gateway/health` - Detailed gateway health
- `GET /metrics` - Prometheus metrics
- `GET /gateway/config` - Current configuration
- `GET /gateway/routes` - Available routes

### Service Endpoints

All service endpoints are automatically routed based on configuration:

- `/api/v1/svg/*` → svg-parser service
- `/api/v1/cmms/*` → cmms-service
- `/api/v1/database/*` → database-infra
- `/api/v1/auth/*` → arx-backend

## 🔐 Authentication

The gateway supports JWT-based authentication with the following features:

### Token Extraction

Tokens can be provided in:
- `Authorization: Bearer <token>` header
- `X-Auth-Token` header
- `token` query parameter

### Role-Based Access Control

```go
// Check if user has specific role
if user.HasRole("admin") {
    // Admin-only logic
}

// Check if user has any of the roles
if user.HasAnyRole([]string{"admin", "moderator"}) {
    // Moderator or admin logic
}
```

### Skip Authentication

Configure paths that skip authentication:

```yaml
auth:
  skip_auth_paths:
    - "/health"
    - "/metrics"
    - "/docs"
```

## 📊 Monitoring

### Metrics

The gateway collects the following metrics:

- Request counts per service/path
- Response times
- Error rates
- Active requests
- Rate limiting statistics

### Health Checks

- Service health monitoring
- Circuit breaker implementation
- Automatic failover

### Logging

Structured logging with correlation IDs:

```json
{
  "level": "info",
  "request_id": "20231201120000-abc123",
  "method": "GET",
  "path": "/api/v1/assets",
  "status_code": 200,
  "duration": "45ms",
  "service": "arx-backend"
}
```

## 🛡️ Security

### Security Headers

The gateway automatically adds security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

### CORS Configuration

```yaml
cors:
  allowed_origins:
    - "http://localhost:3000"
    - "https://arxos.com"
  allowed_methods: ["GET", "POST", "PUT", "DELETE"]
  allow_credentials: true
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
go test ./gateway/...

# Run specific test
go test -v -run TestGatewayHealth

# Run with coverage
go test -cover ./gateway/...
```

### Test Configuration

Create a test configuration file for integration tests:

```yaml
# config/gateway.test.yaml
port: 0  # Use random port for tests
host: "localhost"
services:
  test-service:
    url: "http://localhost:8000"
    health: "http://localhost:8000/health"
```

## 🔄 Development

### Adding New Services

1. Add service configuration to `config/gateway.yaml`:

```yaml
services:
  new-service:
    name: "new-service"
    url: "http://localhost:8003"
    health: "http://localhost:8003/health"
    routes:
      - path: "/api/v1/new/*"
        service: "new-service"
        methods: ["GET", "POST"]
        auth: true
```

2. Restart the gateway to pick up changes.

### Adding New Middleware

1. Create middleware in `gateway/middleware/`
2. Implement the middleware interface
3. Register in `gateway.go`

### Custom Load Balancing

Implement custom load balancing algorithms by extending the `LoadBalancer` interface.

## 🚨 Troubleshooting

### Common Issues

1. **Service Unavailable**
   - Check service health endpoints
   - Verify service URLs in configuration
   - Check network connectivity

2. **Authentication Failures**
   - Verify JWT secret configuration
   - Check token expiration
   - Validate token format

3. **Rate Limiting**
   - Check rate limit configuration
   - Monitor rate limit headers
   - Adjust limits if needed

4. **High Response Times**
   - Check service health
   - Monitor circuit breaker status
   - Review load balancer configuration

### Debug Mode

Enable debug logging:

```yaml
monitoring:
  logging:
    level: "debug"
```

### Health Check

Check gateway health:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/gateway/health
```

## 📈 Performance

### Optimization Tips

1. **Connection Pooling**: Configure appropriate connection limits
2. **Caching**: Implement response caching for static content
3. **Compression**: Enable gzip compression for responses
4. **Load Balancing**: Use weighted load balancing for critical services

### Monitoring

Monitor key metrics:

- Request rate per service
- Response time percentiles
- Error rates
- Circuit breaker status
- Rate limiting statistics

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Follow Go coding standards
5. Add appropriate logging

## 📄 License

This implementation is part of the Arxos platform and follows the same licensing terms. 