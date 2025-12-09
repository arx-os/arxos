# Architecture

ArxOS system design and implementation principles.

---

## Overview

ArxOS is a **single binary application** (`arx`) built in Rust with feature-gated modules. The architecture follows these principles:

1. **Single binary** – One executable handles all functionality
2. **Feature gates** – Optional functionality compiled conditionally
3. **Git-native storage** – All data stored in Git repositories
4. **Terminal-first** – CLI is the primary interface
5. **Web as PWA** – Browser interface via WASM

---

## Core Architecture

```
┌─────────────────────────────────────────┐
│          arx (single binary)            │
├─────────────────────────────────────────┤
│  CLI (clap)                             │
│  ├── Building Management                │
│  ├── Git Operations                     │
│  ├── Import/Export                      │
│  └── Visualization                      │
├─────────────────────────────────────────┤
│  Core Modules (always available)        │
│  ├── config      (configuration)        │
│  ├── core        (data structures)      │
│  ├── error       (error handling)       │
│  ├── git         (Git integration)      │
│  ├── ifc         (IFC parser)           │
│  ├── persistence (YAML storage)         │
│  ├── validation  (data validation)      │
│  ├── sensor      (sensor integration)   │
│  ├── hardware    (hardware interfaces)  │
│  ├── spatial     (spatial queries)      │
│  ├── export      (export formats)       │
│  └── utils       (utilities)            │
├─────────────────────────────────────────┤
│  Feature-Gated Modules                  │
│  ├── tui         (--features tui)       │
│  ├── render3d    (--features render3d)  │
│  ├── agent       (--features agent)     │
│  └── web         (--features web)       │
└─────────────────────────────────────────┘
```

---

## Directory Structure

```
/src
├── main.rs              # Binary entry point
├── lib.rs               # Library root
├── cli/                 # Command-line interface
│   ├── mod.rs           # CLI definitions
│   ├── args.rs          # Argument parsing
│   ├── commands/        # Command implementations
│   └── subcommands/     # Subcommand modules
├── core/                # Core data structures
│   ├── building.rs      # Building entity
│   ├── floor.rs         # Floor entity
│   ├── room.rs          # Room entity
│   ├── equipment.rs     # Equipment entity
│   └── wing.rs          # Wing entity
├── git/                 # Git integration
│   ├── manager.rs       # Git operations
│   └── config.rs        # Git configuration
├── ifc/                 # IFC file handling
│   ├── mod.rs           # IFC parser entry
│   ├── parser.rs        # IFC parsing logic
│   └── hierarchy/       # IFC hierarchy extraction
├── persistence/         # YAML storage
│   ├── mod.rs           # Persistence layer
│   └── yaml.rs          # YAML serialization
├── sensor/              # Sensor integration
│   ├── mod.rs           # Sensor types
│   ├── http.rs          # HTTP endpoint
│   └── mqtt.rs          # MQTT subscriber
├── hardware/            # Hardware interfaces
│   ├── mod.rs           # Hardware abstraction
│   └── simulated.rs     # Simulated devices
├── validation/          # Data validation
│   └── mod.rs           # Validation rules
├── export/              # Export formats
│   ├── mod.rs           # Export dispatcher
│   ├── ifc.rs           # IFC export
│   ├── gltf.rs          # glTF export
│   └── usdz.rs          # USDZ export
├── spatial.rs           # Spatial queries
├── config.rs            # Configuration management
├── error.rs             # Error types
├── utils.rs             # Utilities
├── yaml.rs              # YAML helpers
├── tui/                 # Terminal UI (feature)
│   ├── dashboard.rs     # Interactive dashboard
│   ├── spreadsheet/     # Spreadsheet editor
│   └── merge/           # Merge tool
├── render3d/            # 3D rendering (feature)
│   ├── mod.rs           # Renderer entry
│   ├── point_cloud.rs   # Point cloud renderer
│   └── interactive.rs   # Interactive viewer
├── agent/               # Remote agent (feature)
│   ├── dispatcher.rs    # Command dispatcher
│   └── auth.rs          # Authentication
├── web/                 # WASM PWA (feature)
│   ├── app.rs           # Web app entry
│   ├── pages/           # Page components
│   ├── components/      # UI components
│   └── wasm_bridge.rs   # WASM bridge
└── bin/                 # Additional binaries
    └── arx-web.rs       # Web server binary
```

---

## Feature Gates

### Core Features (Always Available)

Built into every binary:
- Building data management
- Git operations
- IFC import/export
- YAML persistence
- Validation
- Sensor integration
- Configuration

### Optional Features

Enabled at compile time:

#### `--features tui`
Terminal User Interface components:
- Interactive dashboard
- Spreadsheet editor
- Merge conflict resolver
- ASCII visualization

**Build:**
```bash
cargo build --features tui
```

#### `--features render3d`
3D rendering capabilities:
- Interactive point cloud renderer
- WebGPU-accelerated graphics
- Real-time camera controls
- Multi-floor visualization

**Build:**
```bash
cargo build --features render3d
```

**Dependencies:** `wgpu`, `winit`, `cgmath`

#### `--features agent`
Remote agent functionality:
- SSH tunnel management
- Remote command execution
- Hardware interface abstraction
- Authentication/authorization

**Build:**
```bash
cargo build --features agent
```

**Dependencies:** `tokio`, `ssh2`, `async-trait`

#### `--features web`
WASM Progressive Web App:
- Browser-based UI
- Offline capabilities
- IndexedDB storage
- Service worker

**Build:**
```bash
cd src/web
trunk serve
```

**Dependencies:** `yew`, `wasm-bindgen`, `web-sys`

---

## Data Flow

### Import Workflow

```
IFC File
  ↓
ifc::parser::IfcParser
  ↓
core::Building struct
  ↓
persistence::yaml::save()
  ↓
building.yaml + Git commit
```

### Update Workflow

```
User command (arx equipment update)
  ↓
persistence::yaml::load()
  ↓
core::Building (in-memory)
  ↓
Modify equipment
  ↓
persistence::yaml::save()
  ↓
git::manager::commit()
  ↓
Git commit with diff
```

### Sensor Integration

```
Sensor data (HTTP/MQTT)
  ↓
sensor::http/mqtt
  ↓
Parse JSON payload
  ↓
Match to equipment by address
  ↓
Update equipment status
  ↓
persistence::yaml::save()
  ↓
Optional: Git commit
```

---

## Git Integration

### Storage Model

All building data stored in Git:

```
.git/
├── objects/          # Git object database
│   └── ...           # building.yaml versions
├── refs/
│   ├── heads/        # Branches
│   └── tags/         # Version tags
└── index             # Staging area
```

### Operations

**Read:**
```rust
git::manager::load_building()
  → git show HEAD:building.yaml
  → Parse YAML
  → Return Building struct
```

**Write:**
```rust
persistence::save()
  → Write building.yaml
  → git add building.yaml
  → git commit -m "message"
```

**Diff:**
```rust
git::manager::diff()
  → git diff HEAD~1 HEAD
  → Parse unified diff
  → Display changes
```

---

## Error Handling

### Error Type Hierarchy

```rust
pub enum ArxError {
    Io(std::io::Error),
    Yaml(serde_yaml::Error),
    Git(git2::Error),
    Ifc(String),
    Validation(String),
    Config(String),
    // ... more variants
}
```

### Error Propagation

Uses `Result<T, ArxError>` throughout:

```rust
pub fn import_ifc(path: &str) -> Result<Building, ArxError> {
    let parser = IfcParser::new(path)?;  // ? operator
    let building = parser.parse()?;
    Ok(building)
}
```

### User-Facing Errors

CLI displays friendly error messages:

```bash
❌ Error: IFC file not found: building.ifc

💡 Tip: Check the file path and try again
   Use 'arx import --help' for usage information
```

---

## Configuration System

### Configuration Sources (Priority Order)

1. **Command-line arguments** (highest priority)
2. **Environment variables** (`ARX_*`)
3. **Local config** (`.arxos/config.toml`)
4. **User config** (`~/.config/arxos/config.toml`)
5. **Defaults** (lowest priority)

### Example Configuration

```toml
[user]
name = "John Doe"
email = "john@example.com"

[git]
auto_stage = true
auto_commit = false
commit_template = "Building update: {message}"

[performance]
cache_enabled = true
max_parallel_threads = 8
memory_limit_mb = 1024

[sensors]
enable_mqtt = false
enable_http = true
http_port = 3000
```

---

## Performance Considerations

### Caching

Optional caching layer for large buildings:

```rust
.arxos/cache/
├── building_hash.bin     # Cached Building struct
└── spatial_index.bin     # Spatial query index
```

### Parallel Processing

IFC import uses parallel processing:

```rust
use rayon::prelude::*;

entities.par_iter()
    .map(|entity| parse_entity(entity))
    .collect()
```

### Memory Management

- Streaming IFC parsing (no full file in memory)
- Lazy loading of equipment properties
- Optional spatial index (trade memory for speed)

---

## Security

### GPG Signing

Support for GPG-signed commits:

```bash
arx config --set git.sign_commits=true
arx commit "Verified update"
```

### User Permissions

User registry with role-based access:

```yaml
users:
  - name: "John Doe"
    email: "john@example.com"
    permissions:
      - verify_users
      - commit
      - import_ifc
```

---

## Testing Strategy

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_building_creation() {
        let building = Building::new("Test");
        assert_eq!(building.name, "Test");
    }
}
```

### Integration Tests

```bash
tests/
├── ifc_integration_test.rs
├── git_integration_test.rs
└── persistence/
    └── yaml_tests.rs
```

### Test Data

```
test_data/
├── sample_building.ifc
├── Building-Architecture.ifc
└── sensor-data/
    └── sample-sensor.json
```

---

## Build System

### Standard Build

```bash
# Debug build
cargo build

# Release build
cargo build --release

# With all features
cargo build --release --all-features
```

### WASM Build

```bash
cd src/web
trunk serve           # Development
trunk build --release # Production
```

### Cross-Compilation

```bash
# Windows
cargo build --target x86_64-pc-windows-msvc

# macOS
cargo build --target x86_64-apple-darwin

# Linux
cargo build --target x86_64-unknown-linux-gnu
```

---

## Extensibility

### Adding New Commands

1. Define command in `src/cli/mod.rs`
2. Implement in `src/cli/commands/`
3. Add subcommand variant
4. Wire up in `execute()` match

### Adding Equipment Types

1. Update `EquipmentType` enum in `src/core/equipment.rs`
2. Add validation rules in `src/validation/`
3. Update documentation

### Adding Export Formats

1. Create module in `src/export/`
2. Implement `Exporter` trait
3. Add CLI option
4. Wire up in export dispatcher

---

## Design Decisions

### Why Single Binary?

- **Simplicity:** One artifact to deploy
- **Performance:** No IPC overhead
- **Distribution:** Easy installation
- **Maintenance:** Fewer moving parts

### Why Git for Storage?

- **Version control:** Built-in history
- **Collaboration:** Git workflows
- **Diffing:** Line-based changes
- **Branching:** Multiple scenarios
- **Distribution:** Decentralized sync

### Why YAML not JSON?

- **Human-readable:** Comments and formatting
- **Git-friendly:** Better diffs
- **Less verbose:** Cleaner syntax
- **Industry standard:** Used in CAD tools

### Why Feature Gates?

- **Optional deps:** Smaller binaries
- **Platform support:** Not all features everywhere
- **Build time:** Faster compilation
- **Modularity:** Clear boundaries

---

## Future Considerations

- **Plugin system:** Dynamic module loading
- **Database backend:** Optional SQL storage
- **Cloud sync:** Git remote with auth
- **Real-time collaboration:** Operational transforms
- **Mobile support:** Capacitor.js wrapper for PWA

---

**See Also:**
- [Getting Started](./getting-started.md)
- [Data Format](./data-format.md)
- [Development Guide](./development/building.md)
