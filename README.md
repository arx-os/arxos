# ArxOS - Building Version Control

**ArxOS** brings version control to building management. Import IFC files, manage equipment and rooms, track changes with Git, and visualize buildings in 3D — all from your terminal.

**A Decentralized Physical Infrastructure Network (DePIN)** powered by Git—no blockchain complexity, just distributed, crowd-sourced verification, and network effects that grow with participation.

### What Makes ArxOS Different?

- 🌐 **DePIN Architecture** - Decentralized Physical Infrastructure Network with distributed sensors and crowd-sourced building data
- 📦 **Git-Based Storage** - Your building data IS your version control. No databases needed.
- 🔧 **Open Hardware Integration** - Deploy ESP32, RP2040, or Arduino sensors to monitor buildings and earn rewards
- 🏗️ **IFC Import** - Import building models and extract hierarchy automatically
- 🔍 **Smart Search** - Find equipment and rooms with regex and filtering
- 🎨 **3D Visualization** - Interactive terminal-based 3D building visualization
- 🎮 **Gamified Planning** - Interactive PR review and equipment placement with constraint validation
- 🪙 **On-Chain Economy** - Polygon contracts, staking CLI, and mobile FFI for rewards and revenue splits
- 📱 **Mobile Support** - Native iOS/Android apps with AR capabilities for field verification
- ⚡ **Terminal-First** - Designed for efficiency and automation

---

## 🚀 Quick Start

### Quick Start Examples

#### Building Management
```bash
# Initialize a new building project
arx init "Office Building" --location "123 Main St"

# Import IFC building model
arx import building.ifc --output "Office Building"

# Query building information
arx query "/usa/ny/brooklyn/*/floor-*/room-*"

# View building structure
arx list --building "Office Building"
```

#### Equipment Management
```bash
# Add equipment to a building
arx add equipment --building "Office Building" --floor 1 \
  --name "VAV-101" --type HVAC --position "10,20,3"

# Open spreadsheet editor for equipment (Excel-like TUI)
arx spreadsheet equipment --building "Office Building"

# Search for specific equipment
arx search "VAV" --building "Office Building"

# Filter equipment by floor
arx filter --floor 2 --type HVAC

# Remove equipment
arx remove equipment "VAV-101" --building "Office Building"
```

#### Room Management
```bash
# Add a room
arx add room --building "Office Building" --floor 1 \
  --name "Conference Room A" --type Office \
  --dimensions "10x8x3"

# Edit rooms in spreadsheet
arx spreadsheet rooms --building "Office Building"

# List rooms on a floor
arx list rooms --floor 1
```

#### Version Control & Collaboration
```bash
# View change history
arx history --building "Office Building"

# Show current changes
arx diff --building "Office Building"

# Commit changes
arx commit --building "Office Building" -m "Added HVAC equipment"

# View Git log
arx log --building "Office Building"
```

#### Export & Integration
```bash
# Export to IFC
arx export ifc --building "Office Building" --output building.ifc

# Export to AR formats (glTF/USDZ)
arx export ar --building "Office Building" --format gltf --output model.gltf
arx export ar --building "Office Building" --format usdz --output model.usdz

# Generate documentation
arx docs --building "Office Building" --output docs/
```

#### Visualization & Analysis
```bash
# Visualize in 3D (terminal-based)
arx render --building "Office Building" --three-d --show-status

# Health dashboard
arx dashboard health --building "Office Building"

# Status dashboard
arx dashboard status --building "Office Building"

# Watch mode (live updates)
arx watch --building "Office Building"
```

#### AR & Mobile Integration
```bash
# Manage pending AR-detected equipment
arx ar pending --building "Office Building"

# Process AR scan data
arx ar process scan.json --building "Office Building"
```

#### Gamified Workflows
```bash
# Review contractor PRs interactively
arx game review --pr-id pr_001 --building "Office Building" --interactive

# Plan equipment placement with validation
arx game plan --building "Office Building" --interactive
```

📖 **[See Complete CLI Reference](docs/CLI_REFERENCE.md)** for all commands and options

---

## Installation

**Currently requires building from source:**

```bash
# Install Rust (one-time setup)
# https://www.rust-lang.org/tools/install

# Clone and build
git clone https://github.com/arx-os/arxos.git
cd arxos
cargo build --release

# Windows: Binary at target/release/arx.exe
# macOS/Linux: Binary at target/release/arx
```

### Docker Quick Start

Prefer running ArxOS in a container?

```bash
# Pull the official runtime image
docker pull ghcr.io/arx-os/arxos:runtime

# Run the CLI (mount your repo into /workspace)
docker run --rm -v "$(pwd)":/workspace ghcr.io/arx-os/arxos:runtime list --help
```

See `docs/development/DOCKER_GUIDE.md` for full details on builder and Android SDK images.

### Kubernetes Automation

Automate ArxOS tasks at scale with Kubernetes Jobs, CronJobs, or a custom operator. Start with `docs/development/K8S_GUIDE.md` for architecture, CRDs, and Helm chart plans.

📖 **[Complete User Guide](docs/core/USER_GUIDE.md)** - Learn all the commands and features

### Security

ArxOS follows security best practices with automated scanning and comprehensive protections:

- 🔒 Pre-commit hooks for secret detection
- 🔍 CI/CD security scanning on every push
- 🛡️ Path traversal protection
- ✅ FFI safety hardening
- 🧪 20+ security tests

📋 **[Security Guide](docs/development/SECURITY.md)**

---

## 📚 Documentation

- **[User Guide](docs/core/USER_GUIDE.md)** - Complete usage instructions for end users
- **[API Reference](docs/API_REFERENCE.md)** - Comprehensive API reference for CLI, FFI, and core types
- **[Examples](examples/)** - Example building data files and usage patterns
- **[Game System](docs/features/GAME_SYSTEM.md)** - Gamified PR review and planning system
- **[Architecture](docs/core/ARCHITECTURE.md)** - System design and technical details  
- **[Mobile FFI Integration](docs/mobile/MOBILE_FFI_INTEGRATION.md)** - Mobile app development
- **[Hardware Integration](docs/features/HARDWARE_INTEGRATION.md)** - Deploy sensors and contribute to the DePIN network
- **[Reward System](docs/business/REWARD_SYSTEM.md)** - How contributors earn rewards for building data (USD-based, no crypto complexity)

---

## 🏗️ Project Structure

ArxOS is organised as a multi-crate Cargo workspace:

```
arxos/
├── docs/                         # Documentation and design references
├── crates/
│   ├── arx/                      # Protocol core (IFC, Git, spatial, YAML, DePIN primitives)
│   │   ├── src/
│   │   └── examples/
│   ├── arxui/                    # Terminal UI + optional 3D renderer + CLI binary `arx`
│   │   ├── src/
│   │   │   ├── cli/
│   │   │   ├── commands/
│   │   │   ├── render3d/
│   │   │   └── tui/
│   │   └── assets/
│   ├── arxos/                    # Embedded runtime core (no_std capable)
│   │   └── src/
│   └── arxos-hal/                # Hardware abstraction layer workspace
│       ├── src/
│       ├── esp32-c3/
│       └── rp2040/
├── ios/                          # iOS native shell (SwiftUI)
├── android/                      # Android native shell (Jetpack Compose)
├── scripts/                      # Tooling and automation
├── tests/                        # Cross-crate integration tests
└── examples/                     # Sample IFC/building datasets
```

### **Crate Responsibilities:**

- **`crates/arx`** – Core protocol: immutable data model, IFC parser, Git manager, spatial engine, YAML serializer, and DePIN primitives.
- **`crates/arxui`** – Binary crate delivering the `arx` CLI, TUI widgets, command handlers, and optional 3D renderer (`render3d` feature).
- **`crates/arxos`** – Embedded/runtime systems: hardware ingestion, mobile FFI surface, runtime services, and a minimal `no_std` runtime core.
- **`crates/arxos-hal`** – Aggregated hardware abstraction layer with board-specific sub-crates (ESP32-C3, RP2040, …).

---

### **Architecture Philosophy:**

- **Layered Crates** – Protocol (`arx`), UI (`arxui`), runtime (`arxos`), and hardware (`arxos-hal`) cleanly separated.
- **Git-native workflow** – Buildings stored as YAML tracked in Git repositories.
- **FFI-first** – Mobile apps consume the same Rust logic via the FFI surface in `crates/arxos`.
- **Hardware-aware** – Sensors plug into Git-managed buildings through the HAL workspace.
- **Native UI Shells** - iOS (Swift/SwiftUI) and Android (Jetpack Compose)
- **Git-First DePIN** - No database required, uses Git for distributed data storage and contribution tracking
- **Decentralized Network** - Building owners, sensor operators, and field technicians contribute to a distributed building data network
- **FFI Integration** - Mobile apps call Rust via C FFI bindings

---

## 👨‍💻 For Developers

### Development Setup

**Prerequisites:**
- Rust (latest stable): https://rustup.rs/
- Git
- Optional: `cbindgen` for FFI header generation (`cargo install cbindgen`)

**Initial Setup:**
```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# Build the project
cargo build

# Run tests
cargo test
```

### Build for Development

```bash
# Debug build (faster iteration)
cargo build

# Release build (optimized)
cargo build --release

# With specific features
cargo build --features android  # For Android JNI support
```

### Testing

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test suite
cargo test ar_workflow

# Run tests in release mode
cargo test --release
```

### Code Quality

```bash
# Format code
cargo fmt

# Lint with clippy
cargo clippy

# Check for warnings
cargo clippy -- -W clippy::all
```

**Note:** Pre-commit hooks automatically run `fmt`, `clippy`, and tests before commits. CI/CD runs stricter checks with `-D warnings`.

### Mobile Development

**iOS:**
```bash
cargo build -p arxos --target aarch64-apple-ios --release
open ios/ArxOSMobile.xcodeproj
```

**Android:**
```bash
cargo build -p arxos --target aarch64-linux-android --release
cd android && ./gradlew build
```

See [Mobile FFI Integration](docs/mobile/MOBILE_FFI_INTEGRATION.md) for details.

---

## 🔧 Troubleshooting

### Common Issues

**Build Errors:**
- Ensure you have the latest Rust toolchain: `rustup update`
- Clean build artifacts: `cargo clean && cargo build`
- Check platform-specific dependencies (see mobile development sections)

**Test Failures:**
- Some tests require Git repository: Initialize with `git init` in test directory
- Serial tests may conflict: Run with `cargo test --test-threads=1`
- Platform-specific tests: See [Mobile FFI Integration](docs/mobile/MOBILE_FFI_INTEGRATION.md)

**FFI Header Generation:**
- Install cbindgen: `cargo install cbindgen`
- Headers auto-generate during build if cbindgen is available
- Falls back to validation-only if cbindgen is not installed

**Mobile Build Issues:**
- iOS: Ensure Xcode Command Line Tools installed: `xcode-select --install`
- Android: Install Android NDK and set `ANDROID_NDK_HOME`
- See platform-specific guides in `docs/mobile/`

**Performance Issues:**
- Use release builds: `cargo build --release`
- Enable parallel processing in config
- See [Performance Guide](docs/development/PERFORMANCE_GUIDE.md)

### Getting Help

- **Documentation**: Check [Documentation Index](docs/DOCUMENTATION_INDEX.md)
- **Issues**: Open an issue on GitHub with:
  - Platform and Rust version (`rustc --version`)
  - Error messages and logs
  - Steps to reproduce

## 🤝 Contributing

We welcome contributions! Please see [Developer Onboarding](docs/development/DEVELOPER_ONBOARDING.md) for setup and contribution guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Contributing to the DePIN Network

ArxOS operates as a **Decentralized Physical Infrastructure Network** where you can:

- **Deploy Sensors**: Install ESP32, RP2040, or Arduino sensors to monitor buildings
- **Verify Buildings**: Use mobile AR apps to scan and verify building equipment
- **Contribute Data**: Share anonymized building metadata (privacy-preserving)
- **Earn Rewards**: Get paid in USD based on your contributions (see [Reward System](docs/business/REWARD_SYSTEM.md))

All contributions are tracked via Git—no blockchain or cryptocurrency required. Just Git commits and USD payments.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
