# ArxOS - Building Version Control

**ArxOS** brings version control to building management. Import IFC files, manage equipment and rooms, track changes with Git, and visualize buildings in 3D — all from your terminal.

**A Decentralized Physical Infrastructure Network (DePIN)** powered by Git—no blockchain complexity, just distributed sensors, crowd-sourced verification, and network effects that grow with participation.

### What Makes ArxOS Different?

- 🌐 **DePIN Architecture** - Decentralized Physical Infrastructure Network with distributed sensors and crowd-sourced building data
- 📦 **Git-Based Storage** - Your building data IS your version control. No databases needed.
- 🔧 **Open Hardware Integration** - Deploy ESP32, RP2040, or Arduino sensors to monitor buildings and earn rewards
- 🏗️ **IFC Import** - Import building models and extract hierarchy automatically
- 🔍 **Smart Search** - Find equipment and rooms with regex and filtering
- 🎨 **3D Visualization** - Interactive terminal-based 3D building visualization
- 🎮 **Gamified Planning** - Interactive PR review and equipment placement with constraint validation
- 📱 **Mobile Support** - Native iOS/Android apps with AR capabilities for field verification
- ⚡ **Terminal-First** - Designed for efficiency and automation

---

## 🚀 Quick Start

### What You Can Do

```bash
# Import an IFC building file
arx import office-building.ifc

# Open spreadsheet editor (Excel-like TUI)
arx spreadsheet equipment --building "Building Name"

# Search with glob patterns (e.g., all boilers on floor 02)
arx spreadsheet equipment --filter "/usa/ny/*/floor-02/*/boiler-*"

# Search for HVAC equipment
arx search "VAV"

# Filter by floor
arx filter --floor 2

# Visualize in 3D
arx render --building "Building Name" --three-d --show-status

# Review contractor PRs (game mode)
arx game review --pr-id pr_001 --building "Building Name" --interactive

# Plan equipment placement with real-time validation
arx game plan --building "Building Name" --interactive
```

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

ArxOS uses a **unified crate structure** with clear module separation:

```
arxos/
├── src/                         # All Rust source code
│   ├── lib.rs                  # Library API (for tests/mobile FFI)
│   ├── main.rs                 # CLI entry point
│   ├── core/                   # Core business logic
│   ├── cli/                    # CLI command definitions
│   ├── ifc/                    # IFC file processing
│   ├── render3d/               # 3D rendering system
│   ├── git/                    # Git integration
│   ├── spatial/                # Spatial operations
│   ├── search/                 # Search & filtering
│   ├── game/                   # Gamified PR review and planning
│   └── [other modules]/
├── ios/                        # iOS Native Shell (SwiftUI)
├── android/                    # Android Native Shell (Jetpack Compose)
└── docs/                       # Documentation
```

### **Module Responsibilities:**

- **`core/`** - Pure business logic (buildings, rooms, equipment data structures)
- **`cli/`** - Command-line interface definitions and parsing
- **`ifc/`** - IFC file processing and parsing
- **`render3d/`** - 3D visualization engine
- **`git/`** - Git repository operations
- **`mobile_ffi/`** - FFI bindings for mobile apps
- **`search/`** - Advanced search and filtering
- **`spatial/`** - 3D coordinate systems and spatial operations
- **`game/`** - Gamified PR review and planning system

---

### **Architecture Philosophy:**

- **Rust Core** - Single unified crate compiled to static library
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
cargo build --target aarch64-apple-ios --release
open ios/ArxOSMobile.xcodeproj
```

**Android:**
```bash
cargo build --target aarch64-linux-android --release
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
