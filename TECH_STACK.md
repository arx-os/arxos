# ARXOS Technology Stack & Architecture

## STRICT TECHNOLOGY POLICY
**NO DEVIATIONS ALLOWED**: This technology stack is final and must not be modified without explicit user permission. Any proposed additions must be presented to the user with detailed justification before implementation.

## Core Technology Stack

### Backend
- **Go with Chi Router** - Single binary deployment
  - Chi (github.com/go-chi/chi/v5) - HTTP router ONLY
  - Standard library preferred over external packages
  - NO additional web frameworks (no Gin, Echo, Fiber, etc.)

### Frontend
- **Vanilla JavaScript** - No frameworks (NO React, Vue, Angular, etc.)
- **HTML** - Standard HTML5
- **CSS** - Pure CSS, no preprocessors
- **HTMX** - For dynamic HTML updates
- **SVG** - For vector graphics
- **Canvas API** - For 2D graphics

### 3D & Augmented Reality
- **Three.js** - 3D graphics library for web
- **8th Wall** - Web-based AR framework
- Mobile AR validation app (separate from web)

### Databases
- **PostgreSQL with PostGIS** - Primary database with spatial extensions
- **SQLite** - Embedded database for local/lightweight storage

### Caching & Sessions
- **Redis** - Session management and caching
  - Required for authentication system
  - Professional/personal account sessions
  - BILT wallet session data

### Authentication & Security
- **JWT (JSON Web Tokens)** - Token-based authentication
  - Dual account types: professional and personal
  - BILT wallet integration
- **golang.org/x/crypto** - Cryptographic operations

### Real-time Communication
- **WebSocket** (gorilla/websocket) - Real-time updates
  - Wallet balance updates
  - Collaboration features
  - Live notifications

### AI Services
- **Python** - Separate AI service
- **OpenAI API** - For AI-powered features

### Supporting Libraries (Approved)
- **go-redis/redis/v8** - Redis client
- **golang-jwt/jwt/v4** - JWT implementation
- **jmoiron/sqlx** - SQL extensions
- **lib/pq** - PostgreSQL driver
- **gorm** - ORM for database operations
- **joho/godotenv** - Environment variables
- **rs/cors** - CORS handling (under evaluation)
- **pdfcpu** - PDF processing
- **otiai10/gosseract** - OCR capabilities

## Architecture Principles

### Deployment
- **Single Binary** - Go backend compiles to a single executable
- **NO Containerization Complexity** - No Kubernetes, Docker Compose orchestration
- **Simple Infrastructure** - Direct deployment, minimal moving parts

### Code Philosophy
- **Pure Simplicity** - Prefer standard library over frameworks
- **No Over-Engineering** - Avoid unnecessary abstractions
- **Explicit Over Implicit** - Clear, readable code
- **Minimal Dependencies** - Only add what's absolutely necessary

### File Organization
```
/arxos
├── core/
│   ├── backend/        # Go backend services
│   │   ├── handlers/   # HTTP handlers
│   │   ├── models/     # Data models
│   │   ├── services/   # Business logic
│   │   └── db/         # Database connections
│   └── frontend/       # Vanilla JS/HTML/CSS
│       ├── js/         # JavaScript files
│       ├── css/        # Stylesheets
│       └── html/       # HTML templates
├── ai_service/         # Python AI service
└── ar_mobile/          # Mobile AR app

```

## Development Rules

### Adding New Technology
1. **STOP** - Do not add any technology not listed above
2. **ASK** - Request permission with:
   - Specific technology name
   - Detailed reasoning for necessity
   - Impact on existing architecture
   - Alternative solutions using approved stack
3. **WAIT** - Do not proceed without explicit approval

### Using Existing Technology
1. Check if functionality exists in standard library first
2. Use approved libraries from the list above
3. Implement custom solutions over adding dependencies
4. Keep code simple and maintainable

## Prohibited Technologies
The following are explicitly NOT allowed:
- ❌ Viper (configuration management)
- ❌ Prometheus (monitoring)
- ❌ Kubernetes (orchestration)
- ❌ Complex deployment tools
- ❌ Additional web frameworks
- ❌ JavaScript frameworks/libraries (except Three.js, 8th Wall, HTMX)
- ❌ CSS preprocessors (SASS, LESS, etc.)
- ❌ Additional ORMs beyond Gorm
- ❌ Message queues (RabbitMQ, Kafka, etc.)
- ❌ Additional caching layers
- ❌ Service mesh technologies

## Authentication Architecture
- Users have dual accounts:
  - Professional account (work/business)
  - Personal account (individual)
- BILT wallet connects both account types
- JWT tokens manage session state
- Redis stores active sessions

## Data Flow
1. Frontend (HTML/JS/HTMX) → Backend (Go/Chi)
2. Backend → PostgreSQL/SQLite for persistence
3. Backend → Redis for sessions/cache
4. Backend ↔ Python service for AI operations
5. WebSocket for real-time updates
6. Three.js + 8th Wall for AR visualization

## Security Considerations
- All secrets in environment variables
- JWT for stateless authentication
- CORS configured for API access
- No hardcoded credentials
- Secure WebSocket connections

---
**REMINDER**: Any deviation from this stack requires explicit user permission with detailed justification.