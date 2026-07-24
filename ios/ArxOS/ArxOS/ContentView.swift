import SwiftUI
import UIKit
import UniformTypeIdentifiers

/// Terminal-style field client. Peripheral only — agent owns durable writes.
struct ContentView: View {
    @StateObject private var agent = AgentClient()
    @State private var commandLine = ""
    @State private var showImporter = false
    @State private var labelRoom = "Room 1"
    @State private var labelEquip = "Light Switch"
    @State private var busy = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                connectBar
                terminal
                quickActions
                commandBar
            }
            .navigationTitle("ArxOS")
            .navigationBarTitleDisplayMode(.inline)
            .fileImporter(
                isPresented: $showImporter,
                allowedContentTypes: [
                    UTType(filenameExtension: "ply") ?? .data,
                    UTType(filenameExtension: "xyz") ?? .data,
                    UTType(filenameExtension: "las") ?? .data,
                    UTType(filenameExtension: "csv") ?? .plainText,
                    .data,
                ],
                allowsMultipleSelection: false
            ) { result in
                Task { await importScanFile(result) }
            }
        }
    }

    private var connectBar: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Circle()
                    .fill(agent.isConnected ? Color.green : Color.red)
                    .frame(width: 10, height: 10)
                Text(agent.isConnected ? "Online" : "Offline")
                    .font(.caption.bold())
                Spacer()
            }
            TextField("Agent host (LAN:8787)", text: $agent.host)
                .textFieldStyle(.roundedBorder)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .font(.system(.body, design: .monospaced))
            SecureField("ROOT TOKEN", text: $agent.token)
                .textFieldStyle(.roundedBorder)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .font(.system(.caption, design: .monospaced))
            HStack {
                Button(agent.isConnected ? "Reconnect" : "Connect") {
                    Task { await agent.connect() }
                }
                .buttonStyle(.borderedProminent)
                .disabled(busy)
                Button("Disconnect") { agent.disconnect() }
                    .buttonStyle(.bordered)
            }
        }
        .padding(12)
        .background(Color(.secondarySystemBackground))
    }

    private var terminal: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(agent.log.enumerated()), id: \.offset) { i, line in
                        Text(line)
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundStyle(line.contains("ERROR") ? Color.red : Color.green)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .id(i)
                    }
                }
                .padding(8)
            }
            .background(Color.black)
            .onChange(of: agent.log.count) { _, _ in
                if let last = agent.log.indices.last {
                    proxy.scrollTo(last, anchor: .bottom)
                }
            }
        }
    }

    private var quickActions: some View {
        VStack(spacing: 8) {
            HStack {
                TextField("Room", text: $labelRoom)
                    .textFieldStyle(.roundedBorder)
                TextField("Equipment", text: $labelEquip)
                    .textFieldStyle(.roundedBorder)
            }
            .font(.system(.caption, design: .monospaced))
            .padding(.horizontal, 12)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    actionButton("Building") { await runBuilding() }
                    actionButton("Validate") { await runValidate() }
                    actionButton("Scan file") { showImporter = true }
                    actionButton("Label") { await runLabel() }
                    actionButton("Accept room") { await runAcceptRoom() }
                    actionButton("Commit") { await runCommit() }
                    actionButton("Export IFC") { await runExport() }
                }
                .padding(.horizontal, 12)
            }
            Text("Scan = import PLY/XYZ via agent (Decision 11). Labels are proposed until Accept.")
                .font(.caption2)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 12)
        }
        .padding(.vertical, 8)
    }

    private func actionButton(_ title: String, _ work: @escaping () async -> Void) -> some View {
        Button(title) {
            Task {
                busy = true
                defer { busy = false }
                await work()
            }
        }
        .buttonStyle(.bordered)
        .disabled(busy || (!agent.isConnected && title != "Building"))
        .font(.caption.bold())
    }

    private var commandBar: some View {
        HStack {
            TextField("command: help | building | validate | commit msg | export", text: $commandLine)
                .textFieldStyle(.roundedBorder)
                .font(.system(.body, design: .monospaced))
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .onSubmit { Task { await runCommandLine() } }
            Button("Run") {
                Task { await runCommandLine() }
            }
            .buttonStyle(.borderedProminent)
            .disabled(busy)
        }
        .padding(12)
    }

    // MARK: - Commands

    private func runCommandLine() async {
        let line = commandLine.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !line.isEmpty else { return }
        agent.appendLog("> \(line)")
        commandLine = ""
        let parts = line.split(separator: " ", maxSplits: 1, omittingEmptySubsequences: true)
        let cmd = parts.first.map(String.init)?.lowercased() ?? ""
        let rest = parts.count > 1 ? String(parts[1]) : ""
        busy = true
        defer { busy = false }
        switch cmd {
        case "help":
            agent.appendLog("Commands: connect fields above · building · validate · label · accept · commit <msg> · export · scan (button)")
        case "building", "status":
            await runBuilding()
        case "validate":
            await runValidate()
        case "label":
            await runLabel()
        case "accept":
            await runAcceptRoom()
        case "commit":
            await runCommit(message: rest.isEmpty ? nil : rest)
        case "export":
            await runExport()
        default:
            agent.appendLog("ERROR: unknown command (try help)")
        }
    }

    private func runBuilding() async {
        do {
            let result = try await agent.rpc(method: "building.get", params: [:])
            agent.appendLog(pretty(result))
        } catch {
            agent.appendLog("ERROR building.get: \(error.localizedDescription)")
        }
    }

    private func runValidate() async {
        do {
            let result = try await agent.rpc(method: "building.validate", params: [:])
            agent.appendLog(pretty(result))
        } catch {
            agent.appendLog("ERROR validate: \(error.localizedDescription)")
        }
    }

    private func runLabel() async {
        let room = labelRoom.trimmingCharacters(in: .whitespacesAndNewlines)
        let equip = labelEquip.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !room.isEmpty, !equip.isEmpty else {
            agent.appendLog("ERROR: set Room and Equipment fields")
            return
        }
        // Ensure room exists (idempotent-ish); then add equipment as proposed via review defaults
        let script = """
        add equipment \(equip) room=\(room) type=electrical
        set equipment \(equip) review_status=proposed
        """
        do {
            let result = try await agent.rpc(method: "edit.apply", params: ["script": script])
            agent.appendLog("label OK → \(pretty(result))")
        } catch {
            // If room missing, create proposed room then equipment
            let create = """
            add room \(room) floor=0 type=other
            set room \(room) review_status=proposed
            add equipment \(equip) room=\(room) type=electrical
            set equipment \(equip) review_status=proposed
            """
            do {
                let result = try await agent.rpc(method: "edit.apply", params: ["script": create])
                agent.appendLog("label (created room) OK → \(pretty(result))")
            } catch {
                agent.appendLog("ERROR label: \(error.localizedDescription)")
            }
        }
    }

    private func runAcceptRoom() async {
        let room = labelRoom.trimmingCharacters(in: .whitespacesAndNewlines)
        let script = "set room \(room) review_status=accepted\n"
        do {
            let result = try await agent.rpc(method: "edit.apply", params: ["script": script])
            agent.appendLog("accept OK → \(pretty(result))")
        } catch {
            agent.appendLog("ERROR accept: \(error.localizedDescription)")
        }
    }

    private func runCommit(message: String? = nil) async {
        let msg = (message?.isEmpty == false ? message! : "ios field capture \(ISO8601DateFormatter().string(from: Date()))")
        do {
            let result = try await agent.rpc(
                method: "git.commit",
                params: ["message": msg, "stageAll": true]
            )
            agent.appendLog("COMMIT OK → \(pretty(result))")
        } catch {
            agent.appendLog("ERROR commit: \(error.localizedDescription)")
        }
    }

    private func runExport() async {
        do {
            // After accept; default full export for lab visibility of proposed too
            let result = try await agent.rpc(
                method: "ifc.export",
                params: [
                    "filename": "ios-export.ifc",
                    "approved_only": false,
                ]
            )
            if let dict = result as? [String: Any] {
                let name = dict["filename"] as? String ?? "?"
                let size = dict["size_bytes"] as? Int ?? 0
                agent.appendLog("EXPORT OK → \(name) (\(size) bytes) on capture node under exports/")
            } else {
                agent.appendLog("EXPORT OK → \(pretty(result))")
            }
        } catch {
            agent.appendLog("ERROR export: \(error.localizedDescription)")
        }
    }

    private func importScanFile(_ result: Result<[URL], Error>) async {
        switch result {
        case .failure(let err):
            agent.appendLog("ERROR file pick: \(err.localizedDescription)")
        case .success(let urls):
            guard let url = urls.first else { return }
            let access = url.startAccessingSecurityScopedResource()
            defer { if access { url.stopAccessingSecurityScopedResource() } }
            do {
                let data = try Data(contentsOf: url)
                let b64 = data.base64EncodedString()
                let name = url.lastPathComponent
                agent.appendLog("Uploading \(name) (\(data.count) bytes) via lidar.import…")
                let params: [String: Any] = [
                    "filename": name,
                    "data": b64,
                    "merge": true,
                    "light_mode": true,
                    "voxel_size": 0.25,
                    "provenance": [
                        "client": "ios_native",
                        "client_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0.1.0",
                        "captured_at": ISO8601DateFormatter().string(from: Date()),
                        "device_model": UIDevice.current.model,
                        "note": "file hand-off Decision 11 path A",
                    ] as [String: Any],
                ]
                let res = try await agent.rpc(method: "lidar.import", params: params)
                agent.appendLog("SCAN OK → \(pretty(res))")
                if let room = (res as? [String: Any]).flatMap({ _ in Optional(labelRoom) }) {
                    _ = room
                }
            } catch {
                agent.appendLog("ERROR lidar.import: \(error.localizedDescription)")
            }
        }
    }

    private func pretty(_ value: Any) -> String {
        if let dict = value as? [String: Any],
           let data = try? JSONSerialization.data(withJSONObject: dict, options: [.prettyPrinted, .sortedKeys]),
           let s = String(data: data, encoding: .utf8)
        {
            return s
        }
        return String(describing: value)
    }
}

#Preview {
    ContentView()
}
