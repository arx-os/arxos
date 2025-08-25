# ARXOS BIaC Technology Stack & Architecture

## Technology Stack Overview

### Core Technologies (Already in Use)
- **Backend**: Go 1.21+ (single binary deployment capability)
- **Database**: PostgreSQL 15+ with PostGIS (cloud) / SQLite 3.35+ with SpatiaLite (edge)
- **Frontend**: HTMX 1.9+ with Vanilla JavaScript (no React/Vue/Angular)
- **AI/ML**: Python 3.11+ with FastAPI (separate microservice)
- **CLI**: Cobra + Viper (Go libraries for CLI)
- **API**: RESTful with potential GraphQL for complex queries

### New Technologies for BIaC

#### State Management & Versioning
- **Merkle Trees**: For efficient state hashing and comparison
- **CRDT (Conflict-free Replicated Data Types)**: For distributed state synchronization
- **Protocol Buffers**: For efficient state serialization
- **Zstandard**: For state compression

#### Deployment & Orchestration
- **Temporal.io** (optional): For complex workflow orchestration
- **NATS/NATS JetStream**: For event streaming and command distribution
- **HashiCorp Raft**: For distributed consensus (multi-master edge nodes)

#### Edge Computing
- **SQLite**: Embedded database for edge nodes
- **SpatiaLite**: Spatial extension for SQLite
- **libp2p**: For peer-to-peer sync between edge nodes
- **QUIC Protocol**: For efficient data transfer

#### Monitoring & Observability
- **OpenTelemetry**: For distributed tracing
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Loki**: Log aggregation

---

## Application Architecture Layout

```
/arxos/
│
├── core/                                 # [EXISTING] Core Go application
│   ├── internal/
│   │   ├── arxobject/                  # [EXISTING] ArxObject implementation
│   │   ├── models/                     # [EXISTING] Data models
│   │   ├── handlers/                   # [EXISTING] HTTP handlers
│   │   │   ├── state/                  # [NEW] State management handlers
│   │   │   ├── deployment/             # [NEW] Deployment handlers
│   │   │   └── gitops/                 # [NEW] GitOps handlers
│   │   │
│   │   ├── state/                      # [NEW] State management core
│   │   │   ├── manager.go              # BuildingStateManager
│   │   │   ├── snapshot.go             # State snapshotting logic
│   │   │   ├── hash.go                 # Merkle tree hashing
│   │   │   ├── diff.go                 # State diff engine
│   │   │   └── store.go                # State persistence
│   │   │
│   │   ├── vcs/                        # [NEW] Version control system
│   │   │   ├── branch.go               # Branch management
│   │   │   ├── merge.go                # Merge strategies
│   │   │   ├── tag.go                  # Version tagging
│   │   │   ├── history.go              # History tracking
│   │   │   └── conflict.go             # Conflict resolution
│   │   │
│   │   ├── deployment/                 # [NEW] Deployment engine
│   │   │   ├── controller.go           # Main deployment controller
│   │   │   ├── strategies/             # Deployment strategies
│   │   │   │   ├── immediate.go
│   │   │   │   ├── canary.go
│   │   │   │   ├── rolling.go
│   │   │   │   └── blue_green.go
│   │   │   ├── rollback.go             # Rollback mechanism
│   │   │   ├── validation.go           # Pre-deployment validation
│   │   │   └── scheduler.go            # Deployment scheduling
│   │   │
│   │   ├── gitops/                     # [NEW] GitOps features
│   │   │   ├── pr.go                   # Pull request system
│   │   │   ├── review.go               # Code review workflow
│   │   │   ├── approval.go             # Approval mechanisms
│   │   │   └── webhook.go              # External integrations
│   │   │
│   │   ├── sync/                       # [NEW] Synchronization engine
│   │   │   ├── engine.go               # Main sync engine
│   │   │   ├── crdt.go                 # CRDT implementation
│   │   │   ├── protocol.go             # Sync protocol
│   │   │   ├── conflict.go             # Conflict resolution
│   │   │   └── queue.go                # Offline queue
│   │   │
│   │   ├── edge/                       # [NEW] Edge computing
│   │   │   ├── node.go                 # Edge node management
│   │   │   ├── registry.go             # Node registry
│   │   │   ├── health.go               # Health monitoring
│   │   │   └── coordinator.go          # Edge coordination
│   │   │
│   │   ├── templates/                  # [NEW] Configuration templates
│   │   │   ├── engine.go               # Template engine
│   │   │   ├── parser.go               # Template parser
│   │   │   ├── validator.go            # Template validation
│   │   │   └── registry.go             # Template registry
│   │   │
│   │   ├── orchestration/              # [NEW] Orchestration layer
│   │   │   ├── workflow.go             # Workflow engine
│   │   │   ├── scheduler.go            # Task scheduler
│   │   │   ├── executor.go             # Task executor
│   │   │   └── monitor.go              # Execution monitoring
│   │   │
│   │   └── events/                     # [NEW] Event system
│   │       ├── bus.go                  # Event bus
│   │       ├── publisher.go            # Event publisher
│   │       ├── subscriber.go           # Event subscriber
│   │       └── store.go                # Event store
│   │
│   ├── pkg/                            # [EXISTING] Shared packages
│   │   ├── merkle/                     # [NEW] Merkle tree implementation
│   │   ├── compress/                   # [NEW] Compression utilities
│   │   └── crypto/                     # [NEW] Cryptographic utilities
│   │
│   └── cmd/
│       ├── server/                     # [EXISTING] Main server
│       └── edge/                       # [NEW] Edge node binary
│
├── cmd/                                 # [EXISTING] CLI application
│   ├── commands/
│   │   ├── state/                      # [NEW] State management commands
│   │   │   ├── capture.go
│   │   │   ├── restore.go
│   │   │   ├── diff.go
│   │   │   └── branch.go
│   │   │
│   │   ├── deploy/                     # [NEW] Deployment commands
│   │   │   ├── create.go
│   │   │   ├── status.go
│   │   │   ├── rollback.go
│   │   │   └── validate.go
│   │   │
│   │   ├── gitops/                     # [NEW] GitOps commands
│   │   │   ├── pr.go
│   │   │   ├── merge.go
│   │   │   └── review.go
│   │   │
│   │   ├── portfolio/                  # [NEW] Portfolio commands
│   │   │   ├── list.go
│   │   │   ├── analyze.go
│   │   │   └── report.go
│   │   │
│   │   ├── edge/                       # [NEW] Edge commands
│   │   │   ├── init.go
│   │   │   ├── sync.go
│   │   │   └── status.go
│   │   │
│   │   └── maintenance/                # [NEW] Maintenance commands
│   │       ├── predict.go
│   │       ├── schedule.go
│   │       └── dispatch.go
│   │
│   └── client/                         # [EXISTING] API client
│       ├── state_client.go            # [NEW] State API client
│       ├── deployment_client.go       # [NEW] Deployment API client
│       └── sync_client.go             # [NEW] Sync API client
│
├── frontend/                           # [EXISTING] HTMX frontend
│   ├── templates/                      # [EXISTING] HTML templates
│   │   ├── state/                     # [NEW] State management UI
│   │   │   ├── viewer.html
│   │   │   ├── diff.html
│   │   │   └── history.html
│   │   │
│   │   ├── deployment/                # [NEW] Deployment UI
│   │   │   ├── dashboard.html
│   │   │   ├── create.html
│   │   │   └── monitor.html
│   │   │
│   │   ├── gitops/                    # [NEW] GitOps UI
│   │   │   ├── pr_list.html
│   │   │   ├── pr_detail.html
│   │   │   └── review.html
│   │   │
│   │   └── portfolio/                 # [NEW] Portfolio UI
│   │       ├── overview.html
│   │       ├── analytics.html
│   │       └── map.html
│   │
│   ├── static/
│   │   ├── js/
│   │   │   ├── state-manager.js      # [NEW] State management client
│   │   │   ├── deployment.js         # [NEW] Deployment client
│   │   │   ├── diff-viewer.js        # [NEW] Diff visualization
│   │   │   └── sync-worker.js        # [NEW] Service worker for offline
│   │   │
│   │   └── css/
│   │       ├── state.css             # [NEW] State UI styles
│   │       └── deployment.css        # [NEW] Deployment UI styles
│   │
│   └── components/                    # [NEW] Reusable HTMX components
│       ├── state-card.html
│       ├── deployment-status.html
│       └── diff-viewer.html
│
├── templates/                          # [NEW] Building configuration templates
│   ├── hvac/
│   │   ├── standard.yaml
│   │   ├── efficient.yaml
│   │   └── emergency.yaml
│   │
│   ├── electrical/
│   │   ├── standard.yaml
│   │   └── backup.yaml
│   │
│   ├── security/
│   │   ├── basic.yaml
│   │   └── enhanced.yaml
│   │
│   └── composite/                     # Composite templates
│       ├── office-standard.yaml
│       └── retail-standard.yaml
│
├── ai_service/                        # [EXISTING] Python ML service
│   ├── predictive/                    # [NEW] Predictive maintenance
│   │   ├── failure_prediction.py
│   │   ├── lifecycle_analysis.py
│   │   └── cost_estimation.py
│   │
│   └── optimization/                  # [NEW] Optimization algorithms
│       ├── energy_optimizer.py
│       ├── maintenance_scheduler.py
│       └── deployment_optimizer.py
│
├── migrations/                        # [EXISTING] Database migrations
│   ├── 200_building_states.sql      # [NEW] State tables
│   ├── 201_deployments.sql          # [NEW] Deployment tables
│   ├── 202_vcs_branches.sql         # [NEW] VCS tables
│   ├── 203_sync_metadata.sql        # [NEW] Sync tables
│   └── 204_edge_nodes.sql           # [NEW] Edge node registry
│
├── scripts/                          # [NEW] Operational scripts
│   ├── build/
│   │   ├── build_single_binary.sh   # Single binary builder
│   │   ├── embed_resources.sh       # Resource embedding
│   │   └── cross_compile.sh         # Cross-compilation
│   │
│   ├── deploy/
│   │   ├── deploy_edge.sh           # Edge deployment
│   │   └── update_edge.sh           # Edge updates
│   │
│   └── migration/
│       ├── migrate_to_biac.sh       # Migration helper
│       └── backup_states.sh         # State backup
│
├── config/                           # [EXISTING] Configuration
│   ├── biac.yaml                    # [NEW] BIaC configuration
│   ├── edge.yaml                    # [NEW] Edge node config
│   └── sync.yaml                    # [NEW] Sync configuration
│
├── tests/                            # [EXISTING] Test directory
│   ├── state/                       # [NEW] State tests
│   ├── deployment/                  # [NEW] Deployment tests
│   ├── sync/                        # [NEW] Sync tests
│   └── edge/                        # [NEW] Edge tests
│
├── docs/                             # [EXISTING] Documentation
│   ├── biac/                        # [NEW] BIaC documentation
│   │   ├── concepts.md
│   │   ├── state-management.md
│   │   ├── deployment-guide.md
│   │   ├── gitops-workflow.md
│   │   └── edge-computing.md
│   │
│   └── api/                         # [EXISTING] API docs
│       ├── state-api.md            # [NEW] State API
│       ├── deployment-api.md       # [NEW] Deployment API
│       └── sync-api.md             # [NEW] Sync API
│
└── build/                            # [NEW] Build artifacts
    ├── binaries/                    # Compiled binaries
    ├── docker/                      # Docker images
    └── k8s/                         # Kubernetes manifests

```

---

## Data Flow Architecture

### 1. State Management Flow
```
Field Input → ArxObject Update → State Capture → Hash Calculation → Version Storage
     ↓              ↓                 ↓              ↓                    ↓
  HTMX Form    Validation      State Manager   Merkle Tree         PostgreSQL
```

### 2. Deployment Flow
```
Config Template → Target Selection → Validation → Deployment → Monitoring
       ↓               ↓                ↓            ↓            ↓
  Template Engine   AQL Query      Pre-flight   Controller   Prometheus
```

### 3. Sync Flow (Edge ↔ Cloud)
```
Local Change → Queue → Batch → Compress → Transfer → Merge → Acknowledge
      ↓          ↓       ↓         ↓          ↓        ↓         ↓
  SQLite     OfflineQ  Aggregator  Zstd     QUIC    CRDT    Response
```

---

## Database Schema Architecture

### Core Tables (PostgreSQL/SQLite)

```sql
-- State Management Tables
building_states
├── id (UUID)
├── building_id (FK)
├── version (semantic)
├── config_hash (SHA-256)
├── arxobject_snapshot (JSONB/compressed)
├── systems_state (JSONB)
├── branch (varchar)
└── parent_version (FK)

state_transitions
├── id (UUID)
├── from_state_id (FK)
├── to_state_id (FK)
├── transition_type
├── initiated_by
└── timestamp

-- Deployment Tables
deployments
├── id (UUID)
├── name
├── config_template_id (FK)
├── target_query (AQL)
├── strategy (enum)
├── status
└── schedule (JSONB)

deployment_targets
├── deployment_id (FK)
├── building_id (FK)
├── status
├── started_at
└── completed_at

-- VCS Tables
branches
├── id (UUID)
├── building_id (FK)
├── branch_name
├── base_version
├── head_version
└── protected (bool)

pull_requests
├── id (UUID)
├── source_branch (FK)
├── target_branch (FK)
├── status
├── reviewers (JSONB)
└── approvals (JSONB)

-- Sync Tables
sync_queue
├── id (UUID)
├── node_id (FK)
├── operation_type
├── payload (JSONB)
├── status
└── retry_count

edge_nodes
├── id (UUID)
├── node_name
├── building_id (FK)
├── last_sync
├── status
└── capabilities (JSONB)
```

---

## Service Architecture

### Microservices Communication

```yaml
services:
  core-api:
    type: REST/GraphQL
    port: 8080
    responsibilities:
      - ArxObject management
      - State management
      - Deployment orchestration
      - API gateway

  sync-service:
    type: gRPC
    port: 9090
    responsibilities:
      - Edge synchronization
      - Conflict resolution
      - Queue management

  event-bus:
    type: NATS JetStream
    port: 4222
    responsibilities:
      - Event distribution
      - Command routing
      - State notifications

  ai-service:
    type: REST
    port: 8000
    responsibilities:
      - Predictive analytics
      - Optimization
      - Anomaly detection

  metrics-service:
    type: Prometheus
    port: 9091
    responsibilities:
      - Metrics collection
      - Performance monitoring
      - Alert generation
```

---

## Network Architecture

### Edge-Cloud Topology

```
┌─────────────────────────────────────────────────────┐
│                   Cloud (Primary)                    │
│  ┌─────────────────────────────────────────────┐   │
│  │  PostgreSQL  │  Core API  │  Event Bus      │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────┬─────────────┬─────────────────────┘
                  │             │
         QUIC/TLS │             │ WebSocket
                  │             │
    ┌─────────────┴──────┐ ┌───┴──────────────┐
    │   Edge Node A      │ │   Edge Node B     │
    │  ┌──────────────┐  │ │  ┌──────────────┐│
    │  │SQLite│Engine │  │ │  │SQLite│Engine ││
    │  └──────────────┘  │ │  └──────────────┘│
    └────────────────────┘ └──────────────────┘
           Building A           Building B
```

---

## Security Architecture

### Security Layers

```
1. Network Security
   - TLS 1.3 for all communications
   - mTLS for edge-cloud communication
   - QUIC with 0-RTT for performance

2. Data Security
   - Encryption at rest (AES-256)
   - State hashing (SHA-256)
   - Signed commits (Ed25519)

3. Access Control
   - RBAC for user permissions
   - Branch protection rules
   - Deployment approval workflows

4. Audit Trail
   - All state changes logged
   - Deployment history tracked
   - Sync operations recorded
```

---

## Performance Architecture

### Optimization Strategies

```
1. State Management
   - Incremental snapshots
   - Compression (Zstandard)
   - Merkle tree for efficient diff
   - Lazy loading of historical states

2. Deployment
   - Parallel deployment execution
   - Batch operations
   - Connection pooling
   - Query optimization

3. Sync
   - Delta synchronization
   - Compression before transfer
   - Batched operations
   - Conflict-free data types (CRDT)

4. Edge
   - Local caching
   - Offline-first design
   - Background sync
   - Resource constraints handling
```

---

## Integration Points

### External Systems

```yaml
integrations:
  version_control:
    - GitHub (PR webhooks)
    - GitLab (merge requests)
    - Bitbucket (pull requests)

  monitoring:
    - Prometheus (metrics)
    - Grafana (dashboards)
    - PagerDuty (alerts)
    - Datadog (APM)

  building_systems:
    - BACnet (building automation)
    - Modbus (industrial control)
    - MQTT (IoT devices)
    - OPC UA (SCADA)

  enterprise:
    - SAP (ERP integration)
    - ServiceNow (ITSM)
    - Salesforce (CRM)
    - Azure AD (SSO)
```

---

## Development Workflow

### Local Development Setup

```bash
# Core services
docker-compose up -d postgres redis nats

# Run core API
go run core/cmd/server/main.go

# Run edge node (SQLite)
go run core/cmd/edge/main.go --mode=local

# Run AI service
cd ai_service && python main.py

# Run frontend dev server
cd frontend && npm run dev

# Run CLI in dev mode
go run cmd/main.go --config=config/dev.yaml
```

### Build Process

```bash
# Build single binary (cloud version)
./scripts/build/build_single_binary.sh --target=cloud

# Build edge binary (with SQLite)
./scripts/build/build_single_binary.sh --target=edge

# Cross-compile for multiple platforms
./scripts/build/cross_compile.sh

# Build Docker images
docker build -t arxos/core:latest -f docker/core.Dockerfile .
docker build -t arxos/edge:latest -f docker/edge.Dockerfile .
```

---

## Testing Strategy

### Test Pyramid

```
         /\
        /  \    E2E Tests (10%)
       /    \   - Full deployment scenarios
      /      \  - Edge-cloud sync
     /________\ 
    /          \ Integration Tests (30%)
   /            \ - API endpoints
  /              \ - Database operations
 /________________\ - Service communication
/                  \
/                    \ Unit Tests (60%)
/______________________\ - Business logic
                         - State management
                         - Deployment strategies
```

---

## Deployment Architecture

### Cloud Deployment (Kubernetes)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos-core
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: arxos-core
        image: arxos/core:latest
        env:
        - name: DB_TYPE
          value: "postgres"
        - name: MODE
          value: "cloud"
```

### Edge Deployment (Single Binary)

```bash
# Download and install edge binary
curl -L https://arxos.io/edge/install.sh | sh

# Initialize edge node
arxos edge init --building-id=BLDG-123 --sync-url=https://cloud.arxos.io

# Run as systemd service
sudo systemctl enable arxos-edge
sudo systemctl start arxos-edge
```

---

## Monitoring & Observability

### Metrics Collection

```go
// Prometheus metrics
var (
    stateCaptureDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "arxos_state_capture_duration_seconds",
            Help: "Duration of state capture operations",
        },
        []string{"building_id"},
    )
    
    deploymentStatus = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "arxos_deployment_status",
            Help: "Current deployment status",
        },
        []string{"deployment_id", "status"},
    )
    
    syncQueueSize = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "arxos_sync_queue_size",
            Help: "Number of items in sync queue",
        },
        []string{"node_id"},
    )
)
```

---

## Configuration Management

### Environment-Specific Configs

```yaml
# config/biac.yaml
environments:
  development:
    state:
      capture_interval: 5m
      retention_days: 7
    deployment:
      require_approval: false
      rollback_threshold: 0.5
    sync:
      batch_size: 100
      interval: 30s

  production:
    state:
      capture_interval: 1h
      retention_days: 90
    deployment:
      require_approval: true
      rollback_threshold: 0.95
    sync:
      batch_size: 1000
      interval: 5m
```

---

## Error Handling & Recovery

### Failure Scenarios

```go
// Automatic recovery strategies
type RecoveryStrategy interface {
    Detect(error) bool
    Recover(context.Context) error
}

var strategies = []RecoveryStrategy{
    &NetworkFailureRecovery{},
    &DatabaseFailureRecovery{},
    &SyncConflictRecovery{},
    &DeploymentFailureRecovery{},
}
```

---

This architecture provides:

1. **Clear separation of concerns** - Each component has a specific responsibility
2. **Scalability** - Can handle enterprise-scale deployments
3. **Resilience** - Multiple failure recovery mechanisms
4. **Flexibility** - Supports both cloud and edge deployments
5. **Maintainability** - Well-organized code structure
6. **Testability** - Clear boundaries for testing
7. **Performance** - Optimized for both online and offline operations

The implementation follows Go best practices, maintains the existing ARXOS philosophy of minimal complexity, and integrates seamlessly with the current codebase.