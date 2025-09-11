# ArxOS Technology Stack & Architecture

## Current Implementation (What We Have Built)

### Core Technologies

#### Language & Framework
- **Go 1.24.5** - Primary language for all backend services
- **Cobra** - CLI framework for command structure
- **Testify** - Testing framework

#### Data Storage
- **SQLite** (modernc.org/sqlite) - Local database with spatial indexing
- **JSON** - File-based state management in `.arxos/` directory
- **Git** - Version control integration for change tracking

#### PDF Processing
- **pdfcpu v0.11.0** - PDF parsing and generation
- **Custom Parsers** - Multiple extraction strategies:
  - Simple text extraction
  - Content stream parsing
  - Form field extraction
  - OCR fallback capability

#### Terminal & Visualization
- **ASCII Rendering** - Custom terminal-based visualization
- **ABIM (ASCII Building Information Model)** - Layered rendering system
  - 30 FPS update rate
  - Dirty rectangle optimization
  - Z-ordered layer composition

### Current Architecture

```
Current ArxOS CLI Architecture
┌─────────────────────────────────────────┐
│             CLI (arx)                   │
├─────────────────────────────────────────┤
│  cmd/arx/                               │
│  ├── main.go          (entry point)     │
│  ├── navigation.go    (routing)         │
│  ├── connections.go   (equipment links) │
│  ├── electrical.go    (systems)         │
│  ├── energy.go        (flow tracking)   │
│  ├── maintenance.go   (scheduling)      │
│  └── [15 command files total]           │
├─────────────────────────────────────────┤
│  internal/                              │
│  ├── ascii/           (rendering)       │
│  │   ├── abim/        (core renderer)   │
│  │   ├── layers/      (compositing)     │
│  │   └── isometric/   (3D views)        │
│  ├── database/        (SQLite)          │
│  ├── pdf/             (import/export)   │
│  ├── state/           (JSON management) │
│  ├── vcs/             (Git integration) │
│  ├── connections/     (graph analysis)  │
│  └── particles/       (physics sim)     │
├─────────────────────────────────────────┤
│  pkg/models/                            │
│  ├── floor.go         (data models)     │
│  └── floor_test.go                      │
├─────────────────────────────────────────┤
│  Local Storage                          │
│  ├── .arxos/          (JSON state)      │
│  ├── SQLite DB        (queries)         │
│  └── Git repo         (history)         │
└─────────────────────────────────────────┘
```

### Existing Capabilities

#### Data Models (pkg/models/)
```go
type FloorPlan struct {
    Name      string
    Building  string
    Level     int
    Rooms     []Room
    Equipment []Equipment
    CreatedAt time.Time
    UpdatedAt time.Time
}

type Equipment struct {
    ID       string
    Name     string
    Type     string
    Location Point
    Status   EquipmentStatus
    RoomID   string
}
```

#### Database Layer (internal/database/)
- SQLite with migrations
- Spatial indexing for proximity searches
- Connection graph for equipment relationships
- Query interface for complex searches

#### PDF Processing (internal/pdf/)
- Universal parser with multiple strategies
- OCR integration capability
- PDF export with annotations
- Professional report generation

#### Visualization (internal/ascii/)
- Multi-layer rendering system
- Real-time particle simulation
- Energy flow visualization
- Failure zone mapping

## Platform Evolution (What We Will Build)

### New Technology Additions

#### Backend Services (Go)
```yaml
New Services:
  - API Gateway (Go + Chi/Gin router)
  - User Service (Go + JWT auth)
  - Building Service (extends current code)
  - AI Proxy Service (Go + provider SDKs)
  - Notification Service (Go + email/SMS)
  - Analytics Service (Go + time-series DB)
```

#### Web Platform Stack
```yaml
Frontend:
  - Framework: Next.js 14+ (React)
  - Language: TypeScript
  - Styling: Tailwind CSS
  - State: Zustand or Redux Toolkit
  - API Client: Axios + React Query
  - PDF Viewer: PDF.js
  - Real-time: Socket.io or native WebSockets
  - Auth: NextAuth.js

Build Tools:
  - Bundler: Webpack (via Next.js)
  - Testing: Jest + React Testing Library
  - E2E: Playwright or Cypress
  - CI/CD: GitHub Actions
```

#### Mobile Application Stack
```yaml
Framework Options:
  Option 1 - React Native:
    - Core: React Native 0.72+
    - Navigation: React Navigation
    - State: Redux + Redux Persist
    - AR: ViroReact or React Native AR
    
  Option 2 - Flutter:
    - Core: Flutter 3.0+
    - Language: Dart
    - AR: ARCore/ARKit plugins
    - State: Provider or Riverpod

Shared Mobile Tech:
  - Offline: SQLite + sync queue
  - Camera: Native camera APIs
  - Voice: Native speech-to-text
  - Storage: Encrypted local storage
```

#### Cloud Infrastructure
```yaml
Primary Cloud (AWS/GCP/Azure):
  Compute:
    - Kubernetes (EKS/GKE/AKS)
    - Container Registry
    - Load Balancers
    
  Storage:
    - PostgreSQL (RDS/CloudSQL)
    - Redis (ElastiCache/MemoryStore)
    - S3/GCS/Blob (PDF storage)
    
  Services:
    - CDN (CloudFront/Cloud CDN)
    - API Gateway
    - Lambda/Cloud Functions (async jobs)
    - SQS/PubSub (message queuing)

Monitoring:
  - Prometheus + Grafana
  - ELK Stack (logs)
  - Sentry (errors)
  - DataDog or New Relic (APM)
```

#### AI Integration Layer
```yaml
AI Providers:
  - OpenAI API (GPT-4, Whisper)
  - Anthropic API (Claude)
  - Google AI (Gemini, PaLM)
  
Integration:
  - LangChain (Go/Python)
  - Vector DB (Pinecone/Weaviate)
  - Prompt templates
  - Context injection system
```

### Integrated Architecture

```
Full Platform Architecture
┌──────────────────────────────────────────────────────────┐
│                    Client Applications                   │
├──────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │   CLI    │  │   Web    │  │  Mobile  │  │    AR    ││
│  │   (Go)   │  │(Next.js) │  │  (RN/F)  │  │  Layer   ││
│  └─────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘│
│        └────────────┴──────────────┴──────────────┘      │
│                            │                              │
├────────────────────────────▼──────────────────────────────┤
│                      API Gateway                          │
│                   (Go + REST/GraphQL)                     │
├──────────────────────────────────────────────────────────┤
│                     Service Mesh                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │  │Building  │  │   User   │  │    AI    │        │  │
│  │  │ Service  │  │ Service  │  │  Proxy   │        │  │
│  │  │   (Go)   │  │   (Go)   │  │   (Go)   │        │  │
│  │  └──────────┘  └──────────┘  └──────────┘        │  │
│  │                                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │  │  Asset   │  │Analytics │  │  Notify  │        │  │
│  │  │ Service  │  │ Service  │  │ Service  │        │  │
│  │  │   (Go)   │  │   (Go)   │  │   (Go)   │        │  │
│  │  └──────────┘  └──────────┘  └──────────┘        │  │
│  └────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────┤
│                      Data Layer                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │  │PostgreSQL│  │  Redis   │  │    S3    │        │  │
│  │  │(Primary) │  │ (Cache)  │  │ (Files)  │        │  │
│  │  └──────────┘  └──────────┘  └──────────┘        │  │
│  │                                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │  │   Git    │  │  Vector  │  │ TimeSeries│       │  │
│  │  │  Repos   │  │    DB    │  │    DB     │       │  │
│  │  └──────────┘  └──────────┘  └──────────┘        │  │
│  └────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────┤
│                   External Integrations                   │
│  ┌────────────────────────────────────────────────────┐  │
│  │  AI Providers │ Payment │ Email │ SMS │ OAuth     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Technology Migration Path

### Phase 0: Foundation (Current → Cloud-Ready)

```go
// Current: Local-only state
stateManager := state.NewManager(".arxos")

// Upgrade: Cloud-aware state
stateManager := state.NewManager(state.Config{
    LocalPath:  ".arxos",
    RemoteURL:  "https://api.arxos.io",
    SyncMode:   state.SyncBidirectional,
})
```

### Phase 1: API Development

```go
// New API service extending current code
package api

import (
    "github.com/joelpate/arxos/internal/database"
    "github.com/joelpate/arxos/pkg/models"
)

type BuildingAPI struct {
    db database.DB  // Reuse existing database layer
}

func (api *BuildingAPI) GetBuilding(id string) (*models.FloorPlan, error) {
    // Leverage existing database methods
    return api.db.GetFloorPlan(context.Background(), id)
}
```

### Phase 2: Web Platform

```typescript
// Next.js app structure
arxos-web/
├── app/
│   ├── page.tsx                 // Landing page
│   ├── buildings/
│   │   ├── page.tsx             // Building list
│   │   └── [id]/
│   │       ├── page.tsx         // Building detail
│   │       ├── equipment/       // Equipment management
│   │       └── ar-preview/      // AR visualization preview
│   ├── api/
│   │   └── [...proxy].ts        // API proxy to Go backend
│   └── auth/
│       └── [...nextauth].ts     // Authentication
├── components/
│   ├── PDFViewer.tsx            // PDF.js wrapper
│   ├── EquipmentMap.tsx         // Interactive floor plan
│   └── ARPreview.tsx            // AR visualization preview
└── lib/
    ├── api-client.ts            // Axios + React Query
    └── websocket.ts             // Real-time updates
```

### Phase 3: Mobile Development

```typescript
// React Native structure
arxos-mobile/
├── src/
│   ├── screens/
│   │   ├── BuildingList.tsx
│   │   ├── ARCamera.tsx         // AR visualization
│   │   └── EquipmentScan.tsx    // QR/barcode scanning
│   ├── services/
│   │   ├── api.ts               // API client
│   │   ├── offline.ts           // Offline queue
│   │   └── ar.ts                // AR services
│   └── components/
│       ├── VoiceInput.tsx       // Voice to text
│       └── PhotoCapture.tsx     // Annotated photos
```

### Phase 4: AI Integration

```go
// AI abstraction layer
package ai

type Provider interface {
    ProcessVoice(audio []byte) (string, error)
    GenerateCommand(prompt string) (string, error)
    GenerateReport(data interface{}) (string, error)
}

type OpenAIProvider struct {
    client *openai.Client
}

type AnthropicProvider struct {
    client *anthropic.Client
}

// Usage in CLI
func (c *CLI) ProcessNaturalLanguage(input string) {
    provider := ai.GetConfiguredProvider()
    command, _ := provider.GenerateCommand(input)
    c.Execute(command)
}
```

## Development Tools & Pipeline

### Development Environment
```yaml
Local Development:
  - Docker Compose for services
  - Hot reload for all components
  - Local S3 (MinIO)
  - Local PostgreSQL
  - Mock AI responses

Tools:
  - VS Code with Go/TypeScript extensions
  - Postman/Insomnia for API testing
  - React DevTools
  - Redux DevTools
  - ngrok for mobile testing
```

### CI/CD Pipeline
```yaml
GitHub Actions:
  - Go tests on every push
  - TypeScript/Jest tests
  - E2E tests (Playwright)
  - Docker build & push
  - Deployment to staging
  - Production deployment (manual approval)

Quality Gates:
  - Test coverage > 80%
  - No critical security issues
  - Performance benchmarks pass
  - Documentation updated
```

### Deployment Strategy
```yaml
Staging:
  - Kubernetes cluster (3 nodes)
  - Single region
  - Shared database
  - Feature flags for testing

Production:
  - Multi-region Kubernetes
  - Database replication
  - CDN for static assets
  - Blue-green deployments
  - Automated rollback on errors
```

## Technology Decisions & Rationale

### Why Keep Go for Backend?
- **Existing Investment**: Significant codebase already in Go
- **Performance**: Excellent for building services
- **Simplicity**: Easy to maintain and deploy
- **Concurrency**: Great for handling multiple requests
- **Single Binary**: Simple deployment model

### Why Next.js for Web?
- **Full-Stack**: API routes + React in one framework
- **Performance**: Server-side rendering, edge functions
- **Developer Experience**: Hot reload, TypeScript support
- **SEO**: Important for public building repos
- **Ecosystem**: Rich component libraries available

### Why React Native/Flutter for Mobile?
- **Cross-Platform**: One codebase for iOS/Android
- **AR Support**: Good AR libraries available
- **Offline First**: Strong offline capabilities
- **Developer Velocity**: Faster than native development
- **Community**: Large ecosystem of plugins

### Why PostgreSQL Over SQLite for Cloud?
- **Concurrency**: Better multi-user support
- **Scalability**: Can handle millions of buildings
- **Features**: Advanced queries, full-text search
- **Managed Services**: RDS/CloudSQL availability
- **Migration Path**: SQLite → PostgreSQL is straightforward

## Security Architecture

### Authentication & Authorization
```yaml
Authentication:
  - JWT tokens (15-minute expiry)
  - Refresh tokens (7-day expiry)
  - OAuth2 for enterprise SSO
  - API keys for CLI/automation

Authorization:
  - RBAC with custom policies
  - Building-level permissions
  - PDF-embedded access tokens
  - Time-based access control
```

### Data Security
```yaml
Encryption:
  - TLS 1.3 for all traffic
  - AES-256 for data at rest
  - Encrypted PDF tokens
  - Secure key management (KMS)

Compliance:
  - SOC2 Type II ready
  - GDPR compliant architecture
  - CCPA compliant
  - Audit logging for all actions
```

## Performance Targets

### API Response Times
- **P50**: < 100ms
- **P95**: < 500ms
- **P99**: < 1000ms

### Mobile App Performance
- **Cold Start**: < 2 seconds
- **AR Frame Rate**: 30+ FPS
- **Offline Sync**: < 5 seconds
- **Battery Impact**: < 5% per hour

### Web Platform Performance
- **Page Load**: < 1 second
- **Time to Interactive**: < 2 seconds
- **Lighthouse Score**: 90+
- **Bundle Size**: < 500KB initial

## Cost Optimization

### Infrastructure Costs (Monthly)
```yaml
Phase 1 (0-1K users):
  - Compute: $200 (small instances)
  - Database: $100 (basic RDS)
  - Storage: $50 (S3)
  - CDN: $50
  - Total: ~$400/month

Phase 2 (1K-10K users):
  - Compute: $1,000 (auto-scaling)
  - Database: $500 (larger RDS)
  - Storage: $300
  - CDN: $200
  - Total: ~$2,000/month

Phase 3 (10K+ users):
  - Compute: $5,000
  - Database: $2,000 (read replicas)
  - Storage: $1,500
  - CDN: $1,000
  - Total: ~$10,000/month
```

### Optimization Strategies
- **Caching**: Redis for frequent queries
- **CDN**: Static assets and PDFs
- **Lazy Loading**: Load data on demand
- **Image Optimization**: WebP, responsive images
- **Code Splitting**: Reduce initial bundle size
- **Database Indexing**: Optimize query performance

## Future Technology Considerations

### Potential Additions
- **GraphQL**: For flexible API queries
- **WebAssembly**: For client-side PDF processing
- **Blockchain**: For immutable audit trails
- **IoT Integration**: MQTT for sensor data
- **ML Models**: TensorFlow Lite for on-device AI
- **WebRTC**: For real-time collaboration

This technology stack provides a solid foundation that leverages existing Go code while adding modern web and mobile capabilities for the platform vision.