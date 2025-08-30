# AR Interface - Pokémon GO for Buildings

## Catching Building Data with Your iPhone

### The Vision

Point your iPhone at any outlet, sensor, or piece of equipment and see its ArxObject data floating in augmented reality. Tap to capture, control, or contribute data - earning BILT tokens like catching Pokémon.

```swift
// User points camera at outlet
// AR overlay appears showing:
┌─────────────────────┐
│ OUTLET 0x4A7B       │
│ ⚡ Circuit 15       │
│ 📊 Load: 75%        │
│ 💰 Capture: 25 BILT │
└─────────────────────┘
[TAP TO CAPTURE]
```

### How It Works

```
iPhone Camera → ARKit → Object Detection
         ↓
    Mesh Query → LoRa Radio → Building
         ↓
    ArxObject → AR Overlay → Display
         ↓
    User Tap → Update → Earn BILT
```

### Core Features

#### Discovery Mode
- Walk through building
- Unmapped objects glow
- Tap to capture and map
- Earn BILT for discoveries

#### Inspection Mode
- Point at any object
- See complete status
- Historical graphs
- Maintenance records

#### Control Mode
- Tap to toggle outlets
- Adjust thermostats
- Override schedules
- Requires permissions

#### Game Mode
- Daily quests appear
- "Fix 5 faults" = 100 BILT
- Leaderboards
- Achievements

### Technical Architecture

```swift
// iOS App Structure
ArxosAR/
├── ARView/
│   ├── ObjectDetection.swift   // Recognize outlets
│   ├── MeshQuery.swift         // Query via radio
│   └── Overlay.swift           // AR rendering
├── MeshNetwork/
│   ├── LoRaBridge.swift        // Hardware interface
│   ├── ArxObject.swift         // 13-byte protocol
│   └── Cache.swift             // Local storage
└── GameEngine/
    ├── Player.swift            // Profile & stats
    ├── BILT.swift              // Token management
    └── Quests.swift            // Daily challenges
```

### AR Object Recognition

```swift
// Detect electrical outlet in camera feed
func detectOutlet(in frame: ARFrame) -> CGRect? {
    let request = VNDetectRectanglesRequest()
    let handler = VNImageRequestHandler(cvPixelBuffer: frame)
    try? handler.perform([request])
    
    return request.results?.first?.boundingBox
}

// Query mesh for ArxObject at location
func queryMesh(at worldPosition: simd_float3) -> ArxObject? {
    let query = MeshQuery(
        position: worldPosition,
        radius: 0.5 // meters
    )
    
    return meshNetwork.query(query)
}
```

### AR Overlay Rendering

```swift
// Display ArxObject data in AR
func renderOverlay(for object: ArxObject, at position: SCNVector3) {
    let node = SCNNode()
    
    // Create info panel
    let panel = createInfoPanel(object)
    node.addChildNode(panel)
    
    // Add interaction
    node.name = "arxobject_\(object.id)"
    
    // Position in world
    node.position = position
    sceneView.scene.rootNode.addChildNode(node)
}
```

### Mesh Network Bridge

```swift
// iPhone talks to building via external radio
class LoRaBridge {
    let peripheral: CBPeripheral  // Bluetooth to LoRa adapter
    
    func send(_ object: ArxObject) {
        let data = object.toBytes()
        peripheral.writeValue(data, for: loraCharacteristic)
    }
    
    func receive() -> ArxObject? {
        guard let data = receivedData else { return nil }
        return ArxObject(from: data)
    }
}
```

### Gaming Mechanics

#### Capture Mechanism
```swift
// Like Pokémon GO capture
func captureObject(_ object: ArxObject) {
    // Throw virtual "scanner"
    animateScanner(toward: object)
    
    // Success based on:
    // - Distance
    // - Object complexity
    // - Player level
    
    if captureSuccessful {
        player.inventory.add(object)
        player.bilt += object.value
        showCaptureAnimation()
    }
}
```

#### Daily Quests
```swift
enum Quest {
    case mapNewRooms(count: Int)
    case fixFaults(count: Int)
    case optimizeHVAC(savings: Float)
    case completeCircuit(panel: String)
}

// Quests appear at objects
func showQuestMarker(at object: ArxObject) {
    if object.hasFault {
        displayMarker("Fix me! +50 BILT", at: object.position)
    }
}
```

### Player Classes in AR

```swift
enum PlayerClass {
    case electrician  // See electrical details
    case hvac        // See airflow/temp
    case plumber     // See water systems
    case security    // See access/cameras
    case admin       // See everything
}

// Different data based on class
func overlayData(for object: ArxObject) -> String {
    switch player.class {
    case .electrician:
        return "Circuit \(object.circuit), \(object.amps)A"
    case .hvac:
        return "Temp \(object.temperature)°F"
    default:
        return "Object \(object.id)"
    }
}
```

### Social Features

```swift
// See other players in building
func renderPlayer(_ player: Player) {
    let avatar = PlayerAvatar(player)
    avatar.position = player.worldPosition
    sceneView.scene.rootNode.addChildNode(avatar)
    
    // Show what they're working on
    if let currentObject = player.focusedObject {
        drawLine(from: avatar, to: currentObject)
    }
}
```

### Performance Optimization

```swift
// Only render nearby objects
let maxRenderDistance: Float = 50.0  // meters

// Level of detail
func detailLevel(for distance: Float) -> DetailLevel {
    switch distance {
    case 0..<5: return .full
    case 5..<20: return .medium
    default: return .minimal
    }
}

// Occlusion culling
// Don't render objects behind walls
```

### Hardware Requirements

#### iPhone/iPad
- iPhone 12 or newer (LiDAR preferred)
- iOS 15+
- ARKit support

#### LoRa Adapter
- Bluetooth LE to LoRa bridge
- Or Lightning/USB-C LoRa dongle
- $25-45 cost

### Monetization via BILT

```swift
// In-app BILT economy
struct BILTStore {
    let items = [
        "Pro Scanner": 100 BILT,
        "X-Ray Vision": 250 BILT,
        "Speed Boost": 50 BILT,
        "Custom Avatar": 500 BILT
    ]
}

// Earn through gameplay
// Spend on tools/cosmetics
// Trade with other players
```

### Privacy & Security

- **Local first**: Data stays on device
- **Mesh only**: No internet required
- **Permission based**: Building owner controls
- **Anonymous**: No personal data shared

### Future Features

#### AI Assistant
"Hey Siri, show me all faulty outlets"

#### Multiplayer Raids
Team up to map large buildings

#### Time Machine
See historical data in AR

#### Predictive Maintenance
AR highlights failing equipment

### Next Steps

- [ARKit Setup](arkit-setup.md) - iOS development
- [Object Detection](object-detection.md) - Computer vision
- [Mesh Queries](mesh-queries.md) - Radio integration
- [Gestures](gestures.md) - User interaction

---

*"Gotta map 'em all!"* 🏢📱⚡