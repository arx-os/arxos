# Arxos Project Structure

## Overview
Arxos is organized as a Rust workspace with clean separation between core functionality, platform-specific implementations, and supporting infrastructure. The codebase is 100% air-gapped RF-only, with no internet dependencies.

## Directory Structure

```
arxos/
├── src/                      # Source code
│   ├── core/                 # Core library (platform-agnostic)
│   │   ├── arxobject.rs      # 13-byte object protocol
│   │   ├── mesh_network.rs   # RF mesh networking (LoRa)
│   │   ├── ssh_server.rs     # SSH terminal server
│   │   ├── database.rs       # SQLite integration
│   │   ├── semantic_compression.rs  # 10,000:1 compression
│   │   ├── data_consumer_api.rs    # Data access API
│   │   ├── packet.rs         # Mesh packet protocol
│   │   ├── detail_store.rs   # Progressive detail storage
│   │   ├── broadcast_scheduler.rs  # RF broadcast scheduling
│   │   ├── progressive_renderer.rs # ASCII rendering
│   │   ├── slow_bleed_node.rs     # Slow-bleed architecture
│   │   └── lib.rs            # Module exports
│   │
│   ├── terminal/             # Terminal client
│   │   ├── main.rs           # CLI entry point
│   │   └── Cargo.toml        # Terminal dependencies
│   │
│   ├── embedded/             # ESP32 firmware
│   │   ├── lib.rs            # no_std embedded code
│   │   └── Cargo.toml        # Embedded dependencies
│   │
│   └── cad/                  # CAD-like visualization
│       ├── mod.rs            # CAD module root
│       ├── data_model.rs     # 3D data structures
│       ├── viewport.rs       # ASCII viewport
│       ├── renderer.rs       # 3D to ASCII rendering
│       ├── algorithms.rs     # Spatial algorithms
│       └── commands.rs       # CAD commands
│
├── firmware/                 # Hardware firmware
│   └── esp32/               # ESP32 LoRa nodes
│       └── README.md        # Firmware docs
│
├── hardware/                 # Open hardware designs
│   ├── pcb/                 # PCB designs
│   └── enclosures/          # 3D printable cases
│
├── migrations/              # Database schema
│   ├── 001_initial_schema.sql
│   └── 002_spatial_functions.sql
│
├── docs/                    # Documentation
│   ├── 00-overview/         # Project overview
│   ├── 01-vision/           # Vision & philosophy
│   ├── 02-arxobject/        # Object protocol spec
│   ├── 03-architecture/     # Technical architecture
│   ├── 04-sql-database/     # Database design
│   ├── 05-rf-mesh/          # RF networking
│   ├── 06-implementation/   # Development guide
│   ├── 07-ios-integration/  # iOS app docs
│   ├── 10-roadmap/          # Project roadmap
│   ├── 11-data-consumers/   # Data access guide
│   └── 15-rf-updates/       # RF update system
│
├── examples/                # Example code
│   └── slow_bleed_demo.rs  # Progressive rendering demo
│
├── .github/                 # GitHub configuration
│   └── workflows/
│       └── ci.yml          # RF-only CI/CD pipeline
│
├── Cargo.toml              # Workspace configuration
├── README.md               # Project introduction
├── DEVELOPMENT.md          # Developer guide
├── PROJECT_STRUCTURE.md    # This file
├── build.sh                # Build script
└── .gitignore             # Git ignore rules
```

## Module Organization

### Core Library (`src/core/`)
The heart of Arxos - all core functionality that's platform-agnostic:

- **arxobject.rs**: 13-byte object format, the foundation of semantic compression
- **mesh_network.rs**: LoRa-based RF mesh networking, no internet required
- **ssh_server.rs**: Terminal access server for remote control
- **database.rs**: SQLite with spatial indexing
- **semantic_compression.rs**: 10,000:1 compression algorithms
- **data_consumer_api.rs**: API for data consumers (insurance, real estate, etc.)

### Terminal Client (`src/terminal/`)
SSH terminal client for connecting to mesh nodes:
- Simple CLI interface
- ASCII visualization
- Remote command execution

### Embedded Firmware (`src/embedded/`)
no_std code for ESP32 and other embedded platforms:
- Minimal memory footprint
- Real-time RF communication
- Power-efficient operation

### CAD Visualization (`src/cad/`)
ASCII-based 3D visualization system:
- Building floor plans
- Object placement visualization
- Spatial queries

## Key Design Principles

### 1. No Internet Dependencies
- ✅ No HTTP/HTTPS libraries
- ✅ No cloud service SDKs
- ✅ No web frameworks
- ✅ No REST APIs
- ✅ Updates via RF only

### 2. Modular Architecture
- Core library is platform-agnostic
- Clear separation of concerns
- Each module has single responsibility
- Easy to test in isolation

### 3. Performance First
- 13-byte objects for minimal RF bandwidth
- Efficient spatial indexing
- Progressive detail loading
- Memory-safe Rust throughout

### 4. Security by Design
- Air-gapped by default
- SSH for secure access
- No attack surface from internet
- Cryptographic signatures for updates

## Development Workflow

### Building the Project
```bash
# Build everything
cargo build --all

# Build release version
cargo build --release

# Build for embedded (ESP32)
cargo build --package arxos-embedded --target riscv32imc-unknown-none-elf --no-default-features

# Run tests
cargo test --all
```

### Code Organization Rules

1. **Import Order**: 
   - Standard library
   - External crates
   - Internal modules
   - Tests at bottom

2. **Module Structure**:
   - Public API at top
   - Private implementation below
   - Tests in #[cfg(test)] block

3. **Documentation**:
   - Module-level doc comments
   - Public API documentation
   - Examples in doc comments

4. **Error Handling**:
   - Use Result<T, E> for fallible operations
   - Custom error types per module
   - No unwrap() in production code

## Testing Strategy

### Unit Tests
- Located in same file as code
- Test individual functions
- Mock external dependencies

### Integration Tests
- Located in tests/ directory
- Test module interactions
- Use real database/network

### Performance Tests
- Compression benchmarks
- RF transmission tests
- Database query performance

## CI/CD Pipeline

The `.github/workflows/ci.yml` enforces:
- No internet dependencies
- Code formatting (cargo fmt)
- Linting (cargo clippy)
- All tests pass
- Embedded targets compile
- Database migrations work

## Contributing Guidelines

1. **RF-Only**: Never add internet dependencies
2. **Test Coverage**: Add tests for new features
3. **Documentation**: Update docs with changes
4. **Performance**: Benchmark critical paths
5. **Security**: No credentials in code

## Module Dependencies

```
arxos-core (no dependencies on other modules)
    ↑
arxos-terminal (depends on core)
    ↑
arxos-embedded (depends on core, no_std)
```

## Database Schema

Located in `migrations/`:
- 001: Core tables (arxobjects, buildings, users)
- 002: Spatial functions and indexes

## Hardware Integration

- `firmware/`: ESP32 firmware for mesh nodes
- `hardware/`: Open-source PCB designs
- RF frequencies: 915MHz (US), 868MHz (EU)

## Documentation

Comprehensive docs in `docs/`:
- User guides
- API references
- Architecture decisions
- Development tutorials

---

*Clean, organized, and ready for development - 100% air-gapped*