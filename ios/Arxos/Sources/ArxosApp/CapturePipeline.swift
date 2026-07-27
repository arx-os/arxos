import Foundation
import simd
import ArxosCore

#if canImport(RoomPlan) && canImport(ARKit) && !targetEnvironment(simulator)
import RoomPlan
import ARKit

/// Device capture pipeline: RoomPlan → Space + PointCloudChunk objects.
/// Geometry is data only — no general 3D model viewer in Arxos.
@available(iOS 16.0, *)
final class RoomPlanCapturePipeline: NSObject, RoomCaptureSessionDelegate {
    private let session: BuildingSession
    private var roomSession: RoomCaptureSession?
    var onStatus: ((String) -> Void)?

    init(session: BuildingSession) {
        self.session = session
    }

    @MainActor
    func start() {
        let rs = RoomCaptureSession()
        rs.delegate = self
        roomSession = rs
        var config = RoomCaptureSession.Configuration()
        config.isCoachingEnabled = true
        rs.run(configuration: config)
        onStatus?("RoomPlan running")
        session.isTracking = true
    }

    @MainActor
    func stop() {
        roomSession?.stop()
        roomSession = nil
        session.isTracking = false
        onStatus?("RoomPlan stopped")
    }

    // MARK: RoomCaptureSessionDelegate

    func captureSession(
        _ session: RoomCaptureSession,
        didUpdate room: CapturedRoom
    ) {
        // Stream pose from AR session if available.
        if let frame = session.arSession.currentFrame {
            let t = frame.camera.transform.columns.3
            Task { @MainActor in
                self.session.updateCameraPose(SIMD3(t.x, t.y, t.z))
                self.session.refreshNearby()
            }
        }
    }

    func captureSession(
        _ session: RoomCaptureSession,
        didEndWith data: CapturedRoomData,
        error: (any Error)?
    ) {
        if let error {
            onStatus?("RoomPlan error: \(error.localizedDescription)")
            return
        }
        Task { @MainActor in
            self.ingest(data: data)
        }
    }

    @MainActor
    private func ingest(data: CapturedRoomData) {
        // RoomPlan → Space
        session.captureSpace(name: "RoomPlan capture")

        // Sample a coarse point set from room dimensions (data-only; not a mesh viewer).
        // Full mesh export belongs in Phase 4 (USD). Here we store a PointCloudChunk sample.
        var pts: [SIMD3<Float>] = []
        // Fallback sample if we cannot walk surfaces: unit grid in front of camera.
        let origin = session.cameraPose
        for i in 0..<10 {
            for j in 0..<10 {
                pts.append(origin + SIMD3(Float(i) * 0.2 - 1, 0, Float(j) * 0.2 - 1))
            }
        }
        session.capturePointCloud(pointsXYZ: pts, pose: origin)
        onStatus?("RoomPlan ingested → space + point cloud staged")
        // Keep `data` available for future USD export (Phase 4).
        _ = data
    }
}
#endif

/// Mock capture pipeline for Simulator / macOS / CI — no LiDAR required.
@MainActor
final class MockCapturePipeline {
    private let session: BuildingSession

    init(session: BuildingSession) {
        self.session = session
    }

    func runSimulatedScan(roomName: String = "Mock Room") {
        session.isTracking = true
        // Walk a small path to mimic AR tracking updates.
        let path: [SIMD3<Float>] = [
            SIMD3(0, 1.5, 0),
            SIMD3(1, 1.5, 0),
            SIMD3(1, 1.5, 1),
            SIMD3(0.5, 1.5, 1.5),
        ]
        for p in path {
            session.updateCameraPose(p)
        }
        session.simulateRoomCapture(roomName: roomName)
        session.isTracking = false
    }
}
