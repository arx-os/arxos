# ArxOS Architecture

## Design Philosophy

ArxOS follows a single-binary architecture where one executable (`arx`) provides all functionality through different runtime modes. This design prioritizes simplicity, user experience, and operational transparency.

### Core Principles

1. **One Tool, Complete System**: Single binary handles everything
2. **Transparent Infrastructure**: Background services managed automatically
3. **Text as Truth**: `.bim.txt` files are the source of truth
4. **Git-like Workflow**: Familiar version control patterns
5. **Progressive Enhancement**: Complexity only when needed

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│  ┌──────────┬──────────┬──────────┬────────────────────┐  │
│  │ Terminal │  Web 3D  │Mobile AR │   Packet Radio    │  │
│  │  (CLI)   │ (Svelte) │ (React  │  (LoRaWAN/APRS)   │  │
│  │          │          │  Native) │                   │  │
│  └──────────┴──────────┴──────────┴────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                         arx binary                          │
├─────────────────────────────────────────────────────────────┤
│                    Command Layer (Cobra)                     │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │ install  │   repo   │  import  │  query   │  serve   │ │
│  │          │          │  export  │  search  │  watch   │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Core Services                          │
│  ┌────────────────┬────────────────┬────────────────────┐ │
│  │   Repository   │    Database    │   File Watcher    │ │
│  │    Manager     │    Manager     │     Service       │ │
│  └────────────────┴────────────────┴────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Transport Layers                         │
│  ┌────────────────┬────────────────┬────────────────────┐ │
│  │   HTTP/REST    │   WebSocket    │   Packet Radio    │ │
│  │               │  (Real-time)    │  (Low-bandwidth)  │ │
│  └────────────────┴────────────────┴────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Runtime Modes                          │
│  ┌────────────────┬────────────────┬────────────────────┐ │
│  │   CLI Mode     │  Daemon Mode   │   Server Mode     │ │
│  │ (interactive) │ (background)    │    (HTTP API)     │ │
│  └────────────────┴────────────────┴────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Storage Layer                           │
│  ┌────────────────────────┬────────────────────────────┐  │
│  │   Filesystem (.bim.txt) │      SQLite Database      │  │
│  │    (source of truth)    │    (query cache)          │  │
│  └────────────────────────┴────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Runtime Modes

### 1. CLI Mode (Default)
- **Lifecycle**: Start → Execute → Exit
- **Use Case**: User commands, queries, updates
- **Example**: `arx query --status failed`

### 2. Daemon Mode
- **Lifecycle**: System service, long-running
- **Use Case**: File monitoring, auto-import
- **Management**: Handled by systemd/launchd
- **Example**: Started automatically by `arx install`

### 3. Server Mode
- **Lifecycle**: Long-running HTTP server
- **Use Case**: REST API for web/mobile clients
- **Example**: `arx serve --daemon`

## Command Structure

```
arx
├── install                    # System setup and initialization
│   ├── --with-server         # Include API server setup
│   ├── --watch <dir>         # Initial watch directories
│   └── --config <file>       # Custom configuration
│
├── repo                      # Repository management (Git-like)
│   ├── init <building>       # Initialize building repository
│   ├── status                # Show changes
│   ├── diff                  # Show detailed differences
│   ├── commit                # Commit changes
│   ├── log                   # View history
│   ├── branch                # Branch operations
│   └── merge                 # Merge branches
│
├── import <file>             # Import from various formats
│   ├── --format              # Specify format (pdf/ifc/dwg)
│   ├── --building            # Target building ID
│   └── --auto-commit         # Auto-commit after import
│
├── export <building>         # Export building data
│   ├── --format              # Output format
│   ├── --template            # Report template
│   └── --output              # Output file
│
├── query                     # Database queries
│   ├── --building            # Filter by building
│   ├── --floor               # Filter by floor
│   ├── --type                # Filter by equipment type
│   ├── --status              # Filter by status
│   └── --sql                 # Raw SQL query
│
├── watch                     # File monitoring control
│   ├── add <dir>            # Add watch directory
│   ├── remove <dir>         # Remove watch directory
│   ├── list                 # List watched directories
│   ├── pause                # Pause monitoring
│   └── resume               # Resume monitoring
│
├── serve                     # API server
│   ├── --port               # Server port (default: 8080)
│   ├── --daemon             # Run as background service
│   ├── --stop               # Stop background server
│   └── --status             # Check server status
│
└── [CRUD operations]
    ├── add <path>           # Add component
    ├── get <path>           # Get component details
    ├── update <path>        # Update component
    ├── remove <path>        # Remove component
    └── list                 # List components
```

## Data Flow

### Import Flow
```
PDF/IFC/DWG File
       ↓
   [Parser]
       ↓
   .bim.txt
       ↓
   [Validator]
       ↓
   Git Repository
       ↓
   [Sync Service]
       ↓
   SQLite DB
```

### Query Flow
```
User Query → SQLite (fast) → Results
                ↑
                │
           .bim.txt files
         (source of truth)
```

### Update Flow
```
User Update → .bim.txt → Git Commit → Database Sync
                            ↓
                     File Watcher → Auto-sync
```

## Installation Process

When user runs `arx install`:

1. **Create Directory Structure**
   ```
   ~/.arxos/
   ├── config.yaml           # Configuration
   ├── arxos.db             # SQLite database
   ├── logs/                # Log files
   └── run/                 # PID files, sockets
   ```

2. **Initialize Database**
   - Create schema
   - Set up indexes
   - Initialize system tables

3. **Install File Watcher**
   - Create systemd/launchd service
   - Configure watch directories
   - Start service

4. **Optional: Install API Server**
   - Create server service
   - Configure ports/authentication
   - Start if requested

## Interface Layers

### 1. Terminal Interface (Current)
- **Technology**: Native Go with ASCII art rendering
- **Features**: Command-line operations, ASCII floor plans, live monitoring
- **Status**: Fully implemented

### 2. Web 3D Interface (Future)
- **Technology**: Svelte + Three.js + D3.js
- **Architecture**: SPA communicating via WebSocket/REST API
- **Features**:
  - Interactive 3D building models
  - Real-time equipment status updates
  - Energy flow visualization
  - Historical data timeline
- **Status**: Foundation established in `/web`

### 3. Mobile AR Interface (Future)
- **Technology**: React Native + ARKit/ARCore
- **Architecture**: Mobile app with offline-first design
- **Features**:
  - AR equipment identification
  - QR code scanning
  - Spatial anchoring
  - Work order management
  - Voice notes and photo documentation
- **Status**: Foundation established in `/mobile`

### 4. Packet Radio Transport (Experimental)
- **Technology**: LoRaWAN, APRS, custom protocols
- **Architecture**: Compressed binary protocol over radio
- **Features**:
  - 92% message compression
  - Automatic retransmission
  - Context-based optimization
  - Battery-efficient operation
- **Status**: Implementation in `/internal/transport/radio`

## Code Organization

```go
cmd/arx/
├── main.go                   # Entry point, mode detection
├── cmd_install.go            # Installation command
├── cmd_repo.go              # Repository operations
├── cmd_import.go            # Import operations
├── cmd_export.go            # Export operations
├── cmd_query.go             # Query operations
├── cmd_watch.go             # Watch control
├── cmd_serve.go             # Server mode
└── cmd_crud.go              # CRUD operations

internal/
├── core/                    # Core business logic
│   ├── building.go         # Building management
│   ├── equipment.go        # Equipment operations
│   ├── addressing.go       # Universal addressing system
│   └── validation.go       # Data validation
│
├── runtime/                # Runtime modes
│   ├── cli.go             # CLI mode execution
│   ├── daemon.go          # Daemon mode (file watcher)
│   └── server.go          # HTTP server mode
│
├── storage/               # Storage implementations
│   ├── filesystem.go      # .bim.txt file operations
│   ├── database.go        # SQLite operations
│   ├── repository.go      # Git operations
│   ├── git_integration.go # Git operations for buildings
│   └── sync.go           # Sync between storage types
│
├── transport/            # Transport layers
│   ├── http.go          # HTTP/REST transport
│   ├── websocket.go     # WebSocket for real-time
│   └── radio/           # Packet radio transport
│       ├── transport.go # Core radio protocol
│       ├── lorawan.go   # LoRaWAN implementation
│       └── compression.go # Message compression
│
├── rendering/           # Visualization engines
│   ├── ascii.go        # Terminal ASCII art
│   ├── layered_renderer.go # Layered rendering
│   └── svg_renderer.go # SVG output
│
├── services/             # Shared services
│   ├── watcher.go        # File system monitoring
│   ├── importer/         # Import from various formats
│   │   ├── pdf.go
│   │   ├── ifc.go
│   │   └── dwg.go
│   ├── exporter/         # Export to various formats
│   └── validator.go      # BIM validation
│
├── api/                  # REST API (server mode)
│   ├── server.go        # HTTP server setup
│   ├── routes.go        # Route definitions
│   ├── handlers/        # Request handlers
│   └── middleware/      # Auth, logging, etc.
│
└── common/              # Shared utilities
    ├── config.go        # Configuration management
    ├── logger.go        # Logging
    └── errors.go        # Error handling

web/                     # Web 3D interface (Svelte)
├── src/
│   ├── components/     # Svelte components
│   ├── lib/           # Client libraries
│   └── stores/        # State management
└── package.json

mobile/                  # Mobile AR app (React Native)
├── src/
│   ├── screens/       # App screens
│   ├── components/    # React components
│   └── services/      # API and AR services
├── ios/               # iOS-specific code
└── android/           # Android-specific code
```

## Process Management

### Background Services

ArxOS manages background processes through OS service managers:

**Linux (systemd)**:
```ini
[Unit]
Description=ArxOS File Watcher
After=network.target

[Service]
Type=simple
User=%USER%
ExecStart=/usr/local/bin/arx watch --daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**macOS (launchd)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.arxos.watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/arx</string>
        <string>watch</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

### Inter-Process Communication

Services communicate via:
- **Unix sockets**: For local IPC (`~/.arxos/run/arxos.sock`)
- **PID files**: For process management (`~/.arxos/run/watcher.pid`)
- **SQLite**: Shared state with proper locking
- **Filesystem events**: inotify/fsevents for file changes

## Configuration

System configuration in `~/.arxos/config.yaml`:

```yaml
# System paths
paths:
  database: ~/.arxos/arxos.db
  buildings: ./buildings
  logs: ~/.arxos/logs

# File watcher
watcher:
  enabled: true
  directories:
    - ./buildings
    - /shared/bim-files
  patterns:
    - "*.bim.txt"
    - "*.pdf"
  auto_import: true
  scan_interval: 5s

# Database
database:
  type: sqlite
  backup:
    enabled: true
    interval: 24h
    keep: 7

# API Server
server:
  enabled: false
  port: 8080
  host: localhost
  auth:
    enabled: false
    jwt_secret: ${JWT_SECRET}

# Logging
logging:
  level: info
  file: ~/.arxos/logs/arxos.log
  max_size: 100M
  max_age: 30d

# Import/Export
import:
  pdf:
    ocr: true
    dpi: 300
  validation:
    strict: true
```

## Security Considerations

### File System Security
- Config files: 600 permissions
- Database: 644 permissions
- Sockets: 600 permissions
- Logs: 644 permissions

### API Security (when enabled)
- JWT authentication
- Rate limiting
- CORS configuration
- TLS support

### Data Security
- No credentials in .bim.txt files
- Sensitive data in config only
- Audit logging for changes

## Performance Targets

- **Installation**: < 5 seconds
- **Import PDF**: < 10 seconds for 50-page document
- **Query response**: < 100ms for 10,000 equipment items
- **File watch latency**: < 1 second detection
- **API response**: < 50ms for standard queries
- **Database size**: ~1MB per 1,000 equipment items

## Future Enhancements

### Phase 1 (Current - Complete)
- ✅ Single binary architecture
- ✅ File watching and auto-sync
- ✅ Import/export (PDF, BIM formats)
- ✅ SQLite storage with Git versioning
- ✅ ASCII art rendering
- ✅ Repository management (Git-like workflow)

### Phase 2 (In Progress)
- 🚧 Web 3D visualization (Svelte + Three.js)
- 🚧 Mobile AR application (React Native)
- 🚧 Packet radio transport (LoRaWAN/APRS)
- ⬜ Plugin system for custom importers
- ⬜ GraphQL API option
- ⬜ Distributed synchronization

### Phase 3 (Future Vision)
- ⬜ Machine learning for predictive maintenance
- ⬜ Advanced AR/VR with spatial computing
- ⬜ Blockchain audit trail for compliance
- ⬜ IoT device direct integration
- ⬜ Voice control and AI assistant
- ⬜ Digital twin simulation engine

## Troubleshooting

### Common Issues

**Watcher not starting**:
```bash
arx watch list              # Check configuration
arx status                  # Check system status
systemctl status arxos      # Check service status
```

**Database locked**:
```bash
arx status --check-locks    # Check for locks
arx repair                  # Repair database
```

**Import failures**:
```bash
arx validate <file>         # Check file format
arx import --verbose <file> # Detailed error output
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

Key points for contributors:
- All functionality in single binary
- Commands use Cobra framework
- Services must support all three runtime modes
- Tests required for new commands
- Documentation updates required