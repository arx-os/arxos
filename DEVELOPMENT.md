# Arxos Development Environment Setup

## Quick Start for Engineering Team

This guide gets you from zero to building stadium-scale building intelligence in **under 10 minutes**.

## 🚀 Prerequisites

### Required Tools
```bash
# 1. Rust toolchain with WASM support
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup target add wasm32-unknown-unknown

# 2. WASM development tools
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

# 3. Database tools
# Ubuntu/Debian:
sudo apt-get install sqlite3 sqlite3-tools

# macOS:
brew install sqlite

# Windows:
# Download from https://sqlite.org/download.html
```

### Optional Tools (Recommended)
```bash
# Node.js for WASM testing
nvm install 18
nvm use 18

# iOS development (for iPhone LiDAR integration)
# Xcode 15+ with iOS 17+ SDK
# Requires macOS and Apple Developer account

# Database inspection
cargo install sqlitebrowser  # GUI database browser
```

## 🏗️ Project Structure

```
arxos/
├── src/
│   ├── core/           # Rust core library (13-byte ArxObject, compression)
│   ├── terminal/       # CLI tools and ASCII rendering
│   └── embedded/       # ESP32 mesh sensor firmware
├── migrations/         # Database schema migrations  
├── docs/              # Complete technical documentation
├── .github/workflows/ # CI/CD pipeline
└── build.sh           # Development build script
```

## ⚡ Development Workflow

### 1. Clone and Build
```bash
git clone https://github.com/arx-os/arxos.git
cd arxos

# Build all components
./build.sh

# Or manually:
cargo build --workspace
```

### 2. Database Setup
```bash
# Create development database
sqlite3 dev.db < migrations/001_init_spatial_database.sql
sqlite3 dev.db < migrations/002_object_type_definitions.sql

# Verify schema
sqlite3 dev.db ".schema" | head -20
```

### 3. Test Core Library
```bash
# Run all tests
cargo test --workspace

# Test 13-byte ArxObject constraint
cargo test --package arxos-core size_constraint_test -- --nocapture

# Performance benchmarks
cargo bench --package arxos-core
```

### 4. WASM Development
```bash
cd src/core

# Build for web deployment
wasm-pack build --target web --features wasm

# Test in browser
python3 -m http.server 8000
# Open http://localhost:8000/pkg/
```

### 5. Terminal Interface
```bash
# Build CLI tool
cargo build --package arxos-terminal

# Test ASCII rendering
./target/debug/arxos-terminal render-demo
```

## 🏟️ Stadium-Scale Testing

### Load Test Database
```bash
# Generate 190K objects for Raymond James Stadium simulation
cargo run --package arxos-core --bin stadium-simulator -- \
  --venue-type stadium \
  --square-feet 1900000 \
  --floors 4 \
  --output stadium-data.sql

# Load into database
sqlite3 stadium.db < stadium-data.sql

# Test spatial queries
sqlite3 stadium.db "
  SELECT COUNT(*) FROM arxobjects_spatial 
  WHERE min_x BETWEEN 10000 AND 20000;
"
```

### Performance Benchmarks
```bash
# Database performance at scale
cargo bench spatial_benchmark

# WASM bundle size check
cd src/core && wasm-pack build --release --target web
ls -la pkg/*.wasm  # Should be under 5MB

# Memory usage test
cargo run --package arxos-core --bin memory-test
```

## 📱 Mobile Development Setup

### iOS (iPhone LiDAR Integration)
```bash
# Requires macOS with Xcode 15+
xcode-select --install

# Install iOS targets
rustup target add aarch64-apple-ios
rustup target add x86_64-apple-ios  # For simulator

# Create iOS test project
cd ios/
xcodebuild -scheme ArxosDemo -destination 'platform=iOS Simulator,name=iPhone 15 Pro' test
```

### Android (ARCore Integration)  
```bash
# Install Android targets
rustup target add aarch64-linux-android
rustup target add armv7-linux-androideabi

# Android NDK setup (follow Android documentation)
# Build for Android
cargo build --target aarch64-linux-android
```

## 🧪 Testing Strategy

### Unit Tests
```bash
# Core library tests
cargo test --package arxos-core

# Database migration tests  
./test_migrations.sh

# WASM compilation tests
cd src/core && wasm-pack test --node
```

### Integration Tests
```bash
# Stadium workflow simulation
cargo test --package arxos-core stadium_workflow_test

# Contractor BILT reward calculation
cargo test --package arxos-core bilt_calculation_test

# Spatial query performance
cargo test --package arxos-core spatial_performance_test
```

### CI/CD Pipeline
```bash
# Local CI simulation
act -j test-rust-core          # GitHub Actions locally
act -j test-wasm-compilation   # WASM build verification  
act -j simulate-stadium-data   # Stadium scale testing
```

## 🔧 Development Tools

### Database Inspection
```bash
# CLI database exploration
sqlite3 dev.db
.tables
.schema arxobjects
SELECT * FROM object_types LIMIT 10;

# GUI database browser
sqlitebrowser dev.db
```

### Code Quality
```bash
# Formatting
cargo fmt --all

# Linting  
cargo clippy --all-targets --all-features -- -D warnings

# Documentation
cargo doc --workspace --no-deps --open
```

### Debugging
```bash
# Debug builds with full symbols
cargo build --workspace

# Run with backtrace
RUST_BACKTRACE=full cargo test failing_test_name

# Memory debugging (with valgrind)
cargo build --features debug-allocator
valgrind ./target/debug/arxos-terminal
```

## 📊 Key Metrics to Monitor

### Performance Targets
- **ArxObject serialization**: <1ms for 13-byte object
- **Spatial queries**: <50ms for 10K+ objects  
- **WASM bundle size**: <5MB for mobile deployment
- **Memory usage**: <100MB for stadium-scale dataset
- **Database size**: <1GB for 1.9M sqft building

### Quality Gates  
- **Test coverage**: >90% for core library
- **No unsafe code**: In core spatial algorithms
- **WASM compatibility**: All core functions
- **Cross-platform builds**: Windows, macOS, Linux
- **Performance benchmarks**: Must not regress >10%

## 🚀 Ready for Stadium Deployment

### Implementation Priority
1. **WASM compilation** (Week 1) - Universal deployment
2. **iPhone integration** (Week 2-3) - LiDAR capture + AR markup
3. **BIM file daemon** (Week 4) - PDF/IFC/DWG processing
4. **Stadium pilot** (Week 5-6) - Raymond James Stadium trial

### Success Metrics
- ✅ **75% vision compliance** - Architecture implemented
- ✅ **Stadium-scale database** - 1.9M sqft tested
- ✅ **BILT funding model** - Business case proven
- 🔄 **iPhone AR interface** - In development
- 🔄 **Multi-CMMS integration** - In development

## 📚 Additional Resources

- **Architecture Documentation**: `/docs/03-architecture/`
- **API Reference**: `/docs/09-api-reference/`  
- **Business Model**: `/docs/12-dsa-business-model/`
- **Human-in-Loop Workflows**: `/docs/13-human-in-the-loop/`
- **BIM Integration**: `/docs/14-bim-daemon/`

## 🐛 Troubleshooting

### Common Issues

**WASM compilation fails**:
```bash
# Ensure correct Rust version
rustc --version  # Should be 1.70+
rustup update

# Clear cache and rebuild  
cargo clean
wasm-pack build --target web
```

**Database migration errors**:
```bash
# Check SQLite version
sqlite3 --version  # Should be 3.35+

# Manual migration
sqlite3 dev.db < migrations/001_init_spatial_database.sql
```

**Performance issues**:
```bash
# Profile with perf (Linux)
cargo build --release
perf record ./target/release/arxos-terminal
perf report

# Memory profiling
cargo install cargo-profiler
cargo profiler callgrind --bench spatial_benchmark
```

---

**Ready to build stadium-scale building intelligence!** 🏟️

*For questions: Check `/docs/` or create GitHub issues*