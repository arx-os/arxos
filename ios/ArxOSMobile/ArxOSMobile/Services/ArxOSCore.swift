import Foundation
import Combine

#if canImport(arxos_mobile)
import arxos_mobile
#endif

// MARK: - ArxOS Core Integration using C FFI
class ArxOSCore: ObservableObject {
    private let ffi: ArxOSCoreFFI
    
    init() {
        self.ffi = ArxOSCoreFFI()
        print("ArxOS Core initialized")
    }
    
    init(path: String) {
        self.ffi = ArxOSCoreFFI()
        print("ArxOS Core initialized with path: \(path)")
    }
    
    func executeRoomCommand(_ arguments: [String], completion: @escaping (Result<String, Error>) -> Void) {
        let command = "room " + arguments.joined(separator: " ")
        executeCommand(command, completion: completion)
    }
    
    func executeEquipmentCommand(_ arguments: [String], completion: @escaping (Result<String, Error>) -> Void) {
        let command = "equipment " + arguments.joined(separator: " ")
        executeCommand(command, completion: completion)
    }
    
    func getStatus(completion: @escaping (Result<String, Error>) -> Void) {
        executeCommand("status", completion: completion)
    }
    
    func getDiff(completion: @escaping (Result<String, Error>) -> Void) {
        executeCommand("diff", completion: completion)
    }
    
    func getHistory(completion: @escaping (Result<String, Error>) -> Void) {
        executeCommand("history", completion: completion)
    }
    
    private func executeCommand(_ command: String, completion: @escaping (Result<String, Error>) -> Void) {
        DispatchQueue.global().async {
            let result = FFIWrapper.executeCommand(command)
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    func processARData(_ data: Data, roomName: String, completion: @escaping (Result<[DetectedEquipment], Error>) -> Void) {
        DispatchQueue.global().async {
            let jsonString = String(data: data, encoding: .utf8) ?? "{}"
            let result = FFIWrapper.parseARScan(jsonString: jsonString)
            
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    func saveARScan(_ equipment: [DetectedEquipment], room: String, completion: @escaping (Result<String, Error>) -> Void) {
        DispatchQueue.global().async {
            let result = FFIWrapper.saveARScan(equipment: equipment, room: room)
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    private func iconForEquipmentType(_ type: String) -> String {
        switch type.lowercased() {
        case "hvac":
            return "fan"
        case "electrical":
            return "bolt"
        case "av":
            return "tv"
        case "furniture":
            return "chair"
        case "safety":
            return "exclamationmark.triangle"
        case "plumbing":
            return "drop"
        case "network":
            return "network"
        default:
            return "wrench"
        }
    }
}

// MARK: - FFI Wrapper
struct FFIWrapper {
    static func executeCommand(_ command: String) -> Result<String, Error> {
        #if canImport(arxos_mobile)
        // FFI implementation when library is linked
        // return .success(executeFFICommand(command))
        return .failure(TerminalError.ffiError("FFI not yet linked"))
        #else
        return .failure(TerminalError.ffiError("FFI library not available"))
        #endif
    }
    
    static func parseARScan(jsonString: String) -> Result<[DetectedEquipment], Error> {
        #if canImport(arxos_mobile)
        // FFI implementation when library is linked
        return .success([])
        #else
        return .failure(TerminalError.ffiError("FFI library not available"))
        #endif
    }
    
    static func saveARScan(equipment: [DetectedEquipment], room: String) -> Result<String, Error> {
        #if canImport(arxos_mobile)
        // FFI implementation when library is linked
        return .success("AR scan saved for \(room)")
        #else
        return .failure(TerminalError.ffiError("FFI library not available"))
        #endif
    }
}

// MARK: - Terminal Service
class TerminalService: ObservableObject {
    private let arxosCore = ArxOSCore()
    
    func executeCommand(_ command: String, completion: @escaping (Result<String, Error>) -> Void) {
        let components = command.components(separatedBy: " ")
        guard !components.isEmpty else {
            completion(.success(""))
            return
        }
        
        let commandName = components[0]
        let arguments = Array(components.dropFirst())
        
        switch commandName {
        case "help":
            completion(.success(getHelpText()))
            
        case "room":
            handleRoomCommand(arguments, completion: completion)
            
        case "equipment":
            handleEquipmentCommand(arguments, completion: completion)
            
        case "status":
            handleStatusCommand(completion: completion)
            
        case "diff":
            handleDiffCommand(completion: completion)
            
        case "history":
            handleHistoryCommand(completion: completion)
            
        default:
            completion(.failure(TerminalError.unknownCommand(commandName)))
        }
    }
    
    private func getHelpText() -> String {
        return """
        ArxOS Mobile
        
        Available commands:
        room create --name <name> --floor <floor>  Create a new room
        room list                                  List all rooms
        room show <id>                            Show room details
        
        equipment add --name <name> --type <type>  Add equipment
        equipment list                            List equipment
        equipment update <id>                     Update equipment
        
        status                                    Show system status
        diff                                      Show changes
        history                                   Show commit history
        
        help                                      Show this help
        """
    }
    
    private func handleRoomCommand(_ arguments: [String], completion: @escaping (Result<String, Error>) -> Void) {
        arxosCore.executeRoomCommand(arguments) { result in
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    private func handleEquipmentCommand(_ arguments: [String], completion: @escaping (Result<String, Error>) -> Void) {
        arxosCore.executeEquipmentCommand(arguments) { result in
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    private func handleStatusCommand(completion: @escaping (Result<String, Error>) -> Void) {
        arxosCore.getStatus { result in
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    private func handleDiffCommand(completion: @escaping (Result<String, Error>) -> Void) {
        arxosCore.getDiff { result in
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    private func handleHistoryCommand(completion: @escaping (Result<String, Error>) -> Void) {
        arxosCore.getHistory { result in
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
}

// MARK: - Error Types
enum TerminalError: Error, LocalizedError {
    case unknownCommand(String)
    case invalidArguments
    case ffiError(String)
    
    var errorDescription: String? {
        switch self {
        case .unknownCommand(let command):
            return "Unknown command: \(command)"
        case .invalidArguments:
            return "Invalid arguments provided"
        case .ffiError(let message):
            return "FFI error: \(message)"
        }
    }
}
