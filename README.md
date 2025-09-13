# ArxOS - Building Intelligence Platform

ArxOS is a comprehensive platform that treats buildings as living, queryable, version-controlled systems. Built with Go and HTMX, it provides both a powerful CLI and a clean web interface for managing building intelligence.

## 🚀 Current Status

**Platform Evolution Complete** ✅
- **API Server** - RESTful API with authentication
- **Web UI** - Clean HTMX-based interface (no JavaScript build complexity)
- **Cloud Sync** - Push/pull synchronization with conflict resolution
- **CLI Tools** - Powerful command-line interface for all operations
- **Database Layer** - SQLite with spatial indexing and full-text search
- **Mobile AR** 🆕 - Augmented Reality app for field workers (in development)

## 🎯 Key Features

### Web Interface (HTMX)
- **No Build Step** - Just Go templates + HTMX
- **Server-Side Rendering** - Fast, SEO-friendly, works without JS
- **Real-time Updates** - Server-sent events for live data
- **Progressive Enhancement** - Forms work with or without JavaScript
- **Minimal Dependencies** - 14kb HTMX vs 45kb+ for React

### API Server
- **RESTful Design** - Standard HTTP/JSON API
- **JWT-like Auth** - Token-based authentication
- **Rate Limiting** - Built-in protection
- **CORS Support** - Ready for external integrations
- **Middleware Stack** - Logging, recovery, auth, rate limiting

### Cloud Capabilities
- **Sync Engine** - Push/pull/full synchronization
- **Conflict Resolution** - Multiple resolution strategies
- **Storage Abstraction** - Local, S3, Azure backends
- **Offline First** - Works without connection

### Mobile AR Application (Coming Soon)
- **Spatial Anchoring** - Persistent equipment placement in physical space
- **Real-time Visualization** - See equipment status and info in AR
- **Voice Input** - Hands-free equipment updates
- **Offline Support** - Work without connectivity, sync when online
- **Cross-Platform** - iOS (ARKit) and Android (ARCore) support

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/joelpate/arxos.git
cd arxos

# Build everything
make build

# Or build individually
go build -o bin/arx ./cmd/arx           # CLI tool
go build -o bin/arxos-server ./cmd/arxos-server  # API + Web server
go build -o bin/arxd ./cmd/arxd         # Daemon for auto-sync
```

## 🚀 Quick Start

### Start the Web Server

```bash
# Start API server with web UI
./bin/arxos-server -port 8080

# Access the web interface
open http://localhost:8080

# Default credentials
# Email: admin@arxos.io
# Password: admin123
```

### CLI Operations

```bash
# Configure for cloud mode
./bin/arx config set mode cloud
./bin/arx config set cloud.url http://localhost:8080

# Login to cloud
./bin/arx sync login

# Import a building
./bin/arx import building.pdf

# Sync with cloud
./bin/arx sync

# Query the database
./bin/arx query "SELECT * FROM equipment WHERE status = 'failed'"
```

## 🏗️ Architecture

### Technology Stack
```
Backend:
├── Go 1.21+              # Core language
├── SQLite               # Embedded database
├── HTMX                 # Dynamic UI without complexity
├── Tailwind CSS         # Utility-first CSS
└── Server-Sent Events   # Real-time updates

No Node.js, No Webpack, No npm - Just Go!
```

### Project Structure
```
arxos/
├── cmd/
│   ├── arx/             # CLI application
│   ├── arxos-server/    # API + Web server
│   └── arxd/            # Background daemon
├── internal/
│   ├── api/             # API handlers & services
│   ├── web/             # HTMX templates & handlers
│   ├── database/        # SQLite operations
│   ├── sync/            # Cloud sync engine
│   ├── storage/         # Storage abstraction
│   ├── config/          # Configuration management
│   └── auth/            # Authentication
├── pkg/models/          # Core data models
├── templates/           # HTML templates
└── static/              # Static assets
```

## 🌐 Web Interface

The HTMX-based interface provides:

- **Dashboard** - Real-time building statistics
- **Buildings** - Manage floor plans and spaces
- **Equipment** - Track and monitor all equipment
- **Search** - Fast, as-you-type search
- **Analytics** - Building performance metrics
- **Settings** - User and system configuration

### Why HTMX?

We chose HTMX over React/Vue/Angular because:
- **Simplicity** - No build step, no webpack configuration
- **Speed** - Server-rendered HTML is fast
- **Maintainability** - One language (Go) instead of Go + JS
- **Size** - 14kb vs 45kb+ for React
- **SEO** - Server-side rendering works for search engines

## 🔌 API Reference

### Authentication
```bash
# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@arxos.io","password":"admin123"}'

# Returns: { "access_token": "...", "refresh_token": "..." }
```

### Buildings
```bash
# List buildings
curl http://localhost:8080/api/v1/buildings \
  -H "Authorization: Bearer <token>"

# Create building
curl -X POST http://localhost:8080/api/v1/buildings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Main Office","building":"HQ","level":1}'
```

### Equipment
```bash
# List equipment
curl http://localhost:8080/api/v1/equipment \
  -H "Authorization: Bearer <token>"

# Update equipment status
curl -X PATCH http://localhost:8080/api/v1/equipment/SW-01 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status":"failed","notes":"No power"}'
```

## 🔄 Cloud Sync

### Configuration
```bash
# Set sync mode
./bin/arx config set mode cloud

# Configure conflict resolution
./bin/arx sync --conflict-mode remote  # remote wins
./bin/arx sync --conflict-mode local   # local wins
./bin/arx sync --conflict-mode merge   # attempt merge
```

### Sync Operations
```bash
# Full sync
./bin/arx sync

# Push only
./bin/arx sync --mode push

# Pull only
./bin/arx sync --mode pull

# Check sync status
./bin/arx sync status
```

## 📊 Database Operations

### Direct SQL Queries
```bash
# Failed equipment
./bin/arx query "SELECT * FROM equipment WHERE status = 'failed'"

# Equipment by type
./bin/arx query "SELECT type, COUNT(*) FROM equipment GROUP BY type"

# Spatial queries
./bin/arx query "SELECT * FROM equipment WHERE room_id = 'room_2b'"
```

### Connection Tracking
```bash
# Create connections
./bin/arx connect outlet_2b panel_1 --type power
./bin/arx connect switch_1 idf_100 --type data

# Trace connections
./bin/arx trace panel_1 downstream  # What does this power?
./bin/arx trace outlet_2b upstream  # What powers this?

# Impact analysis
./bin/arx analyze panel_1  # What fails if panel_1 fails?
```

## 🚢 Deployment

### Docker
```bash
# Build image
docker build -t arxos .

# Run container
docker run -p 8080:8080 -v arxos-data:/data arxos
```

### Systemd Service
```bash
# Copy service file
sudo cp arxos.service /etc/systemd/system/

# Enable and start
sudo systemctl enable arxos
sudo systemctl start arxos
```

### Environment Variables
```bash
ARXOS_PORT=8080
ARXOS_STATE_DIR=/var/lib/arxos
ARXOS_LOG_LEVEL=info
ARXOS_MODE=cloud
ARXOS_API_URL=https://api.arxos.io
```

## 📖 Documentation

- **[API Documentation](docs/API.md)** - Complete API reference
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup and contribution guide
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture
- **[Vision](docs/VISION.md)** - Platform vision and roadmap
- **[Mobile AR Guide](docs/MOBILE_AR.md)** - AR application development
- **[AR API Specification](docs/AR_API_SPEC.md)** - AR-specific API endpoints

## 🧪 Testing

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run specific package
go test ./internal/api -v

# Run integration tests
go test ./tests/integration -tags=integration
```

## 🛠️ Development

```bash
# Install dependencies
go mod download

# Run development server with hot reload
air

# Format code
go fmt ./...

# Lint code
golangci-lint run

# Generate mocks
go generate ./...
```

## 📈 Performance

- **Fast Startup** - Single binary, no runtime dependencies
- **Low Memory** - ~50MB RAM for typical usage
- **SQLite** - Handles millions of records efficiently
- **HTMX** - Minimal network traffic, only sends diffs
- **Caching** - Built-in caching for templates and queries

## 🔒 Security

- **bcrypt** - Password hashing
- **CORS** - Configurable cross-origin policies
- **Rate Limiting** - Built-in DoS protection
- **HTTPS** - TLS support built-in
- **Input Validation** - All inputs sanitized
- **SQL Injection Protection** - Parameterized queries

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- **HTMX** - For making web development simple again
- **SQLite** - The best embedded database
- **Go** - For being a joy to work with
- **The Community** - For feedback and contributions

---

**ArxOS** - Building Intelligence Made Simple

*No JavaScript frameworks were harmed in the making of this platform* 🎉