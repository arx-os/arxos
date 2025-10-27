# ArxOS Mobile Implementation Guide

## Overview

This document outlines the complete implementation of ArxOS mobile applications using UniFFI for type-safe cross-platform communication between Rust core and native mobile UIs.

## Architecture

### Core Components

1. **Rust Core**: High-performance building data processing (main crate)
2. **Mobile FFI Bindings**: UniFFI-based bindings from `src/mobile_ffi/`
3. **iOS App**: Native SwiftUI interface with ARKit integration
4. **Android App**: Native Jetpack Compose interface with ARCore integration

### Technology Stack

- **Rust**: Core business logic and data processing
- **UniFFI**: Type-safe FFI bindings generation
- **SwiftUI**: iOS native UI framework
- **Jetpack Compose**: Android native UI framework
- **ARKit/ARCore**: Augmented Reality capabilities
- **Git**: Version control and data synchronization

## Build System

### Prerequisites

1. **Rust Toolchain**: Latest stable version
2. **iOS Development**: Xcode 15+ with iOS 15+ SDK
3. **Android Development**: Android Studio with NDK
4. **UniFFI**: `cargo install uniffi-bindgen`

### Build Scripts

#### macOS/Linux
```bash
# Build for iOS
./scripts/build-mobile.sh ios

# Build for Android  
./scripts/build-mobile.sh android

# Build for both platforms
./scripts/build-mobile.sh all

# Generate UniFFI bindings
./scripts/build-mobile.sh bindings

# Clean build artifacts
./scripts/build-mobile.sh clean
```

#### Windows
```cmd
# Build for iOS
scripts\build-mobile.bat ios

# Build for Android
scripts\build-mobile.bat android

# Build for both platforms
scripts\build-mobile.bat all

# Generate UniFFI bindings
scripts\build-mobile.bat bindings

# Clean build artifacts
scripts\build-mobile.bat clean
```

### Target Architectures

#### iOS
- `aarch64-apple-ios` (iOS devices)
- `aarch64-apple-ios-sim` (iOS simulator ARM)
- `x86_64-apple-ios` (iOS simulator x86_64)

#### Android
- `aarch64-linux-android` (ARM64)
- `armv7-linux-androideabi` (ARMv7)
- `i686-linux-android` (x86)
- `x86_64-linux-android` (x86_64)

## UniFFI Configuration

### Cargo.toml Features

```toml
[features]
default = []
core-only = []
ios = []
android = []

[dependencies]
uniffi = { workspace = true }
uniffi_build = { workspace = true }

[build-dependencies]
uniffi_build = { workspace = true }
```

### UniFFI Configuration (`uniffi.toml`)

```toml
[uniffi]
library_name = "arxos_mobile"

[uniffi.bindings]
kotlin = { package_name = "com.arxos.mobile" }
swift = { module_name = "ArxOSMobile" }

[uniffi.build]
library_name = "arxos_mobile"

[uniffi.metadata]
description = "ArxOS Mobile - Git for Buildings"
version = "0.1.0"
authors = ["Joel <joel@arxos.io>"]
license = "MIT"
repository = "https://github.com/arx-os/arxos"
```

## Mobile App Integration

### iOS Integration

#### Package.swift
```swift
let package = Package(
    name: "ArxOSMobile",
    platforms: [.iOS(.v15)],
    products: [
        .library(name: "ArxOSMobile", targets: ["ArxOSMobile"])
    ],
    dependencies: [
        // Rust library will be linked directly
    ],
    targets: [
        .target(
            name: "ArxOSMobile",
            dependencies: ["ArxOSMobileFFI"],
            path: "ArxOSMobile"
        ),
        .binaryTarget(
            name: "ArxOSMobileFFI",
            path: "../target/aarch64-apple-ios/release/libarxos.a"
        )
    ]
)
```

#### Core Service Integration
```swift
class ArxOSCore: ObservableObject {
    private var instance: ArxOSMobile?
    
    init() {
        do {
            instance = try ArxOSMobile()
        } catch {
            print("Failed to initialize ArxOS core: \(error)")
        }
    }
    
    func executeCommand(_ command: String) async throws -> CommandResult {
        guard let instance = instance else {
            throw TerminalError.coreError("ArxOS instance not initialized")
        }
        
        return try instance.executeCommand(command: command)
    }
}
```

### Android Integration

#### build.gradle Configuration
```gradle
android {
    defaultConfig {
        ndk {
            abiFilters 'arm64-v8a', 'armeabi-v7a', 'x86', 'x86_64'
        }
    }
    
    sourceSets {
        main {
            jniLibs.srcDirs = ['../target/aarch64-linux-android/release']
        }
    }
}
```

#### Core Service Integration
```kotlin
class ArxOSCoreService(private val context: Context) {
    private var instance: ArxOSMobile? = null
    
    init {
        try {
            instance = ArxOSMobile()
        } catch (e: Exception) {
            Log.e("ArxOSCoreService", "Failed to initialize ArxOS core: ${e.message}")
        }
    }
    
    suspend fun executeCommand(command: String): CommandResult = withContext(Dispatchers.IO) {
        try {
            instance?.executeCommand(command) ?: throw Exception("ArxOS instance not initialized")
        } catch (e: Exception) {
            CommandResult(success = false, output = "", error = e.message, executionTimeMs = 0)
        }
    }
}
```

## Data Models

### Core Data Structures

#### MobileEquipment
```rust
#[derive(Debug, Clone, Serialize, Deserialize, uniffi::Record)]
pub struct MobileEquipment {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub location: String,
    pub room_id: String,
    pub position: Option<MobilePosition>,
    pub last_maintenance: String,
}
```

#### MobileRoom
```rust
#[derive(Debug, Clone, Serialize, Deserialize, uniffi::Record)]
pub struct MobileRoom {
    pub id: String,
    pub name: String,
    pub floor: i32,
    pub wing: Option<String>,
    pub room_type: String,
    pub equipment_count: i32,
}
```

#### MobilePosition
```rust
#[derive(Debug, Clone, Serialize, Deserialize, uniffi::Record)]
pub struct MobilePosition {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub coordinate_system: String,
    pub accuracy: f64,
}
```

## API Reference

### Core Functions

#### ArxOSMobile Instance Management
- `new() -> MobileResult<Self>`: Create new instance
- `new_with_path(path: String) -> MobileResult<Self>`: Create instance with specific path

#### Room Operations
- `create_room(name: String, floor: i32, wing: Option<String>) -> MobileResult<MobileRoom>`
- `get_rooms() -> MobileResult<Vec<MobileRoom>>`
- `get_room(room_id: String) -> MobileResult<MobileRoom>`

#### Equipment Operations
- `add_equipment(name: String, equipment_type: String, room_id: String, position: Option<MobilePosition>) -> MobileResult<MobileEquipment>`
- `get_equipment() -> MobileResult<Vec<MobileEquipment>>`
- `get_equipment_by_room(room_id: String) -> MobileResult<Vec<MobileEquipment>>`
- `update_equipment_status(equipment_id: String, status: String) -> MobileResult<()>`

#### Git Operations
- `get_git_status() -> MobileResult<GitStatus>`
- `sync_git() -> MobileResult<()>`
- `get_git_history(limit: i32) -> MobileResult<Vec<String>>`
- `get_git_diff() -> MobileResult<String>`

#### Command Execution
- `execute_command(command: String) -> MobileResult<CommandResult>`

#### AR Processing
- `process_ar_scan(scan_data: Vec<u8>, room_name: String) -> MobileResult<ARScanResult>`

## Error Handling

### MobileError Types
```rust
#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum MobileError {
    #[error("Core error: {message}")]
    CoreError { message: String },
    #[error("AR processing error: {message}")]
    ARProcessingError { message: String },
    #[error("Git operation error: {message}")]
    GitError { message: String },
    #[error("Invalid input: {message}")]
    InvalidInput { message: String },
}
```

### Error Handling Patterns

#### Swift
```swift
do {
    let result = try instance.executeCommand(command: "status")
    // Handle success
} catch let error as MobileError {
    switch error {
    case .coreError(let message):
        // Handle core error
    case .arProcessingError(let message):
        // Handle AR error
    case .gitError(let message):
        // Handle Git error
    case .invalidInput(let message):
        // Handle input error
    }
} catch {
    // Handle unexpected error
}
```

#### Kotlin
```kotlin
try {
    val result = instance.executeCommand("status")
    // Handle success
} catch (e: MobileError) {
    when (e) {
        is MobileError.CoreError -> {
            // Handle core error
        }
        is MobileError.ARProcessingError -> {
            // Handle AR error
        }
        is MobileError.GitError -> {
            // Handle Git error
        }
        is MobileError.InvalidInput -> {
            // Handle input error
        }
    }
} catch (e: Exception) {
    // Handle unexpected error
}
```

## AR Integration

### ARKit Integration (iOS)

#### ARScanView
```swift
struct ARScanView: View {
    @StateObject private var arxosCore = ArxOSCore()
    @State private var isScanning = false
    @State private var detectedEquipment: [DetectedEquipment] = []
    
    var body: some View {
        VStack {
            ARViewContainer(
                isScanning: $isScanning,
                onEquipmentDetected: { equipment in
                    detectedEquipment = equipment
                }
            )
            
            if !detectedEquipment.isEmpty {
                EquipmentListView(equipment: detectedEquipment)
            }
        }
    }
}
```

### ARCore Integration (Android)

#### AR Activity
```kotlin
class ARActivity : AppCompatActivity() {
    private lateinit var arxosCore: ArxOSCoreService
    private lateinit var arCoreSession: Session
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        arxosCore = ArxOSCoreService(this)
        
        // Initialize ARCore
        arCoreSession = Session(this)
        
        // Set up AR processing
        setupARProcessing()
    }
    
    private fun setupARProcessing() {
        // AR processing logic
    }
}
```

## Testing

### Unit Tests

#### Rust Core Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_create_room() {
        let mobile = ArxOSMobile::new().unwrap();
        let room = mobile.create_room("Test Room".to_string(), 1, None).unwrap();
        assert_eq!(room.name, "Test Room");
        assert_eq!(room.floor, 1);
    }
}
```

#### iOS Tests
```swift
import XCTest
@testable import ArxOSMobile

class ArxOSCoreTests: XCTestCase {
    func testExecuteCommand() async throws {
        let core = ArxOSCore()
        let result = try await core.executeCommand("help")
        XCTAssertTrue(result.success)
        XCTAssertFalse(result.output.isEmpty)
    }
}
```

#### Android Tests
```kotlin
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ArxOSCoreServiceTest {
    @Test
    fun testExecuteCommand() = runTest {
        val service = ArxOSCoreService(context)
        val result = service.executeCommand("help")
        assertTrue(result.success)
        assertFalse(result.output.isEmpty())
    }
}
```

### Integration Tests

#### End-to-End Testing
1. **Build Verification**: Ensure all targets compile successfully
2. **FFI Testing**: Verify UniFFI bindings work correctly
3. **AR Testing**: Test AR functionality on physical devices
4. **Git Integration**: Test offline Git operations
5. **Performance Testing**: Measure execution times and memory usage

## Deployment

### iOS App Store

1. **Build Release**: Use `cargo build --release --target aarch64-apple-ios`
2. **Archive**: Create Xcode archive with embedded library
3. **TestFlight**: Deploy to TestFlight for beta testing
4. **App Store**: Submit for App Store review

### Google Play Store

1. **Build Release**: Use `cargo build --release --target aarch64-linux-android`
2. **AAB Creation**: Generate Android App Bundle
3. **Internal Testing**: Deploy to internal testing track
4. **Play Store**: Submit for Play Store review

## Performance Considerations

### Memory Management
- Use `Arc<T>` for shared ownership in Rust
- Implement proper cleanup in mobile apps
- Monitor memory usage during AR processing

### Threading
- Keep UI operations on main thread
- Use background threads for heavy computations
- Implement proper async/await patterns

### Battery Optimization
- Minimize AR processing frequency
- Implement efficient Git operations
- Use appropriate power management APIs

## Troubleshooting

### Common Issues

#### Build Failures
- **Missing Targets**: Run `rustup target add <target>`
- **UniFFI Issues**: Ensure `uniffi-bindgen` is installed
- **Linking Errors**: Check library paths and architectures

#### Runtime Errors
- **FFI Errors**: Verify UniFFI bindings are up to date
- **AR Issues**: Check device compatibility and permissions
- **Git Errors**: Ensure proper repository initialization

#### Performance Issues
- **Memory Leaks**: Use proper cleanup patterns
- **Slow AR**: Optimize processing algorithms
- **UI Lag**: Move heavy operations to background threads

### Debug Tools

#### Rust Debugging
```bash
# Enable debug logging
RUST_LOG=debug cargo run

# Profile with perf
perf record cargo run
perf report
```

#### iOS Debugging
- Use Xcode Instruments for profiling
- Enable Metal validation for AR debugging
- Use Console.app for log monitoring

#### Android Debugging
- Use Android Studio Profiler
- Enable GPU debugging for AR
- Use logcat for runtime monitoring

## Future Enhancements

### Planned Features
1. **Real-time Collaboration**: Multi-user AR sessions
2. **Cloud Sync**: Enhanced cloud synchronization
3. **AI Integration**: Machine learning for equipment recognition
4. **IoT Integration**: Real-time equipment monitoring
5. **Advanced AR**: LiDAR integration and 3D reconstruction

### Performance Improvements
1. **Native AR Processing**: Move AR algorithms to Rust
2. **Caching**: Implement intelligent data caching
3. **Compression**: Optimize data transfer and storage
4. **Parallel Processing**: Multi-threaded operations

## Conclusion

The ArxOS mobile implementation provides a robust, type-safe foundation for building management applications with AR capabilities. The UniFFI-based architecture ensures maintainable code while providing excellent performance and cross-platform compatibility.

For questions or contributions, please refer to the main ArxOS documentation or contact the development team.
