# ArxOS Platform Architecture v2

## Overview

This document describes the technical architecture for ArxOS as it evolves from a local CLI tool to a distributed platform for building intelligence. The architecture maintains backward compatibility while enabling cloud collaboration, AR visualization, and AI integration.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        ArxOS Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web App    │  │  Mobile App  │  │   CLI Tool   │      │
│  │  (arxos.io)  │  │  (iOS/Android)│  │   (arx)      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────┴──────────────────┴──────────────────┴───────┐     │
│  │                    API Gateway                      │     │
│  │              (REST / GraphQL / WebSocket)           │     │
│  └──────┬──────────────────┬──────────────────┬───────┘     │
│         │                  │                  │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │   Building   │  │     User     │  │   AI Proxy   │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────┴──────────────────┴──────────────────┴───────┐     │
│  │                  Data Layer                         │     │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │     │
│  │  │ SQLite  │  │   Git   │  │   S3    │            │     │
│  │  │   DB    │  │  Repos  │  │ Storage │            │     │
│  │  └─────────┘  └─────────┘  └─────────┘            │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Client Applications

#### Web Application (arxos.io)
- **Purpose**: Primary interface for building management
- **Technologies**: React/Next.js, TypeScript, Tailwind CSS
- **Features**:
  - Repository browsing and management
  - Visual PDF viewer with annotations
  - Work order creation and tracking
  - Analytics and reporting dashboards
  - Social features (stars, follows, contributions)

#### Mobile Application
- **Purpose**: Field operations and AR visualization
- **Technologies**: React Native or Flutter, ARCore/ARKit
- **Features**:
  - AR overlay for equipment visualization
  - Offline-first architecture
  - Voice-to-text documentation
  - QR/PDF scanning for access
  - Photo/video capture with annotations

#### CLI Tool (arx)
- **Purpose**: Power user interface and automation
- **Technologies**: Go (existing codebase)
- **Features**:
  - All existing CLI functionality
  - Cloud sync capabilities
  - AI command translation
  - Script execution

### 2. Backend Services

#### API Gateway
- **Purpose**: Unified entry point for all clients
- **Technologies**: Go, gRPC/REST
- **Responsibilities**:
  - Authentication and authorization
  - Request routing and load balancing
  - Rate limiting and throttling
  - API versioning
  - WebSocket connections for real-time updates

#### Building Service
- **Purpose**: Core building data management
- **Technologies**: Go (extending existing code)
- **Responsibilities**:
  - Building repository CRUD operations
  - Equipment and room management
  - PDF processing and storage
  - Change tracking and versioning
  - Search and query operations

#### User Service
- **Purpose**: User and organization management
- **Technologies**: Go
- **Responsibilities**:
  - User authentication (JWT/OAuth)
  - Organization and team management
  - Permission and access control
  - Contribution tracking
  - Billing and subscription management

#### AI Proxy Service
- **Purpose**: AI provider integration layer
- **Technologies**: Go, Python
- **Responsibilities**:
  - Provider abstraction (OpenAI, Anthropic, Google)
  - Context injection for AI queries
  - Token usage tracking
  - Response caching
  - Fallback handling

### 3. Data Layer

#### Primary Database (SQLite/PostgreSQL)
```sql
-- Core tables
buildings
equipment
rooms
users
organizations
contributions
work_orders
access_tokens

-- Relationship tables
building_users
equipment_connections
contribution_votes
```

#### Git Storage
- Building repositories with version control
- Distributed architecture support
- Multiple backend support (GitHub, self-hosted, S3)

#### Object Storage
- PDF files and documents
- Images and videos
- AR model data
- Export artifacts

## Key Architectural Patterns

### 1. Repository Structure

```
building-repo/
├── .arxos/
│   ├── config.yml              # Building configuration
│   ├── metadata.json           # Building metadata
│   └── access.log              # Access audit log
├── floors/
│   ├── floor-1/
│   │   ├── layout.json         # Floor plan data
│   │   ├── equipment.json      # Equipment inventory
│   │   └── rooms.json          # Room definitions
│   └── floor-2/
├── documents/
│   ├── architectural/          # PDF drawings
│   ├── electrical/
│   ├── mechanical/
│   └── plumbing/
├── scripts/
│   ├── maintenance.sh          # Automation scripts
│   └── reports.sql             # Query templates
└── README.md                   # Building overview
```

### 2. PDF-Based Access Control

```go
type PDFAccessToken struct {
    BuildingID   string
    Scope        []string  // Systems: hvac, electrical, etc.
    Permissions  []string  // read, write, annotate
    Floors       []int     // Accessible floors
    ExpiresAt    time.Time
    ContractorID string
    Signature    string    // Cryptographic signature
}

// Embed token in PDF metadata
func EmbedAccessToken(pdf *PDF, token PDFAccessToken) error {
    metadata := encodeToken(token)
    pdf.SetMetadata("ArxOS-Access", metadata)
    return pdf.Save()
}
```

### 3. Unsolicited Contribution Flow

```go
type UnsolicitedContribution struct {
    BuildingAddress string
    ContributorID   string
    Timestamp       time.Time
    Data           BuildingData
    Status         string // pending, accepted, rejected
    OwnerNotified  bool
}

// Workflow for unclaimed buildings
func ProcessContribution(contrib UnsolicitedContribution) error {
    // Create orphaned repository
    repo := CreateOrphanedRepo(contrib.BuildingAddress)
    
    // Add contribution as PR
    pr := CreatePullRequest(repo, contrib.Data)
    
    // Attempt owner discovery
    owner := DiscoverOwner(contrib.BuildingAddress)
    if owner != nil {
        NotifyOwner(owner, pr)
    }
    
    // Track for attribution
    RecordContribution(contrib.ContributorID, pr)
    
    return nil
}
```

### 4. AI Integration Layer

```go
type AIProvider interface {
    ProcessVoiceNote(audio []byte) (EquipmentData, error)
    TranslateToCommand(natural string) (ArxCommand, error)
    GenerateReport(data BuildingData, template string) (Report, error)
}

type AIGateway struct {
    providers map[string]AIProvider
    cache     Cache
}

func (g *AIGateway) Process(request AIRequest) (AIResponse, error) {
    // Check cache first
    if cached := g.cache.Get(request.Hash()); cached != nil {
        return cached, nil
    }
    
    // Route to configured provider
    provider := g.providers[request.Provider]
    response, err := provider.Process(request)
    
    // Cache successful responses
    if err == nil {
        g.cache.Set(request.Hash(), response)
    }
    
    return response, err
}
```

### 5. Offline-First Mobile Architecture

```typescript
// Mobile app offline sync
class OfflineSync {
    private queue: Change[] = [];
    private db: LocalDatabase;
    
    async captureChange(change: Change) {
        // Store locally first
        await this.db.save(change);
        this.queue.push(change);
        
        // Attempt sync if online
        if (this.isOnline()) {
            await this.syncChanges();
        }
    }
    
    async syncChanges() {
        while (this.queue.length > 0) {
            const batch = this.queue.splice(0, 10);
            try {
                await this.api.submitChanges(batch);
                await this.db.markSynced(batch);
            } catch (error) {
                // Re-queue failed changes
                this.queue.unshift(...batch);
                break;
            }
        }
    }
}
```

## Security Architecture

### Authentication & Authorization

```yaml
Authentication:
  - JWT tokens for API access
  - OAuth2 for third-party integrations
  - API keys for CLI/automation
  - PDF embedded tokens for contractors

Authorization:
  - Role-based access control (RBAC)
  - Building-level permissions
  - System-scoped access (HVAC only, etc.)
  - Time-limited contractor access
```

### Data Security

- **Encryption at Rest**: All sensitive data encrypted in database
- **Encryption in Transit**: TLS 1.3 for all communications
- **PDF Security**: Signed tokens prevent tampering
- **Audit Logging**: All access and changes logged
- **Compliance**: SOC2, GDPR, CCPA ready architecture

## Scalability Considerations

### Horizontal Scaling
- Stateless services for easy scaling
- Load balancing across service instances
- Database read replicas for query performance
- CDN for static assets and PDFs

### Performance Optimization
- Caching at multiple levels (CDN, API, Database)
- Lazy loading of building data
- Pagination for large datasets
- Background job processing for heavy operations

### Multi-Tenancy
- Logical isolation per organization
- Resource quotas and limits
- Separate databases for large enterprises
- Custom domains for white-labeling

## Integration Points

### External Systems
- **CMMS Integration**: REST APIs for work order sync
- **BIM Systems**: IFC file import/export
- **IoT Platforms**: Sensor data ingestion
- **Payment Systems**: Stripe/similar for subscriptions
- **Analytics**: Segment/Mixpanel for usage tracking

### AI Providers
```go
// Provider configuration
providers:
  openai:
    endpoint: https://api.openai.com/v1
    model: gpt-4
    maxTokens: 4000
  anthropic:
    endpoint: https://api.anthropic.com/v1
    model: claude-3-sonnet
    maxTokens: 4000
  google:
    endpoint: https://generativelanguage.googleapis.com/v1
    model: gemini-pro
    maxTokens: 4000
```

## Deployment Architecture

### Cloud-Native Deployment
```yaml
# Kubernetes deployment example
services:
  - api-gateway: 3 replicas, autoscaling
  - building-service: 5 replicas, autoscaling  
  - user-service: 3 replicas, autoscaling
  - ai-proxy: 2 replicas, fixed
  
databases:
  - postgresql: Managed service (RDS/CloudSQL)
  - redis: Managed service (ElastiCache/MemoryStore)
  
storage:
  - s3-compatible: Object storage for PDFs
  - git-repos: Managed Git service or self-hosted
```

### Development to Production Pipeline
1. **Local Development**: Docker Compose environment
2. **CI/CD**: GitHub Actions for testing and deployment
3. **Staging**: Scaled-down production replica
4. **Production**: Multi-region deployment with failover

## Migration Strategy

### From CLI to Platform
1. **Phase 1**: Add cloud sync to existing CLI
2. **Phase 2**: Launch web interface using same backend
3. **Phase 3**: Add mobile app with AR features
4. **Phase 4**: Enable full collaboration features

### Data Migration
```go
// Migrate existing local ArxOS installations
func MigrateToCloud(localPath string, cloudRepo string) error {
    // Load local state
    local := LoadLocalState(localPath)
    
    // Create cloud repository
    repo := CreateCloudRepo(cloudRepo)
    
    // Upload data preserving history
    for _, commit := range local.History {
        repo.ApplyCommit(commit)
    }
    
    // Configure local to sync with cloud
    local.SetRemote(cloudRepo)
    
    return nil
}
```

## Monitoring & Observability

### Metrics
- Application metrics (Prometheus)
- Business metrics (custom dashboards)
- User behavior (analytics platforms)
- Error tracking (Sentry)

### Logging
- Structured logging (JSON format)
- Centralized log aggregation (ELK stack)
- Audit trails for compliance
- Performance profiling

### Alerting
- Service health monitoring
- Error rate thresholds
- Performance degradation
- Security incidents

## Future Considerations

### Blockchain Integration
- Immutable audit trails
- Smart contracts for maintenance agreements
- Tokenized building ownership
- Decentralized data verification

### Edge Computing
- Local processing for large buildings
- Reduced latency for AR applications
- Offline-first enterprise deployments
- IoT gateway integration

### Machine Learning
- Predictive maintenance models
- Energy optimization algorithms
- Equipment failure prediction
- Automated issue detection

This architecture provides a solid foundation for evolving ArxOS from a CLI tool to a comprehensive platform while maintaining flexibility for future growth and adaptation.