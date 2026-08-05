import Foundation
import simd
#if canImport(ArxosCore)
import ArxosCore
#endif

#if canImport(RoomPlan) && canImport(ARKit) && !targetEnvironment(simulator)
import RoomPlan
import ARKit

/// Device capture pipeline: RoomPlan → Space + PointCloudChunk objects.
/// Geometry is data only — no general 3D model viewer in Arxos.
@available(iOS 17.0, *)
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
        let builder = RoomBuilder(options: [])
        onStatus?("Processing RoomPlan data…")
        Task {
            do {
                let room = try await builder.capturedRoom(from: data)
                
                func doubleArray(from matrix: simd_float4x4) -> [Double] {
                    return [
                        Double(matrix.columns.0.x), Double(matrix.columns.0.y), Double(matrix.columns.0.z), Double(matrix.columns.0.w),
                        Double(matrix.columns.1.x), Double(matrix.columns.1.y), Double(matrix.columns.1.z), Double(matrix.columns.1.w),
                        Double(matrix.columns.2.x), Double(matrix.columns.2.y), Double(matrix.columns.2.z), Double(matrix.columns.2.w),
                        Double(matrix.columns.3.x), Double(matrix.columns.3.y), Double(matrix.columns.3.z), Double(matrix.columns.3.w)
                    ]
                }

                func doubleArray(from vec: simd_float3) -> [Double] {
                    return [Double(vec.x), Double(vec.y), Double(vec.z)]
                }

                var surfaces: [RoomPlanSurface] = []
                
                for item in room.walls {
                    surfaces.append(RoomPlanSurface(
                        id: item.identifier.uuidString,
                        category: "wall",
                        transform: doubleArray(from: item.transform),
                        dimensions: doubleArray(from: item.dimensions)
                    ))
                }
                for item in room.floors {
                    surfaces.append(RoomPlanSurface(
                        id: item.identifier.uuidString,
                        category: "floor",
                        transform: doubleArray(from: item.transform),
                        dimensions: doubleArray(from: item.dimensions)
                    ))
                }
                // Note: CapturedRoom has no separate ceilings array on current SDKs.
                for item in room.doors {
                    surfaces.append(RoomPlanSurface(
                        id: item.identifier.uuidString,
                        category: "door",
                        transform: doubleArray(from: item.transform),
                        dimensions: doubleArray(from: item.dimensions)
                    ))
                }
                for item in room.windows {
                    surfaces.append(RoomPlanSurface(
                        id: item.identifier.uuidString,
                        category: "window",
                        transform: doubleArray(from: item.transform),
                        dimensions: doubleArray(from: item.dimensions)
                    ))
                }
                for item in room.openings {
                    surfaces.append(RoomPlanSurface(
                        id: item.identifier.uuidString,
                        category: "opening",
                        transform: doubleArray(from: item.transform),
                        dimensions: doubleArray(from: item.dimensions)
                    ))
                }

                var objects: [RoomPlanObject] = []
                for item in room.objects {
                    objects.append(RoomPlanObject(
                        id: item.identifier.uuidString,
                        category: String(describing: item.category),
                        transform: doubleArray(from: item.transform),
                        dimensions: doubleArray(from: item.dimensions)
                    ))
                }

                await MainActor.run {
                    // Auto-commits so force-quit cannot lose the scan.
                    self.session.ingestRoomPlan(
                        surfaces: surfaces,
                        objects: objects,
                        autoCommit: true
                    )
                    self.session.isRoomPlanActive = false
                    self.onStatus?(self.session.status)
                }
            } catch {
                await MainActor.run {
                    self.onStatus?("RoomPlan ingest failed: \(error.localizedDescription)")
                }
            }
        }
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
