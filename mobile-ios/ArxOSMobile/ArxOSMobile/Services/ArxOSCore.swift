import Foundation
import Combine

// MARK: - Terminal Service
class TerminalService: ObservableObject {
    private let arxosCore = ArxOSCore()
    
    func executeCommand(_ command: String, completion: @escaping (Result<String, Error>) -> Void) {
        // Parse command and execute through ArxOS core
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
        ArxOS Mobile - Git for Buildings
        
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
        // Integrate with ArxOS core for room operations
        arxosCore.executeRoomCommand(arguments) { result in
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    private func handleEquipmentCommand(_ arguments: [String], completion: @escaping (Result<String, Error>) -> Void) {
        // Integrate with ArxOS core for equipment operations
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

// MARK: - ArxOS Core Integration
class ArxOSCore: ObservableObject {
    private var instance: OpaquePointer?
    
    init() {
        instance = arxos_mobile_new()
    }
    
    init(path: String) {
        instance = path.withCString { cString in
            arxos_mobile_new_with_path(cString)
        }
    }
    
    deinit {
        if let instance = instance {
            arxos_mobile_free(instance)
        }
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
        guard let instance = instance else {
            completion(.failure(TerminalError.coreError("ArxOS instance not initialized")))
            return
        }
        
        DispatchQueue.global().async {
            let result = command.withCString { cString in
                arxos_mobile_execute_command(instance, cString)
            }
            
            guard let result = result else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.coreError("Failed to execute command")))
                }
                return
            }
            
            let jsonString = String(cString: result)
            arxos_mobile_free_string(result)
            
            guard let data = jsonString.data(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.coreError("Failed to parse command result")))
                }
                return
            }
            
            do {
                let commandResult = try JSONDecoder().decode(CommandResult.self, from: data)
                DispatchQueue.main.async {
                    if commandResult.success {
                        completion(.success(commandResult.output))
                    } else {
                        completion(.failure(TerminalError.coreError(commandResult.error ?? "Unknown error")))
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.coreError("Failed to decode command result: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    // MARK: - AR Integration Methods
    func processARData(_ data: Data, completion: @escaping (Result<[DetectedEquipment], Error>) -> Void) {
        // This will integrate with Rust core for AR data processing
        DispatchQueue.global().asyncAfter(deadline: .now() + 1.0) {
            // Mock AR processing - will be replaced with real FFI calls
            let mockEquipment = [
                DetectedEquipment(
                    id: UUID(),
                    name: "VAV-301",
                    type: "HVAC",
                    position: SIMD3<Float>(0, 0, -1),
                    status: "Detected",
                    icon: "fan"
                )
            ]
            DispatchQueue.main.async {
                completion(.success(mockEquipment))
            }
        }
    }
    
    func saveARScan(_ equipment: [DetectedEquipment], room: String, completion: @escaping (Result<String, Error>) -> Void) {
        // This will integrate with Rust core for saving AR scan data
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.5) {
            DispatchQueue.main.async {
                completion(.success("AR scan saved for \(room)"))
            }
        }
    }
}

// MARK: - Data Models

struct CommandResult: Codable {
    let success: Bool
    let output: String
    let error: String?
    let execution_time_ms: UInt64
}

// MARK: - C FFI Declarations

@_silgen_name("arxos_mobile_new")
func arxos_mobile_new() -> OpaquePointer?

@_silgen_name("arxos_mobile_new_with_path")
func arxos_mobile_new_with_path(_ path: UnsafePointer<CChar>) -> OpaquePointer?

@_silgen_name("arxos_mobile_execute_command")
func arxos_mobile_execute_command(_ instance: OpaquePointer?, _ command: UnsafePointer<CChar>) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_mobile_get_rooms")
func arxos_mobile_get_rooms(_ instance: OpaquePointer?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_mobile_get_equipment")
func arxos_mobile_get_equipment(_ instance: OpaquePointer?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_mobile_get_git_status")
func arxos_mobile_get_git_status(_ instance: OpaquePointer?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_mobile_free_string")
func arxos_mobile_free_string(_ s: UnsafeMutablePointer<CChar>?)

@_silgen_name("arxos_mobile_free")
func arxos_mobile_free(_ instance: OpaquePointer?)

// MARK: - Error Types
enum TerminalError: Error, LocalizedError {
    case unknownCommand(String)
    case invalidArguments
    case coreError(String)
    
    var errorDescription: String? {
        switch self {
        case .unknownCommand(let command):
            return "Unknown command: \(command)"
        case .invalidArguments:
            return "Invalid arguments provided"
        case .coreError(let message):
            return "Core error: \(message)"
        }
    }
}
