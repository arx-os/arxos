import SwiftUI
import ArxosCore

/// Phase 1 lived-experience shell: open/create building, capture, annotate, commit, overlay.
public struct CaptureHomeView: View {
    @StateObject private var session = BuildingSession()
    @State private var buildingName: String = "Field Building"
    @State private var openId: String = ""
    @State private var showList = false
    @State private var listed: [BuildingSummary] = []

    public init() {}

    public var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                ARCaptureView(session: session)
                    .frame(maxHeight: 320)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .padding(.horizontal)
                    .padding(.top, 8)

                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        header

                        GroupBox("Building") {
                            if let s = session.summary {
                                labeled("ID", s.buildingId)
                                labeled("Name", s.name ?? "—")
                                labeled("Head", s.headRoot ?? "—")
                                labeled("Pending", "\(s.stagedCount)")
                            } else {
                                Text("No building open")
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

                        GroupBox("Capture") {
                            Text("Geometry is data only — no general 3D viewer.")
                                .font(.caption)
                                .foregroundStyle(.secondary)

                            Button("Simulate RoomPlan scan") {
                                session.simulateRoomCapture(roomName: buildingName)
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(session.buildingId == nil)

                            Button("Capture space @ camera") {
                                session.captureSpace(name: buildingName)
                            }
                            .disabled(session.buildingId == nil)

                            HStack {
                                TextField("Annotation text", text: $session.annotationDraft)
                                    .textFieldStyle(.roundedBorder)
                                Button("Pin note") {
                                    session.captureAnnotation()
                                }
                                .buttonStyle(.bordered)
                                .disabled(session.buildingId == nil)
                            }

                            Button("Commit root") {
                                session.commit(message: "ios capture")
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.green)
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

                        GroupBox("Status") {
                            Text(session.status)
                                .font(.footnote.monospaced())
                            Text("Core \(ArxosCore.version()) · store \(session.storePath)")
                                .font(.caption2)
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
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Lived experience — Phase 1")
                .font(.headline)
            Text("LiDAR/RoomPlan → objects → commit root → AR notes")
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
}
