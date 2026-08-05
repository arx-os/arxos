import Foundation
import Combine
import simd
#if canImport(ArxosCore)
import ArxosCore
#endif

/// Observable session state for one building repository on device.
@MainActor
final class BuildingSession: ObservableObject {
    private static let lastBuildingKey = "arxos.lastBuildingId"

    @Published var summary: BuildingSummary?
    @Published var lastCapture: CapturePutResult?
    @Published var lastCommit: CommitSummary?
    @Published var nearbyAnnotations: [AnnotationOverlay] = []
    @Published var status: String = "Idle"
    @Published var lastError: String?
    @Published var cameraPose: SIMD3<Float> = .zero
    @Published var annotationDraft: String = ""
    @Published var isTracking: Bool = false
    /// True while a real RoomPlan scan is running (AR overlay paused).
    @Published var isRoomPlanActive: Bool = false
    /// True when last ingest is staged but not yet committed.
    @Published var hasUncommittedStaging: Bool = false

    let storePath: String

    init(storePath: String = ArxosCore.defaultStorePath()) {
        self.storePath = storePath
        // Restore last building after force-quit if still present on disk.
        if let last = UserDefaults.standard.string(forKey: Self.lastBuildingKey), !last.isEmpty {
            openBuilding(id: last, quiet: true)
        }
    }

    private func rememberBuilding(_ id: String) {
        UserDefaults.standard.set(id, forKey: Self.lastBuildingKey)
    }

    var buildingId: String? { summary?.buildingId }

    private func report(_ error: Error) {
        let message = error.localizedDescription
        lastError = message
        status = "Error: \(message)"
    }

    func initBuilding(name: String) {
        status = "Initializing…"
        lastError = nil
        do {
            let s = try ArxosCore.initBuilding(storePath: storePath, name: name)
            summary = s
            rememberBuilding(s.buildingId)
            hasUncommittedStaging = s.stagedCount > 0
            status = "Building \(s.buildingId.prefix(12))… ready"
            refreshNearby()
        } catch {
            report(error)
        }
    }

    func openBuilding(id: String, quiet: Bool = false) {
        if !quiet {
            status = "Opening…"
        }
        lastError = nil
        do {
            let s = try ArxosCore.openBuilding(storePath: storePath, buildingId: id)
            summary = s
            rememberBuilding(s.buildingId)
            hasUncommittedStaging = s.stagedCount > 0
            status = "Opened \(s.buildingId.prefix(12))… head=\(s.headRoot?.prefix(16) ?? "none")… pending=\(s.stagedCount)"
            refreshNearby()
        } catch {
            if quiet {
                // Stale last-building id after store wipe — clear quietly.
                UserDefaults.standard.removeObject(forKey: Self.lastBuildingKey)
                status = "No saved building (start a new scan)"
            } else {
                report(error)
            }
        }
    }

    func listBuildings() -> [BuildingSummary] {
        lastError = nil
        do {
            return try ArxosCore.listBuildings(storePath: storePath)
        } catch {
            report(error)
            return []
        }
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
        lastError = nil
        let p = cameraPose
        do {
            let r = try ArxosCore.captureSpace(
                storePath: storePath, buildingId: id, name: name,
                x: Double(p.x), y: Double(p.y), z: Double(p.z)
            )
            lastCapture = r
            summary = try ArxosCore.openBuilding(storePath: storePath, buildingId: id)
            status = "Space \(r.cid.prefix(18))…"
            refreshNearby()
        } catch {
            report(error)
        }
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
        lastError = nil
        let p = cameraPose
        do {
            let r = try ArxosCore.captureAnnotation(
                storePath: storePath, buildingId: id, text: text,
                x: Double(p.x), y: Double(p.y), z: Double(p.z)
            )
            lastCapture = r
            annotationDraft = ""
            summary = try ArxosCore.openBuilding(storePath: storePath, buildingId: id)
            status = "Annotation \(r.cid.prefix(18))…"
            refreshNearby()
        } catch {
            report(error)
        }
    }

    /// Ingest a LiDAR / RoomPlan point sample as PointCloudChunk.
    func capturePointCloud(pointsXYZ: [SIMD3<Float>], pose: SIMD3<Float>? = nil) {
        guard let id = buildingId else {
            status = "No building open"
            return
        }
        lastError = nil
        var data = Data(capacity: pointsXYZ.count * 12)
        for p in pointsXYZ {
            var x = p.x, y = p.y, z = p.z
            withUnsafeBytes(of: &x) { data.append(contentsOf: $0) }
            withUnsafeBytes(of: &y) { data.append(contentsOf: $0) }
            withUnsafeBytes(of: &z) { data.append(contentsOf: $0) }
        }
        let origin = pose ?? cameraPose
        do {
            let r = try ArxosCore.capturePointCloud(
                storePath: storePath, buildingId: id, pointsXYZF32LE: data,
                x: Double(origin.x), y: Double(origin.y), z: Double(origin.z)
            )
            lastCapture = r
            summary = try ArxosCore.openBuilding(storePath: storePath, buildingId: id)
            status = "PointCloud \(pointsXYZ.count) pts \(r.cid.prefix(16))…"
        } catch {
            report(error)
        }
    }

    /// Simulate a full RoomPlan-like capture (no device LiDAR required).
    func simulateRoomCapture(roomName: String = "Captured Room") {
        guard buildingId != nil else {
            status = "No building open"
            return
        }
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
        if lastError == nil {
            status = "Simulated capture staged (pending commit)"
        }
    }

    func commit(message: String = "device capture") {
        guard let id = buildingId else {
            status = "No building open"
            return
        }
        lastError = nil
        do {
            let r = try ArxosCore.commitBuilding(
                storePath: storePath, buildingId: id, message: message
            )
            lastCommit = r
            summary = try ArxosCore.openBuilding(storePath: storePath, buildingId: id)
            hasUncommittedStaging = false
            rememberBuilding(id)
            status = "Committed root \(r.rootCid.prefix(18))… (\(r.objectCount) objects) — safe to force-quit"
            refreshNearby()
        } catch {
            report(error)
        }
    }

    /// Ingest RoomPlan structured geometry, then **auto-commit** so force-quit cannot lose the scan.
    func ingestRoomPlan(
        surfaces: [RoomPlanSurface],
        objects: [RoomPlanObject],
        autoCommit: Bool = true
    ) {
        guard let id = buildingId else {
            status = "No building open"
            return
        }
        lastError = nil
        do {
            let res = try ArxosCore.ingestRoomPlan(
                storePath: storePath,
                buildingId: id,
                surfaces: surfaces,
                objects: objects
            )
            hasUncommittedStaging = true
            summary = try ArxosCore.openBuilding(storePath: storePath, buildingId: id)
            status = "RoomPlan staged: space \(res.spaceCid.prefix(8)), \(res.surfaceCids.count) surfaces, \(res.objectCids.count) objects"
            if autoCommit {
                commit(message: "roomplan scan")
            } else {
                refreshNearby()
            }
        } catch {
            report(error)
        }
    }

    /// Copy the CAS directory to a temporary folder for the share sheet / AirDrop.
    ///
    /// On Mac, unzip/copy into a path and run:
    ///   `arx --store /path/to/arxos-store building status <id>`
    /// The live store is also visible under Files → On My iPhone → Arxos when
    /// file sharing is enabled (Info.plist UIFileSharingEnabled).
    func exportStoreForShare() throws -> URL {
        let fm = FileManager.default
        let src = URL(fileURLWithPath: storePath, isDirectory: true)
        guard fm.fileExists(atPath: src.path) else {
            throw NSError(
                domain: "Arxos",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "Store not found at \(storePath)"]
            )
        }
        let stamp = Int(Date().timeIntervalSince1970)
        let dirCopy = fm.temporaryDirectory
            .appendingPathComponent(
                "arxos-store-\(buildingId?.prefix(8) ?? "export")-\(stamp)",
                isDirectory: true
            )
        if fm.fileExists(atPath: dirCopy.path) {
            try fm.removeItem(at: dirCopy)
        }
        try fm.copyItem(at: src, to: dirCopy)
        return dirCopy
    }

    func refreshNearby(radiusM: Double = 15) {
        guard let id = buildingId else {
            nearbyAnnotations = []
            return
        }
        let p = cameraPose
        do {
            nearbyAnnotations = try ArxosCore.annotationsNear(
                storePath: storePath, buildingId: id,
                x: Double(p.x), y: Double(p.y), z: Double(p.z),
                radiusM: radiusM
            )
        } catch {
            nearbyAnnotations = []
            report(error)
        }
    }
}
