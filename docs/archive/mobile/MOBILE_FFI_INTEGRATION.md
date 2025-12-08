# ArxOS Mobile FFI Integration Guide _(Archived)_

> **Status (November 2025):** Native mobile bindings are paused. Use this document only when working with the archived clients (`mobile-apps-final`). For the active roadmap, see `WEB_PWA_PLAN.md` and the WASM helpers under `ar_integration::wasm`.

**Version:** 1.0  
**Date:** December 2024  
**Status:** Phase 2.1-2.3 Complete

---

## Overview

ArxOS mobile FFI integration enables native mobile applications (iOS/Android) to call Rust functions directly. This guide covers the complete integration process.

---

## Architecture

```
┌─────────────────────────────────┐
│   iOS/Android Application      │
│   (Swift/Kotlin)               │
└────────────┬───────────────────┘
             │
┌────────────▼───────────────────┐
│   Platform Wrapper              │
│   Swift/Kotlin FFI Bridge       │
└────────────┬───────────────────┘
             │
┌────────────▼───────────────────┐
│   C FFI Layer (extern "C")     │
│   arxos_* functions             │
└────────────┬───────────────────┘
             │
┌────────────▼───────────────────┐
│   Rust Core (arxos library)     │
│   Business Logic                │
└─────────────────────────────────┘
```

---

## Phase 2.1: Core C FFI Exports ✅

### Implementation

**File:** `crates/arxos/crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs`

```rust
#[no_mangle]
pub unsafe extern "C" fn arxos_list_rooms(building_name: *const c_char) -> *mut c_char {
    // Implementation
}
```

### Functions Available

1. **`arxos_list_rooms(building_name)`** - List all rooms in a building
2. **`arxos_get_room(building_name, room_id)`** - Get a specific room
3. **`arxos_list_equipment(building_name)`** - List all equipment
4. **`arxos_get_equipment(building_name, equipment_id)`** - Get specific equipment
5. **`arxos_parse_ar_scan(json_data)`** - Parse AR scan JSON
6. **`arxos_extract_equipment(json_data)`** - Extract equipment from AR scan
7. **`arxos_free_string(ptr)`** - Free allocated strings

### Header File

**File:** `include/arxos_mobile.h`

```c
char* arxos_list_rooms(const char* building_name);
char* arxos_get_room(const char* building_name, const char* room_id);
// ... etc
```

---

## Phase 2.2: iOS Integration ✅

### Files Created

1. **`ios/ArxOSMobile/include/arxos_bridge.h`** - Bridge header for Swift
2. **`ios/ArxOSMobile/ArxOSMobile/Services/ArxOSCoreFFI.swift`** - Swift wrapper

### Swift Wrapper

```swift
class ArxOSCoreFFI {
    func listRooms(buildingName: String, completion: @escaping (Result<[Room], Error>) -> Void) {
        // Calls arxos_list_rooms() via FFI
    }
}
```

### Build Steps

1. **Build Rust library:**
   ```bash
   cargo build -p arxos --target aarch64-apple-ios --release
   cargo build -p arxos --target x86_64-apple-ios --release
   ```

2. **Create universal framework:**
   ```bash
   # Combine arm64 and x86_64 into universal binary
   lipo -create target/aarch64-apple-ios/release/libarxos.a \
                target/x86_64-apple-ios/release/libarxos.a \
                -output libarxos_universal.a
   ```

3. **Link in Xcode:**
   - Add `libarxos_universal.a` to "Frameworks, Libraries, and Embedded Content"
   - Add header search path: `$(PROJECT_DIR)/../../include`
   - Add bridging header: `ios/ArxOSMobile/include/arxos_bridge.h`

4. **Update Swift code:**
   - Import FFI functions
   - Remove mock mode
   - Test functionality

---

## Phase 2.3: Android JNI Integration ✅

### Files Created

1. **`android/app/src/main/java/com/arxos/mobile/service/ArxOSCoreJNI.kt`** - JNI wrapper

### JNI Functions

```kotlin
class ArxOSCoreJNI {
    external fun nativeListRooms(buildingName: String): String
    external fun nativeGetRoom(buildingName: String, roomId: String): String
    // ... etc
}
```

### Build Steps

1. **Install Android NDK:**
   ```bash
   # Download from https://developer.android.com/ndk
   export ANDROID_NDK_HOME=/path/to/android-ndk-rXX
   ```

2. **Build for Android architectures:**
   ```bash
   cargo build -p arxos --target aarch64-linux-android --release
   cargo build -p arxos --target armv7-linux-androideabi --release
   cargo build -p arxos --target i686-linux-android --release
   cargo build -p arxos --target x86_64-linux-android --release
   ```

3. **Create JNI libraries:**
   ```bash
   mkdir -p android/app/src/main/jniLibs/{arm64-v8a,armeabi-v7a,x86,x86_64}
   
   cp target/aarch64-linux-android/release/libarxos.so \
      android/app/src/main/jniLibs/arm64-v8a/
   
   cp target/armv7-linux-androideabi/release/libarxos.so \
      android/app/src/main/jniLibs/armeabi-v7a/
   # ... etc
   ```

4. **Update build.gradle:**
   ```gradle
   android {
       ndkVersion "XX.X.X"
       
       sourceSets {
           main {
               jniLibs.srcDirs = ['src/main/jniLibs']
           }
       }
   }
   ```

5. **Create JNI bindings in Rust:**
   ```rust
   // crates/arxos/crates/arxos/crates/arxos/src/mobile_ffi/jni.rs
   #![allow(non_snake_case)]
   
   #[no_mangle]
   pub extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeListRooms(
       env: *mut JNIEnv,
       _class: JClass,
       building_name: JString
   ) -> jstring {
       // Implementation
   }
   ```

---

## Phase 2.4: Build Integration (Next)

### Automated Build Scripts

**File:** `scripts/build-mobile-all.sh`

```bash
#!/bin/bash
# Build ArxOS for both iOS and Android

echo "🚀 Building ArxOS for all mobile platforms..."

# iOS builds
bash scripts/build-mobile-ios.sh

# Android builds
bash scripts/build-mobile-android.sh

echo "✅ All mobile builds complete!"
```

### CI/CD Integration

Add to `.github/workflows/mobile-build.yml`:

```yaml
name: Mobile Build

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - run: bash scripts/build-mobile-ios.sh
  
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
      - run: bash scripts/build-mobile-android.sh
```

---

## Testing

### iOS Testing

```swift
let ffi = ArxOSCoreFFI()
ffi.listRooms(buildingName: "Main Building") { result in
    switch result {
    case .success(let rooms):
        print("Found \(rooms.count) rooms")
    case .failure(let error):
        print("Error: \(error)")
    }
}
```

### Android Testing

```kotlin
val jniWrapper = ArxOSCoreJNIWrapper(ArxOSCoreJNI(context))
CoroutineScope(Dispatchers.IO).launch {
    val rooms = jniWrapper.listRooms("Main Building")
    Log.d("ArxOS", "Found ${rooms.size} rooms")
}
```

---

## Memory Management

### Important Notes

1. **Ownership:** Strings returned from FFI must be freed by caller
2. **Thread Safety:** FFI functions are thread-safe
3. **Error Handling:** All errors returned as JSON with error field
4. **Null Safety:** All pointer inputs validated for null

### Example Usage

```swift
// Swift
let cString = arxos_list_rooms(buildingName)
let jsonString = String(cString: cString!)
arxos_free_string(cString!) // Must free after use
```

```kotlin
// Kotlin
val json = nativeListRooms(buildingName)
val rooms = JSON.parseArray<Room>(json)
nativeFreeString(ptr) // Must free
```

---

## Troubleshooting

### Common Issues

#### iOS: "Undefined symbols"
**Solution:** Ensure library is linked in Xcode project settings

#### Android: "UnsatisfiedLinkError"
**Solution:** Check NDK version and library paths in build.gradle

#### Both: "Segmentation fault"
**Solution:** Check memory management, ensure all strings are freed

---

## Status

**Phase 2.1:** ✅ Complete - Core C FFI exports  
**Phase 2.2:** ✅ Complete - iOS Swift wrapper  
**Phase 2.3:** ✅ Complete - Android JNI wrapper  
**Phase 2.4:** 🚧 In Progress - Build automation

---

**Next:** Complete build automation and finalize mobile integration

