import Foundation
import Combine

// MARK: - ArxOS Core Integration using UniFFI
class ArxOSCore: ObservableObject {
    private var instance: ArxOSMobile?
    
    init() {
        do {
            instance = try ArxOSMobile()
        } catch {
            print("Failed to initialize ArxOS core: \(error)")
        }
    }
    
    init(path: String) {
        do {
            instance = try ArxOSMobile.newWithPath(path: path)
        } catch {
            print("Failed to initialize ArxOS core with path: \(error)")
        }
    }
    
    deinit {
        instance = nil
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
            do {
                let result = try instance.executeCommand(command: command)
                DispatchQueue.main.async {
                    if result.success {
                        completion(.success(result.output))
                    } else {
                        completion(.failure(TerminalError.coreError(result.error ?? "Unknown error")))
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.coreError("Failed to execute command: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    // MARK: - AR Integration Methods
    func processARData(_ data: Data, roomName: String, completion: @escaping (Result<[DetectedEquipment], Error>) -> Void) {
        guard let instance = instance else {
            completion(.failure(TerminalError.coreError("ArxOS instance not initialized")))
            return
        }
        
        DispatchQueue.global().async {
            do {
                let scanData = Array(data)
                let result = try instance.processArScan(scanData: scanData, roomName: roomName)
                
                let detectedEquipment = result.equipmentDetected.map { equipment in
                    DetectedEquipment(
                        id: UUID(),
                        name: equipment.name,
                        type: equipment.equipmentType,
                        position: SIMD3<Float>(
                            Float(equipment.position?.x ?? 0),
                            Float(equipment.position?.y ?? 0),
                            Float(equipment.position?.z ?? 0)
                        ),
                        status: equipment.status,
                        icon: self.iconForEquipmentType(equipment.equipmentType)
                    )
                }
                
                DispatchQueue.main.async {
                    completion(.success(detectedEquipment))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.coreError("AR processing failed: \(error.localizedDescription)")))
                }
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
