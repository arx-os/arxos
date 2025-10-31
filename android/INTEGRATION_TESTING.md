# Android JNI Integration Testing Guide

**Last Updated:** January 2025  
**Status:** Ready for Integration Testing

---

## Overview

This document describes how to test the Android JNI integration for ArxOS. The integration includes:
- 6 JNI functions for room and equipment operations
- JSON serialization/deserialization
- Error handling and memory management
- Kotlin wrapper layer

---

## Test Structure

### 1. Unit Tests (`src/test/java/`)
**Location:** `android/app/src/test/java/com/arxos/mobile/service/ArxOSCoreJNIWrapperTest.kt`

**Purpose:** Test JSON parsing and error handling without requiring native library

**What's Tested:**
- JSON parsing from Rust responses
- Error JSON handling
- Empty response handling
- Invalid JSON handling
- Library loading state checks

**Run:**
```bash
cd android
./gradlew test
```

### 2. Integration Tests (`src/androidTest/java/`)
**Location:** `android/app/src/androidTest/java/com/arxos/mobile/integration/JNIIntegrationTest.kt`

**Purpose:** Test actual JNI calls with native library loaded

**What's Tested:**
- Native library loading
- All 6 JNI functions
- Error handling with real native code
- Memory safety (repeated calls)
- Real-world scenarios

**Run:**
```bash
cd android
./gradlew connectedAndroidTest
```

---

## Prerequisites

### Building Native Library

1. **Build Rust library for Android:**
```bash
# From project root
cd android

# Build for all ABIs (or specific one)
cargo ndk -t arm64-v8a -t armeabi-v7a -t x86 -t x86_64 build --release

# Copy libraries to Android project
# (Adjust paths based on your cargo-ndk output)
cp target/arm64-v8a/release/libarxos.so app/src/main/jniLibs/arm64-v8a/
cp target/armeabi-v7a/release/libarxos.so app/src/main/jniLibs/armeabi-v7a/
cp target/x86_64/release/libarxos.so app/src/main/jniLibs/x86_64/
cp target/x86/release/libarxos.so app/src/main/jniLibs/x86/
```

2. **Verify library exists:**
```bash
ls -la android/app/src/main/jniLibs/*/libarxos.so
```

### Android Setup

1. **Android Studio / SDK:**
   - Android SDK installed
   - Build tools version 34.0.0 or later
   - Minimum SDK: 24 (Android 7.0)
   - Target SDK: 34 (Android 14)

2. **Device/Emulator:**
   - Physical device connected via USB, OR
   - Android emulator running
   - Device must match one of the built ABIs

---

## Running Tests

### Unit Tests (No Device Required)

```bash
cd android
./gradlew test --tests "*ArxOSCoreJNIWrapperTest"
```

**Expected Output:**
```
> Task :app:testDebugUnitTest
ArxOSCoreJNIWrapperTest > test listRooms with valid JSON PASSED
ArxOSCoreJNIWrapperTest > test listRooms with error JSON PASSED
...
BUILD SUCCESSFUL
```

### Integration Tests (Device/Emulator Required)

1. **Connect device or start emulator:**
```bash
adb devices
```

2. **Run integration tests:**
```bash
cd android
./gradlew connectedAndroidTest
```

**Expected Output:**
```
> Task :app:connectedAndroidTest
JNIIntegrationTest > testNativeLibraryLoads PASSED
JNIIntegrationTest > testListRoomsIntegration PASSED
...
BUILD SUCCESSFUL
```

---

## Test Scenarios

### 1. Library Loading
- ✅ Verify native library loads successfully
- ✅ Graceful handling when library not available
- ✅ Error logging when load fails

### 2. Room Operations
- ✅ `listRooms()` - Returns list of rooms
- ✅ `getRoom()` - Returns single room or null
- ✅ Error handling for non-existent building
- ✅ Empty response handling

### 3. Equipment Operations
- ✅ `listEquipment()` - Returns list of equipment
- ✅ `getEquipment()` - Returns single equipment or null
- ✅ Error handling for non-existent equipment
- ✅ Status and properties parsing

### 4. AR Scan Operations
- ✅ `parseARScan()` - Parses AR scan JSON
- ✅ `extractEquipment()` - Extracts equipment from scan
- ✅ Handles empty scans
- ✅ Handles invalid JSON

### 5. Error Handling
- ✅ JSON error responses parsed correctly
- ✅ Empty strings handled gracefully
- ✅ Invalid JSON doesn't crash
- ✅ Library not loaded returns safe defaults

### 6. Memory Safety
- ✅ Repeated calls don't leak memory
- ✅ String conversions are safe
- ✅ No native crashes on invalid input

---

## Manual Testing Checklist

When testing on a real device, verify:

### Basic Functionality
- [ ] App launches without crashes
- [ ] Native library loads (check logcat for "Native library loaded successfully")
- [ ] Rooms screen loads (may be empty if no building data)
- [ ] Equipment screen loads (may be empty)

### Error Scenarios
- [ ] App handles missing native library gracefully
- [ ] Invalid building names don't crash
- [ ] Invalid room/equipment IDs handled
- [ ] Network/IO errors logged appropriately

### Performance
- [ ] Room listing is responsive (< 1 second for typical building)
- [ ] Equipment listing is responsive
- [ ] No memory leaks after extended use
- [ ] No ANRs (Application Not Responding)

### AR Features
- [ ] AR scan initiates
- [ ] AR scan data sent to JNI
- [ ] Equipment extraction works
- [ ] Parsed equipment appears in UI

---

## Troubleshooting

### Native Library Not Loading

**Symptoms:**
```
W/ArxOSCoreJNI: Native library not found - will work in simulation mode
```

**Solutions:**
1. Verify library exists:
```bash
ls -la app/src/main/jniLibs/*/libarxos.so
```

2. Check ABI matches device:
```bash
adb shell getprop ro.product.cpu.abi
# Should match one of: arm64-v8a, armeabi-v7a, x86, x86_64
```

3. Verify library name in `build.gradle`:
```gradle
System.loadLibrary("arxos")  // Should match libarxos.so
```

### JSON Parse Errors

**Symptoms:**
- Empty lists/objects when data should exist
- Logcat shows "Failed to parse" errors

**Solutions:**
1. Check Rust JSON serialization matches Kotlin expectations
2. Verify field names match (Rust uses snake_case, Kotlin expects JSON keys)
3. Add logging to see actual JSON response:
```kotlin
Log.d(TAG, "JSON response: $json")
```

### Memory Issues

**Symptoms:**
- App crashes after multiple operations
- OutOfMemoryErrors

**Solutions:**
1. Verify JNI string handling is correct
2. Check for memory leaks in Rust code
3. Use Android Profiler to identify leaks

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Android JNI Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: |
          cd android
          ./gradlew test

  integration-tests:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Android SDK
        uses: android-actions/setup-android@v2
      - name: Build native library
        run: |
          cargo ndk -t arm64-v8a build --release
      - name: Copy libraries
        run: |
          # Copy built libraries
      - name: Start emulator
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 29
      - name: Run integration tests
        run: |
          cd android
          ./gradlew connectedAndroidTest
```

---

## Next Steps

1. **Add Real Data Tests:**
   - Create test building data
   - Verify end-to-end workflows
   - Test with actual AR scan data

2. **Performance Testing:**
   - Benchmark JNI call latency
   - Test with large datasets
   - Profile memory usage

3. **Edge Case Testing:**
   - Very long strings
   - Special characters in names
   - Large JSON responses
   - Concurrent calls

---

## Resources

- [JNI Documentation](https://docs.oracle.com/javase/8/docs/technotes/guides/jni/)
- [Android NDK Guide](https://developer.android.com/ndk)
- [Rust JNI Crate](https://docs.rs/jni/)
- [Android Testing Guide](https://developer.android.com/training/testing)

---

**For questions or issues, refer to:**
- `android/BUILD_GUIDE.md` - Building native libraries
- `TECHNICAL_DEBT_REMEDIATION_SUMMARY.md` - Implementation details

