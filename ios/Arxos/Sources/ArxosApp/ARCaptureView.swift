import SwiftUI
import simd
#if canImport(ArxosCore)
import ArxosCore
#endif

#if canImport(ARKit) && canImport(RealityKit) && !os(macOS)
import ARKit
import RealityKit

/// AR view that tracks the camera and overlays nearby annotation labels only.
/// Deliberately not a general 3D model viewer.
struct ARCaptureView: UIViewRepresentable {
    @ObservedObject var session: BuildingSession

    func makeUIView(context: Context) -> ARView {
        let view = ARView(frame: .zero)
        view.automaticallyConfigureSession = false

        let config = ARWorldTrackingConfiguration()
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
            config.sceneReconstruction = .mesh
        }
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            config.frameSemantics.insert(.sceneDepth)
        }
        config.planeDetection = [.horizontal, .vertical]
        view.session.delegate = context.coordinator
        view.session.run(config)
        context.coordinator.arView = view
        context.coordinator.session = session
        return view
    }

    func updateUIView(_ uiView: ARView, context: Context) {
        context.coordinator.session = session
        context.coordinator.syncOverlays()
    }

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    final class Coordinator: NSObject, ARSessionDelegate {
        weak var arView: ARView?
        var session: BuildingSession?
        private var anchorEntities: [String: AnchorEntity] = [:]

        func session(_ session: ARSession, didUpdate frame: ARFrame) {
            let t = frame.camera.transform.columns.3
            let pose = SIMD3<Float>(t.x, t.y, t.z)
            Task { @MainActor in
                self.session?.updateCameraPose(pose)
                // Throttle overlay refresh via occasional updates
                if Int(frame.timestamp * 2) % 2 == 0 {
                    self.session?.refreshNearby()
                    self.syncOverlays()
                }
            }
        }

        @MainActor
        func syncOverlays() {
            guard let arView, let session else { return }
            let wanted = Set(session.nearbyAnnotations.map(\.cid))

            // Remove stale
            for (cid, anchor) in anchorEntities where !wanted.contains(cid) {
                arView.scene.removeAnchor(anchor)
                anchorEntities.removeValue(forKey: cid)
            }

            // Add / update annotation billboards (text only — no mesh viewer)
            for ann in session.nearbyAnnotations {
                let position = SIMD3<Float>(Float(ann.x), Float(ann.y), Float(ann.z))
                if let existing = anchorEntities[ann.cid] {
                    existing.position = position
                    continue
                }
                let anchor = AnchorEntity(world: position)
                if let textMesh = try? MeshResource.generateText(
                    ann.text,
                    extrusionDepth: 0.001,
                    font: .systemFont(ofSize: 0.08),
                    containerFrame: .zero,
                    alignment: .center,
                    lineBreakMode: .byWordWrapping
                ) {
                    let material = SimpleMaterial(color: .systemYellow, isMetallic: false)
                    let entity = ModelEntity(mesh: textMesh, materials: [material])
                    entity.position = SIMD3(0, 0.05, 0)
                    anchor.addChild(entity)
                } else {
                    // Fallback sphere marker
                    let mesh = MeshResource.generateSphere(radius: 0.03)
                    let material = SimpleMaterial(color: .systemYellow, isMetallic: false)
                    anchor.addChild(ModelEntity(mesh: mesh, materials: [material]))
                }
                arView.scene.addAnchor(anchor)
                anchorEntities[ann.cid] = anchor
            }
        }
    }
}
#else

/// Placeholder when ARKit is unavailable (macOS SPM demo / Simulator without AR).
struct ARCaptureView: View {
    @ObservedObject var session: BuildingSession

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color.black.opacity(0.85), Color.blue.opacity(0.35)],
                startPoint: .top,
                endPoint: .bottom
            )
            VStack(spacing: 12) {
                Text("AR Preview (shim)")
                    .font(.headline)
                    .foregroundStyle(.white)
                Text("Camera \(fmt(session.cameraPose))")
                    .font(.caption.monospaced())
                    .foregroundStyle(.white.opacity(0.8))
                ForEach(session.nearbyAnnotations) { ann in
                    HStack {
                        Image(systemName: "mappin.circle.fill")
                            .foregroundStyle(.yellow)
                        Text(ann.text)
                            .foregroundStyle(.white)
                        Spacer()
                        Text(String(format: "%.1fm", ann.distanceM))
                            .foregroundStyle(.white.opacity(0.7))
                            .font(.caption.monospaced())
                    }
                    .padding(8)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 8))
                }
                if session.nearbyAnnotations.isEmpty {
                    Text("No annotations in range")
                        .foregroundStyle(.white.opacity(0.6))
                        .font(.footnote)
                }
            }
            .padding()
        }
    }

    private func fmt(_ p: SIMD3<Float>) -> String {
        String(format: "[%.2f, %.2f, %.2f]", p.x, p.y, p.z)
    }
}
#endif
