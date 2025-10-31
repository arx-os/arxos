# Android ARCore Implementation Plan

## Goal: Mirror iOS ARKit Approach

Match the iOS app's AR implementation in Android using ARCore (ARCore = Android's equivalent to iOS's ARKit).

---

## iOS App Analysis

### What iOS Uses
1. **ARKit** (Apple's AR framework) - equivalent to ARCore on Android
2. **RealityKit** - for 3D rendering
3. **ARView** - main AR camera view
4. **ARWorldTrackingConfiguration** - tracks world position
5. **Plane Detection** - horizontal and vertical surfaces
6. **ARAnchor** - placement markers for equipment

### iOS Architecture
```
ARScanView (SwiftUI View)
├── State: isScanning, detectedEquipment, currentRoom
├── ARViewContainer (UIViewRepresentable wrapper)
│   ├── ARView (RealityKit)
│   ├── ARSessionDelegate (handles callbacks)
│   └── Configuration: planeDetection, environmentTexturing
└── UI Overlay
    ├── Top: Room name + Stop button
    ├── Center: AR camera view
    ├── Bottom: Equipment tags (horizontal scroll)
    └── Controls: Add, List, Save
```

---

## Android Equivalent

### What We Need
1. **ARCore** (Google's AR framework) = ARKit
2. **GLSurfaceView** or **CameraX** = ARView
3. **ARSession** = ARSession
4. **Config** = ARWorldTrackingConfiguration
5. **Plane Detection** = Plane detection
6. **Anchor** = ARAnchor

### Android Architecture
```
ARScreen (Compose View)
├── State: isScanning, detectedEquipment, currentRoom
├── ARViewContainer (Composable wrapper)
│   ├── GLSurfaceView + ARSession
│   ├── ARCore SessionDelegate (handles callbacks)
│   └── Config: planeFindingMode
└── UI Overlay
    ├── Top: Room name + Stop button
    ├── Center: AR camera view
    ├── Bottom: Equipment tags (horizontal scroll)
    └── Controls: Add, List, Save
```

---

## Implementation Steps

### Phase 1: Core AR Integration (Matches iOS `ARViewContainer.swift`)

#### Step 1.1: Add ARCore Dependency
```gradle
// In android/app/build.gradle
dependencies {
    implementation 'com.google.ar:core:1.42.0'
}
```

#### Step 1.2: Implement `ARViewContainer` (Matches iOS Structure)

**iOS:**
```swift
struct ARViewContainer: UIViewRepresentable {
    @Binding var detectedEquipment: [DetectedEquipment]
    @Binding var isScanning: Bool
    
    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        let configuration = ARWorldTrackingConfiguration()
        configuration.planeDetection = [.horizontal, .vertical]
        arView.session.run(configuration)
        return arView
    }
}
```

**Android Equivalent:**
```kotlin
@Composable
fun ARViewContainer(
    detectedEquipment: MutableState<List<DetectedEquipment>>,
    isScanning: Boolean,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var arSession by remember { mutableStateOf<Session?>(null) }
    
    AndroidView(
        factory = { ctx ->
            createARSession(ctx) { session -> arSession = session }
        },
        modifier = modifier,
        update = { view ->
            if (isScanning) {
                arSession?.resume()
            } else {
                arSession?.pause()
            }
        }
    )
}

private fun createARSession(
    context: Context,
    onSessionCreated: (Session) -> Unit
): GLSurfaceView {
    val glSurfaceView = GLSurfaceView(context)
    
    // Check ARCore availability (matches iOS ARWorldTrackingConfiguration.supportsFrameSemantics)
    val availability = ArCoreApk.getInstance().checkAvailability(context)
    if (availability.isSupported) {
        try {
            val session = Session(context)
            val config = Config(session)
            config.planeFindingMode = Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL
            session.configure(config)
            session.resume()
            onSessionCreated(session)
        } catch (e: Exception) {
            Log.e("ARViewContainer", "Failed to create AR session", e)
        }
    }
    
    return glSurfaceView
}
```

#### Step 1.3: Create AR Coordinator (Matches iOS `ARCoordinator`)

**iOS:**
```swift
class ARCoordinator: NSObject, ARSessionDelegate {
    var parent: ARViewContainer
    
    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        // Process AR frame
    }
    
    func session(_ session: ARSession, didAdd anchors: [ARAnchor]) {
        for anchor in anchors {
            if let planeAnchor = anchor as? ARPlaneAnchor {
                handlePlaneDetection(planeAnchor)
            }
        }
    }
}
```

**Android Equivalent:**
```kotlin
class AROverlaySessionCallbacks(
    private val onEquipmentDetected: (DetectedEquipment) -> Unit
) : Session.Callback {
    
    override fun onFrame(frame: Frame) {
        // Process AR frame (matches iOS didUpdate frame)
        val planes = frame.getUpdatedTrackables(Plane::class.java)
        for (plane in planes) {
            if (plane.trackingState == TrackingState.TRACKING) {
                handlePlaneDetection(plane)
            }
        }
    }
    
    private fun handlePlaneDetection(plane: Plane) {
        // Process detected plane (matches iOS handlePlaneDetection)
        val pose = plane.centerPose
        val position = pose.translation() // x, y, z
        
        // Simulate equipment detection
        val equipment = DetectedEquipment(
            id = "detected_${System.currentTimeMillis()}",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(position[0], position[1], position[2]),
            status = "Detected",
            icon = "fan"
        )
        onEquipmentDetected(equipment)
    }
}
```

### Phase 2: UI Integration (Matches iOS `ARScanView.swift`)

#### Step 2.1: Update ARScreen to use Real AR

The current `ARScreen.kt` already has the right structure. Just need to replace:
```kotlin
// OLD: Placeholder
Text("ARCore integration needed")

// NEW: Real AR view
ARViewContainer(
    detectedEquipment = detectedEquipment,
    isScanning = isScanning,
    modifier = Modifier.fillMaxSize()
)
```

This matches iOS where `ARScanView` embeds `ARViewContainer`.

### Phase 3: Service Integration (Matches iOS `ArxOSCore.swift`)

#### Step 3.1: Add AR Methods to ArxOSCoreService

Already exists! Just need to implement:

**iOS:**
```swift
func processARData(_ data: Data, roomName: String, completion: @escaping (Result<[DetectedEquipment], Error>) -> Void)
func saveARScan(_ equipment: [DetectedEquipment], room: String, completion: @escaping (Result<String, Error>) -> Void)
```

**Android:**
```kotlin
// Already in ArxOSCoreService.kt - just needs JNI implementation
suspend fun processARScan(scanData: ARScanData): ARScanResult
suspend fun saveARScan(equipment: List<DetectedEquipment>, roomName: String): Boolean
```

### Phase 4: Testing & Polish

- Test on physical device (ARCore needs real camera)
- Handle edge cases (no ARCore support, permissions, etc.)
- Match iOS UX exactly

---

## Side-by-Side Comparison

| iOS Component | Android Equivalent | Status |
|--------------|-------------------|--------|
| ARKit | ARCore | ✅ Framework exists |
| ARView | GLSurfaceView + ARSession | ⚠️ Needs implementation |
| ARWorldTrackingConfiguration | Config | ✅ API exists |
| planeDetection | planeFindingMode | ✅ API exists |
| ARAnchor | Anchor | ✅ API exists |
| ARSessionDelegate | Session.Callback | ✅ Callback exists |
| ARFrame | Frame | ✅ API exists |
| ARPlaneAnchor | Plane | ✅ API exists |

---

## Implementation File Structure

```
android/app/src/main/java/com/arxos/mobile/
├── ui/
│   ├── screens/
│   │   └── ARScreen.kt (already exists - just needs ARViewContainer connection)
│   └── components/
│       └── ARViewContainer.kt (needs real ARCore implementation)
├── service/
│   ├── ArxOSCoreService.kt (already has AR methods - needs JNI)
│   └── ARSessionManager.kt (new - manages AR lifecycle)
└── ar/
    ├── ARCoreManager.kt (new - wraps ARCore APIs)
    └── AROverlayRenderer.kt (new - renders AR overlays)
```

---

## Matching iOS Behavior

### iOS: Plane Detection
```swift
configuration.planeDetection = [.horizontal, .vertical]
```

**Android:**
```kotlin
config.planeFindingMode = Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL
```

### iOS: Manual Equipment Placement
```swift
private func addEquipmentManually() {
    let newEquipment = DetectedEquipment(
        name: "Manual Equipment",
        type: "Manual",
        position: Position3D(x: 0, y: 0, z: 0),
        status: "Detected",
        icon: "wrench"
    )
    detectedEquipment.append(newEquipment)
}
```

**Android:** Already matches this in `ARScreen.kt` ✅

### iOS: Save Scan
```swift
private func saveScan() {
    // Save scan results to ArxOS
    // This would integrate with the Rust core
    isScanning = false
}
```

**Android:** Already has this structure ✅

---

## Next Steps

**Would you like me to:**

1. **Start implementing Phase 1** (add ARCore dependency and create real ARViewContainer)?
2. **Just add the dependency** first and verify it builds?
3. **Create all the implementation files** at once?
4. **Something else?**

The structure is already there (your Android UI is very similar to iOS). We mainly need to:
- Add ARCore library
- Replace placeholder ARViewContainer with real AR implementation
- Connect the callbacks to update detected equipment

This should be straightforward since the architectures are so similar!

