# Android AR Integration Testing Plan

**Last Updated:** January 2025  
**Status:** Ready for Implementation

---

## Overview

This document outlines a comprehensive testing strategy for the Android AR integration features implemented in Phases 1-5. The testing plan covers unit tests, integration tests, and end-to-end workflow tests to ensure robust functionality.

---

## Test Structure

### 1. Unit Tests (`app/src/test/java/`)

**Purpose:** Test individual components in isolation without requiring native library or Android runtime

#### 1.1 Service Layer Tests

**File:** `app/src/test/java/com/arxos/mobile/service/ArxOSCoreJNIWrapperARTest.kt`

**What to Test:**
- JSON parsing for AR model load results
- JSON parsing for AR scan save results
- JSON parsing for pending equipment list results
- JSON parsing for confirm/reject results
- Error JSON handling
- Empty response handling
- Invalid JSON handling
- Null safety checks

**Test Cases:**
```kotlin
// AR Model Loading
- testLoadARModelSuccessParsing()
- testLoadARModelErrorParsing()
- testLoadARModelEmptyResponse()
- testLoadARModelInvalidJSON()

// AR Scan Saving
- testSaveARScanSuccessParsing()
- testSaveARScanPendingIdsParsing()
- testSaveARScanErrorParsing()
- testSaveARScanInvalidJSON()

// Pending Equipment
- testListPendingEquipmentSuccessParsing()
- testListPendingEquipmentEmptyList()
- testListPendingEquipmentItemParsing()
- testConfirmPendingEquipmentSuccessParsing()
- testConfirmPendingEquipmentCommitIdParsing()
- testRejectPendingEquipmentSuccessParsing()

// Error Handling
- testAllFunctionsWithErrorJSON()
- testAllFunctionsWithEmptyResponse()
- testAllFunctionsWithInvalidJSON()
```

#### 1.2 ViewModel Tests

**File:** `app/src/test/java/com/arxos/mobile/ui/viewmodel/ARViewModelTest.kt`

**What to Test:**
- State management for AR scanning
- State management for model loading
- State management for scan saving
- Pending equipment operations
- Error state handling
- Coroutine-based async operations

**Test Cases:**
```kotlin
// AR Scanning State
- testStartScanning()
- testStopScanning()
- testUpdateCurrentRoom()
- testUpdateFloorLevel()
- testUpdateBuildingName()

// Model Loading
- testLoadARModelSuccess()
- testLoadARModelError()
- testClearLoadedModel()
- testLoadARModelLoadingState()

// Scan Saving
- testSaveScanSuccess()
- testSaveScanWithPendingIds()
- testSaveScanError()
- testSaveScanDurationCalculation()
- testSaveScanPreventsMultipleSaves()

// Pending Equipment
- testListPendingEquipment()
- testConfirmPendingEquipment()
- testRejectPendingEquipment()
- testPendingEquipmentStateUpdates()

// Equipment Detection
- testAddDetectedEquipment()
- testAddEquipmentManually()
- testEquipmentDeduplication()
```

**Mocking Strategy:**
- Mock `ArxOSCoreService` using Mockito
- Use `runTest` from `kotlinx.coroutines.test` for coroutines
- Verify state updates via `StateFlow` collection

#### 1.3 Data Model Tests

**File:** `app/src/test/java/com/arxos/mobile/data/ARDataModelsTest.kt`

**What to Test:**
- `ARScanData` serialization to JSON
- `DetectedEquipment` serialization
- `Vector3` handling
- `RoomBoundaries` serialization
- Equipment type mapping
- Position data encoding

**Test Cases:**
```kotlin
- testARScanDataSerialization()
- testARScanDataWithAllMetadata()
- testDetectedEquipmentSerialization()
- testDetectedEquipmentTypeProperty()
- testVector3Conversion()
- testRoomBoundariesSerialization()
- testEquipmentIconMapping()
```

---

### 2. Integration Tests (`app/src/androidTest/java/`)

**Purpose:** Test actual JNI calls with native library loaded and Android runtime

#### 2.1 JNI AR Integration Tests

**File:** `app/src/androidTest/java/com/arxos/mobile/integration/JNIARIntegrationTest.kt`

**What to Test:**
- Native library loading
- All 5 new AR JNI functions
- Real building data interaction
- Error handling with real native code
- Memory safety (repeated calls)
- End-to-end AR workflow

**Test Cases:**
```kotlin
// AR Model Loading
- testNativeLoadARModelWithGLTF()
- testNativeLoadARModelWithUSDZ()
- testNativeLoadARModelWithCustomPath()
- testNativeLoadARModelNonexistentBuilding()
- testNativeLoadARModelInvalidFormat()

// AR Scan Saving
- testNativeSaveARScanWithValidData()
- testNativeSaveARScanWithPendingEquipment()
- testNativeSaveARScanInvalidJSON()
- testNativeSaveARScanNonexistentBuilding()
- testNativeSaveARScanConfidenceThreshold()

// Pending Equipment
- testNativeListPendingEquipmentEmpty()
- testNativeListPendingEquipmentWithItems()
- testNativeListPendingEquipmentNonexistentBuilding()
- testNativeConfirmPendingEquipmentSuccess()
- testNativeConfirmPendingEquipmentWithGitCommit()
- testNativeConfirmPendingEquipmentNonexistent()
- testNativeRejectPendingEquipmentSuccess()
- testNativeRejectPendingEquipmentNonexistent()

// Memory Safety
- testRepeatedARFunctionCalls()
- testConcurrentARFunctionCalls()
- testLargeARScanData()
```

#### 2.2 Service Integration Tests

**File:** `app/src/androidTest/java/com/arxos/mobile/integration/ARServiceIntegrationTest.kt`

**What to Test:**
- Service layer with real JNI
- Complete AR workflow through service
- Error propagation
- State management

**Test Cases:**
```kotlin
- testARServiceLoadModel()
- testARServiceSaveScan()
- testARServiceListPending()
- testARServiceConfirmPending()
- testARServiceRejectPending()
- testARServiceCompleteWorkflow()
```

#### 2.3 Android AR Workflow Integration Tests

**File:** `app/src/androidTest/java/com/arxos/mobile/integration/AndroidARWorkflowTest.kt`

**What to Test:**
- Complete end-to-end Android AR workflow
- Model loading → Scan saving → Pending listing → Confirmation
- Rejection workflow
- Building data persistence
- Git commit integration

**Test Cases:**
```kotlin
- testCompleteAndroidARWorkflow()
  // 1. Create test building
  // 2. Load AR model
  // 3. Save AR scan with equipment
  // 4. List pending equipment
  // 5. Confirm pending equipment
  // 6. Verify equipment added to building
  // 7. Verify Git commit created

- testAndroidARWorkflowWithRejection()
  // 1. Create test building
  // 2. Save AR scan
  // 3. List pending equipment
  // 4. Reject pending equipment
  // 5. Verify equipment NOT added
  // 6. Verify pending item marked as rejected

- testAndroidARWorkflowMultipleScans()
  // Test multiple scans creating multiple pending items
  // Test batch confirmation
  // Test mixed confirm/reject operations
```

---

### 3. UI Component Tests (Optional)

**File:** `app/src/androidTest/java/com/arxos/mobile/ui/components/ARComponentTest.kt`

**Purpose:** Test Compose UI components with Compose testing framework

**What to Test:**
- Equipment placement dialog rendering
- Pending equipment confirmation view rendering
- State updates reflected in UI
- User interactions (button clicks, input changes)

**Test Cases:**
```kotlin
- testEquipmentPlacementDialogDisplay()
- testEquipmentPlacementDialogInput()
- testPendingEquipmentConfirmationViewDisplay()
- testPendingEquipmentConfirmationViewEmptyState()
- testPendingEquipmentRowConfirmButton()
- testPendingEquipmentRowRejectButton()
```

**Note:** UI tests are optional and may require more complex setup. Focus on unit and integration tests first.

---

## Test Data Requirements

### Test Building Data

Create a dedicated test building for Android AR tests:

```yaml
# test_building_android.yaml
building:
  id: "test-building-android"
  name: "Test Building Android"
  # ... minimal building structure
floors:
  - id: "floor-1"
    name: "Floor 1"
    level: 1
    rooms: []
    equipment: []
```

### Test AR Scan Data

Create test AR scan JSON matching Rust FFI structure:

```json
{
  "detectedEquipment": [
    {
      "name": "VAV-301",
      "type": "HVAC",
      "position": {"x": 10.0, "y": 20.0, "z": 3.0},
      "confidence": 0.9,
      "detectionMethod": "ARCore"
    }
  ],
  "roomBoundaries": {
    "walls": [],
    "openings": []
  },
  "deviceType": "Pixel 8 Pro",
  "scanDurationMs": 5000,
  "roomName": "Room 301",
  "floorLevel": 3
}
```

---

## Testing Dependencies

Ensure these dependencies are in `build.gradle`:

```gradle
dependencies {
    // Testing
    testImplementation 'junit:junit:4.13.2'
    testImplementation 'org.mockito:mockito-core:5.7.0'
    testImplementation 'org.mockito:mockito-inline:5.2.0'
    testImplementation 'org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3'
    testImplementation 'androidx.arch.core:core-testing:2.2.0'
    
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
    androidTestImplementation 'androidx.test:runner:1.5.2'
    androidTestImplementation 'androidx.test:rules:1.5.0'
    androidTestImplementation platform('androidx.compose:compose-bom:2023.10.01')
    androidTestImplementation 'androidx.compose.ui:ui-test-junit4'
}
```

---

## Running Tests

### Unit Tests (No Device Required)

```bash
cd android
./gradlew test --tests "*AR*"
```

### Integration Tests (Device/Emulator Required)

```bash
# Connect device or start emulator
adb devices

# Run integration tests
cd android
./gradlew connectedAndroidTest --tests "*AR*"
```

### Run All Tests

```bash
cd android
./gradlew test connectedAndroidTest
```

---

## Test Coverage Goals

### Target Coverage

- **Service Layer:** >90% coverage
- **ViewModel Layer:** >85% coverage
- **Data Models:** >95% coverage
- **Integration Tests:** All major workflows covered

### Critical Paths to Test

1. ✅ AR model loading (success and error paths)
2. ✅ AR scan saving (with and without pending items)
3. ✅ Pending equipment listing
4. ✅ Pending equipment confirmation
5. ✅ Pending equipment rejection
6. ✅ Complete workflow (scan → save → review → confirm)
7. ✅ Error handling at all layers
8. ✅ State management correctness

---

## Implementation Priority

### Phase 1: Foundation (High Priority)
1. Service layer unit tests (`ArxOSCoreJNIWrapperARTest.kt`)
2. JNI integration tests (`JNIARIntegrationTest.kt`)
3. Basic ViewModel tests (`ARViewModelTest.kt`)

### Phase 2: Completeness (Medium Priority)
4. Data model tests (`ARDataModelsTest.kt`)
5. Complete workflow integration tests (`AndroidARWorkflowTest.kt`)
6. Service integration tests (`ARServiceIntegrationTest.kt`)

### Phase 3: Polish (Low Priority)
7. UI component tests (`ARComponentTest.kt`)
8. Performance tests
9. Edge case tests

---

## Test Best Practices

### 1. Isolated Test Environments
- Use temporary directories for test buildings
- Clean up test data after each test
- Use unique building names per test

### 2. Mocking Strategy
- Mock `ArxOSCoreService` in ViewModel tests
- Use real JNI in integration tests
- Mock Android Context where needed

### 3. Coroutine Testing
- Use `runTest` from `kotlinx.coroutines.test`
- Use `TestDispatcher` for controlled coroutine execution
- Test both success and error paths

### 4. Error Testing
- Test null pointer handling
- Test invalid JSON handling
- Test network/FFI errors
- Test edge cases (empty lists, large data)

### 5. State Testing
- Verify state updates via `StateFlow` collection
- Test state transitions
- Test concurrent state updates

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Android AR Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: |
          cd android
          ./gradlew test --tests "*AR*"

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
          # Copy built libraries to android/app/src/main/jniLibs/
      - name: Start emulator
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 29
      - name: Run integration tests
        run: |
          cd android
          ./gradlew connectedAndroidTest --tests "*AR*"
```

---

## Test Documentation

### Test File Structure

Each test file should include:
- File header with purpose and scope
- Module-level documentation
- Test case documentation
- Setup/teardown explanations

### Example Test File Header

```kotlin
/**
 * Integration tests for Android AR JNI bindings
 * 
 * These tests verify the Android AR integration JNI functions:
 * - nativeLoadARModel
 * - nativeSaveARScan
 * - nativeListPendingEquipment
 * - nativeConfirmPendingEquipment
 * - nativeRejectPendingEquipment
 * 
 * Prerequisites:
 * - Native library must be built and placed in src/main/jniLibs/
 * - Device/emulator must support the target ABI
 * - Test building data must be available
 */
```

---

## Future Enhancements

- [ ] Performance benchmarks for AR operations
- [ ] Memory leak detection tests
- [ ] Thread safety tests
- [ ] UI automation tests
- [ ] ARCore integration tests (requires physical device)
- [ ] Stress tests (large datasets, concurrent operations)

---

## References

- [Android Testing Guide](https://developer.android.com/training/testing)
- [JUnit Documentation](https://junit.org/junit4/)
- [Mockito Documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/)
- [Kotlin Coroutines Testing](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/)
- [Compose Testing](https://developer.android.com/jetpack/compose/testing)

---

**Next Steps:**
1. Review and approve this testing plan
2. Implement Phase 1 tests (Foundation)
3. Run tests and verify coverage
4. Iterate on test quality and completeness

