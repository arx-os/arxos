# ARXOS System Architecture

## Overview
ARXOS is a building information and validation system with AR capabilities, designed for simplicity and direct deployment.

## System Components

### 1. Core Backend Service (Go)
**Single Binary Application**
- REST API endpoints via Chi router
- WebSocket server for real-time features
- Direct database connections
- JWT-based authentication
- Redis session management

**Key Responsibilities:**
- Building data management
- User authentication (dual accounts)
- BILT wallet operations
- PDF processing and extraction
- Export services
- Real-time collaboration

### 2. Web Frontend
**Pure Web Technologies**
- Static HTML pages
- Vanilla JavaScript for interactivity
- HTMX for dynamic content updates
- CSS for styling
- Canvas API for 2D drawings
- SVG for vector graphics

**AR/3D Components:**
- Three.js for 3D rendering
- 8th Wall for web-based AR
- Camera access for AR features
- Spatial mapping capabilities

### 3. AI Service (Python)
**Separate Microservice**
- OpenAI API integration
- Floor plan analysis
- Image processing
- OCR text extraction
- Pattern recognition

**Communication:**
- REST API interface
- JSON data exchange
- Async processing queue

### 4. Mobile AR Application
**Native Mobile App**
- AR validation features
- Camera-based measurements
- Real-time sync with backend
- Offline capability

### 5. Data Layer

**PostgreSQL + PostGIS**
- Primary data store
- Spatial data queries
- Building geometries
- User accounts
- Transaction history

**SQLite**
- Local data caching
- Offline storage
- Configuration data
- Temporary workspaces

**Redis**
- Session storage
- Authentication tokens
- Temporary cache
- Real-time state
- Rate limiting

## Data Models

### Core Entities
```
User
├── Professional Account
├── Personal Account
└── BILT Wallet

Building
├── Geometry (PostGIS)
├── Metadata
├── Floor Plans
└── Export History

ValidationData
├── AR Captures
├── Measurements
├── Timestamps
└── User Annotations

ExportActivity
├── Format Type
├── Download Count
├── Processing Time
└── Access Logs
```

## API Architecture

### RESTful Endpoints
```
/api/v1/
├── auth/
│   ├── login
│   ├── logout
│   └── refresh
├── buildings/
│   ├── list
│   ├── create
│   ├── update
│   └── delete
├── export/
│   ├── pdf
│   ├── dwg
│   └── ifc
├── ai/
│   ├── ingest
│   └── process
└── ar/
    ├── validate
    └── measure
```

### WebSocket Events
```
ws://[host]/ws
├── wallet.update
├── collaboration.sync
├── building.change
└── notification.push
```

## Security Architecture

### Authentication Flow
1. User provides credentials
2. Backend validates against PostgreSQL
3. JWT token generated with claims
4. Token stored in Redis with session
5. Client stores token (httpOnly cookie)
6. Token validated on each request

### Authorization Levels
- **Anonymous**: Public building data
- **Personal Account**: Individual features
- **Professional Account**: Business features
- **Admin**: System management

## Deployment Architecture

### Production Setup
```
┌─────────────────┐
│   Web Client    │
│  (Browser/AR)   │
└────────┬────────┘
         │ HTTPS
┌────────▼────────┐
│   Go Backend    │
│ (Single Binary) │
└────┬──────┬─────┘
     │      │
┌────▼──┐ ┌▼──────┐
│ Redis │ │ PostgreSQL │
└───────┘ └────────┘
```

### Development Setup
- Local Go binary
- Local PostgreSQL + PostGIS
- Local Redis instance
- Python AI service
- Hot reload for frontend

## Performance Considerations

### Caching Strategy
- Redis for hot data
- PostgreSQL for persistent data
- SQLite for offline/local cache
- Browser cache for static assets

### Optimization Points
- Database connection pooling
- Prepared SQL statements
- Gzip compression
- WebSocket connection reuse
- Lazy loading for 3D assets

## Scalability Plan

### Horizontal Scaling
- Multiple Go binary instances
- Load balancer for distribution
- Shared Redis for sessions
- Read replicas for PostgreSQL

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Enhance caching layers
- CDN for static assets

## Monitoring & Logging

### Application Logs
- Standard Go log package
- Structured logging format
- Error tracking
- Performance metrics

### System Monitoring
- Health check endpoints
- Database connection pools
- Redis memory usage
- API response times

## Backup & Recovery

### Data Backup
- PostgreSQL daily backups
- Point-in-time recovery
- Redis persistence (RDB/AOF)
- Code repository backups

### Disaster Recovery
- Database replication
- Backup restoration procedures
- Session recovery from Redis
- Configuration management

## Integration Points

### CMMS Systems
- REST API integration
- Data synchronization
- Webhook notifications
- Batch processing

### External Services
- OpenAI API (AI processing)
- 8th Wall (AR services)
- Email service (notifications)
- Storage service (file uploads)

## Development Workflow

### Code Organization
```
Feature Development
├── Backend Handler (Go)
├── Frontend UI (HTML/JS)
├── Database Migration
├── API Documentation
└── Tests
```

### Testing Strategy
- Unit tests for handlers
- Integration tests for API
- Frontend functionality tests
- AR feature validation
- Load testing

## Future Considerations
(Requires explicit permission to implement)
- API rate limiting expansion
- Enhanced caching strategies
- Additional export formats
- Extended AR features
- Performance optimizations

---
**Note**: This architecture is designed for simplicity and maintainability. Any modifications require explicit approval as per TECH_STACK.md guidelines.