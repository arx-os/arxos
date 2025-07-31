# Construction Management Application Architecture

## Overview

The Construction Management Application is a comprehensive project management platform built with Go + Chi that leverages existing Arxos capabilities (BIM, AI, IoT, CMMS) to provide construction-specific project management, scheduling, safety monitoring, and quality control features.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Construction Management                     │
│                         Application                           │
├─────────────────────────────────────────────────────────────────┤
│  Web Frontend (React)  │  Mobile Apps (iOS/Android)  │  API  │
├─────────────────────────────────────────────────────────────────┤
│                    Construction Service                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │   Projects  │ │  Schedules  │ │ Documents   │ │ Safety  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Integration Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │     AI      │ │     IoT     │ │     BIM     │ │  CMMS   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Database Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │  Projects   │ │  Schedules  │ │ Documents   │ │ Safety  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Service Architecture

#### 1. Construction Service (`services/construction/`)

**Technology Stack:**
- **Language**: Go 1.21+
- **Framework**: Chi (lightweight, fast HTTP router)
- **Database**: PostgreSQL + PostGIS (prod), SQLite (edge/offline)
- **ORM**: GORM or SQLC for type-safe database operations
- **Authentication**: JWT with Arxos Auth Service
- **File Storage**: MinIO/S3 for document management
- **Caching**: Redis for session and data caching
- **Message Queue**: RabbitMQ for async processing

**Core Components:**
```go
// services/construction/cmd/main.go
package main

import (
    "log"
    "net/http"
    
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "github.com/go-chi/cors"
    
    "arxos/construction/internal/config"
    "arxos/construction/api"
)

func main() {
    r := chi.NewRouter()
    
    // Middleware
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(cors.Handler(cors.Options{
        AllowedOrigins:   []string{"*"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
        ExposedHeaders:   []string{"Link"},
        AllowCredentials: true,
        MaxAge:           300,
    }))
    
    // Routes
    r.Route("/api/v1", func(r chi.Router) {
        r.Route("/projects", api.ProjectsHandler)
        r.Route("/schedules", api.SchedulesHandler)
        r.Route("/documents", api.DocumentsHandler)
        r.Route("/inspections", api.InspectionsHandler)
        r.Route("/safety", api.SafetyHandler)
        r.Route("/reporting", api.ReportingHandler)
    })
    
    log.Fatal(http.ListenAndServe(":8080", r))
}
```

#### 2. Database Schema

**Core Tables:**
```sql
-- Construction Projects
CREATE TABLE construction_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location JSONB,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'planning',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Construction Schedules
CREATE TABLE construction_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES construction_projects(id) ON DELETE CASCADE,
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    duration_days INTEGER,
    dependencies JSONB,
    assigned_to UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Construction Documents
CREATE TABLE construction_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES construction_projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    file_path VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    version VARCHAR(50),
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    tags TEXT[]
);

-- Construction Inspections
CREATE TABLE construction_inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES construction_projects(id) ON DELETE CASCADE,
    inspection_type VARCHAR(100),
    location JSONB,
    inspector_id UUID REFERENCES users(id),
    scheduled_date DATE,
    completed_date DATE,
    status VARCHAR(50) DEFAULT 'scheduled',
    findings JSONB,
    photos JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Safety Incidents
CREATE TABLE construction_safety_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES construction_projects(id) ON DELETE CASCADE,
    incident_type VARCHAR(100),
    severity VARCHAR(50),
    location JSONB,
    description TEXT,
    reported_by UUID REFERENCES users(id),
    reported_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    resolution TEXT,
    photos JSONB
);

-- Cost Tracking
CREATE TABLE construction_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES construction_projects(id) ON DELETE CASCADE,
    category VARCHAR(100),
    description TEXT,
    amount DECIMAL(15,2),
    date DATE,
    approved_by UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. Directory Structure

```bash
arxos/services/construction/
├── cmd/
│   └── main.go                       # Application entry point
├── api/                              # HTTP route handlers
│   ├── projects.go                   # Project management API
│   ├── schedules.go                  # Scheduling and Gantt charts
│   ├── documents.go                  # Document management
│   ├── inspections.go                # Quality control and inspections
│   ├── safety.go                     # Safety management
│   └── reporting.go                  # Analytics and reporting
├── internal/
│   ├── core/                         # Core construction logic
│   │   ├── project_manager.go        # Project lifecycle management
│   │   ├── schedule_engine.go        # Critical path analysis
│   │   ├── document_processor.go     # Document parsing and indexing
│   │   ├── inspection_engine.go      # Inspection workflow engine
│   │   ├── safety_monitor.go         # Safety compliance tracking
│   │   └── cost_controller.go        # Budget and cost management
│   ├── models/                       # Data models
│   │   ├── project.go                # Project data model
│   │   ├── schedule.go               # Schedule data model
│   │   ├── document.go               # Document data model
│   │   ├── inspection.go             # Inspection data model
│   │   ├── safety.go                 # Safety data model
│   │   └── cost.go                   # Cost data model
│   ├── templates/                    # Construction templates
│   │   ├── safety.go                 # Safety templates
│   │   └── reports.go                # Report templates
│   └── config/                       # Configuration
│       ├── settings.go               # Application settings
│       └── database.go               # Database configuration
├── pkg/
│   └── svgxbridge/                   # SVGX BIM integrations
│       ├── markup_sync.go            # Sync construction progress with SVGX
│       └── behavior_hooks.go         # SVGX behavior integration
├── tests/                            # Test suites
│   ├── project_test.go               # Project management tests
│   ├── schedule_test.go              # Scheduling tests
│   ├── inspection_test.go            # Inspection tests
│   └── safety_test.go                # Safety tests
├── go.mod                            # Go module definition
├── go.sum                            # Go module checksums
└── README.md                         # Service documentation
```

## 🔧 Integration Architecture

### 1. SVGX BIM Integration

**SVGX Bridge Package:**
```go
// pkg/svgxbridge/markup_sync.go
package svgxbridge

import (
    "context"
    "encoding/json"
    "fmt"
)

type MarkupSync struct {
    svgxClient *SVGXClient
}

type ConstructionProgress struct {
    ProjectID    string                 `json:"project_id"`
    TaskID       string                 `json:"task_id"`
    Progress     float64                `json:"progress"`
    Status       string                 `json:"status"`
    MarkupData   map[string]interface{} `json:"markup_data"`
}

func (ms *MarkupSync) SyncConstructionProgress(ctx context.Context, progress ConstructionProgress) error {
    // Sync construction progress with SVGX markups
    markup := &SVGXMarkup{
        ProjectID:  progress.ProjectID,
        TaskID:     progress.TaskID,
        Progress:   progress.Progress,
        Status:     progress.Status,
        Data:       progress.MarkupData,
    }
    
    return ms.svgxClient.UpdateMarkup(ctx, markup)
}

func (ms *MarkupSync) ValidateAsBuilt(ctx context.Context, projectID string, designID string) (*ValidationResult, error) {
    // Validate as-built vs design drawings
    design, err := ms.svgxClient.GetDesign(ctx, designID)
    if err != nil {
        return nil, fmt.Errorf("failed to get design: %w", err)
    }
    
    asBuilt, err := ms.svgxClient.GetAsBuilt(ctx, projectID)
    if err != nil {
        return nil, fmt.Errorf("failed to get as-built: %w", err)
    }
    
    return ms.compareDesigns(design, asBuilt), nil
}
```

### 2. AI Services Integration

**Integration Points:**
```go
// internal/core/ai_integration.go
package core

import (
    "context"
    "encoding/json"
    "net/http"
)

type AIIntegration struct {
    aiClient *AIClient
}

func (ai *AIIntegration) AnalyzeSafetyPhotos(ctx context.Context, photos []string) (*SafetyAnalysis, error) {
    // Analyze safety photos for compliance violations
    request := &SafetyPhotoRequest{
        Photos: photos,
        Task:   "safety_compliance",
    }
    
    response, err := ai.aiClient.AnalyzeImages(ctx, request)
    if err != nil {
        return nil, err
    }
    
    return &SafetyAnalysis{
        Compliance: response.Compliance,
        Violations: response.Violations,
        Score:      response.Score,
    }, nil
}

func (ai *AIIntegration) PredictProjectDelays(ctx context.Context, scheduleData map[string]interface{}) (*DelayPrediction, error) {
    // Predict potential project delays using AI
    request := &DelayPredictionRequest{
        ScheduleData: scheduleData,
    }
    
    response, err := ai.aiClient.PredictDelays(ctx, request)
    if err != nil {
        return nil, err
    }
    
    return &DelayPrediction{
        RiskLevel:    response.RiskLevel,
        PredictedDelay: response.PredictedDelay,
        Recommendations: response.Recommendations,
    }, nil
}
```

### 3. IoT Services Integration

**Integration Points:**
```go
// internal/core/iot_integration.go
package core

import (
    "context"
    "time"
)

type IoTIntegration struct {
    iotClient *IoTClient
}

func (iot *IoTIntegration) MonitorSiteSafety(ctx context.Context, projectID string) (*SafetyMonitoring, error) {
    // Monitor safety sensors on construction site
    devices, err := iot.iotClient.GetProjectDevices(ctx, projectID)
    if err != nil {
        return nil, err
    }
    
    safetyData, err := iot.iotClient.GetSafetyData(ctx, devices)
    if err != nil {
        return nil, err
    }
    
    return &SafetyMonitoring{
        ProjectID:   projectID,
        AlertLevel:  safetyData.AlertLevel,
        Sensors:     safetyData.Sensors,
        LastUpdated: time.Now(),
    }, nil
}

func (iot *IoTIntegration) TrackEquipmentUsage(ctx context.Context, projectID string) (*EquipmentTracking, error) {
    // Track equipment usage and maintenance needs
    equipment, err := iot.iotClient.GetEquipment(ctx, projectID)
    if err != nil {
        return nil, err
    }
    
    usageData, err := iot.iotClient.GetEquipmentData(ctx, equipment)
    if err != nil {
        return nil, err
    }
    
    return &EquipmentTracking{
        ProjectID: projectID,
        Equipment: usageData.Equipment,
        Usage:     usageData.Usage,
        Alerts:    usageData.Alerts,
    }, nil
}
```

### 4. CMMS Integration

**Integration Points:**
```go
// internal/core/cmms_integration.go
package core

import (
    "context"
    "time"
)

type CMMSIntegration struct {
    cmmsClient *CMMSClient
}

func (cmms *CMMSIntegration) TrackEquipmentMaintenance(ctx context.Context, projectID string) (*MaintenanceSchedule, error) {
    // Track equipment maintenance schedules
    equipment, err := cmms.cmmsClient.GetProjectEquipment(ctx, projectID)
    if err != nil {
        return nil, err
    }
    
    schedule, err := cmms.cmmsClient.GetMaintenanceSchedule(ctx, equipment)
    if err != nil {
        return nil, err
    }
    
    return &MaintenanceSchedule{
        ProjectID: projectID,
        Equipment: schedule.Equipment,
        Schedule:  schedule.Schedule,
        NextMaintenance: schedule.NextMaintenance,
    }, nil
}

func (cmms *CMMSIntegration) TrackMaintenanceCosts(ctx context.Context, projectID string) (*MaintenanceCosts, error) {
    // Track maintenance costs for project
    costs, err := cmms.cmmsClient.GetProjectCosts(ctx, projectID)
    if err != nil {
        return nil, err
    }
    
    return &MaintenanceCosts{
        ProjectID: projectID,
        TotalCost: costs.TotalCost,
        Breakdown: costs.Breakdown,
        Monthly:   costs.Monthly,
    }, nil
}
```

## 🔐 Security Architecture

### Authentication & Authorization

```go
// internal/config/auth.go
package config

import (
    "context"
    "net/http"
    "strings"
    
    "github.com/golang-jwt/jwt/v5"
)

type AuthMiddleware struct {
    secretKey []byte
}

func (am *AuthMiddleware) Authenticate(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            http.Error(w, "Authorization header required", http.StatusUnauthorized)
            return
        }
        
        tokenString := strings.TrimPrefix(authHeader, "Bearer ")
        if tokenString == authHeader {
            http.Error(w, "Bearer token required", http.StatusUnauthorized)
            return
        }
        
        token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
            return am.secretKey, nil
        })
        
        if err != nil || !token.Valid {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }
        
        claims, ok := token.Claims.(jwt.MapClaims)
        if !ok {
            http.Error(w, "Invalid token claims", http.StatusUnauthorized)
            return
        }
        
        userID, ok := claims["sub"].(string)
        if !ok {
            http.Error(w, "Invalid user ID", http.StatusUnauthorized)
            return
        }
        
        ctx := context.WithValue(r.Context(), "user_id", userID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

### Data Security

```python
# services/construction/core/security.py
from cryptography.fernet import Fernet
import hashlib

class ConstructionSecurity:
    def __init__(self):
        self.cipher_suite = Fernet(os.getenv("ENCRYPTION_KEY").encode())
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive construction data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive construction data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def hash_document(self, document_content: bytes) -> str:
        """Create hash for document integrity verification"""
        return hashlib.sha256(document_content).hexdigest()
```

## 📊 Performance Architecture

### Caching Strategy

```go
// internal/core/cache.go
package core

import (
    "context"
    "encoding/json"
    "time"
    
    "github.com/go-redis/redis/v8"
)

type Cache struct {
    client *redis.Client
}

func (c *Cache) GetProjectData(ctx context.Context, projectID string) (*Project, error) {
    key := "project:" + projectID
    data, err := c.client.Get(ctx, key).Result()
    if err == redis.Nil {
        return nil, nil // Cache miss
    }
    if err != nil {
        return nil, err
    }
    
    var project Project
    err = json.Unmarshal([]byte(data), &project)
    if err != nil {
        return nil, err
    }
    
    return &project, nil
}

func (c *Cache) SetProjectData(ctx context.Context, projectID string, project *Project, ttl time.Duration) error {
    key := "project:" + projectID
    data, err := json.Marshal(project)
    if err != nil {
        return err
    }
    
    return c.client.Set(ctx, key, data, ttl).Err()
}
```

### Database Optimization

```sql
-- Indexes for performance
CREATE INDEX idx_construction_projects_status ON construction_projects(status);
CREATE INDEX idx_construction_projects_dates ON construction_projects(start_date, end_date);
CREATE INDEX idx_construction_schedules_project ON construction_schedules(project_id);
CREATE INDEX idx_construction_schedules_dates ON construction_schedules(start_date, end_date);
CREATE INDEX idx_construction_documents_project ON construction_documents(project_id);
CREATE INDEX idx_construction_documents_type ON construction_documents(type);
CREATE INDEX idx_construction_inspections_project ON construction_inspections(project_id);
CREATE INDEX idx_construction_inspections_date ON construction_inspections(scheduled_date);
CREATE INDEX idx_construction_safety_project ON construction_safety_incidents(project_id);
CREATE INDEX idx_construction_costs_project ON construction_costs(project_id);
```

## 🚀 Deployment Architecture

### Docker Configuration

```dockerfile
# services/construction/Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main ./cmd/main.go

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy the binary from builder stage
COPY --from=builder /app/main .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the binary
CMD ["./main"]
```

### Kubernetes Deployment

```yaml
# k8s/construction-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: construction-service
  namespace: arxos
spec:
  replicas: 3
  selector:
    matchLabels:
      app: construction-service
  template:
    metadata:
      labels:
        app: construction-service
    spec:
      containers:
      - name: construction-service
        image: arxos/construction-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: construction-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: construction-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: construction-service
  namespace: arxos
spec:
  selector:
    app: construction-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

## 📈 Monitoring & Observability

### Metrics Collection

```go
// internal/core/metrics.go
package core

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    projectRequests = promauto.NewCounter(prometheus.CounterOpts{
        Name: "construction_project_requests_total",
        Help: "Total project requests",
    })
    
    scheduleRequests = promauto.NewCounter(prometheus.CounterOpts{
        Name: "construction_schedule_requests_total",
        Help: "Total schedule requests",
    })
    
    documentUploads = promauto.NewCounter(prometheus.CounterOpts{
        Name: "construction_document_uploads_total",
        Help: "Total document uploads",
    })
    
    safetyIncidents = promauto.NewCounter(prometheus.CounterOpts{
        Name: "construction_safety_incidents_total",
        Help: "Total safety incidents",
    })
    
    requestDuration = promauto.NewHistogram(prometheus.HistogramOpts{
        Name: "construction_request_duration_seconds",
        Help: "Request duration",
    })
    
    activeProjects = promauto.NewGauge(prometheus.GaugeOpts{
        Name: "construction_active_projects",
        Help: "Number of active projects",
    })
)

func TrackRequest(requestType string) {
    switch requestType {
    case "project":
        projectRequests.Inc()
    case "schedule":
        scheduleRequests.Inc()
    case "document":
        documentUploads.Inc()
    }
}

func TrackSafetyIncident() {
    safetyIncidents.Inc()
}

func TrackRequestDuration(duration float64) {
    requestDuration.Observe(duration)
}

func UpdateActiveProjects(count float64) {
    activeProjects.Set(count)
}
```

### Logging Configuration

```go
// internal/config/logging.go
package config

import (
    "log"
    "os"
    "time"
    
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

func SetupLogging() *zap.Logger {
    config := zap.NewProductionConfig()
    config.EncoderConfig.TimeKey = "timestamp"
    config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
    
    logger, err := config.Build()
    if err != nil {
        log.Fatal("Failed to initialize logger:", err)
    }
    
    return logger
}

func LogProjectEvent(logger *zap.Logger, projectID, eventType string, details map[string]interface{}) {
    logger.Info("project_event",
        zap.String("project_id", projectID),
        zap.String("event_type", eventType),
        zap.Any("details", details),
        zap.Time("timestamp", time.Now()),
    )
}
```

## 🔄 Data Flow Architecture

### Request Flow

```
1. Client Request → API Gateway
2. API Gateway → Authentication Service
3. Authentication Service → Construction Service
4. Construction Service → Database/Cache
5. Construction Service → Integration Services (AI/IoT/BIM/CMMS)
6. Construction Service → Response to Client
```

### Real-time Updates Flow

```
1. IoT Sensors → IoT Service → Message Queue
2. Message Queue → Construction Service → WebSocket
3. WebSocket → Frontend → Real-time UI Updates
```

### SVGX BIM Integration Flow

```
1. Construction Progress Update → Construction Service
2. Construction Service → SVGX Bridge → SVGX Engine
3. SVGX Engine → Markup Update → Real-time BIM Visualization
4. SVGX Engine → Construction Service → Progress Validation
```

## 📋 API Design

### RESTful API Endpoints

```go
// api/projects.go
package api

import (
    "encoding/json"
    "net/http"
    "strconv"
    
    "github.com/go-chi/chi/v5"
    "arxos/construction/internal/core"
)

func ProjectsHandler() http.Handler {
    r := chi.NewRouter()
    
    r.Get("/", getProjects)
    r.Post("/", createProject)
    r.Get("/{projectID}", getProject)
    r.Put("/{projectID}", updateProject)
    r.Delete("/{projectID}", deleteProject)
    
    return r
}

func getProjects(w http.ResponseWriter, r *http.Request) {
    // Implementation for getting projects list
    projects, err := core.GetProjects(r.Context())
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    json.NewEncoder(w).Encode(map[string]interface{}{
        "success": true,
        "data":    projects,
    })
}

func createProject(w http.ResponseWriter, r *http.Request) {
    // Implementation for creating a new project
    var project core.Project
    if err := json.NewDecoder(r.Body).Decode(&project); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    createdProject, err := core.CreateProject(r.Context(), &project)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(map[string]interface{}{
        "success": true,
        "data":    createdProject,
    })
}
```

### WebSocket Endpoints

```python
# services/construction/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Project {project_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Project {project_id} disconnected")
```

## 🧪 Testing Architecture

### Unit Tests

```go
// tests/project_test.go
package tests

import (
    "context"
    "testing"
    
    "github.com/stretchr/testify/assert"
    "arxos/construction/internal/core"
)

func TestCreateProject(t *testing.T) {
    ctx := context.Background()
    
    project := &core.Project{
        Name:        "Test Project",
        Description: "Test Description",
        StartDate:   "2024-01-01",
        EndDate:     "2024-12-31",
        Budget:      1000000.00,
    }
    
    createdProject, err := core.CreateProject(ctx, project)
    
    assert.NoError(t, err)
    assert.NotNil(t, createdProject)
    assert.Equal(t, "Test Project", createdProject.Name)
    assert.Equal(t, "planning", createdProject.Status)
}

func TestGetProject(t *testing.T) {
    ctx := context.Background()
    projectID := "test-project-id"
    
    project, err := core.GetProject(ctx, projectID)
    
    assert.NoError(t, err)
    assert.NotNil(t, project)
    assert.Equal(t, projectID, project.ID)
}
```

### Integration Tests

```go
// tests/integration_test.go
package tests

import (
    "context"
    "testing"
    
    "github.com/stretchr/testify/assert"
    "arxos/construction/pkg/svgxbridge"
)

func TestSVGXIntegration(t *testing.T) {
    ctx := context.Background()
    
    sync := &svgxbridge.MarkupSync{}
    
    progress := svgxbridge.ConstructionProgress{
        ProjectID: "test-project",
        TaskID:    "test-task",
        Progress:  75.0,
        Status:    "in_progress",
    }
    
    err := sync.SyncConstructionProgress(ctx, progress)
    
    assert.NoError(t, err)
}

func TestAIIntegration(t *testing.T) {
    ctx := context.Background()
    
    ai := &core.AIIntegration{}
    photos := []string{"photo1.jpg", "photo2.jpg"}
    
    analysis, err := ai.AnalyzeSafetyPhotos(ctx, photos)
    
    assert.NoError(t, err)
    assert.NotNil(t, analysis)
    assert.NotEmpty(t, analysis.Compliance)
}
```

### End-to-End Tests

```python
# tests/e2e/test_construction_workflow.py
import pytest
from playwright.sync_api import sync_playwright

class TestConstructionWorkflow:
    def test_project_creation_workflow(self):
        """Test complete project creation workflow"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Navigate to construction app
            page.goto("http://localhost:3000/construction")
            
            # Create new project
            page.click("text=New Project")
            page.fill("[data-testid=project-name]", "Test Construction Project")
            page.fill("[data-testid=project-description]", "Test project description")
            page.fill("[data-testid=start-date]", "2024-01-01")
            page.fill("[data-testid=end-date]", "2024-12-31")
            page.fill("[data-testid=budget]", "1000000")
            page.click("text=Create Project")
            
            # Verify project created
            assert page.locator("text=Test Construction Project").is_visible()
            
            browser.close()
```

## 📚 Documentation Standards

### API Documentation

```python
# services/construction/api/projects.py
@router.post("/", response_model=Project, status_code=201)
async def create_project(
    project: ProjectCreate,
    current_user: str = Depends(get_current_user)
):
    """
    Create a new construction project.
    
    Args:
        project: Project creation data
        current_user: Authenticated user ID
    
    Returns:
        Project: Created project details
    
    Raises:
        HTTPException: If project creation fails
    """
    pass
```

### Code Documentation

```python
# services/construction/core/project_manager.py
class ProjectManager:
    """
    Manages construction project lifecycle operations.
    
    This class handles all project-related operations including creation,
    updates, deletion, and status management. It integrates with
    other services for comprehensive project management.
    """
    
    def __init__(self, db: Session):
        """
        Initialize ProjectManager with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.cache = ConstructionCache()
        self.ai = ConstructionAI()
    
    async def create_project(self, project_data: ProjectCreate, user_id: str) -> Project:
        """
        Create a new construction project.
        
        Args:
            project_data: Project creation data
            user_id: ID of user creating the project
        
        Returns:
            Project: Created project object
        
        Raises:
            ValidationError: If project data is invalid
            DatabaseError: If database operation fails
        """
        pass
```

---

**Created:** $(date)
**Status:** Architecture Design Complete
**Version:** 1.0.0
**Next Steps:** Implementation planning and development 