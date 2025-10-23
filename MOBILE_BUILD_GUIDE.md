# ArxOS Mobile Build Guide

## Overview

ArxOS Mobile provides cross-platform mobile applications for iOS and Android using UniFFI for Rust-to-native language bindings.

## Architecture

- **Rust Core**: `arxos-mobile` crate with UniFFI bindings
- **iOS**: SwiftUI app with Swift bindings
- **Android**: Jetpack Compose app with Kotlin bindings
- **FFI**: UniFFI generates native language bindings automatically

## Prerequisites

### For iOS Development (macOS only)
```bash
# Install Xcode from App Store
# Install iOS targets
rustup target add aarch64-apple-ios x86_64-apple-ios

# Set up iOS development environment
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
```

### For Android Development (Cross-platform)
```bash
# Install Android Studio
# Install Android NDK
# Install Android targets
rustup target add aarch64-linux-android armv7-linux-androideabi x86_64-linux-android i686-linux-android

# Set up Android development environment
export ANDROID_HOME=/path/to/android/sdk
export NDK_HOME=$ANDROID_HOME/ndk/25.1.8937393
```

## Building the Mobile Crate

### Windows (Development)
```bash
# Build for Windows development
cargo build -p arxos-mobile --no-default-features --features core-only
```

### iOS (macOS only)
```bash
# Build for iOS device
cargo build -p arxos-mobile --no-default-features --features core-only --target aarch64-apple-ios --release

# Build for iOS simulator
cargo build -p arxos-mobile --no-default-features --features core-only --target x86_64-apple-ios --release
```

### Android (Cross-platform)
```bash
# Build for Android ARM64
cargo build -p arxos-mobile --no-default-features --features core-only --target aarch64-linux-android --release

# Build for Android x86_64
cargo build -p arxos-mobile --no-default-features --features core-only --target x86_64-linux-android --release
```

## Mobile API Reference

### Core Functions

#### `hello_world() -> String`
Basic connectivity test function.

#### `create_room(name: String, floor: i32, wing: String) -> MobileRoom`
Creates a new room in the building.

#### `get_rooms() -> Vec<MobileRoom>`
Returns a list of all rooms in the building.

#### `add_equipment(name: String, equipment_type: String, room_id: String) -> MobileEquipment`
Adds equipment to a specific room.

#### `get_equipment() -> Vec<MobileEquipment>`
Returns a list of all equipment in the building.

#### `get_git_status() -> GitStatus`
Returns the current Git repository status.

#### `execute_command(command: String) -> CommandResult`
Executes CLI commands and returns results.

### Data Structures

#### `MobileRoom`
```rust
pub struct MobileRoom {
    pub id: String,
    pub name: String,
    pub floor: i32,
    pub wing: String,
    pub room_type: String,
}
```

#### `MobileEquipment`
```rust
pub struct MobileEquipment {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub location: String,
    pub room_id: String,
}
```

#### `GitStatus`
```rust
pub struct GitStatus {
    pub branch: String,
    pub commit_count: i32,
    pub last_commit: String,
    pub has_changes: bool,
}
```

#### `CommandResult`
```rust
pub struct CommandResult {
    pub success: bool,
    pub output: String,
    pub error: String,
}
```

## Integration with Native Apps

### iOS Integration

1. **Build the Rust library**:
   ```bash
   cargo build -p arxos-mobile --target aarch64-apple-ios --release
   ```

2. **Generate Swift bindings**:
   ```bash
   uniffi-bindgen generate src/arxos_mobile.udl --language swift --out-dir mobile-ios/
   ```

3. **Add to Xcode project**:
   - Add the generated Swift files to your Xcode project
   - Link the compiled Rust library
   - Import and use the generated Swift classes

### Android Integration

1. **Build the Rust library**:
   ```bash
   cargo build -p arxos-mobile --target aarch64-linux-android --release
   ```

2. **Generate Kotlin bindings**:
   ```bash
   uniffi-bindgen generate src/arxos_mobile.udl --language kotlin --out-dir mobile-android/
   ```

3. **Add to Android project**:
   - Add the generated Kotlin files to your Android project
   - Link the compiled Rust library
   - Import and use the generated Kotlin classes

## Troubleshooting

### Common Issues

#### "linker `cc` not found" (Android)
- Install Android NDK
- Set `NDK_HOME` environment variable
- Ensure NDK is in your PATH

#### "xcrun not found" (iOS)
- Install Xcode from App Store
- Set `DEVELOPER_DIR` environment variable
- Ensure Xcode command line tools are installed

#### "target_os cfg conflicts"
- Fixed in build script - no manual cfg setting
- Use `TARGET` environment variable for platform detection

### Build Script

The `build.rs` script handles platform-specific linking:

```rust
fn main() {
    uniffi_build::generate_scaffolding("src/arxos_mobile.udl").unwrap();
    
    let target = std::env::var("TARGET").unwrap();
    
    if target.contains("ios") {
        println!("cargo:rustc-link-lib=framework=Foundation");
        println!("cargo:rustc-link-lib=framework=Security");
        println!("cargo:rustc-link-lib=framework=SystemConfiguration");
    } else if target.contains("android") {
        println!("cargo:rustc-link-lib=log");
        println!("cargo:rustc-link-lib=android");
    }
}
```

## Development Workflow

1. **Develop on Windows**: Use Windows build for rapid development
2. **Test on macOS**: Build for iOS when testing iOS features
3. **Test on Linux/Windows**: Build for Android when testing Android features
4. **Deploy**: Use CI/CD for automated cross-platform builds

## Next Steps

- [ ] Set up iOS development environment on macOS
- [ ] Set up Android development environment
- [ ] Create sample mobile applications
- [ ] Implement AR scanning features
- [ ] Add real-time equipment monitoring
- [ ] Integrate with building management systems
