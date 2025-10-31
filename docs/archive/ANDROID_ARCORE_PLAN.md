# ARCore Integration Plan for ArxOS Android

## Goal

Enable real AR equipment scanning in the ArxOS Android app using Google ARCore, allowing users to scan buildings with their phone camera and automatically detect/tag equipment in 3D space.

---

## Current State

### ✅ What's Already Done
- **UI Screens**: ARScreen.kt with scanning interface, equipment list, manual tagging
- **Data Models**: DetectedEquipment, Vector3, ARScanResult defined
- **Manifest**: Camera permissions and ARCore features declared
- **Placeholders**: ARViewContainer.kt ready to implement
- **Rust Backend**: AR integration module exists in Rust core
- **Documentation**: AR scan data format and workflow documented

### ❌ What's Missing
- ARCore library not included in dependencies
- No actual AR camera view
- No ARCore session management
- No plane detection or equipment visualization
- No connection between AR detection and Rust backend

---

## Architecture

### Data Flow
```
User taps "Start AR Scan"
    ↓
ARScreen.kt creates ARSession
    ↓
ARViewContainer.kt displays live camera with AR overlays
    ↓
ARCore detects planes/surfaces
    ↓
User taps to place equipment markers
    ↓
Equipment position captured as Vector3
    ↓
ARViewModel saves to DetectedEquipment list
    ↓
User taps "Save Scan"
    ↓
ArxOSCoreService.processARScan() formats data
    ↓
Send to Rust via FFI: nativeParseARScan(json)
    ↓
Rust processes and adds to building data
```

### Components

```
ARScreen.kt (UI orchestrator)
├── ARViewModel (state management)
├── ARViewContainer.kt (ARCore integration)
│   ├── ARSession (camera + tracking)
│   ├── Plane Detection
│   ├── Anchor Placement
│   └── Equipment Visualization
└── ARScanResult (captured data)
    ↓
ArxOSCoreService (business logic)
├── processARScan()
├── saveARScan()
└── FFI bridge to Rust
```

---

## Implementation Options

### Option 1: ARCore SDK (Recommended)
**Pros:**
- Google's official AR platform
- Most devices supported (Android 7.0+)
- Good performance and stability
- Mature API with good documentation
- Works on many phones/tablets

**Cons:**
- Requires Google Play Services
- Larger APK size (~10-15MB)
- Device-specific compatibility

**Best for:** Real-world deployment on multiple device types

---

### Option 2: ARCore + Sceneform (Legacy)
**Pros:**
- Easy 3D rendering with Sceneform
- Pre-built materials and models

**Cons:**
- **DEPRECATED by Google** (stopped April 2021)
- No longer maintained
- Not recommended for new projects

**Best for:** ❌ Avoid this approach

---

### Option 3: Custom Camera + Computer Vision
**Pros:**
- No external dependencies
- Full control over AR experience
- Lighter weight

**Cons:**
- Much more complex to implement
- Have to build AR tracking yourself
- Not as polished as ARCore

**Best for:** Specific use cases where ARCore doesn't fit

---

## Recommended Approach: ARCore SDK

### Why ARCore?
1. **Official Google Solution**: Industry standard for Android AR
2. **Your App is Already Designed for It**: Manifest, permissions, UI all set up
3. **Best Device Support**: Works on hundreds of millions of Android devices
4. **Good Performance**: Optimized for phone hardware
5. **Documentation**: Extensive resources and examples

### What ARCore Provides
- **Motion Tracking**: Tracks device position and orientation
- **Environmental Understanding**: Detects flat surfaces (planes)
- **Light Estimation**: Adjusts rendering for realistic lighting
- **Depth API**: Optional for devices with depth sensors
- **Cloud Anchors**: Optional for multi-user experiences

### What We Need to Build
- Session management (start/stop AR)
- Plane visualization (show detected surfaces)
- Anchor placement (where equipment gets placed)
- Equipment markers (3D icons/sprites)
- Capture and data formatting

---

## Implementation Steps

### Phase 1: Setup & Dependencies (1-2 hours)

1. **Add ARCore to Gradle**
   ```gradle
   // In android/app/build.gradle
   dependencies {
       // ARCore SDK
       implementation 'com.google.ar:core:1.42.0'
       
       // Optional: ARCore extensions for extra features
       implementation 'com.google.ar.sceneform:core:1.17.1'
   }
   ```

2. **Add Maven Repository** (if needed)
   ```gradle
   // In android/build.gradle
   repositories {
       google()
       mavenCentral()
   }
   ```

3. **Update minSdk** (if needed)
   - ARCore requires Android 7.0 (API 24) minimum
   - Current: API 24 ✅

### Phase 2: Camera View Integration (2-4 hours)

4. **Replace ARViewContainer with Real Implementation**
   - Create `ARCoreView` composable
   - Use `GLSurfaceView` for AR rendering
   - Integrate with Android's `CameraX` or direct ARCore

5. **Implement ARSession Management**
   - Check ARCore availability
   - Create and configure AR session
   - Handle session pause/resume
   - Proper cleanup on destroy

### Phase 3: Plane Detection (3-5 hours)

6. **Detect Horizontal/Vertical Planes**
   - ARCore plane detection callback
   - Visualize detected planes
   - Show grid or mesh overlay

7. **User Interaction**
   - Raycast from touch screen
   - Place equipment anchors on planes
   - Show placement preview

### Phase 4: Equipment Visualization (3-5 hours)

8. **Equipment Markers**
   - 3D models or 2D sprites
   - Equipment-specific icons
   - Text labels for names

9. **AR Overlays**
   - Distance indicators
   - Equipment info cards
   - Grid guides

### Phase 5: Data Capture & Integration (2-3 hours)

10. **Capture AR Data**
    - Get anchor positions (Vector3)
    - Store equipment metadata
    - Format as ARScanData

11. **Connect to Rust Backend**
    - Call `ArxOSCoreJNI.nativeParseARScan(json)`
    - Handle success/failure responses
    - Update UI with results

### Phase 6: Polish & Testing (2-4 hours)

12. **Error Handling**
    - ARCore not available
    - Camera permissions denied
    - No planes detected
    - Session lost

13. **Performance Optimization**
    - Frame rate monitoring
    - Memory management
    - Battery efficiency

14. **User Testing**
    - Test on multiple devices
    - Different lighting conditions
    - Various surface types

---

## Technical Details

### ARCore Session Lifecycle

```kotlin
// Session creation
val session = Session(context)
val config = Config(session)
config.planeFindingMode = Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL
session.configure(config)

// Frame processing
while (isScanning) {
    session.update() // Get latest camera frame
    val frame = session.update()
    val planes = frame.getUpdatedTrackables(Plane::class.java)
    // Process planes and update UI
}

// Cleanup
session.close()
```

### Equipment Placement

```kotlin
// On user tap
val ray = arFrame.camera.getRay(touchPoint.x, touchPoint.y)
val hitResults = session.hitTest(ray, Trackable.Type.PLANE)

if (hitResults.isNotEmpty()) {
    val hit = hitResults[0]
    val anchor = session.createAnchor(hit.hitPose)
    
    val position = hit.hitPose.translation() // x, y, z
    val equipment = DetectedEquipment(
        name = "VAV-301",
        position = Vector3(position[0], position[1], position[2]),
        // ...
    )
    onEquipmentDetected(equipment)
}
```

### Data Format for Rust

```json
{
  "detectedEquipment": [
    {
      "name": "VAV-301",
      "type": "HVAC",
      "position": {"x": 1.23, "y": 0.0, "z": 2.45},
      "confidence": 1.0,
      "detectionMethod": "ARCore"
    }
  ],
  "roomName": "Room 301",
  "timestamp": 1234567890
}
```

---

## Considerations

### Device Compatibility
- Check ARCore availability before starting scan
- Gracefully degrade if ARCore not supported
- Show helpful error messages

### Performance
- AR is computationally intensive
- Monitor frame rate (target: 30+ FPS)
- Reduce quality on low-end devices
- Close session when not needed

### User Experience
- Clear instructions ("Move device slowly to detect surfaces")
- Visual feedback (grid appears when plane detected)
- Easy placement (tap to add equipment)
- Simple correction (tap to remove/change)

### Battery Life
- AR drains battery quickly
- Auto-pause after inactivity
- Show warning about battery usage
- Quick save option

---

## Alternative: Start Simple

If full ARCore feels overwhelming, we can start with a **"Marker-based AR"** approach:

1. Take regular photo
2. User taps on photo to place equipment markers
3. Auto-detect room dimensions (simpler CV)
4. Convert 2D taps to approximate 3D positions

**Pros:** Much simpler, faster to implement  
**Cons:** Less accurate, not true AR

---

## Questions to Discuss

1. **Do you want full ARCore or simpler marker-based approach?**
2. **Do you have specific device targets in mind?**
3. **What's the priority - speed to market or polished AR experience?**
4. **Should we do this in phases or all at once?**
5. **Do you want me to implement the full ARCore solution or just the setup first?**

---

## My Recommendation

**Start with Phase 1 (Setup) only** to:
1. Verify ARCore can be added to the project
2. Make sure it builds successfully
3. Test on a device if available

Then **decide** if you want to continue with full ARCore implementation or go simpler.

Would you like to:
- **Option A**: Just add ARCore dependencies and see if it builds?
- **Option B**: Full ARCore implementation (all phases)?
- **Option C**: Start with simple marker-based approach?
- **Option D**: Something else?

