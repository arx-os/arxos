# ArxOS Build Scripts

This directory contains automation scripts for building, testing, and setting up the ArxOS development environment.

## Scripts Overview

### Build Scripts

#### `build-mobile-ios.sh`
**Purpose:** Builds the Rust library for iOS and creates an XCFramework.

**Usage:**
```bash
./scripts/build-mobile-ios.sh
```

**Requirements:**
- macOS (iOS builds require macOS)
- Xcode with Command Line Tools
- Rust toolchain with iOS targets

**What it does:**
1. Checks for macOS platform
2. Sets up Xcode environment
3. Installs iOS Rust targets if needed
4. Builds for iOS devices (arm64) and simulators (x86_64, arm64)
5. Creates universal simulator library using `lipo`
6. Packages XCFramework with proper structure and Info.plist

**Output:**
- `ios/build/ArxOS.xcframework` - XCFramework ready for Xcode integration

---

#### `build-mobile-android.sh`
**Purpose:** Builds the Rust library for Android (all architectures).

**Usage:**
```bash
./scripts/build-mobile-android.sh
```

**Requirements:**
- Android NDK installed and `ANDROID_NDK_HOME` set
- Rust toolchain with Android targets installed
- Cargo configured for Android cross-compilation

**What it does:**
1. Validates Android NDK path
2. Builds for all Android architectures:
   - `aarch64-linux-android` (ARM64)
   - `armv7-linux-androideabi` (ARMv7)
   - `i686-linux-android` (x86)
   - `x86_64-linux-android` (x86_64)
3. Copies .so files to `android/app/src/main/jniLibs/` directories

**Environment Variables:**
- `ANDROID_NDK_HOME` - Path to Android NDK (required)

**Output:**
- `.so` files in `target/{target}/release/libarxos.so`
- Copied to `android/app/src/main/jniLibs/{arch}/`

---

#### `build-android-mac.sh`
**Purpose:** Builds the Rust library for Android on macOS using `cargo-ndk`.

**Usage:**
```bash
./scripts/build-android-mac.sh
```

**Requirements:**
- macOS
- Homebrew (for NDK installation)
- `cargo-ndk` installed (`cargo install cargo-ndk`)

**What it does:**
1. Installs Android NDK via Homebrew if not found
2. Uses `cargo-ndk` to build and automatically copy libraries
3. Builds for ARM64 and ARMv7 architectures

**Note:** This script is macOS-specific and uses `cargo-ndk` for easier setup. For Linux or manual NDK setup, use `build-mobile-android.sh`.

---

#### `build-workspace.sh` / `build-workspace.bat`
**Purpose:** Builds the entire ArxOS workspace (main crate, tests, benchmarks).

**Usage:**
```bash
# Unix/macOS
./scripts/build-workspace.sh

# Windows
scripts\build-workspace.bat
```

**What it does:**
1. Builds protocol core (`crates/arx`), CLI (`crates/arxui`), and runtime (`crates/arxos`)
2. Builds all tests (`cargo test --no-run`)
3. Builds all benchmarks (`cargo bench --no-run`)

---

#### `build-mobile.bat`
**Purpose:** Windows batch script for mobile builds (placeholder for future implementation).

**Usage:**
```cmd
scripts\build-mobile.bat android
scripts\build-mobile.bat install
```

**Note:** Currently checks for FFI bindings and provides instructions. Full implementation pending.

---

### Utility Scripts

#### `link-framework.sh`
**Purpose:** Helper script to guide Xcode framework linking (doesn't auto-link due to Xcode complexity).

**Usage:**
```bash
./scripts/link-framework.sh
```

**What it does:**
1. Checks if XCFramework exists
2. Checks if already linked in Xcode project
3. Provides step-by-step instructions for manual linking

**Note:** Manual linking is recommended because Xcode project files are complex and error-prone to edit programmatically.

---

#### `setup-android-cargo.sh`
**Purpose:** Configures Cargo for Android cross-compilation (one-time setup).

**Usage:**
```bash
./scripts/setup-android-cargo.sh
```

**Requirements:**
- Android NDK installed
- `ANDROID_NDK_HOME` environment variable set (or default path)

**What it does:**
1. Detects Android NDK toolchain
2. Generates `~/.cargo/config.toml` with Android linker configuration
3. Backs up existing config if present
4. Configures all 4 Android architectures

**Note:** This is a one-time setup. Run before first Android build.

---

#### `setup-security-hooks.sh`
**Purpose:** Sets up Git pre-commit hooks for code quality and security.

**Usage:**
```bash
./scripts/setup-security-hooks.sh
```

**What it does:**
1. Installs `pre-commit` tool if not present
2. Installs pre-commit hooks from `.pre-commit-config.yaml`
3. Creates secrets baseline if not exists
4. Runs hooks on all files (first-time setup)

**Hooks installed:**
- Rust formatting (`cargo fmt`)
- Rust linting (`cargo clippy`)
- Rust tests (`cargo test`)
- File checks (trailing whitespace, etc.)
- Secret detection (`detect-secrets`)
- Private key detection

---

## Prerequisites

### All Scripts
- Rust toolchain (latest stable)
- `cargo` and `rustup`

### iOS Builds
- macOS
- Xcode with Command Line Tools
- `lipo` tool (comes with Xcode)

### Android Builds
- Android NDK (version 26+ recommended)
- Rust Android targets installed
- For macOS: `cargo-ndk` (`cargo install cargo-ndk`)
- For Linux/Windows: Manual NDK setup

### Setup Scripts
- Python 3 with `pip` (for `pre-commit`)
- `detect-secrets` (optional, for secret scanning)

---

## Environment Variables

### Android Builds
```bash
export ANDROID_NDK_HOME=/path/to/android-ndk
```

### iOS Builds
```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer  # Optional
export IPHONEOS_DEPLOYMENT_TARGET=17.0  # Optional, defaults to 17.0
```

---

## Quick Start

### Initial Setup
```bash
# 1. Set up security hooks
./scripts/setup-security-hooks.sh

# 2. Build workspace
./scripts/build-workspace.sh
```

### Mobile Development Setup

#### iOS
```bash
# Build for iOS
./scripts/build-mobile-ios.sh

# Link framework in Xcode (manual steps)
./scripts/link-framework.sh  # Shows instructions
```

#### Android (macOS)
```bash
# Install cargo-ndk if not installed
cargo install cargo-ndk

# Build for Android
./scripts/build-android-mac.sh
```

#### Android (Linux/Manual)
```bash
# Set NDK path
export ANDROID_NDK_HOME=$HOME/Android/Sdk/ndk-bundle

# Setup Cargo configuration (one-time setup)
./scripts/setup-android-cargo.sh

# Install Android targets
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android

# Build
./scripts/build-mobile-android.sh
```

---

## Troubleshooting

### "lipo: command not found"
**Solution:** Install Xcode Command Line Tools:
```bash
xcode-select --install
```

### "Android NDK not found"
**Solution:** Set `ANDROID_NDK_HOME` environment variable:
```bash
export ANDROID_NDK_HOME=/path/to/android-ndk
```

### "cargo-ndk: command not found"
**Solution:** Install cargo-ndk:
```bash
cargo install cargo-ndk
```

### "Rust target not installed"
**Solution:** Install the required target:
```bash
rustup target add <target-name>
```

### Build fails with linker errors
**Solution:** Ensure Cargo is configured for cross-compilation. See Android build guide for `~/.cargo/config.toml` setup.

---

## Script Maintenance

### Adding New Scripts
1. Follow existing naming conventions (`build-`, `setup-`, `test-`, etc.)
2. Include shebang (`#!/bin/bash` for shell scripts)
3. Use `set -e` for error handling
4. Add prerequisite checks
5. Provide clear error messages
6. Update this README

### Best Practices
- ✅ Check for prerequisites before use
- ✅ Use `set -e` for error handling
- ✅ Provide helpful error messages
- ✅ Use colors for better UX (optional)
- ✅ Document what the script does
- ✅ Make scripts idempotent (safe to run multiple times)

---

## Related Documentation

- [Mobile Build Guide](../docs/mobile/ANDROID.md)
- [iOS Build Guide](../docs/mobile/IOS_AR_INTEGRATION_PLAN.md)
- [CI/CD Documentation](../docs/mobile/MOBILE_CI_CD.md)
- [Development Setup](../README.md#development-setup)

---

## Script Comparison

### Android Build Scripts

| Feature | `build-mobile-android.sh` | `build-android-mac.sh` |
|---------|---------------------------|------------------------|
| Platform | Linux/Windows/Generic | macOS only |
| NDK Setup | Manual | Auto-install via Homebrew |
| Tool Used | Direct `cargo build` | `cargo-ndk` |
| File Copying | Manual | Automatic |
| Architectures | All 4 | ARM64 + ARMv7 only |
| **When to use** | Linux/Windows, manual NDK | macOS, quick setup |

**Recommendation:** Use `build-android-mac.sh` on macOS, `build-mobile-android.sh` on Linux/Windows.

