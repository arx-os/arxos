# Building from Source

How to build and install ArxOS from source code.

---

## Prerequisites

### Required

- **Rust** 1.75+ – [Install from rustup.rs](https://rustup.rs)
- **Git** – For cloning the repository
- **C/C++ Compiler** – For native dependencies
  - **Linux:** `gcc` and `g++`
  - **macOS:** Xcode Command Line Tools
  - **Windows:** MSVC (Visual Studio Build Tools)

### Optional

- **Trunk** – For web interface: `cargo install trunk`
- **wasm-pack** – Alternative WASM bundler
- **Docker** – For containerized builds

---

## Quick Build

```bash
# Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Build release binary
cargo build --release

# Binary location
./target/release/arx

# Install to PATH
cargo install --path .

# Verify installation
arx --version
```

---

## Build Configurations

### Debug Build

```bash
# Fast compilation, includes debug symbols
cargo build

# Binary: ./target/debug/arx
# Slower runtime performance
```

### Release Build

```bash
# Optimized for performance
cargo build --release

# Binary: ./target/release/arx
# Smaller size, faster execution
```

### With All Features

```bash
# Include TUI, render3d, agent, web
cargo build --release --all-features
```

### Specific Features

```bash
# Terminal UI only
cargo build --release --features tui

# 3D rendering only
cargo build --release --features render3d

# Remote agent only
cargo build --release --features agent

# Web interface only
cargo build --release --features web

# Multiple features
cargo build --release --features "tui,render3d"
```

---

## Platform-Specific Builds

### Linux

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install build-essential pkg-config libssl-dev

# Build
cargo build --release

# Install
cargo install --path .
```

### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Build
cargo build --release

# Install
cargo install --path .
```

### Windows

```bash
# Install Visual Studio Build Tools
# https://visualstudio.microsoft.com/downloads/

# Build (PowerShell)
cargo build --release

# Install
cargo install --path .
```

---

## Cross-Compilation

### For Linux (from macOS/Windows)

```bash
# Add target
rustup target add x86_64-unknown-linux-gnu

# Build
cargo build --release --target x86_64-unknown-linux-gnu

# Binary: ./target/x86_64-unknown-linux-gnu/release/arx
```

### For Windows (from Linux/macOS)

```bash
# Add target
rustup target add x86_64-pc-windows-msvc

# Install cross-compilation toolchain
# Linux: sudo apt-get install mingw-w64
# macOS: brew install mingw-w64

# Build
cargo build --release --target x86_64-pc-windows-msvc
```

### For macOS (from Linux/Windows)

```bash
# Add target
rustup target add x86_64-apple-darwin

# Requires macOS SDK (legal complications)
# Recommended: Use macOS for macOS builds
```

---

## Web Interface Build

### Development

```bash
# Install Trunk
cargo install trunk

# Add WASM target
rustup target add wasm32-unknown-unknown

# Navigate to web directory
cd src/web

# Start development server
trunk serve

# Opens http://localhost:8080 with hot reload
```

### Production

```bash
cd src/web

# Build optimized WASM bundle
trunk build --release

# Output: dist/
# - index.html
# - pkg/arxos_bg.wasm
# - pkg/arxos.js
# - styles/app.css
```

---

## Optimization

### Size Optimization

```toml
# Cargo.toml
[profile.release]
opt-level = 'z'     # Optimize for size
lto = true          # Link-time optimization
strip = true        # Strip symbols
codegen-units = 1   # Better optimization
```

**Result:** ~5MB binary (from ~15MB)

### Performance Optimization

```toml
[profile.release]
opt-level = 3       # Maximum optimization
lto = "fat"         # Aggressive LTO
codegen-units = 1
```

**Result:** Faster runtime, longer compile time

---

## Docker Build

### Dockerfile

```dockerfile
FROM rust:1.75 as builder

WORKDIR /app
COPY . .

# Build release binary
RUN cargo build --release --all-features

# Runtime image
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y \
      libssl3 \
      ca-certificates \
      git && \
    rm -rf /var/lib/apt/lists/*

# Copy binary
COPY --from=builder /app/target/release/arx /usr/local/bin/

# Set entrypoint
ENTRYPOINT ["arx"]
CMD ["--help"]
```

### Build and Run

```bash
# Build image
docker build -t arxos:latest .

# Run
docker run -it arxos:latest --version

# Mount volume for data
docker run -it -v $(pwd):/data arxos:latest init --name "Building"
```

---

## CI/CD

### GitHub Actions

```yaml
name: Build

on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable
      
      - name: Cache
        uses: actions/cache@v3
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/index/
            ~/.cargo/registry/cache/
            ~/.cargo/git/db/
            target/
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Build
        run: cargo build --release --all-features
      
      - name: Test
        run: cargo test --release --all-features
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: arx-${{ matrix.os }}
          path: target/release/arx*
```

---

## Troubleshooting

### Compilation Errors

**Error:** `linker 'cc' not found`

```bash
# Linux
sudo apt-get install build-essential

# macOS
xcode-select --install
```

**Error:** `failed to run custom build command for 'openssl-sys'`

```bash
# Linux
sudo apt-get install pkg-config libssl-dev

# macOS
brew install openssl
export OPENSSL_DIR=$(brew --prefix openssl)
```

**Error:** `could not find system library 'git2'`

```bash
# Build with vendored libgit2
cargo build --release --features "git2/vendored"
```

### Slow Compilation

```bash
# Use faster linker (Linux)
sudo apt-get install lld
export RUSTFLAGS="-C link-arg=-fuse-ld=lld"

# Use incremental compilation
export CARGO_INCREMENTAL=1

# Reduce parallelism (if out of memory)
cargo build --release -j 1
```

### Out of Memory

```bash
# Reduce codegen units
export CARGO_BUILD_JOBS=1

# Or edit Cargo.toml
[profile.release]
codegen-units = 1
```

---

## Development Tools

### Essential

```bash
# Rust formatter
rustup component add rustfmt
cargo fmt

# Linter
rustup component add clippy
cargo clippy --all-features

# Documentation generator
cargo doc --all-features --no-deps
```

### Optional

```bash
# Code coverage
cargo install cargo-tarpaulin
cargo tarpaulin --all-features

# Benchmarking
cargo bench

# Audit dependencies
cargo install cargo-audit
cargo audit

# Check outdated dependencies
cargo install cargo-outdated
cargo outdated
```

---

## Build Scripts

### Automated Build Script

```bash
#!/bin/bash
# build.sh

set -e

echo "Building ArxOS..."

# Clean previous builds
cargo clean

# Format code
cargo fmt --all

# Lint
cargo clippy --all-features -- -D warnings

# Test
cargo test --all-features

# Build release
cargo build --release --all-features

# Build web interface
cd src/web
trunk build --release
cd ../..

echo "✅ Build complete!"
echo "Binary: ./target/release/arx"
echo "Web: ./src/web/dist/"
```

**Usage:**
```bash
chmod +x build.sh
./build.sh
```

---

## Installation

### System-wide Installation

```bash
# Install from local path
cargo install --path .

# Installs to ~/.cargo/bin/arx
# Add to PATH if not already
export PATH="$HOME/.cargo/bin:$PATH"
```

### Custom Installation Path

```bash
# Install to specific directory
cargo install --path . --root /usr/local

# Creates /usr/local/bin/arx
```

### Uninstall

```bash
# Remove installed binary
cargo uninstall arx
```

---

## Verification

### Test Installation

```bash
# Check version
arx --version

# Run help
arx --help

# Create test building
mkdir test-building
cd test-building
arx init --name "Test" --git-init

# Verify it works
arx status
```

### Run Tests

```bash
# Unit tests
cargo test

# Integration tests
cargo test --test '*'

# With all features
cargo test --all-features

# Specific test
cargo test test_building_creation
```

---

**See Also:**
- [Testing Guide](./testing.md) – Running tests and benchmarks
- [Contributing Guide](./contributing.md) – Contribution guidelines
- [Architecture](../architecture.md) – System design
