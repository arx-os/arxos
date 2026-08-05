import SwiftUI
#if canImport(UIKit)
import UIKit
#endif
#if canImport(ArxosCore)
import ArxosCore
#endif

/// Capture shell: RoomPlan scan → ingest → auto-commit → reopen survives force-quit.
public struct CaptureHomeView: View {
    @StateObject private var session = BuildingSession()
    @State private var buildingName: String = "Home Room"
    @State private var openId: String = ""
    @State private var showList = false
    @State private var listed: [BuildingSummary] = []
#if canImport(RoomPlan) && canImport(ARKit) && !targetEnvironment(simulator)
    @State private var roomPlan: RoomPlanCapturePipeline?
#endif
    @State private var shareItems: [Any] = []
    @State private var showShare = false
    @State private var showAdvancedSimulate = false

    public init() {}

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Pause AR overlay while RoomPlan owns the camera.
                if !session.isRoomPlanActive {
                    ARCaptureView(session: session)
                        .frame(maxHeight: 280)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .padding(.horizontal)
                        .padding(.top, 8)
                } else {
                    ZStack {
                        Color.black.opacity(0.9)
                        VStack(spacing: 8) {
                            ProgressView()
                                .tint(.white)
                            Text("RoomPlan scanning…")
                                .foregroundStyle(.white)
                                .font(.headline)
                            Text("Walk the room slowly. Tap Stop when finished.")
                                .foregroundStyle(.white.opacity(0.7))
                                .font(.caption)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal)
                        }
                    }
                    .frame(maxHeight: 280)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .padding(.horizontal)
                    .padding(.top, 8)
                }

                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        header

                        GroupBox("Building") {
                            if let s = session.summary {
                                labeled("ID", s.buildingId)
                                labeled("Name", s.name ?? "—")
                                labeled("Head", s.headRoot ?? "(not committed)")
                                labeled("Pending staged", "\(s.stagedCount)")
                                if session.hasUncommittedStaging {
                                    Text("Staged only — commit so force-quit is safe")
                                        .font(.caption)
                                        .foregroundStyle(.orange)
                                }
                            } else {
                                Text("No building open — Init or open one first")
                                    .foregroundStyle(.secondary)
                            }

                            HStack {
                                TextField("Name", text: $buildingName)
                                    .textFieldStyle(.roundedBorder)
                                Button("Init") {
                                    session.initBuilding(name: buildingName)
                                }
                                .buttonStyle(.borderedProminent)
                            }

                            HStack {
                                TextField("Building ID", text: $openId)
                                    .textFieldStyle(.roundedBorder)
                                    .font(.caption.monospaced())
                                Button("Open") {
                                    session.openBuilding(id: openId)
                                }
                                .buttonStyle(.bordered)
                            }

                            Button("List buildings") {
                                listed = session.listBuildings()
                                showList = true
                            }
                            .font(.footnote)

                            if let err = session.lastError {
                                Text(err)
                                    .font(.caption)
                                    .foregroundStyle(.red)
                                    .textSelection(.enabled)
                            }
                        }

                        GroupBox("RoomPlan (real scan)") {
                            Text("Uses device LiDAR. Requires a physical iPhone with LiDAR.")
                                .font(.caption)
                                .foregroundStyle(.secondary)

                            if session.isRoomPlanActive {
                                Button("Stop RoomPlan scan") {
                                    stopRoomPlan()
                                }
                                .buttonStyle(.borderedProminent)
                                .tint(.red)
                            } else {
                                Button("Start RoomPlan scan") {
                                    startRoomPlan()
                                }
                                .buttonStyle(.borderedProminent)
                                .disabled(session.buildingId == nil)
                            }

                            Text("On Stop, geometry is ingested and auto-committed.")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }

                        GroupBox("Notes & commit") {
                            HStack {
                                TextField("Annotation text", text: $session.annotationDraft)
                                    .textFieldStyle(.roundedBorder)
                                Button("Pin note") {
                                    session.captureAnnotation()
                                }
                                .buttonStyle(.bordered)
                                .disabled(session.buildingId == nil)
                            }

                            Button("Commit root now") {
                                session.commit(message: "ios capture")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.green)
                            .disabled(session.buildingId == nil)

                            if let c = session.lastCommit {
                                Text("Last commit \(c.rootCid.prefix(18))… (\(c.objectCount) objects)")
                                    .font(.caption2.monospaced())
                            }
                        }

                        GroupBox("Export to Mac") {
                            Text("Share the store folder (AirDrop / Files), then on Mac:")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text("arx --store /path/to/arxos-store building status <id>")
                                .font(.caption2.monospaced())
                                .textSelection(.enabled)

                            Button("Export store…") {
                                exportStore()
                            }
                            .buttonStyle(.bordered)
                            .disabled(session.buildingId == nil)
                        }

                        GroupBox("Nearby annotations") {
                            if session.nearbyAnnotations.isEmpty {
                                Text("None in radius")
                                    .foregroundStyle(.secondary)
                            } else {
                                ForEach(session.nearbyAnnotations) { ann in
                                    HStack {
                                        VStack(alignment: .leading) {
                                            Text(ann.text).font(.body)
                                            Text(ann.cid)
                                                .font(.caption2.monospaced())
                                                .foregroundStyle(.secondary)
                                                .lineLimit(1)
                                        }
                                        Spacer()
                                        Text(String(format: "%.1fm", ann.distanceM))
                                            .font(.caption.monospaced())
                                    }
                                }
                            }
                            Button("Refresh nearby") {
                                session.refreshNearby()
                            }
                            .font(.footnote)
                        }

                        DisclosureGroup("Advanced / no LiDAR", isExpanded: $showAdvancedSimulate) {
                            Button("Simulate scan (dev only)") {
                                session.simulateRoomCapture(roomName: buildingName)
                                session.commit(message: "simulate")
                            }
                            .disabled(session.buildingId == nil)
                            Text("Does not use RoomPlan. Prefer real scan on device.")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        .font(.footnote)

                        GroupBox("Status") {
                            Text(session.status)
                                .font(.footnote.monospaced())
                            Text("Core \(ArxosCore.version())")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Text(session.storePath)
                                .font(.caption2.monospaced())
                                .foregroundStyle(.secondary)
                                .textSelection(.enabled)
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("Arxos")
            .sheet(isPresented: $showList) {
                NavigationStack {
                    List(listed, id: \.buildingId) { b in
                        Button {
                            openId = b.buildingId
                            session.openBuilding(id: b.buildingId)
                            showList = false
                        } label: {
                            VStack(alignment: .leading) {
                                Text(b.name ?? "(unnamed)")
                                Text(b.buildingId)
                                    .font(.caption.monospaced())
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .navigationTitle("Buildings")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Close") { showList = false }
                        }
                    }
                }
            }
#if canImport(UIKit)
            .sheet(isPresented: $showShare) {
                ActivityView(items: shareItems)
            }
#endif
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Scan → commit → reopen")
                .font(.headline)
            Text("RoomPlan → entities → signed root (survives force-quit)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    @ViewBuilder
    private func labeled(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title.uppercased())
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.caption.monospaced())
                .textSelection(.enabled)
                .lineLimit(2)
        }
        .padding(.bottom, 4)
    }

    private func startRoomPlan() {
        guard session.buildingId != nil else {
            session.status = "Init or open a building first"
            return
        }
#if canImport(RoomPlan) && canImport(ARKit) && !targetEnvironment(simulator)
        if #available(iOS 17.0, *) {
            let pipeline = RoomPlanCapturePipeline(session: session)
            pipeline.onStatus = { msg in
                Task { @MainActor in
                    session.status = msg
                }
            }
            roomPlan = pipeline
            session.isRoomPlanActive = true
            pipeline.start()
        } else {
            session.status = "RoomPlan requires iOS 17+ (LiDAR iPhone)"
        }
#else
        session.status = "RoomPlan unavailable (simulator / macOS) — use Advanced simulate"
#endif
    }

    private func stopRoomPlan() {
#if canImport(RoomPlan) && canImport(ARKit) && !targetEnvironment(simulator)
        if #available(iOS 17.0, *) {
            roomPlan?.stop()
        }
#endif
        roomPlan = nil
        session.isRoomPlanActive = false
        // Ingest runs asynchronously from RoomPlan didEndWith → auto-commit.
        session.status = "RoomPlan stopped — processing capture…"
    }

    private func exportStore() {
        do {
            let url = try session.exportStoreForShare()
            shareItems = [url]
            showShare = true
            session.status = "Export ready: \(url.lastPathComponent)"
        } catch {
            session.status = "Export failed: \(error.localizedDescription)"
        }
    }
}

// MARK: - Share sheet

#if canImport(UIKit)
struct ActivityView: UIViewControllerRepresentable {
    let items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
#endif
