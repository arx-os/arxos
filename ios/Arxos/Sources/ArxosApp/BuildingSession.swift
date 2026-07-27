import Foundation
import Combine
import simd
import ArxosCore

/// Observable session state for one building repository on device.
@MainActor
final class BuildingSession: ObservableObject {
    @Published var summary: BuildingSummary?
    @Published var lastCapture: CapturePutResult?
    @Published var lastCommit: CommitSummary?
    @Published var nearbyAnnotations: [AnnotationOverlay] = []
    @Published var status: String = "Idle"
    @Published var cameraPose: SIMD3<Float> = .zero
    @Published var annotationDraft: String = ""
    @Published var isTracking: Bool = false

    let storePath: String

    init(storePath: String = ArxosCore.defaultStorePath()) {
        self.storePath = storePath
    }

    var buildingId: String? { summary?.buildingId }

    func initBuilding(name: String) {
        status = "Initializing…"
        let s = ArxosCore.initBuilding(storePath: storePath, name: name)
        summary = s
        status = "Building \(s.buildingId.prefix(12))… ready"
        refreshNearby()
    }

    func openBuilding(id: String) {
        status = "Opening…"
        let s = ArxosCore.openBuilding(storePath: storePath, buildingId: id)
        summary = s
        status = "Opened \(s.buildingId.prefix(12))… head=\(s.headRoot?.prefix(16) ?? "none")…"
        refreshNearby()
    }

    func listBuildings() -> [BuildingSummary] {
        ArxosCore.listBuildings(storePath: storePath)
    }

    func updateCameraPose(_ position: SIMD3<Float>) {
        cameraPose = position
    }

    /// Capture a space at the current camera pose (RoomPlan result or mock).
    func captureSpace(name: String?) {
        guard let id = buildingId else {
            status = "No building open"
            return
        }
        let p = cameraPose
        let r = ArxosCore.captureSpace(
            storePath: storePath, buildingId: id, name: name,
            x: Double(p.x), y: Double(p.y), z: Double(p.z)
        )
        lastCapture = r
        summary = ArxosCore.openBuilding(storePath: storePath, buildingId: id)
        status = "Space \(r.cid.prefix(18))…"
        refreshNearby()
    }

    /// Capture annotation text at current camera pose.
    func captureAnnotation() {
        guard let id = buildingId else {
            status = "No building open"
            return
        }
        let text = annotationDraft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            status = "Annotation text empty"
            return
        }
        let p = cameraPose
        let r = ArxosCore.captureAnnotation(
            storePath: storePath, buildingId: id, text: text,
            x: Double(p.x), y: Double(p.y), z: Double(p.z)
        )
        lastCapture = r
        annotationDraft = ""
        summary = ArxosCore.openBuilding(storePath: storePath, buildingId: id)
        status = "Annotation \(r.cid.prefix(18))…"
        refreshNearby()
    }

    /// Ingest a LiDAR / RoomPlan point sample as PointCloudChunk.
    func capturePointCloud(pointsXYZ: [SIMD3<Float>], pose: SIMD3<Float>? = nil) {
        guard let id = buildingId else {
            status = "No building open"
            return
        }
        var data = Data(capacity: pointsXYZ.count * 12)
        for p in pointsXYZ {
            var x = p.x, y = p.y, z = p.z
            withUnsafeBytes(of: &x) { data.append(contentsOf: $0) }
            withUnsafeBytes(of: &y) { data.append(contentsOf: $0) }
            withUnsafeBytes(of: &z) { data.append(contentsOf: $0) }
        }
        let origin = pose ?? cameraPose
        let r = ArxosCore.capturePointCloud(
            storePath: storePath, buildingId: id, pointsXYZF32LE: data,
            x: Double(origin.x), y: Double(origin.y), z: Double(origin.z)
        )
        lastCapture = r
        summary = ArxosCore.openBuilding(storePath: storePath, buildingId: id)
        status = "PointCloud \(pointsXYZ.count) pts \(r.cid.prefix(16))…"
    }

    /// Simulate a full RoomPlan-like capture (no device LiDAR required).
    func simulateRoomCapture(roomName: String = "Captured Room") {
        guard buildingId != nil else {
            status = "No building open"
            return
        }
        // Place camera at a synthetic pose if still at origin.
        if cameraPose == .zero {
            cameraPose = SIMD3(1.0, 1.5, 2.0)
        }
        captureSpace(name: roomName)

        var pts: [SIMD3<Float>] = []
        for i in 0..<8 {
            for j in 0..<8 {
                pts.append(SIMD3(Float(i) * 0.25, 0, Float(j) * 0.25))
            }
        }
        capturePointCloud(pointsXYZ: pts, pose: SIMD3(0, 0, 0))

        if annotationDraft.isEmpty {
            annotationDraft = "Room note @ \(roomName)"
        }
        captureAnnotation()
        status = "Simulated capture staged (pending commit)"
    }

    func commit(message: String = "device capture") {
        guard let id = buildingId else {
            status = "No building open"
            return
        }
        let r = ArxosCore.commitBuilding(
            storePath: storePath, buildingId: id, message: message
        )
        lastCommit = r
        summary = ArxosCore.openBuilding(storePath: storePath, buildingId: id)
        status = "Committed root \(r.rootCid.prefix(18))… (\(r.objectCount) objects)"
        refreshNearby()
    }

    func refreshNearby(radiusM: Double = 15) {
        guard let id = buildingId else {
            nearbyAnnotations = []
            return
        }
        let p = cameraPose
        nearbyAnnotations = ArxosCore.annotationsNear(
            storePath: storePath, buildingId: id,
            x: Double(p.x), y: Double(p.y), z: Double(p.z),
            radiusM: radiusM
        )
    }
}
