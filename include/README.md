# ArxOS Mobile FFI Headers

This directory contains C header files for ArxOS mobile FFI (Foreign Function Interface) integration.

## Purpose

The C header files in this directory define the public API for calling ArxOS Rust functions from iOS (Swift) and Android (Kotlin) applications.

## Files

- **`arxos_mobile.h`** - C FFI bindings for mobile integration
  - Defines function signatures for room/equipment operations
  - Provides AR scan processing functions
  - Includes memory management functions (`arxos_free_string`)

## Build Integration

These headers are automatically copied to the iOS XCFramework during the build process:

```bash
# When building for iOS
scripts/build-mobile-ios.sh
# → Copies include/arxos_mobile.h to ios/build/ArxOS.xcframework/Headers/
```

## Usage

**For iOS:**
- Headers are included in the XCFramework bundle
- Swift wrappers in `ios/ArxOSMobile/Services/ArxOSCoreFFI.swift` use these functions

**For Android:**
- JNI bindings in `src/mobile_ffi/jni.rs` implement these same functions
- Kotlin wrappers in `android/app/src/main/java/com/arxos/mobile/` use the JNI functions

## Memory Management

⚠️ **Important:** All strings returned from FFI functions must be freed using `arxos_free_string()` to prevent memory leaks.

## See Also

- [Mobile FFI Integration Documentation](../docs/MOBILE_FFI_INTEGRATION.md)
- [iOS FFI Status](../docs/IOS_FFI_STATUS.md)
- [FFI Source Code](../src/mobile_ffi/)

