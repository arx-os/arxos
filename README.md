# ArxOS - Git for Buildings

**ArxOS** is a free, open-source tool that brings version control to building management. It's designed with a **terminal-first philosophy** and uses **Git as the primary data store**.

## 🏗️ Architecture

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

### **Mobile Architecture:**

- **Rust Core** - Single unified crate compiled to FFI library
- **Native UI Shells** - iOS (Swift/SwiftUI) and Android (Kotlin/Jetpack Compose)
- **Git-First** - No database required, uses Git for all data storage

## 🚀 Getting Started

### **Prerequisites:**
- Rust 1.70+
- Git
- iOS: Xcode 14+ (for mobile development)
- Android: Android Studio (for mobile development)

### **Build:**
```bash
# Build the project
cargo build

# Build in release mode
cargo build --release

# Build for mobile (iOS)
cargo build --target aarch64-apple-ios --release

# Build for mobile (Android)
cargo build --target aarch64-linux-android --release
```

### **Run CLI:**
```bash
# Run the CLI
cargo run -- --help

# Or if installed via cargo install
arxos --help

# Room management
cargo run -- room create --name "Classroom 301" --floor 3

# Equipment management
cargo run -- equipment add --name "VAV-301" --equipment-type HVAC
```

## 📱 Mobile Development

### **iOS Development:**
```bash
cd ios
# Build Rust library for iOS
cargo build --target aarch64-apple-ios --release
# Then open the Xcode project
open ArxOSMobile.xcodeproj
```

### **Android Development:**
```bash
cd android
# Build Rust library for Android
cargo build --target aarch64-linux-android --release
# Then build the Android app
./gradlew build
```

## 🧪 Testing

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test file
cargo test --test integration_tests
```

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [User Guide](docs/USER_GUIDE.md)
- [Mobile Build Guide](docs/MOBILE_BUILD_GUIDE.md)
- [Hardware Integration](docs/hardware_integration.md)
- [IFC Processing](docs/ifc_processing.md)

## 🎯 Key Features

- **Git-First Architecture** - No database required
- **Terminal-First** - Optimized for command-line usage
- **Cross-Platform** - CLI + Native mobile apps
- **High Performance** - Rust core with native UI shells
- **AR/LiDAR Support** - Mobile AR scanning capabilities
- **Spatial Data Processing** - 3D coordinate systems
- **Equipment Management** - YAML-based equipment data
- **Version Control** - Git-based change tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Rust for performance and safety
- Uses Git for version control and collaboration
- Inspired by the terminal-first philosophy
- Designed for building management professionals
