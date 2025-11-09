import Foundation
import Combine

/// High-level facade around the ArxOS FFI surface used by the SwiftUI app.
class ArxOSCore: ObservableObject {
    @Published private(set) var activeBuildingName: String
    private let ffi: ArxOSCoreFFI
    
    init(activeBuildingName: String = "main") {
        self.activeBuildingName = activeBuildingName
        self.ffi = ArxOSCoreFFI()
    }
    
    func setActiveBuilding(_ building: String) {
        let trimmed = building.trimmingCharacters(in: .whitespacesAndNewlines)
        activeBuildingName = trimmed.isEmpty ? "main" : trimmed
    }
    
    private func resolveBuilding(_ building: String?) -> String {
        let trimmed = building?.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed?.isEmpty == false ? trimmed! : activeBuildingName
    }
    
    // MARK: - Terminal command helpers
    
    func executeRoomCommand(_ arguments: [String], completion: @escaping (Result<String, Error>) -> Void) {
        guard let action = arguments.first?.lowercased() else {
            completion(.failure(TerminalError.invalidArguments))
            return
        }
        let building = resolveBuilding(nil)
        switch action {
        case "list":
            ffi.listRooms(buildingName: building) { result in
                switch result {
                case .success(let rooms):
                    let lines = rooms.map { "\($0.name) (floor \($0.floor))" }
                    completion(.success(lines.joined(separator: "\n")))
                case .failure(let error):
                    completion(.failure(error))
                }
            }
        default:
            completion(.failure(TerminalError.ffiError("Room command '\(action)' not supported on mobile yet")))
        }
    }
    
    func executeEquipmentCommand(_ arguments: [String], completion: @escaping (Result<String, Error>) -> Void) {
        guard let action = arguments.first?.lowercased() else {
            completion(.failure(TerminalError.invalidArguments))
            return
        }
        let building = resolveBuilding(nil)
        switch action {
        case "list":
            ffi.listEquipment(buildingName: building) { result in
                switch result {
                case .success(let equipment):
                    let lines = equipment.map { "\($0.name) [\($0.type)] - \($0.locationDescription)" }
                    completion(.success(lines.joined(separator: "\n")))
                case .failure(let error):
                    completion(.failure(error))
                }
            }
        default:
            completion(.failure(TerminalError.ffiError("Equipment command '\(action)' not supported on mobile yet")))
        }
    }
    
    func getStatus(completion: @escaping (Result<String, Error>) -> Void) {
        completion(.failure(TerminalError.ffiError("Status command not yet available on mobile")))
    }
    
    func getDiff(completion: @escaping (Result<String, Error>) -> Void) {
        completion(.failure(TerminalError.ffiError("Diff command not yet available on mobile")))
    }
    
    func getHistory(completion: @escaping (Result<String, Error>) -> Void) {
        completion(.failure(TerminalError.ffiError("History command not yet available on mobile")))
    }
    
    // MARK: - AR helpers
    
    func processARData(_ data: Data, completion: @escaping (Result<[DetectedEquipment], Error>) -> Void) {
        guard let jsonString = String(data: data, encoding: .utf8) else {
            completion(.failure(TerminalError.parseError("Invalid AR scan payload")))
            return
        }
        ffi.parseARScan(jsonData: jsonString) { result in
            switch result {
            case .success(let scanData):
                completion(.success(scanData.detectedEquipment))
            case .failure(let error):
                completion(.failure(error))
            }
        }
    }
    
    func saveARScan(
        scanData: ARScanData,
        buildingName: String? = nil,
        confidenceThreshold: Double = 0.7,
        completion: @escaping (Result<ARScanSaveResult, Error>) -> Void
    ) {
        let building = resolveBuilding(buildingName ?? scanData.roomName)
        ffi.saveARScan(
            scanData: scanData,
            buildingName: building,
            confidenceThreshold: confidenceThreshold,
            completion: completion
        )
    }
    
    func listPendingEquipment(buildingName: String? = nil, completion: @escaping (Result<PendingEquipmentListResult, Error>) -> Void) {
        ffi.listPendingEquipment(buildingName: resolveBuilding(buildingName), completion: completion)
    }
    
    func confirmPendingEquipment(
        buildingName: String,
        pendingId: String,
        commitToGit: Bool = true,
        completion: @escaping (Result<PendingEquipmentConfirmResult, Error>) -> Void
    ) {
        ffi.confirmPendingEquipment(
            buildingName: resolveBuilding(buildingName),
            pendingId: pendingId,
            commitToGit: commitToGit,
            completion: completion
        )
    }
    
    func rejectPendingEquipment(
        buildingName: String,
        pendingId: String,
        completion: @escaping (Result<PendingEquipmentRejectResult, Error>) -> Void
    ) {
        ffi.rejectPendingEquipment(
            buildingName: resolveBuilding(buildingName),
            pendingId: pendingId,
            completion: completion
        )
    }
    
    func listEquipment(buildingName: String? = nil, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        ffi.listEquipment(buildingName: resolveBuilding(buildingName), completion: completion)
    }
    
    func listRooms(buildingName: String? = nil, completion: @escaping (Result<[Room], Error>) -> Void) {
        ffi.listRooms(buildingName: resolveBuilding(buildingName), completion: completion)
    }
}

// MARK: - Terminal Service
class TerminalService: ObservableObject {
    private let arxosCore = ArxOSCore()
    
    func executeCommand(_ command: String, completion: @escaping (Result<String, Error>) -> Void) {
        let components = command.split(separator: " ").map(String.init)
        guard let commandName = components.first else {
            completion(.success(""))
            return
        }
        let arguments = Array(components.dropFirst())
        
        switch commandName.lowercased() {
        case "help":
            completion(.success(getHelpText()))
        case "room":
            arxosCore.executeRoomCommand(arguments, completion: completion)
        case "equipment":
            arxosCore.executeEquipmentCommand(arguments, completion: completion)
        case "status":
            arxosCore.getStatus(completion: completion)
        case "diff":
            arxosCore.getDiff(completion: completion)
        case "history":
            arxosCore.getHistory(completion: completion)
        default:
            completion(.failure(TerminalError.unknownCommand(commandName)))
        }
    }
    
    private func getHelpText() -> String {
        """
        ArxOS Mobile
        
        Available commands:
        room list                                  List all rooms
        equipment list                             List equipment
        status                                     Show system status (coming soon)
        diff                                       Show changes (coming soon)
        history                                    Show commit history (coming soon)
        help                                       Show this help
        """
    }
}
