# ArxOS Integration Guide

## Overview

This guide explains how to integrate ArxOS with external systems and how the internal modules work together.

## Internal Module Integration

### Analytics ↔ IT Management
- **Asset Performance Tracking**: Analytics monitors IT asset performance and utilization
- **Energy Consumption**: Track energy usage of IT equipment by room and building
- **Predictive Maintenance**: Use analytics to predict IT equipment failures

### Workflow ↔ CMMS
- **Automated Maintenance**: Workflows trigger maintenance schedules and work orders
- **Asset Lifecycle**: Automated workflows for asset procurement, deployment, and disposal
- **Compliance**: Automated compliance checking and reporting

### Hardware ↔ Analytics
- **Real-time Data**: Hardware devices feed data to analytics engine
- **Performance Monitoring**: Monitor hardware device performance and health
- **Anomaly Detection**: Detect hardware failures and performance issues

### IT Management ↔ Workflow
- **Automated Provisioning**: Workflows for IT asset deployment and configuration
- **Incident Response**: Automated workflows for IT incident handling
- **Inventory Management**: Automated parts ordering and inventory updates

## External System Integration

### n8n Workflow Integration

#### Setup
```bash
# Configure n8n connection
arx workflow n8n configure --url "https://n8n.yourdomain.com" --api-key "your-api-key"

# Test connection
arx workflow n8n test-connection
```

#### Workflow Examples
```json
{
  "name": "Energy Optimization",
  "nodes": [
    {
      "name": "Check Energy Usage",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "{{ $env.ARXOS_API_URL }}/api/analytics/energy/data",
        "method": "GET"
      }
    },
    {
      "name": "Send Alert",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "to": "facilities@school.edu",
        "subject": "High Energy Usage Alert",
        "message": "Energy consumption exceeded threshold"
      }
    }
  ]
}
```

### MQTT Integration

#### Device Configuration
```yaml
# configs/mqtt.yml
mqtt:
  broker: "mqtt.arxos.com"
  port: 1883
  username: "device_user"
  password: "device_password"
  topics:
    - "sensors/+/temperature"
    - "sensors/+/humidity"
    - "sensors/+/energy"
```

#### Message Handling
```go
// Subscribe to MQTT topics
func (h *HardwareManager) handleMQTTMessage(topic string, payload []byte) {
    switch {
    case strings.HasPrefix(topic, "sensors/"):
        h.handleSensorData(topic, payload)
    case strings.HasPrefix(topic, "devices/"):
        h.handleDeviceStatus(topic, payload)
    }
}
```

### Database Integration

#### PostgreSQL/PostGIS
```yaml
# configs/database.yml
database:
  host: "localhost"
  port: 5432
  database: "arxos"
  username: "arxos"
  password: "arxos"
  ssl_mode: "disable"
  max_connections: 25
  spatial_extensions: true
```

#### Redis Cache
```yaml
# configs/redis.yml
redis:
  host: "localhost"
  port: 6379
  password: ""
  database: 0
  max_connections: 10
  ttl: "1h"
```

### API Integration

#### REST API Client
```go
type ArxOSClient struct {
    baseURL    string
    apiKey     string
    httpClient *http.Client
}

func (c *ArxOSClient) GetAssets(buildingID string) ([]*Asset, error) {
    url := fmt.Sprintf("%s/api/v1/it/assets?building=%s", c.baseURL, buildingID)
    
    req, err := http.NewRequest("GET", url, nil)
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("Authorization", "Bearer "+c.apiKey)
    
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var response struct {
        Data []*Asset `json:"data"`
    }
    
    if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
        return nil, err
    }
    
    return response.Data, nil
}
```

#### Webhook Integration
```go
func (h *WebhookHandler) HandleWebhook(w http.ResponseWriter, r *http.Request) {
    var payload WebhookPayload
    if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
        http.Error(w, "Invalid payload", http.StatusBadRequest)
        return
    }
    
    switch payload.Event {
    case "asset.created":
        h.handleAssetCreated(payload.Data)
    case "workorder.completed":
        h.handleWorkOrderCompleted(payload.Data)
    }
}
```

## Module Communication

### Event System
```go
// Event bus for module communication
type EventBus struct {
    subscribers map[string][]EventHandler
    mu          sync.RWMutex
}

type EventHandler interface {
    HandleEvent(event Event) error
}

// Publish event
func (eb *EventBus) Publish(event Event) error {
    eb.mu.RLock()
    defer eb.mu.RUnlock()
    
    handlers := eb.subscribers[event.Type]
    for _, handler := range handlers {
        go handler.HandleEvent(event)
    }
    
    return nil
}
```

### Service Dependencies
```go
// Service dependency injection
type ServiceContainer struct {
    analyticsService  *analytics.AnalyticsEngine
    itService        *it.ITManager
    workflowService  *workflow.WorkflowManager
    facilityService  *facility.FacilityManager
}

func NewServiceContainer(config *Config) *ServiceContainer {
    // Initialize services with dependencies
    analyticsService := analytics.NewAnalyticsEngine()
    itService := it.NewITManager()
    workflowService := workflow.NewWorkflowManager()
    facilityService := facility.NewFacilityManager()
    
    return &ServiceContainer{
        analyticsService:  analyticsService,
        itService:        itService,
        workflowService:  workflowService,
        facilityService:  facilityService,
    }
}
```

## Configuration Management

### Environment Variables
```bash
# Database
DATABASE_URL=postgres://user:pass@localhost:5432/arxos
REDIS_URL=redis://localhost:6379

# API
API_HOST=localhost
API_PORT=8080
JWT_SECRET=your-secret

# External Services
N8N_URL=https://n8n.yourdomain.com
N8N_API_KEY=your-api-key
MQTT_BROKER=mqtt.arxos.com
MQTT_PORT=1883
```

### Configuration Files
```yaml
# configs/integration.yml
integrations:
  n8n:
    enabled: true
    url: "https://n8n.yourdomain.com"
    api_key: "your-api-key"
    timeout: "30s"
  
  mqtt:
    enabled: true
    broker: "mqtt.arxos.com"
    port: 1883
    username: "device_user"
    password: "device_password"
  
  webhooks:
    enabled: true
    secret: "webhook-secret"
    timeout: "10s"
```

## Testing Integration

### Integration Test Setup
```go
func setupIntegrationTest(t *testing.T) *TestEnvironment {
    // Start test database
    db := startTestPostgres(t)
    
    // Start test Redis
    redis := startTestRedis(t)
    
    // Start test MQTT broker
    mqtt := startTestMQTT(t)
    
    return &TestEnvironment{
        DB:   db,
        Redis: redis,
        MQTT: mqtt,
    }
}
```

### End-to-End Testing
```go
func TestCompleteWorkflow(t *testing.T) {
    env := setupIntegrationTest(t)
    defer env.Cleanup()
    
    // Create IT asset
    asset, err := env.ITService.CreateAsset(&it.CreateAssetRequest{
        Name: "Test Laptop",
        Type: "laptop",
        Room: "/buildings/main/floors/2/rooms/classroom-205",
    })
    require.NoError(t, err)
    
    // Create work order
    workOrder, err := env.FacilityService.CreateWorkOrder(&facility.CreateWorkOrderRequest{
        Title: "Install Laptop",
        Building: "main",
        Room: "classroom-205",
        Type: "installation",
    })
    require.NoError(t, err)
    
    // Execute workflow
    execution, err := env.WorkflowService.ExecuteWorkflow("asset_deployment", map[string]interface{}{
        "asset_id": asset.ID,
        "work_order_id": workOrder.ID,
    })
    require.NoError(t, err)
    
    // Verify completion
    assert.Equal(t, "completed", execution.Status)
}
```

## Monitoring and Observability

### Metrics Collection
```go
// Prometheus metrics
var (
    httpRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "endpoint", "status"},
    )
    
    httpRequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "http_request_duration_seconds",
            Help: "HTTP request duration in seconds",
        },
        []string{"method", "endpoint"},
    )
)
```

### Logging
```go
// Structured logging
logger.Info("integration event",
    "event_type", "asset.created",
    "asset_id", asset.ID,
    "building", asset.Building,
    "room", asset.Room,
    "timestamp", time.Now(),
)
```

### Health Checks
```go
func (h *HealthHandler) CheckHealth(w http.ResponseWriter, r *http.Request) {
    health := &HealthStatus{
        Status: "healthy",
        Checks: make(map[string]CheckResult),
    }
    
    // Check database
    if err := h.db.Ping(); err != nil {
        health.Checks["database"] = CheckResult{Status: "unhealthy", Error: err.Error()}
        health.Status = "unhealthy"
    } else {
        health.Checks["database"] = CheckResult{Status: "healthy"}
    }
    
    // Check Redis
    if err := h.redis.Ping().Err(); err != nil {
        health.Checks["redis"] = CheckResult{Status: "unhealthy", Error: err.Error()}
        health.Status = "unhealthy"
    } else {
        health.Checks["redis"] = CheckResult{Status: "healthy"}
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(health)
}
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
arx system health

# Test database connection
arx config test database

# Check database logs
arx logs --module database --level error
```

#### MQTT Connection Issues
```bash
# Test MQTT connection
arx hardware protocols test mqtt --host mqtt.arxos.com --port 1883

# Check MQTT logs
arx logs --module hardware --level error
```

#### Workflow Execution Issues
```bash
# Check workflow status
arx workflow status execution_001

# List failed workflows
arx workflow executions list --status failed

# Retry failed workflow
arx workflow retry execution_001
```

### Debug Mode
```bash
# Enable debug logging
arx --verbose --debug daemon start

# Check specific module
arx --verbose analytics energy data --building main --debug
```

This integration guide provides comprehensive information for integrating ArxOS with external systems and understanding internal module interactions.
