import SwiftUI
import ARKit
import RealityKit
import Combine

struct ARViewContainer: UIViewRepresentable {
    @Binding var detectedEquipment: [DetectedEquipment]
    @Binding var isScanning: Bool
    var loadedModel: String? = nil // Building name to load model for
    
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
        
        // Load AR model if specified
        if let buildingName = loadedModel {
            loadModelForBuilding(arView: arView, buildingName: buildingName)
        }
        
        return arView
    }
    
    func updateUIView(_ uiView: ARView, context: Context) {
        // Update AR view if model changed
        if let buildingName = loadedModel {
            // Check if model already loaded
            let anchorName = "building_\(buildingName)_model"
            if uiView.scene.anchors.first(where: { $0.name == anchorName }) == nil {
                loadModelForBuilding(arView: uiView, buildingName: buildingName)
            }
        }
    }
    
    func makeCoordinator() -> ARCoordinator {
        ARCoordinator(self)
    }
    
    /// Load AR model for a building
    private func loadModelForBuilding(arView: ARView, buildingName: String) {
        // Look for USDZ file first (ARKit preferred)
        let usdzPath = Bundle.main.path(forResource: buildingName, ofType: "usdz")
        if let usdzPath = usdzPath {
            loadUSDZModel(arView: arView, filePath: usdzPath, buildingName: buildingName)
            return
        }
        
        // Fallback to glTF
        let gltfPath = Bundle.main.path(forResource: buildingName, ofType: "gltf")
        if let gltfPath = gltfPath {
            loadGLTFModel(arView: arView, filePath: gltfPath, buildingName: buildingName)
            return
        }
        
        print("⚠️ No AR model found for building: \(buildingName)")
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
        // For now, log that it was requested
        print("⚠️ glTF loading not yet implemented. Convert \(buildingName).gltf to USDZ for best ARKit support.")
    }
}

class ARCoordinator: NSObject, ARSessionDelegate {
    var parent: ARViewContainer
    
    init(_ parent: ARViewContainer) {
        self.parent = parent
    }
    
    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        // Process AR frame for equipment detection
        // This is where we would integrate with the Rust core for equipment detection
    }
    
    func session(_ session: ARSession, didAdd anchors: [ARAnchor]) {
        // Handle new AR anchors (detected planes, objects, etc.)
        for anchor in anchors {
            if let planeAnchor = anchor as? ARPlaneAnchor {
                // Handle plane detection
                handlePlaneDetection(planeAnchor)
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
}

// MARK: - Equipment Detection
extension ARCoordinator {
    func detectEquipment(in frame: ARFrame) {
        // This is where we would integrate with the Rust core for equipment detection
        // For now, we'll simulate equipment detection
        
        DispatchQueue.main.async {
            // Simulate equipment detection
            let simulatedEquipment = DetectedEquipment(
                name: "VAV-301",
                type: "HVAC",
                position: Position3D(x: Double(0), y: Double(0), z: Double(-1)),
                status: "Detected",
                icon: "fan"
            )
            
            if !self.parent.detectedEquipment.contains(where: { $0.name == simulatedEquipment.name }) {
                self.parent.detectedEquipment.append(simulatedEquipment)
            }
        }
    }
}
