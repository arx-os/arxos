# Arxos - Building Infrastructure-as-Code Platform

[![Go Version](https://img.shields.io/badge/Go-1.21+-blue.svg)](https://golang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

Arxos transforms buildings into programmable infrastructure through revolutionary ASCII-BIM visualization, ArxObject behavioral components, and infrastructure-as-code workflows. Buildings become navigable filesystems with infinite zoom capability, from campus level down to microcontroller internals.

## 🚀 Key Features

- **ASCII-BIM Engine**: Buildings rendered as navigable ASCII art with <10ms performance
- **Filesystem Navigation**: Navigate buildings like Unix directories (`/electrical/panel-a/circuit-7`)
- **Nanometer Precision**: Submicron accuracy with adaptive Level of Detail (LOD)
- **Progressive Construction**: PDF → LiDAR → 3D with confidence tracking
- **Infrastructure-as-Code**: Git-like version control for physical buildings
- **Multi-Modal Interfaces**: 6 layers from 3D rendering to pure CLI
- **Field Validation**: AR-based progressive validation with BILT token rewards (planned)

## 📊 Performance

| Operation | Performance | vs Target |
|-----------|------------|-----------|
| ArxObject Creation | 83ns | 12,048x faster |
| Property Operations | 167ns | 598x faster |
| ASCII Rendering | 2.75μs | 3,636x faster |
| Spatial Query | 2.25μs | 2,222x faster |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│         Interface Layer (6 Modes)               │
├─────────────────────────────────────────────────┤
│         Go Services (API, WebSocket)            │
├─────────────────────────────────────────────────┤
│         CGO Bridge (Go ↔ C)                    │
├─────────────────────────────────────────────────┤
│         C Core Engine (High Performance)        │
├─────────────────────────────────────────────────┤
│         PostgreSQL + PostGIS (Spatial Data)     │
└─────────────────────────────────────────────────┘
```

## 🚦 Quick Start

### Prerequisites

- Go 1.21 or higher
- PostgreSQL 14+ with PostGIS extension
- Python 3.9+ (for AI services)
- GCC/Clang (for C core compilation)

### Installation

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Setup database
./scripts/database/setup-postgres.sh

# Build the project
make build

# Run migrations
make migrate

# Start the server
make run
```

### CLI Usage

```bash
# Initialize a building
./arxos init building_demo --type office --floors 3

# Navigate the building
./arxos ls /electrical
./arxos cd /electrical/main-panel
./arxos inspect circuit-1

# Query with AQL
./arxos query "SELECT * FROM /electrical WHERE type='outlet' AND load > 15A"

# Version control
./arxos commit -m "Added emergency lighting"
./arxos diff HEAD~1
./arxos rollback HEAD~2
```

## 📁 Project Structure

```
arxos/
├── cmd/           # CLI application
├── core/          # Core backend (Go + C)
│   ├── c/        # High-performance C engine
│   ├── cgo/      # Go-C bridge
│   └── internal/ # Go services
├── ai_service/    # Python AI processing
├── frontend/      # Web interface
└── scripts/       # Utility scripts
```

## 🔧 Development

### Building from Source

```bash
# Build everything
make all

# Build specific components
make cli        # CLI tool only
make server     # Backend server
make c-engine   # C core library

# Development mode (hot reload)
make dev
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run benchmarks
make benchmark

# Run specific test suite
go test ./core/internal/arxobject/...
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📚 Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Vision Document](vision.md)
- [API Documentation](docs/api/README.md)
- [CLI Commands](docs/cli/commands.md)
- [Development Guide](docs/development/guide.md)

## 🎯 Roadmap

### ✅ Completed
- Core C engine with exceptional performance
- ArxObject system with nanometer precision
- CGO bridge for Go-C integration
- PostgreSQL with spatial indexing
- Basic CLI navigation

### 🚧 In Progress
- BILT token implementation
- 6-layer interface system
- Enhanced AQL functionality
- AI service integration

### 📅 Planned
- AR field validation app
- PDF+LiDAR fusion pipeline
- ArxOS hardware platform
- Enterprise features

## 🤝 Community

- **Discord**: [Join our server](https://discord.gg/arxos)
- **Forum**: [community.arxos.io](https://community.arxos.io)
- **Twitter**: [@arxos_io](https://twitter.com/arxos_io)

## 📄 License

This project is proprietary software. See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Documentation**: [docs.arxos.io](https://docs.arxos.io)
- **Issues**: [GitHub Issues](https://github.com/arx-os/arxos/issues)
- **Email**: support@arxos.io

## 🙏 Acknowledgments

- Pixatool for ASCII rendering inspiration
- The open-source BIM community
- All contributors and early adopters

---

**Built with ❤️ by the Arxos Team**