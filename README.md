# ArxOS - Git for Buildings

**ArxOS** brings version control to building management. Import IFC files, manage equipment and rooms, track changes with Git, and visualize buildings in 3D—all from your terminal.

**A Decentralized Physical Infrastructure Network (DePIN)** powered by Git—no blockchain complexity, just distributed sensors, crowd-sourced verification, and network effects that grow with participation.

### What Makes ArxOS Different?

- 🌐 **DePIN Architecture** - Decentralized Physical Infrastructure Network with distributed sensors and crowd-sourced building data
- 📦 **Git-Based Storage** - Your building data IS your version control. No databases needed.
- 🔧 **Open Hardware Integration** - Deploy ESP32, RP2040, or Arduino sensors to monitor buildings and earn rewards
- 🏗️ **IFC Import** - Import building models and extract hierarchy automatically
- 🔍 **Smart Search** - Find equipment and rooms with regex and filtering
- 🎨 **3D Visualization** - Interactive terminal-based 3D building visualization
- 📱 **Mobile Support** - Native iOS/Android apps with AR capabilities for field verification
- ⚡ **Terminal-First** - Designed for efficiency and automation

---

## 🚀 Quick Start

### What You Can Do

```bash
# Import an IFC building file
arx import office-building.ifc

# Search for HVAC equipment
arx search "VAV"

# Filter by floor
arx filter --floor 2

# Visualize in 3D
arx render --building "Building Name" --three-d --show-status
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

📖 **[Complete User Guide](docs/USER_GUIDE.md)** - Learn all the commands and features

### Security

ArxOS follows security best practices with automated scanning and comprehensive protections:

- 🔒 Pre-commit hooks for secret detection
- 🔍 CI/CD security scanning on every push
- 🛡️ Path traversal protection
- ✅ FFI safety hardening
- 🧪 20+ security tests

📋 **[Security Audit Report](docs/SECURITY_AUDIT_REPORT.md)** | **[Security Guide](docs/SECURITY.md)**

---

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage instructions for end users
- **[Architecture](docs/ARCHITECTURE.md)** - System design and technical details  
- **[Mobile FFI Integration](docs/MOBILE_FFI_INTEGRATION.md)** - Mobile app development
- **[Hardware Integration](docs/hardware_integration.md)** - Deploy sensors and contribute to the DePIN network
- **[Reward System](docs/reward_system.md)** - How contributors earn rewards for building data (USD-based, no crypto complexity)

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

---

### **Architecture Philosophy:**

- **Rust Core** - Single unified crate compiled to static library
- **Native UI Shells** - iOS (Swift/SwiftUI) and Android (Jetpack Compose)
- **Git-First DePIN** - No database required, uses Git for distributed data storage and contribution tracking
- **Decentralized Network** - Building owners, sensor operators, and field technicians contribute to a distributed building data network
- **FFI Integration** - Mobile apps call Rust via C FFI bindings

---

## 👨‍💻 For Developers

### Build for Development

```bash
cargo build --release
```

### Test

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture
```

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

See [docs/MOBILE_FFI_INTEGRATION.md](docs/MOBILE_FFI_INTEGRATION.md) for details.

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/CONTRIBUTING.md).

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
- **Earn Rewards**: Get paid in USD based on your contributions (see [Reward System](docs/reward_system.md))

All contributions are tracked via Git—no blockchain or cryptocurrency required. Just Git commits and USD payments.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
