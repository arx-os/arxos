import Foundation

/// Thin JSON-RPC client for the ArxOS agent (Decision 11 path A).
/// Peripheral only — never writes building.yaml.
@MainActor
final class AgentClient: ObservableObject {
    @Published var isConnected = false
    @Published var lastError: String?
    @Published var log: [String] = []
    @Published var host: String = UserDefaults.standard.string(forKey: "arx_host") ?? "127.0.0.1:8787"
    @Published var token: String = UserDefaults.standard.string(forKey: "arx_token") ?? ""

    private var webSocket: URLSessionWebSocketTask?
    private var session: URLSession?
    private var nextId: Int = 1
    private var pending: [Int: CheckedContinuation<Any, Error>] = [:]

    func appendLog(_ line: String) {
        let ts = ISO8601DateFormatter().string(from: Date())
        log.append("[\(ts.suffix(8))] \(line)")
        if log.count > 500 {
            log.removeFirst(log.count - 500)
        }
    }

    func connect() async {
        disconnect()
        lastError = nil
        let hostPort = host.trimmingCharacters(in: .whitespacesAndNewlines)
        let tok = token.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !tok.isEmpty else {
            lastError = "Token is empty — paste ROOT TOKEN from `arx agent`"
            appendLog("ERROR: \(lastError!)")
            return
        }
        guard let url = URL(string: "ws://\(hostPort)/ws?token=\(tok.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? tok)") else {
            lastError = "Invalid host URL"
            appendLog("ERROR: \(lastError!)")
            return
        }

        UserDefaults.standard.set(hostPort, forKey: "arx_host")
        UserDefaults.standard.set(tok, forKey: "arx_token")

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        let session = URLSession(configuration: config)
        self.session = session
        let task = session.webSocketTask(with: url)
        self.webSocket = task
        task.resume()
        appendLog("Connecting \(url.absoluteString.prefix(60))…")

        // Kick receive loop
        Task { await self.receiveLoop() }

        // Connectivity probe
        do {
            let _ = try await rpc(method: "building.get", params: [:])
            isConnected = true
            appendLog("● Online — building.get OK")
        } catch {
            // building.yaml might be missing; try validate-less path via git.status
            do {
                let _ = try await rpc(method: "git.status", params: [:])
                isConnected = true
                appendLog("● Online — git.status OK (building may be empty)")
            } catch {
                isConnected = false
                lastError = error.localizedDescription
                appendLog("ERROR connect: \(error.localizedDescription)")
                disconnect()
            }
        }
    }

    func disconnect() {
        webSocket?.cancel(with: .goingAway, reason: nil)
        webSocket = nil
        for (_, cont) in pending {
            cont.resume(throwing: AgentError.disconnected)
        }
        pending.removeAll()
        isConnected = false
    }

    func rpc(method: String, params: [String: Any]) async throws -> Any {
        guard let ws = webSocket else { throw AgentError.disconnected }
        let id = nextId
        nextId += 1

        var body: [String: Any] = [
            "jsonrpc": "2.0",
            "method": method,
            "id": id,
            "params": params,
        ]
        // Some agents expect params always present
        if params.isEmpty {
            body["params"] = [String: Any]()
        }

        let data = try JSONSerialization.data(withJSONObject: body)
        guard let text = String(data: data, encoding: .utf8) else {
            throw AgentError.encoding
        }

        return try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Any, Error>) in
            pending[id] = cont
            ws.send(.string(text)) { [weak self] err in
                if let err {
                    Task { @MainActor in
                        if let c = self?.pending.removeValue(forKey: id) {
                            c.resume(throwing: err)
                        }
                    }
                }
            }
            // Timeout
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 120_000_000_000)
                if let c = self.pending.removeValue(forKey: id) {
                    c.resume(throwing: AgentError.timeout)
                }
            }
        }
    }

    private func receiveLoop() async {
        guard let ws = webSocket else { return }
        while true {
            do {
                let msg = try await ws.receive()
                switch msg {
                case .string(let text):
                    handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        handleMessage(text)
                    }
                @unknown default:
                    break
                }
            } catch {
                await MainActor.run {
                    self.appendLog("WS closed: \(error.localizedDescription)")
                    self.isConnected = false
                }
                break
            }
        }
    }

    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else {
            appendLog("RX (non-json): \(text.prefix(120))")
            return
        }

        let idVal = obj["id"]
        let id: Int? = {
            if let i = idVal as? Int { return i }
            if let n = idVal as? NSNumber { return n.intValue }
            return nil
        }()

        guard let id, let cont = pending.removeValue(forKey: id) else {
            appendLog("RX unsolicited id=\(String(describing: idVal))")
            return
        }

        if let err = obj["error"] as? [String: Any] {
            let message = err["message"] as? String ?? "RPC error"
            cont.resume(throwing: AgentError.rpc(message))
            return
        }
        cont.resume(returning: obj["result"] as Any)
    }
}

enum AgentError: LocalizedError {
    case disconnected
    case encoding
    case timeout
    case rpc(String)

    var errorDescription: String? {
        switch self {
        case .disconnected: return "Not connected to agent"
        case .encoding: return "Failed to encode request"
        case .timeout: return "RPC timed out"
        case .rpc(let m): return m
        }
    }
}
