# Arxos Multi-Modal Mobile Terminal
## Software Architecture & Development Plan

### Executive Summary
The Arxos mobile application is a multi-modal terminal interface that seamlessly switches between 2D ASCII-BIM navigation, 3D ASCII building visualization, and AR camera overlays. The app maintains a consistent terminal-based interaction paradigm while providing touch-optimized building infrastructure management through real-time LiDAR scanning, ArxObject interaction, and field contribution workflows.

---

## 1. System Architecture Overview

### 1.1 Multi-Modal Interface Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                ARXOS MOBILE TERMINAL APP                        │
├─────────────────────────────────────────────────────────────────┤
│  View Mode Controller (Swift/Kotlin)                           │
│  - Mode switching logic (2D ↔ 3D ↔ AR)                        │
│  - Context-aware terminal updates                              │
│  - Touch gesture interpretation                                │
│  - Voice command processing                                    │
├─────────────────────────────────────────────────────────────────┤
│  2D ASCII Renderer     │  3D ASCII Renderer  │  AR Engine      │
│  - Top-down building   │  - Perspective view  │  - ARKit/ARCore │
│  - Touch navigation    │  - Depth-based ASCII │  - LiDAR scan   │
│  - Zoom/pan controls   │  - Walk-through mode │  - Spatial anchors│
│  - Object selection    │  - Isometric display │  - Overlay rendering│
├─────────────────────────────────────────────────────────────────┤
│              SHARED CORE ENGINE (C via FFI)                    │
│  ASCII-BIM Engine      │  ArxObject Runtime   │  Terminal Engine│
│  - 2D/3D/AR rendering  │  - Object queries    │  - CLI commands │
│  - Real-time updates   │  - State management  │  - Response parsing│
│  - Spatial intelligence│  - Constraint validation│ - Auto-complete│
├─────────────────────────────────────────────────────────────────┤
│                    DATA & COMMUNICATION LAYER                  │
│  Building State Cache  │  Network Sync        │  LiDAR Processing│
│  - Local ArxObjects    │  - Real-time updates │  - Point cloud   │
│  - ASCII cache        │  - Conflict resolution│  - Object detection│
│  - Offline capability  │  - Delta sync        │  - Spatial mapping│
├─────────────────────────────────────────────────────────────────┤
│                     DEVICE INTEGRATION                         │
│  Camera/LiDAR          │  Sensors             │  Storage        │
│  - Live point clouds   │  - Gyroscope/compass │  - Local cache  │
│  - Photo/video capture │  - Accelerometer     │  - Offline data │
│  - AR tracking         │  - Location services │  - Media files  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow Architecture
```
User Input (Touch/Voice/Camera) → Mode Controller → ASCII Renderers → C Engine → ArxObject Runtime
                                        ↓                ↑                      ↕
Device Sensors (LiDAR/Camera) → Spatial Processing → Building State → Terminal Engine
                                        ↓                ↑                      ↕
Network Sync ← Building Cache ← Local Storage ← Real-time Updates ← CLI Commands
```

---

## 2. Core Components

### 2.1 View Mode Controller (Swift/Kotlin)

#### Purpose
Central orchestrator that manages seamless transitions between 2D ASCII, 3D ASCII, and AR camera modes while maintaining terminal interface consistency.

#### Core Architecture
```swift
// iOS implementation - primary reference
class ViewModeController: ObservableObject {
    @Published var currentMode: ViewMode = .ascii2D
    @Published var terminalContext: TerminalContext
    @Published var buildingState: BuildingState
    
    // Core view mode components
    let ascii2DRenderer: ASCII2DRenderer
    let ascii3DRenderer: ASCII3DRenderer  
    let arEngine: AREngine
    let terminalEngine: TerminalEngine
    let coreEngine: ArxosCoreEngine  // C engine bridge
    
    // Mode transition logic
    func switchToMode(_ mode: ViewMode, context: TransitionContext?) {
        // Seamless transition with shared state
    }
}

enum ViewMode {
    case ascii2D        // Top-down building navigation
    case ascii3D        // 3D perspective ASCII rendering
    case arCamera       // AR camera with ASCII overlays
    case terminal       // Full-screen terminal mode
}

struct TransitionContext {
    let selectedObject: ArxObject?
    let cameraPosition: CameraPosition?
    let zoomLevel: Float
    let terminalCommand: String?
}
```

#### Mode Switching Logic
```swift
// Context-aware mode transitions
func handleObjectSelection(_ object: ArxObject, currentMode: ViewMode) {
    switch (currentMode, object.type) {
    case (.ascii2D, .electrical):
        // Electrical object selected in 2D → Switch to AR for real-world validation
        switchToMode(.arCamera, context: TransitionContext(
            selectedObject: object,
            terminalCommand: "arx inspect \(object.id)"
        ))
        
    case (.arCamera, .room):
        // Room detected in AR → Switch to 3D ASCII for spatial context  
        switchToMode(.ascii3D, context: TransitionContext(
            selectedObject: object,
            cameraPosition: CameraPosition.roomOverview
        ))
        
    case (.ascii3D, .wall):
        // Wall selected in 3D → Switch to 2D for building context
        switchToMode(.ascii2D, context: TransitionContext(
            selectedObject: object,
            zoomLevel: 2.0  // Zoom to show wall context
        ))
    }
}
```

#### Terminal Context Management
```swift
class TerminalContext: ObservableObject {
    @Published var currentPrompt: String
    @Published var commandHistory: [TerminalCommand]
    @Published var availableCommands: [String]  // Context-aware autocomplete
    @Published var outputBuffer: [TerminalOutput]
    
    // Update terminal based on current view mode and selected objects
    func updateContext(mode: ViewMode, selectedObjects: [ArxObject]) {
        switch mode {
        case .ascii2D:
            availableCommands = ["navigate", "map", "query", "zoom", "find"]
            currentPrompt = "arx @\(buildingID) 2d> "
            
        case .ascii3D:
            availableCommands = ["view", "walk-through", "perspective", "rotate"]  
            currentPrompt = "arx @\(buildingID) 3d> "
            
        case .arCamera:
            availableCommands = ["scan", "contribute", "validate", "inspect"]
            currentPrompt = "arx @\(buildingID) ar> "
        }
    }
}
```

### 2.2 ASCII 2D Renderer (Swift/Kotlin)

#### Purpose
Provides touch-optimized 2D ASCII building navigation with zoom, pan, and object selection capabilities.

#### Core Implementation
```swift
class ASCII2DRenderer: ObservableObject {
    @Published var asciiCanvas: ASCIICanvas
    @Published var cameraTransform: Camera2D
    @Published var selectedObjects: Set<ArxObject>
    
    private let coreEngine: ArxosCoreEngineProtocol
    private var renderTimer: Timer?
    
    // Touch gesture handling
    func handlePanGesture(_ gesture: DragGesture.Value) {
        let deltaX = Float(gesture.translation.x) * panSensitivity
        let deltaY = Float(gesture.translation.y) * panSensitivity
        
        cameraTransform.position.x -= deltaX / cameraTransform.zoom
        cameraTransform.position.y -= deltaY / cameraTransform.zoom
        
        requestRenderUpdate()
    }
    
    func handlePinchGesture(_ gesture: MagnificationGesture.Value) {
        let newZoom = cameraTransform.zoom * Float(gesture)
        cameraTransform.zoom = clamp(newZoom, minZoom: 0.5, maxZoom: 10.0)
        
        requestRenderUpdate()
    }
    
    // Object selection through touch
    func handleTapGesture(_ location: CGPoint) {
        let screenCoords = convertToScreenCoords(location)
        let asciiCoords = convertToASCIICoords(screenCoords, camera: cameraTransform)
        
        if let object = coreEngine.getObjectAtCoords(asciiCoords.x, asciiCoords.y) {
            selectedObjects.insert(object)
            
            // Trigger context-aware mode switch if appropriate
            viewModeController.handleObjectSelection(object, currentMode: .ascii2D)
        }
    }
}

struct Camera2D {
    var position: Point2D = Point2D(x: 0, y: 0)
    var zoom: Float = 1.0
    var rotation: Float = 0.0  // For building orientation
}
```

#### Performance Optimizations
```swift
// Efficient ASCII rendering for mobile
class ASCII2DRenderOptimizer {
    private var asciiCache: LRUCache<String, ASCIICanvas>
    private var visibilityChecker: VisibilityChecker
    
    func renderVisibleRegion(camera: Camera2D, screenSize: CGSize) -> ASCIICanvas {
        let visibleBounds = calculateVisibleBounds(camera, screenSize)
        
        // Only render ASCII characters within screen bounds
        let cacheKey = generateCacheKey(visibleBounds, camera.zoom)
        
        if let cachedCanvas = asciiCache.get(cacheKey) {
            return cachedCanvas
        }
        
        // Render only visible portion through C engine
        let canvas = coreEngine.renderRegion(visibleBounds, detailLevel: camera.zoom)
        asciiCache.set(cacheKey, canvas)
        
        return canvas
    }
}
```

### 2.3 ASCII 3D Renderer (Swift/Kotlin)

#### Purpose
Provides 3D perspective ASCII rendering for immersive building exploration with depth-based character selection and walk-through capabilities.

#### Core 3D ASCII Implementation
```swift
class ASCII3DRenderer: ObservableObject {
    @Published var camera3D: Camera3D
    @Published var renderMode: ASCII3DMode = .isometric
    @Published var walkThroughPath: [Point3D] = []
    
    private let coreEngine: ArxosCoreEngineProtocol
    private var depthBuffer: [Float] = []
    
    enum ASCII3DMode {
        case isometric      // Fixed 45-degree perspective
        case perspective    // True 3D perspective  
        case walkThrough    // Animated path through building
        case roomFocus      // Focus on specific room with context
    }
    
    // 3D camera controls
    func handleRotationGesture(_ gesture: RotationGesture.Value) {
        camera3D.rotation.y += Float(gesture.rotation)
        requestRender()
    }
    
    func handleDragGesture(_ gesture: DragGesture.Value) {
        let sensitivity: Float = 0.01
        camera3D.rotation.x += Float(gesture.translation.y) * sensitivity
        camera3D.rotation.y += Float(gesture.translation.x) * sensitivity
        
        // Clamp vertical rotation to prevent flipping
        camera3D.rotation.x = clamp(camera3D.rotation.x, min: -π/2, max: π/2)
        
        requestRender()
    }
}

struct Camera3D {
    var position: Point3D = Point3D(x: 0, y: 2.0, z: 5.0)  // Eye height
    var rotation: Point3D = Point3D(x: 0, y: 0, z: 0)
    var fieldOfView: Float = 60.0  // Degrees
    var near: Float = 0.1
    var far: Float = 100.0
}
```

#### 3D ASCII Character Selection Algorithm
```swift
extension ASCII3DRenderer {
    // Advanced character selection based on depth and viewing angle
    func selectCharacterForPixel(_ worldPos: Point3D, _ normal: Vector3D, _ material: MaterialType) -> Character {
        let viewDir = normalize(camera3D.position - worldPos)
        let distance = length(camera3D.position - worldPos)
        
        // Depth-based density selection
        let depthDensity = calculateDepthDensity(distance)
        
        // Surface orientation affects character choice
        let surfaceAlignment = dot(normal, viewDir)
        
        // Material-specific character sets
        switch material {
        case .wall:
            return selectWallCharacter(depthDensity, surfaceAlignment)
        case .equipment:
            return selectEquipmentCharacter(depthDensity, distance)
        case .room_interior:
            return selectRoomCharacter(depthDensity, material)
        }
    }
    
    private func selectWallCharacter(_ depth: Float, _ alignment: Float) -> Character {
        // Front-facing walls get solid characters
        if alignment > 0.8 {
            return depth > 0.7 ? "█" : "▓"
        }
        // Side-facing walls get line characters  
        else if alignment > 0.3 {
            return "│"
        }
        // Edge-on walls get thin characters
        else {
            return "║"
        }
    }
}
```

### 2.4 AR Engine (Swift/Kotlin + ARKit/ARCore)

#### Purpose
Provides real-world camera view with ASCII-BIM overlays, LiDAR-based building reconstruction, and spatial anchor contribution workflows.

#### Core AR Implementation
```swift
class AREngine: NSObject, ObservableObject, ARSessionDelegate {
    @Published var arSession: ARSession = ARSession()
    @Published var spatialAnchors: [ArxosSpatialAnchor] = []
    @Published var livePointCloud: [Point3D] = []
    @Published var detectedObjects: [DetectedObject] = []
    
    private let coreEngine: ArxosCoreEngineProtocol
    private var scanningMode: ARScanningMode = .inspection
    
    enum ARScanningMode {
        case inspection     // View existing ArxObject data
        case contribution   // Add new spatial anchors
        case validation     // Verify existing data accuracy
        case liveScanning   // Real-time building reconstruction
    }
    
    func startARSession() {
        let config = ARWorldTrackingConfiguration()
        config.planeDetection = [.horizontal, .vertical]
        config.sceneReconstruction = .meshWithClassification
        
        // Enable LiDAR if available
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.meshWithClassification) {
            config.sceneReconstruction = .meshWithClassification
        }
        
        arSession.run(config)
        arSession.delegate = self
    }
    
    // ARSessionDelegate - Process LiDAR data in real-time
    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        guard let pointCloud = frame.rawFeaturePoints else { return }
        
        // Convert ARKit points to Arxos coordinate system
        let arxosPoints = convertARKitToArxosCoords(pointCloud.points)
        
        // Update live point cloud
        DispatchQueue.main.async {
            self.livePointCloud = arxosPoints
        }
        
        // Process points for building reconstruction
        if scanningMode == .liveScanning {
            processLiDARForBuilding(arxosPoints)
        }
        
        // Update ASCII overlays based on current camera position
        updateASCIIOverlays(frame.camera.transform)
    }
    
    // Real-time building reconstruction from LiDAR
    private func processLiDARForBuilding(_ points: [Point3D]) {
        // Send points to C engine for real-time processing
        coreEngine.processLiDARPoints(points) { [weak self] detectedObjects in
            DispatchQueue.main.async {
                self?.detectedObjects = detectedObjects
                // Trigger ASCII update with new building data
                self?.notifyBuildingModelUpdated()
            }
        }
    }
}

// AR Overlay Rendering
extension AREngine {
    func renderASCIIOverlay(for camera: ARCamera, onto frame: ARFrame) -> ASCIIOverlay {
        let cameraTransform = camera.transform
        let projectionMatrix = camera.projectionMatrix(for: .portrait, viewportSize: frame.camera.imageResolution, zNear: 0.1, zFar: 100.0)
        
        // Get ASCII characters that should be visible from current position
        let visibleASCII = coreEngine.getASCIIForCameraPosition(cameraTransform, projectionMatrix)
        
        // Project ASCII coordinates to screen space
        let overlayElements = visibleASCII.map { asciiElement in
            let screenPos = projectToScreen(asciiElement.worldPosition, camera, projectionMatrix)
            return ASCIIOverlayElement(
                character: asciiElement.character,
                screenPosition: screenPos,
                depth: asciiElement.depth,
                arxObject: asciiElement.linkedObject
            )
        }
        
        return ASCIIOverlay(elements: overlayElements)
    }
}
```

#### Spatial Anchor Management
```swift
class SpatialAnchorManager: ObservableObject {
    @Published var anchors: [ArxosSpatialAnchor] = []
    private let coreEngine: ArxosCoreEngineProtocol
    
    // Create spatial anchor linking AR position to ASCII coordinates
    func createSpatialAnchor(arTransform: matrix_float4x4, asciiCoords: Point2D, arxObject: ArxObject) {
        let anchor = ArxosSpatialAnchor(
            id: UUID().uuidString,
            arTransform: arTransform,
            asciiCoordinates: asciiCoords,
            arxObject: arxObject,
            confidence: 1.0,
            contributorID: UserManager.shared.currentUser.id
        )
        
        // Store in core engine for spatial intelligence
        coreEngine.addSpatialAnchor(anchor)
        
        // Add to AR session for tracking
        let arAnchor = ARAnchor(transform: arTransform)
        AREngine.shared.arSession.add(anchor: arAnchor)
        
        anchors.append(anchor)
    }
    
    // Validate existing spatial anchor accuracy
    func validateSpatialAnchor(_ anchor: ArxosSpatialAnchor, currentTransform: matrix_float4x4) -> ValidationResult {
        let expectedTransform = anchor.arTransform
        let actualTransform = currentTransform
        
        let positionError = distance(expectedTransform.position, actualTransform.position)
        let rotationError = angleBetween(expectedTransform.rotation, actualTransform.rotation)
        
        let accuracy = calculateAccuracyScore(positionError, rotationError)
        
        return ValidationResult(
            accuracy: accuracy,
            positionError: positionError,
            rotationError: rotationError,
            needsUpdate: accuracy < 0.8
        )
    }
}
```

### 2.5 Terminal Engine (Swift/Kotlin + C Integration)

#### Purpose
Provides consistent CLI interface across all view modes with context-aware commands, auto-completion, and real-time ArxObject interaction.

#### Core Terminal Implementation
```swift
class TerminalEngine: ObservableObject {
    @Published var outputBuffer: [TerminalLine] = []
    @Published var commandHistory: [String] = []
    @Published var currentInput: String = ""
    @Published var availableCommands: [String] = []
    
    private let coreEngine: ArxosCoreEngineProtocol
    private var commandProcessor: CommandProcessor
    
    // Execute CLI command and update output
    func executeCommand(_ command: String) {
        let trimmedCommand = command.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Add to history
        commandHistory.append(trimmedCommand)
        
        // Add command to output buffer
        outputBuffer.append(TerminalLine(
            text: "$ \(trimmedCommand)",
            type: .input
        ))
        
        // Process command through C engine
        let result = coreEngine.executeCommand(trimmedCommand)
        
        // Add result to output buffer
        outputBuffer.append(contentsOf: result.outputLines)
        
        // Handle view mode changes if command triggers them
        if let viewModeChange = result.viewModeChange {
            ViewModeController.shared.switchToMode(viewModeChange.mode, context: viewModeChange.context)
        }
        
        // Clear current input
        currentInput = ""
    }
    
    // Context-aware auto-completion
    func getCompletions(for input: String) -> [String] {
        let currentMode = ViewModeController.shared.currentMode
        let selectedObjects = ViewModeController.shared.selectedObjects
        
        return commandProcessor.getCompletions(
            input: input,
            mode: currentMode,
            selectedObjects: selectedObjects,
            buildingState: BuildingStateManager.shared.currentBuilding
        )
    }
}

struct TerminalLine {
    let text: String
    let type: LineType
    let timestamp: Date = Date()
    
    enum LineType {
        case input      // User command
        case output     // Command result
        case error      // Error message
        case system     // System notification
    }
}
```

#### Command Context Management
```swift
class CommandProcessor {
    private let coreEngine: ArxosCoreEngineProtocol
    
    func getCompletions(input: String, mode: ViewMode, selectedObjects: [ArxObject], buildingState: BuildingState) -> [String] {
        let tokens = input.split(separator: " ")
        
        guard let command = tokens.first else {
            // Return available commands for current mode
            return getCommandsForMode(mode)
        }
        
        switch String(command) {
        case "arx":
            if tokens.count == 1 {
                return ["@\(buildingState.id)"]
            } else if tokens.count == 2 {
                return getSubCommandsForMode(mode, selectedObjects)
            }
            
        case "inspect":
            return selectedObjects.map { $0.id }
            
        case "query":
            return ["SELECT * FROM", "UPDATE", "DELETE FROM"]
            
        case "navigate":
            return ["--room", "--floor", "--system", "--object"]
            
        default:
            return []
        }
    }
    
    private func getSubCommandsForMode(_ mode: ViewMode, _ selectedObjects: [ArxObject]) -> [String] {
        switch mode {
        case .ascii2D:
            return ["status", "map", "navigate", "query", "find", "zoom"]
        case .ascii3D:
            return ["view", "walk-through", "perspective", "rotate", "focus"]
        case .arCamera:
            return ["scan", "contribute", "validate", "inspect", "anchor"]
        case .terminal:
            return ["status", "query", "inspect", "update", "commit", "rollback"]
        }
    }
}
```

### 2.6 C Core Engine Integration (FFI Bridge)

#### Purpose
Provides high-performance ArxObject runtime, ASCII rendering, and spatial intelligence through Foreign Function Interface to shared C library.

#### Swift FFI Bridge
```swift
// FFI bridge to C core engine
class ArxosCoreEngine: ArxosCoreEngineProtocol {
    private let engineHandle: OpaquePointer
    
    init() throws {
        // Initialize C engine
        engineHandle = arxos_engine_create()
        guard engineHandle != nil else {
            throw ArxosEngineError.initializationFailed
        }
    }
    
    deinit {
        arxos_engine_destroy(engineHandle)
    }
    
    // ASCII rendering functions
    func renderASCII2D(_ buildingID: String, _ camera: Camera2D) -> ASCIICanvas {
        var cCamera = camera.toCStruct()
        
        let result = arxos_render_2d(engineHandle, buildingID, &cCamera)
        
        return ASCIICanvas(from: result)
    }
    
    func renderASCII3D(_ buildingID: String, _ camera: Camera3D) -> ASCIICanvas {
        var cCamera = camera.toCStruct()
        
        let result = arxos_render_3d(engineHandle, buildingID, &cCamera)
        
        return ASCIICanvas(from: result)
    }
    
    // ArxObject operations
    func executeCommand(_ command: String) -> CommandResult {
        let cString = command.cString(using: .utf8)
        let result = arxos_execute_command(engineHandle, cString)
        
        return CommandResult(from: result)
    }
    
    func getObjectAtCoords(_ x: Int, _ y: Int) -> ArxObject? {
        let result = arxos_get_object_at_coords(engineHandle, Int32(x), Int32(y))
        
        guard result != nil else { return nil }
        
        return ArxObject(from: result)
    }
    
    // LiDAR processing
    func processLiDARPoints(_ points: [Point3D], completion: @escaping ([DetectedObject]) -> Void) {
        let cPoints = points.map { $0.toCStruct() }
        
        arxos_process_lidar_async(engineHandle, cPoints, Int32(cPoints.count)) { detectedObjects, count in
            let objects = Array(UnsafeBufferPointer(start: detectedObjects, count: Int(count)))
                .map { DetectedObject(from: $0) }
            
            completion(objects)
        }
    }
}

// C function declarations
@_silgen_name("arxos_engine_create")
func arxos_engine_create() -> OpaquePointer?

@_silgen_name("arxos_engine_destroy")  
func arxos_engine_destroy(_ engine: OpaquePointer?)

@_silgen_name("arxos_render_2d")
func arxos_render_2d(_ engine: OpaquePointer?, _ buildingID: UnsafePointer<CChar>?, _ camera: UnsafeMutablePointer<CCamera2D>) -> CASCIICanvas

@_silgen_name("arxos_render_3d")
func arxos_render_3d(_ engine: OpaquePointer?, _ buildingID: UnsafePointer<CChar>?, _ camera: UnsafeMutablePointer<CCamera3D>) -> CASCIICanvas

@_silgen_name("arxos_execute_command")
func arxos_execute_command(_ engine: OpaquePointer?, _ command: UnsafePointer<CChar>?) -> CCommandResult

@_silgen_name("arxos_get_object_at_coords")
func arxos_get_object_at_coords(_ engine: OpaquePointer?, _ x: Int32, _ y: Int32) -> UnsafeMutablePointer<CArxObject>?

@_silgen_name("arxos_process_lidar_async")
func arxos_process_lidar_async(_ engine: OpaquePointer?, _ points: UnsafePointer<CPoint3D>, _ count: Int32, _ callback: @escaping (UnsafePointer<CDetectedObject>?, Int32) -> Void)
```

---

## 3. Development Phases

### Phase 1: Core Multi-Modal Framework (Months 1-2)
**Goal**: Basic view mode switching with shared terminal interface

#### Week 1-2: View Mode Controller Foundation
- [ ] Swift project setup with SwiftUI architecture
- [ ] View mode enumeration and state management  
- [ ] Basic mode switching logic without rendering
- [ ] Terminal engine foundation with command parsing
- [ ] C FFI bridge setup and basic integration testing

#### Week 3-4: 2D ASCII Renderer
- [ ] ASCII 2D rendering with touch gestures (pan, zoom, tap)
- [ ] Camera2D transformation and viewport management
- [ ] Object selection through touch coordinates
- [ ] Integration with C ASCII rendering engine
- [ ] Performance optimization for smooth 60fps scrolling

#### Week 5-6: Terminal Integration
- [ ] Context-aware terminal commands based on view mode
- [ ] Auto-completion system with building-aware suggestions
- [ ] Command history and output buffer management
- [ ] Real-time command execution with C engine
- [ ] Terminal overlay UI that works across all view modes

#### Week 7-8: Basic Mode Transitions
- [ ] Seamless switching between 2D ASCII and terminal modes
- [ ] State preservation during mode changes
- [ ] Context passing between different renderers
- [ ] Touch gesture recognition and mode triggers
- [ ] Performance testing for sub-200ms mode switches

**Deliverable**: Working 2D ASCII navigation with terminal interface and basic mode switching

### Phase 2: 3D ASCII Rendering (Months 3-4)
**Goal**: 3D perspective ASCII visualization with depth-based character selection

#### Week 9-10: 3D ASCII Renderer Foundation
- [ ] 3D camera system with rotation and perspective controls
- [ ] Depth buffer management for character selection
- [ ] 3D to 2D screen projection algorithms
- [ ] Touch gesture handling for 3D camera manipulation
- [ ] Integration with C 3D ASCII rendering engine

#### Week 11-12: Advanced 3D Rendering
- [ ] Isometric and perspective view modes
- [ ] Walk-through path generation and animation
- [ ] Room-focused rendering with context preservation  
- [ ] Material-aware character selection (walls, equipment, rooms)
- [ ] Level-of-detail optimization for complex buildings

#### Week 13-14: 3D Mode Integration
- [ ] Smooth transitions between 2D and 3D ASCII modes
- [ ] Shared object selection state across modes
- [ ] Context-aware terminal commands for 3D operations
- [ ] Performance optimization for real-time 3D ASCII rendering
- [ ] 3D navigation controls and user experience refinement

#### Week 15-16: Advanced 3D Features
- [ ] Building section views and cutaway rendering
- [ ] Floor-by-floor navigation in 3D space
- [ ] Equipment highlighting and inspection in 3D
- [ ] 3D ASCII debugging and visualization tools
- [ ] Performance benchmarking and optimization

**Deliverable**: Full 3D ASCII building visualization with smooth mode transitions

### Phase 3: AR Integration & LiDAR Scanning (Months 5-7)
**Goal**: Real-world AR overlays with live LiDAR building reconstruction

#### Week 17-20: ARKit/ARCore Foundation  
- [ ] AR session management and camera tracking
- [ ] LiDAR point cloud processing and real-time updates
- [ ] Spatial anchor creation and management system
- [ ] AR coordinate system integration with ASCII coordinates
- [ ] Basic AR overlay rendering with ASCII elements

#### Week 21-24: Live Building Reconstruction
- [ ] Real-time LiDAR to building model conversion
- [ ] Wall detection and room boundary identification
- [ ] Equipment classification from point cloud data
- [ ] Progressive building model updates during scanning
- [ ] ASCII-BIM generation from LiDAR scan data

#### Week 25-28: AR-ASCII Integration
- [ ] Real-world ASCII overlay positioning and tracking
- [ ] AR to 2D/3D ASCII mode transitions
- [ ] Spatial anchor validation and accuracy measurement
- [ ] Field contribution workflow for spatial anchoring
- [ ] AR debugging tools and calibration systems

#### Week 29-32: Advanced AR Features
- [ ] Multi-user spatial anchor sharing and validation
- [ ] AR occlusion handling and depth testing  
- [ ] Equipment inspection workflow with AR overlays
- [ ] Photo/video capture with ASCII overlay integration
- [ ] AR performance optimization and battery efficiency

**Deliverable**: Full AR integration with live building reconstruction and spatial anchoring

### Phase 4: Production Optimization (Months 8-9)
**Goal**: Performance optimization, testing, and production deployment

#### Week 33-36: Performance & Optimization
- [ ] Memory usage optimization across all view modes
- [ ] Battery life optimization for continuous AR usage
- [ ] Network sync optimization for real-time building updates
- [ ] Cache management for offline building access
- [ ] CPU/GPU performance profiling and optimization

#### Week 37-40: Testing & Quality Assurance
- [ ] Unit testing for all major components
- [ ] Integration testing for mode transitions
- [ ] Performance testing under various conditions
- [ ] User experience testing with real building data
- [ ] Stability testing for extended usage sessions

**Deliverable**: Production-ready mobile application with comprehensive testing

---

## 4. Technical Specifications

### 4.1 Performance Requirements

#### View Mode Performance
- **2D ASCII Rendering**: 60fps smooth navigation with zoom/pan
- **3D ASCII Rendering**: 30fps minimum, 60fps target for simple buildings
- **AR Mode**: 60fps camera processing, 30fps ASCII overlay updates
- **Mode Transitions**: <200ms for any mode switch
- **Terminal Operations**: <100ms command execution and response

#### Memory & Storage
- **Runtime Memory**: <500MB total app memory usage
- **Building Cache**: <100MB per cached building
- **Offline Storage**: <2GB total for frequently accessed buildings
- **LiDAR Buffer**: <50MB for real-time point cloud processing

#### Battery Performance  
- **2D/3D ASCII Mode**: >8 hours continuous usage
- **AR Scanning Mode**: >4 hours continuous LiDAR usage
- **Background Sync**: <5% battery drain per hour
- **Thermal Management**: No thermal throttling during normal usage

### 4.2 Device Requirements

#### Minimum Requirements
- **iOS**: iPhone 12 Pro (LiDAR required), iOS 15.0+
- **Android**: Flagship device with ARCore support, Android 10+
- **Storage**: 4GB available space for app and building data
- **Network**: WiFi or cellular data for building sync

#### Optimal Requirements  
- **iOS**: iPhone 14 Pro or later, iOS 16.0+
- **Android**: Latest flagship with advanced AR capabilities
- **Storage**: 16GB+ for extensive building library
- **Network**: High-speed WiFi for real-time collaboration

### 4.3 User Interface Specifications

#### Touch Interaction Standards
- **Tap**: Object selection, button activation
- **Long Press**: Context menu, detailed object inspection
- **Pan**: 2D navigation, 3D camera movement
- **Pinch**: Zoom in 2D mode, distance adjustment in 3D
- **Rotation**: 3D camera rotation, building orientation
- **Swipe Up/Down**: Mode switching triggers
- **Two-Finger Tap**: Quick terminal toggle

#### Terminal Interface Requirements
```
┌─────────────────────────────────────────┐
│ Current View Mode        [2D][3D][AR]   │
├─────────────────────────────────────────┤
│                                         │
│          ASCII RENDERING AREA           │
│              (Context-based)            │
│                                         │
├─────────────────────────────────────────┤
│ $ arx @building-47 status               │ <- Terminal always
│ > Room 300: 85% complete, 2 outlets     │    visible at bottom
│ $ _                                     │
└─────────────────────────────────────────┘
```

### 4.4 Data Synchronization

#### Real-Time Sync Requirements
- **Building Updates**: <5 second latency for remote building changes
- **Spatial Anchors**: Real-time sync across devices for collaboration
- **Command Execution**: Immediate local execution, background sync
- **Conflict Resolution**: Automatic merge for non-conflicting changes

#### Offline Capability
- **Core Features**: All viewing and navigation works offline
- **Building Cache**: Recently accessed buildings cached locally
- **Command Queue**: CLI commands queued for sync when online
- **Partial Sync**: Progressive download of building details as needed

---

## 5. Platform-Specific Implementation

### 5.1 iOS Implementation (Primary Platform)

#### SwiftUI Architecture
```swift
@main
struct ArxosApp: App {
    @StateObject private var viewModeController = ViewModeController()
    @StateObject private var buildingState = BuildingStateManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(viewModeController)
                .environmentObject(buildingState)
                .onAppear {
                    ArxosCore.shared.initialize()
                }
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var viewModeController: ViewModeController
    @EnvironmentObject var buildingState: BuildingStateManager
    
    var body: some View {
        ZStack {
            // Main view area
            switch viewModeController.currentMode {
            case .ascii2D:
                ASCII2DView()
            case .ascii3D:
                ASCII3DView()  
            case .arCamera:
                ARView()
            case .terminal:
                TerminalView()
            }
            
            // Terminal overlay (always present)
            VStack {
                Spacer()
                TerminalOverlay()
                    .frame(height: 120)
            }
        }
        .gesture(
            DragGesture()
                .onEnded { value in
                    handleModeSwipeGesture(value)
                }
        )
    }
}
```

#### iOS-Specific Optimizations
- **Metal Performance Shaders**: GPU-accelerated ASCII rendering
- **Core ML**: Equipment recognition in AR mode
- **ARKit 6**: Advanced LiDAR processing and occlusion
- **SwiftUI**: Declarative UI with smooth transitions
- **Combine**: Reactive data flow between components

### 5.2 Android Implementation (Secondary Platform)

#### Jetpack Compose Architecture
```kotlin
@Composable
fun ArxosApp() {
    val viewModeController = remember { ViewModeController() }
    val buildingState = remember { BuildingStateManager() }
    
    CompositionLocalProvider(
        LocalViewModeController provides viewModeController,
        LocalBuildingState provides buildingState
    ) {
        ArxosMainScreen()
    }
}

@Composable 
fun ArxosMainScreen() {
    val viewModeController = LocalViewModeController.current
    
    Box(modifier = Modifier.fillMaxSize()) {
        // Main content area
        when (viewModeController.currentMode.value) {
            ViewMode.ASCII2D -> ASCII2DView()
            ViewMode.ASCII3D -> ASCII3DView()
            ViewMode.ARCamera -> ARView()
            ViewMode.Terminal -> TerminalView()
        }
        
        // Terminal overlay
        TerminalOverlay(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .height(120.dp)
        )
    }
}
```

#### Android-Specific Optimizations
- **Vulkan API**: High-performance graphics rendering
- **ARCore**: Android AR framework integration
- **ML Kit**: Object detection and classification
- **Jetpack Compose**: Modern declarative UI framework
- **Room Database**: Local building data persistence

---

## 6. Development Tools & Environment

### 6.1 Development Setup

#### iOS Development Environment
```bash
# Xcode project setup
git clone https://github.com/arxos/mobile-terminal
cd mobile-terminal/ios

# Install dependencies
pod install  # CocoaPods for native dependencies
swift package resolve  # Swift Package Manager

# C library integration
make build-c-engine     # Build shared C library
make integrate-ffi      # Setup FFI bridge

# Development build
xcodebuild -workspace ArxosTerminal.xcworkspace -scheme ArxosTerminal -destination 'platform=iOS Simulator,name=iPhone 14 Pro'
```

#### Android Development Environment  
```bash
# Android Studio setup
cd mobile-terminal/android

# Gradle dependencies
./gradlew build

# NDK for C integration
export ANDROID_NDK_HOME=/path/to/ndk
make build-c-engine-android

# Development build
./gradlew assembleDebug
```

### 6.2 Testing Strategy

#### Unit Testing Requirements
- **View Controllers**: 90%+ test coverage for mode switching logic
- **ASCII Renderers**: Performance and accuracy testing
- **Terminal Engine**: Command parsing and execution testing
- **AR Integration**: Spatial anchor accuracy testing
- **C Engine Bridge**: FFI interface validation

#### Integration Testing
```swift
class ViewModeIntegrationTests: XCTestCase {
    func testModeTransitions() {
        let controller = ViewModeController()
        
        // Test 2D -> AR transition
        controller.switchToMode(.arCamera, context: TransitionContext(selectedObject: testOutlet))
        XCTAssertEqual(controller.currentMode, .arCamera)
        XCTAssertEqual(controller.terminalContext.currentPrompt, "arx @test-building ar> ")
        
        // Test AR -> 3D transition  
        controller.handleObjectSelection(testRoom, currentMode: .arCamera)
        XCTAssertEqual(controller.currentMode, .ascii3D)
    }
    
    func testPerformanceRequirements() {
        measure {
            // Mode switch should complete in <200ms
            controller.switchToMode(.ascii3D, context: nil)
        }
        // Assert performance benchmark
    }
}
```

#### Field Testing Requirements
- **Building Scanning**: Test with real HCPS buildings
- **AR Accuracy**: Validate spatial anchor precision
- **Battery Performance**: Extended usage testing
- **Network Conditions**: Offline/poor connectivity testing
- **User Experience**: Field staff usability testing

---

## 7. Deployment & Distribution

### 7.1 App Store Requirements

#### iOS App Store
- **Target Audience**: Business/Productivity category
- **Age Rating**: 4+ (no restricted content)
- **Device Requirements**: iPhone 12 Pro+ (LiDAR required)
- **Privacy**: Comprehensive privacy policy for camera/location usage
- **App Review**: Detailed explanation of LiDAR usage for building scanning

#### Google Play Store
- **Target Audience**: Business/Tools category  
- **Content Rating**: Everyone (business application)
- **Device Requirements**: ARCore-capable Android devices
- **Permissions**: Camera, storage, location access explanations
- **Play Console**: Alpha/beta testing with HCPS pilot users

### 7.2 Distribution Strategy

#### Phase 1: Closed Beta (HCPS Pilot)
- **TestFlight**: iOS distribution to HCPS facilities staff
- **Google Play Console**: Android internal testing track
- **Device Management**: Corporate device deployment
- **Training**: On-site training for facilities teams

#### Phase 2: Enterprise Release
- **Volume Purchase Program**: iOS enterprise distribution
- **Google Play for Business**: Android enterprise deployment  
- **Custom Distribution**: Direct enterprise customer deployment
- **Support**: Dedicated enterprise customer success

#### Phase 3: Public Release
- **App Store**: Public availability with freemium model
- **Marketing**: Developer/facilities management community outreach
- **Documentation**: Comprehensive user guides and tutorials
- **Community**: Open-source components and developer ecosystem

---

## 8. Success Metrics & KPIs

### 8.1 Technical Performance Metrics
- **Mode Switch Performance**: <200ms for 95% of transitions
- **ASCII Rendering**: 60fps for 2D mode, 30fps for 3D mode  
- **AR Performance**: 60fps camera, 30fps overlays, <100ms spatial queries
- **Memory Usage**: <500MB peak memory usage during normal operation
- **Battery Life**: >4 hours AR scanning, >8 hours ASCII navigation

### 8.2 User Experience Metrics
- **Task Completion**: >90% success rate for building navigation tasks
- **Learning Curve**: <30 minutes to proficiency for facilities staff
- **Error Rate**: <5% user errors during typical building operations
- **Mode Usage**: Balanced usage across 2D/3D/AR modes (no single mode >70%)
- **Terminal Adoption**: >80% of users regularly use terminal commands

### 8.3 Business Impact Metrics
- **HCPS Pilot**: 100% of pilot buildings successfully mapped and operational
- **Field Efficiency**: >50% reduction in time to find building equipment
- **Data Quality**: >95% accuracy for AR spatial anchor validation
- **User Satisfaction**: >4.5/5 rating from facilities management users
- **Enterprise Adoption**: 10+ enterprise customers within 6 months of release

---

## 9. Risk Assessment & Mitigation

### 9.1 Technical Risks

#### Performance Limitations
- **Risk**: ASCII rendering doesn't achieve target framerate on older devices
- **Mitigation**: Adaptive quality settings and level-of-detail optimization
- **Fallback**: Simplified ASCII character sets for performance-constrained devices

#### AR Accuracy Issues
- **Risk**: Spatial anchors drift or become inaccurate over time
- **Mitigation**: Multi-user validation system and confidence scoring
- **Fallback**: Manual spatial anchor correction tools and GPS fallback

#### Battery Life Concerns
- **Risk**: AR mode drains battery too quickly for field use
- **Mitigation**: Aggressive power management and selective LiDAR usage
- **Fallback**: Extended battery accessories and power-saving modes

### 9.2 Platform Risks

#### iOS/Android API Changes  
- **Risk**: ARKit/ARCore updates break compatibility
- **Mitigation**: Multiple API version support and gradual migration
- **Fallback**: Fallback to older API versions with reduced functionality

#### App Store Approval
- **Risk**: App store policies restrict LiDAR or building scanning usage
- **Mitigation**: Clear privacy policies and business use case explanation
- **Fallback**: Enterprise distribution bypassing public app stores

### 9.3 User Adoption Risks

#### Learning Curve  
- **Risk**: Terminal interface too complex for non-technical users
- **Mitigation**: Progressive disclosure and contextual help system
- **Fallback**: Simplified GUI wrapper over terminal commands

#### Device Compatibility
- **Risk**: Limited LiDAR device availability restricts user base
- **Mitigation**: Fallback modes for non-LiDAR devices
- **Fallback**: Manual measurement tools and photo-based validation

---

## 10. Next Steps & Implementation Timeline

### Week 1-2: Project Initialization
- [ ] **Team Assembly**: Hire iOS/Android developers with AR experience
- [ ] **Development Environment**: Setup Xcode/Android Studio with C integration
- [ ] **Architecture Review**: Final technical architecture validation
- [ ] **HCPS Partnership**: Finalize pilot program requirements and access

### Week 3-4: Foundation Development
- [ ] **C Engine Integration**: Setup FFI bridge and basic ASCII rendering
- [ ] **View Mode Framework**: Implement core mode switching architecture
- [ ] **Terminal Engine**: Basic command parsing and execution
- [ ] **UI Framework**: SwiftUI/Compose foundation with ASCII rendering

### Month 2: Core Features
- [ ] **2D ASCII Navigation**: Complete touch-based building navigation
- [ ] **Terminal Integration**: Context-aware commands and auto-completion
- [ ] **Performance Optimization**: Meet framerate and responsiveness targets
- [ ] **HCPS Building Data**: Load and render real school building data

### Month 3: 3D ASCII Implementation
- [ ] **3D Rendering Engine**: Perspective ASCII with depth-based characters
- [ ] **Camera Controls**: 3D navigation and view manipulation  
- [ ] **Mode Transitions**: Smooth switching between 2D/3D modes
- [ ] **Building Visualization**: Complete 3D building exploration

### Month 6: AR Integration Complete
- [ ] **AR Foundation**: ARKit/ARCore with LiDAR processing
- [ ] **Live Scanning**: Real-time building reconstruction
- [ ] **Spatial Anchoring**: AR-to-ASCII coordinate mapping
- [ ] **Field Testing**: HCPS pilot testing and validation

### Month 9: Production Release
- [ ] **Performance Optimization**: Battery life and rendering optimization
- [ ] **Enterprise Features**: Multi-user collaboration and data sync
- [ ] **App Store Submission**: iOS/Android store approval process
- [ ] **Production Deployment**: HCPS full deployment and training

This comprehensive architecture provides the technical foundation for building the revolutionary multi-modal mobile terminal that seamlessly integrates 2D ASCII navigation, 3D building visualization, and real-world AR overlays into a unified infrastructure-as-code experience.