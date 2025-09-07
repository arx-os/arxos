# ArxOS Architecture

## Overview

ArxOS implements a sophisticated event-driven architecture that transforms physical buildings into queryable, real-time databases with tokenized economic incentives. The system is built on Rust for performance and safety, PostgreSQL for persistent storage, and leverages modern patterns for scalability.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Systems                         │
│  (Trading Platforms, IoT Devices, Building Management Systems)   │
└─────────────────┬───────────────────────────┬───────────────────┘
                  │                           │
                  ▼                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│                    (REST + SSE + WebSockets)                     │
└─────────────────┬───────────────────────────┬───────────────────┘
                  │                           │
    ┌─────────────▼─────────────┐ ┌──────────▼──────────┐
    │    Terminal Interface     │ │    Web Interface    │
    │   (CLI Navigation Tool)   │ │  (Future: Web UI)   │
    └───────────────────────────┘ └─────────────────────┘
                  │                           │
┌─────────────────▼───────────────────────────▼───────────────────┐
│                      Core ArxOS Engine                           │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Building   │  │    BILT      │  │    Market    │          │
│  │   Objects    │◄─┤   Rating     │◄─┤ Integration  │          │
│  │   Service    │  │   Engine     │  │   Service    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│  ┌──────▼────────────────▼──────────────────▼───────┐          │
│  │              Event System (Pub/Sub)               │          │
│  │         PostgreSQL LISTEN/NOTIFY + Channels       │          │
│  └────────────────────────┬──────────────────────────┘          │
│                           │                                      │
│  ┌────────────────────────▼──────────────────────────┐          │
│  │           Database Abstraction Layer              │          │
│  │              (Connection Pooling)                 │          │
│  └────────────────────────┬──────────────────────────┘          │
└───────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     PostgreSQL Database                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Objects    │  │   Ratings    │  │   Markets    │         │
│  │   & State    │  │  & History   │  │  & Tokens    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└───────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Building Objects Service (`src/core/`)

The heart of ArxOS - manages the hierarchical representation of building infrastructure as navigable objects.

**Key Responsibilities:**
- Object CRUD operations
- Hierarchical path navigation (`/electrical/circuits/2/outlet_2A`)
- State management and health tracking
- Location and spatial queries
- Property management (JSON)

**Design Patterns:**
- Repository pattern for data access
- Command pattern for operations
- Observer pattern for state changes

### 2. BILT Rating Engine (`src/rating/`)

Algorithmic valuation system that calculates building grades from 0z (minimal) to 1A (digital twin).

**Key Responsibilities:**
- Calculate ratings based on 7 components
- Real-time rating triggers on data changes
- Historical rating tracking
- Grade progression management

**Components:**
```rust
pub struct RatingComponents {
    pub structure_score: f64,    // Floor plans, spaces
    pub inventory_score: f64,    // Object documentation
    pub metadata_score: f64,     // Properties completeness
    pub sensors_score: f64,      // IoT integration
    pub history_score: f64,      // Maintenance records
    pub quality_score: f64,      // Data verification
    pub activity_score: f64,     // Recent contributions
}
```

**Algorithm:**
- Weighted scoring system
- Exponential value for higher grades
- Immediate recalculation on triggers
- Cache with 5-minute TTL

### 3. Market Integration Service (`src/market/`)

Token economics and contribution tracking system.

**Key Responsibilities:**
- Contribution recording and validation
- Token distribution calculations
- Reputation management
- Market data feeds
- Incentive algorithms

**Token Flow:**
```
Worker Contribution → Validation → Rating Impact → Token Reward
                          ↓              ↓              ↓
                    Reputation++    BILT Grade↑    Market Signal
```

### 4. Event System (`src/events/`)

Real-time event propagation using PostgreSQL LISTEN/NOTIFY.

**Event Types:**
- Object lifecycle: created, updated, deleted
- State changes: status, health, repair needs
- Rating events: calculated, changed
- Market events: contribution, reward, trade

**Event Flow:**
```
Database Trigger → NOTIFY channel → Event System → Subscribers
                                           ↓
                                    SSE/Webhook/Internal
```

### 5. API Layer (`src/api/`)

RESTful API with real-time capabilities.

**Endpoints:**
- `/api/objects` - Building object CRUD
- `/api/query` - SQL query interface
- `/api/buildings/{id}/rating` - BILT ratings
- `/api/contributions` - Record work
- `/api/events` - SSE stream
- `/api/webhooks` - External integrations

**Security:**
- API key authentication
- Rate limiting (100 req/min default)
- SQL injection prevention
- HMAC webhook signatures

### 6. Terminal Interface (`src/terminal.rs`)

Command-line navigation tool for building exploration.

**Features:**
- Filesystem-like navigation
- Object inspection
- SQL queries
- Proximity searches
- Connection tracing

## Data Flow Architecture

### 1. Contribution Flow
```
Physical Work → Mobile App → API → Database → Event → Rating → Token → Market
```

### 2. Query Flow
```
Client Request → API → Query Parser → Database → Response Formatter → Client
```

### 3. Real-time Flow
```
Database Change → Trigger → NOTIFY → Event System → SSE/Webhook → Client
```

## Database Architecture

### Schema Design

**Core Tables:**
- `building_objects` - Hierarchical object storage
- `object_properties` - JSON property storage
- `bilt_ratings` - Current ratings and components
- `rating_history` - Historical rating changes
- `contributions` - Worker data contributions
- `contributor_profiles` - Reputation and badges
- `token_transactions` - Token flows
- `webhooks` - External integrations

**Key Indexes:**
```sql
-- Path-based navigation
CREATE INDEX idx_objects_path ON building_objects(path);
CREATE INDEX idx_objects_path_pattern ON building_objects(path text_pattern_ops);

-- Spatial queries
CREATE INDEX idx_objects_location ON building_objects USING GIST(location);

-- Rating lookups
CREATE INDEX idx_ratings_building ON bilt_ratings(building_id);
CREATE INDEX idx_ratings_grade ON bilt_ratings(current_grade);
```

### Trigger System

PostgreSQL triggers for automatic event propagation:
```sql
CREATE TRIGGER notify_object_change
AFTER INSERT OR UPDATE OR DELETE ON building_objects
FOR EACH ROW EXECUTE FUNCTION emit_object_event();
```

## Scalability Patterns

### Horizontal Scaling

**API Servers:**
- Stateless design allows N instances
- Load balancer distribution
- Shared PostgreSQL backend
- Redis for session/cache (optional)

**Database:**
- Read replicas for queries
- Connection pooling (25 default)
- Partitioning for large tables
- Archive old data

### Performance Optimization

**Caching Strategy:**
- BILT ratings: 5-minute cache
- Market data: 1-minute cache
- Static queries: CDN
- Connection pool: reuse

**Query Optimization:**
- Prepared statements
- Index usage monitoring
- EXPLAIN ANALYZE reviews
- Materialized views for aggregates

## Security Architecture

### Defense in Depth

1. **Network Layer:**
   - TLS/HTTPS only
   - Firewall rules
   - DDoS protection

2. **Application Layer:**
   - API key authentication
   - Rate limiting
   - Input validation
   - SQL parameterization

3. **Database Layer:**
   - Least privilege access
   - Encrypted connections
   - Audit logging
   - Regular backups

### Data Privacy

- PII isolation
- GDPR compliance ready
- Audit trail for changes
- Right to deletion support

## Integration Patterns

### Webhook System

Reliable webhook delivery with retry logic:
```rust
pub struct WebhookConfig {
    pub url: String,
    pub secret: String,
    pub retry_count: u32,
    pub timeout_seconds: u32,
    pub event_types: Vec<EventType>,
}
```

### Event Streaming

Server-Sent Events for real-time updates:
```javascript
const eventSource = new EventSource('/api/events');
eventSource.addEventListener('bilt.rating.changed', (e) => {
    const rating = JSON.parse(e.data);
    updateDashboard(rating);
});
```

### Trading Integration

Fast market data propagation:
```
Rating Change → Event → Market Feed → Trading Platform
    <100ms        <10ms      <50ms         <200ms
                Total latency: <400ms
```

## Deployment Architecture

### Container Strategy

**Docker Composition:**
```yaml
services:
  arxos-api:
    image: arxos:latest
    replicas: 3
    
  postgres:
    image: postgres:14
    volumes: persistent
    
  redis:
    image: redis:7
    purpose: cache/sessions
```

### Kubernetes Deployment

**Resource Allocation:**
- API Pods: 3-5 replicas
- CPU: 250m request, 500m limit
- Memory: 256Mi request, 512Mi limit
- HPA: Scale on CPU >70%

## Monitoring & Observability

### Metrics Collection

**Prometheus Metrics:**
- Request rate and latency
- Database connection pool
- Rating calculations/minute
- Token distributions
- Error rates by endpoint

### Logging Strategy

**Structured Logging:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "component": "rating_engine",
  "event": "rating_calculated",
  "building_id": "123",
  "old_grade": "0m",
  "new_grade": "0n",
  "duration_ms": 45
}
```

### Distributed Tracing

OpenTelemetry integration for request flow visibility:
```
Client → API → Database → Event → Response
  └─ trace_id: abc123 ─────────────────┘
```

## Development Workflow

### Code Organization

```
arxos/
├── src/
│   ├── api/          # REST API handlers
│   ├── core/         # Building objects
│   ├── database/     # Data access layer
│   ├── events/       # Event system
│   ├── market/       # Token economics
│   ├── rating/       # BILT rating engine
│   ├── terminal.rs   # CLI interface
│   └── main.rs       # Application entry
├── migrations/       # Database schemas
├── tests/           # Integration tests
└── docs/            # Documentation
```

### Testing Strategy

**Test Pyramid:**
- Unit tests: Business logic
- Integration tests: Database operations
- E2E tests: API workflows
- Load tests: Performance validation

## Future Architecture Considerations

### Planned Enhancements

1. **GraphQL API** - Flexible query interface
2. **WebSocket Support** - Bidirectional real-time
3. **Multi-tenancy** - Building isolation
4. **Blockchain Integration** - Token ledger
5. **ML Pipeline** - Predictive maintenance
6. **3D Visualization** - Spatial navigation

### Scaling Roadmap

**Phase 1 (Current):**
- Single building support
- Thousands of objects
- Hundreds of contributors

**Phase 2:**
- Multi-building support
- Millions of objects
- Thousands of contributors

**Phase 3:**
- Global deployment
- Billions of objects
- Market integration

## Conclusion

ArxOS architecture is designed for scalability, reliability, and real-time performance. The event-driven design ensures immediate value reflection from contributions, while the modular structure allows for independent scaling of components. The system maintains data integrity through PostgreSQL's ACID guarantees while providing the flexibility needed for rapid market integration.