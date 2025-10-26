# ArxOS - Git for Buildings

**ArxOS** is a free, open-source tool that brings version control to building management. It's designed with a **terminal-first philosophy** and uses **Git as the primary data store**.

## 🏗️ Architecture

ArxOS uses a **monorepo structure** with clear separation of concerns:

```
arxos/
├── crates/                      # Shared Rust crates
│   ├── arxos-core/              # Core business logic
│   ├── arxos-mobile/             # Mobile FFI wrapper
│   └── arxos-cli/                # CLI application
├── ios/                         # iOS Native Shell
├── android/                     # Android Native Shell
└── docs/                        # Documentation
```

### **Crate Responsibilities:**

- **`arxos-core`** - Pure business logic (spatial processing, equipment management, Git operations)
- **`arxos-mobile`** - FFI wrapper for mobile applications (iOS/Android)
- **`arxos-cli`** - Command-line interface using arxos-core

### **Mobile Architecture:**

- **Rust Core** - High-performance data processing via FFI
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
# Build all crates
cargo build --workspace

# Build specific crate
cargo build -p arxos-cli
cargo build -p arxos-core
cargo build -p arxos-mobile
```

### **Run CLI:**
```bash
# Run the CLI
cargo run --bin arxos-cli -- --help

# Room management
cargo run --bin arxos-cli -- room create --name "Classroom 301" --floor 3

# Equipment management
cargo run --bin arxos-cli -- equipment add --name "VAV-301" --equipment-type HVAC
```

## 📱 Mobile Development

### **iOS Development:**
```bash
cd ios
# iOS project setup will be added here
```

### **Android Development:**
```bash
cd android
# Android project setup will be added here
```

## 🧪 Testing

```bash
# Run all tests
cargo test --workspace

# Run specific crate tests
cargo test -p arxos-core
cargo test -p arxos-mobile
cargo test -p arxos-cli
```

## 📚 Documentation

- [Architecture Overview](ARXOS_ARCHITECTURE_V2.md)
- [Development Roadmap](DEVELOPMENT_ROADMAP.md)
- [High School Project Questions](HIGH_SCHOOL_PROJECT_QUESTIONS.md)

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
