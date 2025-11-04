import SwiftUI
import ARKit
import RealityKit
import Combine
import UIKit

struct ARViewContainer: UIViewRepresentable {
    @Binding var detectedEquipment: [DetectedEquipment]
    @Binding var isScanning: Bool
    var loadedModel: String? = nil // Building name to load model for
    var onEquipmentPlaced: ((DetectedEquipment) -> Void)? = nil // Callback for equipment placement
    
    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        
        // Configure AR session
        let configuration = ARWorldTrackingConfiguration()
        configuration.planeDetection = [.horizontal, .vertical]
        configuration.environmentTexturing = .automatic
        
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            configuration.frameSemantics = .sceneDepth
        }
        
        arView.session.run(configuration)
        
        // Set up AR session delegate
        arView.session.delegate = context.coordinator
        
        // Store ARView reference in coordinator for model loading
        context.coordinator.arView = arView
        
        // Set up tap gesture for equipment placement
        context.coordinator.setupTapGesture(on: arView)
        
        // Store placement callback
        context.coordinator.onEquipmentPlaced = onEquipmentPlaced
        
        // Load AR model if specified
        if let buildingName = loadedModel {
            loadModelForBuilding(arView: arView, buildingName: buildingName, coordinator: context.coordinator)
        }
        
        return arView
    }
    
    func updateUIView(_ uiView: ARView, context: Context) {
        // Update coordinator's ARView reference
        context.coordinator.arView = uiView
        
        // Update AR view if model changed
        if let buildingName = loadedModel {
            // Check if model already loaded
            let anchorName = "building_\(buildingName)_model"
            if uiView.scene.anchors.first(where: { $0.name == anchorName }) == nil {
                // Only load if not already loading
                if !context.coordinator.isLoadingModel {
                    loadModelForBuilding(arView: uiView, buildingName: buildingName, coordinator: context.coordinator)
                }
            }
        }
    }
    
    func makeCoordinator() -> ARCoordinator {
        ARCoordinator(self)
    }
    
    /// Load AR model for a building using FFI
    private func loadModelForBuilding(arView: ARView, buildingName: String, coordinator: ARCoordinator) {
        // Set loading state
        coordinator.isLoadingModel = true
        
        // Use FFI to export and load model
        let ffi = ArxOSCoreFFI()
        
        // Prefer USDZ for ARKit (best compatibility)
        ffi.loadARModel(buildingName: buildingName, format: "usdz") { result in
            DispatchQueue.main.async {
                coordinator.isLoadingModel = false
                
                switch result {
                case .success(let modelResult):
                    print("✅ AR model loaded: \(modelResult.filePath) (\(modelResult.fileSize) bytes)")
                    self.loadModelFromPath(arView: arView, filePath: modelResult.filePath, buildingName: buildingName, coordinator: coordinator)
                    
                case .failure(let error):
                    print("❌ Failed to load AR model via FFI: \(error.localizedDescription)")
                    // Fallback to Bundle.main if FFI fails
                    self.fallbackToBundleModel(arView: arView, buildingName: buildingName)
                }
            }
        }
    }
    
    /// Load model from file path (from FFI export)
    private func loadModelFromPath(arView: ARView, filePath: String, buildingName: String, coordinator: ARCoordinator) {
        let url = URL(fileURLWithPath: filePath)
        let anchorName = "building_\(buildingName)_model"
        
        // Remove existing anchor if present
        if let existingAnchor = arView.scene.anchors.first(where: { $0.name == anchorName }) {
            arView.scene.removeAnchor(existingAnchor)
        }
        
        // Cancel any existing load operation
        coordinator.modelLoadCancellable?.cancel()
        
        // Create new anchor at origin
        let anchor = AnchorEntity(world: simd_float3(x: 0, y: 0, z: 0))
        anchor.name = anchorName
        
        // Load entity asynchronously and store cancellable
        coordinator.modelLoadCancellable = Entity.loadAsync(contentsOf: url).sink(
            receiveCompletion: { completion in
                if case .failure(let error) = completion {
                    print("❌ Failed to load model entity: \(error.localizedDescription)")
                }
                coordinator.modelLoadCancellable?.cancel()
                coordinator.modelLoadCancellable = nil
            },
            receiveValue: { entity in
                anchor.addChild(entity)
                arView.scene.addAnchor(anchor)
                print("✅ Successfully loaded AR model for: \(buildingName)")
                coordinator.modelLoadCancellable?.cancel()
                coordinator.modelLoadCancellable = nil
            }
        )
    }
    
    /// Fallback to Bundle.main model loading (for backward compatibility)
    private func fallbackToBundleModel(arView: ARView, buildingName: String) {
        // Look for USDZ file first (ARKit preferred)
        if let usdzPath = Bundle.main.path(forResource: buildingName, ofType: "usdz") {
            loadUSDZModel(arView: arView, filePath: usdzPath, buildingName: buildingName)
            return
        }
        
        // Fallback to glTF
        if let gltfPath = Bundle.main.path(forResource: buildingName, ofType: "gltf") {
            loadGLTFModel(arView: arView, filePath: gltfPath, buildingName: buildingName)
            return
        }
        
        print("⚠️ No AR model found for building: \(buildingName) (neither FFI nor Bundle)")
    }
    
    /// Load USDZ model using RealityKit
    private func loadUSDZModel(arView: ARView, filePath: String, buildingName: String) {
        let url = URL(fileURLWithPath: filePath)
        
        // Create anchor at origin
        let anchor = AnchorEntity(world: simd_float3(x: 0, y: 0, z: 0))
        anchor.name = "building_\(buildingName)_model"
        
        // Load USDZ entity
        Entity.loadAsync(contentsOf: url).sink(receiveCompletion: { completion in
            if case .failure(let error) = completion {
                print("Failed to load USDZ model: \(error)")
            }
        }, receiveValue: { entity in
            anchor.addChild(entity)
            arView.scene.addAnchor(anchor)
            print("✅ Successfully loaded USDZ model for: \(buildingName)")
        })
    }
    
    /// Load glTF model (basic support, ARKit prefers USDZ)
    private func loadGLTFModel(arView: ARView, filePath: String, buildingName: String) {
        // ARKit doesn't natively support glTF, would need custom parser or conversion
        // Log model load request
        print("⚠️ glTF loading not yet implemented. Convert \(buildingName).gltf to USDZ for best ARKit support.")
    }
}

class ARCoordinator: NSObject, ARSessionDelegate {
    var parent: ARViewContainer
    var arView: ARView?
    var isLoadingModel: Bool = false
    var modelLoadCancellable: AnyCancellable?
    var tapGestureRecognizer: UITapGestureRecognizer?
    var onEquipmentPlaced: ((DetectedEquipment) -> Void)?
    var placedEquipmentAnchors: [String: AnchorEntity] = [:] // Track visual markers
    
    init(_ parent: ARViewContainer) {
        self.parent = parent
    }
    
    deinit {
        // Clean up any pending cancellables
        modelLoadCancellable?.cancel()
        // Remove tap gesture if needed
        if let tapGesture = tapGestureRecognizer {
            arView?.removeGestureRecognizer(tapGesture)
        }
    }
    
    private var lastDetectionTime: TimeInterval = 0
    
    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        // Process AR frame for equipment detection
        // Only process frames periodically to avoid performance issues
        if parent.isScanning {
            // Process approximately once per second
            let currentTime = frame.timestamp
            if currentTime - lastDetectionTime >= 1.0 {
                lastDetectionTime = currentTime
                detectEquipment(in: frame)
            }
        }
    }
    
    func session(_ session: ARSession, didAdd anchors: [ARAnchor]) {
        // Handle new AR anchors (detected planes, objects, etc.)
        for anchor in anchors {
            if let planeAnchor = anchor as? ARPlaneAnchor {
                // Handle plane detection for equipment placement surfaces
                handlePlaneDetection(planeAnchor)
            } else if let objectAnchor = anchor as? ARObjectAnchor {
                // Handle ARKit object detection (requires ARReferenceObject configuration)
                processDetectedObject(objectAnchor)
            }
        }
    }
    
    func session(_ session: ARSession, didUpdate anchors: [ARAnchor]) {
        // Handle updated AR anchors
    }
    
    private func handlePlaneDetection(_ planeAnchor: ARPlaneAnchor) {
        // Process detected planes for equipment placement
        // This would integrate with spatial processing from Rust core
    }
    
    // MARK: - Tap Gesture Handling
    func setupTapGesture(on arView: ARView) {
        let tapGesture = UITapGestureRecognizer(
            target: self,
            action: #selector(handleTap(_:))
        )
        arView.addGestureRecognizer(tapGesture)
        self.tapGestureRecognizer = tapGesture
        self.arView = arView
    }
    
    @objc func handleTap(_ gesture: UITapGestureRecognizer) {
        guard let arView = arView else { return }
        
        // Only allow tap-to-place when scanning
        guard parent.isScanning else { return }
        
        let location = gesture.location(in: arView)
        
        // Perform hit test to find real-world position
        // Use raycast for better accuracy (iOS 13+)
        if #available(iOS 13.0, *) {
            let raycastResults = arView.raycast(
                from: location,
                allowing: .estimatedPlane,
                alignment: .any
            )
            
            guard let firstResult = raycastResults.first else {
                print("⚠️ No plane detected at tap location")
                return
            }
            
            // Extract position from raycast result
            let worldTransform = firstResult.worldTransform
            let position = Position3D(
                x: Double(worldTransform.columns.3.x),
                y: Double(worldTransform.columns.3.y),
                z: Double(worldTransform.columns.3.z)
            )
            
            // Show equipment placement UI
            showEquipmentPlacementDialog(at: position, in: arView)
            
        } else {
            // Fallback for older iOS versions - use hit test
            let hitTestResults = arView.hitTest(location, types: [.estimatedHorizontalPlane, .existingPlane])
            
            guard let firstResult = hitTestResults.first else {
                print("⚠️ No plane detected at tap location")
                return
            }
            
            let worldTransform = firstResult.worldTransform
            let position = Position3D(
                x: Double(worldTransform.columns.3.x),
                y: Double(worldTransform.columns.3.y),
                z: Double(worldTransform.columns.3.z)
            )
            
            showEquipmentPlacementDialog(at: position, in: arView)
        }
    }
    
    private func showEquipmentPlacementDialog(at position: Position3D, in arView: ARView) {
        // Create visual marker at tap location to show user where equipment will be placed
        addPlacementMarker(at: position, in: arView)
        
        // Notify parent to show equipment placement UI via callback
        DispatchQueue.main.async {
            // Create initial equipment data with tap position
            // User will fill in name and type in the dialog
            let initialEquipment = DetectedEquipment(
                name: "New Equipment",
                type: "Unknown",
                position: position,
                confidence: 1.0,
                detectionMethod: "Tap-to-Place",
                status: "Placed",
                icon: "plus.circle"
            )
            
            // Call the placement callback to show dialog
            self.onEquipmentPlaced?(initialEquipment)
        }
    }
    
    private func addPlacementMarker(at position: Position3D, in arView: ARView) {
        // Create a simple 3D marker (sphere) at the placement location
        let markerName = "placement_marker_\(UUID().uuidString)"
        
        // Remove existing marker if any
        if let existingMarker = placedEquipmentAnchors[markerName] {
            arView.scene.removeAnchor(existingMarker)
        }
        
        // Create anchor at position
        let anchor = AnchorEntity(world: simd_float3(
            Float(position.x),
            Float(position.y),
            Float(position.z)
        ))
        anchor.name = markerName
        
        // Create a simple sphere marker (using RealityKit)
        let sphere = MeshResource.generateSphere(radius: 0.05)
        let material = SimpleMaterial(color: UIColor.systemBlue, roughness: 0.5, isMetallic: false)
        let markerEntity = ModelEntity(mesh: sphere, materials: [material])
        
        anchor.addChild(markerEntity)
        arView.scene.addAnchor(anchor)
        
        // Store anchor for later removal
        placedEquipmentAnchors[markerName] = anchor
        
        // Animate marker appearance
        markerEntity.scale = [0, 0, 0]
        markerEntity.move(to: anchor.transform, relativeTo: nil, duration: 0.3)
        markerEntity.scale = [1, 1, 1]
        
        // Remove marker after 3 seconds (or when equipment is confirmed)
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            if let marker = self.placedEquipmentAnchors[markerName] {
                markerEntity.move(to: anchor.transform, relativeTo: nil, duration: 0.3)
                markerEntity.scale = [0, 0, 0]
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                    arView.scene.removeAnchor(marker)
                    self.placedEquipmentAnchors.removeValue(forKey: markerName)
                }
            }
        }
    }
    
    func removePlacementMarker(at position: Position3D) {
        // Find and remove marker closest to position
        let threshold: Float = 0.1 // 10cm threshold
        var closestMarker: (String, AnchorEntity)? = nil
        var closestDistance: Float = Float.greatestFiniteMagnitude
        
        for (name, anchor) in placedEquipmentAnchors {
            let distance = simd_distance(
                anchor.position(relativeTo: nil),
                simd_float3(Float(position.x), Float(position.y), Float(position.z))
            )
            if distance < threshold && distance < closestDistance {
                closestDistance = distance
                closestMarker = (name, anchor)
            }
        }
        
        if let (name, marker) = closestMarker {
            arView?.scene.removeAnchor(marker)
            placedEquipmentAnchors.removeValue(forKey: name)
        }
    }
}

// MARK: - Equipment Detection
extension ARCoordinator {
    func detectEquipment(in frame: ARFrame) {
        // Equipment detection from AR frames
        // This method processes AR frames to detect potential equipment using ARKit capabilities
        
        guard parent.isScanning else { return }
        
        // Analyze scene depth for equipment-like structures (iOS 14+)
        if #available(iOS 14.0, *), frame.sceneDepth != nil {
            analyzeSceneDepth(frame: frame)
        }
        
        // Note: ARKit object detection requires ARReferenceObject configuration
        // Object anchors are delivered via session(_:didAdd:) delegate method
        // See session(_:didAdd:) for handling ARObjectAnchor instances
    }
    
    private func processDetectedObject(_ object: ARObjectAnchor) {
        // Process ARKit detected objects (requires ARReferenceObject configuration)
        // This is used when ARKit object detection is configured with equipment reference objects
        
        let transform = object.transform
        let position = Position3D(
            x: Double(transform.columns.3.x),
            y: Double(transform.columns.3.y),
            z: Double(transform.columns.3.z)
        )
        
        // Only add if not already detected (avoid duplicates)
        let threshold: Double = 0.5 // 50cm threshold
        let existing = parent.detectedEquipment.first { eq in
            abs(eq.position.x - position.x) < threshold &&
            abs(eq.position.y - position.y) < threshold &&
            abs(eq.position.z - position.z) < threshold
        }
        
        if existing == nil {
            // Use reference object name if available, otherwise generic name
            let equipmentName = object.referenceObject.name ?? "Detected Equipment"
            
            let detectedEquipment = DetectedEquipment(
                name: equipmentName,
                type: "Unknown", // Could be derived from reference object metadata
                position: position,
                confidence: 0.8, // ARKit object detection has high confidence
                detectionMethod: "ARKit Object Detection",
                status: "Detected",
                icon: "cube"
            )
            
            DispatchQueue.main.async {
                self.parent.detectedEquipment.append(detectedEquipment)
            }
        }
    }
    
    @available(iOS 14.0, *)
    private func analyzeSceneDepth(frame: ARFrame) {
        // Analyze scene depth data for equipment-like structures
        // Scene depth analysis provides depth maps that can be used for:
        // 1. Point cloud generation for 3D structure detection
        // 2. Shape recognition algorithms for equipment classification
        // 3. Integration with Rust core for ML-based equipment identification
        
        // Current implementation focuses on tap-to-place gesture for equipment placement
        // See handleTap method for user-initiated placement
        // Future enhancement: Implement depth-based automatic equipment detection
        
        // Access scene depth data via frame.sceneDepth?.depthMap
        // Process depth map to identify equipment-like structures
    }
}
