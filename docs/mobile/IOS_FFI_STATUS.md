# iOS FFI Integration Status _(Archived)_

> **Status (November 2025):** Native iOS FFI integration is on hold while we ship the WASM PWA. The information below is preserved for historical reference.

**Date:** January 2025  
**Status:** Ready for Integration  
**Priority:** High

---

## Overview

ArxOS iOS app has complete FFI integration infrastructure but requires final linking and testing on physical devices.

---

## Current Status

### ✅ Completed

1. **FFI Wrappers**: Complete Swift wrapper implementation in `ArxOSCoreFFI.swift`
   - All C FFI functions imported and wrapped
   - Proper memory management with `arxos_free_string()`
   - JSON parsing and error handling
   - Generic `callFFI` helper function

2. **Swift Models**: Complete model definitions in `ArxOSModels.swift`
   - `Room` with proper Codable conformance
   - `Equipment` with position and properties
   - `DetectedEquipment` for AR scans
   - `Position3D` for spatial data
   - `TerminalError` enum for error handling

3. **XCFramework**: Built for all iOS architectures
   - ✅ `aarch64-apple-ios` (devices)
   - ✅ `x86_64-apple-ios` (Intel simulators)
   - ✅ `aarch64-apple-ios-sim` (M1/M2 simulators)
   - Location: `ios/build/ArxOS.xcframework`

4. **Build Configuration**: Xcode project properly configured
   - Framework linked in project settings
   - Headers properly configured
   - Linker flags added (`-lz -liconv`)

### ⏳ Pending

1. **FFI Calls**: Currently commented out for safety
   - Location: `EquipmentListView.swift` lines 88-112
   - FFI library calls wrapped in TODO comments
   - Fallback to empty array implemented

2. **Testing**: Requires physical iOS device or simulator
   - Memory management verification
   - Actual FFI call testing
   - Error handling validation

---

## Integration Steps

### Step 1: Verify Framework Linkage

```bash
# Ensure XCFramework exists
ls -la ios/build/ArxOS.xcframework/

# Verify architectures
lipo -info ios/build/ArxOS.xcframework/ios-arm64/libarxos.a
```

### Step 2: Enable FFI Calls

**File:** `ios/ArxOSMobile/ArxOSMobile/Views/EquipmentListView.swift`

Uncomment lines 88-112:

```swift
private func loadEquipment() {
    isLoading = true
    
    // ENABLE THIS: Uncomment when FFI library is properly linked
    let ffi = ArxOSCoreFFI()
    ffi.listEquipment(buildingName: "Default Building") { result in
        DispatchQueue.main.async {
            switch result {
            case .success(let equipment):
                self.equipmentList = equipment.map { eq in
                    Equipment(
                        id: eq.id,
                        name: eq.name,
                        type: eq.equipmentType,
                        status: eq.status,
                        location: "Room \(eq.position.x), \(eq.position.y)",
                        lastMaintenance: "Unknown"
                    )
                }
            case .failure(let error):
                print("Error loading equipment: \(error.localizedDescription)")
                self.equipmentList = []
            }
            self.isLoading = false
        }
    }
}
```

**Remove lines 114-118** (temporary empty array fallback)

### Step 3: Update FFI Wrapper

**File:** `ios/ArxOSMobile/ArxOSMobile/Services/ArxOSCoreFFI.swift`

Uncomment FFI calls in:
- `listRooms()` - line 86
- `getRoom()` - line 100
- `listEquipment()` - line 122
- Other methods as needed

---

## Testing Checklist

- [ ] Build iOS app successfully in Xcode
- [ ] Launch on iOS simulator (M1/M2 Mac)
- [ ] Launch on physical iOS device
- [ ] Verify equipment list loads from FFI
- [ ] Verify memory management (no leaks)
- [ ] Test error handling (offline, invalid data)
- [ ] Verify AR scan data processing
- [ ] Test room listing functionality
- [ ] Verify position data accuracy

---

## Memory Management

### Critical: Always Free Strings

```swift
// ✅ CORRECT: Always call arxos_free_string after getting result
let resultPtr = arxos_list_equipment(buildingName)
guard let resultPtr = resultPtr else { return .failure(...) }
let resultString = String(cString: resultPtr)
arxos_free_string(resultPtr)  // CRITICAL: Free the memory

// ❌ WRONG: Forgetting to free memory
let resultPtr = arxos_list_equipment(buildingName)
let resultString = String(cString: resultPtr)
// Missing: arxos_free_string(resultPtr)
```

### Memory Leak Testing

Use Instruments in Xcode:
1. Product → Profile (Cmd+I)
2. Select "Leaks" template
3. Run app and perform operations
4. Check for memory leaks in FFI calls

---

## Known Issues

### 1. FFI Library Not Linked

**Symptom:** App crashes or returns null pointers  
**Solution:** Verify XCFramework is linked in Xcode project settings

### 2. Missing Framework Paths

**Symptom:** Build errors about missing headers  
**Solution:** Check Framework Search Paths in Build Settings

### 3. Architecture Mismatch

**Symptom:** "Can't load library" error  
**Solution:** Ensure XCFramework includes simulator architectures

---

## FFI Function Reference

### Available Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `arxos_list_rooms` | List all rooms | JSON array of Room objects |
| `arxos_list_equipment` | List all equipment | JSON array of Equipment objects |
| `arxos_get_room` | Get specific room | JSON Room object |
| `arxos_get_equipment` | Get specific equipment | JSON Equipment object |
| `arxos_parse_ar_scan` | Parse AR scan data | JSON DetectedEquipment array |
| `arxos_extract_equipment` | Extract equipment from scan | JSON Equipment array |
| `arxos_free_string` | Free returned string | void |

### Response Format

All functions return JSON strings that must be:
1. Parsed from `UnsafeMutablePointer<CChar>`
2. Converted to Swift String
3. Freed with `arxos_free_string()`
4. Deserialized to model objects

```swift
let resultPtr = arxos_list_equipment(buildingName)
let jsonString = String(cString: resultPtr)
arxos_free_string(resultPtr)

let data = jsonString.data(using: .utf8)!
let equipment = try JSONDecoder().decode([Equipment].self, from: data)
```

---

## Next Actions

1. **Build and test on iOS simulator**
   - Verify XCFramework loads correctly
   - Test FFI calls with sample data

2. **Test on physical device**
   - Deploy to iPhone/iPad
   - Verify real-world operation

3. **Performance testing**
   - Memory leak checks
   - Performance profiling
   - Battery usage monitoring

4. **Error handling validation**
   - Test offline scenarios
   - Test invalid input handling
   - Test large data sets

---

## Support

For FFI integration issues:
- Check `docs/MOBILE_FFI_INTEGRATION.md` for detailed documentation
- Review `crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs` for Rust FFI implementation
- Check Xcode build logs for linker errors

---

**Status:** Ready for integration testing on iOS devices  
**Estimated Effort:** 2-4 hours for complete testing  
**Risk:** Low (infrastructure complete, needs verification)

